## Context

创建一个Web前端+Python后端的聊天机器人，需要：
- Web界面用于用户交互
- Python后端处理聊天请求和联网搜索
- 使用MiMo AI模型（通义千问）
- 使用SerpAPI进行联网搜索

## Goals / Non-Goals

**Goals:**
- 实现聊天功能：用户发送消息，AI回复
- 实现联网搜索：AI可以搜索最新信息
- 简单的Web前端界面
- 后端API服务

**Non-Goals:**
- 不实现用户认证/登录
- 不实现复杂的前端框架（用原生HTML/JS）
- 不实现数据库持久化

## Decisions

### 1. 后端框架：FastAPI
- 轻量级异步框架，适合API服务
- 自动生成OpenAPI文档
- 支持流式响应

### 2. 前端：原生HTML/JS
- 无需构建工具，快速原型
- 使用fetch API与后端交互
- 支持Server-Sent Events（SSE）流式显示

### 3. AI模型：MiMo（小米MiMoV2.5Pro）
- 通过API调用
- 支持流式输出

### 4. 搜索：SerpAPI
- 提供实时搜索结果
- 封装简单，Python库支持好

### 5. 架构模式
```
用户 <-> Web前端 <-> FastAPI后端 <-> MiMo AI
                           |
                           +-> SerpAPI搜索
```

## Risks / Trade-offs

- [风险] API密钥暴露 → [缓解] 通过环境变量配置
- [风险] 免费搜索API限制 → [缓解] 限制搜索频率
- [风险] 流式响应兼容性 → [缓解] 前端使用EventSource或fetch流式读取
