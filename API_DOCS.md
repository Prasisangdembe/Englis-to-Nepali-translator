# API Documentation

## Base URL

- Local: `http://localhost:5000`

## Authentication

No authentication is currently enforced. Add API key or token auth for production.

## Rate Limiting

- Global default limit is configured via `RATE_LIMIT_PER_MINUTE` (default: `60 per minute`).
- `POST /api/translate` has an explicit limit of `10 per minute`.

---

## `GET /`

Serves the web interface (`web/templates/index.html`).

### Response

- `200 OK` with HTML content.

---

## `POST /api/translate`

Translate English text to Limbu.

### Request Body

```json
{
  "text": "hello water"
}
```

### Success Response (`200`)

```json
{
  "success": true,
  "translation": {
    "original_text": "hello water",
    "translated_romanized": "sewaro wa",
    "translated_script": "ᤛᤣᤘᤠᤖᤥ ᤘᤠ",
    "found_all": true,
    "tokens": [
      {
        "english": "hello",
        "limbu_romanized": "sewaro",
        "limbu_script": "ᤛᤣᤘᤠᤖᤥ",
        "found": true,
        "method": "dictionary"
      },
      {
        "english": "water",
        "limbu_romanized": "wa",
        "limbu_script": "ᤘᤠ",
        "found": true,
        "method": "dictionary"
      }
    ],
    "method": "hybrid"
  }
}
```

### Error Response (`400`)

```json
{
  "success": false,
  "error": "Field 'text' is required"
}
```

### Rate Limited (`429`)

When the request limit is exceeded.

---

## `GET /api/dictionary/search`

Search dictionary entries by English query.

### Query Parameters

- `q` (required): search text

### Example

`GET /api/dictionary/search?q=thank`

### Success Response (`200`)

```json
{
  "success": true,
  "query": "thank",
  "count": 1,
  "results": [
    {
      "english": "thank you",
      "limbu_romanized": "khambe",
      "limbu_script": "ᤂᤠᤔᤒᤣ"
    }
  ]
}
```

### Error Response (`400`)

```json
{
  "success": false,
  "error": "Query parameter 'q' is required"
}
```

---

## `POST /api/feedback`

Submit translation feedback/suggestions.

### Request Body

```json
{
  "english": "hello",
  "suggested_limbu": "sewaro",
  "comment": "Looks correct"
}
```

### Success Response (`200`)

```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "feedback": {
    "id": 1,
    "english": "hello",
    "suggested_limbu": "sewaro",
    "comment": "Looks correct",
    "status": "received"
  }
}
```

### Error Response (`400`)

```json
{
  "success": false,
  "error": "Fields 'english' and 'suggested_limbu' are required"
}
```

---

## `GET /api/feedback`

Retrieve all submitted feedback entries.

### Success Response (`200`)

```json
{
  "success": true,
  "count": 2,
  "feedback": [
    {
      "id": 1,
      "english": "hello",
      "suggested_limbu": "sewaro",
      "comment": "Looks correct",
      "status": "received"
    }
  ]
}
```

---

## Error Handling Summary

- `400`: Invalid or missing request data.
- `429`: Rate limit exceeded.
- `500`: Unexpected server-side failure.

---

## Future API Enhancements

- API key/JWT authentication
- Versioned endpoints (e.g., `/api/v1/...`)
- Batch translation endpoint
- Pagination for feedback and dictionary search
- Formal OpenAPI/Swagger specification
