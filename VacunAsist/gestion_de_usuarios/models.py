from django.db import models
from gestion_de_turnos.models import Vacunatorio

# Create your models here.

class Persona(models.Model):
    dni = models.CharField(unique=True,max_length=8,editable=False)
    nombre_apellido = models.CharField(max_length=50)
    opciones_sexo = [("F","Femenino"),("M","Masculino")]
    sexo = models.CharField(max_length=1,choices=opciones_sexo)
    email = models.EmailField()
    es_adm = models.BooleanField(default=False)
    fecha_nacimiento = models.DateField()
    contrasenia = models.CharField()  #ver max_length por hashing/encriptacion
    clave_alfanumerica = models.CharField(max_length=4)
    vacunatorio_pref = models.ForeignKey(Vacunatorio, on_delete=models.SET_NULL, null=True ) #deberiamos cambiar las HU en tal caso, noguta


