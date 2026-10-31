# Assignment 4 — notes

## Part A → Part B

`part_a_prompt.py` reads the rewritten voice prompt from `part_a/A4_partA_manan.md` (A1). Evals still judge tools and store state, not wording. There is still no settle/mark-paid tool (A3.4).

## Choices

- LangGraph `create_react_agent` + `MemorySaver` (brief allows LangGraph). Tools are LangChain `@tool`.
- Evals call tools directly so pass/fail is deterministic and matches “tool calls and data state”.
- Clock is injected (`Store.now`) so date-window tests do not depend on wall clock.

## Trade-offs

- Live LLM quality is not scored by eval.py. That is intentional: wording is not the rubric.
- Escalation blocks further PTP on that account for the session; a human would clear it.

## Another day

- Golden-path LLM traces with a recorded model.
- Voice latency: smaller prompts, tool-arg streaming, barge-in cancel.
