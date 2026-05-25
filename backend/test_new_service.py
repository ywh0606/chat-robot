import httpx
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_new_service():
    print("测试新服务 (端口8001) 的搜索功能")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 测试普通聊天
        print("\n测试1: 普通聊天")
        response = await client.post(
            "http://localhost:8001/api/chat",
            json={"message": "你好"},
            timeout=60.0
        )
        result = response.json()
        print(f"搜索: {result.get('searched', False)}")
        print(f"响应: {result.get('response', '')[:200]}...")

        # 测试需要搜索的问题
        print("\n测试2: 需要搜索的问题")
        response = await client.post(
            "http://localhost:8001/api/chat",
            json={"message": "今天北京天气怎么样"},
            timeout=120.0
        )
        result = response.json()
        print(f"搜索: {result.get('searched', False)}")
        if result.get('searched'):
            print(f"搜索词: {result.get('query', '')}")
        print(f"响应: {result.get('response', '')[:500]}...")

if __name__ == "__main__":
    asyncio.run(test_new_service())
