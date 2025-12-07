# apps/jornadas_laborales/forms.py

from django import forms
from django.db.models import Q
from datetime import date

from .models import JornadaLaboral, CalendarioLaboral, JornadaDias, TrabajadorJornada
from apps.trabajadores.models import Trabajador


# =========================================================
#   FORMULARIO: JORNADA LABORAL
# =========================================================

class JornadaLaboralForm(forms.ModelForm):

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
    )

    class Meta:
        model = JornadaLaboral
        fields = ['descripcion', 'hora_entrada', 'hora_salida']

        widgets = {
            'descripcion': forms.Select(attrs={
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
            'hora_entrada': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
            'hora_salida': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition'
            }),
        }

        labels = {
            'descripcion': 'Tipo de Jornada',
            'hora_entrada': 'Hora de Entrada',
            'hora_salida': 'Hora de Salida',
        }




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
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition'
            }),
            'es_inhabil': forms.CheckboxInput(attrs={
                'class': 'w-6 h-6 bg-gray-900 border-gray-600 rounded text-red-500 focus:ring-red-500 focus:ring-2 cursor-pointer'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition placeholder-gray-500',
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
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition'
            }),
            'id_jornada': forms.Select(attrs={
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition'
            }),
            'fecha_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full bg-gray-900 border border-gray-600 text-white rounded-lg px-4 py-3 focus:ring-2 focus:ring-green-500 focus:border-green-500 transition'
            }),
        }
        labels = {
            'id_trabajador': 'Trabajador',
            'id_jornada': 'Jornada',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Solo mostrar trabajadores activos
        qs = Trabajador.objects.filter(activo=True)

        # Si es jefe → limitar a su unidad
        if request and hasattr(request.user, 'perfil') and request.user.perfil.es_jefe():
            unidad = request.user.perfil.id_trabajador.id_unidad
            qs = qs.filter(id_unidad=unidad)

        self.fields['id_trabajador'].queryset = qs

        if not self.instance.pk:
            self.fields['fecha_inicio'].initial = date.today()

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
