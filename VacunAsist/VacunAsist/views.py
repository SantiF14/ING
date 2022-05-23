
from django.http import HttpResponse
from django.template import Template,Context,loader


def Index(request):


    doc_externo=loader.get_template("index.html")

    documento=doc_externo.render({})

    return HttpResponse(documento)
    
