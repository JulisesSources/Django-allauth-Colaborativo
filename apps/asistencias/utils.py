
from datetime import datetime, date, timedelta
from django.db.models import Q

# Modelos externos
from apps.jornadas_laborales.models import (
    JornadaLaboral,
    CalendarioLaboral,
    TrabajadorJornada,
    JornadaDias
)


# =========================================================
#   JORNADA DEL TRABAJADOR
# =========================================================

def obtener_jornada_vigente(trabajador, fecha):
    """
    Obtiene la jornada laboral vigente para un trabajador en una fecha dada.

    Args:
        trabajador (Trabajador): Instancia del trabajador
        fecha (date): Fecha a validar

    Returns:
        JornadaLaboral | None: Jornada si existe, de lo contrario None.
    
    Tips de rendimiento:
        - select_related reduce las consultas al traer la jornada junto a la asignación.
        - first() es más rápido cuando solo necesitamos un resultado.
    """
    try:
        asignacion = (
            TrabajadorJornada.objects.filter(
                id_trabajador=trabajador,
                fecha_inicio__lte=fecha
            )
            .filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha))
            .select_related('id_jornada')
            .first()
        )

        return asignacion.id_jornada if asignacion else None

    except Exception as e:
        print(f"[ERROR] obtener_jornada_vigente(): {e}")
        return None


# =========================================================
#   CALENDARIO LABORAL
# =========================================================

def es_dia_inhabil(fecha):
    """
    Verifica si la fecha es inhábil según el calendario laboral.

    Args:
        fecha (date)

    Returns:
        bool: True si es inhábil, False si no.
    
    Optimización:
        - first() detiene la búsqueda en cuanto encuentra un registro.
    """
    try:
        return CalendarioLaboral.objects.filter(
            fecha=fecha,
            es_inhabil=True
        ).exists()

    except Exception:
        return False


# =========================================================
#   VALIDACIÓN SI EL TRABAJADOR DEBE ASISTIR
# =========================================================

def trabajador_debe_asistir(trabajador, fecha):
    """
    Determina si un trabajador debe asistir en una fecha específica,
    considerando:
        - Días inhábiles
        - Jornada asignada
        - Días laborales de la jornada

    Returns:
        (bool debe_asistir, str razon)
    """

    # 1. Día inhábil
    if es_dia_inhabil(fecha):
        return (False, "Día inhábil según calendario laboral")

    # 2. Validar jornada asignada
    jornada = obtener_jornada_vigente(trabajador, fecha)
    if not jornada:
        return (False, "Trabajador sin jornada asignada")

    # 3. Validar si ese día labora
    numero_dia = fecha.isoweekday()  # 1 = Lunes ... 7 = Domingo
    trabaja_este_dia = JornadaDias.objects.filter(
        id_jornada=jornada,
        numero_dia=numero_dia
    ).exists()

    if not trabaja_este_dia:
        return (False, f"No labora el día {fecha.strftime('%A')}")

    return (True, "Debe asistir")


# =========================================================
#   CÁLCULO DE ESTATUS (ASI, RET, FAL, JUS)
# =========================================================

def calcular_estatus_asistencia(trabajador, fecha, hora_entrada=None, hora_salida=None):
    """
    Determina el estatus de asistencia basado en:
        - Si debe asistir
        - Hora de entrada vs hora esperada
        - Tolerancia configurable (10 min)

    Returns:
        str: 'ASI', 'RET', 'FAL', 'JUS'
    """

    debe_asistir, razon = trabajador_debe_asistir(trabajador, fecha)

    # 1. No debe asistir (día no laboral o inhábil)
    if not debe_asistir:
        return 'ASI' if hora_entrada else 'JUS'

    # 2. Debe asistir pero no registró entrada
    if not hora_entrada:
        return 'FAL'

    # 3. Calcular retardo
    jornada = obtener_jornada_vigente(trabajador, fecha)
    if not jornada:
        return 'ASI'

    hora_esperada = jornada.hora_entrada
    TOLERANCIA_MINUTOS = 10

    hora_esperada_dt = datetime.combine(fecha, hora_esperada)
    hora_entrada_dt = datetime.combine(fecha, hora_entrada)

    hora_limite = hora_esperada_dt + timedelta(minutes=TOLERANCIA_MINUTOS)

    return 'ASI' if hora_entrada_dt <= hora_limite else 'RET'


# =========================================================
#   MINUTOS DE RETARDO
# =========================================================

def calcular_minutos_retardo(trabajador, fecha, hora_entrada):
    """
    Calcula los minutos de retardo reales del trabajador.

    Returns:
        int: minutos de retardo. 0 si no hay retardo.
    """

    jornada = obtener_jornada_vigente(trabajador, fecha)
    if not jornada:
        return 0

    hora_esperada = jornada.hora_entrada

    diferencia = (
        datetime.combine(fecha, hora_entrada) -
        datetime.combine(fecha, hora_esperada)
    )

    return max(0, int(diferencia.total_seconds() / 60))


# =========================================================
#   VALIDACIÓN GENERAL DEL REGISTRO
# =========================================================

def validar_registro_asistencia(trabajador, fecha, hora_entrada=None, hora_salida=None):
    """
    Valida coherencia del registro de asistencia.

    Reglas:
        - No permitir fechas futuras
        - Si hay salida debe haber entrada
        - La salida debe ser después de entrada
        - El trabajador debe estar activo
    """

    errores = []

    if fecha > date.today():
        errores.append("No se puede registrar asistencia en fechas futuras.")

    if hora_salida and not hora_entrada:
        errores.append("No puede registrar salida sin haber registrado entrada.")

    if hora_entrada and hora_salida and hora_salida <= hora_entrada:
        errores.append("La hora de salida debe ser posterior a la de entrada.")

    if not trabajador.activo:
        errores.append("El trabajador no está activo en el sistema.")

    return (not errores, errores)


# =========================================================
#   RESUMEN DE ASISTENCIAS
# =========================================================

def obtener_resumen_asistencia_trabajador(trabajador, fecha_inicio, fecha_fin):
    """
    Calcula estadísticas de asistencia en un periodo:
        - Asistencias
        - Retardos
        - Faltas
        - Justificadas
        - % de asistencia útil

    Returns:
        dict con métricas
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

    dias_laborales_reales = (
        resumen['asistencias'] +
        resumen['retardos'] +
        resumen['faltas']
    )

    if dias_laborales_reales > 0:
        resumen['porcentaje_asistencia'] = round(
            (resumen['asistencias'] + resumen['retardos']) / dias_laborales_reales * 100,
            2
        )

    return resumen
