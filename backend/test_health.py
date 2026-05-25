"""
健康检查模块单元测试
测试 /health 端点的功能
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    """健康检查端点测试"""

    def test_health_returns_200(self, client):
        """验证健康检查端点返回200状态码"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_format(self, client):
        """验证健康检查返回正确的JSON格式"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_health_response_content_type(self, client):
        """验证响应Content-Type为application/json"""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"
