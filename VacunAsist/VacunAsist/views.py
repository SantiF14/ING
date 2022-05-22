
from django.http import HttpResponse
from django.template import Template,Context,loader


def Index(request):

    #doc_externo=open(os.path.normpath(os.path.join(os.path.dirname(
    #__file__), "VacunAsist", "templates", "index.html")))

    #plt=Template(doc_externo.read())

    #doc_externo.close()

    doc_externo=loader.get_template("index.html")

    documento=doc_externo.render({})

    return HttpResponse(documento)
    
