import httpx
import asyncio
import json
import sys
import os
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_BASE_URL = os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

TOOLS = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "搜索互联网获取最新信息",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    }
}]

async def execute_web_search(query: str) -> str:
    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        return "搜索功能未配置"

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

async def test_full_flow():
    print("=" * 60)
    print("测试完整Function Calling流程")
    print("=" * 60)
    print(f"SERPAPI_KEY配置: {'已配置' if SERPAPI_KEY and SERPAPI_KEY != 'your_serpapi_key_here' else '未配置'}")
    print()

    async with httpx.AsyncClient() as client:
        url = f"{MIMO_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {MIMO_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = [{"role": "user", "content": "今天北京天气怎么样"}]

        # 第一次调用
        print("步骤1: 发送请求到MiMo API (带tools)")
        payload = {
            "model": MIMO_MODEL,
            "messages": messages,
            "tools": TOOLS,
            "stream": False
        }

        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        result = response.json()

        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls")

        print(f"  finish_reason: {choice.get('finish_reason')}")
        print(f"  有tool_calls: {tool_calls is not None}")

        if tool_calls:
            tool_call = tool_calls[0]
            function_name = tool_call.get("function", {}).get("name")
            arguments = json.loads(tool_call.get("function", {}).get("arguments", "{}"))
            query = arguments.get("query", "")

            print(f"  函数名: {function_name}")
            print(f"  搜索词: {query}")
            print()

            # 执行搜索
            print("步骤2: 执行SerpAPI搜索")
            search_result = await execute_web_search(query)
            print(f"  搜索结果: {search_result[:200]}...")
            print()

            # 第二次调用
            print("步骤3: 将搜索结果发送给AI，获取最终回答")
            messages.append(message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id"),
                "content": search_result
            })

            payload2 = {
                "model": MIMO_MODEL,
                "messages": messages,
                "stream": False
            }

            response2 = await client.post(url, json=payload2, headers=headers, timeout=60.0)
            result2 = response2.json()
            content = result2.get("choices", [{}])[0].get("message", {}).get("content", "")

            print(f"  AI最终回答:")
            print(f"  {content[:500]}...")
        else:
            print(f"  AI直接回答: {message.get('content', '')[:300]}...")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
