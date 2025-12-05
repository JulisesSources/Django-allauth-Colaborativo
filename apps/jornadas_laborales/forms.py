from django import forms
from django.db.models import Q
from datetime import date

from .models import JornadaLaboral, CalendarioLaboral, JornadaDias, TrabajadorJornada
from apps.trabajadores.models import Trabajador


# =========================================================
#   FORMULARIO: JORNADA LABORAL
# =========================================================

class JornadaLaboralForm(forms.ModelForm):
    """
    Formulario para crear/editar jornadas laborales
    Incluye selección de días laborales mediante MultipleChoiceField
    """
    DIAS_CHOICES = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]
    
    dias = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox h-4 w-4 text-blue-600'
        }),
        label='Días Laborales',
        required=True,
        help_text='Selecciona los días en que aplica esta jornada'
    )
    
    class Meta:
        model = JornadaLaboral
        fields = ['descripcion', 'hora_entrada', 'hora_salida']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej: Jornada Normal - Lunes a Viernes'
            }),
            'hora_entrada': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
            'hora_salida': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
        }
        labels = {
            'descripcion': 'Descripción',
            'hora_entrada': 'Hora de Entrada',
            'hora_salida': 'Hora de Salida',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, marcar los días actuales
        if self.instance.pk:
            dias_actuales = JornadaDias.objects.filter(
                id_jornada=self.instance
            ).values_list('numero_dia', flat=True)
            self.fields['dias'].initial = [str(d) for d in dias_actuales]
    
    def clean(self):
        cleaned_data = super().clean()
        hora_entrada = cleaned_data.get('hora_entrada')
        hora_salida = cleaned_data.get('hora_salida')
        dias = cleaned_data.get('dias')
        
        # Validar horarios
        if hora_entrada and hora_salida:
            if hora_salida <= hora_entrada:
                raise forms.ValidationError(
                    "La hora de salida debe ser posterior a la hora de entrada"
                )
        
        # Validar que se haya seleccionado al menos un día
        if not dias:
            raise forms.ValidationError(
                "Debe seleccionar al menos un día laboral"
            )
        
        return cleaned_data


# =========================================================
#   FORMULARIO: CALENDARIO LABORAL
# =========================================================

class CalendarioLaboralForm(forms.ModelForm):
    """
    Formulario para registrar días inhábiles en el calendario
    """
    class Meta:
        model = CalendarioLaboral
        fields = ['fecha', 'es_inhabil', 'descripcion']
        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full border rounded px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
            'es_inhabil': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full border rounded px-3 py-2 focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ej: Día de la Independencia'
            }),
        }
        labels = {
            'fecha': 'Fecha',
            'es_inhabil': 'Marcar como día inhábil',
            'descripcion': 'Descripción',
        }
    
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        
        # Validar que no sea muy antigua
        if fecha and fecha.year < 2020:
            raise forms.ValidationError(
                "Ingrese una fecha válida (2020 en adelante)"
            )
        
        # Verificar que no exista ya (excepto si estamos editando)
        if fecha:
            existe = CalendarioLaboral.objects.filter(fecha=fecha)
            if self.instance.pk:
                existe = existe.exclude(pk=self.instance.pk)
            if existe.exists():
                raise forms.ValidationError(
                    f"Ya existe un registro para la fecha {fecha.strftime('%d/%m/%Y')}"
                )
        
        return fecha


# =========================================================
#   FORMULARIO: ASIGNAR JORNADA A TRABAJADOR
# =========================================================

class AsignarJornadaForm(forms.ModelForm):
    """
    Formulario principal para asignar jornadas a trabajadores
    Incluye validaciones de traslape y coherencia de fechas
    """
    class Meta:
        model = TrabajadorJornada
        fields = ['id_trabajador', 'id_jornada', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'id_trabajador': forms.Select(attrs={
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
            'id_jornada': forms.Select(attrs={
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full rounded border px-3 py-2 focus:ring-2 focus:ring-blue-500'
            }),
        }
        labels = {
            'id_trabajador': 'Trabajador',
            'id_jornada': 'Jornada',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar trabajadores activos
        self.fields['id_trabajador'].queryset = Trabajador.objects.filter(activo=True)
        # Fecha inicio por defecto es hoy
        if not self.instance.pk:
            self.fields['fecha_inicio'].initial = date.today()
        # Fecha fin es opcional
        self.fields['fecha_fin'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        trabajador = cleaned_data.get('id_trabajador')
        jornada = cleaned_data.get('id_jornada')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Validar coherencia de fechas
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise forms.ValidationError(
                    "La fecha de fin debe ser posterior a la fecha de inicio"
                )
        
        # Validar traslapes con otras asignaciones del mismo trabajador
        if trabajador and fecha_inicio:
            # Buscar asignaciones que se traslapen
            traslapes = TrabajadorJornada.objects.filter(
                id_trabajador=trabajador,
                fecha_inicio__lte=fecha_fin or date(2099, 12, 31),
            ).filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_inicio)
            )
            
            # Excluir la instancia actual si estamos editando
            if self.instance.pk:
                traslapes = traslapes.exclude(pk=self.instance.pk)
            
            if traslapes.exists():
                jornada_existente = traslapes.first()
                raise forms.ValidationError(
                    f"El trabajador ya tiene asignada la jornada '{jornada_existente.id_jornada.descripcion}' "
                    f"desde {jornada_existente.fecha_inicio.strftime('%d/%m/%Y')}. "
                    f"Debe finalizar esa asignación antes de crear una nueva."
                )
        
        return cleaned_data


# Alias para mantener compatibilidad si se usa en otros lados
