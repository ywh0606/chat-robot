## Context

当前聊天机器人使用小米MiMo模型（OpenAI兼容API），已有独立的SerpAPI搜索端点但未与AI对话集成。用户希望AI能够自主判断是否需要联网搜索，实现智能化的信息获取。

**现有架构：**
- 后端：FastAPI，单文件`main.py`
- AI调用：通过httpx POST到MiMo API，无function calling
- 搜索：独立的`/api/search`端点，使用SerpAPI
- 前端：原生HTML/JS，已有`enable_search`标志但后端未使用

## Goals / Non-Goals

**Goals:**
- 实现AI function calling机制，让模型自主决定是否搜索
- 将SerpAPI搜索集成到AI对话流程
- AI获取搜索结果后进行加工总结
- 支持流式和非流式两种模式

**Non-Goals:**
- 不实现多轮对话历史（当前架构不支持）
- 不添加新的搜索提供商
- 不修改前端UI（只需移除手动搜索触发）

## Decisions

### 1. 使用OpenAI兼容的function calling格式

**选择：** 采用OpenAI的tools/tool_choice格式定义搜索函数

**理由：**
- MiMo API兼容OpenAI格式，大概率支持function calling
- 无需学习新的API格式
- 社区广泛使用，文档完善

**备选方案：**
- 自定义prompt引导模型输出特殊标记：脆弱且难以维护
- 使用LangChain等框架：过度工程化

### 2. 搜索工具定义

```python
tools = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "搜索互联网获取最新信息，当用户询问实时信息、新闻、天气、股价等需要最新数据的问题时使用",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，应该是简洁有效的搜索词"
                }
            },
            "required": ["query"]
        }
    }
}]
```

### 3. 对话流程设计

**非流式模式：**
1. 发送消息到MiMo API（带tools定义）
2. 如果返回`tool_calls`，执行搜索
3. 将搜索结果作为`tool`角色消息发送回API
4. 获取最终响应返回给用户

**流式模式：**
- 暂不支持function calling的流式处理
- 检测到tool_calls时，切换为非流式处理
- 搜索完成后，以流式方式返回最终响应

### 4. 搜索结果处理

**选择：** 让AI模型自己处理和总结搜索结果

**理由：**
- 模型擅长信息提取和总结
- 无需额外的后端处理逻辑
- 保持架构简单

**实现：**
- 将搜索结果（标题、链接、摘要）格式化为文本
- 作为tool消息发送给模型
- 模型基于搜索结果生成回答

## Risks / Trade-offs

**[风险] MiMo模型可能不支持function calling**
→ 先测试API调用，如果不支持则回退到prompt engineering方案

**[风险] 搜索结果质量不稳定**
→ 限制返回前3条结果，减少噪音
→ 让AI模型自行判断信息可信度

**[风险] 增加响应延迟**
→ 搜索本身需要时间，无法避免
→ 前端已有loading状态，用户体验可接受

**[权衡] 流式模式下function calling的处理**
→ 选择：检测到tool_calls时暂停流式，搜索完成后继续
→ 代价：用户体验有短暂中断
→ 好处：实现简单可靠
