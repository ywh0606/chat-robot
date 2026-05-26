## Context

当前 system prompt 仅包含日期信息和搜索时机指导，缺少对搜索结果处理方式的指令。gemma-2-27b-instruct 模型在 function calling 场景下，收到搜索结果后可能直接输出原始数据片段（URL + 标题），而非综合成自然语言回答。

现有代码路径：`backend/main.py` 的 `stream_response()` 函数在第一次 LLM 调用检测到 tool_call 后，执行 SerpAPI 搜索，将结果作为 tool message 传入第二次 LLM 调用。第二次调用时 `tools=[]`，LLM 应该输出最终回答，但因缺乏指令约束，行为不可控。

实际测试发现三个额外问题：
- LLM 可能在 content 中输出 `<tool_call>` XML 标签而非使用正确的 function calling 协议
- LLM 可能发出多个并行 tool_calls（如同时搜索天气和大模型），原代码只处理最后一个
- 即使有 system prompt 指令，LLM 仍可能输出原始搜索词，需要代码层兜底

## Goals / Non-Goals

**Goals:**
- LLM 收到搜索结果后必须输出自然语言综合回答，禁止输出原始 URL、搜索片段或 XML 标签
- 支持 LLM 发出多个并行 tool_calls，正确执行所有搜索并合并结果
- 检测到不良输出时自动重试，提高回答成功率
- 搜索查询构造应包含日期上下文，提升结果时效性

**Non-Goals:**
- 不更换 LLM 模型
- 不改变前端展示逻辑
- 不修改 API 接口格式

## Decisions

### 1. 在 system prompt 中增加搜索结果处理指令

在现有的 system prompt 末尾追加明确的行为约束，指导 LLM 如何处理 tool 返回的搜索结果。

**理由**: 对于 instruction-following 能力较弱的小模型，显式指令比隐式期望更可靠。这是最小改动、最高效果的方案。

### 2. 代码层兜底：needs_retry 检测 + 自动重试

新增 `needs_retry()` 函数，用正则检测 LLM 输出是否包含 URL、XML 标签、短关键词等不良模式。检测到时自动追加纠正指令重试一次。

**理由**: system prompt 不能 100% 保证模型遵守指令，代码层兜底是必要的防线。只重试一次避免无限循环。

**替代方案**: 在代码层直接过滤 URL——但这治标不治本，且可能误伤正常引用链接的场景。

### 3. 支持多个并行 tool_calls

用 `tool_calls_map`（按 index 索引）替代单一变量，用 `asyncio.gather` 并行执行所有搜索，构造包含所有 tool_calls 的 assistant message。

**理由**: LLM 可能同时发出多个搜索请求（如天气+大模型），原代码只处理最后一个导致搜索结果丢失、前端收到空内容。这是导致"AI 未返回有效内容"的直接原因。

### 4. 天气查询使用 SerpAPI 的 `google` 引擎但优化搜索词

保持使用 Google 引擎，但在 system prompt 中指导 LLM 构造更精确的搜索词（如 "西安 今天天气预报 温度"）。

**理由**: SerpAPI 的 `weather` 引擎需要付费计划，且返回的结构化数据格式可能不稳定。通过优化搜索词，用免费的 Google 引擎也能获得足够好的天气信息摘要。

## Risks / Trade-offs

- **[system prompt 过长]** → 指令精简到必要内容，总 prompt 控制在合理长度内
- **[模型仍不遵守指令]** → 有 `needs_retry` 兜底，重试时使用更具体的纠正指令（含示例）
- **[重试增加延迟]** → 只重试一次，且仅在检测到不良输出时触发，不影响正常流程
- **[搜索结果本身质量差]** → SerpAPI 返回的 snippet 实际包含温度、天气状况等有用数据，经验证可用于生成回答
