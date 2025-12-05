from datetime import date
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import Http404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)

from .models import (
    JornadaLaboral,
    CalendarioLaboral,
    TrabajadorJornada,
    JornadaDias
)

from .forms import (
    JornadaLaboralForm,
    CalendarioLaboralForm,
    AsignarJornadaForm
)

# Decoradores de roles
from apps.accounts.decorators import (
    rol_requerido,
    admin_requerido,
    jefe_o_admin_requerido
)


# =========================================================
#   JORNADAS LABORALES - LIST & DETAIL
# =========================================================

@method_decorator(rol_requerido('admin', 'jefe'), name='dispatch')
class JornadaListView(LoginRequiredMixin, ListView):
    """
    Lista de jornadas laborales
    Acceso: Admin y Jefe
    """
    model = JornadaLaboral
    template_name = 'jornadas_laborales/lista_jornadas.html'
    context_object_name = 'jornadas'
    paginate_by = 10

    def get_queryset(self):
        return JornadaLaboral.objects.prefetch_related('dias').annotate(
            num_dias=Count('dias', distinct=True),
            num_trabajadores=Count('trabajadores_asignados', distinct=True)
        ).order_by('descripcion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_jornadas'] = JornadaLaboral.objects.count()
        return context


@method_decorator(rol_requerido('admin', 'jefe'), name='dispatch')
class JornadaDetailView(LoginRequiredMixin, DetailView):
    """
    Detalle de una jornada laboral
    Acceso: Admin y Jefe
    """
    model = JornadaLaboral
    template_name = 'jornadas_laborales/detalle_jornada.html'
    context_object_name = 'jornada'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jornada = self.get_object()

        context['dias_asignados'] = jornada.dias.all().order_by('numero_dia')
        context['trabajadores_vigentes'] = TrabajadorJornada.objects.filter(
            id_jornada=jornada,
            fecha_fin__isnull=True
        ).select_related('id_trabajador')

        context['trabajadores_historicos'] = TrabajadorJornada.objects.filter(
            id_jornada=jornada,
            fecha_fin__isnull=False
        ).select_related('id_trabajador').order_by('-fecha_fin')[:5]

        return context


# =========================================================
#   JORNADAS LABORALES - CRUD (Solo Admin)
# =========================================================

@method_decorator(admin_requerido, name='dispatch')
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


@method_decorator(admin_requerido, name='dispatch')
class JornadaUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar jornada laboral existente
    Acceso: Solo Admin
    """
    model = JornadaLaboral
    form_class = JornadaLaboralForm
    template_name = 'jornadas_laborales/form_jornada.html'
    success_url = reverse_lazy('jornadas:list')

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


@method_decorator(admin_requerido, name='dispatch')
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
        
        messages.success(
            request,
            f"Jornada '{jornada.descripcion}' eliminada exitosamente"
        )
        return super().delete(request, *args, **kwargs)


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
        return context


# =========================================================
#   CALENDARIO LABORAL - CRUD (Jefe + Admin)
# =========================================================

@method_decorator(jefe_o_admin_requerido, name='dispatch')
class CalendarioCreateView(LoginRequiredMixin, CreateView):
    """
    Crear día en calendario laboral
    Acceso: Jefe y Admin
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


@method_decorator(jefe_o_admin_requerido, name='dispatch')
class CalendarioUpdateView(LoginRequiredMixin, UpdateView):
    """
    Editar día del calendario laboral
    Acceso: Jefe y Admin
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


@method_decorator(jefe_o_admin_requerido, name='dispatch')
class CalendarioDeleteView(LoginRequiredMixin, DeleteView):
    """
    Eliminar día del calendario laboral
    Acceso: Jefe y Admin
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
        return TrabajadorJornada.objects.select_related(
            'id_trabajador', 'id_jornada'
        ).order_by('-fecha_inicio')


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
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.save()
        messages.success(
            self.request,
            f"Jornada asignada a {obj.id_trabajador.nombre_completo} exitosamente"
        )
        return super().form_valid(form)


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
        obj = form.save(commit=False)
        obj.updated_by = self.request.user
        obj.save()
        messages.success(
            self.request,
            f"Asignación actualizada para {obj.id_trabajador.nombre_completo}"
        )
        return super().form_valid(form)


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

        # Buscar jornada activa
        jornada_asignada = TrabajadorJornada.objects.select_related(
            'id_jornada'
        ).filter(
            id_trabajador=trabajador,
            fecha_fin__isnull=True
        ).first()

        context['trabajador'] = trabajador
        context['jornada_asignada'] = jornada_asignada
        
        if jornada_asignada:
            context['dias_laborales'] = jornada_asignada.id_jornada.dias.all().order_by('numero_dia')
        
        return context