from datetime import date
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import Template,Context,loader
from gestion_de_usuarios.models import Inscripcion
from gestion_de_usuarios.forms import FormularioDeRegistro, FormularioDeAutenticacion
from django.contrib.auth import login, authenticate, logout



# Create your views here.


def registrar(request):

    user = request.user
    if user.is_authenticated:
        return HttpResponse("Ya iniciaste sesión como " + str(user.get_full_name()))

    context = {}
    if request.POST:
        form = FormularioDeRegistro(request.POST)
        if form.is_valid():
            print("hola")
            form.save("as12")
            dni = form.cleaned_data.get('dni')
            raw_password = form.cleaned_data.get('password1')
            account = authenticate(dni=dni, contrasenia= raw_password)
            login(request, account)
            return redirect("Home")
        else:
            context['registration_form'] = form

    else:
        form = FormularioDeRegistro()
        context['registration_form'] = form
    return render(request, 'registro2.0.html', context)


def cerrar_sesion(request):
    logout(request)
    return redirect("Index")


def ver_turnos_del_dia(request):
    try: 
        turnos = Inscripcion.objects.filter(fecha=date.today())
    except Inscripcion.DoesNotExist:
        return HttpResponse("No hay turnos asignados para el día de hoy.")
    context = {"turnos": turnos}
    return render(request, "ver_turnos_hoy.html", context)

def iniciar_sesion(request, *args, **kwargs):
    context = {}

    user = request.user
    if user.is_authenticated: 
        return redirect("Index/")

    if request.POST:
        form = FormularioDeAutenticacion(request.POST)
        print(request.POST)
        if form.is_valid():
            print("hola")
            dni = request.POST.get('dni')
            password = request.POST.get('password')
          #  clave_alfanumerica = request.POST['clave_alfanumerica']
            user = authenticate(dni=dni, password=password)
            if user is not None:
                login(request, user)
                return redirect("adentro")
        else:
            context['login_form'] = form
    return render(request, "Login.html",context)


def entraste(request):
    return render(request, 'entraste.html')

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