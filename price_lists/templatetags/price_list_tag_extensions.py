from django import template

register = template.Library()


@register.filter
def get_price_list_bonus(feature, price_list):
    return feature.pricelistbonus_set.get(price_list=price_list)
