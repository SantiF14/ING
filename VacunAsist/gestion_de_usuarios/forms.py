from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import date
from django.http import request
from gestion_de_usuarios.models import *
from django.core.exceptions import ValidationError
from VacunAsist.settings import DATE_INPUT_FORMATS


class FormularioDeRegistro (UserCreationForm):
    dni =  forms.CharField(max_length=8, label = "DNI")
    email = forms.EmailField(label="Email")
    nombre_apellido = forms.CharField(max_length=50, label="Nombre y apellido")
    sexo = forms.ChoiceField(label="Sexo (Como figura en el DNI)", choices=(("M","Masculino"),("F","Femenino")))
    de_riesgo = forms.ChoiceField(label = "Sos de riesgo?",choices=(("1","Si"),("0","No")), widget=forms.RadioSelect)
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Repita su contraseña", widget=forms.PasswordInput)
    fecha_nacimiento  = forms.DateField(label="Fecha de nacimiento",widget=forms.SelectDateWidget(years=range(date.today().year-110, date.today().year)), input_formats= DATE_INPUT_FORMATS)
    vacunatorio_pref = forms.ModelChoiceField(label="Vacunatorio de preferencia",queryset=Vacunatorio.objects.all(), widget=forms.Select, empty_label=None)
    field_order = ['dni', 'nombre_apellido', 'sexo', "fecha_nacimiento", "email", "password1", "password2", "vacunatorio_pref", "de_riesgo"]
    def validate_dni(value):
        raise ValidationError("This field accepts mail id of google only")


    def __init__(self, *args, **kwargs): 
        super(FormularioDeRegistro, self).__init__(*args, **kwargs) 
        # remove username
        self.fields.pop('username')
    

    def clean_dni(self):

        dni = self.cleaned_data["dni"]
        new = Usuario.objects.filter(dni = dni)  
        if new.count():  
            raise ValidationError("Ya existe una cuenta con el DNI. Probá con otro.")  
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
        user = Usuario.objects.crear_usuario(  
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
    
    dni =  forms.CharField(max_length=8, label = "DNI")
    password = forms.CharField(label = "Contraseña", widget=forms.PasswordInput)
    clave_alfanumerica = forms.CharField(label= "Clave alfanumérica", max_length=5)

    class Meta:
        model = Usuario
        fields = ("dni","password","clave_alfanumerica")
   
    def clean(self):

        if self.is_valid():
            dni = self.cleaned_data['dni']
            password = self.cleaned_data['password']
            clave_alfanumerica = self.cleaned_data['clave_alfanumerica']
            try:
                user = Usuario.objects.get(dni=dni)
            except Usuario.DoesNotExist:
                 raise ValidationError("El DNI ingresado no se encuentra registrado en el sistema.")
            if not(user.check_password(password) and (user.clave_alfanumerica == clave_alfanumerica)):
                raise forms.ValidationError("DNI y/o contraseñas inválidas")