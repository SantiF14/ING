from pyexpat import model
from django.db import models
from datetime import date

# Create your models here.

class Usuario(models.Model):
    dni = models.CharField(primary_key=True, max_length=8, editable=False)
    nombre_apellido = models.CharField(max_length=50)
    opciones_sexo = [("F","Femenino"),("M","Masculino")]
    sexo = models.CharField(max_length=1,choices=opciones_sexo)
    email = models.EmailField()
    de_riesgo = models.BooleanField(default=False)
    es_adm = models.BooleanField(default=False)
    fecha_nacimiento = models.DateField()
    contrasenia = models.CharField(max_length=30)  #ver max_length por hashing/encriptacion
    clave_alfanumerica = models.CharField(max_length=5)
    vacunatorio_pref = models.ForeignKey("Vacunatorio", on_delete=models.SET_NULL, null=True) #deberiamos cambiar las HU en tal caso, noguta

class Vacunador(models.Model):
    usuario = models.ForeignKey("Usuario", unique=True, on_delete=models.CASCADE)
    vacunatorio_de_trabajo = models.ForeignKey("Vacunatorio", on_delete=models.PROTECT)

class Inscripcion(models.Model):
    class ClaveUnivoca:
        unique_together = (("usuario","vacuna"),)

    usuario = models.ForeignKey("Usuario", on_delete=models.SET_NULL, null=True) #decidir
    fecha = models.DateField(blank=True, null=True)
    vacunatorio = models.ForeignKey("Vacunatorio", on_delete=models.PROTECT)  #decidir
    vacuna = models.ForeignKey("Vacuna", on_delete=models.PROTECT) #decidir



class Vacunatorio(models.Model):
    nombre = models.CharField(max_length=30)
    direccion = models.CharField(max_length=25)
    email = models.EmailField()
    numero_telefono = models.CharField(max_length=20)

class Vacuna(models.Model):
    tipo = models.CharField(max_length=20)

class VacunaAplicada(models.Model):
    usuario = models.ForeignKey("Usuario", on_delete=models.DO_NOTHING)
    vacuna = models.ForeignKey(Vacuna, on_delete=models.DO_NOTHING)
    fecha = models.DateField(default=date.today)
    marca = models.CharField(max_length=20, blank=True, null=True)
    lote = models.CharField(max_length=20, blank=True, null=True)
    con_nosotros = models.BooleanField()


class VacunaVacunatorio(models.Model):
    vacuna = models.ForeignKey(Vacuna, on_delete=models.PROTECT)
    vacunatorio = models.ForeignKey(Vacunatorio, on_delete=models.PROTECT)
    stock_actual = models.PositiveIntegerField()