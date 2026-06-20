from django import template

register = template.Library()


@register.filter
def clp(value):
    """Formatea un número como moneda chilena: $1.234.567"""
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    negative = value < 0
    s = str(abs(value))
    groups = []
    while len(s) > 3:
        groups.insert(0, s[-3:])
        s = s[:-3]
    groups.insert(0, s)
    formatted = '.'.join(groups)
    return ('-$' if negative else '$') + formatted
