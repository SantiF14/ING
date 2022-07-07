
from http.client import REQUEST_ENTITY_TOO_LARGE
from django.template import loader
from django.shortcuts import render, redirect
from gestion_de_usuarios.views import gestionar_usuarios_admin
from gestion_de_usuarios.models import VacunaAplicada
from datetime import datetime, date
from dateutil.relativedelta import *
from gestion_de_usuarios.models import *
from VacunAsist.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from gestion_de_usuarios.views import ver_turnos_del_dia
from django.urls import reverse
from urllib.parse import urlencode
import re
import requests
import random, string

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def index(request):
    if request.user.is_authenticated:
        return redirect(home)
    return render(request, 'index.html', {})

def home(request):

    if request.user.is_authenticated:
        context = dict.fromkeys(["user","rol","covid","fiebre_amarilla","gripe","mensaje","titulo","vacuna_fa"], "No")
        user = request.user
        context["user"] = user
        context["mensaje"] = request.session.get('mensaje', "")
        context["titulo"] = request.session.get('titulo', "")
        request.session["mensaje"] = ""
        request.session["titulo"] = ""

        inscripciones = Inscripcion.objects.filter(usuario = user)
        covid = inscripciones.filter(vacuna = Vacuna.objects.filter(tipo = "COVID-19").first()) #ARREGLAR
        fiebre_amarilla = inscripciones.filter(vacuna = Vacuna.objects.filter(tipo = "Fiebre_amarilla").first())
        vacuna_fa = VacunaAplicada.objects.filter(usuario = user, vacuna = Vacuna.objects.filter(tipo = "Fiebre_amarilla").first(),con_nosotros = True)
        gripe = inscripciones.filter(vacuna = Vacuna.objects.filter(tipo = "Gripe").first())
        if(vacuna_fa):
            context["vacuna_fa"] = "Si"
        if (covid):
            context["covid"] = "Si"
        if (fiebre_amarilla):
            context["fiebre_amarilla"] = "Si"
        if (gripe):
            context["gripe"] = "Si"

    

        return render(request,"home.html", context)

    return redirect('Index')    

@login_required
def mostrar_mis_turnos(request):
    usuario = request.user
    context = request.session.get("context",{})
    if (context == {}):
        context["mensaje"] = request.session.get('mensaje',"")
    turnos = Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])
 
    if not turnos:
        context["mensaje"]="Usted no tiene turnos asignados."
        
    request.session["context"] = {}
    context["turnos"]=turnos   
    return render(request, "mostrar_mis_turnos.html",context)

@login_required
def mostrar_vacunas_aplicadas(request):

    usuario = request.user
    context=dict.fromkeys(["vacunas","tipos","mensaje","today"],"")
    vacunas = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni)
    context["vacunas"]= vacunas
    context["tipos"]=Vacuna.objects.all()
    context["today"]=str(date.today())
    if not vacunas:
        context["mensaje"]= "Usted no tiene vacunas cargadas en el sistema"
    
    context["mensaje"] = request.session.get('mensaje', "")
    request.session["mensaje"] = ""
    return render(request, "mostrar_historial_vacuna_aplicada.html",context)

@login_required
def inscribir_campania_gripe (request):
 
    usuario = request.user

    inscripcion = Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])

    #si ya esta inscripcion
    if (inscripcion):
        request.session["mensaje"] = "Ya estas inscripto"
        return home(request)


    hoy = datetime.today()

    antes = hoy + relativedelta(years=-1)
    #antes = hoy + relativedelta(years=-1)  
  

    #filtro las vacunas aplicadas de la gripe de ese usuario y me fijo que sea en el ultimo anio, despues las ordeno en orden desendente y me quedo con el primero (sin que sea desendente es sin el -)
    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").order_by('-fecha').first()
    #vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, vacuna_id__tipo__exact="Gripe")
    #si se dio una vacuna contra la gripe en el ultimo anio
    #vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, marca__exact="Gripe", fecha__range=[antes,hoy]).order_by('-fecha').first()
    if (vacuna):
        if ((vacuna.fecha + relativedelta(years=1)) < (hoy.date() + relativedelta(days=7))):
            fecha_turno = hoy + relativedelta(days=7)
        else:
            fecha_turno = vacuna.fecha + relativedelta(years=1)
    else:
        #calculo la edad del usuario
        anios = calculate_age(usuario.fecha_nacimiento)
        if (anios < 60):
            fecha_turno = hoy + relativedelta(months=6)
        else:
            fecha_turno = hoy + relativedelta(months=3) 

#estas lineas se guardan por posibles futuros problemas
#anios = hoy + relativedelta(days=-int(usuario.fecha_nacimiento[-2:]))
#anios = anios + relativedelta(months=-int((usuario.fecha_nacimiento[-5:])[:2]))
#anios = anios + relativedelta(years=-int(usuario.fecha_nacimiento[:4]))

    fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)

    vacuna= Vacuna.objects.filter(tipo="Gripe").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio_pref,vacuna=vacuna)
    ins.save()
    html_message = loader.render_to_string('email_turno.html',{'fecha': fecha_turno, "user": usuario, "vacuna": "gripe"})
    try:
        send_mail('Notificación de turno para vacuna contra la gripe',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
    except:
        pass
    request.session["mensaje"]= f"Usted se inscribió a la campaña de vacunación de la gripe. Le hemos enviado un mail a la dirección {usuario.email} con la fecha de su turno. Por favor, revise su correo no deseado.",
    request.session["titulo"]="Inscripción exitosa"
    return redirect(home)

@login_required
def inscribir_campania_COVID (request):
    
    usuario = request.user

    hoy = datetime.today()
    antes = hoy + relativedelta(months=-3)

    #calculo la edad del usuario
    anios = calculate_age(usuario.fecha_nacimiento)

    if (anios < 18):
        request.session["mensaje"] = "Debe ser mayor de edad para poder inscribirse."
        request.session["titulo"] = "Inscripción fallida"
        return redirect(home)


    inscripcion = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="COVID-19").first()

    #si ya esta inscripto
    if (inscripcion):
        return redirect(home)

    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="COVID-19").order_by('-fecha').first()
    
    #si se dio una vacuna contra el COVID en los ultimos 3 meses
    if (vacuna):
        if ((vacuna.fecha + relativedelta(months=3)) < (hoy.date() + relativedelta(days=7))):
            fecha_turno = hoy + relativedelta(days=7)
        else:
            fecha_turno = vacuna.fecha + relativedelta(months=3)

    elif (anios > 60) or (usuario.de_riesgo): 

        fecha_turno = hoy + relativedelta(days=7)
        fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
    else:
        fecha_turno = None

    vacuna= Vacuna.objects.filter(tipo="COVID-19").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio_pref,vacuna=vacuna)
    ins.save()

    if (fecha_turno != None):
        html_message = loader.render_to_string('email_turno.html',{'fecha': fecha_turno, "user": usuario, "vacuna": "COVID-19"})
        try:
            send_mail('Notificación de turno para vacuna contra el COVID-19',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
        except:
            pass
        request.session["mensaje"]= f"Usted se inscribió a la campaña de vacunación del COVID-19. Le hemos enviado un mail a la dirección {usuario.email} con la fecha de su turno. Por favor, revise su correo no deseado."
        request.session["titulo"]="Inscripción exitosa"
        return redirect(home)

    request.session["mensaje"]="Usted se inscribió a la campaña de vacunación del COVID-19."
    request.session["titulo"]= "Inscripción exitosa"
    return redirect(home)

@login_required
def inscribir_campania_fiebre_amarilla(request):
    
    usuario = request.user

    hoy = datetime.today()
    
    #calculo la edad del usuario
    anios = calculate_age(usuario.fecha_nacimiento + relativedelta(days=15))

    if (anios  > 60):
        request.session["mensaje"] = "Usted supera el límite de edad para inscribirse a esta campaña."
        request.session["titulo"] = "Inscripción fallida"
        return redirect(home)


    inscripcion = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="Fiebre_amarilla").first()
    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, vacuna = Vacuna.objects.filter(tipo = "Fiebre_amarilla").first())

    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    if (vacuna):
        request.session["mensaje"] = "Usted ya tiene una vacuna aplicada en otro vacunatorio"
        request.session["titulo"] = "Inscripción fallida"
        return redirect(home)
    
    fecha_turno = None

    vacuna= Vacuna.objects.filter(tipo="Fiebre_amarilla").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio_pref,vacuna=vacuna)
    ins.save()

    request.session["mensaje"] = "Usted se inscribió a la campaña de vacunación de la fiebre amarilla"
    request.session["titulo"] = "Inscripción exitosa"

    return redirect(home) 

@login_required
def cargar_vacuna_con_turno(request):
    user = request.user
    dni = request.POST.get("Dni")
    tipo = request.POST.get("Tipo")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")

    hoy = datetime.today()
    
    fecha_turno = None

    if (str(tipo) == "COVID-19"):

        fecha_turno = hoy + relativedelta(months=3)
        fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
    elif (str(tipo) == "Gripe"):
        fecha_turno = hoy + relativedelta(years=1)
        fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
    

    vacu = Vacuna.objects.filter(tipo__exact=tipo).first()

    usuario = Usuario.objects.get(dni=dni)

    inscripcion = Inscripcion.objects.get(usuario_id=usuario.dni,vacuna_id__tipo=tipo)
    if (tipo != "Fiebre_amarilla"):
            if (inscripcion): #REVISAR : Innecesario, si entra a esta funcion la inscripcion existe
                inscripcion.fecha=fecha_turno
                inscripcion.save()
            else:
                inscripcion = inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio,vacuna=vacu)
                inscripcion.save()
    else:
        inscripcion.delete()
        
    #REVISAR : Deberia restar uno a vacunas en stock? Depende de como lo terminemos modelando.

    vacuna = VacunaAplicada(usuario=usuario,vacuna=vacu,fecha=hoy,marca=marca,lote=lote,con_nosotros=True,vacunatorio=user.vacunatorio_trabajo)
    vacuna.save()


    request.session["mensaje"]="La vacuna se cargó de forma exitosa."
    
    return redirect(ver_turnos_del_dia)

@login_required
def cargar_vacuna_stock(request):
    cant = int(request.POST.get("Cantidad"))
    tipo = request.POST.get("Tipo")
    lugar = request.POST.get("lugar")
    
    cant = int(cant)
    if (cant < 0):
        #fijarse donde lo va a retornar
        request.session["mensaje"] = "No se puede ingresar una cantidad negativa. Ingrese un valor positivo."
        return redirect(visualizar_stock_administrador)

    user = request.user

    vacuna = Vacuna.objects.get(tipo=tipo)

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio__nombre=lugar, vacuna=vacuna).first()

    if (vacuna_vacunatorio):
        vacuna_vacunatorio.stock_remanente = vacuna_vacunatorio.stock_remanente + cant
    else:
        vacuna_vacunatorio = VacunaVacunatorio(vacunatorio=lugar,vacuna=vacuna,stock_remanente=cant)

    vacuna_vacunatorio.save()

    #fijarse donde lo va a retornar
    request.session["mensaje"] = f'Las vacunas se cargaron de forma exitosa en el sistema, cantidad actual de vacunas de {tipo} en el vacunatorio {vacuna_vacunatorio.vacunatorio.nombre} es de: {vacuna_vacunatorio.stock_remanente}.'
    return redirect(visualizar_stock_administrador)

@login_required
def eliminar_vacuna_stock(request):
    cant = request.POST.get("Cantidad")
    tipo = request.POST.get("Tipo")
    lugar = request.POST.get("lugar")
    cant =int(cant)
    if (cant < 0):
        #fijarse donde lo va a retornar
        request.session["mensaje"] = 'Debe ingresarse un numero positivo de vacunas a eliminar.'
        return redirect(visualizar_stock_administrador)

    user = request.user

    vacuna = Vacuna.objects.get(tipo=tipo)

    vacvacunatorio = VacunaVacunatorio.objects.filter(vacunatorio__nombre=lugar,vacuna=vacuna).first()

    if (vacvacunatorio.stock_remanente < cant):
        mensaje = f'No pueden eliminarse más vacunas de las que hay en stock ({vacvacunatorio.stock_remanente}).'
    else:
        vacvacunatorio.stock_remanente = vacvacunatorio.stock_remanente - cant
        vacvacunatorio.save()
        mensaje = f'Las vacunas se eliminaron correctamente, cantidad actual de vacunas de {tipo} en el vacunatorio {vacvacunatorio.vacunatorio.nombre} es de: {vacvacunatorio.stock_remanente}.'
    

    #fijarse donde lo va a retornar
    request.session["mensaje"] = mensaje
    return redirect(visualizar_stock_administrador)


@login_required
def agregar_vacuna_gripe_historial(request):

    marca = request.POST.get("Marca")
    tipo = request.POST.get("Tipo")
    fecha = datetime.strptime(request.POST.get("Fecha"), '%Y-%m-%d').date()
    lote = request.POST.get("Lote")
    user = request.user
    hoy = datetime.today()

    vacuna = Vacuna.objects.get(tipo=tipo)

    inscripcion = Inscripcion.objects.filter(usuario=user,vacuna=vacuna).first()
    fecha_turno = None
    if inscripcion:
        if (inscripcion.fecha < (fecha + relativedelta(years=1))):
            if ((fecha + relativedelta(years=1)) < (hoy.date() + relativedelta(days=7))):
                fecha_turno = hoy + relativedelta(days=7)
            else:
                fecha_turno = fecha + relativedelta(years=1)
            fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
            inscripcion.fecha = fecha_turno
            inscripcion.save()
            #envia el mail
            html_message = loader.render_to_string('email_turno.html',{'fecha': fecha_turno, "user": request.user, "vacuna": "Gripe"})
            try:    
                send_mail('Notificación de actualizacion de turno de vacuna contra la gripe',"",EMAIL_HOST_USER,[request.user.email], html_message=html_message)
            except:
                pass

    fecha = date(fecha.year, fecha.month, fecha.day)

    vacunaaplicada = VacunaAplicada(usuario=user,fecha=fecha,vacuna=vacuna,marca=marca,lote=lote,con_nosotros=False,vacunatorio=None)
    vacunaaplicada.save()


@login_required
def agregar_vacuna_COVID_historial(request):
    marca = request.POST.get("Marca")
    tipo = request.POST.get("Tipo")
    fecha = datetime.strptime(request.POST.get("Fecha"), '%Y-%m-%d').date()
    lote = request.POST.get("Lote")
    user = request.user
    hoy = datetime.today()

    vacuna = Vacuna.objects.get(tipo=tipo)

    inscripcion = Inscripcion.objects.filter(usuario=user,vacuna=vacuna).first()
    fecha_turno = None

    #ver si no existe la inscripcion tira error, en caso de que si, cambiar a esto y probar if (inscripcion) and (inscripcion.fecha < (fecha + relativedelta(years=3))):
    #si eso no funciona llamar al 0800-222-lucho para mas informacion
    if inscripcion:
        if (inscripcion.fecha == None) or (inscripcion.fecha < (fecha + relativedelta(months=3))):
            if  ((fecha + relativedelta(months=3)) < (hoy.date() + relativedelta(days=7))):
                fecha_turno = hoy + relativedelta(days=7)
            else:
                fecha_turno = fecha + relativedelta(months=3)
            fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
            inscripcion.fecha = fecha_turno
            inscripcion.save()
            #envia el mail
            html_message = loader.render_to_string('email_turno.html',{'fecha': fecha_turno, "user": request.user, "vacuna": "COVID-19"})
            try:    
                send_mail('Notificación de actualizacion de turno de vacuna contra el COVID-19',"",EMAIL_HOST_USER,[request.user.email], html_message=html_message)
            except:
                pass

    fecha = date(fecha.year, fecha.month, fecha.day)

    vacunaaplicada = VacunaAplicada(usuario=user,fecha=fecha,vacuna=vacuna,marca=marca,lote=lote,con_nosotros=False,vacunatorio=None)
    vacunaaplicada.save()


@login_required
def agregar_vacuna_fiebre_amarilla_historial(request):
    marca = request.POST.get("Marca")
    tipo = request.POST.get("Tipo")
    fecha = datetime.strptime(request.POST.get("Fecha"), '%Y-%m-%d').date()
    lote = request.POST.get("Lote")
    user = request.user

    vacuna = Vacuna.objects.get(tipo=tipo)

    inscripcion = Inscripcion.objects.filter(usuario=user,vacuna=vacuna).first()

    if (inscripcion):
        inscripcion.delete()

    fecha = date(fecha.year, fecha.month, fecha.day)

    vacunaaplicada = VacunaAplicada(usuario=user,fecha=fecha,vacuna=vacuna,marca=marca,lote=lote,con_nosotros=False,vacunatorio=None)
    vacunaaplicada.save()

@login_required
def agregar_vacuna_al_historial(request):
    
    tipo = request.POST.get("Tipo")
    if (tipo == "Gripe"):
        agregar_vacuna_gripe_historial(request)
    elif (tipo == "COVID-19"):
        agregar_vacuna_COVID_historial(request)
    else:
        agregar_vacuna_fiebre_amarilla_historial(request)

    #base_url = reverse('MisVacunas')  
    #query_string =  urlencode({'mensaje': "La vacuna ha sido cargada exitosamente"}) 
    #url = '{}?{}'.format(base_url, query_string) 
    #return redirect(url) 
    request.session["mensaje"] = "La vacuna ha sido cargada exitosamente."
    return redirect(mostrar_vacunas_aplicadas)
    #return redirect('/mostrar_vacunas_aplicadas/',mensaje="La vacuna ha sido cargada exitosamente.")




@login_required
def visualizar_stock_vacunador(request):
    #ver si al apretar un boton devuelve un tipo, no me acuerdo
    context = dict.fromkeys(["vacunas"], "")
    #context["mensaje"]=mensaje

    user = request.user
    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=user.vacunador.vacunatorio_de_trabajo)
    context["vacunas"]=vacuna_vacunatorio
    #ver si contemplar esto

    #cambiar return
    return render(request, 'vacunas.html', context)

#REVISAR
@login_required
def visualizar_stock_administrador(request):


    context = dict.fromkeys(["vacunas","mensaje"], "")

    vacuna_vacunatorio = VacunaVacunatorio
    context["vacunas"]=vacuna_vacunatorio.objects.filter()
    context["mensaje"]= request.session.get('mensaje', "")
    request.session["mensaje"] = ""
    #ver si contemplar esto

    #cambiar return
    return render(request, 'vacunas_adm.html', context)



@login_required
def boton_gripe(request):
    
    context = dict.fromkeys(["mensaje", "dni_a_cargar", "email_a_cargar","tipo_a_cargar"], "")

    user = request.user
    vacunador = Vacunador.objects.get(usuario_id=user.dni)
    sobrante = VacunaVacunatorio.objects.get(vacunatorio_id=vacunador.vacunatorio_de_trabajo_id, vacuna_id__tipo__exact="Gripe")
    
    if (sobrante.stock_remanente == 0):
        #cambiar return
        context["mensaje"] = 'No hay sobrante de vacunas de Gripe en este momento.'
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)

    dni = request.POST.get("Dni")
    
    vacunaaplicada = VacunaAplicada.objects.filter(usuario_id__dni__exact=dni).filter(vacuna_id__tipo__exact="Gripe").order_by('-fecha').first()
    hoy = datetime.today()

    if (vacunaaplicada) and ((hoy + relativedelta(years=-1)).date() < (vacunaaplicada.fecha)):
        #cambiar return
        context["mensaje"] = 'Esta persona tiene una vacuna aplicada en el ultimo año, no puede aplicarse la vacuna'
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)

    context["dni_a_cargar"] = dni
    context["email_a_cargar"] = request.POST.get("Email")
    context["tipo_a_cargar"] = "Gripe"
    request.session["context"] = context
    
    return redirect(ver_turnos_del_dia)

@login_required
def cargar_vacuna_gripe_sin_turno(request):

    context = {"mensaje":""}
    user = request.user

    dni = request.POST.get("Dni")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")
    usuario = Usuario.objects.filter(dni=dni).first()
    vacuna = Vacuna.objects.filter(tipo='Gripe').first()

    inscripcion = Inscripcion.objects.filter(usuario=usuario,vacuna=vacuna).first()

    hoy = datetime.today()
    hoy = date(hoy.year, hoy.month, hoy.day)

    vacuna_aplicada = VacunaAplicada(fecha=hoy, marca=marca, lote=lote, con_nosotros=True, usuario_id=dni, vacuna=vacuna, vacunatorio=user.vacunatorio_trabajo)
    vacuna_aplicada.save()

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=request.user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    if (vacuna_vacunatorio): #PROVISORIAMENTE: DEBERIAN ESTAR SI O SI TODAS LAS VACUNA_VACUNATORIO
        vacuna_vacunatorio.stock_remanente = vacuna_vacunatorio.stock_remanente - 1
        vacuna_vacunatorio.save()

    if (inscripcion):
        inscripcion.fecha = hoy + relativedelta(years=1)
        inscripcion.save()
        html_message = loader.render_to_string('email_turno.html',{'fecha': hoy + relativedelta(years=1), "vacuna": "gripe"})
        try:    
            send_mail('Notificación de actualizacion de turno para vacuna contra la gripe',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
        except:
            pass
        
    
    if (not usuario):
        email = request.POST.get("Email")
        html_message = loader.render_to_string('email_aviso_vacunacion.html',{'fecha': hoy, "vacuna": "gripe"})
        try:    
            send_mail('Vacunacion contra la gripe',"",EMAIL_HOST_USER,[email], html_message=html_message)
        except:
            pass
        
    context["mensaje"] = 'La vacuna se cargo de forma exitosa.'
    request.session["context"] = context
    return redirect(ver_turnos_del_dia)

@login_required
def boton_COVID(request):
    
    context = dict.fromkeys(["mensaje", "dni_a_cargar", "email_a_cargar","tipo_a_cargar"], "")

    user = request.user
    vacunador = Vacunador.objects.get(usuario_id=user.dni)
    sobrante = VacunaVacunatorio.objects.get(vacunatorio_id=vacunador.vacunatorio_de_trabajo_id, vacuna_id__tipo__exact="COVID-19")
    
    if (sobrante.stock_remanente == 0 ):
        #cambiar return
        context["mensaje"] = 'No hay sobrante de vacunas de COVID-19 en este momento.'
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)

    dni = request.POST.get("Dni")
    fecha_nacimiento = request.POST.get("Fecha_nacimiento")
    fecha_nacimiento = datetime.strptime(fecha_nacimiento,"%Y-%m-%d").date()
 #   usuario = Usuario.objects.filter(dni=dni).first()
#
 #   if (usuario):
 #       #calculo la edad del usuario
 #       anios = calculate_age(usuario.fecha_nacimiento)
#
 #       if (anios < 18):
 #           #cambiar return
 #           return nose(request, "La persona es menor de 18 años no puede aplicarse la vacuna")
     
    anios = calculate_age(fecha_nacimiento)
    
    if (anios < 18):
            #cambiar return
            context["mensaje"] = "La persona es menor de 18 años no puede aplicarse la vacuna"
            request.session["context"] = context
            return redirect(ver_turnos_del_dia)

    #-------------------------IMPORTANTE-----------------------------#
    #falta chequear lo de los 18n anios para el que no esta registrado, nose como vamos a obtener la fecha de nacimiento
    #-----------------------------------------------------------------#


    vacuna_aplicada = VacunaAplicada.objects.filter(usuario_id__dni__exact=dni).filter(vacuna_id__tipo__exact="COVID-19").order_by('-fecha').first()
    hoy = datetime.today()

    if (vacuna_aplicada) and ((hoy + relativedelta(months=-3)).date() < vacuna_aplicada.fecha): #chequear que este mayor este bien puesto y no sea menor
        #cambiar return
        context["mensaje"] = 'Esta persona tiene una vacuna aplicada en los ultimos tres meses, no puede aplicarse la vacuna'
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)
    
    #cambiar return en este caso todo esta ok xD
    context["dni_a_cargar"] = dni
    context["email_a_cargar"] = request.POST.get("Email")
    context["tipo_a_cargar"] = "COVID-19"
    request.session["context"] = context
    
    return redirect(ver_turnos_del_dia)

@login_required
def cargar_vacuna_COVID_sin_turno(request):

    context = {"mensaje":""}

    user = request.user
    dni = request.POST.get("Dni")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")
    usuario = Usuario.objects.filter(dni=dni).first()

    vacuna = Vacuna.objects.filter(tipo='COVID-19').first()
    inscripcion = Inscripcion.objects.filter(usuario_id=usuario,vacuna=vacuna).first()

    hoy = datetime.today()
    hoy = date(hoy.year, hoy.month, hoy.day)

    #en teoria deberia ser distinto el cargar la vacuna aplicada si esta registrado o no, pero si esto es legal, deberia funcionar para ambos
    vacuna_aplicada = VacunaAplicada(fecha=hoy, marca=marca, lote=lote, con_nosotros=True, usuario_id=dni,vacuna=vacuna, vacunatorio=user.vacunatorio_trabajo)
    vacuna_aplicada.save()

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=request.user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    if (vacuna_vacunatorio): #PROVISORIAMENTE: DEBERIAN ESTAR SI O SI TODAS LAS VACUNA_VACUNATORIO
        vacuna_vacunatorio.stock_remanente = vacuna_vacunatorio.stock_remanente - 1
        vacuna_vacunatorio.save()

    if (inscripcion):
        inscripcion.fecha = hoy + relativedelta(months=3)
        inscripcion.save()
        html_message = loader.render_to_string('email_turno.html',{'fecha': hoy + relativedelta(months=3), "vacuna": "COVID-19"})
        try:    
            send_mail('Notificación de actualizacion de turno para vacuna contra el COVID-19',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
        except:
            pass
    
    
    if (not usuario):
        email = request.POST.get("Email")
        html_message = loader.render_to_string('email_aviso_vacunacion.html',{'fecha': hoy, "vacuna": "COVID-19"})
        try:    
            send_mail('Vacunacion contra el COVID-19',"",EMAIL_HOST_USER,[email], html_message=html_message)
        except:
            pass
        
    context["mensaje"] = "La vacuna se cargo de forma exitosa."
    request.session["context"] = context
    return redirect(ver_turnos_del_dia)
    
@login_required
def boton_fiebre_amarilla(request):
    
    context = dict.fromkeys(["mensaje", "dni_a_cargar", "email_a_cargar","tipo_a_cargar"], "")
    
    user = request.user
    vacunador = Vacunador.objects.get(usuario_id=user.dni)
    sobrante = VacunaVacunatorio.objects.get(vacunatorio_id=vacunador.vacunatorio_de_trabajo_id, vacuna_id__tipo__exact="Fiebre_amarilla")

    if (sobrante.stock_remanente == 0):
        
        context["mensaje"] = 'No hay sobrante de vacunas de Fiebre amarilla en este momento.'
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)

    dni = request.POST.get("Dni")

    fecha_nacimiento = request.POST.get("Fecha_nacimiento")
    fecha_nacimiento = datetime.strptime(fecha_nacimiento,"%Y-%m-%d").date()
    anios = calculate_age(fecha_nacimiento)
    print(anios)
    if (anios > 60):
            
            context["mensaje"] = "La persona es mayor de 60 años, no puede aplicarse la vacuna"
            request.session["context"] = context
            return redirect(ver_turnos_del_dia)


    vacunaaplicada = VacunaAplicada.objects.filter(usuario_id__dni__exact=dni).filter(vacuna_id__tipo__exact="Fiebre_amarilla").order_by('-fecha').first()
    hoy = datetime.today()

    if (vacunaaplicada):
        
        context["mensaje"] = "Esta persona ya tiene aplicada la vacuna contra fiebre amarilla, no se la puede volver a aplicar"
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)
    
    context["dni_a_cargar"] = dni
    context["email_a_cargar"] = request.POST.get("Email")
    context["tipo_a_cargar"] = "Fiebre_amarilla"
    request.session["context"] = context
    return redirect(ver_turnos_del_dia)

@login_required
def cargar_vacuna_fiebre_amarilla_sin_turno(request):

    context={"mensaje":""}
    #asignar el sobrante cuando este echo en la base de datos

    user = request.user
    dni = request.POST.get("Dni")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")
    

    vacuna = Vacuna.objects.filter(tipo='Fiebre_amarilla').first()

    inscripcion = Inscripcion.objects.filter(usuario_id=dni,vacuna=vacuna).first()

    hoy = datetime.today()

    hoy = date(hoy.year, hoy.month, hoy.day)

    #en teoria deberia ser distinto el cargar la vacuna aplicada si esta registrado o no, pero si esto es legal, deberia funcionar para ambos
    vacuna_aplicada = VacunaAplicada(fecha=hoy, marca=marca, lote=lote, con_nosotros=True, usuario_id=dni,vacuna=vacuna, vacunatorio=user.vacunatorio_trabajo)
    vacuna_aplicada.save()

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=request.user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    if (vacuna_vacunatorio): #PROVISORIAMENTE: DEBERIAN ESTAR SI O SI TODAS LAS VACUNA_VACUNATORIO
        vacuna_vacunatorio.stock_remanente = vacuna_vacunatorio.stock_remanente - 1
        vacuna_vacunatorio.save()

    if (inscripcion):
        inscripcion.delete()
    
    usuario = Usuario.objects.filter(dni=dni).first()
    if (usuario):
        pass 
        html_message = loader.render_to_string('email_aviso_certificado2.html',{'fecha': hoy})
        try:    
            send_mail('Certificado de vacunacion de fiebre amarilla',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
        except:
            pass
    else: 
        email =request.POST.get("Email")
        html_message = loader.render_to_string('email_aviso_vacunacion.html',{'fecha': hoy, "vacuna": "Fiebre amarilla"})
        try:    
            send_mail('Vacunacion contra la fiebre amarilla',"",EMAIL_HOST_USER,[email], html_message=html_message)
        except:
            pass
        
    context["mensaje"] = "La vacuna se cargo de forma exitosa."
    request.session["context"] = context
    return redirect(ver_turnos_del_dia)

@login_required
def baja_campania(request):
    user = request.user
    tipo = request.POST.get("tipo")
    
    context = dict.fromkeys(["mensaje"], "")

    inscripcion = Inscripcion.objects.filter(usuario_id=user.dni,vacuna_id__tipo= tipo).first()

    hoy = datetime.today()
    if ((inscripcion.fecha != None)):
        vacuna_no_aplicada = VacunasNoAplicadas(usuario=user, vacuna=inscripcion.vacuna, vacunatorio=inscripcion.vacunatorio,fecha=inscripcion.fecha, estado="Cancelado")
        vacuna_no_aplicada.save()
        if (inscripcion.fecha < (date(hoy.year, hoy.month, hoy.day) + relativedelta(days=7))):
            vacuna_vacunatorio = VacunaVacunatorio.objects.get(vacunatorio_id=inscripcion.vacunatorio, vacuna_id__tipo__exact= tipo)
            vacuna_vacunatorio.stock_remanente = vacuna_vacunatorio.stock_remanente + 1
            vacuna_vacunatorio.save()

    inscripcion.delete()
    request.session["mensaje"] = f'Ha sido dado de baja exitosamente de la campaña {tipo}'
    return redirect(home)

@login_required
def baja_vacunador(request):
    dni = request.POST.get("Dni")

    context = dict.fromkeys(["mensaje", "rol"], "")
    context["rol"] = "Vacunador"
    usuario=Usuario.objects.get(dni=dni)
    usuario.es_vacunador=False

    vacunador = Vacunador.objects.get(usuario_id=dni)

    vacunador.delete()
    context["mensaje"] = 'El vacunador ha sido dado de baja exitosamente'
    request.session["context"] = context
    return redirect(gestionar_usuarios_admin)


@login_required
def baja_administrador(request):
    dni = request.POST.get("Dni")

    context = dict.fromkeys(["mensaje","rol"], "")

    usuario=Usuario.objects.get(dni=dni)
    usuario.es_administrador=False

    context["mensaje"] = 'El administrador ha sido dado de baja exitosamente'
    request.session["context"] = context
    return redirect(gestionar_usuarios_admin)

@login_required()
def recuperar_contrasenia(request):
    dni = request.POST.get("Dni")
    numero_tramite = request.POST.get("Tramite")
    context = dict.fromkeys(["mensaje"], "")

    usuario=Usuario.objects.filter(dni=dni).first()

    if (usuario):

        persona = {"dni":dni,
                "tramite": numero_tramite,
                "sexo": usuario.sexo}
        headers = {
            'X-Api-Key': 'JhKDui9uWt63sxGsdE1Xw1pGisfKpjZK1WJ7EMmy',
            'Content-Type' : "application/json"
            }
        try:
            response = requests.post("https://hhvur3txna.execute-api.sa-east-1.amazonaws.com/dev/person/validate", 
            headers=headers, json=persona)
        except:
            context["mensaje"] = "Hubo un fallo de la conexión con el RENAPER, vuelva a intentarlo más tarde."
        else:
            if (response.status_code == 403):
                context["mensaje"] = "Hubo un fallo de la conexión con el RENAPER, vuelva a intentarlo más tarde."
            if (response.status_code != 200):
                context["mensaje"] = "Error de validación. Verifique que sus datos sean correctos e intente de nuevo."
            else:
                context["mensaje"] = f'Se ha enviado un mail a la dirección de correo electrónico {usuario.email} con la nueva clave'
                contrasenia = ''.join(random.choices(string.ascii_letters, k=6), random.choices(string.digits, k=2))
                usuario.set_password(self, contrasenia)
                usuario.save()
                #envia el mail
                html_message = loader.render_to_string('email_turno.html',{'fecha': fecha_turno, "user": request.user, "vacuna": "COVID-19"}) #REVISAR FLACA NO TE OLVIDES UwU aribel
                #try:    
                #    send_mail('Nueva contraseña VacunAssist',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
                #except:
                #    pass
    else:
        context["mensaje"] = 'El DNI ingresado no está cargado en el sistema'

    request.session["context"] = context
    return redirect(gestionar_usuarios_admin)

@login_required()
def posponer_turno_fallido(request):
    context = dict.fromkeys(["mensaje"], "")
    context["mensaje"] = 'usted cumplirá 60 años en este lapso de tiempo, si presiona aceptar, se le cancelara el turno'
    request.session["context"] = context
    return redirect('MOSTRAR MODAL')

@login_required()
def posponer_turno(request):
    dni = request.POST.get("Dni")
    dias = int(request.POST.get("Dias"))
    tipo = request.POST.get("Tipo")
    confirmacion = request.POST.get("Confirmacion")
    context = dict.fromkeys(["mensaje","Confi"], "")

    #esto seria para hacer la confirmacion de la baja pero no estoy del todo seguro.
    #if confirmacion != "":

    usuario=Usuario.objects.filter(dni=dni).first()
    anios = calculate_age(usuario.fecha_nacimiento + relativedelta(days=dias))
    inscripcion = Inscripcion.objects.filter(usuario_id=dni,vacuna_id__tipo= tipo).first()
    vacuna_tipo = inscripcion.vacuna
    vacunatorio = inscripcion.vacunatorio
    fecha_inscripcion = inscripcion.fecha
    vacuna_vacunatorio = VacunaVacunatorio.objects.get(vacunatorio_id=inscripcion.vacunatorio, vacuna_id__tipo__exact= tipo)
    if anios > 60:
        context["mensaje"] = 'usted cumplirá 60 años en este lapso de tiempo, si presiona aceptar, se le cancelara el turno'
        context["Confi"] = "si"
        request.session["context"] = context
        redirect (mostrar_mis_turnos)
    elif (anios < 60):
        estado = "Pospuesto"
        inscripcion.fecha = inscripcion.fecha + relativedelta(days=dias)
        inscripcion.save()
        context["mensaje"] = f'Su turno para la vacuna del {tipo} se pospuso correctamente para el día {inscripcion.fecha}'
    else:
        estado = "Cancelado"
        inscripcion.delete()
        context["mensaje"] = 'Su turno no se pospuso ya que no cumple con el limite de edad, usted fue desuscripto de la campaña'
    vacuna_no_aplicada = VacunasNoAplicadas(usuario=usuario, vacuna=vacuna_tipo, vacunatorio=vacunatorio,fecha=fecha_inscripcion, estado=estado)
    vacuna_no_aplicada.save()
    vacuna_vacunatorio.stock_remanente = vacuna_vacunatorio.stock_remanente + 1
    vacuna_vacunatorio.save()

    request.session["context"] = context
    return redirect(mostrar_mis_turnos)

@login_required()
def cambiar_vacunatorio_trabajo(request):
    dni = request.POST.get("Dni")
    nombre_vacunatorio = request.POST.get("Vacunatorio")
    context = dict.fromkeys(["mensaje","rol"], "")
    context["rol"] = "Vacunador"
    vacunatorio = Vacunatorio.objects.get(nombre=nombre_vacunatorio)
    
    vacunador = Vacunador.objects.get(usuario_id=dni)
    vacunador.vacunatorio_de_trabajo = vacunatorio
    vacunador.save()

    context["mensaje"] = 'La modificación ha sido realizada con éxito'
    request.session["context"] = context
    return redirect(gestionar_usuarios_admin)

@login_required()
def modificar_vacunatorio_preferencia(request):
    dni = request.POST.get("Dni")
    nombre_vacunatorio = request.POST.get("Vacunatorio")
    context = dict.fromkeys(["mensaje"], "")
    vacunatorio = Vacunatorio.objects.get(nombre=nombre_vacunatorio)

    usuario = Usuario.objects.get(usuario_id=dni)
    usuario.vacunatorio_pref = vacunatorio
    usuario.save()

    context["mensaje"] = 'Su nuevo vacunatorio de preferencia que es: {nombre_vacunatorio}, esto no modifica los turnos que ya tenga asignados'
    request.session["context"] = context
    return redirect('LA MISMA PAGINA ANASHEI')

@login_required()
def modificar_cuestionario_salud(request):
    dni = request.POST.get("Dni")
    cuestionario = request.POST.get("Cuestionario")
    context = dict.fromkeys(["mensaje"], "")

    usuario = Usuario.objects.get(usuario_id=dni)
    usuario.de_riesgo = cuestionario
    usuario.save()

    context["mensaje"] = 'Su cuestionario de salud se modifico correctamente'
    request.session["context"] = context
    return redirect('LA MISMA PAGINA ANASHEI')

@login_required()
def modificar_datos_personales(request):
    mail = request.POST.get("mail")
    dni = request.POST.get("Dni")
    context = dict.fromkeys(["mensaje"], "")

    usuario = Usuario.objects.get(usuario_id=dni)
    usuario.email = mail
    usuario.save()

    context["mensaje"] = 'Su mail se modifico correctamente'
    request.session["context"] = context
    return redirect('LA MISMA PAGINA ANASHEI')
    

@login_required
def cambiar_rol(request):
    user = request.user
    rol = request.POST.get("rol")
    user.rol_actual = rol
    user.save()
    if rol == "Ciudadano":
        return redirect(home)
    elif rol == "Vacunador":
        return redirect(ver_turnos_del_dia)
    else:
        return redirect(visualizar_stock_administrador)
    

@login_required()
def modificar_contrasenia(request):
    context = dict.fromkeys(["mensaje"], "")
    dni = request.POST.get("Dni")
    password = request.POST.get("password")
    password2 = request.POST.get("password2")


    if ((not bool(re.search(r'\d', password))) or (not bool(re.search('[a-zA-Z]', password)))):
        context["mensaje"] = "La nueva contraseña debe tener al menos 8 caracteres, 1 letra y 1 número."
    elif password and password2 and password != password2:  
        context["mensaje"] ="La nueva contraseña y la confirmación deben ser iguales."
    elif (usuario.check_password(password)):
        context["mensaje"] ='La nueva contraseña debe ser distinta a la contraseña actual'
    else:
        usuario = Usuario.objects.get(usuario_id=dni)
        usuario.set_password(password)
        usuario.save()
        context["mensaje"] = 'La contraseña ha sido modificada exitosamente'

    request.session["context"] = context
    return redirect('LA MISMA PAGINA ANASHEI')


@login_required()
def asignar_turno_manual_covid(request):        
    context = dict.fromkeys(["mensaje"], "")
    nombre_vacunatorio = request.POST.get("Vacunatorio")
    cantidad = request.POST.get("Cantidad")

    vacunatorio = Vacunatorio.objects.get(nombre=nombre_vacunatorio)

    inscripcion = Inscripcion.objects.all(vacuna_id__tipo= 'COVID-19', fecha = None, vacunatorio_id__nombre= nombre_vacunatorio)
    
    if( len(inscripcion) >= cantidad):
        hoy = datetime.today()
        indice = 0
        while (indice < cantidad):
            inscripcion[indice].fecha = hoy + relativedelta(days=15)
            inscripcion[indice].save()
            indice = indice + 1
        context["mensaje"] = 'Se han asignado los turnos correctamente'
    else:
        context["mensaje"] = f'La cantidad ingresada supera a los {len(inscripcion)} usuarios pendiente a vacunarse'
        
    request.session["context"] = context
    return redirect('LA MISMA PAGINA ANASHEI')

@login_required()
def asignar_turno_manual_fiebre_amarilla(request):        
    context = dict.fromkeys(["mensaje"], "")
    nombre_vacunatorio = request.POST.get("Vacunatorio")
    cantidad = request.POST.get("Cantidad")

    eliminar = Inscripcion.objects.all(vacuna_id__tipo= 'Fiebre_amarilla', fecha = None, vacunatorio_id__nombre= nombre_vacunatorio).filter(60 < calculate_age(usuario.fecha_nacimiento + relativedelta(days=15)))  
   
    for elim in eliminar:
        elim.delete()

    inscripcion = Inscripcion.objects.all(vacuna_id__tipo= 'Fiebre_amarilla', fecha = None, vacunatorio_id__nombre= nombre_vacunatorio)
    
    if( len(inscripcion) >= cantidad):
        indice = 0
        hoy = datetime.today()
        while (indice < cantidad):
            inscripcion[indice].fecha = hoy + relativedelta(days=15)
            inscripcion[indice].save()
            indice = indice + 1
        context["mensaje"] = 'Se han asignado los turnos correctamente'
    else:
        context["mensaje"] = f'La cantidad ingresada supera a los {len(inscripcion)} usuarios pendiente a vacunarse'
        
    request.session["context"] = context
    return redirect('LA MISMA PAGINA ANASHEI')

@login_required
def visualizar_cantidad_turnos(request):


    context = dict.fromkeys(["turnos","mensaje"], "")

    fecha_inicio = request.POST.get("fecha_inicio")
    fecha_fin = request.POST.get("fecha_fin")
    if (fecha_inicio < fecha_fin):
        context["turnos"]= Inscripcion.objects.filter(fecha__range=[fecha_inicio,fecha_fin])
    else:
        context["mensaje"]= 'Las fechas ingresadas no son válidas'

    #ver si contemplar esto
    request.session["context"] = context
    #cambiar return
    return redirect('LA MISMA PAGINA ANASHEI')
    #return render(request, 'vacunas_adm.html', context)

@login_required
def ver_cantidad_turnos(request):

    context = request.session.get('context',{})
    request.session["context"] = {}
    hoy = datetime.today()
    
    if (context == {}):
        context = dict.fromkeys(["turnos","mensaje"], "")
        context["turnos"]= Inscripcion.objects.filter(fecha__range=[(hoy + relativedelta(days=-7)),hoy])
    elif (context['mensaje'] == 'Las fechas ingresadas no son válidas'):
        context["turnos"]= Inscripcion.objects.filter(fecha__range=[(hoy + relativedelta(days=-7)),hoy])
    
    ##fraaaaaaan correegi esto ananananashey
    return render(request, 'index.html', context)
