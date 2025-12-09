from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, Sum
from datetime import datetime, timedelta
from apps.asistencias.models import RegistroAsistencia
from apps.trabajadores.models import Trabajador
from apps.unidades.models import UnidadAdministrativa
import csv


@login_required
def index(request):
    """Vista principal de reportes"""
    # Verificar permisos (solo admin y jefes)
    if not (request.user.perfil.es_admin() or request.user.perfil.es_jefe()):
        return HttpResponseForbidden("No tienes permiso para acceder a esta página")
    
    # Obtener unidades según el rol
    if request.user.perfil.es_admin():
        unidades = UnidadAdministrativa.objects.all()
        trabajadores = Trabajador.objects.filter(activo=True)
    else:
        # Jefe solo ve su unidad
        unidades = UnidadAdministrativa.objects.filter(
            id_unidad=request.user.perfil.id_trabajador.id_unidad.id_unidad
        )
        trabajadores = Trabajador.objects.filter(
            id_unidad=request.user.perfil.id_trabajador.id_unidad,
            activo=True
        )
    
    context = {
        'unidades': unidades,
        'trabajadores': trabajadores,
    }
    
    return render(request, 'reportes/index.html', context)


@login_required
def reporte_asistencias(request):
    """Generar reporte de asistencias con filtros"""
    # Verificar permisos
    if not (request.user.perfil.es_admin() or request.user.perfil.es_jefe()):
        return HttpResponseForbidden("No tienes permiso para acceder a esta página")
    
    # Obtener parámetros de filtrado
    trabajador_id = request.GET.get('trabajador')
    unidad_id = request.GET.get('unidad')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Fechas por defecto (último mes)
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    # Query base de asistencias
    asistencias = RegistroAsistencia.objects.select_related(
        'id_trabajador',
        'id_trabajador__id_unidad',
        'id_trabajador__id_puesto'
    ).filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    )
    
    # Aplicar filtro de unidad según rol
    if request.user.perfil.es_jefe() and request.user.perfil.id_trabajador:
        asistencias = asistencias.filter(
            id_trabajador__id_unidad=request.user.perfil.id_trabajador.id_unidad
        )
    
    # Aplicar filtros adicionales
    if trabajador_id:
        asistencias = asistencias.filter(id_trabajador_id=trabajador_id)
    
    if unidad_id:
        asistencias = asistencias.filter(id_trabajador__id_unidad_id=unidad_id)
    
    # Estadísticas
    total_registros = asistencias.count()
    asistencias_normales = asistencias.filter(estatus='ASI').count()
    retardos = asistencias.filter(estatus='RET').count()
    faltas = asistencias.filter(estatus='FAL').count()
    justificadas = asistencias.filter(estatus='JUS').count()
    
    # Porcentajes
    porcentaje_asistencia = round((asistencias_normales / total_registros * 100) if total_registros > 0 else 0, 1)
    porcentaje_retardos = round((retardos / total_registros * 100) if total_registros > 0 else 0, 1)
    porcentaje_faltas = round((faltas / total_registros * 100) if total_registros > 0 else 0, 1)
    
    # Obtener trabajadores y unidades para filtros
    if request.user.perfil.es_admin():
        unidades = UnidadAdministrativa.objects.all()
        trabajadores = Trabajador.objects.filter(activo=True)
    else:
        unidades = UnidadAdministrativa.objects.filter(
            id_unidad=request.user.perfil.id_trabajador.id_unidad.id_unidad
        )
        trabajadores = Trabajador.objects.filter(
            id_unidad=request.user.perfil.id_trabajador.id_unidad,
            activo=True
        )
    
    context = {
        'asistencias': asistencias.order_by('-fecha', 'id_trabajador__nombre'),
        'total_registros': total_registros,
        'asistencias_normales': asistencias_normales,
        'retardos': retardos,
        'faltas': faltas,
        'justificadas': justificadas,
        'porcentaje_asistencia': porcentaje_asistencia,
        'porcentaje_retardos': porcentaje_retardos,
        'porcentaje_faltas': porcentaje_faltas,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'trabajador_seleccionado': trabajador_id,
        'unidad_seleccionada': unidad_id,
        'unidades': unidades,
        'trabajadores': trabajadores,
    }
    
    return render(request, 'reportes/reporte_asistencias.html', context)


@login_required
def exportar_asistencias_csv(request):
    """Exportar reporte de asistencias a CSV"""
    # Verificar permisos
    if not (request.user.perfil.es_admin() or request.user.perfil.es_jefe()):
        return HttpResponseForbidden("No tienes permiso para exportar reportes")
    
    # Obtener los mismos parámetros que el reporte
    trabajador_id = request.GET.get('trabajador')
    unidad_id = request.GET.get('unidad')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Fechas por defecto
    if not fecha_inicio:
        fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not fecha_fin:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    # Query de asistencias
    asistencias = RegistroAsistencia.objects.select_related(
        'id_trabajador',
        'id_trabajador__id_unidad',
        'id_trabajador__id_puesto'
    ).filter(
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    )
    
    # Aplicar filtro de unidad según rol
    if request.user.perfil.es_jefe() and request.user.perfil.id_trabajador:
        asistencias = asistencias.filter(
            id_trabajador__id_unidad=request.user.perfil.id_trabajador.id_unidad
        )
    
    # Aplicar filtros adicionales
    if trabajador_id:
        asistencias = asistencias.filter(id_trabajador_id=trabajador_id)
    
    if unidad_id:
        asistencias = asistencias.filter(id_trabajador__id_unidad_id=unidad_id)
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_asistencias_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Agregar BOM para Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # Encabezados
    writer.writerow([
        'Fecha',
        'Trabajador',
        'Número de Empleado',
        'Unidad Administrativa',
        'Puesto',
        'Hora Entrada',
        'Hora Salida',
        'Estatus',
        'Observaciones'
    ])
    
    # Datos
    for asistencia in asistencias.order_by('-fecha', 'id_trabajador__nombre'):
        writer.writerow([
            asistencia.fecha.strftime('%d/%m/%Y'),
            asistencia.id_trabajador.nombre_completo,
            asistencia.id_trabajador.numero_empleado,
            asistencia.id_trabajador.id_unidad.nombre,
            asistencia.id_trabajador.id_puesto.nombre_puesto,
            asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else '',
            asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else '',
            asistencia.get_estatus_display(),
            ''
        ])
    
    return response