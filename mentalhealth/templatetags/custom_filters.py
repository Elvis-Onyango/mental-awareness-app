from django import template

register = template.Library()

@register.filter
def enumerate_list(value):
    if value is None:
        return []
    return enumerate(value)
