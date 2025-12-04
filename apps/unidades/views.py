from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.urls import reverse_lazy
from .models import UnidadAdministrativa


class UnidadListView(ListView):
    model = UnidadAdministrativa
    template_name = "unidades/index.html"
    context_object_name = "unidades"


class UnidadCreateView(CreateView):
    model = UnidadAdministrativa
    fields = ['nombre', 'descripcion']
    template_name = "unidades/form.html"
    success_url = reverse_lazy('unidades:lista')


class UnidadUpdateView(UpdateView):
    model = UnidadAdministrativa
    fields = ['nombre', 'descripcion']
    template_name = "unidades/form.html"
    success_url = reverse_lazy('unidades:lista')


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
