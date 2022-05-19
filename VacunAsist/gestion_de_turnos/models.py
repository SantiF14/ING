from django.db import models

# Create your models here.

class Vacunatorio(models.Model):
    nombre = models.CharField(max_length=30)
    direccion = models.CharField(max_length=25)
    email = models.EmailField()
    numero_telefono = models.CharField(max_length=20)
    



