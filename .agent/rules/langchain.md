# LangChain Implementation Standards (IPPOC-OS)

This document defines the strict standards for using LangChain in IPPOC-OS (`ippoc` and `mind/openclaw`).
Deviation requires explicit justification.

## 1. Core Philosophy: LCEL First
**Rule**: All chains must be built using **[LangChain Expression Language (LCEL)](https://python.langchain.com/docs/expression_language/)**.
-   **Forbidden**: Legacy `Chain` classes (e.g., `LLMChain`, `SequentialChain`, `RouterChain`).
-   **Required**: Use the pipe `|` syntax or `.pipe()`.
-   **Reason**: LCEL provides automatic streaming, async support, and efficient parallelization.

```python
# BAD (Legacy)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(input)

# GOOD (LCEL)
chain = prompt | llm | output_parser
result = await chain.ainvoke(input)
```

## 2. Agent Orchestration: LangGraph
**Rule**: All stateful, multi-step, or cycling workflows MUST use **[LangGraph](https://langchain-ai.github.io/langgraph/)**.
-   **Forbidden**: `AgentExecutor` (legacy).
-   **Required**: `StateGraph`, `MessageGraph`.
-   **Structure**:
    -   Define a `TypedDict` (Python) or Interface (TS) for `State`.
    -   Nodes return state updates, not just strings.
    -   Edges determine control flow.

## 3. Imports & Dependencies (Python)
**Rule**: Use granular, integration-specific packages.
-   **Forbidden**: `from langchain.llms import OpenAI`, `from langchain.chat_models import ChatOpenAI`.
-   **Required**:
    -   **Core**: `langchain_core` (Prompts, Runnables, Documents).
    -   **Community**: `langchain_community` (Loaders, Tools).
    -   **OpenAI**: `langchain_openai`.
    -   **Anthropic**: `langchain_anthropic`.

## 4. Imports & Dependencies (TypeScript/Node.js)
**Rule**: Align with LangChain.js v0.2+ modular architecture.
-   **Packages**: `npm install @langchain/core @langchain/community @langchain/openai`.
-   **Imports**:
    ```typescript
    import { StringOutputParser } from "@langchain/core/output_parsers";
    import { ChatOpenAI } from "@langchain/openai";
    ```

## 5. Memory & Context
**Rule**: "Memory" is state, not a magic class.
-   **Forbidden**: `ConversationBufferMemory` inside simple chains.
-   **Required**: Explicit state management via LangGraph `StateSchema`.
-   **Persistence**: Use `RedisChatMessageHistory` or Postgres-backed checkpointers.

## 6. Tools & Thinking
**Rule**: Tools must be strictly typed.
-   **Python**: Use `@tool` decorator with Pydantic `args_schema`.
-   **JS**: Use `DynamicStructuredTool` with Zod schema.
-   **Docstrings**: Every tool MUST have a detailed description string for the LLM.

## 7. Performance & Async
**Rule**: default to Async.
-   **Python**: `async def`, `await chain.ainvoke()`.
-   **JS**: `await model.invoke()`.
-   **Why**: To support high-concurrency swarm operations without blocking the event loop.

## 8. Tracing
**Rule**: All complex chains should be trace-friendly.
-   Ensure `config={"callbacks": [...]}` is passed down to runnables if manual tracing involves standard callbacks.
