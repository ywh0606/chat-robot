## ADDED Requirements

### Requirement: Chat API Endpoint
The system SHALL provide a POST endpoint `/api/chat` that accepts user messages and returns AI responses.

#### Scenario: Valid chat request
- **WHEN** POST request is sent to `/api/chat` with JSON body `{"message": "hello"}`
- **THEN** the system returns AI response with status 200

#### Scenario: Invalid request
- **WHEN** POST request is sent with missing or invalid JSON
- **THEN** the system returns 400 error with error message

### Requirement: Stream Response
The system SHALL support streaming responses for better user experience.

#### Scenario: Stream chat endpoint
- **WHEN** POST request is sent to `/api/chat/stream` with user message
- **THEN** the system returns Server-Sent Events (SSE) stream with AI responses

### Requirement: Health Check
The system SHALL provide a GET endpoint `/health` for health checks.

#### Scenario: Health check
- **WHEN** GET request is sent to `/health`
- **THEN** the system returns `{"status": "ok"}`
