from datetime import date
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import Template,Context,loader
from gestion_de_usuarios.models import Inscripcion
from gestion_de_usuarios.forms import FormularioDeRegistro, FormularioDeAutenticacion
from django.contrib.auth import login, authenticate, logout
from gestion_de_usuarios.models import Usuario
import random, string
from django.core.mail import send_mail
from VacunAsist.settings import EMAIL_HOST_USER
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
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
        return HttpResponse("Ya iniciaste sesión como " + str(user.get_full_name()))

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
            #send_mail('Clave alfanumerica Vacunassist',"",EMAIL_HOST_USER,[mail], html_message=html_message)
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
    us = request.user
    turnos = Inscripcion.objects.filter(fecha=date.today()).filter(vacunatorio_id = us.vacunador.vacunatorio_de_trabajo)
    if not turnos:
        return HttpResponse("No hay turnos asignados para el día de hoy.")
    context = {"turnos": turnos}
    print(turnos)
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