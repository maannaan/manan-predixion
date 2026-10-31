from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from typing import Union

from ledger.exceptions import InvalidAmountError

AmountInput = Union[Decimal, int, str]

_PAISE = Decimal("0.01")


def to_paise(amount: AmountInput) -> int:
    """Convert rupees to integer paise. Rejects float to avoid binary rounding."""
    if isinstance(amount, bool) or isinstance(amount, float):
        raise InvalidAmountError("amount must be Decimal, int, or numeric string — not float")
    try:
        value = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    except (InvalidOperation, ValueError) as exc:
        raise InvalidAmountError(f"invalid amount: {amount!r}") from exc
    if not value.is_finite():
        raise InvalidAmountError("amount must be finite")
    quantized = value.quantize(_PAISE, rounding=ROUND_HALF_EVEN)
    if quantized != value:
        # more than 2 decimal places
        raise InvalidAmountError("amount must have at most 2 decimal places")
    return int(quantized * 100)


def paise_to_decimal(paise: int) -> Decimal:
    return (Decimal(paise) / Decimal(100)).quantize(_PAISE)
