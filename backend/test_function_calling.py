import httpx
import asyncio
import json
import sys

# 设置标准输出编码为UTF-8
sys.stdout.reconfigure(encoding='utf-8')

async def test_chat():
    async with httpx.AsyncClient() as client:
        # 测试普通聊天
        print("=" * 50)
        print("测试1: 普通聊天")
        print("=" * 50)
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "你好"},
            timeout=60.0
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"搜索: {result.get('searched', False)}")
        print(f"响应: {result.get('response', '')[:200]}...")
        print()

        # 测试需要搜索的问题
        print("=" * 50)
        print("测试2: 需要搜索的问题 (今天天气)")
        print("=" * 50)
        response = await client.post(
            "http://localhost:8000/api/chat",
            json={"message": "今天天气怎么样"},
            timeout=120.0
        )
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"搜索: {result.get('searched', False)}")
        if result.get('searched'):
            print(f"搜索词: {result.get('query', '')}")
        print(f"响应: {result.get('response', '')[:500]}...")

if __name__ == "__main__":
    asyncio.run(test_chat())
