"""
Utilidades para cálculo de retardos y validación de asistencias
"""
from datetime import datetime, date, time, timedelta
from django.db.models import Q
from apps.jornadas_laborales.models import (
    JornadaLaboral, 
    CalendarioLaboral, 
    TrabajadorJornada,
    JornadaDias
)


def obtener_jornada_vigente(trabajador, fecha):
    """
    Obtiene la jornada laboral asignada al trabajador en una fecha específica
    
    Args:
        trabajador: Instancia de Trabajador
        fecha: date - Fecha a consultar
    
    Returns:
        JornadaLaboral o None si no tiene jornada asignada
    """
    try:
        asignacion = TrabajadorJornada.objects.filter(
            id_trabajador=trabajador,
            fecha_inicio__lte=fecha
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha)
        ).select_related('id_jornada').first()
        
        return asignacion.id_jornada if asignacion else None
    except Exception as e:
        print(f"Error al obtener jornada: {e}")
        return None


def es_dia_inhabil(fecha):
    """
    Verifica si una fecha es día inhábil según el calendario laboral
    
    Args:
        fecha: date - Fecha a consultar
    
    Returns:
        bool - True si es inhábil, False si es hábil
    """
    try:
        dia = CalendarioLaboral.objects.filter(
            fecha=fecha,
            es_inhabil=True
        ).first()
        return dia is not None
    except Exception:
        return False


def trabajador_debe_asistir(trabajador, fecha):
    """
    Determina si un trabajador debe asistir en una fecha específica
    considerando su jornada y el calendario laboral
    
    Args:
        trabajador: Instancia de Trabajador
        fecha: date - Fecha a verificar
    
    Returns:
        tuple: (debe_asistir: bool, razon: str)
    """
    # 1. Verificar si es día inhábil
    if es_dia_inhabil(fecha):
        return (False, "Día inhábil según calendario laboral")
    
    # 2. Obtener jornada del trabajador
    jornada = obtener_jornada_vigente(trabajador, fecha)
    if not jornada:
        return (False, "Trabajador sin jornada asignada")
    
    # 3. Verificar si el día de la semana está en su jornada
    numero_dia = fecha.isoweekday()  # 1=Lunes, 7=Domingo
    
    dias_jornada = JornadaDias.objects.filter(
        id_jornada=jornada,
        numero_dia=numero_dia
    ).exists()
    
    if not dias_jornada:
        return (False, f"No labora {fecha.strftime('%A')}")
    
    return (True, "Debe asistir")


def calcular_estatus_asistencia(trabajador, fecha, hora_entrada=None, hora_salida=None):
    """
    Calcula el estatus de asistencia basado en la hora de entrada
    y la jornada del trabajador
    
    Args:
        trabajador: Instancia de Trabajador
        fecha: date - Fecha del registro
        hora_entrada: time - Hora de entrada (puede ser None)
        hora_salida: time - Hora de salida (puede ser None)
    
    Returns:
        str: Estatus ('ASI', 'RET', 'FAL', 'JUS')
    """
    # Verificar si debe asistir
    debe_asistir, razon = trabajador_debe_asistir(trabajador, fecha)
    
    if not debe_asistir:
        # Si no debe asistir pero registró entrada, es asistencia normal
        if hora_entrada:
            return 'ASI'
        return 'JUS'  # Falta justificada (día inhábil o no laboral)
    
    # Si debe asistir pero no hay hora de entrada
    if not hora_entrada:
        return 'FAL'  # Falta
    
    # Obtener jornada y hora esperada
    jornada = obtener_jornada_vigente(trabajador, fecha)
    if not jornada:
        return 'ASI'  # Si no hay jornada, considerarlo asistencia
    
    # Comparar hora de entrada con hora esperada
    hora_esperada = jornada.hora_entrada
    
    # Tolerancia de 10 minutos
    TOLERANCIA_MINUTOS = 10
    
    hora_esperada_dt = datetime.combine(fecha, hora_esperada)
    hora_entrada_dt = datetime.combine(fecha, hora_entrada)
    hora_limite = hora_esperada_dt + timedelta(minutes=TOLERANCIA_MINUTOS)
    
    if hora_entrada_dt <= hora_limite:
        return 'ASI'  # Asistencia normal
    else:
        return 'RET'  # Retardo


def calcular_minutos_retardo(trabajador, fecha, hora_entrada):
    """
    Calcula cuántos minutos de retardo tiene un trabajador
    
    Args:
        trabajador: Instancia de Trabajador
        fecha: date
        hora_entrada: time
    
    Returns:
        int: Minutos de retardo (0 si no hay retardo)
    """
    jornada = obtener_jornada_vigente(trabajador, fecha)
    if not jornada:
        return 0
    
    hora_esperada = jornada.hora_entrada
    hora_esperada_dt = datetime.combine(fecha, hora_esperada)
    hora_entrada_dt = datetime.combine(fecha, hora_entrada)
    
    diferencia = hora_entrada_dt - hora_esperada_dt
    
    if diferencia.total_seconds() > 0:
        return int(diferencia.total_seconds() / 60)
    return 0


def validar_registro_asistencia(trabajador, fecha, hora_entrada=None, hora_salida=None):
    """
    Valida que un registro de asistencia sea coherente
    
    Args:
        trabajador: Instancia de Trabajador
        fecha: date
        hora_entrada: time
        hora_salida: time
    
    Returns:
        tuple: (es_valido: bool, errores: list)
    """
    errores = []
    
    # 1. No puede ser fecha futura
    if fecha > date.today():
        errores.append("No se puede registrar asistencia en fechas futuras")
    
    # 2. Si hay salida, debe haber entrada
    if hora_salida and not hora_entrada:
        errores.append("No puede haber hora de salida sin hora de entrada")
    
    # 3. Salida debe ser después de entrada
    if hora_entrada and hora_salida:
        if hora_salida <= hora_entrada:
            errores.append("La hora de salida debe ser posterior a la hora de entrada")
    
    # 4. Verificar que el trabajador esté activo
    if not trabajador.activo:
        errores.append("El trabajador no está activo en el sistema")
    
    return (len(errores) == 0, errores)


def obtener_resumen_asistencia_trabajador(trabajador, fecha_inicio, fecha_fin):
    """
    Genera un resumen de asistencias de un trabajador en un rango de fechas
    
    Args:
        trabajador: Instancia de Trabajador
        fecha_inicio: date
        fecha_fin: date
    
    Returns:
        dict: Resumen con contadores
    """
    from apps.asistencias.models import RegistroAsistencia
    
    registros = RegistroAsistencia.objects.filter(
        id_trabajador=trabajador,
        fecha__range=[fecha_inicio, fecha_fin]
    )
    
    resumen = {
        'total_dias': (fecha_fin - fecha_inicio).days + 1,
        'asistencias': registros.filter(estatus='ASI').count(),
        'retardos': registros.filter(estatus='RET').count(),
        'faltas': registros.filter(estatus='FAL').count(),
        'faltas_justificadas': registros.filter(estatus='JUS').count(),
        'porcentaje_asistencia': 0
    }
    
    dias_laborales = resumen['asistencias'] + resumen['retardos'] + resumen['faltas']
    if dias_laborales > 0:
        resumen['porcentaje_asistencia'] = round(
            ((resumen['asistencias'] + resumen['retardos']) / dias_laborales) * 100, 
            2
        )
    
    return resumen