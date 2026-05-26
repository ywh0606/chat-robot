## MODIFIED Requirements

### Requirement: AI加工搜索结果
系统 SHALL 通过 system prompt 明确指导 LLM 将搜索结果综合为自然语言回答，并通过代码层兜底机制检测和重试不良输出。

#### Scenario: 信息总结
- **WHEN** AI 收到搜索结果后
- **THEN** AI SHALL 基于搜索结果生成自然语言回答，禁止直接输出 URL、标题原文或搜索结果片段

#### Scenario: 引用来源
- **WHEN** AI 基于搜索结果回答问题时
- **THEN** AI SHOULD 以自然语言方式提及信息来源（如"根据中国气象局数据"），而非输出原始链接

#### Scenario: 搜索结果不相关
- **WHEN** 搜索结果与用户问题不完全匹配
- **THEN** AI SHALL 说明搜索结果的局限性，并基于可用信息给出最佳回答

#### Scenario: 天气类查询
- **WHEN** 用户查询天气信息
- **THEN** AI SHALL 从搜索结果中提取温度、天气状况等关键数据，组织成结构化的天气描述回答

#### Scenario: 不良输出检测与重试
- **WHEN** LLM 第二次调用的输出包含 URL、XML 标签或原始搜索关键词
- **THEN** 系统 SHALL 检测到不良输出，自动追加纠正指令并重试一次 LLM 调用

## ADDED Requirements

### Requirement: System Prompt 搜索行为约束
系统 SHALL 在 system prompt 中包含搜索结果处理指令，指导 LLM 的搜索后行为。

#### Scenario: System prompt 包含处理指令
- **WHEN** 后端构造发送给 LLM 的 system message
- **THEN** system message SHALL 包含以下指令：LLM 必须将搜索结果综合为自然语言回答，禁止直接输出原始 URL 和搜索片段

#### Scenario: System prompt 包含搜索词构造指导
- **WHEN** 后端构造发送给 LLM 的 system message
- **THEN** system message SHALL 指导 LLM 构造精确的搜索词（如包含城市名 + 日期 + 查询类型）

### Requirement: 多个并行 Tool Calls 支持
系统 SHALL 正确处理 LLM 发出的多个并行 tool_calls。

#### Scenario: LLM 发出多个 web_search 调用
- **WHEN** LLM 在一次响应中发出多个 web_search tool_calls
- **THEN** 系统 SHALL 并行执行所有搜索，构造包含所有 tool_calls 的 assistant message，为每个 tool_call 添加对应的 tool message

#### Scenario: 搜索结果合并
- **WHEN** 多个搜索均完成
- **THEN** 系统 SHALL 将所有搜索结果作为 tool messages 传入第二次 LLM 调用

### Requirement: 输出质量检测
系统 SHALL 检测 LLM 输出是否为有效的自然语言回答。

#### Scenario: 检测 URL 输出
- **WHEN** LLM 输出包含 `https?://` 模式
- **THEN** `needs_retry` SHALL 返回 True 触发重试

#### Scenario: 检测 XML 标签输出
- **WHEN** LLM 输出包含 `<tool_call>`、`<function>`、`<parameter>`、`<invoke>` 等 XML 标签
- **THEN** `needs_retry` SHALL 返回 True 触发重试

#### Scenario: 检测原始搜索关键词
- **WHEN** LLM 输出为短文本（<50字符）且无标点，或为空格分隔的关键词模式
- **THEN** `needs_retry` SHALL 返回 True 触发重试
