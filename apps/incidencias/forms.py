# incidencias/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Incidencia, TipoIncidencia


class IncidenciaForm(forms.ModelForm):
    """
    Formulario para crear y editar incidencias
    """
    class Meta:
        model = Incidencia
        fields = [
            'id_trabajador',
            'id_tipo_incidencia',
            'fecha_inicio',
            'fecha_fin',
            'observaciones'
        ]
        widgets = {
            'id_trabajador': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'id_tipo_incidencia': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ingresa observaciones adicionales (opcional)'
            }),
        }
        labels = {
            'id_trabajador': 'Trabajador',
            'id_tipo_incidencia': 'Tipo de Incidencia',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin',
            'observaciones': 'Observaciones',
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo tipos de incidencia activos
        self.fields['id_tipo_incidencia'].queryset = TipoIncidencia.objects.filter(activo=True)
        
        # Filtrar solo trabajadores activos
        self.fields['id_trabajador'].queryset = self.fields['id_trabajador'].queryset.filter(activo=True)
        
        # Si el usuario tiene un trabajador asociado y no es admin/jefe, solo puede crear para sí mismo
        if self.user and hasattr(self.user, 'perfil'):
            if self.user.perfil.es_trabajador() and self.user.perfil.id_trabajador:
                self.fields['id_trabajador'].initial = self.user.perfil.id_trabajador
                self.fields['id_trabajador'].widget = forms.HiddenInput()
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
        
        return cleaned_data


class AutorizarIncidenciaForm(forms.Form):
    """
    Formulario para autorizar o rechazar una incidencia
    """
    ACCION_CHOICES = [
        ('autorizar', 'Autorizar'),
        ('rechazar', 'Rechazar'),
    ]
    
    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Acción'
    )
    comentario = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ingresa un comentario (opcional)'
        }),
        required=False,
        label='Comentario'
    )


class FiltroIncidenciaForm(forms.Form):
    """
    Formulario para filtrar incidencias
    """
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('pendiente', 'Pendiente'),
        ('autorizada', 'Autorizada'),
        ('rechazada', 'Rechazada'),
    ]
    
    trabajador = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o número de empleado...'
        }),
        label='Trabajador'
    )
    
    tipo_incidencia = forms.ModelChoiceField(
        queryset=TipoIncidencia.objects.filter(activo=True),
        required=False,
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Incidencia'
    )
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Estado'
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )