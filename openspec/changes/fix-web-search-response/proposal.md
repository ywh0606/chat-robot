## Why

当用户通过多轮对话查询天气时，LLM（gemma-2-27b-instruct）直接输出原始搜索结果（URL + 标题），而不是将搜索结果综合成自然语言回答。例如用户问"我在西安"，AI 返回 `https://weather.cma.cn/web/weather/V8870.html 西安 天气` 而非一段天气描述。

根本原因：
1. 系统提示词（system prompt）只告诉 LLM **何时**搜索，没有告诉它**如何处理**搜索结果。对于 function calling 能力较弱的小模型，缺少明确指令会导致它直接输出原始数据。
2. LLM 有时会在 content 中输出 `<tool_call>` XML 标签而非使用正确的 function calling 协议。
3. LLM 可能发出多个并行 tool_calls，但原代码只处理最后一个，导致搜索结果丢失、前端收到空内容。
4. 即使有 system prompt 指令，LLM 仍可能输出原始搜索词，需要代码层兜底检测和重试机制。

## What Changes

- 修改 system prompt，增加对搜索结果处理方式的明确指导：LLM 必须将搜索结果综合为自然语言回答，禁止直接输出 URL 和原始搜索片段
- 增强 system prompt 中的搜索查询构造指导，提示 LLM 使用更精确的搜索词（如 "西安 今天天气" 而非泛泛的 "天气"）
- 新增 `needs_retry()` 函数，检测 LLM 输出是否为原始搜索结果（URL、关键词、XML 标签等），而非自然语言回答
- 在 `stream_response()` 中增加重试机制：检测到不良输出时，自动追加纠正指令并重新请求 LLM 回答
- 修复多个并行 tool_calls 的处理：用 `tool_calls_map` 替代单一变量，支持 LLM 同时发起多个搜索，使用 `asyncio.gather` 并行执行

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `search-result-processing`: 强化"AI 加工搜索结果"的约束——在 system prompt 中增加明确指令；新增输出质量检测和自动重试机制；支持多个并行 tool_calls 的正确处理

## Impact

- **backend/main.py**: 修改 `stream_response()` 函数（支持多 tool_calls、增加重试机制）、新增 `needs_retry()` 函数、修改 `chat_stream` 和 `chat` 端点的 system prompt、新增 `import asyncio` 和 `import re`
- **现有测试**: `test_chat.py` 中的 16 个测试全部通过，无需修改
- **无 API 变更**: 前端和外部 API 接口不变
