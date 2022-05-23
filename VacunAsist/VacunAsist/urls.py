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
from VacunAsist.views import Index
from VacunAsist.views import visualizar_vacunas_aplicadas
from VacunAsist.views import buscar
from VacunAsist.views import inscribir_campania_gripe
from VacunAsist.views import inscribir_campania_COVID
from VacunAsist.views import cargar_vacuna_aplicada_con_turno
from VacunAsist.views import resultado_carga_vacuna

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Index/', Index), 
    path('visualizar_historial_vacunas_aplicadas/', visualizar_vacunas_aplicadas),
    path('buscar/', buscar),
    path('inscribir_campania_gripe/', inscribir_campania_gripe),
    path('inscribir_campania_COVID/', inscribir_campania_COVID),
    path('cargar_vacuna_aplicada_con_turno/', cargar_vacuna_aplicada_con_turno),
    path('resultado_carga_vacuna/', resultado_carga_vacuna),
]
