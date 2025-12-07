# apps/asistencias/forms.py

from django import forms
from .models import RegistroAsistencia
from apps.trabajadores.models import Trabajador
from datetime import date, datetime


# =========================================================
#   FORMULARIO: REGISTRO DE ASISTENCIA (Completo)
# =========================================================

class RegistroAsistenciaForm(forms.ModelForm):
    class Meta:
        model = RegistroAsistencia
        fields = ['id_trabajador', 'fecha', 'hora_entrada', 'hora_salida', 'estatus']
        widgets = {
            'id_trabajador': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'max': date.today().isoformat()
            }),
            'hora_entrada': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'hora_salida': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'estatus': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar trabajadores activos
        self.fields['id_trabajador'].queryset = Trabajador.objects.filter(activo=True)
        # Fecha por defecto es hoy
        if not self.instance.pk:
            self.fields['fecha'].initial = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_entrada = cleaned_data.get('hora_entrada')
        hora_salida = cleaned_data.get('hora_salida')
        
        # Validar fecha no futura
        if fecha and fecha > date.today():
            raise forms.ValidationError("No se puede registrar asistencia en fechas futuras")
        
        # Validar coherencia de horas
        if hora_entrada and hora_salida:
            if hora_salida <= hora_entrada:
                raise forms.ValidationError("La hora de salida debe ser posterior a la hora de entrada")
        
        return cleaned_data


# =========================================================
#   FORMULARIO: REGISTRO RÁPIDO (Checador)
# =========================================================

class RegistroRapidoForm(forms.Form):
    numero_empleado = forms.ModelChoiceField(
        queryset=Trabajador.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 text-lg border-2 border-blue-500 rounded-lg focus:ring-2 focus:ring-blue-500',
            'autofocus': True
        }),
        label='Selecciona el trabajador',
        empty_label='-- Selecciona un trabajador --'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar cómo se muestra cada trabajador en el combo
        self.fields['numero_empleado'].label_from_instance = lambda obj: f"{obj.numero_empleado} - {obj.nombre} {obj.apellido_paterno} {obj.apellido_materno}"


# =========================================================
#   FORMULARIO: FILTROS DE ASISTENCIA
# =========================================================

class FiltroAsistenciaForm(forms.Form):
    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label='Fecha Inicio'
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label='Fecha Fin'
    )
    estatus = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + RegistroAsistencia.ESTATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label='Estatus'
    )
    trabajador = forms.ModelChoiceField(
        required=False,
        queryset=Trabajador.objects.filter(activo=True),
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        }),
        label='Trabajador'
    )