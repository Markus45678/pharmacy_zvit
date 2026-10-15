from django import template

register = template.Library()


@register.simple_tag
def stock_status(quantity):
    if quantity <= 0:
        return 'Немає в наявності'
    if quantity < 5:
        return 'Малий залишок'
    return 'В наявності'
