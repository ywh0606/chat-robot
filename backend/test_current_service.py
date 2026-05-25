import httpx
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_current_service():
    print("测试当前运行的服务是否支持搜索功能")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 测试需要搜索的问题
        print("发送请求: 今天上海天气怎么样")
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "今天上海天气怎么样"},
            timeout=120.0
        )

        print(f"状态码: {response.status_code}")
        result = response.json()

        print(f"searched字段: {result.get('searched', '字段不存在')}")
        if result.get('searched'):
            print(f"搜索词: {result.get('query', '')}")
        print(f"响应: {result.get('response', '')[:500]}...")

if __name__ == "__main__":
    asyncio.run(test_current_service())
