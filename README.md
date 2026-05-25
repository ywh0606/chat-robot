# AI Chat Robot

基于 MiMo (小米) 大模型的 AI 聊天应用，支持联网搜索。使用 Python/FastAPI 后端 + 单页 HTML 前端，通过 SSE 实现流式对话。

## 功能特性

- 流式对话 — SSE 实时输出 AI 回复，打字机效果
- 联网搜索 — AI 自动判断是否需要搜索互联网，通过 Function Calling 调用 SerpAPI 获取实时信息
- Markdown 渲染 — AI 回复支持 Markdown 格式（使用 marked.js）
- 无需构建 — 前端为单个 HTML 文件，无框架依赖

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.13+, FastAPI, httpx, uvicorn |
| 前端 | HTML/CSS/JS, marked.js |
| LLM | MiMo API (OpenAI 兼容接口) |
| 搜索 | SerpAPI (Google Search) |

## 快速开始

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 2. 配置环境变量

复制示例配置并填入你的 API Key：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：

```env
MIMO_API_KEY=your_mimo_api_key_here
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=gemma-2-27b-instruct

SERPAPI_KEY=your_serpapi_key_here
```

- `MIMO_API_KEY` — MiMo 平台 API 密钥
- `SERPAPI_KEY` — SerpAPI 密钥（可选，用于联网搜索），可从 [serpapi.com](https://serpapi.com) 获取免费额度

### 3. 启动服务

```bash
cd backend && python main.py
```

服务启动后访问 http://localhost:8000 即可使用。

Windows 用户也可使用 PowerShell 重启脚本：

```powershell
.\restart_server.ps1
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/chat` | 非流式聊天（支持 Function Calling） |
| `POST` | `/api/chat/stream` | SSE 流式聊天（前端默认使用） |
| `POST` | `/api/search` | 直接搜索代理 |
| `GET`  | `/health` | 健康检查 |

### 请求示例

```bash
# 流式聊天
curl -N -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "今天天气怎么样？"}'

# 非流式聊天
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

## 项目结构

```
chat-robot/
├── backend/
│   ├── main.py              # FastAPI 应用（单文件）
│   ├── requirements.txt     # Python 依赖
│   ├── .env.example         # 环境变量示例
│   ├── test_chat.py         # 聊天接口测试
│   ├── test_search.py       # 搜索接口测试
│   └── test_health.py       # 健康检查测试
├── frontend/
│   └── index.html           # 前端页面（单文件）
├── restart_server.ps1       # Windows 重启脚本
└── README.md
```

## 运行测试

```bash
cd backend && pytest
```

测试使用 `unittest.mock` 模拟外部 API 调用，无需真实 API Key。

## 工作原理

1. 用户发送消息 → 前端通过 SSE 连接 `/api/chat/stream`
2. 后端将消息转发给 MiMo LLM，附带 `web_search` 工具定义
3. LLM 判断是否需要搜索：
   - **需要搜索** → 返回 `tool_calls`，后端执行 SerpAPI 搜索，将结果回传 LLM，生成最终回答
   - **无需搜索** → 直接生成回答
4. 全程流式输出，前端实时渲染 Markdown
