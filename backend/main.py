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

# Function calling工具定义
TOOLS = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "搜索互联网获取最新信息。当用户询问实时信息、新闻、天气、股价、赛事结果、最新动态等需要最新数据的问题时使用。不要用于常识性问题。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，应该是简洁有效的搜索词"
                }
            },
            "required": ["query"]
        }
    }
}]


class ChatRequest(BaseModel):
    message: str
    enable_search: bool = False


class SearchRequest(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "ok"}


async def execute_web_search(query: str) -> str:
    """执行内部搜索，返回格式化的结果文本供AI使用"""
    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        return "搜索功能未配置：请在.env文件中设置有效的SERPAPI_KEY。您可以从 https://serpapi.com 获取免费API密钥。"

    async with httpx.AsyncClient() as client:
        params = {
            "q": query,
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
            organic_results = result.get("organic_results", [])[:3]

            if not organic_results:
                return f"未找到与'{query}'相关的搜索结果"

            formatted = f"搜索'{query}'的结果：\n\n"
            for i, item in enumerate(organic_results, 1):
                title = item.get("title", "无标题")
                link = item.get("link", "")
                snippet = item.get("snippet", "无摘要")
                formatted += f"{i}. {title}\n   链接：{link}\n   摘要：{snippet}\n\n"

            return formatted.strip()
        except Exception as e:
            return f"搜索出错：{str(e)}"


async def stream_response(messages: list):
    url = f"{MIMO_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {MIMO_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # 第一次流式调用，带tools
        payload = {
            "model": MIMO_MODEL,
            "messages": messages,
            "tools": TOOLS,
            "stream": True
        }

        # 收集tool_calls数据
        tool_calls_data = None
        tool_call_id = ""
        tool_function_name = ""
        tool_arguments = ""

        async with client.stream("POST", url, json=payload, headers=headers, timeout=60.0) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})

                        # 检查是否有tool_calls
                        if "tool_calls" in delta and delta["tool_calls"]:
                            tc = delta["tool_calls"][0]
                            if "id" in tc:
                                tool_call_id = tc["id"]
                            if "function" in tc:
                                if "name" in tc["function"]:
                                    tool_function_name = tc["function"]["name"]
                                if "arguments" in tc["function"]:
                                    tool_arguments += tc["function"]["arguments"]
                            tool_calls_data = True
                            continue

                        # 正常内容流式输出
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content})}\n\n"

                    except json.JSONDecodeError:
                        continue

        # 如果检测到tool_calls，执行搜索并继续
        if tool_calls_data and tool_function_name == "web_search":
            try:
                arguments = json.loads(tool_arguments)
                query = arguments.get("query", "")
            except json.JSONDecodeError:
                query = ""

            if query:
                # 通知前端正在搜索
                yield f"data: {json.dumps({'content': f'\n\n正在搜索: {query}...'})}\n\n"

                # 执行搜索
                search_result = await execute_web_search(query)

                # 构造完整的消息历史
                assistant_message = {
                    "role": "assistant",
                    "tool_calls": [{
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": "web_search",
                            "arguments": tool_arguments
                        }
                    }]
                }
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": search_result
                }
                messages.append(assistant_message)
                messages.append(tool_message)

                # 第二次流式调用，获取最终回答
                payload2 = {
                    "model": MIMO_MODEL,
                    "messages": messages,
                    "stream": True
                }

                async with client.stream("POST", url, json=payload2, headers=headers, timeout=60.0) as response2:
                    async for line in response2.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                choices = chunk.get("choices", [])
                                if not choices:
                                    continue
                                content = choices[0].get("delta", {}).get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                            except json.JSONDecodeError:
                                continue


@app.post("/api/chat")
async def chat(request: ChatRequest):
    url = f"{MIMO_BASE_URL}/chat/completions"
    messages = [{"role": "user", "content": request.message}]

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {MIMO_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            # 第一次API调用，带上tools定义
            payload = {
                "model": MIMO_MODEL,
                "messages": messages,
                "tools": TOOLS,
                "stream": False
            }
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            result = response.json()

            # 检查是否有tool_calls
            choices = result.get("choices", [])
            if not choices:
                return {"response": "", "searched": False}
            choice = choices[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls")

            if tool_calls:
                # AI请求调用搜索
                tool_call = tool_calls[0]
                function_name = tool_call.get("function", {}).get("name")
                arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))

                if function_name == "web_search":
                    query = arguments.get("query", "")
                    search_result = await execute_web_search(query)

                    # 将搜索结果添加到消息历史
                    messages.append(message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "content": search_result
                    })

                    # 第二次API调用，获取基于搜索结果的最终回答
                    payload2 = {
                        "model": MIMO_MODEL,
                        "messages": messages,
                        "stream": False
                    }
                    response2 = await client.post(url, json=payload2, headers=headers, timeout=60.0)
                    result2 = response2.json()
                    choices2 = result2.get("choices", [])
                    content = choices2[0].get("message", {}).get("content", "") if choices2 else ""
                    return {"response": content, "searched": True, "query": query}

            # 没有tool_calls，直接返回AI回答
            content = message.get("content", "")
            return {"response": content, "searched": False}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    messages = [{"role": "user", "content": request.message}]

    async def safe_stream():
        try:
            async for chunk in stream_response(messages):
                yield chunk
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'content': f'\n\n错误: {str(e)}'})}\n\n"

    return StreamingResponse(
        safe_stream(),
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