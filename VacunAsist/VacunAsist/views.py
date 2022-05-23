from django.http import HttpResponse
from django.template import Template,Context,loader
from django.shortcuts import render
from gestion_de_usuarios.models import VacunaAplicada
from datetime import datetime
from dateutil.relativedelta import relativedelta
from gestion_de_usuarios.models import *




def Index(request):
    #doc_externo=open(os.path.normpath(os.path.join(os.path.dirname(
    #__file__), "VacunAsist", "templates", "index.html")))

    #plt=Template(doc_externo.read())

    #doc_externo.close()

    doc_externo=loader.get_template("index.html")

    documento=doc_externo.render({})

    return HttpResponse(documento)

def visualizar_vacunas_aplicadas(request):
    
    return render(request,"visualizar_historial_vacunas_aplicadas.html")

#def buscar(request):
#
#    us = Usuario("40188236","Luciano_Lopez","M","lucholopezlp@hotmail.com",False,datetime(1997, 3, 13),"lalala12","lala")
#
#    vac = VacunaAplicada.objects.filter(usuario_id__dni__exact=us.dni)
#        
#    if (vac):
#
#        return render(request, "mostrar_historial_vacuna_aplicada.html",{"Usu":vac, "query":us.dni})
#
#    else:
#        mensaje="Usted no tiene vacunas cargadas en el sistema"
#
#    return HttpResponse(mensaje)

def buscar(request):

    us = Usuario("40188236","Luciano_Lopez","M","lucholopezlp@hotmail.com",False,datetime(1997, 3, 13),"lalala12","lala")

    vac = VacunaAplicada.objects.filter(usuario_id__dni__exact=us.dni)
        
    if (vac):

        return render(request, "mostrar_historial_vacuna_aplicada.html",{"Usu":vac, "query":us.dni})

    else:
        mensaje="Usted no tiene vacunas cargadas en el sistema"

    return HttpResponse(mensaje)

def inscribir_campania_gripe (request):

    us = Usuario("401883","Luciano_Lopez","M","lucholopezlp@hotmail.com",False,datetime(1997, 3, 13),"lalala12","lala")
    
    pepe=Inscripcion.objects.filter(usuario_id__dni__exact=us.dni)

    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    if (pepe):
        return render(request, "inscribir_campania_gripe.html",{"query":"no"})

    hoy = datetime.today()
    antes = hoy + relativedelta(years=-1)


    #filtro las vacunas aplicadas de la gripe de ese usuarioy me fijo que sea en el ultimo anio
    vac = VacunaAplicada.objects.filter(usuario_id__dni__exact=us.dni).filter(marca__exact="Gripe").filter(fecha__range=[antes,hoy])
    
    #Filtro por las vacunas de aca a un anio atras
    #actual = gripe.filter(date_joined__range=[antes,hoy])

    #si se dio una vacuna contra la gripe en el ultimo anio
    if (vac):
        fecha_turno = hoy + relativedelta(years=1)

    else:
        #calculo la edad del usuario
        anios = hoy + relativedelta(days=-us.fecha_nacimiento.day)
        anios = anios + relativedelta(months=-us.fecha_nacimiento.month)
        anios = anios + relativedelta(years=-us.fecha_nacimiento.year)

        if (anios.year < 60):
            fecha_turno = hoy + relativedelta(months=6)
        else:
            fecha_turno = hoy + relativedelta(months=3)
    #vacunator= Vacunatorio(nombre="Polideportivo",email="polideportivo@gmail.com",direccion="155",numero_telefono="2213169122")
    vacunator= Vacunatorio.objects.first() #cambiar anashey
    vacun= Vacuna.objects.first() #cambiar anashey
    ins = Inscripcion(usuario=us,fecha=fecha_turno,vacunatorio=vacunator,vacuna=vacun)
    
    ins.save()

    return render(request, "inscribir_campania_gripe.html",{"query":"si"})


def inscribir_campania_COVID (request):

    us = Usuario("4018","Luciano_Lopez","M","lucholopezlp@hotmail.com",False,datetime(2015, 3, 13),"lalala12","lala")

    hoy = datetime.today()
    antes = hoy + relativedelta(months=-3)

    anios = hoy + relativedelta(days=-us.fecha_nacimiento.day)
    anios = anios + relativedelta(months=-us.fecha_nacimiento.month)
    anios = anios + relativedelta(years=-us.fecha_nacimiento.year)

    if (anios.year < 18):
        return render(request, "inscribir_campania_COVID.html",{"query":"uwu"})
    
    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    pepe=Inscripcion.objects.filter(usuario_id__dni__exact=us.dni)
    if (pepe):
        return render(request, "inscribir_campania_COVID.html",{"query":"no"})

    

    #filtra las vacunas por dni, que sean de covid y que se lo haya dado un vacuna en los ultimos 3 meses, despues los ordeno en orden desendente y me quedo con el primero (sin que sea desendente es sin el -)
    vac = VacunaAplicada.objects.filter(usuario_id__dni__exact=us.dni, marca__exact="COVID-19", fecha__range=[antes,hoy]).order_by('-fecha').first()

    #hay que ver lo de la condicion de salud
    #si se dio una vacuna en los ultimos 3 meses
    if (vac):
        
        fecha_turno = vac.fecha + relativedelta(months=3)

    elif (anios.year > 60): #o tiene condiciones de salud
        fecha_turno = hoy + relativedelta(days=7)

    else:

        fecha_turno = None

    vacunator= Vacunatorio.objects.first() #cambiar anashey
    vacun= Vacuna.objects.last() #cambiar anashey
    ins = Inscripcion(usuario=us,fecha=fecha_turno,vacunatorio=vacunator,vacuna=vacun)
    
    ins.save()

    return render(request, "inscribir_campania_COVID.html",{"query":"si"})

def resultado_carga_vacuna(request):
    return render(request, "cargar_vacuna_aplicada_con_turno.html")


def cargar_vacuna_aplicada_con_turno(request):

    datos = request

    dni = request.GET.get("DNI")
    tipo = request.GET.get("tipo")
    marca = request.GET.get("marca")
    lote = request.GET.get("lote")

    hoy = datetime.today()

    fecha_turno = None

    if (str(tipo) == "COVID-19"):

        fecha_turno = hoy + relativedelta(months=3)

    elif (str(tipo) == "Gripe"):
        fecha_turno = hoy + relativedelta(years=1)
    
        
    
    us = Usuario.objects.filter(dni__exact=dni).first()
    vacun= Vacuna.objects.filter(tipo__exact=tipo).first()
    vac = VacunaAplicada(usuario=us,fecha=fecha_turno,vacuna=vacun,marca=marca,lote=lote,con_nosotros=True)
    vac.save()

    if (tipo != "Fiebre_Amarila"):
            vacunator= Vacunatorio.objects.first() #cambiar anashey
            ins = Inscripcion(usuario=us,fecha=fecha_turno,vacunatorio=vacunator,vacuna=vacun)
            ins.save()
            
    #actualizar permisos del usuario para que imprima el comprobante de la fiebre amarilla
    #else
        #actualizar el boton a imprimir comprobante en el usuario

    return render(request, "resultado_carga_vacuna.html")