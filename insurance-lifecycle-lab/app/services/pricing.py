from decimal import Decimal

from ..errors import AppError
from ..utils import money


def age_factor(age: int) -> Decimal:
    if age <= 30:
        return Decimal("1.0")
    if age <= 40:
        return Decimal("1.1")
    if age <= 50:
        return Decimal("1.25")
    return Decimal("1.5")


def calculate_premium(product, age: int, sum_insured, term_months: int) -> Decimal:
    if age < product.min_age or age > product.max_age:
        raise AppError(
            422,
            "RULE_AGE_OUT_OF_RANGE",
            f"Age must be between {product.min_age} and {product.max_age}",
        )

    amount = Decimal(str(sum_insured))
    minimum = Decimal(str(product.min_sum_insured))
    maximum = Decimal(str(product.max_sum_insured))
    if amount < minimum or amount > maximum:
        raise AppError(
            422,
            "RULE_SUM_INSURED_OUT_OF_RANGE",
            f"Sum insured must be between {minimum} and {maximum}",
        )

    if term_months not in (product.term_options or []):
        raise AppError(
            422,
            "RULE_TERM_INVALID",
            f"Term must be one of {product.term_options}",
        )

    raw = (
        Decimal(str(product.base_rate))
        * (amount / Decimal("10000"))
        * (Decimal(str(term_months)) / Decimal("12"))
        * age_factor(age)
    )
    return money(raw)
