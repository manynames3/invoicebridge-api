from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def decimal_text(value: Decimal | None) -> str:
    if value is None:
        return ""
    normalized = value.normalize()
    return format(normalized, "f").rstrip("0").rstrip(".") or "0"


def same_money(left: Decimal | None, right: Decimal) -> bool:
    if left is None:
        return True
    return abs(money(left) - money(right)) <= Decimal("0.01")
