from django import forms
from django.forms import formset_factory
from .models import Puesto


class PuestoSimpleForm(forms.Form):
    nombre_puesto = forms.CharField(
        max_length=200,
        label="Nombre del puesto",
        widget=forms.TextInput(attrs={'class': 'form-input w-full'})
    )

    NIVEL_CHOICES = [
        ('Docente', 'Docente'),
        ('Administrativo', 'Administrativo'),
        ('Directivo', 'Directivo'),
    ]

    nivel = forms.ChoiceField(
        choices=NIVEL_CHOICES,
        label="Nivel",
        widget=forms.Select(attrs={'class': 'form-select w-full'})
    )


PuestoFormSet = formset_factory(PuestoSimpleForm, extra=5)
