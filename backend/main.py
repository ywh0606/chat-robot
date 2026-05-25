import os
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "gemma-2-27b-instruct")


class ChatRequest(BaseModel):
    message: str
    enable_search: bool = False


class SearchRequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "ok"}


async def stream_response(messages: list):
    url = f"{MIMO_BASE_URL}/chat/completions"
    async with httpx.AsyncClient() as client:
        payload = {
            "model": MIMO_MODEL,
            "messages": messages,
            "stream": True
        }
        headers = {
            "Authorization": f"Bearer {MIMO_API_KEY}",
            "Content-Type": "application/json"
        }
        async with client.stream("POST", url, json=payload, headers=headers, timeout=60.0) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    except json.JSONDecodeError:
                        continue


@app.post("/api/chat")
async def chat(request: ChatRequest):
    url = f"{MIMO_BASE_URL}/chat/completions"
    messages = [{"role": "user", "content": request.message}]

    async with httpx.AsyncClient() as client:
        payload = {
            "model": MIMO_MODEL,
            "messages": messages,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {MIMO_API_KEY}",
            "Content-Type": "application/json"
        }
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {"response": content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    messages = [{"role": "user", "content": request.message}]
    return StreamingResponse(
        stream_response(messages),
        media_type="text/event-stream"
    )


@app.post("/api/search")
async def search(request: SearchRequest):
    if not SERPAPI_KEY:
        raise HTTPException(status_code=500, detail="SERPAPI_KEY not configured")

    async with httpx.AsyncClient() as client:
        params = {
            "q": request.query,
            "api_key": SERPAPI_KEY,
            "engine": "google"
        }
        try:
            response = await client.get(
                "https://serpapi.com/search",
                params=params,
                timeout=30.0
            )
            result = response.json()
            results = []
            for item in result.get("organic_results", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            return {"results": results}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)