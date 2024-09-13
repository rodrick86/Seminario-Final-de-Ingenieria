from django import template

register = template.Library()

@register.filter
def range_filter(value):
    """Genera una lista de números de 1 a 'value' (inclusive)."""
    return range(1, value + 1)

@register.filter
def to(value):
    """Genera una lista de números de 1 a 'value' (inclusive)."""
    return range(1, value + 1)