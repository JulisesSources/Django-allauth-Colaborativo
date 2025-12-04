from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario


class CustomSignupForm(forms.Form):
    """Formulario para el registro con allauth sin nombre y apellido"""

    def signup(self, request, user):
        """Este método lo llama allauth automáticamente al registrar"""
        PerfilUsuario.objects.get_or_create(user=user)
        return user


class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para que los usuarios editen su perfil
    Incluye username editable y email readonly
    """
    username = forms.CharField(
        label='Nombre de usuario',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Correo Electrónico',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    class Meta:
        model = PerfilUsuario
        fields = []  # No editamos directamente campos del perfil aquí

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def save(self, commit=True):
        perfil = super().save(commit=False)

        if self.user:
            self.user.username = self.cleaned_data['username']
            # email permanece readonly
            if commit:
                self.user.save()
                perfil.save()

        return perfil


class AsignarRolForm(forms.ModelForm):
    """
    Formulario para que los administradores asignen roles
    """
    class Meta:
        model = PerfilUsuario
        fields = ['rol', 'id_trabajador']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'id_trabajador': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'rol': 'Rol del Usuario',
            'id_trabajador': 'Trabajador Asociado (opcional)',
        }
        help_texts = {
            'id_trabajador': 'Asocia este usuario con un trabajador existente si es necesario.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo trabajadores activos
        if 'id_trabajador' in self.fields:
            self.fields['id_trabajador'].queryset = self.fields['id_trabajador'].queryset.filter(activo=True)
            self.fields['id_trabajador'].required = False
