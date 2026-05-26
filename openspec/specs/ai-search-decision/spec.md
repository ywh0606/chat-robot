# ai-search-decision Specification

## Purpose

AI-driven search decision logic, enabling the chat robot to autonomously determine when web search is needed via function calling.
## Requirements
### Requirement: AI自主判断搜索需求
系统 SHALL 实现function calling机制，让AI模型能够自主判断用户问题是否需要联网搜索。

#### Scenario: 用户询问实时信息
- **WHEN** 用户提问涉及最新新闻、天气、股价、实时数据等需要联网获取的信息
- **THEN** AI模型 SHALL 返回tool_calls请求调用web_search函数

#### Scenario: 用户询问通用知识
- **WHEN** 用户提问涉及常识、定义、历史等不需要实时信息的问题
- **THEN** AI模型 SHALL 直接返回回答，不调用搜索函数

#### Scenario: 用户明确要求搜索
- **WHEN** 用户在消息中包含"搜索"、"查询"、"查一下"等关键词
- **THEN** AI模型 SHALL 优先判断为需要搜索并调用web_search函数

### Requirement: 搜索工具定义
系统 SHALL 向AI模型提供标准格式的搜索工具定义。

#### Scenario: 工具定义格式
- **WHEN** 后端调用MiMo API时
- **THEN** 请求中 SHALL 包含tools参数，定义web_search函数及其参数schema

#### Scenario: 工具描述准确性
- **WHEN** 定义web_search工具时
- **THEN** description字段 SHALL 清晰说明何时应该使用搜索功能

