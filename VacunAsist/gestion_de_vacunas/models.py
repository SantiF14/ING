from django.db import models
from gestion_de_usuarios.models import Usuario
from gestion_de_turnos.models import Vacunatorio

from datetime import date
# Create your models here.



class Vacuna(models.Model):
    tipo = models.CharField(max_length=20)

class VacunaAplicada(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)
    vacuna = models.ForeignKey(Vacuna, on_delete=models.DO_NOTHING)
    fecha = models.DateField(default=date.today)
    marca = models.CharField(max_length=20, blank=True, null=True)
    lote = models.CharField(max_length=20, blank=True, null=True)
    con_nosotros = models.BooleanField()


class VacunaVacunatorio(models.Model):
    vacuna = models.ForeignKey(Vacuna)
    vacunatorio = models.ForeignKey(Vacunatorio, on_delete=models.PROTECT)
    stock_actual = models.PositiveIntegerField()

