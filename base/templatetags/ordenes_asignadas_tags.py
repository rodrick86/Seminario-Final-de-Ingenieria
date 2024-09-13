from django import template
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from base.models import Orden

register = template.Library()


@register.simple_tag
def obtener_ordenes_asignadas(user):
    tecnico = None
    if hasattr(user, 'tecnico'):
        tecnico = user.tecnico

    if tecnico:
        return Orden.objects.filter(tecnico=tecnico).exclude(estado__exact='finalizado')
    return None
