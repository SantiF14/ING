
from django.template import loader
from django.shortcuts import render, redirect
from gestion_de_usuarios.models import VacunaAplicada
from datetime import datetime, date
from dateutil.relativedelta import *
from gestion_de_usuarios.models import *
from VacunAsist.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from gestion_de_usuarios.views import ver_turnos_del_dia

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def index(request):
    if request.user.is_authenticated:
        return redirect(home)
    return render(request, 'index.html', {})

def home(request, mensaje=None, titulo=None):

    if request.user.is_authenticated:
        context = dict.fromkeys(["user","covid","fiebre_amarilla","gripe","mensaje","titulo","vacuna_fa"], "No")
        user = request.user
        context["user"] = user
        context["mensaje"] = mensaje
        context["titulo"] = titulo

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

    

        return render(request,"home.html",context)

    return render(request, 'index.html', {})    

@login_required
def mostrar_mis_turnos(request):

    usuario = request.user
    context=dict.fromkeys(["turnos","mensaje"],"")
    turnos = Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])
    context["turnos"]=turnos

    if not turnos:
        context["mensaje"]="Usted no tiene turnos asignados."
        
    return render(request, "mostrar_mis_turnos.html",context)

@login_required
def mostrar_vacunas_aplicadas(request):


    usuario = request.user
    context=dict.fromkeys(["vacunas","mensaje"],"")
    vacunas = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni)
    context["vacunas"]=vacunas     
    if not vacunas:
        context["mensaje"]="Usted no tiene vacunas cargadas en el sistema"
        
    return render(request, "mostrar_historial_vacuna_aplicada.html",context)

@login_required
def inscribir_campania_gripe (request):

 
    usuario = request.user

    inscripcion = Inscripcion.objects.filter(usuario_id__dni__exact=usuario.dni).filter(vacuna_id__tipo__exact="Gripe").filter(fecha__range=[datetime(1900, 3, 13), datetime(2200, 3, 13)])

    #si ya esta inscripcion
    if (inscripcion):
        return home(request,"Ya estas inscripcion")


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
    return home(request,f"Usted se inscribió a la campaña de vacunación de la gripe. Le hemos enviado un mail a la dirección {usuario.email} con la fecha de su turno. Por favor, revise su correo no deseado.","Inscripción exitosa")

@login_required
def inscribir_campania_COVID (request):
    
    usuario = request.user

    hoy = datetime.today()
    antes = hoy + relativedelta(months=-3)

    #calculo la edad del usuario
    anios = calculate_age(usuario.fecha_nacimiento)

    if (anios < 18):
        return home(request, "Debe ser mayor de edad para poder inscribirse.","Inscripción fallida")


    inscripcion = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="COVID-19").first()

    #si ya esta inscripcion
    if (inscripcion):
        return home(request)

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
        return home(request,f"Usted se inscribió a la campaña de vacunación del COVID-19. Le hemos enviado un mail a la dirección {usuario.email} con la fecha de su turno. Por favor, revise su correo no deseado.","Inscripción exitosa")
    return home(request,"Usted se inscribió a la campaña de vacunación del COVID-19.","Inscripción exitosa")

@login_required
def inscribir_campania_fiebre_amarilla(request):
    
    usuario = request.user

    hoy = datetime.today()
    
    #calculo la edad del usuario
    anios = calculate_age(usuario.fecha_nacimiento)

    if (anios > 60):
        return home(request,"Usted supera el límite de edad para inscribirse a esta campaña.","Inscripción fallida")


    inscripcion = Inscripcion.objects.filter(usuario_id=usuario.dni).filter(vacuna_id__tipo__exact="Fiebre_amarilla").first()
    vacuna = VacunaAplicada.objects.filter(usuario_id__dni__exact=usuario.dni, vacuna = Vacuna.objects.filter(tipo = "Fiebre_amarilla").first())

    #Provisoriamente vamos a poner el if gigante anashey evaluar si ya tiene turno, que en teoria no es necesario
    if (inscripcion) or (vacuna):
        return home(request,"Usted se encuentra inscripcion o ya tiene una vacuna aplicada","Inscripción fallida")
    
    fecha_turno = None

    vacuna= Vacuna.objects.filter(tipo="Fiebre_amarilla").get()

    ins = Inscripcion(usuario=usuario,fecha=fecha_turno,vacunatorio=usuario.vacunatorio_pref,vacuna=vacuna)
    ins.save()

    return home(request,"Usted se inscribió a la campaña de vacunación de la fiebre amarilla","Inscripción exitosa") 

@login_required
def cargar_vacuna_con_turno(request):

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

    vacuna = VacunaAplicada(usuario=usuario,vacuna=vacu,fecha=hoy,marca=marca,lote=lote,con_nosotros=True)
    vacuna.save()



    return ver_turnos_del_dia(request, "La vacuna se cargó de forma exitosa.")

@login_required
def cargar_vacuna_stock(request):
    cant = int(request.POST.get("Cantidad"))
    tipo = request.POST.get("Tipo")

    if (cant < 0):
        #fijarse donde lo va a retornar
        return nose(request, 'No se puede ingresar una cantidad negativa. Ingrese un valor positivo.')

    user = request.user

    vacuna = Vacuna.objects.get(tipo=tipo)

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()

    if (vacuna_vacunatorio):
        vacuna_vacunatorio.stock_actual = vacuna_vacunatorio.stock_actual + cant
    else:
        vacuna_vacunatorio = VacunaVacunatorio(vacunatorio=user.vacunador.vacunatorio_de_trabajo,vacuna=vacuna,stock_actual=cant)

    vacuna_vacunatorio.save()

    #fijarse donde lo va a retornar
    return nose(request, 'Las vacunas se cargaron de forma exitosa en el sistema.')

@login_required
def eliminar_vacuna_stock(request):
    cant = request.POST.get("Cantidad")
    tipo = request.POST.get("Tipo")

    if (cant < 0):
        #fijarse donde lo va a retornar
        return visualizar_stock_vacunador(request, 'Debe ingresarse un numero positivo de vacunas a eliminar.')

    user = request.user

    vacuna = Vacuna.objects.get(tipo=tipo)

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    # REVISAR : Sacar el primer if-else, nunca entraria al else por como lo pensamos.
    if (vacuna_vacunatorio):
        if (vacuna_vacunatorio.stock_actual < cant):
            mensaje = f'No pueden eliminarse más vacunas de las que hay en stock({vacuna_vacunatorio.stock_actual}).'
        else:
            vacuna_vacunatorio.stock_actual = vacuna_vacunatorio.stock_actual - cant
            vacuna_vacunatorio.save()
            mensaje = f'Las vacunas se eliminaron correctamente, cantidad actual de vacunas de la gripe en el vacunatorio {vacuna_vacunatorio.vacunatorio.nombre} es de: {vacuna_vacunatorio.stock_actual}.'
    else:
        #checkear esto
        vacuna_vacunatorio = VacunaVacunatorio(vacunatorio=user.vacunador.vacunatorio_de_trabajo,vacuna=vacuna,stock_actual=0)
        vacuna_vacunatorio.save()
        mensaje = f'No pueden eliminarse más vacunas de las que hay en stock({vacuna_vacunatorio.stock_actual}).'


    #fijarse donde lo va a retornar
    return visualizar_stock_vacunador(request, mensaje)

@login_required
def agregar_vacuna_gripe_historial(request):
    marca = request.POST.get("Marca")
    tipo = request.POST.get("Tipo")
    fecha = request.POST.get("Fecha")
    user = request.user
    hoy = datetime.today()

    vacuna = Vacuna.objects.get(tipo=tipo)

    inscripcion = Inscripcion.objects.filter(usuario=user,vacuna=vacuna).first()
    fecha_turno = None
    if not inscripcion:
        if (inscripcion.fecha < (fecha + relativedelta(years=1))):
            if ((fecha + relativedelta(years=1)) < (hoy.date() + relativedelta(days=7))):
                fecha_turno = hoy + relativedelta(days=7)
            else:
                fecha_turno = fecha + relativedelta(years=1)
            fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
            inscripcion.fecha = fecha_turno
            inscripcion.save()

    fecha = date(fecha.year, fecha.month, fecha.day)

    vacunaaplicada = VacunaAplicada(usuario=user,fecha=fecha,vacuna=vacuna,marca=marca,con_nosotros=False)
    vacunaaplicada.save()

    return mostrar_vacunas_aplicadas(request, 'La vacuna ha sido cargada exitosamente.')

@login_required
def agregar_vacuna_COVID_historial(request):
    marca = request.POST.get("Marca")
    tipo = request.POST.get("Tipo")
    fecha = request.POST.get("Fecha")
    user = request.user
    hoy = datetime.today()

    vacuna = Vacuna.objects.get(tipo=tipo)

    inscripcion = Inscripcion.objects.filter(usuario=user,vacuna=vacuna).first()
    fecha_turno = None

    #ver si no existe la inscripcion tira error, en caso de que si, cambiar a esto y probar if (inscripcion) and (inscripcion.fecha < (fecha + relativedelta(years=3))):
    #si eso no funciona llamar al 0800-222-lucho para mas informacion
    if not inscripcion:
        if (inscripcion.fecha < (fecha + relativedelta(months=3))):
            if ((fecha + relativedelta(months=3)) < (hoy.date() + relativedelta(days=7))):
                fecha_turno = hoy + relativedelta(days=7)
            else:
                fecha_turno = fecha + relativedelta(months=3)
            fecha_turno = date(fecha_turno.year, fecha_turno.month, fecha_turno.day)
            inscripcion.fecha = fecha_turno
            inscripcion.save()


    fecha = date(fecha.year, fecha.month, fecha.day)

    vacunaaplicada = VacunaAplicada(usuario=user,fecha=fecha,vacuna=vacuna,marca=marca,con_nosotros=False)
    vacunaaplicada.save()

    #cambiar return
    return mostrar_vacunas_aplicadas(request, 'La vacuna ha sido cargada exitosamente.')

@login_required
def agregar_vacuna_fiebre_amarilla_historial(request):
    marca = request.POST.get("Marca")
    tipo = request.POST.get("Tipo")
    fecha = request.POST.get("Fecha")
    user = request.user

    vacuna = Vacuna.objects.get(tipo=tipo)

    inscripcion = Inscripcion.objects.filter(usuario=user,vacuna=vacuna).first

    if (inscripcion):
        inscripcion.delete()

    fecha = date(fecha.year, fecha.month, fecha.day)

    vacunaaplicada = VacunaAplicada(usuario=user,fecha=fecha,vacuna=vacuna,marca=marca,con_nosotros=False)
    vacunaaplicada.save()


    #cambiar return y acordarse de actualizar boton
    return mostrar_vacunas_aplicadas(request, 'La vacuna ha sido cargada exitosamente.')

@login_required
def visualizar_stock_vacunador(request, mensaje):
    
    user = request.user

    context = dict.fromkeys(["vacunas","mensaje"],"")

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=user.vacunador.vacunatorio_de_trabajo)

    context["vacunas"] = vacuna_vacunatorio
    context["mensaje"] = mensaje

    #ver si contemplar esto
    #if (not vacuna_vacunatorio):
    #    vacuna_vacunatorio = VacunaVacunatorio(vacunatorio=user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna,stock_actual=0)
    #    vacuna_vacunatorio.save()

    return render(request, mensaje)

#REVISAR
@login_required
def visualizar_stock_administrador(request):
    vacunatorio = request.POST.get("Vacunatorio")
    tipo = request.POST.get("Tipo")
    user = request.user
 
    vacuna = Vacuna.objects.filter(tipo=tipo).first()


    if (vacuna):
        vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=vacunatorio, vacuna=vacuna).first()
        #cambiar return
        return nose(request, f'Hay {vacuna_vacunatorio.stock_actual} vacunas en stock de tipo {tipo} en el vacunatorio {nomvacunatorio}.')

    #ver si esto funciona como deberia o si hay que poner .get() o como carajo es
    listavacunatorios = VacunaVacunatorio.objects.all()
    stocktotal = 0
    for vacunatorio in listavacunatorios:
        stocktotal = stocktotal + vacunatorio.stock_actual

    #cambiar return
    return nose(request, f'Hay {stocktotal} vacunas en stock de tipo {tipo} en {vacunatorio} los vacunatorios.')

@login_required
def boton_gripe(request):
    
    #asignar el sobrante cuando este echo en la base de datos
    sobrante = 10

    if (sobrante == 0):
        #cambiar return
        return nose(request, 'No hay sobrante de vacunas en este momento.')

    dni = request.POST.get("DNI")
    vacunaaplicada = VacunaAplicada.objects.filter(usuario_id__dni__exact=dni).filter(vacuna_id__tipo__exact="Gripe").order_by('-fecha').first()
    hoy = datetime.today()

    if (vacunaaplicada) and ((hoy + relativedelta(years=-1)) < vacunaaplicada.fecha):
        #cambiar return
        return nose(request, 'Esta persona tiene una vacuna aplicada en el ultimo año, no puede aplicarse la vacuna')
    
    #cambiar return en este caso todo esta ok xD
    return nose(request, 'ok')

@login_required
def Cargar_vacuna_gripe_sin_turno(request):

    #asignar el sobrante cuando este echo en la base de datos
    sobrante = 10


    dni = request.POST.get("DNI")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")
    usuario = Usuario.objects.filter(dni=dni).first()
    vacuna = Vacuna.objects.filter(tipo='Gripe').first()

    inscripcion = Inscripcion.objects.filter(usuario=usuario,vacuna=vacuna).first()

    hoy = datetime.today()

    hoy = date(hoy.year, hoy.month, hoy.day)

    vacuna_aplicada = VacunaAplicada(fecha=hoy, marca=marca, lote=lote, con_nosotros=True, usuario_id=dni,vacuna=vacuna)
    vacuna_aplicada.save()

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=request.user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    vacuna_vacunatorio.stock_actual = vacuna_vacunatorio.stock_actual - 1
    vacuna_vacunatorio.save()

    if (inscripcion):
        inscripcion.fecha = hoy + relativedelta(years=1)
        inscripcion.save()
        #html_message = loader.render_to_string('email_turno.html',{'fecha': hoy + relativedelta(years=1), "vacuna": "gripe"})
        #send_mail('Notificación de turno para vacuna contra la gripe',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
    
    if (not usuario):
        email =request.POST.get("Email")
        #html_message = loader.render_to_string('email_aviso_vacunacion.html',{'fecha': hoy, "vacuna": "gripe"})
        #send_mail('Vacunacion contra la gripe',"",EMAIL_HOST_USER,[email], html_message=html_message)
        

    return nose(request, 'La vacuna se cargo de forma exitosa.')

@login_required
def boton_COVID(request):
    
    #asignar el sobrante cuando este echo en la base de datos
    sobrante = 9

    if (sobrante == 0 ):
        #cambiar return
        return nose(request, 'No hay sobrante de vacunas en este momento.')

    dni = request.POST.get("DNI")
    fecha_nacimiento = request.POST.get("Fecha_nacimiento")
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
            return nose(request, "La persona es menor de 18 años no puede aplicarse la vacuna")

    #-------------------------IMPORTANTE-----------------------------#
    #falta chequear lo de los 18n anios para el que no esta registrado, nose como vamos a obtener la fecha de nacimiento
    #-----------------------------------------------------------------#


    vacuna_aplicada = VacunaAplicada.objects.filter(usuario_id__dni__exact=dni).filter(vacuna_id__tipo__exact="COVID-19").order_by('-fecha').first()
    hoy = datetime.today()

    if (vacuna_aplicada) and ((hoy + relativedelta(months=-3)) < vacuna_aplicada.fecha): #chequear que este mayor este bien puesto y no sea menor
        #cambiar return
        return nose(request, 'Esta persona tiene una vacuna aplicada en los ultimos tres meses, no puede aplicarse la vacuna')
    
    #cambiar return en este caso todo esta ok xD
    return nose(request, 'ok')

@login_required
def Cargar_vacuna_COVID_sin_turno(request):

    #asignar el sobrante cuando este echo en la base de datos
    sobrante = 9


    dni = request.POST.get("DNI")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")
    usuario = Usuario.objects.filter(dni=dni).first()

    vacuna = Vacuna.objects.filter(tipo='COVID-19').first()
    inscripcion = Inscripcion.objects.filter(usuario_id=usuario,vacuna=vacuna).first()

    hoy = datetime.today()
    hoy = date(hoy.year, hoy.month, hoy.day)

    #en teoria deberia ser distinto el cargar la vacuna aplicada si esta registrado o no, pero si esto es legal, deberia funcionar para ambos
    vacuna_aplicada = VacunaAplicada(fecha=hoy, marca=marca, lote=lote, con_nosotros=True, usuario_id=dni,vacuna=vacuna)
    vacuna_aplicada.save()

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=request.user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    vacuna_vacunatorio.stock_actual = vacuna_vacunatorio.stock_actual - 1
    vacuna_vacunatorio.save()

    if (inscripcion):
        inscripcion.fecha = hoy + relativedelta(months=3)
        inscripcion.save()
        #html_message = loader.render_to_string('email_turno.html',{'fecha': hoy + relativedelta(months=3), "vacuna": "COVID-19"})
        #send_mail('Notificación de turno para vacuna contra el COVID-19',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
    
    
    if (not usuario):
        email =request.POST.get("Email")
        #html_message = loader.render_to_string('email_aviso_vacunacion.html',{'fecha': hoy, "vacuna": "COVID-19"})
        #send_mail('Vacunacion contra el COVID-19',"",EMAIL_HOST_USER,[email], html_message=html_message)
        
    return nose(request, 'La vacuna se cargo de forma exitosa.')
    
@login_required
def boton_fiebre_amarilla(request):
    
    #asignar el sobrante cuando este echo en la base de datos
    sobrante = 9

    if (sobrante == 0):
        #cambiar return
        return nose(request, 'No hay sobrante de vacunas en este momento.')

    dni = request.POST.get("DNI")

    fecha_nacimiento = request.POST.get("Fecha_nacimiento")
    anios = calculate_age(fecha_nacimiento)
    if (anios < 18):
            #cambiar return
            return nose(request, "El usuario es mayor de 60 años, no puede aplicarse la vacuna")

    #-------------------------IMPORTANTE-----------------------------#
    #falta chequear lo de los 60 anios para el que no esta registrado, nose como vamos a obtener la fecha de nacimiento
    #-----------------------------------------------------------------#


    vacunaaplicada = VacunaAplicada.objects.filter(usuario_id__dni__exact=dni).filter(vacuna_id__tipo__exact="Fiebre_amarilla").order_by('-fecha').first()
    hoy = datetime.today()

    if (vacunaaplicada):
        #cambiar return
        return nose(request, 'Esta persona ya tiene aplicada la vacuna contra fiebre amarilla, no se la puede volver a aplicar')
    
    #cambiar return en este caso todo esta ok xD
    return nose(request, 'ok')

@login_required
def Cargar_vacuna_fiebre_amarilla_sin_turno(request):

    #asignar el sobrante cuando este echo en la base de datos
    sobrante = 9


    dni = request.POST.get("DNI")
    marca = request.POST.get("Marca")
    lote = request.POST.get("Lote")
    

    vacuna = Vacuna.objects.filter(tipo='Fiebre_amarilla').first()

    inscripcion = Inscripcion.objects.filter(usuario_id=dni,vacuna=vacuna).first

    hoy = datetime.today()

    hoy = date(hoy.year, hoy.month, hoy.day)

    #en teoria deberia ser distinto el cargar la vacuna aplicada si esta registrado o no, pero si esto es legal, deberia funcionar para ambos
    vacuna_aplicada = VacunaAplicada(fecha=hoy, marca=marca, lote=lote, con_nosotros=True, usuario_id=dni,vacuna=vacuna)
    vacuna_aplicada.save()

    vacuna_vacunatorio = VacunaVacunatorio.objects.filter(vacunatorio=request.user.vacunador.vacunatorio_de_trabajo, vacuna=vacuna).first()
    vacuna_vacunatorio.stock_actual = vacuna_vacunatorio.stock_actual - 1
    vacuna_vacunatorio.save()

    if (inscripcion):
        inscripcion.delete()
    
    usuario = Usuario.objects.filter(dni=dni).first()
    if (usuario):
        pass
        #html_message = loader.render_to_string('email_aviso_certificado.html',{'fecha': hoy})
        #send_mail('Certificado de vacunacion de fiebre amarilla',"",EMAIL_HOST_USER,[usuario.email], html_message=html_message)
    else: 
        email =request.POST.get("Email")
        #html_message = loader.render_to_string('email_aviso_vacunacion.html',{'fecha': hoy, "vacuna": "Fiebre amarilla"})
        #send_mail('Vacunacion contra la fiebre amarilla',"",EMAIL_HOST_USER,[email], html_message=html_message)
        
    return nose(request, 'La vacuna se cargo de forma exitosa.')