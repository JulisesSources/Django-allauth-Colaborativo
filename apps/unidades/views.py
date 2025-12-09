from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from apps.accounts.decorators import admin_requerido, jefe_o_admin_requerido
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import UnidadAdministrativa

@method_decorator([login_required, admin_requerido], name='dispatch')
class UnidadListView(ListView):
    model = UnidadAdministrativa
    template_name = "unidades/lista_unidades_administrativas.html"
    context_object_name = "unidades"

@method_decorator([login_required, admin_requerido], name='dispatch')
class UnidadCreateView(CreateView):
    model = UnidadAdministrativa
    fields = ['nombre', 'descripcion']
    template_name = "unidades/formulario_unidad_administrativa.html"
    success_url = reverse_lazy('unidades:lista')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

@method_decorator([login_required, admin_requerido], name='dispatch')
class UnidadUpdateView(UpdateView):
    model = UnidadAdministrativa
    fields = ['nombre', 'descripcion']
    template_name = "unidades/formulario_unidad_administrativa.html"
    success_url = reverse_lazy('unidades:lista')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


@method_decorator([admin_requerido], name='dispatch')
class UnidadDeleteView(DeleteView):
    model = UnidadAdministrativa
    template_name = "unidades/confirmar_eliminar_unidad_administrativa.html"
    success_url = reverse_lazy("unidades:lista")

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            success_url = self.get_success_url()
            self.object.delete()
            messages.success(request, f'La unidad administrativa "{self.object.nombre}" ha sido eliminada correctamente.')
            return redirect(success_url)
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar la unidad administrativa "{self.object.nombre}" porque tiene trabajadores relacionados. Primero debes reasignar o eliminar los trabajadores asociados.'
            )
            return redirect('unidades:lista')
