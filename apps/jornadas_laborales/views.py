# apps/jornadas_laborales/views.py

from datetime import date, timedelta
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import Http404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Exists, OuterRef
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)

from .models import (
    JornadaLaboral,
    CalendarioLaboral,
    TrabajadorJornada,
    JornadaDias
)

from apps.trabajadores.models import Trabajador
from apps.unidades.models import UnidadAdministrativa

from .forms import (
    JornadaLaboralForm,
    CalendarioLaboralForm,
    AsignarJornadaForm
)

from apps.accounts.decorators import (
    rol_requerido,
    requiere_trabajador_y_unidad,
    jefe_o_admin_requerido,
    admin_requerido
)



# =========================================================
#   JORNADAS LABORALES - LIST & DETAIL
# =========================================================

@method_decorator([rol_requerido('admin', 'jefe'), requiere_trabajador_y_unidad], name='dispatch')
class JornadaListView(LoginRequiredMixin, ListView):
    model = JornadaLaboral
    template_name = 'jornadas_laborales/lista_jornadas.html'
    context_object_name = 'jornadas'
    paginate_by = 10

    def get_queryset(self):
        hoy = date.today()
        user = self.request.user

        # 🔹 Si es jefe, anotar solo trabajadores de su unidad
        if user.perfil.es_jefe() and user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
            unidad = user.perfil.id_trabajador.id_unidad
            # Anotamos con trabajadores de la unidad del jefe
            qs = JornadaLaboral.objects.prefetch_related('dias').annotate(
                num_dias=Count('dias', distinct=True),
                num_trabajadores=Count(
                    'trabajadores_asignados',
                    filter=Q(trabajadores_asignados__id_trabajador__id_unidad=unidad),
                    distinct=True
                ),
                num_trabajadores_activos=Count(
                    'trabajadores_asignados',
                    filter=(
                        Q(trabajadores_asignados__id_trabajador__id_unidad=unidad) &
                        (Q(trabajadores_asignados__fecha_fin__isnull=True) | Q(trabajadores_asignados__fecha_fin__gte=hoy))
                    ),
                    distinct=True
                )
            ).order_by('descripcion')
            
            # Mostrar jornadas que tienen trabajadores de su unidad asignados
            qs = qs.filter(trabajadores_asignados__id_trabajador__id_unidad=unidad).distinct()
        else:
            # Admin ve todo
            qs = JornadaLaboral.objects.prefetch_related('dias').annotate(
                num_dias=Count('dias', distinct=True),
                num_trabajadores=Count('trabajadores_asignados', distinct=True),
                num_trabajadores_activos=Count(
                    'trabajadores_asignados',
                    filter=Q(trabajadores_asignados__fecha_fin__isnull=True) | Q(trabajadores_asignados__fecha_fin__gte=hoy),
                    distinct=True
                )
            ).order_by('descripcion')

        # 🔹 FILTRO desde GET - Solo tipo de jornada
        tipo = self.request.GET.get('tipo', '')

        # Filtro por tipo de jornada
        if tipo:
            qs = qs.filter(descripcion=tipo)

        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        hoy = date.today()

        # Base queryset según rol
        if user.perfil.es_jefe() and user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
            unidad = user.perfil.id_trabajador.id_unidad
            # Jornadas que tienen trabajadores de la unidad del jefe
            jornadas_qs = JornadaLaboral.objects.filter(
                trabajadores_asignados__id_trabajador__id_unidad=unidad
            ).distinct()
            trabajadores_qs = Trabajador.objects.filter(id_unidad=unidad, activo=True)
            
            # Estadísticas específicas para jefes
            # 1. Total de trabajadores en su unidad
            context['total_trabajadores_unidad'] = trabajadores_qs.count()
            
            # 2. Trabajadores con jornada asignada (de su unidad)
            trabajadores_con_jornada = TrabajadorJornada.objects.filter(
                id_trabajador__id_unidad=unidad
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
            ).values_list('id_trabajador', flat=True).distinct()
            context['trabajadores_con_jornada'] = len(trabajadores_con_jornada)
            
            # 3. Trabajadores sin jornada vigente (de su unidad)
            context['trabajadores_sin_jornada'] = trabajadores_qs.exclude(
                id_trabajador__in=trabajadores_con_jornada
            ).count()
            
            # 4. Jornadas activas en su unidad
            context['jornadas_activas_unidad'] = jornadas_qs.filter(
                trabajadores_asignados__fecha_fin__isnull=True
            ).distinct().count() or jornadas_qs.filter(
                trabajadores_asignados__fecha_fin__gte=hoy
            ).distinct().count()
            
            # No mostrar estadísticas globales irrelevantes para jefes
            context['es_jefe'] = True
        else:
            # Admin ve todo
            jornadas_qs = JornadaLaboral.objects.all()
            trabajadores_qs = Trabajador.objects.filter(activo=True)

            # 1. Total de jornadas
            context['total_jornadas'] = jornadas_qs.count()

            # 2. Jornadas en uso (tienen al menos un trabajador con asignación vigente)
            jornadas_en_uso = jornadas_qs.filter(
                Exists(
                    TrabajadorJornada.objects.filter(
                        id_jornada=OuterRef('pk')
                    ).filter(
                        Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
                    )
                )
            ).count()
            context['jornadas_en_uso'] = jornadas_en_uso

            # 3. Jornadas sin uso (no tienen trabajadores vigentes)
            context['jornadas_sin_uso'] = context['total_jornadas'] - jornadas_en_uso

            # 4. Trabajadores sin jornada vigente
            trabajadores_con_jornada = TrabajadorJornada.objects.filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
            ).values_list('id_trabajador', flat=True)
            context['trabajadores_sin_jornada'] = trabajadores_qs.exclude(
                id_trabajador__in=trabajadores_con_jornada
            ).count()

            # 5. Días inhábiles próximos (próximos 30 días)
            fecha_limite = hoy + timedelta(days=30)
            context['dias_inhabiles_proximos'] = CalendarioLaboral.objects.filter(
                fecha__gte=hoy,
                fecha__lte=fecha_limite,
                es_inhabil=True
            ).count()
            
            context['es_jefe'] = False

        # Asignaciones para el tab de asignaciones
        if user.perfil.es_jefe() and user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
            context['asignaciones'] = TrabajadorJornada.objects.filter(
                id_trabajador__id_unidad=unidad
            ).select_related('id_trabajador', 'id_jornada').order_by('-fecha_inicio')[:20]
        else:
            context['asignaciones'] = TrabajadorJornada.objects.all().select_related(
                'id_trabajador', 'id_jornada'
            ).order_by('-fecha_inicio')[:20]

        # Calendario laboral para el tab de calendario
        context['dias_calendario'] = CalendarioLaboral.objects.filter(
            fecha__gte=hoy - timedelta(days=30)
        ).order_by('fecha')[:30]

        return context



@method_decorator([rol_requerido('admin', 'jefe'), requiere_trabajador_y_unidad], name='dispatch')
class JornadaDetailView(LoginRequiredMixin, DetailView):
    model = JornadaLaboral
    template_name = 'jornadas_laborales/detalle_jornada.html'
    context_object_name = 'jornada'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        user = self.request.user
        if user.perfil.es_jefe():
            unidad = user.perfil.id_trabajador.id_unidad

            pertenece = TrabajadorJornada.objects.filter(
                id_jornada=obj,
                id_trabajador__id_unidad=unidad
            ).exists()

            if not pertenece:
                raise Http404("No tienes permiso para ver esta jornada.")

        return obj
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        # Si es jefe → validar que la jornada sea de su unidad
        user = request.user
        if user.perfil.es_jefe():
            unidad_jefe = user.perfil.id_trabajador.id_unidad

            # jornada pertenece a su unidad?
            pertenece = TrabajadorJornada.objects.filter(
                id_jornada=obj,
                id_trabajador__id_unidad=unidad_jefe
            ).exists()

            if not pertenece:
                raise Http404("No puedes acceder a esta jornada")

        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jornada = self.get_object()
        hoy = date.today()

        context['dias_asignados'] = jornada.dias.all().order_by('numero_dia')
        context['hoy'] = hoy
        
        # Trabajadores vigentes = fecha_fin NULL o >= hoy
        context['trabajadores_vigentes'] = TrabajadorJornada.objects.filter(
            id_jornada=jornada
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
        ).select_related('id_trabajador')

        context['trabajadores_historicos'] = TrabajadorJornada.objects.filter(
            id_jornada=jornada,
            fecha_fin__isnull=False,
            fecha_fin__lt=hoy
        ).select_related('id_trabajador').order_by('-fecha_fin')[:5]

        return context



# =========================================================
#   JORNADAS LABORALES - CRUD 
# =========================================================

@method_decorator([rol_requerido('admin', 'jefe'), requiere_trabajador_y_unidad], name='dispatch')
class JornadaCreateView(LoginRequiredMixin, CreateView):
    """
    Crear nueva jornada laboral
    Acceso: Solo Admin
    """
    model = JornadaLaboral
    form_class = JornadaLaboralForm
    template_name = 'jornadas_laborales/form_jornada.html'
    success_url = reverse_lazy('jornadas:list')

    def form_valid(self, form):
        jornada = form.save(commit=False)
        jornada.created_by = self.request.user
        jornada.save()

        # Guardar días laborales
        for dia in form.cleaned_data['dias']:
            JornadaDias.objects.create(
                id_jornada=jornada,
                numero_dia=int(dia)
            )
        
        messages.success(
            self.request,
            f"Jornada '{jornada.descripcion}' creada exitosamente"
        )
        return redirect(self.success_url)
    
    


@method_decorator([rol_requerido('admin', 'jefe'), requiere_trabajador_y_unidad], name='dispatch')
class JornadaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar jornada laboral existente
    Acceso: Solo Admin
    """
    model = JornadaLaboral
    form_class = JornadaLaboralForm
    template_name = 'jornadas_laborales/form_jornada.html'
    success_url = reverse_lazy('jornadas:list')

    def get_initial(self):
        initial = super().get_initial()
        # Cargar los días existentes de la jornada
        jornada = self.get_object()
        dias_existentes = list(jornada.dias.values_list('numero_dia', flat=True))
        initial['dias'] = [str(d) for d in dias_existentes]
        return initial

    def form_valid(self, form):
        jornada = form.save(commit=False)
        jornada.updated_by = self.request.user
        jornada.save()

        # Actualizar días laborales
        JornadaDias.objects.filter(id_jornada=jornada).delete()
        for dia in form.cleaned_data['dias']:
            JornadaDias.objects.create(
                id_jornada=jornada,
                numero_dia=int(dia)
            )
        
        messages.success(
            self.request,
            f"Jornada '{jornada.descripcion}' actualizada exitosamente"
        )
        return redirect(self.success_url)
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        # Si es jefe → validar que la jornada sea de su unidad
        user = request.user
        if user.perfil.es_jefe():
            unidad_jefe = user.perfil.id_trabajador.id_unidad

            # jornada pertenece a su unidad?
            pertenece = TrabajadorJornada.objects.filter(
                id_jornada=obj,
                id_trabajador__id_unidad=unidad_jefe
            ).exists()

            if not pertenece:
                raise Http404("No puedes acceder a esta jornada")

        return super().dispatch(request, *args, **kwargs)



@method_decorator([rol_requerido('admin', 'jefe'), requiere_trabajador_y_unidad], name='dispatch')
class JornadaDeleteView(LoginRequiredMixin, DeleteView):
    """
    Eliminar jornada laboral
    Acceso: Solo Admin
    """
    model = JornadaLaboral
    template_name = 'jornadas_laborales/confirmar_eliminar_jornada.html'
    success_url = reverse_lazy('jornadas:list')
    
    def delete(self, request, *args, **kwargs):
        jornada = self.get_object()
        
        # Verificar si tiene trabajadores asignados
        if TrabajadorJornada.objects.filter(id_jornada=jornada).exists():
            messages.error(
                request,
                f"No se puede eliminar '{jornada.descripcion}' porque tiene trabajadores asignados"
            )
            return redirect(self.success_url)
        
        try:
            messages.success(
                request,
                f"Jornada '{jornada.descripcion}' eliminada exitosamente"
            )
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(
                request,
                f"No se puede eliminar '{jornada.descripcion}' porque tiene registros relacionados protegidos"
            )
            return redirect(self.success_url)
    
    def post(self, request, *args, **kwargs):
        """Manejo alternativo para formularios POST"""
        return self.delete(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        # Si es jefe → validar que la jornada sea de su unidad
        user = request.user
        if user.perfil.es_jefe():
            unidad_jefe = user.perfil.id_trabajador.id_unidad

            # jornada pertenece a su unidad?
            pertenece = TrabajadorJornada.objects.filter(
                id_jornada=obj,
                id_trabajador__id_unidad=unidad_jefe
            ).exists()

            if not pertenece:
                raise Http404("No puedes acceder a esta jornada")

        return super().dispatch(request, *args, **kwargs)


# =========================================================
#   CALENDARIO LABORAL - LIST
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe', 'trabajador'), name='dispatch')
class CalendarioListView(LoginRequiredMixin, ListView):
    """
    Lista de días del calendario laboral
    Acceso: Todos los roles autenticados
    """
    model = CalendarioLaboral
    template_name = 'jornadas_laborales/calendario/calendario.html'
    context_object_name = 'dias_calendario'
    paginate_by = 20

    def get_queryset(self):
        return CalendarioLaboral.objects.filter(
            Q(es_inhabil=True) | Q(fecha__gte=date.today())
        ).order_by('fecha')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_dias_inhabiles'] = CalendarioLaboral.objects.filter(
            es_inhabil=True
        ).count()
        context['proximos_inhabiles'] = CalendarioLaboral.objects.filter(
            es_inhabil=True,
            fecha__gte=date.today()
        ).order_by('fecha')[:5]
        context['es_admin'] = self.request.user.perfil.es_admin()
        return context


# =========================================================
#   CALENDARIO LABORAL - CRUD (Jefe + Admin)
# =========================================================

@method_decorator(admin_requerido, name='dispatch')
class CalendarioCreateView(LoginRequiredMixin, CreateView):
    """
    Crear día en calendario laboral
    Acceso: Solo Admin
    """
    model = CalendarioLaboral
    form_class = CalendarioLaboralForm
    template_name = 'jornadas_laborales/calendario/form_calendario.html'
    success_url = reverse_lazy('jornadas:calendario')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        messages.success(
            self.request,
            f"Día {obj.fecha.strftime('%d/%m/%Y')} registrado exitosamente"
        )
        return super().form_valid(form)


@method_decorator(admin_requerido, name='dispatch')
class CalendarioUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar día del calendario laboral
    Acceso: Solo Admin
    """
    model = CalendarioLaboral
    form_class = CalendarioLaboralForm
    template_name = 'jornadas_laborales/calendario/form_calendario.html'
    success_url = reverse_lazy('jornadas:calendario')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        obj.save()
        messages.success(
            self.request,
            f"Día {obj.fecha.strftime('%d/%m/%Y')} actualizado exitosamente"
        )
        return super().form_valid(form)


@method_decorator(admin_requerido, name='dispatch')
class CalendarioDeleteView(LoginRequiredMixin, DeleteView):
    """
    Eliminar día del calendario laboral
    Acceso: Solo Admin
    """
    model = CalendarioLaboral
    template_name = 'jornadas_laborales/calendario/confirmar_eliminar_calendario.html'
    success_url = reverse_lazy('jornadas:calendario')
    
    def delete(self, request, *args, **kwargs):
        dia = self.get_object()
        messages.success(
            request,
            f"Día {dia.fecha.strftime('%d/%m/%Y')} eliminado del calendario"
        )
        return super().delete(request, *args, **kwargs)


# =========================================================
#   ASIGNACIONES DE JORNADAS - LIST & CRUD
# =========================================================

@method_decorator(jefe_o_admin_requerido, name='dispatch')
class AsignacionListView(LoginRequiredMixin, ListView):
    """
    Lista de asignaciones de jornadas a trabajadores
    Acceso: Jefe y Admin
    """
    model = TrabajadorJornada
    template_name = 'jornadas_laborales/asignaciones/lista_asignaciones.html'
    context_object_name = 'asignaciones'
    paginate_by = 20

    def get_queryset(self):
        qs = TrabajadorJornada.objects.select_related(
            'id_trabajador', 'id_jornada', 'id_trabajador__id_unidad'
        ).order_by('-fecha_inicio')

        user = self.request.user

        # 🔹 Filtro por unidad del jefe (si no es admin)
        if user.perfil.es_jefe() and not user.perfil.es_admin():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                qs = qs.filter(id_trabajador__id_unidad=unidad)
            else:
                # Si el jefe no tiene trabajador asignado, no ve nada
                qs = TrabajadorJornada.objects.none()
        
        # 🔹 Filtro por unidad (solo para admin)
        unidad_id = self.request.GET.get('unidad')
        if unidad_id and user.perfil.es_admin():
            qs = qs.filter(id_trabajador__id_unidad_id=unidad_id)
        
        # 🔹 Filtro por trabajador (por ID)
        trabajador_id = self.request.GET.get('trabajador')
        if trabajador_id:
            qs = qs.filter(id_trabajador_id=trabajador_id)
        
        # 🔹 Filtro por estado (vigente/finalizada)
        estado = self.request.GET.get('estado')
        if estado == 'vigente':
            qs = qs.filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=timezone.now().date())
            )
        elif estado == 'finalizada':
            qs = qs.filter(
                fecha_fin__lt=timezone.now().date()
            )

        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Filtrar unidades y trabajadores según el rol
        if user.perfil.es_admin():
            context['unidades'] = UnidadAdministrativa.objects.all().order_by('nombre')
            context['trabajadores'] = Trabajador.objects.filter(activo=True).select_related('id_unidad').order_by('nombre', 'apellido_paterno')
        elif user.perfil.es_jefe():
            # Para jefe, solo su unidad y sus trabajadores
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                context['unidades'] = UnidadAdministrativa.objects.filter(id_unidad=unidad.id_unidad)
                context['trabajadores'] = Trabajador.objects.filter(
                    id_unidad=unidad,
                    activo=True
                ).order_by('nombre', 'apellido_paterno')
            else:
                context['unidades'] = UnidadAdministrativa.objects.none()
                context['trabajadores'] = Trabajador.objects.none()
        else:
            context['unidades'] = UnidadAdministrativa.objects.none()
            context['trabajadores'] = Trabajador.objects.none()
        
        return context


@method_decorator(jefe_o_admin_requerido, name='dispatch')
class AsignacionCreateView(LoginRequiredMixin, CreateView):
    """
    Crear asignación de jornada a trabajador
    Acceso: Jefe y Admin
    """
    model = TrabajadorJornada
    form_class = AsignarJornadaForm
    template_name = 'jornadas_laborales/asignaciones/form_asignacion.html'
    success_url = reverse_lazy('jornadas:asignaciones')

    def form_valid(self, form):
        user = self.request.user

        if user.perfil.es_jefe():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                trabajador = form.cleaned_data['id_trabajador']

                if trabajador.id_unidad != unidad:
                    messages.error(self.request, "No puedes asignar jornadas a trabajadores de otra unidad.")
                    return redirect('jornadas:asignaciones')
            else:
                messages.error(self.request, "No tienes un trabajador asignado.")
                return redirect('jornadas:asignaciones')

        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()

        messages.success(
            self.request,
            f"Jornada asignada a {obj.id_trabajador.nombre_completo} exitosamente"
        )
        return super().form_valid(form)
    
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user = self.request.user

        if user.perfil.es_jefe():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                form.fields['id_trabajador'].queryset = Trabajador.objects.filter(
                    id_unidad=unidad,
                    activo=True
                )
                # Filtrar jornadas: las creadas por el jefe o que tengan trabajadores de su unidad
                form.fields['id_jornada'].queryset = JornadaLaboral.objects.filter(
                    Q(created_by=user) |
                    Q(trabajadores_asignados__id_trabajador__id_unidad=unidad)
                ).distinct()
            else:
                form.fields['id_trabajador'].queryset = Trabajador.objects.none()
                form.fields['id_jornada'].queryset = JornadaLaboral.objects.none()
        else:
            # Admin → todos
            form.fields['id_trabajador'].queryset = Trabajador.objects.filter(activo=True)
            form.fields['id_jornada'].queryset = JornadaLaboral.objects.all()

        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Pasar unidades y trabajadores al contexto
        if user.perfil.es_admin():
            context['unidades'] = UnidadAdministrativa.objects.all().order_by('nombre')
            context['todos_trabajadores'] = Trabajador.objects.filter(activo=True).select_related('id_unidad').order_by('id_unidad', 'nombre', 'apellido_paterno')
        elif user.perfil.es_jefe():
            # Para jefe, solo su unidad
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                context['unidades'] = UnidadAdministrativa.objects.filter(id_unidad=unidad.id_unidad)
                context['todos_trabajadores'] = Trabajador.objects.filter(
                    id_unidad=unidad,
                    activo=True
                ).order_by('nombre', 'apellido_paterno')
            else:
                context['unidades'] = UnidadAdministrativa.objects.none()
                context['todos_trabajadores'] = Trabajador.objects.none()
        else:
            context['unidades'] = UnidadAdministrativa.objects.none()
            context['todos_trabajadores'] = Trabajador.objects.none()
        
        # Agrupar jornadas por tipo
        jornadas_agrupadas = {}
        jornadas_queryset = self.get_form().fields['id_jornada'].queryset
        
        for jornada in jornadas_queryset.prefetch_related('dias'):
            tipo_key = jornada.descripcion
            tipo_label = jornada.get_descripcion_display()
            
            if tipo_key not in jornadas_agrupadas:
                jornadas_agrupadas[tipo_key] = {
                    'label': tipo_label,
                    'jornadas': []
                }
            
            jornadas_agrupadas[tipo_key]['jornadas'].append(jornada)
        
        context['jornadas_agrupadas'] = jornadas_agrupadas
        context['tipos_jornada'] = JornadaLaboral.TIPO_JORNADA
        
        return context




@method_decorator(jefe_o_admin_requerido, name='dispatch')
class AsignacionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar asignación de jornada
    Acceso: Jefe y Admin
    """
    model = TrabajadorJornada
    form_class = AsignarJornadaForm
    template_name = 'jornadas_laborales/asignaciones/form_asignacion.html'
    success_url = reverse_lazy('jornadas:asignaciones')

    def form_valid(self, form):
        user = self.request.user

        if user.perfil.es_jefe():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                trabajador = form.cleaned_data['id_trabajador']

                if trabajador.id_unidad != unidad:
                    messages.error(self.request, "No puedes editar asignaciones de un trabajador de otra unidad.")
                    return redirect('jornadas:asignaciones')
            else:
                messages.error(self.request, "No tienes un trabajador asignado.")
                return redirect('jornadas:asignaciones')

        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        obj.save()

        messages.success(
            self.request,
            f"Asignación actualizada para {obj.id_trabajador.nombre_completo}"
        )
        return super().form_valid(form)
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.perfil.es_jefe():
            if request.user.perfil.id_trabajador and request.user.perfil.id_trabajador.id_unidad:
                unidad_jefe = request.user.perfil.id_trabajador.id_unidad
                
                if obj.id_trabajador.id_unidad != unidad_jefe:
                    raise Http404("No puedes modificar esta asignación")
            else:
                raise Http404("No tienes un trabajador asignado")

        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user = self.request.user

        if user.perfil.es_jefe():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                unidad = user.perfil.id_trabajador.id_unidad
                form.fields['id_trabajador'].queryset = Trabajador.objects.filter(
                    id_unidad=unidad,
                    activo=True
                )
                # Filtrar jornadas: las creadas por el jefe o que tengan trabajadores de su unidad
                form.fields['id_jornada'].queryset = JornadaLaboral.objects.filter(
                    Q(created_by=user) |
                    Q(trabajadores_asignados__id_trabajador__id_unidad=unidad)
                ).distinct()
            else:
                form.fields['id_trabajador'].queryset = Trabajador.objects.none()
                form.fields['id_jornada'].queryset = JornadaLaboral.objects.none()
        else:
            form.fields['id_trabajador'].queryset = Trabajador.objects.filter(activo=True)
            form.fields['id_jornada'].queryset = JornadaLaboral.objects.all()

        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Agrupar jornadas por tipo
        jornadas_agrupadas = {}
        jornadas_queryset = self.get_form().fields['id_jornada'].queryset
        
        for jornada in jornadas_queryset.prefetch_related('dias'):
            tipo_key = jornada.descripcion
            tipo_label = jornada.get_descripcion_display()
            
            if tipo_key not in jornadas_agrupadas:
                jornadas_agrupadas[tipo_key] = {
                    'label': tipo_label,
                    'jornadas': []
                }
            
            jornadas_agrupadas[tipo_key]['jornadas'].append(jornada)
        
        context['jornadas_agrupadas'] = jornadas_agrupadas
        context['tipos_jornada'] = JornadaLaboral.TIPO_JORNADA
        
        return context





@method_decorator(jefe_o_admin_requerido, name='dispatch')
class AsignacionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Eliminar asignación de jornada
    Acceso: Jefe y Admin
    """
    model = TrabajadorJornada
    template_name = 'jornadas_laborales/asignaciones/confirmar_eliminar_asignacion.html'
    success_url = reverse_lazy('jornadas:asignaciones')
    
    def delete(self, request, *args, **kwargs):
        asignacion = self.get_object()
        trabajador_nombre = asignacion.id_trabajador.nombre_completo
        messages.success(
            request,
            f"Asignación eliminada para {trabajador_nombre}"
        )
        return super().delete(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.perfil.es_jefe():
            if request.user.perfil.id_trabajador and request.user.perfil.id_trabajador.id_unidad:
                unidad_jefe = request.user.perfil.id_trabajador.id_unidad
                
                if obj.id_trabajador.id_unidad != unidad_jefe:
                    raise Http404("No puedes modificar esta asignación")
            else:
                raise Http404("No tienes un trabajador asignado")

        return super().dispatch(request, *args, **kwargs)



# =========================================================
#   MI JORNADA (Vista para Trabajadores)
# =========================================================

@method_decorator(rol_requerido('trabajador', 'jefe', 'admin'), name='dispatch')
class MiJornadaView(LoginRequiredMixin, TemplateView):
    """
    Vista para que el trabajador vea su jornada asignada
    Acceso: Todos los roles autenticados
    """
    template_name = 'jornadas_laborales/mi_jornada.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        context['hoy'] = hoy

        # Verificar si el usuario tiene un trabajador asociado
        if not hasattr(self.request.user.perfil, 'id_trabajador') or not self.request.user.perfil.id_trabajador:
            messages.warning(
                self.request,
                "No tienes un trabajador asociado. Contacta al administrador."
            )
            context['trabajador'] = None
            context['jornada_asignada'] = None
            return context

        trabajador = self.request.user.perfil.id_trabajador

        # Buscar jornada vigente (fecha_fin NULL o >= hoy)
        jornada_asignada = TrabajadorJornada.objects.select_related(
            'id_jornada'
        ).filter(
            id_trabajador=trabajador
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
        ).first()

        context['trabajador'] = trabajador
        context['jornada_asignada'] = jornada_asignada
        
        if jornada_asignada:
            context['dias_laborales'] = jornada_asignada.id_jornada.dias.all().order_by('numero_dia')
        
        # Todas las jornadas vigentes del trabajador
        context['jornadas_vigentes'] = TrabajadorJornada.objects.select_related(
            'id_jornada'
        ).filter(
            id_trabajador=trabajador
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
        ).order_by('-fecha_inicio')
        
        return context