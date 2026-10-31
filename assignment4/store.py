from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def seed_accounts() -> dict[str, dict[str, Any]]:
    return {
        "A10001": {
            "account_id": "A10001",
            "name": "Ravi Kumar",
            "dob": "1990-05-12",
            "outstanding": Decimal("15000.00"),
            "minimum_due": Decimal("2500.00"),
            "dpd": 42,
            "status": "OVERDUE",
        },
        "A10002": {
            "account_id": "A10002",
            "name": "Neha Shah",
            "dob": "1988-11-03",
            "outstanding": Decimal("0.00"),
            "minimum_due": Decimal("0.00"),
            "dpd": 0,
            "status": "PAID",
        },
    }


@dataclass
class Store:
    accounts: dict[str, dict[str, Any]] = field(default_factory=seed_accounts)
    verified: set[str] = field(default_factory=set)
    blocked_payment_push: set[str] = field(default_factory=set)
    ptps: list[dict[str, Any]] = field(default_factory=list)
    callbacks: list[dict[str, Any]] = field(default_factory=list)
    escalations: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    now: datetime = field(default_factory=lambda: datetime(2026, 8, 15, 11, 0, tzinfo=IST))

    def log(self, name: str, args: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        self.tool_calls.append({"name": name, "args": args, "result": result})
        return result

    def snapshot(self) -> dict[str, Any]:
        return {
            "verified": set(self.verified),
            "ptps": deepcopy(self.ptps),
            "callbacks": deepcopy(self.callbacks),
            "escalations": deepcopy(self.escalations),
            "outstanding": {k: v["outstanding"] for k, v in self.accounts.items()},
            "tool_names": [c["name"] for c in self.tool_calls],
        }
