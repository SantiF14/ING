"""VacunAsist URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from VacunAsist.views import *
from gestion_de_usuarios.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Index/', index, name = "Index"), 
    path('Signup/', registrar, name = "Register"), 
    path('Login/', iniciar_sesion, name = "Login"),
    path('Logout', cerrar_sesion, name = "Logout"),
    path('home/', home, name='Home'),
    path('inscribir_campania_gripe/', inscribir_campania_gripe),
    path('inscribir_campania_COVID/', inscribir_campania_COVID),
    path('inscribir_campania_fiebre_amarilla/', inscribir_campania_fiebre_amarilla),
    path('cargar_vacuna_aplicada_con_turno/', cargar_vacuna_con_turno),
    path('visualizar_stock_vacunador/', visualizar_stock_vacunador, name="VacunasStock"),
    path('visualizar_stock_adm/', visualizar_stock_administrador),
    path('cargar_vacuna_stock/', cargar_vacuna_stock),
    path('eliminar_vacuna_stock/', eliminar_vacuna_stock),
    path('mostrar_mis_turnos/', mostrar_mis_turnos, name="MisTurnos"),
    path('mostrar_vacunas_aplicadas/', mostrar_vacunas_aplicadas, name = 'MisVacunas'),
    path('turnos_del_dia/', ver_turnos_del_dia, name="TurnosHoy"),
    path("imprimir_certificado/", descargar_certificado_fiebre_amarilla),
]