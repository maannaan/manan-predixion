class InvalidAmountError(ValueError):
    """Raised when a payment amount is missing, non-numeric, or not strictly positive."""


class UnknownLoanError(LookupError):
    """Raised when post_payment targets a loan_id that does not exist."""


class InvalidPaymentError(ValueError):
    """Raised when required payment fields are invalid (e.g. empty gateway_txn_id)."""
