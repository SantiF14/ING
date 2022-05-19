
from django.db import models
from gestion_de_usuarios.models import Usuario
from gestion_de_vacunas.models import Vacuna
#import gestion_de_usuarios as app_usuarios
#import gestion_de_vacunas as app_vacunas
# Create your models here.


class Vacunatorio(models.Model):
    nombre = models.CharField(max_length=30)
    direccion = models.CharField(max_length=25)
    email = models.EmailField()
    numero_telefono = models.CharField(max_length=20)


class Inscripcion(models.Model):
    class ClaveUnivoca:
        unique_together = (("usuario","vacuna"),)

    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True) #decidir
    fecha = models.DateField(blank=True, null=True)
    vacunatorio = models.ForeignKey(Vacunatorio, on_delete=models.PROTECT)  #decidir
    vacuna = models.ForeignKey(Vacuna, on_delete=models.PROTECT) #decidir
    


