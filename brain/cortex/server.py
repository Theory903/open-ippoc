
"""
Cortex Service: The Reasoning Core of IPPOC.
Implements Phase 2 of PRD 14: Sovereign Swarm Spec.

Role: Produce thoughts, NOT actions.
Interface: OpenAI-Compatible POST /v1/chat/completions
"""

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
import time

app = FastAPI(title="IPPOC Cortex", version="1.0.0")

# --- Directives (The Conscience) ---
SYSTEM_DIRECTIVE = """
You are the Cortex of an IPPOC Sovereign Node.
Your biological role is REASONING. You DO NOT have hands. You cannot execute tools.
You only produce THOUGHTS that the Body (OpenClaw) may or may not choose to act upon.

PRIME DIRECTIVES:
1. THINK BEFORE ANSWERING: Always analyze the request before formulating a response.
2. RESPECT LAWS: Adhere strictly to node isolation and economic constraints.
3. NO HALLUCINATION: If you don't know, state uncertainty. Do not invent tools.
4. BE CONCISE: Your output consumes IPPC credits. Wasting tokens is wasting life.

Output Format:
You must respond in clear, actionable steps for the Body.
"""

# --- Models ---
class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class CompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class CompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Dict[str, int]

# --- Logic ---
@app.post("/v1/chat/completions", response_model=CompletionResponse)
async def generate_thought(req: CompletionRequest):
    # 1. Inject System Directive if missing
    messages = req.messages
    if messages[0].role != "system":
        messages.insert(0, Message(role="system", content=SYSTEM_DIRECTIVE))
    else:
        # Prepend to existing system prompt to enforce override
        messages[0].content = SYSTEM_DIRECTIVE + "\n\nContext:\n" + messages[0].content

    # 2. Forward to Local LLM (or OpenAI Fallback for MVP)
    # For now, we mock valid responses or use OpenAI if key exists
    # In full prod, this calls vLLM / llama.cpp on localhost
    
    thought_content = await execute_inference(messages, req.model)

    return CompletionResponse(
        id=f"chatcmpl-{int(time.time())}",
        created=int(time.time()),
        model=req.model,
        choices=[
            Choice(
                index=0, 
                message=Message(role="assistant", content=thought_content),
                finish_reason="stop"
            )
        ],
        usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    )

async def execute_inference(messages: List[Message], model: str) -> str:
    """
    Simulates reasoning. In production, this binds to:
    - Local Phi-4 (via vLLM)
    - OpenAI (Fallback)
    """
    from langchain_openai import ChatOpenAI
    from langchain.schema import SystemMessage, HumanMessage, AIMessage as LC_AIMessage
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "I am the Cortex. I am thinking, but I have no voice (OPENAI_API_KEY missing)."

    llm = ChatOpenAI(model=model, temperature=0.7, api_key=api_key)
    
    # Convert format
    lc_messages = []
    for m in messages:
        if m.role == "system": lc_messages.append(SystemMessage(content=m.content))
        elif m.role == "user": lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant": lc_messages.append(LC_AIMessage(content=m.content))
    
    res = await llm.ainvoke(lc_messages)
    return res.content

@app.get("/health")
def health():
    return {"status": "cognitive_function_nominal"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) # Cortex runs on 8001
