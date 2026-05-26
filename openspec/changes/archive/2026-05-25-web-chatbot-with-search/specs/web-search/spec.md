## ADDED Requirements

### Requirement: Web Search API
The system SHALL provide a POST endpoint `/api/search` that accepts search queries and returns search results.

#### Scenario: Valid search request
- **WHEN** POST request is sent to `/api/search` with JSON body `{"query": "今天的天气"}`
- **THEN** the system returns search results from SerpAPI with status 200

#### Scenario: Search with context
- **WHEN** user asks AI about current information
- **THEN** AI can trigger web search to get real-time data

### Requirement: Search Integration
The system SHALL integrate search results into AI responses when needed.

#### Scenario: AI uses search results
- **WHEN** AI determines a query requires up-to-date information
- **THEN** the system calls SerpAPI and includes results in the AI context
