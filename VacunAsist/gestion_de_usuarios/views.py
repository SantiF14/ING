from datetime import date
from django.http import HttpResponse
from django.shortcuts import render, redirect, HttpResponse
from django.template import loader
from gestion_de_usuarios.models import Inscripcion, VacunaAplicada, Vacuna
from gestion_de_usuarios.forms import FormularioDeRegistro, FormularioDeAutenticacion
from django.contrib.auth import login, authenticate, logout
from gestion_de_usuarios.models import Usuario
import random, string
from django.core.mail import send_mail
from VacunAsist.settings import EMAIL_HOST_USER
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import pdfkit
import mimetypes
import os
from pathlib import Path
import requests
import json
from datetime import date, datetime

User = get_user_model()



def get_redirect_if_exists(request):
    redirect = None
    if request.GET:
        if request.GET.get("next"):
            redirect = str(request.GET.get("next"))
    return redirect

def registrar(request):

    user = request.user
    if user.is_authenticated:
        return redirect("Home")

    context = {}
    if request.POST:
        form = FormularioDeRegistro(request.POST)
        if form.is_valid():
            clave_alfanum = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
            form.save(clave_alfanum)
            dni = form.cleaned_data["dni"]
            password = form.cleaned_data["password1"]
            mail = request.POST.get('email')
            html_message = loader.render_to_string('email_clave.html',{'clave': clave_alfanum})
            try:
                send_mail('Clave alfanumerica Vacunassist',"",EMAIL_HOST_USER,[mail], html_message=html_message)
            except:
                pass
            user = authenticate(dni=dni, password=password)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            destination = get_redirect_if_exists(request)
            if destination: 
                return redirect(destination)
            return redirect("Home")
        else:
            context['registration_form'] = form

    else:
        form = FormularioDeRegistro()
        context['registration_form'] = form
    return render(request, 'registro.html', context)

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect("Index")

@login_required
def ver_turnos_del_dia(request):
    user = request.user
    context = request.session.get("context",{})
    if (context == {}):
        context["mensaje"] = request.session.get('mensaje',"")
    turnos = Inscripcion.objects.filter(fecha=date.today()).filter(vacunatorio_id = user.vacunador.vacunatorio_de_trabajo)
    hoy = str(date.today())
    tipos = Vacuna.objects.all()
    
    if (context["mensaje"] == "") and (not turnos ):
        context["mensaje"]= "No existen turnos asignados para el día de hoy."
    else:
        request.session["mensaje"] = ""

    if "registrado" not in context.keys():
        context["registrado"]=""
    if "tipo_a_cargar" not in context.keys():
        context["tipo_a_cargar"]=""

    request.session["context"] = {}
    context["turnos"] = turnos
    context["tipos"] = tipos
    context["today"] = hoy
    return render(request, "ver_turnos_hoy.html", context)

def iniciar_sesion(request, *args, **kwargs):
    context = {}
    user = request.user
    if user.is_authenticated: 
        return redirect("Home")

    if request.POST:
        form = FormularioDeAutenticacion(request.POST)
        if form.is_valid():
            dni = request.POST.get('dni')
            user = Usuario.objects.get(dni = dni)
            if user:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                destination = get_redirect_if_exists(request)
                if destination:
                    return redirect(destination)
                return redirect("Home")
        else:  
            context['login_form'] = form
    else:
        form = FormularioDeAutenticacion()
        context['login_form'] = form
    return render(request, "Login.html", context)



@login_required
def buscar_turno(request):

    if request.POST:
        dni = request.POST["dni"]
        if dni:
            try:
                turno = Inscripcion.objects.get(usuario=dni)
            except Inscripcion.DoesNotExist:
                return HttpResponse("El dni ingresado no tiene turno.")
            else:
                return HttpResponse(turno)
    context = {}
    return render(request, "busqueda_turno.html", context)

@login_required
def descargar_certificado_fiebre_amarilla(request):
    options = {
        'dpi': 360,
        'page-size': 'A4',
        'margin-top': '0.0in',
        'margin-right': '0.0in',
        'margin-bottom': '0.0in',
        'margin-left': '0.0in',
        'encoding': "UTF-8",
        'custom-header': [
           ('Accept-Encoding', 'gzip')
        ],
        'no-outline': None,
    }
    config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
    context = dict.fromkeys("user","vacuna")
    usuario = request.user
    context["user"] = usuario
    vacuna = VacunaAplicada.objects.filter(usuario=usuario,vacuna=Vacuna.objects.get(tipo="Fiebre_amarilla")).first()
    context["vacuna"] = vacuna
    filename = "certificado.pdf"
    path_certificado = os.path.normpath(os.path.join(Path(__file__), os.pardir, os.pardir, "Vacunasist", "Vacunasist", "templates", "CERTIFICADO-RENDER.html"))
    f = open(path_certificado, "w")
    html = loader.get_template("CERTIFICADO.html")
    html_content = html.render(context)
    f.write(html_content)
    f.close()

    certificado = pdfkit.from_file(path_certificado, output_path=None, configuration=config, options=options)
    response = HttpResponse(certificado, content_type=mimetypes.guess_type)
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response

@login_required
def buscar_dni(request): 

    context = dict.fromkeys(["dni","nombre_apellido","fecha_nacimiento","registrado","mensaje"],"")
    dni = request.POST.get("Dni")
    usuario_registrado = Usuario.objects.filter(dni=dni).first()
    
    if (usuario_registrado):
        context["dni"] = dni
        context["nombre_apellido"] = usuario_registrado.nombre_apellido
        context["fecha_nacimiento"] = str(usuario_registrado.fecha_nacimiento)
        context["email"] = usuario_registrado.email
        context["registrado"] = "si"
        request.session["context"] = context
        return redirect(ver_turnos_del_dia)
    
    persona = {"dni":dni}
    headers = {
            'X-Api-Key': 'JhKDui9uWt63sxGsdE1Xw1pGisfKpjZK1WJ7EMmy',
            'Content-Type' : "application/json"
            }
    try:
        response = requests.post("https://hhvur3txna.execute-api.sa-east-1.amazonaws.com/dev/person/lookup", 
        headers=headers, json=persona)
    except:
        context["mensaje"] = "Hubo un fallo en la conexión con el servidor. Vuelva a intentarlo más tarde."
    else:
        if (response.status_code  == 403):
            context["mensaje"] = "Hubo un fallo en la conexión con el servidor. Vuelva a intentarlo más tarde."
        if (response.status_code != 200):
            context["mensaje"] = "El DNI no esta asociado a un documento valido de la República Argentina."
        else:
            persona = response.content
            persona = json.loads(persona)
            context["dni"] = dni
            context["nombre_apellido"] = persona["apellido"]
            context["fecha_nacimiento"] = str(datetime.strptime(persona["fechaNacimiento"][:10],"%Y-%m-%d").date())
            context["registrado"] = "no"
    request.session["context"] = context
    return redirect(ver_turnos_del_dia)


    
