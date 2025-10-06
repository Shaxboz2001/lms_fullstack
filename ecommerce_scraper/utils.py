def clean_price(price_str: str) -> int:
    """Narxni raqamga o‘tkazish ('12 990 000 so‘m' -> 12990000)"""
    return int("".join([c for c in price_str if c.isdigit()]))
