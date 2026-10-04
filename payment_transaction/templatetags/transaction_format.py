from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def rupiah(value):
    if value is None:
        value = Decimal("0")
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return value
    rounded = int(amount)
    return f"Rp{rounded:,}".replace(",", ".")
