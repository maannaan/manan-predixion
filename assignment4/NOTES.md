# Assignment 4 — notes

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
