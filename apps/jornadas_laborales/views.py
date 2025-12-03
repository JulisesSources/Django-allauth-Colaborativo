from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import JornadaLaboral, CalendarioLaboral, TrabajadorJornada
from django.db.models import Count, Q
from datetime import date


class JornadaListView(ListView):
    """
    Vista para listar todas las jornadas laborales
    """
    model = JornadaLaboral
    template_name = 'jornadas_laborales/lista_jornadas.html'
    context_object_name = 'jornadas'
    paginate_by = 10
    
    def get_queryset(self):
        """Obtener jornadas con conteo de días y trabajadores asignados"""
        queryset = JornadaLaboral.objects.prefetch_related('dias').annotate(
            num_dias=Count('dias', distinct=True),
            num_trabajadores=Count('trabajadores_asignados', distinct=True)
        )
        return queryset.order_by('descripcion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_jornadas'] = JornadaLaboral.objects.count()
        return context


class JornadaDetailView(DetailView):
    """
    Vista para ver el detalle de una jornada laboral
    """
    model = JornadaLaboral
    template_name = 'jornadas_laborales/detalle_jornada.html'
    context_object_name = 'jornada'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jornada = self.get_object()
        
        # Obtener días asignados ordenados
        context['dias_asignados'] = jornada.dias.all().order_by('numero_dia')
        
        # Obtener trabajadores con esta jornada vigente
        context['trabajadores_vigentes'] = TrabajadorJornada.objects.filter(
            id_jornada=jornada,
            fecha_fin__isnull=True
        ).select_related('id_trabajador')
        
        # Obtener trabajadores con esta jornada histórica
        context['trabajadores_historicos'] = TrabajadorJornada.objects.filter(
            id_jornada=jornada,
            fecha_fin__isnull=False
        ).select_related('id_trabajador').order_by('-fecha_fin')[:5]
        
        return context


class CalendarioListView(ListView):
    """
    Vista para ver el calendario laboral (días inhábiles)
    """
    model = CalendarioLaboral
    template_name = 'jornadas_laborales/calendario.html'
    context_object_name = 'dias_calendario'
    paginate_by = 20
    
    def get_queryset(self):
        """Obtener días del calendario ordenados por fecha"""
        # Filtrar solo días inhábiles o próximos eventos
        queryset = CalendarioLaboral.objects.filter(
            Q(es_inhabil=True) | Q(fecha__gte=date.today())
        ).order_by('fecha')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_dias_inhabiles'] = CalendarioLaboral.objects.filter(es_inhabil=True).count()
        context['proximos_inhabiles'] = CalendarioLaboral.objects.filter(
            es_inhabil=True,
            fecha__gte=date.today()
        ).order_by('fecha')[:5]
        return context