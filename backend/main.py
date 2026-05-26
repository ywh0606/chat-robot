import os
import json
import re
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
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
    message: str = ""
    messages: list = []


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


def needs_retry(text: str) -> bool:
    """检测LLM是否直接输出了原始搜索结果（URL、关键词、XML标签等）而非自然语言回答"""
    text = text.strip()
    if not text:
        return False

    # 包含URL → 直接返回了搜索结果链接
    if re.search(r'https?://', text):
        return True

    # LLM 输出了 XML 标签而非正常回答（tool_call, function_call 等）
    if re.search(r'<(tool_call|function|parameter|invoke)', text):
        return True

    # 没有中文标点（。！？）和英文标点（.!?:）→ 不像正常句子
    has_sentence_punct = bool(re.search(r'[。！？.!?:]', text))

    # 短文本且没有标点 → 原始搜索词
    if len(text) < 50 and not has_sentence_punct:
        return True

    # 多个空格分隔的关键词模式（如 "西安 今天 天气 2026年5月26日"）
    words = text.split()
    if len(words) >= 3 and not has_sentence_punct:
        avg_len = sum(len(w) for w in words) / len(words)
        if avg_len < 5:
            return True

    # 主要由非中文字符组成且没有标点 → 可能是英文标题/链接
    chinese_chars = len(re.findall(r'[一-鿿]', text))
    if chinese_chars < len(text) * 0.2 and not has_sentence_punct:
        return True

    return False


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

        # 收集tool_calls数据（支持多个并行tool_calls）
        tool_calls_map = {}  # index -> {id, name, arguments}
        has_tool_calls = False

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
                            has_tool_calls = True
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in tool_calls_map:
                                    tool_calls_map[idx] = {"id": "", "name": "", "arguments": ""}
                                if "id" in tc:
                                    tool_calls_map[idx]["id"] = tc["id"]
                                if "function" in tc:
                                    if "name" in tc["function"]:
                                        tool_calls_map[idx]["name"] = tc["function"]["name"]
                                    if "arguments" in tc["function"]:
                                        tool_calls_map[idx]["arguments"] += tc["function"]["arguments"]
                            continue

                        # 正常内容流式输出（但如果已检测到tool_calls则不输出）
                        content = delta.get("content", "")
                        if content and not has_tool_calls:
                            yield f"data: {json.dumps({'content': content})}\n\n"

                    except json.JSONDecodeError:
                        continue

        # 如果检测到web_search tool_calls，执行搜索并继续
        search_calls = [tc for tc in tool_calls_map.values() if tc["name"] == "web_search"]
        if has_tool_calls and search_calls:
            # 通知前端正在搜索
            yield f"data: {json.dumps({'status': 'searching'})}\n\n"

            # 并行执行所有搜索
            queries = []
            for tc in search_calls:
                try:
                    arguments = json.loads(tc["arguments"])
                    queries.append(arguments.get("query", ""))
                except json.JSONDecodeError:
                    queries.append("")

            search_results = await asyncio.gather(
                *[execute_web_search(q) for q in queries]
            )

            # 构造assistant message（包含所有tool_calls）
            assistant_tool_calls = []
            for tc in search_calls:
                assistant_tool_calls.append({
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                })
            messages.append({"role": "assistant", "tool_calls": assistant_tool_calls})

            # 为每个tool_call添加对应的tool message
            for tc, result in zip(search_calls, search_results):
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result
                })

            # 第二次流式调用，获取最终回答
            payload2 = {
                "model": MIMO_MODEL,
                "messages": messages,
                "tools": [],
                "stream": True
            }

            # 收集完整回答后检查是否为原始搜索结果
            collected_content = ""
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
                                collected_content += content
                        except json.JSONDecodeError:
                            continue

            # 如果检测到原始搜索结果（URL、关键词、XML标签等），追加纠正指令重试
            if needs_retry(collected_content):
                print(f"[DEBUG] Detected raw search output: {repr(collected_content[:80])}, retrying...")
                messages.append({"role": "assistant", "content": collected_content})
                messages.append({
                    "role": "user",
                    "content": (
                        '你的上一条回答不是有效的回答。你不能输出URL链接、搜索关键词或XML标签。\n'
                        '请你仔细阅读前面 tool 消息中的搜索结果摘要，然后用中文写一段自然语言回答。\n'
                        '例如，如果搜索结果提到温度是25度、天气是晴天，你应该回答：西安今天天气晴朗，气温约25度。\n'
                        '请直接给出回答，不要输出任何链接或标签。'
                    )
                })
                payload3 = {
                    "model": MIMO_MODEL,
                    "messages": messages,
                    "tools": [],
                    "stream": True
                }
                collected_content = ""
                async with client.stream("POST", url, json=payload3, headers=headers, timeout=60.0) as response3:
                    async for line in response3.aiter_lines():
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
                                    collected_content += content
                            except json.JSONDecodeError:
                                continue

            # 输出最终内容
            if collected_content:
                yield f"data: {json.dumps({'content': collected_content})}\n\n"


@app.post("/api/chat")
async def chat(request: ChatRequest):
    url = f"{MIMO_BASE_URL}/chat/completions"
    messages = request.messages if request.messages else [{"role": "user", "content": request.message}]

    # 添加当前日期提示，避免AI搜索时使用过时的日期
    today = datetime.now().strftime("%Y年%m月%d日")
    system_msg = {
        "role": "system",
        "content": (
            f"Current date: {today}. When users ask time-related questions (like 'now', 'this year', 'this month'), "
            "the search query MUST include the current date to ensure up-to-date information.\n\n"
            "When constructing search queries, use precise and specific terms. For example, for weather queries, "
            "use '城市名 天气预报 温度' instead of just '天气'.\n\n"
            "CRITICAL: When you receive search results from the web_search tool, you MUST synthesize the information "
            "into a natural language answer. NEVER output raw URLs, titles, or search result snippets directly. "
            "Compose a helpful, conversational response based on the search data. "
            "For weather queries, extract temperature, conditions, and other details to form a structured weather report."
        )
    }
    messages = [system_msg] + messages

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
    messages = request.messages if request.messages else [{"role": "user", "content": request.message}]

    # 添加当前日期提示，避免AI搜索时使用过时的日期
    today = datetime.now().strftime("%Y年%m月%d日")
    system_msg = {
        "role": "system",
        "content": (
            f"Current date: {today}. When users ask time-related questions (like 'now', 'this year', 'this month'), "
            "the search query MUST include the current date to ensure up-to-date information.\n\n"
            "When constructing search queries, use precise and specific terms. For example, for weather queries, "
            "use '城市名 天气预报 温度' instead of just '天气'.\n\n"
            "CRITICAL: When you receive search results from the web_search tool, you MUST synthesize the information "
            "into a natural language answer. NEVER output raw URLs, titles, or search result snippets directly. "
            "Compose a helpful, conversational response based on the search data. "
            "For weather queries, extract temperature, conditions, and other details to form a structured weather report."
        )
    }
    messages = [system_msg] + messages

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