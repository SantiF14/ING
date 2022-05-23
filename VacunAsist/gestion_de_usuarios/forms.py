from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from datetime import date
from django.db.models.fields import EmailField
from django.http import request
from gestion_de_usuarios.models import *
from django.db.models import Q

class FormularioDeRegistro (UserCreationForm):
    email = forms.EmailField(help_text="Aqui va tu dirección de email")
    nombre_apellido = forms.CharField(max_length=50, help_text="Aqui va tu nombre y apellido")
    date_of_birth  = forms.DateField()


    class Meta:
        model = Usuario
        fields = ('dni','email', 'sexo', 'de_riesgo', 'password1', 'password2', 'clave_alfanumerica')

    def clean_dni(self):

        """Recibe un dni y lo valida."""

        dni = self.cleaned_data['dni']
        try:
            user = Usuario.objects.exclude(pk=self.instance.pk).get(dni=dni)
        except Usuario.DoesNotExist:
            return dni
        raise forms.ValidationError(f"Ya existe una cuenta con el DNI {dni} ya está en uso! Probá con otro.")

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data['date_of_birth']
        today = date.today()
        if (fecha_nacimiento) > (today):
            raise forms.ValidationError('Ingresá una fecha válida.')
        
        return fecha_nacimiento
    
    def clean_riesgo(self):
        de_riesgo = self.cleaned_data['de_riesgo']
        return de_riesgo

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        return email
    
    def clean_nombre_apellido(self):
        nombre_apellido = self.cleaned_data['nombre_apellido']
        return nombre_apellido

    

class FormularioDeAutenticacion(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ("dni", "password", "clave_alfanumerica")
   
    def clean(self):
        
        """Define el error que debe ser mostrado"""

        if self.is_valid():
            dni = self.cleaned_data['dni']
            password = self.cleaned_data['password']
            clave_alfanumerica = self.cleaned_data['clave_alfanumerica']
            try:
                user = Usuario.objects.get(dni=dni)
                user.save()
            except Usuario.DoesNotExist:
                pass
            if not authenticate(dni=dni, password=password, clave_alfanumerica=clave_alfanumerica):
                raise forms.ValidationError("Inicio de sesión inválido.")

