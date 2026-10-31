from __future__ import annotations

import os

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from part_a_prompt import system_prompt
from store import Store
from tools import build_tools


def build_model():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)


def build_agent(store: Store | None = None, model=None):
    store = store or Store()
    tools = build_tools(store)
    model = model or build_model()
    if model is None:
        return None, store, tools
    memory = MemorySaver()
    agent = create_react_agent(model, tools, checkpointer=memory)
    return agent, store, tools


def turn(agent, user_text: str, thread_id: str = "call-1", store: Store | None = None) -> str:
    prompt = system_prompt(now=None if store is None else store.now)
    result = agent.invoke(
        {
            "messages": [
                SystemMessage(content=prompt),
                HumanMessage(content=user_text),
            ]
        },
        config={"configurable": {"thread_id": thread_id}},
    )
    messages = result["messages"]
    return messages[-1].content


if __name__ == "__main__":
    agent, store, _tools = build_agent()
    if agent is None:
        print("No OPENAI_API_KEY. Tools and eval.py still run without an LLM.")
        raise SystemExit(0)
    print("Collections assistant. Type 'quit' to exit.")
    thread = "interactive"
    while True:
        text = input("borrower> ").strip()
        if not text or text.lower() in {"quit", "exit"}:
            break
        print("agent>", turn(agent, text, thread_id=thread, store=store))
