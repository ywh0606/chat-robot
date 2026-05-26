## MODIFIED Requirements

### Requirement: Chat API Endpoint
The system SHALL provide a POST endpoint `/api/chat` that accepts user messages and returns AI responses, supporting function calling for search integration.

#### Scenario: Valid chat request
- **WHEN** POST request is sent to `/api/chat` with JSON body `{"message": "hello"}`
- **THEN** the system returns AI response with status 200

#### Scenario: Invalid request
- **WHEN** POST request is sent with missing or invalid JSON
- **THEN** the system returns 400 error with error message

#### Scenario: AI requests search
- **WHEN** AI response contains tool_calls for web_search function
- **THEN** the system SHALL execute the search, send results back to AI, and return the final response

#### Scenario: Search execution flow
- **WHEN** AI returns tool_calls with web_search function
- **THEN** the system SHALL call SerpAPI, format results as tool message, and make follow-up API call to get final answer

### Requirement: Stream Response
The system SHALL support streaming responses for better user experience, with fallback to non-streaming for function calling.

#### Scenario: Stream chat endpoint
- **WHEN** POST request is sent to `/api/chat/stream` with user message
- **THEN** the system returns Server-Sent Events (SSE) stream with AI responses

#### Scenario: Stream with function calling
- **WHEN** streaming response detects tool_calls
- **THEN** the system SHALL pause streaming, execute search, and resume streaming with final response