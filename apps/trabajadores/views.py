from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.trabajadores.forms import PuestoFormSet
from .models import Puesto, TipoNombramiento, Trabajador
from apps.unidades.models import UnidadAdministrativa
from django.db import models
from django.views.generic import ListView
from .models import Trabajador, Puesto, TipoNombramiento
from django.utils.decorators import method_decorator
from apps.accounts.decorators import jefe_o_admin_requerido, admin_requerido
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db.models.deletion import ProtectedError

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class TrabajadorListView(ListView):
    model = Trabajador
    template_name = 'trabajadores/lista_trabajadores.html'
    context_object_name = 'trabajadores'

    def get_queryset(self):
        queryset = Trabajador.objects.select_related(
            'id_unidad', 'id_puesto', 'id_tipo_nombramiento'
        ).all()

        user = self.request.user
        
        # 🔹 Si es jefe → filtrar solo trabajadores de su unidad
        if user.perfil.es_jefe():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                queryset = queryset.filter(id_unidad=user.perfil.id_trabajador.id_unidad)
            else:
                # Si el jefe no tiene trabajador asignado, no ve nada
                queryset = Trabajador.objects.none()

        # ---- FILTRO POR NOMBRE ----
        nombre = self.request.GET.get('nombre', '')
        if nombre:
            queryset = queryset.filter(
                models.Q(nombre__icontains=nombre) |
                models.Q(apellido_paterno__icontains=nombre) |
                models.Q(apellido_materno__icontains=nombre)
            )

        # ---- FILTRO POR UNIDAD ----
        unidad = self.request.GET.get('unidad', '')
        if unidad:
            queryset = queryset.filter(id_unidad__id_unidad=unidad)

        # ---- FILTRO POR PUESTO ----
        puesto = self.request.GET.get('puesto', '')
        if puesto:
            queryset = queryset.filter(id_puesto__id_puesto=puesto)

        # ---- FILTRO POR TIPO DE NOMBRAMIENTO ----
        nombramiento = self.request.GET.get('nombramiento', '')
        if nombramiento:
            queryset = queryset.filter(id_tipo_nombramiento__id_tipo_nombramiento=nombramiento)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        
        # 🔹 Si es jefe → solo su unidad en filtros
        if user.perfil.es_jefe() and user.perfil.id_trabajador:
            context["unidades"] = UnidadAdministrativa.objects.filter(
                id_unidad=user.perfil.id_trabajador.id_unidad.id_unidad
            )
        else:
            # Admin ve todas las unidades
            context["unidades"] = UnidadAdministrativa.objects.all()
        
        context["puestos"] = Puesto.objects.all()
        context["nombramientos"] = TipoNombramiento.objects.all()
        context["values"] = self.request.GET  # conserva valores del formulario

        return context

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class TrabajadorDetailView(DetailView):
    model = Trabajador
    template_name = 'trabajadores/detalle_trabajador.html'
    context_object_name = 'trabajador'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # 🔹 Si es jefe → solo puede ver trabajadores de su unidad
        if user.perfil.es_jefe():
            if user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
                queryset = queryset.filter(id_unidad=user.perfil.id_trabajador.id_unidad)
            else:
                queryset = Trabajador.objects.none()
        
        return queryset

@method_decorator([login_required, admin_requerido], name='dispatch')
class TrabajadorCreateView(LoginRequiredMixin, CreateView):
    model = Trabajador
    fields = [
        'numero_empleado',
        'nombre',
        'apellido_paterno',
        'apellido_materno',
        'rfc',
        'curp',
        'id_unidad',
        'id_puesto',
        'id_tipo_nombramiento',
        'activo',
    ]
    template_name = 'trabajadores/formulario_trabajador.html'
    success_url = reverse_lazy('trabajadores:index')
    
    def form_valid(self, form):
        # Auditoría
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

@method_decorator([login_required, admin_requerido], name='dispatch')
class TrabajadorUpdateView(LoginRequiredMixin, UpdateView):
    model = Trabajador
    fields = [
        'numero_empleado',
        'nombre',
        'apellido_paterno',
        'apellido_materno',
        'rfc',
        'curp',
        'id_unidad',
        'id_puesto',
        'id_tipo_nombramiento',
        'activo',
    ]
    template_name = 'trabajadores/formulario_trabajador.html'
    success_url = reverse_lazy('trabajadores:index')
    
    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        user = self.request.user
        
        # 🔹 Si es jefe, pre-seleccionar su unidad y deshabilitarla
        if user.perfil.es_jefe() and user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
            unidad = user.perfil.id_trabajador.id_unidad
            form.fields['id_unidad'].queryset = UnidadAdministrativa.objects.filter(id_unidad=unidad.id_unidad)
            form.fields['id_unidad'].widget.attrs['disabled'] = True
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Pasar flag al template para saber si es jefe
        context['es_jefe'] = user.perfil.es_jefe()
        
        return context

    def form_valid(self, form):
        user = self.request.user
        
        # 🔹 Si es jefe, forzar la unidad (por si intentan manipular el HTML)
        if user.perfil.es_jefe() and user.perfil.id_trabajador and user.perfil.id_trabajador.id_unidad:
            form.instance.id_unidad = user.perfil.id_trabajador.id_unidad
        
        # Auditoría
        form.instance.updated_by = user
        return super().form_valid(form)

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class TrabajadorToggleActivoView(View):
    """Vista para activar/desactivar un trabajador"""
    
    def post(self, request, pk):
        trabajador = get_object_or_404(Trabajador, pk=pk)
        
        # Cambiar el estado activo
        trabajador.activo = not trabajador.activo
        trabajador.updated_by = request.user
        trabajador.save()
        
        # Mensaje de éxito
        if trabajador.activo:
            messages.success(request, f'El trabajador {trabajador.nombre} {trabajador.apellido_paterno} ha sido activado correctamente.')
        else:
            messages.warning(request, f'El trabajador {trabajador.nombre} {trabajador.apellido_paterno} ha sido desactivado.')
        
        return redirect('trabajadores:index')
  
@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')  
class TrabajadorDeleteView(DeleteView):
    model = Trabajador
    template_name = 'trabajadores/confirmar_eliminar_trabajador.html'
    success_url = reverse_lazy('trabajadores:index')
    
# -- PUESTOS --

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class PuestoListView(ListView):
    model = Puesto
    template_name = 'trabajadores/puestos/lista_puestos.html'
    context_object_name = 'puestos'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['es_admin'] = self.request.user.perfil.es_admin()
        return context

@method_decorator([login_required, admin_requerido], name='dispatch')
class PuestoCreateView(CreateView):
    model = Puesto
    fields = ['nombre_puesto', 'nivel']
    template_name = 'trabajadores/puestos/formulario_puesto.html'
    success_url = reverse_lazy('trabajadores:puestos-lista')

@method_decorator([login_required, admin_requerido], name='dispatch')
class PuestoUpdateView(UpdateView):
    model = Puesto
    fields = ['nombre_puesto', 'nivel']
    template_name = 'trabajadores/puestos/formulario_puesto.html'
    success_url = reverse_lazy('trabajadores:puestos-lista')

@method_decorator([login_required, admin_requerido], name='dispatch')
class PuestoDeleteView(DeleteView):
    model = Puesto
    template_name = 'trabajadores/puestos/confirmar_eliminar_puesto.html'
    success_url = reverse_lazy("trabajadores:puestos-lista")
    
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            puesto_nombre = self.object.nombre_puesto
            self.object.delete()
            messages.success(request, f'El puesto "{puesto_nombre}" ha sido eliminado correctamente.')
            return redirect(success_url)
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar el puesto "{self.object.nombre_puesto}" porque tiene trabajadores relacionados. Primero debes reasignar los trabajadores a otro puesto.'
            )
            return redirect('trabajadores:puestos-lista')
    
# -- NOMBRAMIENTOS --

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class NombramientoListView(ListView):
    model = TipoNombramiento
    template_name = "trabajadores/nombramientos/lista_nombramientos.html"
    context_object_name = "nombramientos"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['es_admin'] = self.request.user.perfil.es_admin()
        return context

@method_decorator([login_required, admin_requerido], name='dispatch')
class NombramientoCreateView(CreateView):
    model = TipoNombramiento
    fields = ['descripcion']
    template_name = "trabajadores/nombramientos/formulario_nombramiento.html"
    success_url = reverse_lazy('trabajadores:nombramientos-lista')

@method_decorator([login_required, admin_requerido], name='dispatch')
class NombramientoUpdateView(UpdateView):
    model = TipoNombramiento
    fields = ['descripcion']
    template_name = "trabajadores/nombramientos/formulario_nombramiento.html"
    success_url = reverse_lazy('trabajadores:nombramientos-lista')

@method_decorator([login_required, admin_requerido], name='dispatch')
class NombramientoDeleteView(DeleteView):
    model = TipoNombramiento
    template_name = "trabajadores/nombramientos/confirmar_eliminar_nombramiento.html"
    success_url = reverse_lazy("trabajadores:nombramientos-lista")
    
    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            nombramiento_descripcion = self.object.descripcion
            self.object.delete()
            messages.success(request, f'El tipo de nombramiento "{nombramiento_descripcion}" ha sido eliminado correctamente.')
            return redirect(success_url)
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar el tipo de nombramiento "{self.object.descripcion}" porque tiene trabajadores relacionados. Primero debes reasignar los trabajadores a otro tipo de nombramiento.'
            )
            return redirect('trabajadores:nombramientos-lista')
    