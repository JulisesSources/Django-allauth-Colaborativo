# apps/asistencias/views.py

from datetime import date, datetime, timedelta

from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils.decorators import method_decorator

from .models import RegistroAsistencia
from .forms import (
    RegistroAsistenciaForm,
    RegistroRapidoForm,
    FiltroAsistenciaForm
)
from .utils import (
    calcular_estatus_asistencia,
    obtener_resumen_asistencia_trabajador,
    trabajador_debe_asistir
)

from apps.trabajadores.models import Trabajador
from apps.unidades.models import UnidadAdministrativa
from apps.accounts.decorators import rol_requerido




# =========================================================
#   LISTA DE ASISTENCIAS (Admin + Jefe)
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe'), name='dispatch')
class AsistenciaListView(ListView):
    model = RegistroAsistencia
    template_name = 'asistencias/lista_asistencias.html'
    context_object_name = 'registros'
    paginate_by = 20

    def get_queryset(self):
        queryset = RegistroAsistencia.objects.select_related(
            'id_trabajador', 'id_trabajador__id_unidad'
        ).order_by('-fecha', 'id_trabajador')

        user = self.request.user

        # 🔹 Si es jefe → filtrar solo su unidad
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            queryset = queryset.filter(id_trabajador__id_unidad=unidad)

        # ----- Filtros -----
        unidad_id = self.request.GET.get('unidad')
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        estatus = self.request.GET.get('estatus')
        trabajador_id = self.request.GET.get('trabajador')

        # Filtro por unidad (solo admin puede filtrar por unidad)
        if unidad_id and user.perfil.es_admin():
            queryset = queryset.filter(id_trabajador__id_unidad_id=unidad_id)
        
        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)
        if estatus:
            queryset = queryset.filter(estatus=estatus)
        if trabajador_id:
            queryset = queryset.filter(id_trabajador_id=trabajador_id)

        if not any([unidad_id, fecha_inicio, fecha_fin, estatus, trabajador_id]):
            queryset = queryset.filter(fecha__gte=date.today() - timedelta(days=7))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        hoy = date.today()

        context['filtro_form'] = FiltroAsistenciaForm(self.request.GET or None)

        context['fecha_actual'] = hoy
        context['asistencias_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy, estatus='ASI').count()
        context['retardos_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy, estatus='RET').count()
        context['faltas_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy, estatus='FAL').count()

        form = FiltroAsistenciaForm(self.request.GET or None)

        user = self.request.user
        
        # Agregar unidades y trabajadores para el filtro dinámico (solo admin)
        if user.perfil.es_admin():
            context['unidades'] = UnidadAdministrativa.objects.all().order_by('nombre')
            context['todos_trabajadores'] = Trabajador.objects.filter(activo=True).select_related('id_unidad').order_by('nombre')
        elif user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            form.fields['trabajador'].queryset = Trabajador.objects.filter(
                activo=True,
                id_unidad=unidad
            )
            context['trabajadores'] = Trabajador.objects.filter(activo=True, id_unidad=unidad).order_by('nombre')
        elif user.perfil.es_trabajador():
            # Solo él mismo
            form.fields['trabajador'].queryset = Trabajador.objects.filter(
                pk=user.perfil.id_trabajador.id
            )

        context['filtro_form'] = form

        return context



# =========================================================
#   REGISTRO RÁPIDO (Admin + Jefe)
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe'), name='dispatch')
class RegistroRapidoView(FormView):
    template_name = 'asistencias/registro_rapido.html'
    form_class = RegistroRapidoForm
    success_url = reverse_lazy('asistencias:registro_rapido')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        user = self.request.user
        hoy = date.today()
        
        # 🔹 Si es jefe, filtrar trabajadores solo de su unidad
        if user.perfil.es_jefe():
            trabajador_jefe = user.perfil.id_trabajador
            if trabajador_jefe and trabajador_jefe.id_unidad:
                trabajadores_base = Trabajador.objects.filter(
                    id_unidad=trabajador_jefe.id_unidad,
                    activo=True
                )
        else:
            # Admin ve todos los trabajadores activos
            trabajadores_base = Trabajador.objects.filter(activo=True)
        
        # 🔹 Filtrar solo trabajadores que tienen jornadas asignadas
        from apps.jornadas_laborales.models import TrabajadorJornada
        trabajadores_con_jornada = TrabajadorJornada.objects.filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
        ).values_list('id_trabajador', flat=True)
        
        trabajadores_base = trabajadores_base.filter(id_trabajador__in=trabajadores_con_jornada)
        
        # Obtener trabajadores que ya completaron su asistencia hoy
        trabajadores_completos_hoy = RegistroAsistencia.objects.filter(
            fecha=hoy,
            hora_entrada__isnull=False,
            hora_salida__isnull=False
        ).values_list('id_trabajador', flat=True)
        
        # Excluir trabajadores que ya completaron su asistencia
        trabajadores_disponibles = trabajadores_base.exclude(
            id_trabajador__in=trabajadores_completos_hoy
        ).order_by('apellido_paterno', 'apellido_materno', 'nombre')
        
        form.fields['numero_empleado'].queryset = trabajadores_disponibles
        
        # Guardar flag si todos asistieron
        self.todos_asistieron = not trabajadores_disponibles.exists() and trabajadores_base.exists()
        
        return form

    def form_valid(self, form):
        trabajador = form.cleaned_data['numero_empleado']
        hoy = date.today()
        hora_actual = datetime.now().time()

        user = self.request.user
        
        # 🔹 Validar si es día inhábil
        from .utils import es_dia_inhabil
        if es_dia_inhabil(hoy):
            messages.error(self.request, "Hoy es día festivo/inhábil. No se puede registrar asistencia.")
            return redirect(self.success_url)

        # 🔹 Jefe no puede registrar asistencia de trabajador de otra unidad
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            if trabajador.id_unidad != unidad:
                messages.error(self.request, "No puedes registrar asistencia de otra unidad.")
                return redirect(self.success_url)

        # === Lógica normal ===
        registro_existente = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha=hoy
        ).first()

        if registro_existente:
            if not registro_existente.hora_entrada:
                registro_existente.hora_entrada = hora_actual
                registro_existente.calcular_estatus_automatico()
                registro_existente.save()
                messages.success(self.request, f"Entrada registrada")
            elif not registro_existente.hora_salida:
                registro_existente.hora_salida = hora_actual
                registro_existente.save()
                messages.success(self.request, f"Salida registrada")
            else:
                messages.warning(self.request, "El registro ya estaba completo.")
        else:
            estatus = calcular_estatus_asistencia(trabajador, hoy, hora_actual)
            RegistroAsistencia.objects.create(
                id_trabajador=trabajador,
                fecha=hoy,
                hora_entrada=hora_actual,
                estatus=estatus
            )
            messages.success(self.request, f"Asistencia creada")

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        context['fecha_actual'] = hoy
        context['hora_actual'] = datetime.now().strftime('%H:%M:%S')
        
        # Verificar si es día festivo/inhábil
        from .utils import es_dia_inhabil
        context['es_dia_inhabil'] = es_dia_inhabil(hoy)
        
        # Flag de todos asistieron
        context['todos_asistieron'] = getattr(self, 'todos_asistieron', False)

        # 🔹 Filtrar últimos registros según rol
        user = self.request.user
        ultimos_registros = RegistroAsistencia.objects.filter(fecha=hoy)
        
        if user.perfil.es_jefe():
            trabajador_jefe = user.perfil.id_trabajador
            if trabajador_jefe and trabajador_jefe.id_unidad:
                ultimos_registros = ultimos_registros.filter(
                    id_trabajador__id_unidad=trabajador_jefe.id_unidad
                )
        
        context['ultimos_registros'] = ultimos_registros.select_related(
            'id_trabajador'
        ).order_by('-created_at')[:5]

        return context



# =========================================================
#   REGISTRO MANUAL - CREATE
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe'), name='dispatch')
class RegistroAsistenciaCreateView(CreateView):
    model = RegistroAsistencia
    form_class = RegistroAsistenciaForm
    template_name = 'asistencias/registrar_asistencia.html'
    success_url = reverse_lazy('asistencias:lista')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        hoy = date.today()

        # Base queryset de trabajadores activos
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            trabajadores_base = Trabajador.objects.filter(id_unidad=unidad, activo=True)
        else:
            trabajadores_base = Trabajador.objects.filter(activo=True)
        
        # 🔹 Filtrar solo trabajadores que tienen jornadas asignadas
        from apps.jornadas_laborales.models import TrabajadorJornada
        from django.db.models import Q
        trabajadores_con_jornada = TrabajadorJornada.objects.filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
        ).values_list('id_trabajador', flat=True)
        
        trabajadores_base = trabajadores_base.filter(id_trabajador__in=trabajadores_con_jornada)

        # Obtener trabajadores que ya completaron su asistencia hoy
        # (tienen entrada Y salida registradas)
        trabajadores_completos_hoy = RegistroAsistencia.objects.filter(
            fecha=hoy,
            hora_entrada__isnull=False,
            hora_salida__isnull=False
        ).values_list('id_trabajador', flat=True)

        # Excluir trabajadores que ya completaron su asistencia
        trabajadores_disponibles = trabajadores_base.exclude(
            id_trabajador__in=trabajadores_completos_hoy
        )

        form.fields['id_trabajador'].queryset = trabajadores_disponibles

        # Verificar si hay trabajadores disponibles
        if not trabajadores_disponibles.exists():
            self.todos_asistieron = True
        else:
            self.todos_asistieron = False

        # Si estamos editando un trabajador que ya tiene entrada, deshabilitar hora_entrada
        trabajador_id = self.request.POST.get('id_trabajador') or self.request.GET.get('trabajador')
        if trabajador_id:
            registro_existente = RegistroAsistencia.objects.filter(
                id_trabajador_id=trabajador_id,
                fecha=hoy,
                hora_entrada__isnull=False
            ).first()
            if registro_existente:
                form.fields['hora_entrada'].widget.attrs['readonly'] = True
                form.fields['hora_entrada'].initial = registro_existente.hora_entrada

        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['todos_asistieron'] = getattr(self, 'todos_asistieron', False)
        
        # Verificar si es día festivo/inhábil
        from .utils import es_dia_inhabil
        hoy = date.today()
        context['es_dia_inhabil'] = es_dia_inhabil(hoy)
        
        # Obtener trabajadores con registro parcial (solo entrada)
        user = self.request.user
        
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            registros_parciales = RegistroAsistencia.objects.filter(
                fecha=hoy,
                hora_entrada__isnull=False,
                hora_salida__isnull=True,
                id_trabajador__id_unidad=unidad
            ).select_related('id_trabajador')
        else:
            registros_parciales = RegistroAsistencia.objects.filter(
                fecha=hoy,
                hora_entrada__isnull=False,
                hora_salida__isnull=True
            ).select_related('id_trabajador')
        
        context['registros_parciales'] = registros_parciales
        context['fecha_actual'] = hoy
        
        return context

    def form_valid(self, form):
        registro = form.save(commit=False)
        hoy = date.today()
        
        # Verificar si es día inhábil
        from .utils import es_dia_inhabil
        if es_dia_inhabil(registro.fecha):
            messages.error(self.request, "No se puede registrar asistencia en días festivos/inhábiles.")
            return redirect(self.success_url)
        
        # Verificar si ya existe un registro para este trabajador hoy
        registro_existente = RegistroAsistencia.objects.filter(
            id_trabajador=registro.id_trabajador,
            fecha=registro.fecha
        ).first()
        
        if registro_existente:
            # Si ya tiene entrada pero no salida, solo actualizar la salida
            if registro_existente.hora_entrada and not registro_existente.hora_salida:
                if registro.hora_salida:
                    registro_existente.hora_salida = registro.hora_salida
                    registro_existente.save()
                    messages.success(self.request, "Salida registrada correctamente")
                    return redirect(self.success_url)
                else:
                    messages.warning(self.request, "El trabajador ya tiene entrada. Solo falta registrar la salida.")
                    return redirect(self.success_url)
            elif registro_existente.hora_entrada and registro_existente.hora_salida:
                messages.warning(self.request, "El trabajador ya completó su asistencia hoy.")
                return redirect(self.success_url)
        
        registro.calcular_estatus_automatico()
        registro.created_by = self.request.user
        registro.save()

        messages.success(self.request, "Registro creado correctamente")
        return redirect(self.success_url)



# =========================================================
#   DETALLE DE ASISTENCIA
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe'), name='dispatch')
class AsistenciaDetailView(DetailView):
    model = RegistroAsistencia
    template_name = 'asistencias/detalle_asistencia.html'
    context_object_name = 'registro'

    def dispatch(self, request, *args, **kwargs):
        registro = self.get_object()

        # 🔹 Jefe solo ve registros de su unidad
        if request.user.perfil.es_jefe():
            unidad = request.user.perfil.id_trabajador.id_unidad
            if registro.id_trabajador.id_unidad != unidad:
                from django.http import Http404
                raise Http404("No puedes acceder a esta asistencia.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro = self.get_object()

        debe, razon = trabajador_debe_asistir(registro.id_trabajador, registro.fecha)
        context['debe_asistir'] = debe
        context['razon'] = razon

        return context



# =========================================================
#   RESUMEN DE TRABAJADOR
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe', 'trabajador'), name='dispatch')
class ResumenTrabajadorView(DetailView):
    model = Trabajador
    template_name = 'asistencias/resumen_trabajador.html'
    context_object_name = 'trabajador'
    slug_field = 'numero_empleado'
    slug_url_kwarg = 'numero_empleado'

    def dispatch(self, request, *args, **kwargs):
        numero_empleado = kwargs.get('numero_empleado')
        user = request.user

        try:
            trabajador = Trabajador.objects.get(numero_empleado=numero_empleado)
        except Trabajador.DoesNotExist:
            from django.http import Http404
            raise Http404("Trabajador no encontrado.")

        # Trabajador: solo puede ver su propio resumen
        if user.perfil.rol == 'trabajador':
            if user.perfil.id_trabajador.numero_empleado != numero_empleado:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("No puedes ver a otro trabajador.")

        # Jefe: solo trabajadores de su unidad
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            if trabajador.id_unidad != unidad:
                from django.http import Http404
                raise Http404("No tienes acceso a este trabajador.")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = self.get_object()
        hoy = date.today()

        fecha_fin = hoy
        fecha_inicio = fecha_fin - timedelta(days=30)

        if self.request.GET.get('fecha_inicio'):
            fecha_inicio = datetime.strptime(self.request.GET['fecha_inicio'], '%Y-%m-%d').date()

        if self.request.GET.get('fecha_fin'):
            fecha_fin = datetime.strptime(self.request.GET['fecha_fin'], '%Y-%m-%d').date()

        # Obtener resumen estadístico
        resumen = obtener_resumen_asistencia_trabajador(trabajador, fecha_inicio, fecha_fin)
        context['resumen'] = resumen
        context['fecha_inicio'] = fecha_inicio
        context['fecha_fin'] = fecha_fin

        # Estadísticas para las tarjetas
        context['asistencias'] = resumen.get('asistencias', 0)
        context['retardos'] = resumen.get('retardos', 0)
        context['faltas'] = resumen.get('faltas', 0)
        context['porcentaje_asistencia'] = resumen.get('porcentaje_asistencia', 0)
        context['porcentaje_retardos'] = resumen.get('porcentaje_retardos', 0)
        context['porcentaje_faltas'] = resumen.get('porcentaje_faltas', 0)

        # Resumen de la semana (últimos 7 días)
        inicio_semana = hoy - timedelta(days=7)
        context['resumen_semana'] = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha__gte=inicio_semana,
            fecha__lte=hoy
        ).order_by('-fecha')

        # Historial de registros en el rango de fechas
        context['registros'] = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha__range=[fecha_inicio, fecha_fin]
        ).order_by('-fecha')

        context['registro_hoy'] = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha=hoy
        ).first()

        return context
    
@method_decorator(rol_requerido('admin', 'jefe', 'trabajador'), name='dispatch')
class RegistrarMiAsistenciaView(View):
    """
    Vista que permite al trabajador (o jefe/admin) registrar su propia entrada y salida.
    - Valida que tenga jornada vigente asignada
    - Entrada si no tiene entrada registrada
    - Salida si ya tiene entrada pero no salida
    """
    
    def get(self, request):
        """Mostrar la página de registro de asistencia"""
        trabajador = request.user.perfil.id_trabajador
        hoy = date.today()
        
        # Verificar si tiene jornada vigente y día inhábil
        from .utils import obtener_jornada_vigente, trabajador_debe_asistir, es_dia_inhabil, obtener_resumen_asistencia_trabajador
        jornada_vigente = obtener_jornada_vigente(trabajador, hoy)
        debe_asistir, razon = trabajador_debe_asistir(trabajador, hoy)
        dia_inhabil = es_dia_inhabil(hoy)
        
        # Obtener registro de hoy si existe
        registro_hoy = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha=hoy
        ).first()
        
        # Obtener últimos registros
        ultimos_registros = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador
        ).order_by('-fecha')[:10]
        
        # Obtener resumen de asistencias (últimos 30 días)
        fecha_fin = hoy
        fecha_inicio = hoy - timedelta(days=30)
        resumen = obtener_resumen_asistencia_trabajador(trabajador, fecha_inicio, fecha_fin)
        
        context = {
            'trabajador': trabajador,
            'registro_hoy': registro_hoy,
            'ultimos_registros': ultimos_registros,
            'fecha_actual': hoy,
            'jornada_vigente': jornada_vigente,
            'debe_asistir': debe_asistir,
            'razon_no_asistir': razon if not debe_asistir else None,
            'es_dia_inhabil': dia_inhabil,
            # Resumen estadístico
            'asistencias': resumen.get('asistencias', 0),
            'retardos': resumen.get('retardos', 0),
            'faltas': resumen.get('faltas', 0),
            'porcentaje_asistencia': resumen.get('porcentaje_asistencia', 0),
        }
        
        return render(request, 'asistencias/mi_registro.html', context)

    def post(self, request):
        trabajador = request.user.perfil.id_trabajador
        hoy = date.today()
        hora_actual = datetime.now().time()
        
        # Verificar si es día inhábil
        from .utils import obtener_jornada_vigente, trabajador_debe_asistir, calcular_estatus_asistencia, es_dia_inhabil
        
        if es_dia_inhabil(hoy):
            messages.error(request, "Hoy es día festivo/inhábil. No se puede registrar asistencia.")
            return redirect('asistencias:mi_registro')
        
        jornada_vigente = obtener_jornada_vigente(trabajador, hoy)
        
        # Si no tiene jornada vigente, avisar pero permitir registrar lo que alcanzó
        if not jornada_vigente:
            # Verificar si ya tiene registro de hoy (pudo haber tenido jornada al inicio del día)
            registro_existente = RegistroAsistencia.objects.filter(
                id_trabajador=trabajador,
                fecha=hoy
            ).first()
            
            if registro_existente:
                if not registro_existente.hora_salida:
                    registro_existente.hora_salida = hora_actual
                    registro_existente.save()
                    messages.warning(
                        request, 
                        "Ya no tienes jornada asignada para hoy, pero se registró tu salida con lo que alcanzaste."
                    )
                else:
                    messages.warning(request, "Tu registro de hoy ya está completo.")
            else:
                messages.error(
                    request, 
                    "No tienes una jornada asignada vigente. Contacta a tu supervisor."
                )
            return redirect('asistencias:mi_registro')

        registro, creado = RegistroAsistencia.objects.get_or_create(
            id_trabajador=trabajador,
            fecha=hoy
        )

        # Registrar entrada
        if not registro.hora_entrada:
            registro.hora_entrada = hora_actual
            registro.calcular_estatus_automatico()
            registro.save()
            messages.success(request, "Entrada registrada correctamente.")

        # Registrar salida
        elif not registro.hora_salida:
            registro.hora_salida = hora_actual
            registro.save()
            messages.success(request, "Salida registrada correctamente.")

        else:
            messages.warning(request, "El registro de hoy ya está completo.")

        return redirect('asistencias:mi_registro')


