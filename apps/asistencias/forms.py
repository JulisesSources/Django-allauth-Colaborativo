from django import forms
from .models import RegistroAsistencia
from apps.trabajadores.models import Trabajador
from datetime import date, datetime


class RegistroAsistenciaForm(forms.ModelForm):
    """
    Formulario para registrar asistencia de trabajadores
    """
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


class RegistroRapidoForm(forms.Form):
    """
    Formulario simplificado para registro rápido (solo entrada)
    """
    numero_empleado = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 text-2xl text-center border-2 border-blue-500 rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Número de empleado',
            'autofocus': True
        }),
        label='Número de Empleado'
    )
    
    def clean_numero_empleado(self):
        numero = self.cleaned_data.get('numero_empleado')
        try:
            trabajador = Trabajador.objects.get(numero_empleado=numero, activo=True)
            return trabajador
        except Trabajador.DoesNotExist:
            raise forms.ValidationError("Número de empleado no encontrado o trabajador inactivo")


class FiltroAsistenciaForm(forms.Form):
    """
    Formulario para filtrar registros de asistencia
    """
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