from django.http import HttpResponse
from django.shortcuts import render
from django.template import Template,Context,loader

# Create your views here.

def Signup(request):

    #doc_externo=open(os.path.normpath(os.path.join(os.path.dirname(
    #__file__), "VacunAsist", "templates", "index.html")))

    #plt=Template(doc_externo.read())

    #doc_externo.close()

    doc_externo=loader.get_template("Registro.html")

    documento=doc_externo.render({})

    return HttpResponse(documento)

def Login(request):

    #doc_externo=open(os.path.normpath(os.path.join(os.path.dirname(
    #__file__), "VacunAsist", "templates", "index.html")))

    #plt=Template(doc_externo.read())

    #doc_externo.close()


    return render(request, "Login.html")
