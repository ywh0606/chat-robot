## MODIFIED Requirements

### Requirement: Web Search API
The system SHALL provide a POST endpoint `/api/search` that accepts search queries and returns search results, and also support being called as an internal function for AI function calling.

#### Scenario: Valid search request
- **WHEN** POST request is sent to `/api/search` with JSON body `{"query": "今天的天气"}`
- **THEN** the system returns search results from SerpAPI with status 200

#### Scenario: Internal function call
- **WHEN** AI function calling requests web_search with query parameter
- **THEN** the system SHALL execute search internally and return formatted results

## ADDED Requirements

### Requirement: Search Result Format
The system SHALL return search results in a structured format suitable for both API response and AI consumption.

#### Scenario: API response format
- **WHEN** search is called via `/api/search` endpoint
- **THEN** the system returns JSON with results array containing title, link, and snippet

#### Scenario: AI consumption format
- **WHEN** search is called via function calling
- **THEN** the system returns formatted text with top 3 results including title, link, and snippet