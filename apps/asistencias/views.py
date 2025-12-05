# =========================================================
#   IMPORTS
# =========================================================

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
            'id_trabajador'
        ).order_by('-fecha', 'id_trabajador')

        user = self.request.user

        # 🔹 Si es jefe → filtrar solo su unidad
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            queryset = queryset.filter(id_trabajador__id_unidad=unidad)

        # ----- Filtros -----
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')
        estatus = self.request.GET.get('estatus')
        trabajador_id = self.request.GET.get('trabajador')

        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)
        if estatus:
            queryset = queryset.filter(estatus=estatus)
        if trabajador_id:
            queryset = queryset.filter(id_trabajador_id=trabajador_id)

        if not any([fecha_inicio, fecha_fin, estatus, trabajador_id]):
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
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            form.fields['trabajador'].queryset = Trabajador.objects.filter(
                activo=True,
                id_unidad=unidad
            )
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
        
        # 🔹 Si es jefe, filtrar trabajadores solo de su unidad
        if user.perfil.es_jefe():
            trabajador_jefe = user.perfil.id_trabajador
            if trabajador_jefe and trabajador_jefe.id_unidad:
                form.fields['numero_empleado'].queryset = Trabajador.objects.filter(
                    id_unidad=trabajador_jefe.id_unidad,
                    activo=True
                ).order_by('apellido_paterno', 'apellido_materno', 'nombre')
        else:
            # Admin ve todos los trabajadores activos
            form.fields['numero_empleado'].queryset = Trabajador.objects.filter(
                activo=True
            ).order_by('apellido_paterno', 'apellido_materno', 'nombre')
        
        return form

    def form_valid(self, form):
        trabajador = form.cleaned_data['numero_empleado']
        hoy = date.today()
        hora_actual = datetime.now().time()

        user = self.request.user

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
        context['fecha_actual'] = date.today()
        context['hora_actual'] = datetime.now().strftime('%H:%M:%S')

        # 🔹 Filtrar últimos registros según rol
        user = self.request.user
        ultimos_registros = RegistroAsistencia.objects.filter(fecha=date.today())
        
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

        # 🔹 Filtrar trabajadores por unidad si es jefe
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad
            form.fields['id_trabajador'].queryset = Trabajador.objects.filter(id_unidad=unidad)

        return form

    def form_valid(self, form):
        registro = form.save(commit=False)
        registro.calcular_estatus_automatico()
        registro.save()

        messages.success(self.request, "Registro creado correctamente")
        return super().form_valid(form)



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

        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=30)

        if self.request.GET.get('fecha_inicio'):
            fecha_inicio = datetime.strptime(self.request.GET['fecha_inicio'], '%Y-%m-%d').date()

        if self.request.GET.get('fecha_fin'):
            fecha_fin = datetime.strptime(self.request.GET['fecha_fin'], '%Y-%m-%d').date()

        context['resumen'] = obtener_resumen_asistencia_trabajador(trabajador, fecha_inicio, fecha_fin)
        context['fecha_inicio'] = fecha_inicio
        context['fecha_fin'] = fecha_fin

        context['registros'] = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha__range=[fecha_inicio, fecha_fin]
        ).order_by('-fecha')

        context['registro_hoy'] = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha=date.today()
        ).first()

        return context
    
@method_decorator(rol_requerido('trabajador'), name='dispatch')
class RegistrarMiAsistenciaView(View):
    """
    Vista que permite al trabajador registrar su propia entrada y salida.
    - Entrada si no tiene entrada registrada
    - Salida si ya tiene entrada pero no salida
    """
    
    def get(self, request):
        """Mostrar la página de registro de asistencia"""
        trabajador = request.user.perfil.id_trabajador
        hoy = date.today()
        
        # Obtener registro de hoy si existe
        registro_hoy = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha=hoy
        ).first()
        
        # Obtener últimos registros
        ultimos_registros = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador
        ).order_by('-fecha')[:10]
        
        context = {
            'trabajador': trabajador,
            'registro_hoy': registro_hoy,
            'ultimos_registros': ultimos_registros,
            'fecha_actual': hoy,
        }
        
        return render(request, 'asistencias/mi_registro.html', context)

    def post(self, request):
        trabajador = request.user.perfil.id_trabajador
        hoy = date.today()
        hora_actual = datetime.now().time()

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


