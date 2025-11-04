# 🌐 Buggy Call API Documentation

## Base URL
```
Development: http://localhost:5000
Production: https://your-domain.com
```

## Authentication
Most endpoints require authentication using JWT tokens or session cookies.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Giriş başarılı",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

---

## Locations API

### Get All Locations
```http
GET /api/locations
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 10,
    "page": 1
  }
}
```

### Create Location
```http
POST /api/locations
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Pool",
  "description": "Hotel Pool Area",
  "latitude": 41.0082,
  "longitude": 28.9784
}
```

---

## Buggies API

### Get All Buggies
```http
GET /api/buggies
Authorization: Bearer {token}
```

### Create Buggy
```http
POST /api/buggies
Authorization: Bearer {token}
Content-Type: application/json

{
  "code": "BUGGY-01",
  "model": "Club Car",
  "license_plate": "34ABC123",
  "driver_id": 1
}
```

---

## Requests API

### Create Request
```http
POST /api/requests
Content-Type: application/json

{
  "location_id": 1,
  "room_number": "204",
  "notes": "Please hurry"
}
```

### Accept Request (Driver)
```http
PUT /api/requests/{id}/accept
Authorization: Bearer {token}
```

### Complete Request (Driver)
```http
PUT /api/requests/{id}/complete
Authorization: Bearer {token}
```

---

## Health Check

### Health Status
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-XX..."
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "error": "Validation failed",
  "errors": {...}
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Unauthorized"
}
```

### 429 Rate Limit
```json
{
  "success": false,
  "error": "Rate limit exceeded"
}
```

---

## Rate Limits
- Authentication: 5 requests/minute
- API endpoints: 30 requests/minute
- Guest endpoints: 10 requests/minute
