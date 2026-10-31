"""Part B uses the corrected Part A retry logic. Do not duplicate it here."""

from __future__ import annotations

import sys
from pathlib import Path

_PART_A = Path(__file__).resolve().parents[1] / "part_a"
if str(_PART_A) not in sys.path:
    sys.path.insert(0, str(_PART_A))

from A3_partA_manan import (  # noqa: E402
    IST,
    RETRY_GAPS_MIN,
    RETRYABLE,
    notify_crm,
    schedule_retry,
)

__all__ = ["IST", "RETRY_GAPS_MIN", "RETRYABLE", "notify_crm", "schedule_retry"]
