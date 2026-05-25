import httpx
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_stream():
    print("测试流式响应 (端口8001)")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        print("发送请求: 今天北京天气怎么样")
        print("等待流式响应...")
        print()

        async with client.stream(
            "POST",
            "http://localhost:8001/api/chat/stream",
            json={"message": "今天北京天气怎么样"},
            headers={"Content-Type": "application/json"},
            timeout=120.0
        ) as response:
            print(f"状态码: {response.status_code}")
            print()

            full_content = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        content = data.get("content", "")
                        if content:
                            full_content += content
                            print(content, end="", flush=True)
                    except json.JSONDecodeError:
                        pass

            print()
            print()
            print("=" * 60)
            print(f"完整响应长度: {len(full_content)} 字符")

if __name__ == "__main__":
    asyncio.run(test_stream())
