
from re import template
from this import d
from django.http import HttpResponse
from django.template import Template,Context
import os


def Index(request):

    doc_externo=open(os.path.normpath(os.path.join(os.path.dirname(
    __file__), "Plantillas", "index.html")))

    plt=Template(doc_externo.read())

    doc_externo.close()

    ctx=Context()

    documento=plt.render(ctx)

    return HttpResponse(documento)
    
