#!/usr/bin/env python3
"""
IPPOC Ollama API Wrapper
Provides a simple HTTP interface to Ollama Cloud API for IPPOC services.
Supports kimi-k2.5:cloud and other Ollama models.
"""

import os
import json
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IPPOC Ollama API", version="1.0.0")

# Ollama configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://api.ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")

# Request/Response models
class GenerateRequest(BaseModel):
    model: Optional[str] = OLLAMA_MODEL
    prompt: str
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[list] = None
    stream: bool = False
    raw: bool = False
    options: Optional[Dict[str, Any]] = None

class GenerateResponse(BaseModel):
    model: str
    response: str
    done: bool
    context: Optional[list] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: Optional[str] = OLLAMA_MODEL
    messages: list
    stream: bool = False
    options: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    model: str
    message: Dict[str, str]
    done: bool
    total_duration: Optional[int] = None

@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/version")
            if resp.status_code == 200:
                return {
                    "status": "healthy", 
                    "ollama_host": OLLAMA_HOST,
                    "default_model": OLLAMA_MODEL
                }
            raise HTTPException(status_code=503, detail="Ollama not available")
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/api/version")
async def version():
    """Get Ollama version."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{OLLAMA_HOST}/api/version")
        return resp.json()

@app.get("/api/tags")
async def list_models():
    """List available models."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{OLLAMA_HOST}/api/tags")
        return resp.json()

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text from a prompt."""
    payload = request.model_dump(exclude_none=True)
    logger.info(f"Generating with model: {payload.get('model', OLLAMA_MODEL)}")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with a model."""
    payload = request.model_dump(exclude_none=True)
    logger.info(f"Chatting with model: {payload.get('model', OLLAMA_MODEL)}")
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/chat", json=payload)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.post("/api/pull")
async def pull_model(name: str):
    """Pull a model from Ollama library."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/pull", json={"name": name})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return {"status": "success", "model": name}

@app.delete("/api/delete")
async def delete_model(name: str):
    """Delete a model."""
    async with httpx.AsyncClient() as client:
        resp = await client.delete(f"{OLLAMA_HOST}/api/delete", json={"name": name})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return {"status": "success", "model": name}

@app.get("/models/{model_name}")
async def model_info(model_name: str):
    """Get information about a specific model."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{OLLAMA_HOST}/api/show", params={"name": model_name})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@app.post("/embed")
async def create_embeddings(input_text: str, model: str = OLLAMA_MODEL):
    """Create embeddings for text using the configured model."""
    payload = {
        "model": model,
        "input": input_text
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{OLLAMA_HOST}/api/embed", json=payload)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
