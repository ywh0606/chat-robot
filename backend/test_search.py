"""
搜索功能模块单元测试
测试 /api/search 端点和SerpAPI集成功能
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_serpapi_response():
    """模拟SerpAPI响应"""
    return {
        "organic_results": [
            {
                "title": "测试标题1",
                "link": "https://example.com/1",
                "snippet": "测试摘要1"
            },
            {
                "title": "测试标题2",
                "link": "https://example.com/2",
                "snippet": "测试摘要2"
            },
            {
                "title": "测试标题3",
                "link": "https://example.com/3",
                "snippet": "测试摘要3"
            }
        ]
    }


@pytest.fixture
def mock_serpapi_empty_response():
    """模拟SerpAPI空响应"""
    return {
        "organic_results": []
    }


class TestSearchEndpoint:
    """搜索端点测试"""

    def test_search_returns_200(self, client, mock_serpapi_response):
        """验证搜索端点返回200状态码"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response

                response = client.post("/api/search", json={"query": "测试查询"})
                assert response.status_code == 200

    def test_search_returns_results(self, client, mock_serpapi_response):
        """验证搜索返回结果列表"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response

                response = client.post("/api/search", json={"query": "测试查询"})
                data = response.json()
                assert "results" in data
                assert len(data["results"]) == 3

    def test_search_result_format(self, client, mock_serpapi_response):
        """验证搜索结果格式正确"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response

                response = client.post("/api/search", json={"query": "测试查询"})
                data = response.json()
                result = data["results"][0]
                assert "title" in result
                assert "link" in result
                assert "snippet" in result

    def test_search_limits_results_to_5(self, client):
        """验证搜索结果限制为5条"""
        mock_response_data = {
            "organic_results": [
                {"title": f"标题{i}", "link": f"https://example.com/{i}", "snippet": f"摘要{i}"}
                for i in range(10)
            ]
        }

        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_response_data
                mock_get.return_value = mock_response

                response = client.post("/api/search", json={"query": "测试查询"})
                data = response.json()
                assert len(data["results"]) == 5

    def test_search_with_empty_results(self, client, mock_serpapi_empty_response):
        """验证空搜索结果的处理"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_serpapi_empty_response
                mock_get.return_value = mock_response

                response = client.post("/api/search", json={"query": "不存在的内容"})
                data = response.json()
                assert data["results"] == []

    def test_search_with_missing_query(self, client):
        """验证缺少query字段返回422错误"""
        response = client.post("/api/search", json={})
        assert response.status_code == 422

    def test_search_with_invalid_json(self, client):
        """验证无效JSON请求返回422错误"""
        response = client.post(
            "/api/search",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestSearchWithoutApiKey:
    """没有API密钥时的搜索测试"""

    def test_search_without_api_key(self, client):
        """验证没有配置SERPAPI_KEY时返回500错误"""
        with patch("main.SERPAPI_KEY", ""):
            response = client.post("/api/search", json={"query": "测试"})
            assert response.status_code == 500
            data = response.json()
            assert "SERPAPI_KEY not configured" in data["detail"]

    def test_search_with_api_key(self, client, mock_serpapi_response):
        """验证配置了SERPAPI_KEY时正常工作"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response

                response = client.post("/api/search", json={"query": "测试"})
                assert response.status_code == 200


class TestSearchApiCall:
    """搜索API调用测试"""

    def test_search_calls_serpapi_with_correct_params(self, client, mock_serpapi_response):
        """验证搜索使用正确的参数调用SerpAPI"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_serpapi_response
                mock_get.return_value = mock_response

                client.post("/api/search", json={"query": "天气预报"})

                mock_get.assert_called_once()
                call_args = mock_get.call_args
                assert call_args[1]["params"]["q"] == "天气预报"
                assert call_args[1]["params"]["api_key"] == "test_key"
                assert call_args[1]["params"]["engine"] == "google"

    def test_search_handles_api_error(self, client):
        """验证搜索API调用失败时的错误处理"""
        with patch("main.SERPAPI_KEY", "test_key"):
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.side_effect = Exception("API调用失败")

                response = client.post("/api/search", json={"query": "测试"})
                assert response.status_code == 500
                data = response.json()
                assert "API调用失败" in data["detail"]
