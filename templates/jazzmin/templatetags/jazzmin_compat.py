from django import template

register = template.Library()

@register.filter(name='length_is')
def length_is(value, arg):
    """Given a list, return True if its length is equal to arg"""
    try:
        return len(value) == int(arg)
    except (ValueError, TypeError):
        return False 