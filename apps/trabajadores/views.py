from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.trabajadores.forms import PuestoFormSet
from .models import Puesto, TipoNombramiento, Trabajador
from apps.unidades.models import UnidadAdministrativa
from django.db import models
from django.views.generic import ListView
from .models import Trabajador, Puesto, TipoNombramiento
from django.utils.decorators import method_decorator
from apps.accounts.decorators import jefe_o_admin_requerido
from django.contrib.auth.decorators import login_required

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class TrabajadorListView(ListView):
    model = Trabajador
    template_name = 'trabajadores/index.html'
    context_object_name = 'trabajadores'

    def get_queryset(self):
        queryset = Trabajador.objects.select_related(
            'id_unidad', 'id_puesto', 'id_tipo_nombramiento'
        ).all()

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

        context["unidades"] = UnidadAdministrativa.objects.all()
        context["puestos"] = Puesto.objects.all()
        context["nombramientos"] = TipoNombramiento.objects.all()
        context["values"] = self.request.GET  # conserva valores del formulario

        return context

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
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
    template_name = 'trabajadores/form.html'
    success_url = reverse_lazy('trabajadores:index')
    
    def form_valid(self, form):
        # Auditoría
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
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
    template_name = 'trabajadores/form.html'
    success_url = reverse_lazy('trabajadores:index')

    def form_valid(self, form):
        # Auditoría
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
  
@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')  
class TrabajadorDeleteView(DeleteView):
    model = Trabajador
    template_name = 'trabajadores/eliminar.html'
    success_url = reverse_lazy('trabajadores:index')
    
# -- PUESTOS --

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class PuestoListView(ListView):
    model = Puesto
    template_name = 'trabajadores/puestos/puestos_index.html'
    context_object_name = 'puestos'

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class PuestoCreateView(CreateView):
    model = Puesto
    fields = ['nombre_puesto', 'nivel']
    template_name = 'trabajadores/puestos/puestos_form.html'
    success_url = reverse_lazy('trabajadores:puestos-lista')

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class PuestoUpdateView(UpdateView):
    model = Puesto
    fields = ['nombre_puesto', 'nivel']
    template_name = 'trabajadores/puestos/puestos_form.html'
    success_url = reverse_lazy('trabajadores:puestos-lista')

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class PuestoDeleteView(DeleteView):
    model = Puesto
    template_name = 'trabajadores/eliminar.html'
    success_url = reverse_lazy("trabajadores:puestos-lista")
    
# -- NOMBRAMIENTOS --

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class NombramientoListView(ListView):
    model = TipoNombramiento
    template_name = "trabajadores/nombramientos/nombramientos_list.html"
    context_object_name = "nombramientos"

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class NombramientoCreateView(CreateView):
    model = TipoNombramiento
    fields = ['descripcion']
    template_name = "trabajadores/nombramientos/nombramientos_form.html"
    success_url = reverse_lazy('trabajadores:nombramientos-lista')

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class NombramientoUpdateView(UpdateView):
    model = TipoNombramiento
    fields = ['descripcion']
    template_name = "trabajadores/nombramientos/nombramientos_form.html"
    success_url = reverse_lazy('trabajadores:nombramientos-lista')

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class NombramientoDeleteView(DeleteView):
    model = TipoNombramiento
    template_name = "trabajadores/eliminar.html"
    success_url = reverse_lazy("trabajadores:nombramientos-lista")
    