"""
聊天功能模块单元测试
测试 /api/chat 和 /api/chat/stream 端点的功能
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import asynccontextmanager
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_mimo_response():
    """模拟MiMo API响应"""
    return {
        "choices": [
            {
                "message": {
                    "content": "你好！我是AI助手。"
                }
            }
        ]
    }


class TestChatEndpoint:
    """聊天端点测试（非流式）"""

    def test_chat_returns_200(self, client, mock_mimo_response):
        """验证聊天端点返回200状态码"""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mimo_response
            mock_post.return_value = mock_response

            response = client.post("/api/chat", json={"message": "你好"})
            assert response.status_code == 200

    def test_chat_returns_correct_format(self, client, mock_mimo_response):
        """验证聊天返回正确的JSON格式"""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mimo_response
            mock_post.return_value = mock_response

            response = client.post("/api/chat", json={"message": "你好"})
            data = response.json()
            assert "response" in data
            assert data["response"] == "你好！我是AI助手。"

    def test_chat_with_empty_message(self, client, mock_mimo_response):
        """验证空消息也能正常处理"""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mimo_response
            mock_post.return_value = mock_response

            response = client.post("/api/chat", json={"message": ""})
            assert response.status_code == 200

    def test_chat_with_enable_search(self, client, mock_mimo_response):
        """验证enable_search参数可以传递"""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_mimo_response
            mock_post.return_value = mock_response

            response = client.post("/api/chat", json={
                "message": "今天天气怎么样",
                "enable_search": True
            })
            assert response.status_code == 200

    def test_chat_with_invalid_json(self, client):
        """验证无效JSON请求返回422错误"""
        response = client.post(
            "/api/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_chat_with_missing_message(self, client):
        """验证缺少message字段但有messages时返回200"""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "test response"}}]
            }
            mock_post.return_value = mock_response
            response = client.post(
                "/api/chat",
                json={"messages": [{"role": "user", "content": "hello"}]},
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200

    def test_chat_with_empty_choices(self, client):
        """验证API返回空choices数组时不抛出IndexError"""
        empty_choices_response = {"choices": []}
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = empty_choices_response
            mock_post.return_value = mock_response

            response = client.post("/api/chat", json={"message": "你好"})
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == ""
            assert data["searched"] is False


class AsyncLineIterator:
    """模拟异步行迭代器"""
    def __init__(self, lines):
        self._lines = iter(lines)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._lines)
        except StopIteration:
            raise StopAsyncIteration


class TestChatStreamEndpoint:
    """流式聊天端点测试"""

    def _create_mock_stream_context(self, lines):
        """创建模拟的流式响应上下文管理器"""
        mock_response = MagicMock()
        mock_response.aiter_lines.return_value = AsyncLineIterator(lines)

        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            yield mock_response

        return mock_stream

    def test_stream_returns_200(self, client):
        """验证流式端点返回200状态码"""
        mock_lines = [
            'data: {"choices":[{"delta":{"content":"你好"}}]}',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            response = client.post("/api/chat/stream", json={"message": "你好"})
            assert response.status_code == 200

    def test_stream_returns_event_stream(self, client):
        """验证返回Content-Type为text/event-stream"""
        mock_lines = [
            'data: {"choices":[{"delta":{"content":"你好"}}]}',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            response = client.post("/api/chat/stream", json={"message": "你好"})
            assert "text/event-stream" in response.headers["content-type"]

    def test_stream_returns_data(self, client):
        """验证流式响应包含数据"""
        mock_lines = [
            'data: {"choices":[{"delta":{"content":"你好"}}]}',
            'data: {"choices":[{"delta":{"content":"世界"}}]}',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            response = client.post("/api/chat/stream", json={"message": "你好"})
            content = response.content.decode()
            assert "data:" in content
            assert "\\u4f60\\u597d" in content or "你好" in content
            assert "\\u4e16\\u754c" in content or "世界" in content


class TestStreamResponseFunction:
    """stream_response生成器函数测试"""

    def _create_mock_stream_context(self, lines):
        """创建模拟的流式响应上下文管理器"""
        mock_response = MagicMock()
        mock_response.aiter_lines.return_value = AsyncLineIterator(lines)

        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            yield mock_response

        return mock_stream

    @pytest.mark.asyncio
    async def test_stream_generator_yields_content(self):
        """验证流式生成器正确产出内容"""
        from main import stream_response

        mock_lines = [
            'data: {"choices":[{"delta":{"content":"测试"}}]}',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            messages = [{"role": "user", "content": "测试"}]
            results = []
            async for chunk in stream_response(messages):
                results.append(chunk)

            assert len(results) > 0
            assert "\\u6d4b\\u8bd5" in results[0] or "测试" in results[0]

    @pytest.mark.asyncio
    async def test_stream_generator_handles_done(self):
        """验证流式生成器正确处理[DONE]信号"""
        from main import stream_response

        mock_lines = [
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            messages = [{"role": "user", "content": "测试"}]
            results = []
            async for chunk in stream_response(messages):
                results.append(chunk)

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_stream_generator_handles_invalid_json(self):
        """验证流式生成器正确处理无效JSON"""
        from main import stream_response

        mock_lines = [
            'data: invalid json',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            messages = [{"role": "user", "content": "测试"}]
            results = []
            async for chunk in stream_response(messages):
                results.append(chunk)

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_stream_generator_handles_empty_choices(self):
        """验证流式生成器正确处理空choices数组（不抛出IndexError）"""
        from main import stream_response

        mock_lines = [
            'data: {"choices":[]}',
            'data: {"choices":[{"delta":{"content":"正常"}}]}',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            messages = [{"role": "user", "content": "测试"}]
            results = []
            async for chunk in stream_response(messages):
                results.append(chunk)

            assert len(results) == 1
            assert "\\u6b63\\u5e38" in results[0] or "正常" in results[0]

    @pytest.mark.asyncio
    async def test_stream_generator_handles_null_tool_calls(self):
        """验证流式生成器正确处理null tool_calls（不抛出TypeError）"""
        from main import stream_response

        mock_lines = [
            'data: {"choices":[{"delta":{"tool_calls":null}}]}',
            'data: {"choices":[{"delta":{"content":"回复"}}]}',
            'data: [DONE]'
        ]

        with patch("httpx.AsyncClient.stream", side_effect=self._create_mock_stream_context(mock_lines)):
            messages = [{"role": "user", "content": "测试"}]
            results = []
            async for chunk in stream_response(messages):
                results.append(chunk)

            assert len(results) == 1
            assert "\\u56de\\u590d" in results[0] or "回复" in results[0]

    @pytest.mark.asyncio
    async def test_search_notification_uses_actual_newlines(self):
        """验证搜索通知消息使用真实换行符而非转义\\n"""
        from main import stream_response

        # 第一次流：触发tool_calls（web_search）
        mock_lines_1 = [
            'data: {"choices":[{"delta":{"tool_calls":[{"id":"call_1","function":{"name":"web_search","arguments":""}}]}}]}',
            'data: {"choices":[{"delta":{"tool_calls":[{"function":{"arguments":"{\\"query\\":\\"test\\"}"}}]}}]}',
            'data: [DONE]'
        ]

        # 第二次流：搜索后的回答
        mock_lines_2 = [
            'data: {"choices":[{"delta":{"content":"搜索结果"}}]}',
            'data: [DONE]'
        ]

        call_count = [0]

        def mock_stream_factory(*args, **kwargs):
            mock_response = MagicMock()
            if call_count[0] == 0:
                mock_response.aiter_lines.return_value = AsyncLineIterator(mock_lines_1)
            else:
                mock_response.aiter_lines.return_value = AsyncLineIterator(mock_lines_2)
            call_count[0] += 1

            @asynccontextmanager
            async def mock_stream(*a, **kw):
                yield mock_response

            return mock_stream()

        mock_search = AsyncMock(return_value="搜索结果Mock")

        with patch("httpx.AsyncClient.stream", side_effect=mock_stream_factory), \
             patch("main.execute_web_search", mock_search):
            messages = [{"role": "user", "content": "测试"}]
            results = []
            async for chunk in stream_response(messages):
                results.append(chunk)

            # 应该包含搜索通知消息（可能unicode转义）
            search_notifications = [r for r in results if "\\u6b63\\u5728\\u641c\\u7d22" in r or "正在搜索" in r]
            assert len(search_notifications) >= 1
            # 搜索通知应包含真实换行符（\n），而非字面反斜杠+n（\\n）
            notification = json.loads(search_notifications[0].removeprefix("data: "))
            content = notification["content"]
            assert content.startswith("\n\n")
            # 不应包含转义的\\n（即字面反斜杠+n）
            assert "\\n" not in content
