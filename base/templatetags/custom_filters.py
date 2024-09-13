from django import template

register = template.Library()

@register.filter
def exclude_estado_finalizado(ordenes):
    # Filtra las órdenes excluyendo las que tienen estado 'finalizado'
    return [orden for orden in ordenes if orden.estado != 'finalizado']


@register.filter
def dictkey(dictionary, key):
    return dictionary.get(key)

@register.filter
def calcular_porcentaje(valor, total):
    try:
        return (valor / total) * 100
    except (TypeError, ZeroDivisionError):
        return 0

@register.filter
def color_class(estado):
    if estado == 'pendiente':
        return 'warning'
    elif estado == 'asignado':
        return 'secondary'
    elif estado == 'pausado':
        return 'warning'
    elif estado == 'frenado':
        return 'danger'
    elif estado == 'finalizado':
        return 'success'
    elif estado == 'aprobado':
        return 'danger'
    elif estado == 'entregado':
        return 'success'
    elif estado == 'presupuestado':
        return 'info'
    elif estado == 'en progreso':
        return 'info'
    return 'default'  # Valor por defecto


@register.filter
def format_timedelta(value):
    if not value:
        return '00:00:00'
    total_segundos = value.total_seconds()
    horas = int(total_segundos // 3600)
    minutos = int((total_segundos % 3600) // 60)
    segundos = int(total_segundos % 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"