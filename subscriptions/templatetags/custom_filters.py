from django import template

register = template.Library()

@register.filter
def format_duration(duration):
    days = duration.days
    return f"{days} day{'s' if days != 1 else ''}"
