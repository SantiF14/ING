from django.http import HttpResponse
from django.template import Template,Context,loader
from django.shortcuts import render
from gestion_de_usuarios.models import VacunaAplicada
from datetime import datetime
from dateutil.relativedelta import *
from gestion_de_usuarios.models import *
from VacunAsist.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required


def calcular_edad(fecha_nacimiento):
    hoy = datetime.today()
    anios = hoy + relativedelta(days=-usuario.fecha_nacimiento.day)
    anios = anios + relativedelta(months=-usuario.fecha_nacimiento.month)
    anios = anios + relativedelta(years=-usuario.fecha_nacimiento.year)
    return (anios)

def Index(request):
    doc_externo=loader.get_template("index.html")

    documento=doc_externo.render({})

    return HttpResponse(documento)

@login_required
def visualizar_mis_turnos(request):
    
    return render(request,"visualizar_mis_turnos.html")

@login_required
def mostrar_mis_turnos(request):

    usuario = request.user

    #para probar cositas
    #usuario =  Usuario.objects.filter(dni="42291299").first()

    turnos = Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])

    if (turnos):

        return render(request, "mostrar_mis_turnos.html",{"turnos":turnos, "dni":usuario.dni})

    else:
        mensaje="Usted no tiene turnos asignados"

    return HttpResponse(mensaje)


@login_required
def visualizar_vacunas_aplicadas(request):
    
    return render(request,"visualizar_historial_vacunas_aplicadas.html")

@login_required
def mostrar_vacunas_aplicadas(request):


    usuario = request.user

    vacunas = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni)
        
    if (vacunas):

        return render(request, "mostrar_historial_vacuna_aplicada.html",{"vacunas":vacunas, "dni":usuario.dni})

    else:
        mensaje="Usted no tiene vacunas cargadas en el sistema"

    return HttpResponse(mensaje)

@login_required
def inscribir_campania_gripe (request):

 
    usuario = request.user

    inscripcion=Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])

    #si ya esta inscripto
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
        anios = calcular_edad(usuario.fecha_nacimiento)
        if (anios.year < 60):
            fecha_turno = hoy + relativedelta(months=6)
        else:
            fecha_turno = hoy + relativedelta(months=3) 

#estas lineas se guardan por posibles futuros problemas
#anios = hoy + relativedelta(days=-int(usuario.fecha_nacimiento[-2:]))
#anios = anios + relativedelta(months=-int((usuario.fecha_nacimiento[-5:])[:2]))
#anios = anios + relativedelta(years=-int(usuario.fecha_nacimiento[:4]))

    fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)

    vacuna= Vacuna.objects.filter(tipo="Gripe").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio,vacuna=vacu)
    ins.save()
    html_message = loader.render_to_string('email_turno_gripe.html',{'fecha_turno': fecha_turno})
    send_mail('Fecha de turno para vacuna contra la gripe',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)

    return render(request, "inscribir_campania_gripe.html",{"query":"si"})

@login_required
def inscribir_campania_COVID (request):
    
    usuario = request.user

    hoy = datetime.today()
    antes = hoy + relativedelta(months=-3)

    #calculo la edad del usuario
    anios = calcular_edad(usuario.fecha_nacimiento)

    if (anios.year < 18):
        return render(request, "inscribir_campania_COVID.html",{"query":"uwu"}) 


    inscripto = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="COVID-19").first()

    #si ya esta inscripto
    if (inscripto):
        return render(request, "inscribir_campania_COVID.html",{"query":"no"})

    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, marca__exact="COVID-19", fecha__range=[antes,hoy]).order_by('-fecha').first()
    
    #si se dio una vacuna contra el COVID en los ultimos 3 meses
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

    


    vacuna= Vacuna.objects.filter(tipo="COVID-19").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio,vacuna=vacuna)
    ins.save()

    if (fecha_turno != None):
        html_message = loader.render_to_string('email_turno_COVID-19.html',{'fecha_turno': fecha_turno})
        send_mail('Fecha de turno para vacuna contra el COVID-19',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)

    return render(request, "inscribir_campania_COVID.html",{"query":"si"})

@login_required
def inscribir_campania_fiebre_amarilla(request):
    
    usuario = request.user

    hoy = datetime.today()
    
    #calculo la edad del usuario
    anios = calcular_edad(usuario.fecha_nacimiento)

    if (anios.year > 60):
        return render(request, "inscribir_campania_fiebre_amarilla.html",{"query":"uwu"}) 


    inscripto = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="Fiebre_amarilla").first()
    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, marca__exact="Fiebre_amarilla")

    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    if (inscripto) or (vacuna):
        return render(request, "inscribir_campania_fiebre_amarilla.html",{"query":"no"})
    
    fecha_turno = None

    vacuna= Vacuna.objects.filter(tipo="Fiebre_amarilla").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio,vacuna=vacu)
    ins.save()

    return render(request, "inscribir_campania_fiebre_amarilla.html",{"query":"si"})

@login_required
def cargar_vacuna_aplicada_con_turno(request):
    return render(request, "cargar_vacuna_aplicada_con_turno.html")

@login_required
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

                inscripto = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio,vacuna=vacu)
                inscripto.save()

    vacuna = VacunaAplicada(usuario=usuario,vacuna=vacu,fecha=fecha_turno,marca=marca,lote=lote,con_nosotros=True)
    vacuna.save()

    return render(request, "resultado_carga_vacuna.html")