import httpx
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_debug():
    async with httpx.AsyncClient() as client:
        # 测试原始API响应
        url = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"

        payload = {
            "model": "mimo-v2.5-pro",
            "messages": [{"role": "user", "content": "今天北京天气怎么样"}],
            "tools": [{
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
            }],
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {open('.env').read().split('MIMO_API_KEY=')[1].split(chr(10))[0]}",
            "Content-Type": "application/json"
        }

        print("发送请求到MiMo API...")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        print()

        response = await client.post(url, json=payload, headers=headers, timeout=60.0)
        result = response.json()

        print("=" * 50)
        print("原始API响应:")
        print("=" * 50)
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 检查是否有tool_calls
        choice = result.get("choices", [{}])[0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls")

        print()
        print("=" * 50)
        print("分析结果:")
        print("=" * 50)
        print(f"是否有tool_calls: {tool_calls is not None}")
        if tool_calls:
            print(f"Tool calls: {json.dumps(tool_calls, ensure_ascii=False, indent=2)}")
        else:
            print(f"Content: {message.get('content', '')[:300]}...")

if __name__ == "__main__":
    asyncio.run(test_debug())
