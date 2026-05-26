## Why

当前聊天机器人的搜索功能是独立的API端点，用户需要手动触发。用户希望AI能够自主判断何时需要联网搜索，自动获取最新信息并加工后返回，提升对话的智能化和实用性。

## What Changes

- 实现AI function calling机制，让MiMo模型能够自主决定是否调用搜索
- 将现有SerpAPI搜索功能集成到AI对话流程中
- AI获取搜索结果后，进行信息加工和总结后返回给用户
- 移除前端手动搜索触发逻辑，改为AI自动判断

## Capabilities

### New Capabilities
- `ai-search-decision`: AI通过function calling自主判断是否需要联网搜索
- `search-result-processing`: AI对搜索结果进行加工、总结后返回给用户

### Modified Capabilities
- `chat-backend`: 添加function calling支持，集成搜索工具调用流程
- `web-search`: 修改为可被AI function calling调用的工具函数

## Impact

- **后端代码**: `backend/main.py` 需要添加tools定义、function calling处理逻辑
- **API变更**: `/api/chat` 和 `/api/chat/stream` 端点需要支持tool calling流程
- **依赖**: 无需新增依赖，现有httpx已足够
- **配置**: 需要确认MiMo模型是否支持function calling（OpenAI兼容格式通常支持）