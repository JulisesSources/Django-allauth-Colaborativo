from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Trabajador

class TrabajadorListView(ListView):
    model = Trabajador
    template_name = 'trabajadores/index.html'
    context_object_name = 'trabajadores'

    def get_queryset(self):
        return Trabajador.objects.select_related('id_unidad', 'id_puesto', 'id_tipo_nombramiento').all()


class TrabajadorCreateView(CreateView):
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


class TrabajadorUpdateView(UpdateView):
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


class TrabajadorDeleteView(DeleteView):
    model = Trabajador
    template_name = 'trabajadores/eliminar.html'
    success_url = reverse_lazy('trabajadores:index')
