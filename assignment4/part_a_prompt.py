"""Load the rewritten system prompt from Part A. Do not edit part_a/."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from store import IST

_PART_A_MD = Path(__file__).resolve().parent / "part_a" / "A4_partA_manan.md"


def load_prompt_template() -> str:
    text = _PART_A_MD.read_text(encoding="utf-8")
    marker = "### Rewrite"
    start = text.index(marker)
    fence = text.index("```text", start)
    body_start = text.index("\n", fence) + 1
    body_end = text.index("```", body_start)
    return text[body_start:body_end].strip()


def system_prompt(
    *,
    now: datetime | None = None,
    borrower_first_name: str = "the borrower",
    agent_name: str = "Priya",
    lender_name: str = "Predixion Collections",
) -> str:
    clock = now or datetime(2026, 8, 15, 11, 0, tzinfo=IST)
    return load_prompt_template().format(
        agent_name=agent_name,
        lender_name=lender_name,
        today=clock.astimezone(IST).date().isoformat(),
        weekday=clock.astimezone(IST).strftime("%A"),
        borrower_first_name=borrower_first_name,
    )
