## Why

需要创建一个具备聊天和联网搜索功能的AI聊天机器人，支持用户与AI对话以及实时联网查询信息。

## What Changes

- 创建Python后端API服务（FastAPI）
- 创建Web前端界面（HTML/JS）
- 实现聊天功能（与AI模型交互）
- 实现联网搜索功能（SerpAPI）
- 支持流式响应展示

## Capabilities

### New Capabilities

- `chat-interface`: Web聊天界面，支持用户输入和AI回复展示，流式响应结果
- `chat-backend`: Python后端聊天API，处理用户消息并调用AI模型
- `web-search`: 联网搜索功能，通过SerpAPI获取实时搜索结果

## Impact

- 新增 `backend/` 目录存放Python后端代码
- 新增 `frontend/` 目录存放Web前端文件
- 依赖：fastapi, uvicorn, httpx, serpapi