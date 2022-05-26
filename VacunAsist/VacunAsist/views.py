from django.http import HttpResponse
from django.template import Template,Context,loader
from django.shortcuts import render
from gestion_de_usuarios.models import VacunaAplicada
from datetime import datetime
from dateutil.relativedelta import *
from gestion_de_usuarios.models import *




def Index(request):
    #doc_externo=open(os.path.normpath(os.path.join(os.path.dirname(
    #__file__), "VacunAsist", "templates", "index.html")))

    #plt=Template(doc_externo.read())

    #doc_externo.close()

    doc_externo=loader.get_template("index.html")

    documento=doc_externo.render({})

    return HttpResponse(documento)

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

def visualizar_mis_turnos(request):
    
    return render(request,"visualizar_mis_turnos.html")

def mostrar_mis_turnos(request):

    #cambiar
    vacunator= Vacunatorio.objects.first() 

    #cambiar
    usuario = Usuario.objects.filter(dni="40188236").first()
    
    turnos = Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])

    if (turnos):

        return render(request, "mostrar_mis_turnos.html",{"turnos":turnos, "dni":usuario.dni})

    else:
        mensaje="Usted no tiene turnos asignados"

    return HttpResponse(mensaje)



def visualizar_vacunas_aplicadas(request):
    
    return render(request,"visualizar_historial_vacunas_aplicadas.html")

def mostrar_vacunas_aplicadas(request):

    #cambiar
    usuario =  Usuario.objects.filter(dni="42291299").first()

    vacunas = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni)
        
    if (vacunas):

        return render(request, "mostrar_historial_vacuna_aplicada.html",{"vacunas":vacunas, "dni":usuario.dni})

    else:
        mensaje="Usted no tiene vacunas cargadas en el sistema"

    return HttpResponse(mensaje)


def inscribir_campania_gripe (request):

 
    usuario = Usuario.objects.filter(dni="42291299").get()

    inscripcion=Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])

    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    if (inscripcion):
        return render(request, "inscribir_campania_gripe.html",{"query":"no"})


    hoy = datetime.today()
    antes = hoy + relativedelta(years=-1)

    #filtro las vacunas aplicadas de la gripe de ese usuario y me fijo que sea en el ultimo anio, despues las ordeno en orden desendente y me quedo con el primero (sin que sea desendente es sin el -)
    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").filter(fecha__range=[antes,hoy]).order_by('-fecha').first()
    
    #si se dio una vacuna contra la gripe en el ultimo anio
    if (vacuna):
        if ((vacuna.fecha + relativedelta(years=1)) < (hoy.date() + relativedelta(days=7))):
            fecha_turno = hoy + relativedelta(days=7)
        else:
            fecha_turno = vacuna.fecha + relativedelta(years=1)
    else:
        #calculo la edad del usuario
        anios = hoy + relativedelta(days=-usuario.fecha_nacimiento.day)
        anios = anios + relativedelta(months=-usuario.fecha_nacimiento.month)
        anios = anios + relativedelta(years=-usuario.fecha_nacimiento.year)

        if (anios.year < 60):
            fecha_turno = hoy + relativedelta(months=6)
        else:
            fecha_turno = hoy + relativedelta(months=3) 

#estas lineas se guardan por posibles futuros problemas
#anios = hoy + relativedelta(days=-int(usuario.fecha_nacimiento[-2:]))
#anios = anios + relativedelta(months=-int((usuario.fecha_nacimiento[-5:])[:2]))
#anios = anios + relativedelta(years=-int(usuario.fecha_nacimiento[:4]))

    fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)

    inscripto = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").first()
    if (inscripto):
        inscripto.fecha=fecha_turno
        inscripto.save()
    else:
        #cambiar
        vacunatorio= Vacunatorio.objects.first()

        #cambiar
        vacu= Vacuna.objects.first() 

        ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=vacunatorio,vacuna=vacu)
        ins.save()

    return render(request, "inscribir_campania_gripe.html",{"query":"si"})


def inscribir_campania_COVID (request):
    
    usuario = Usuario.objects.get(dni="40188236")

    inscripto = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="COVID-19").first()

    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    if (inscripto):
        return render(request, "inscribir_campania_COVID.html",{"query":"no"})

    hoy = datetime.today()
    antes = hoy + relativedelta(months=-3)
    #calculo la edad del usuario
    anios = hoy + relativedelta(days=-usuario.fecha_nacimiento.day)
    anios = anios + relativedelta(months=-usuario.fecha_nacimiento.month)
    anios = anios + relativedelta(years=-usuario.fecha_nacimiento.year)

    

    if (anios.year < 18):
        return render(request, "inscribir_campania_COVID.html",{"query":"uwu"}) 
 
    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, marca__exact="COVID-19", fecha__range=[antes,hoy]).order_by('-fecha').first()
    
    #si se dio una vacuna contra la gripe en los ultimos 3 meses
    if (vacuna):
        if ((vacuna.fecha + relativedelta(months=3)) < (hoy.date() + relativedelta(days=7))):
            fecha_turno = hoy + relativedelta(days=7)
        else:
            fecha_turno = vacuna.fecha + relativedelta(months=3)

    elif (anios.year > 60) or (usuario.de_riesgo): 
        fecha_turno = hoy + relativedelta(days=7)
        fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
    else:
        fecha_turno = None

    inscripto=Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="COVID-19").filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])
    

    if (inscripto):
        inscripto.fecha=fecha_turno
        inscripto.save()
    else:
        #cambiar
        vacunatorio= Vacunatorio.objects.first()

        #cambiar
        vacu= Vacuna.objects.last() 

        ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=vacunatorio,vacuna=vacu)
        ins.save()

    return render(request, "inscribir_campania_COVID.html",{"query":"si"})



def cargar_vacuna_aplicada_con_turno(request):
    return render(request, "cargar_vacuna_aplicada_con_turno.html")


def resultado_carga_vacuna(request):

    datos = request

    dni = request.POST.get("DNI")
    tipo = request.POST.get("tipo")
    marca = request.POST.get("marca")
    lote = request.GET.get("lote")

    hoy = datetime.today()
    
    fecha_turno = None

    if (str(tipo) == "COVID-19"):

        fecha_turno = hoy + relativedelta(months=3)
        fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
    elif (str(tipo) == "Gripe"):
        fecha_turno = hoy + relativedelta(years=1)
        fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
    

    vacu= Vacuna.objects.filter(tipo__exact=tipo).first()

    usuario = Usuario.objects.get(dni=dni)

   
    if (tipo != "Fiebre_Amarilla"):
            inscripto = Inscripcion.objects.get(usuario_id=usuario.dni)
            if (inscripto):
                inscripto.fecha=fecha_turno
                inscripto.save()
            else:
                #cambiar
                vacunatorio= Vacunatorio.objects.first() 
                inscripto = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=vacunatorio,vacuna=vacu)
                inscripto.save()

    vacuna = VacunaAplicada(usuario=usuario,vacuna=vacu,fecha=fecha_turno,marca=marca,lote=lote,con_nosotros=True)
    vacuna.save()

    return render(request, "resultado_carga_vacuna.html")