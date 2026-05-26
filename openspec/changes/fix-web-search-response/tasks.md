# Tasks

## 1. System Prompt 强化

- [x] 1.1 修改 `backend/main.py` 中 `chat_stream` 端点的 system prompt，追加搜索结果处理指令：要求 LLM 将搜索结果综合为自然语言回答，禁止输出原始 URL 和搜索片段；指导 LLM 构造精确搜索词（如 "城市名 天气预报 温度"）
- [x] 1.2 同步修改 `chat` 非流式端点的 system prompt，保持两个端点指令一致

## 2. 输出质量检测与重试机制

- [x] 2.1 新增 `needs_retry()` 函数，检测 LLM 输出是否为不良内容：包含 URL（`https?://`）、XML 标签（`<tool_call>`、`<function>`、`<parameter>`、`<invoke>`）、短文本无标点、空格分隔的关键词模式
- [x] 2.2 在 `stream_response()` 的第二次 LLM 调用后，收集完整回答并用 `needs_retry()` 检测，若检测到不良输出则追加纠正指令重试一次

## 3. 多个并行 Tool Calls 支持

- [x] 3.1 将 `stream_response()` 中的单一 tool_call 变量（`tool_call_id`、`tool_function_name`、`tool_arguments`）替换为 `tool_calls_map`（按 index 索引的字典），支持 LLM 同时发出多个 tool_calls
- [x] 3.2 用 `asyncio.gather` 并行执行所有 web_search 调用，构造包含所有 tool_calls 的 assistant message，为每个 tool_call 添加对应的 tool message
- [x] 3.3 新增 `import asyncio` 和 `import re`

## 4. 测试验证

- [x] 4.1 运行现有测试 `cd backend && pytest test_chat.py -v`，确认所有修改后 16 个测试全部通过
- [x] 4.2 启动服务器手动测试天气查询和多轮对话，验证 AI 返回自然语言描述而非原始 URL（需用户手动验证）
