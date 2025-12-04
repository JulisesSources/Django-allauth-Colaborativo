from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count
from datetime import date, datetime, timedelta
from .models import RegistroAsistencia
from .forms import RegistroAsistenciaForm, RegistroRapidoForm, FiltroAsistenciaForm
from apps.trabajadores.models import Trabajador
from .utils import (
    calcular_estatus_asistencia,
    obtener_resumen_asistencia_trabajador,
    trabajador_debe_asistir
)


class AsistenciaListView(ListView):
    """
    Vista para listar registros de asistencia con filtros
    """
    model = RegistroAsistencia
    template_name = 'asistencias/lista_asistencias.html'
    context_object_name = 'registros'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = RegistroAsistencia.objects.select_related('id_trabajador').order_by('-fecha', 'id_trabajador')
        
        # Aplicar filtros
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
        
        # Si no hay filtros, mostrar solo los últimos 7 días
        if not any([fecha_inicio, fecha_fin, estatus, trabajador_id]):
            hace_7_dias = date.today() - timedelta(days=7)
            queryset = queryset.filter(fecha__gte=hace_7_dias)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formulario de filtros
        context['filtro_form'] = FiltroAsistenciaForm(self.request.GET or None)
        
        # Estadísticas del día
        hoy = date.today()
        context['fecha_actual'] = hoy
        context['asistencias_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy, estatus='ASI').count()
        context['retardos_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy, estatus='RET').count()
        context['faltas_hoy'] = RegistroAsistencia.objects.filter(fecha=hoy, estatus='FAL').count()
        
        return context


class RegistroRapidoView(FormView):
    """
    Vista para registro rápido de entrada con número de empleado
    """
    template_name = 'asistencias/registro_rapido.html'
    form_class = RegistroRapidoForm
    success_url = reverse_lazy('asistencias:registro_rapido')
    
    def form_valid(self, form):
        trabajador = form.cleaned_data['numero_empleado']
        hoy = date.today()
        hora_actual = datetime.now().time()
        
        # Verificar si ya existe registro hoy
        registro_existente = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha=hoy
        ).first()
        
        if registro_existente:
            if not registro_existente.hora_entrada:
                # Registrar entrada
                registro_existente.hora_entrada = hora_actual
                registro_existente.calcular_estatus_automatico()
                registro_existente.save()
                messages.success(
                    self.request,
                    f"✅ Entrada registrada: {trabajador.nombre_completo} a las {hora_actual.strftime('%H:%M')}"
                )
            elif not registro_existente.hora_salida:
                # Registrar salida
                registro_existente.hora_salida = hora_actual
                registro_existente.save()
                messages.success(
                    self.request,
                    f"✅ Salida registrada: {trabajador.nombre_completo} a las {hora_actual.strftime('%H:%M')}"
                )
            else:
                messages.warning(
                    self.request,
                    f"⚠️ Ya hay registro completo para {trabajador.nombre_completo} hoy"
                )
        else:
            # Crear nuevo registro
            estatus = calcular_estatus_asistencia(trabajador, hoy, hora_actual)
            registro = RegistroAsistencia.objects.create(
                id_trabajador=trabajador,
                fecha=hoy,
                hora_entrada=hora_actual,
                estatus=estatus
            )
            
            if estatus == 'RET':
                messages.warning(
                    self.request,
                    f"🟡 Retardo registrado: {trabajador.nombre_completo} - {registro.minutos_retardo} minutos"
                )
            else:
                messages.success(
                    self.request,
                    f"✅ Asistencia registrada: {trabajador.nombre_completo}"
                )
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fecha_actual'] = date.today()
        context['hora_actual'] = datetime.now().strftime('%H:%M:%S')
        
        # Últimos 5 registros de hoy
        context['ultimos_registros'] = RegistroAsistencia.objects.filter(
            fecha=date.today()
        ).select_related('id_trabajador').order_by('-created_at')[:5]
        
        return context


class RegistroAsistenciaCreateView(CreateView):
    """
    Vista para registro completo de asistencia
    """
    model = RegistroAsistencia
    form_class = RegistroAsistenciaForm
    template_name = 'asistencias/registrar_asistencia.html'
    success_url = reverse_lazy('asistencias:lista')
    
    def form_valid(self, form):
        # Calcular estatus automáticamente
        registro = form.save(commit=False)
        registro.calcular_estatus_automatico()
        registro.save()
        
        messages.success(
            self.request,
            f"✅ Registro de asistencia creado: {registro.id_trabajador.nombre_completo} - {registro.get_estatus_display()}"
        )
        return super().form_valid(form)


class AsistenciaDetailView(DetailView):
    """
    Vista para ver detalle de un registro de asistencia
    """
    model = RegistroAsistencia
    template_name = 'asistencias/detalle_asistencia.html'
    context_object_name = 'registro'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro = self.get_object()
        
        # Información adicional
        debe_asistir, razon = trabajador_debe_asistir(
            registro.id_trabajador,
            registro.fecha
        )
        context['debe_asistir'] = debe_asistir
        context['razon'] = razon
        
        return context


class ResumenTrabajadorView(DetailView):
    """
    Vista para ver resumen de asistencias de un trabajador
    """
    model = Trabajador
    template_name = 'asistencias/resumen_trabajador.html'
    context_object_name = 'trabajador'
    pk_url_kwarg = 'trabajador_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trabajador = self.get_object()
        
        # Rango de fechas (último mes por defecto)
        fecha_fin = date.today()
        fecha_inicio = fecha_fin - timedelta(days=30)
        
        # Permitir filtro personalizado
        if self.request.GET.get('fecha_inicio'):
            fecha_inicio = datetime.strptime(self.request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
        if self.request.GET.get('fecha_fin'):
            fecha_fin = datetime.strptime(self.request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        
        # Obtener resumen
        resumen = obtener_resumen_asistencia_trabajador(trabajador, fecha_inicio, fecha_fin)
        context['resumen'] = resumen
        context['fecha_inicio'] = fecha_inicio
        context['fecha_fin'] = fecha_fin
        
        # Registros del periodo
        context['registros'] = RegistroAsistencia.objects.filter(
            id_trabajador=trabajador,
            fecha__range=[fecha_inicio, fecha_fin]
        ).order_by('-fecha')
        
        return context