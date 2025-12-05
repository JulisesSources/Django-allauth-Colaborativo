# incidencias/forms.py

from django import forms
from django.core.exceptions import ValidationError
from .models import Incidencia, TipoIncidencia
# from apps.workers.models import Trabajador   # ← Aún no existe, lo comentamos


class IncidenciaForm(forms.ModelForm):
    """
    Formulario principal para crear y editar incidencias.
    Mientras no exista el modelo Trabajador, se desactiva ese filtrado.
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
                'class': 'form-control'
            }),
            'id_tipo_incidencia': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
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

        perfil = getattr(self.user, 'perfil', None)

        # TIPOS DE INCIDENCIA ACTIVOS
        self.fields['id_tipo_incidencia'].queryset = TipoIncidencia.objects.filter(activo=True)

        # ===========================================================
        #  SECCIÓN DE TRABAJADORES — DESACTIVADA TEMPORALMENTE
        # ===========================================================
        #
        # queryset_trab = Trabajador.objects.filter(activo=True)
        #
        # if perfil:
        #
        #     if perfil.es_admin():
        #         self.fields['id_trabajador'].queryset = queryset_trab
        #
        #     elif perfil.es_jefe():
        #         if perfil.id_trabajador and perfil.id_trabajador.id_unidad:
        #             unidad = perfil.id_trabajador.id_unidad
        #             self.fields['id_trabajador'].queryset = queryset_trab.filter(id_unidad=unidad)
        #         else:
        #             self.fields['id_trabajador'].queryset = queryset_trab.none()
        #
        #     elif perfil.es_trabajador():
        #         if perfil.id_trabajador:
        #             self.fields['id_trabajador'].queryset = queryset_trab.filter(id=perfil.id_trabajador.id)
        #             self.fields['id_trabajador'].initial = perfil.id_trabajador
        #             self.fields['id_trabajador'].widget = forms.HiddenInput()
        #         else:
        #             self.fields['id_trabajador'].queryset = queryset_trab.none()
        #
        # ===========================================================

        # Validación dinámica de fechas
        self.fields['fecha_inicio'].required = True
        self.fields['fecha_fin'].required = True

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')

        return cleaned_data


class AutorizarIncidenciaForm(forms.Form):
    """
    Formulario para autorizar o rechazar una incidencia.
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
    Formulario para filtrar incidencias en lista general.
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
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Desde'
    )

    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Hasta'
    )


class TipoIncidenciaForm(forms.ModelForm):
    class Meta:
        model = TipoIncidencia
        fields = ['descripcion', 'requiere_autorizacion', 'activo']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Permiso con goce de sueldo'
            }),
            'requiere_autorizacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'descripcion': 'Descripción',
            'requiere_autorizacion': '¿Requiere Autorización?',
            'activo': 'Activo'
        }
