from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from apps.accounts.decorators import admin_requerido, jefe_o_admin_requerido
from django.contrib.auth.decorators import login_required
from .models import UnidadAdministrativa

@method_decorator([login_required, jefe_o_admin_requerido], name='dispatch')
class UnidadListView(ListView):
    model = UnidadAdministrativa
    template_name = "unidades/index.html"
    context_object_name = "unidades"

@method_decorator([login_required, admin_requerido], name='dispatch')
class UnidadCreateView(CreateView):
    model = UnidadAdministrativa
    fields = ['nombre', 'descripcion']
    template_name = "unidades/form.html"
    success_url = reverse_lazy('unidades:lista')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)

@method_decorator([login_required, admin_requerido], name='dispatch')
class UnidadUpdateView(UpdateView):
    model = UnidadAdministrativa
    fields = ['nombre', 'descripcion']
    template_name = "unidades/form.html"
    success_url = reverse_lazy('unidades:lista')

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


@method_decorator([admin_requerido], name='dispatch')
class UnidadDeleteView(DeleteView):
    model = UnidadAdministrativa
    template_name = "unidades/eliminar.html"
    success_url = reverse_lazy("unidades:lista")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                "No puedes eliminar esta unidad porque tiene trabajadores relacionados."
            )
            return self.render_to_response(self.get_context_data())
