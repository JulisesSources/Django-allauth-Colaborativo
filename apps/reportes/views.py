from django.shortcuts import render
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Value
from django.db.models.functions import TruncMonth, Concat
from datetime import datetime, timedelta
from apps.asistencias.models import RegistroAsistencia
from apps.trabajadores.models import Trabajador
from apps.unidades.models import UnidadAdministrativa
import csv

@login_required
def index(request):
    """Vista principal de reportes - Solo administradores"""
    # Verificar permisos (solo admin)
    if not request.user.perfil.es_admin():
        return HttpResponseForbidden("No tienes permiso para acceder a esta página")
    
    # Obtener todas las unidades y trabajadores (solo admin puede acceder)
    unidades = UnidadAdministrativa.objects.all()
    trabajadores = Trabajador.objects.filter(activo=True)
    
    context = {
        'unidades': unidades,
        'trabajadores': trabajadores,
    }
    
    return render(request, 'reportes/index.html', context)


@login_required
def reporte_asistencias(request):
    """Generar reporte de asistencias con filtros y estadísticas avanzadas - Solo administradores"""
    # Verificar permisos (solo admin)
    if not request.user.perfil.es_admin():
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
    
    if unidad_id:
        asistencias = asistencias.filter(id_trabajador__id_unidad_id=unidad_id)
    
    # Estadísticas básicas
    total_registros = asistencias.count()
    asistencias_normales = asistencias.filter(estatus='ASI').count()
    retardos = asistencias.filter(estatus='RET').count()
    faltas = asistencias.filter(estatus='FAL').count()
    justificadas = asistencias.filter(estatus='JUS').count()
    
    # Porcentajes
    porcentaje_asistencia = round((asistencias_normales / total_registros * 100) if total_registros > 0 else 0, 1)
    porcentaje_retardos = round((retardos / total_registros * 100) if total_registros > 0 else 0, 1)
    porcentaje_faltas = round((faltas / total_registros * 100) if total_registros > 0 else 0, 1)
    porcentaje_puntualidad = round((asistencias_normales / (asistencias_normales + retardos) * 100) if (asistencias_normales + retardos) > 0 else 0, 1)
    
    # Estadísticas por día de la semana
    stats_por_dia_semana = {
        0: {'nombre': 'Lunes', 'asistencias': 0, 'retardos': 0, 'faltas': 0},
        1: {'nombre': 'Martes', 'asistencias': 0, 'retardos': 0, 'faltas': 0},
        2: {'nombre': 'Miércoles', 'asistencias': 0, 'retardos': 0, 'faltas': 0},
        3: {'nombre': 'Jueves', 'asistencias': 0, 'retardos': 0, 'faltas': 0},
        4: {'nombre': 'Viernes', 'asistencias': 0, 'retardos': 0, 'faltas': 0},
    }
    
    for asistencia in asistencias:
        dia_semana = asistencia.fecha.weekday()
        if dia_semana < 5:  # Solo días laborales
            if asistencia.estatus == 'ASI':
                stats_por_dia_semana[dia_semana]['asistencias'] += 1
            elif asistencia.estatus == 'RET':
                stats_por_dia_semana[dia_semana]['retardos'] += 1
            elif asistencia.estatus == 'FAL':
                stats_por_dia_semana[dia_semana]['faltas'] += 1
    
    # Tendencia mensual (últimos 3 meses si no hay filtro específico)
    if not trabajador_id and not unidad_id:
        tres_meses_atras = datetime.now() - timedelta(days=90)
        asistencias_tendencia = RegistroAsistencia.objects.filter(
            fecha__gte=tres_meses_atras.date()
        )
        
        tendencia_mensual = asistencias_tendencia.annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            asistencias=Count('id_registro', filter=Q(estatus='ASI')),
            retardos=Count('id_registro', filter=Q(estatus='RET')),
            faltas=Count('id_registro', filter=Q(estatus='FAL'))
        ).order_by('mes')
    else:
        tendencia_mensual = []
    
    # Estadísticas por trabajador (si hay filtro de unidad)
    stats_trabajadores = []
    if unidad_id and not trabajador_id:
        stats_trabajadores = asistencias.values(
            'id_trabajador__numero_empleado',
            'id_trabajador__id_unidad__nombre'
        ).annotate(
            nombre_trabajador=Concat(
                'id_trabajador__nombre',
                Value(' '),
                'id_trabajador__apellido_paterno',
                Value(' '),
                'id_trabajador__apellido_materno'
            ),
            total_asistencias=Count('id_registro', filter=Q(estatus='ASI')),
            total_retardos=Count('id_registro', filter=Q(estatus='RET')),
            total_faltas=Count('id_registro', filter=Q(estatus='FAL')),
        ).order_by('-total_asistencias')
        
        for stat in stats_trabajadores:
            total = stat['total_asistencias'] + stat['total_retardos'] + stat['total_faltas']
            stat['porcentaje'] = round((stat['total_asistencias'] / total * 100) if total > 0 else 0, 1)
    
    # Obtener todas las unidades y trabajadores (solo admin puede acceder)
    unidades = UnidadAdministrativa.objects.all()
    trabajadores = Trabajador.objects.filter(activo=True)
    
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
        'porcentaje_puntualidad': porcentaje_puntualidad,
        'stats_por_dia_semana': list(stats_por_dia_semana.values()),
        'tendencia_mensual': list(tendencia_mensual),
        'stats_trabajadores': stats_trabajadores,
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
    """Exportar reporte de asistencias a CSV con métricas completas - Solo administradores"""
    # Verificar permisos (solo admin)
    if not request.user.perfil.es_admin():
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
    
    # Aplicar filtros adicionales
    if trabajador_id:
        asistencias = asistencias.filter(id_trabajador_id=trabajador_id)
    
    if unidad_id:
        asistencias = asistencias.filter(id_trabajador__id_unidad_id=unidad_id)
    
    # Calcular métricas
    total_registros = asistencias.count()
    asistencias_normales = asistencias.filter(estatus='ASI').count()
    retardos = asistencias.filter(estatus='RET').count()
    faltas = asistencias.filter(estatus='FAL').count()
    justificadas = asistencias.filter(estatus='JUS').count()
    
    # Porcentajes
    porcentaje_asistencia = round((asistencias_normales / total_registros * 100) if total_registros > 0 else 0, 2)
    porcentaje_retardos = round((retardos / total_registros * 100) if total_registros > 0 else 0, 2)
    porcentaje_faltas = round((faltas / total_registros * 100) if total_registros > 0 else 0, 2)
    porcentaje_puntualidad = round((asistencias_normales / (asistencias_normales + retardos) * 100) if (asistencias_normales + retardos) > 0 else 0, 2)
    
    # Calcular días del período
    fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    dias_periodo = (fecha_fin_obj - fecha_inicio_obj).days + 1
    
    # Estadísticas por trabajador
    stats_trabajadores = asistencias.values(
        'id_trabajador__numero_empleado',
        'id_trabajador__id_unidad__nombre'
    ).annotate(
        nombre_trabajador=Concat(
            'id_trabajador__nombre',
            Value(' '),
            'id_trabajador__apellido_paterno',
            Value(' '),
            'id_trabajador__apellido_materno'
        ),
        total_asistencias=Count('id_registro', filter=Q(estatus='ASI')),
        total_retardos=Count('id_registro', filter=Q(estatus='RET')),
        total_faltas=Count('id_registro', filter=Q(estatus='FAL')),
        total_justificadas=Count('id_registro', filter=Q(estatus='JUS'))
    ).order_by('nombre_trabajador')
    
    # Estadísticas por unidad
    stats_unidades = asistencias.values(
        'id_trabajador__id_unidad__nombre'
    ).annotate(
        total_asistencias=Count('id_registro', filter=Q(estatus='ASI')),
        total_retardos=Count('id_registro', filter=Q(estatus='RET')),
        total_faltas=Count('id_registro', filter=Q(estatus='FAL')),
        total_registros=Count('id_registro')
    ).order_by('id_trabajador__id_unidad__nombre')
    
    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_asistencias_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    # Agregar BOM para Excel
    response.write('\ufeff')
    
    writer = csv.writer(response)
    
    # ========== SECCIÓN 1: ENCABEZADO Y RESUMEN ==========
    writer.writerow(['REPORTE DE ASISTENCIAS - SISTEMA DE CONTROL'])
    writer.writerow(['Generado:', datetime.now().strftime('%d/%m/%Y %H:%M:%S')])
    writer.writerow(['Usuario:', request.user.get_full_name() or request.user.username])
    writer.writerow(['Período:', f'{fecha_inicio_obj.strftime("%d/%m/%Y")} - {fecha_fin_obj.strftime("%d/%m/%Y")} ({dias_periodo} días)'])
    writer.writerow([])
    
    # ========== SECCIÓN 2: RESUMEN EJECUTIVO ==========
    writer.writerow(['RESUMEN EJECUTIVO'])
    writer.writerow(['=' * 80])
    writer.writerow(['Métrica', 'Valor', 'Porcentaje'])
    writer.writerow(['Total de Registros', total_registros, '100.00%'])
    writer.writerow(['Asistencias Normales', asistencias_normales, f'{porcentaje_asistencia}%'])
    writer.writerow(['Retardos', retardos, f'{porcentaje_retardos}%'])
    writer.writerow(['Faltas', faltas, f'{porcentaje_faltas}%'])
    writer.writerow(['Faltas Justificadas', justificadas, f'{round((justificadas/total_registros*100) if total_registros > 0 else 0, 2)}%'])
    writer.writerow([])
    writer.writerow(['INDICADORES CLAVE (KPIs)'])
    writer.writerow(['Índice de Asistencia', f'{porcentaje_asistencia}%'])
    writer.writerow(['Índice de Puntualidad', f'{porcentaje_puntualidad}%'])
    writer.writerow(['Índice de Ausentismo', f'{round((faltas/total_registros*100) if total_registros > 0 else 0, 2)}%'])
    writer.writerow([])
    writer.writerow([])
    
    # ========== SECCIÓN 3: ESTADÍSTICAS POR UNIDAD ==========
    if len(stats_unidades) > 1 or not trabajador_id:
        writer.writerow(['ESTADÍSTICAS POR UNIDAD ADMINISTRATIVA'])
        writer.writerow(['=' * 80])
        writer.writerow(['Unidad', 'Total Registros', 'Asistencias', 'Retardos', 'Faltas', '% Asistencia', '% Puntualidad'])
        
        for stat in stats_unidades:
            total = stat['total_registros']
            porc_asist = round((stat['total_asistencias'] / total * 100) if total > 0 else 0, 2)
            porc_punt = round((stat['total_asistencias'] / (stat['total_asistencias'] + stat['total_retardos']) * 100) if (stat['total_asistencias'] + stat['total_retardos']) > 0 else 0, 2)
            
            writer.writerow([
                stat['id_trabajador__id_unidad__nombre'],
                total,
                stat['total_asistencias'],
                stat['total_retardos'],
                stat['total_faltas'],
                f'{porc_asist}%',
                f'{porc_punt}%'
            ])
        writer.writerow([])
        writer.writerow([])
    
    # ========== SECCIÓN 4: ESTADÍSTICAS POR TRABAJADOR ==========
    if len(stats_trabajadores) > 1:
        writer.writerow(['ESTADÍSTICAS POR TRABAJADOR'])
        writer.writerow(['=' * 80])
        writer.writerow(['Trabajador', 'No. Empleado', 'Unidad', 'Asistencias', 'Retardos', 'Faltas', 'Justificadas', 'Total', '% Asistencia', '% Puntualidad', 'Calificación'])
        
        for stat in stats_trabajadores:
            total = stat['total_asistencias'] + stat['total_retardos'] + stat['total_faltas'] + stat['total_justificadas']
            porc_asist = round((stat['total_asistencias'] / total * 100) if total > 0 else 0, 2)
            porc_punt = round((stat['total_asistencias'] / (stat['total_asistencias'] + stat['total_retardos']) * 100) if (stat['total_asistencias'] + stat['total_retardos']) > 0 else 0, 2)
            
            # Calificación cualitativa
            if porc_asist >= 95:
                calificacion = 'EXCELENTE'
            elif porc_asist >= 90:
                calificacion = 'MUY BUENO'
            elif porc_asist >= 80:
                calificacion = 'BUENO'
            elif porc_asist >= 70:
                calificacion = 'REGULAR'
            else:
                calificacion = 'DEFICIENTE'
            
            writer.writerow([
                stat['nombre_trabajador'],
                stat['id_trabajador__numero_empleado'],
                stat['id_trabajador__id_unidad__nombre'],
                stat['total_asistencias'],
                stat['total_retardos'],
                stat['total_faltas'],
                stat['total_justificadas'],
                total,
                f'{porc_asist}%',
                f'{porc_punt}%',
                calificacion
            ])
        writer.writerow([])
        writer.writerow([])
    
    # ========== SECCIÓN 5: DETALLE DE ASISTENCIAS ==========
    writer.writerow(['DETALLE DE REGISTROS DE ASISTENCIA'])
    writer.writerow(['=' * 80])
    writer.writerow([
        'Fecha',
        'Día Semana',
        'Trabajador',
        'No. Empleado',
        'Unidad Administrativa',
        'Puesto',
        'Hora Entrada',
        'Hora Salida',
        'Horas Trabajadas',
        'Estatus',
        'Nivel Puesto'
    ])
    
    # Datos detallados
    for asistencia in asistencias.order_by('fecha', 'id_trabajador__nombre'):
        # Calcular horas trabajadas
        horas_trabajadas = ''
        if asistencia.hora_entrada and asistencia.hora_salida:
            entrada = datetime.combine(asistencia.fecha, asistencia.hora_entrada)
            salida = datetime.combine(asistencia.fecha, asistencia.hora_salida)
            diferencia = salida - entrada
            horas = diferencia.total_seconds() / 3600
            horas_trabajadas = f'{horas:.2f}h'
        
        # Día de la semana
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_semana = dias_semana[asistencia.fecha.weekday()]
        
        writer.writerow([
            asistencia.fecha.strftime('%d/%m/%Y'),
            dia_semana,
            asistencia.id_trabajador.nombre_completo,
            asistencia.id_trabajador.numero_empleado,
            asistencia.id_trabajador.id_unidad.nombre,
            asistencia.id_trabajador.id_puesto.nombre_puesto,
            asistencia.hora_entrada.strftime('%H:%M') if asistencia.hora_entrada else 'N/A',
            asistencia.hora_salida.strftime('%H:%M') if asistencia.hora_salida else 'N/A',
            horas_trabajadas,
            asistencia.get_estatus_display(),
            asistencia.id_trabajador.id_puesto.nivel
        ])
    
    # ========== PIE DE PÁGINA ==========
    writer.writerow([])
    writer.writerow([])
    writer.writerow(['=' * 80])
    writer.writerow(['FIN DEL REPORTE'])
    writer.writerow([])
    writer.writerow(['Índice de Asistencia: Porcentaje de asistencias normales sobre el total'])
    writer.writerow(['Índice de Puntualidad: Porcentaje de asistencias sin retardo'])
    writer.writerow(['Índice de Ausentismo: Porcentaje de faltas sobre el total'])
    
    return response
    # Verificar permisos
