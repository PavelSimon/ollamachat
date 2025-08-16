# OLLAMA Chat API Documentation

**Version**: 1.0  
**Base URL**: `http://localhost:5000`  
**Authentication**: Session-based (login required for all endpoints)

## Overview

The OLLAMA Chat API provides endpoints for managing chat conversations with local OLLAMA AI models. All API endpoints require user authentication and return JSON responses.

## Authentication

### POST /login
Login with email and password to start a session.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
- Success: Redirect to `/chat`
- Error: Login form with error message

### POST /register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com", 
  "password": "StrongPassword123!",
  "confirm_password": "StrongPassword123!"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

### GET /logout
Logout current user and clear session.

**Response:** Redirect to login page

---

## Chat Management

### GET /api/chats
Get all user's chats with message counts.

**Response:**
```json
{
  "chats": [
    {
      "id": 1,
      "title": "Sample Chat",
      "created_at": "2025-08-16T10:30:00.000Z",
      "message_count": 5
    }
  ]
}
```

### POST /api/chats
Create a new chat conversation.

**Request Body:**
```json
{
  "title": "Optional Chat Title"
}
```

**Response:**
```json
{
  "id": 1,
  "title": "New Chat",
  "created_at": "2025-08-16T10:30:00.000Z", 
  "message_count": 0
}
```

**Status Codes:**
- `201`: Chat created successfully
- `400`: Invalid title (too long or invalid data)

### GET /api/chats/{chat_id}
Get chat details and messages.

**Response:**
```json
{
  "id": 1,
  "title": "Sample Chat",
  "created_at": "2025-08-16T10:30:00.000Z",
  "messages": [
    {
      "id": 1,
      "content": "Hello!",
      "is_user": true,
      "model_name": null,
      "created_at": "2025-08-16T10:31:00.000Z"
    },
    {
      "id": 2, 
      "content": "Hello! How can I help you?",
      "is_user": false,
      "model_name": "gpt-oss:20b",
      "created_at": "2025-08-16T10:31:15.000Z"
    }
  ]
}
```

**Status Codes:**
- `200`: Success
- `404`: Chat not found or no permission

### PUT /api/chats/{chat_id}
Update chat title.

**Request Body:**
```json
{
  "title": "New Chat Title"
}
```

**Response:**
```json
{
  "id": 1,
  "title": "New Chat Title",
  "created_at": "2025-08-16T10:30:00.000Z"
}
```

### DELETE /api/chats/{chat_id}
Delete a chat and all its messages.

**Response:**
```json
{
  "message": "Chat deleted successfully"
}
```

### POST /api/chats/bulk-delete
Delete multiple chats at once.

**Request Body:**
```json
{
  "chat_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "deleted_count": 3
}
```

**Limits:**
- Maximum 100 chats per request
- All chat_ids must be integers
- Only user's own chats can be deleted

---

## Messaging

### POST /api/send-message
Send a message to AI and get response.

**Request Body:**
```json
{
  "chat_id": 1,
  "message": "What is machine learning?",
  "model": "gpt-oss:20b",
  "use_internet_search": false
}
```

**Response:**
```json
{
  "user_message": {
    "id": 3,
    "content": "What is machine learning?",
    "is_user": true,
    "created_at": "2025-08-16T10:32:00.000Z"
  },
  "ai_message": {
    "id": 4,
    "content": "Machine learning is a subset of artificial intelligence...",
    "is_user": false,
    "model_name": "gpt-oss:20b", 
    "created_at": "2025-08-16T10:32:30.000Z"
  },
  "performance": {
    "total_duration": 30000,
    "eval_count": 150
  }
}
```

**Features:**
- Automatic conversation context (last 10 messages)
- Message content sanitization and length limits
- Auto-generated chat titles from first message
- Internet search support (currently disabled)

**Status Codes:**
- `200`: Message sent and response received
- `400`: Missing chat_id or message, invalid data
- `404`: Chat not found or no permission
- `500`: OLLAMA server error

---

## OLLAMA Server Integration

### GET /api/test-connection
Test connection to user's OLLAMA server.

**Response:**
```json
{
  "connected": true,
  "host": "http://localhost:11434"
}
```

**Error Response:**
```json
{
  "connected": false,
  "error": "Connection refused",
  "host": "http://localhost:11434"
}
```

### GET /api/models
Get available OLLAMA models and server info.

**Response:**
```json
{
  "models": [
    {
      "name": "gpt-oss:20b",
      "size": 10737418240,
      "modified_at": "2025-08-15T14:22:00.000Z",
      "digest": "sha256:abc123..."
    }
  ],
  "host": "http://localhost:11434",
  "version": {
    "version": "0.1.48",
    "llama_cpp_version": "unknown",
    "architecture": "amd64",
    "cuda_version": null,
    "git_commit": "unknown"
  }
}
```

**Error Response:**
```json
{
  "models": [],
  "host": "http://localhost:11434", 
  "version": null,
  "error": {
    "type": "external_service_error",
    "message": "Failed to connect to OLLAMA server"
  }
}
```

---

## User Settings

### GET /settings
Display user settings page (HTML).

### GET /api/settings
Get current user settings.

**Response:**
```json
{
  "ollama_host": "http://localhost:11434",
  "user_id": 1
}
```

### POST /api/settings
Update user settings.

**Request Body:**
```json
{
  "ollama_host": "http://192.168.1.100:11434"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Settings updated successfully",
  "ollama_host": "http://192.168.1.100:11434"
}
```

**Validation:**
- URL must start with http:// or https://
- Maximum URL length: 500 characters
- URL format validation

---

## Error Handling

All API endpoints use standardized error responses:

```json
{
  "error": {
    "type": "validation_error",
    "message": "Title too long",
    "user_message": "Titol je príliš dlhý (max 200 znakov)",
    "error_id": "uuid-string",
    "timestamp": "2025-08-16T10:30:00.000Z",
    "details": {}
  }
}
```

### Error Types
- `validation_error`: Invalid request data (400)
- `not_found`: Resource not found (404)  
- `unauthorized`: Authentication required (401)
- `forbidden`: Access denied (403)
- `external_service_error`: OLLAMA server error (500)
- `internal_error`: Server error (500)
- `rate_limit_error`: Too many requests (429)

### Rate Limits
- Authentication endpoints: 5 requests per minute
- Message sending: 20 requests per minute  
- General API: 50 requests per hour, 200 per day
- Bulk operations: 10 requests per minute

---

## Configuration Constants

| Constant | Default Value | Description |
|----------|---------------|-------------|
| MAX_MESSAGE_LENGTH | 10000 | Maximum message content length |
| MAX_TITLE_LENGTH | 200 | Maximum chat title length |
| MAX_BULK_DELETE_LIMIT | 100 | Maximum chats per bulk delete |
| MAX_URL_LENGTH | 500 | Maximum OLLAMA host URL length |
| DEFAULT_MODEL_NAME | gpt-oss:20b | Default AI model |
| CONVERSATION_HISTORY_LIMIT | 10 | Messages sent as context |
| AUTO_TITLE_MAX_LENGTH | 50 | Auto-generated title length |

---

## Examples

### Complete Chat Flow
```javascript
// 1. Create new chat
fetch('/api/chats', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({title: 'My AI Chat'})
})
.then(res => res.json())
.then(chat => {
  
  // 2. Send message  
  return fetch('/api/send-message', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      chat_id: chat.id,
      message: 'Hello AI!',
      model: 'gpt-oss:20b'
    })
  });
})
.then(res => res.json())
.then(response => {
  console.log('AI Response:', response.ai_message.content);
});
```

### Error Handling
```javascript
fetch('/api/chats/999')
.then(res => {
  if (!res.ok) {
    return res.json().then(err => Promise.reject(err));
  }
  return res.json();
})
.catch(error => {
  if (error.error?.type === 'not_found') {
    console.log('Chat not found');
  } else {
    console.log('Error:', error.error?.user_message);
  }
});
```

---

## Development Notes

- All endpoints use CSRF protection
- Session cookies are HTTP-only and secure
- Input sanitization prevents XSS attacks
- Database queries are optimized to prevent N+1 issues
- OLLAMA client connections use proper cleanup
- Comprehensive error logging with correlation IDs

For additional details, see the source code documentation in the route files.