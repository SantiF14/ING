from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from datetime import date
from django.db.models.fields import EmailField
from django.http import request
from gestion_de_usuarios.models import *
from django.db.models import Q
from django.core.exceptions import ValidationError

class FormularioDeRegistro (UserCreationForm):
    dni =  forms.IntegerField(help_text="Aqui va tu dni")
    email = forms.EmailField(help_text="Aqui va tu dirección de email")
    nombre_apellido = forms.CharField(max_length=50, help_text="Aqui va tu nombre y apellido")
    sexo = forms.ChoiceField(choices=(("M","Masculino"),("F","Femenino")))
    de_riesgo = forms.ChoiceField(choices=(("1","Si"),("0","No")), widget=forms.RadioSelect)
    password1 = forms.CharField(help_text="Aqui va tu contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(help_text="Por favor repita su contraseña", widget=forms.PasswordInput)
    fecha_nacimiento  = forms.DateField()
    vacunatorio_pref = forms.ChoiceField(choices=(("1","Polideportivo"),("2","Corralon municipal"),("3","Hospital 9 de julio")))
    

    def __init__(self, *args, **kwargs): 
        super(FormularioDeRegistro, self).__init__(*args, **kwargs) 
        # remove username
        self.fields.pop('username')
    

    def clean_dni(self):

        dni = self.cleaned_data["dni"]
        new = Usuario.objects.filter(dni = dni)  
        if new.count():  
            raise ValidationError("Ya existe una cuenta con el DNI {dni}. Probá con otro.")  
        return dni
        

    def clean_fecha_nacimiento(self):

        fecha_nacimiento = self.cleaned_data['fecha_nacimiento']
        today = date.today()
        if (fecha_nacimiento) > (today):
            raise forms.ValidationError('Ingresá una fecha válida.')
        
        return fecha_nacimiento

    def clean_email(self):  

        email = self.cleaned_data['email'].lower()  
        return email  
  
    def clean_password2(self):  

        password1 = self.cleaned_data['password1']  
        password2 = self.cleaned_data['password2'] 
        if password1 and password2 and password1 != password2:  
            raise ValidationError("Password don't match")  
        return password2  

    def clean_riesgo(self):

        de_riesgo = self.cleaned_data['de_riesgo']
        return de_riesgo

    
    def clean_nombre_apellido(self):

        nombre_apellido = self.cleaned_data['nombre_apellido']
        return nombre_apellido
    
    def save(self, clave_alfanumerica, commit = True):
        user = MyAccountManager.crear_usuario(  
            self.cleaned_data['dni'],  
            self.cleaned_data['nombre_apellido'],  
            self.cleaned_data['sexo'],
            self.cleaned_data['email'],
            self.cleaned_data['de_riesgo'],
            self.cleaned_data['fecha_nacimiento'] ,
            clave_alfanumerica,
            self.cleaned_data['vacunatorio_pref'],
            self.cleaned_data['password1']
        )  
        return user

    

class FormularioDeAutenticacion(forms.ModelForm):
    password = forms.CharField(label="password", widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ("dni", "password")
   
    def clean(self):
        print("holaform1")
        """Define el error que debe ser mostrado"""

        if self.is_valid():
            print("holaform2")
            dni = self.cleaned_data['dni']
            password = self.cleaned_data['password']
        #    clave_alfanumerica = self.cleaned_data['clave_alfanumerica']
            print("holaform2")
            try:
                print("holaform2")
                user = Usuario.objects.get(dni=dni)
                user.save()
            except Usuario.DoesNotExist:
                pass
            if not authenticate(dni=dni, password=password):
                print("holaform3")
                raise forms.ValidationError("Inicio de sesión inválido.")
