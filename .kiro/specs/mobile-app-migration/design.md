# Design Document

## Overview

Bu tasarım, mevcut Flask tabanlı shuttle Call web uygulamasını modern bir mobil uygulama mimarisine taşımayı hedeflemektedir. Yeni mimari üç ana katmandan oluşacaktır:

1. **Mobile App (React Native + Expo)**: iOS ve Android için native mobil uygulama
2. **Backend API (FastAPI)**: Yüksek performanslı Python REST API
3. **Database (PostgreSQL)**: İlişkisel veritabanı

### Mimari Prensipler

- **Separation of Concerns**: Her katman kendi sorumluluğuna odaklanır
- **API-First Design**: Backend API, mobil uygulama ve gelecekteki istemciler için tasarlanmıştır
- **Security by Default**: JWT authentication, input validation, rate limiting
- **Performance Optimized**: Connection pooling, caching, eager loading
- **Real-time Updates**: WebSocket ve FCM push notifications
- **Offline Support**: Local caching ve sync mekanizması

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Mobile App Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Guest UI   │  │  Driver UI   │  │   Admin UI   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│              ┌────────────┴────────────┐                     │
│              │  React Native (Expo)    │                     │
│              │  - Navigation           │                     │
│              │  - State Management     │                     │
│              │  - API Client           │                     │
│              │  - FCM Integration      │                     │
│              │  - QR Scanner           │                     │
│              └─────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                           │
                    HTTPS (REST + WebSocket)
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Backend API Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  FastAPI Application                  │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐     │   │
│  │  │   Routes   │  │  Services  │  │ Middleware │     │   │
│  │  └────────────┘  └────────────┘  └────────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Core Components                          │   │
│  │  - JWT Authentication                                 │   │
│  │  - Pydantic Validation                                │   │
│  │  - SQLAlchemy ORM                                     │   │
│  │  - WebSocket Manager                                  │   │
│  │  - FCM Admin SDK                                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                    PostgreSQL Protocol
                           │
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              PostgreSQL Database                      │   │
│  │  - Hotels, Users, Locations                           │   │
│  │  - shuttles, Requests                                  │   │
│  │  - Audit Trail                                        │   │
│  │  - Indexes & Constraints                              │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Mobile App

- **Framework**: React Native 0.72+ with Expo SDK 49+
- **Language**: TypeScript 5.0+
- **Navigation**: React Navigation 6.x
- **State Management**: Redux Toolkit + RTK Query
- **UI Components**: React Native Paper / Native Base
- **QR Scanner**: expo-camera + expo-barcode-scanner
- **Push Notifications**: expo-notifications + Firebase Cloud Messaging
- **Storage**: AsyncStorage + SQLite (offline cache)
- **HTTP Client**: Axios with interceptors
- **WebSocket**: socket.io-client

#### Backend API

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.10+
- **ORM**: SQLAlchemy 2.0+
- **Migration**: Alembic
- **Validation**: Pydantic 2.0+
- **Authentication**: python-jose (JWT)
- **Password Hashing**: passlib with bcrypt
- **WebSocket**: FastAPI WebSocket + python-socketio
- **Push Notifications**: firebase-admin SDK
- **CORS**: fastapi-cors-middleware
- **Rate Limiting**: slowapi
- **Testing**: pytest + pytest-asyncio

#### Database

- **RDBMS**: PostgreSQL 14+
- **Connection Pooling**: SQLAlchemy pool (size: 20, max_overflow: 40)
- **Extensions**: uuid-ossp, pg_trgm (for text search)

#### DevOps

- **Containerization**: Docker + Docker Compose
- **Mobile Build**: Expo EAS Build
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry (error tracking)

## Components and Interfaces

### Mobile App Components

#### 1. Authentication Module

```typescript
// src/modules/auth/
├── screens/
│   ├── LoginScreen.tsx
│   └── ChangePasswordScreen.tsx
├── services/
│   └── authService.ts
├── store/
│   └── authSlice.ts
└── types/
    └── auth.types.ts
```

**Key Features**:

- JWT token storage (AsyncStorage)
- Auto token refresh
- Biometric authentication (optional)
- Role-based navigation

#### 2. Guest Module

```typescript
// src/modules/guest/
├── screens/
│   ├── QRScannerScreen.tsx
│   ├── LocationSelectScreen.tsx
│   ├── RequestFormScreen.tsx
│   └── RequestStatusScreen.tsx
├── services/
│   └── requestService.ts
└── components/
    ├── QRScanner.tsx
    └── RequestCard.tsx
```

**Key Features**:

- QR kod okuma
- Lokasyon seçimi
- shuttle çağırma formu
- Real-time durum takibi

#### 3. Driver Module

```typescript
// src/modules/driver/
├── screens/
│   ├── DashboardScreen.tsx
│   ├── RequestListScreen.tsx
│   ├── RequestDetailScreen.tsx
│   ├── ActiveRequestScreen.tsx
│   └── LocationSetupScreen.tsx
├── services/
│   └── driverService.ts
└── components/
    ├── RequestListItem.tsx
    ├── shuttleStatusCard.tsx
    └── LocationPicker.tsx
```

**Key Features**:

- Bekleyen requestleri görüntüleme
- Request kabul etme
- Aktif request yönetimi
- Lokasyon güncelleme
- Push notification handling

#### 4. Admin Module

```typescript
// src/modules/admin/
├── screens/
│   ├── DashboardScreen.tsx
│   ├── LocationManagementScreen.tsx
│   ├── shuttleManagementScreen.tsx
│   ├── DriverManagementScreen.tsx
│   ├── ReportsScreen.tsx
│   └── QRGeneratorScreen.tsx
├── services/
│   ├── locationService.ts
│   ├── shuttleService.ts
│   └── userService.ts
└── components/
    ├── LocationForm.tsx
    ├── shuttleForm.tsx
    ├── DriverForm.tsx
    └── QRCodeGenerator.tsx
```

**Key Features**:

- CRUD operations (locations, shuttles, drivers)
- QR kod oluşturma ve indirme
- Raporlama ve istatistikler
- Real-time dashboard

#### 5. Shared Components

```typescript
// src/shared/
├── components/
│   ├── Button.tsx
│   ├── Input.tsx
│   ├── Card.tsx
│   ├── LoadingSpinner.tsx
│   └── ErrorBoundary.tsx
├── hooks/
│   ├── useAuth.ts
│   ├── useWebSocket.ts
│   ├── useNotifications.ts
│   └── useOfflineSync.ts
├── utils/
│   ├── api.ts
│   ├── storage.ts
│   ├── validation.ts
│   └── dateHelpers.ts
└── constants/
    ├── colors.ts
    ├── routes.ts
    └── config.ts
```

### Backend API Components

#### 1. API Routes Structure

```python
# app/api/
├── v1/
│   ├── __init__.py
│   ├── auth.py          # Authentication endpoints
│   ├── locations.py     # Location CRUD
│   ├── shuttles.py       # shuttle CRUD
│   ├── requests.py      # Request management
│   ├── users.py         # User management
│   ├── reports.py       # Reporting endpoints
│   └── health.py        # Health check
└── deps.py              # Dependencies (auth, db session)
```

#### 2. Service Layer

```python
# app/services/
├── __init__.py
├── auth_service.py      # Authentication logic
├── location_service.py  # Location business logic
├── shuttle_service.py     # shuttle business logic
├── request_service.py   # Request business logic
├── user_service.py      # User management
├── fcm_service.py       # Push notification service
├── audit_service.py     # Audit trail logging
└── websocket_service.py # WebSocket event handling
```

#### 3. Database Models

```python
# app/models/
├── __init__.py
├── base.py              # Base model with common fields
├── hotel.py             # Hotel model
├── user.py              # SystemUser model
├── location.py          # Location model
├── shuttle.py             # shuttle model
├── shuttle_driver.py      # shuttleDriver association
├── request.py           # shuttleRequest model
├── audit.py             # AuditTrail model
└── enums.py             # Enums (UserRole, shuttleStatus, RequestStatus)
```

#### 4. Pydantic Schemas

```python
# app/schemas/
├── __init__.py
├── auth.py              # Login, Token, ChangePassword
├── location.py          # LocationCreate, LocationUpdate, LocationResponse
├── shuttle.py             # shuttleCreate, shuttleUpdate, shuttleResponse
├── request.py           # RequestCreate, RequestAccept, RequestComplete
├── user.py              # UserCreate, UserUpdate, UserResponse
└── common.py            # PaginationParams, ErrorResponse
```

#### 5. Middleware & Dependencies

```python
# app/middleware/
├── __init__.py
├── auth.py              # JWT verification, role checking
├── rate_limit.py        # Rate limiting
├── error_handler.py     # Global error handling
└── logging.py           # Request/response logging

# app/core/
├── __init__.py
├── config.py            # Configuration management
├── security.py          # Password hashing, JWT utils
└── database.py          # Database session management
```

## Data Models

### PostgreSQL Schema

#### 1. hotels

```sql
CREATE TABLE hotels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    logo VARCHAR(500),
    timezone VARCHAR(50) DEFAULT 'Europe/Istanbul',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hotels_code ON hotels(code);
```

#### 2. system_users

```sql
CREATE TABLE system_users (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'driver')),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
    fcm_token VARCHAR(255),
    fcm_token_date TIMESTAMP,
    notification_preferences TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE INDEX idx_users_hotel ON system_users(hotel_id);
CREATE INDEX idx_users_username ON system_users(username);
CREATE INDEX idx_users_role ON system_users(role);
CREATE INDEX idx_users_active ON system_users(is_active);
CREATE INDEX idx_users_fcm_token ON system_users(fcm_token);
```

#### 3. locations

```sql
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    qr_code_data VARCHAR(500) NOT NULL UNIQUE,
    qr_code_image TEXT,
    location_image TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_locations_hotel ON locations(hotel_id);
CREATE INDEX idx_locations_qr_code ON locations(qr_code_data);
CREATE INDEX idx_locations_active ON locations(is_active);
CREATE INDEX idx_locations_order ON locations(display_order);
```

#### 4. shuttles

```sql
CREATE TABLE shuttles (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    current_location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    model VARCHAR(100),
    license_plate VARCHAR(50),
    icon VARCHAR(10),
    status VARCHAR(20) NOT NULL DEFAULT 'available'
        CHECK (status IN ('available', 'busy', 'offline')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_shuttles_hotel ON shuttles(hotel_id);
CREATE INDEX idx_shuttles_code ON shuttles(code);
CREATE INDEX idx_shuttles_status ON shuttles(status);
CREATE INDEX idx_shuttles_location ON shuttles(current_location_id);
```

#### 5. shuttle_drivers (Association Table)

```sql
CREATE TABLE shuttle_drivers (
    id SERIAL PRIMARY KEY,
    shuttle_id INTEGER NOT NULL REFERENCES shuttles(id) ON DELETE CASCADE,
    driver_id INTEGER NOT NULL REFERENCES system_users(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMP,
    UNIQUE(shuttle_id, driver_id)
);

CREATE INDEX idx_shuttle_drivers_shuttle ON shuttle_drivers(shuttle_id);
CREATE INDEX idx_shuttle_drivers_driver ON shuttle_drivers(driver_id);
CREATE INDEX idx_shuttle_drivers_active ON shuttle_drivers(is_active);
```

#### 6. shuttle_requests

```sql
CREATE TABLE shuttle_requests (
    id SERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    completion_location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    shuttle_id INTEGER REFERENCES shuttles(id) ON DELETE SET NULL,
    accepted_by_id INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    guest_name VARCHAR(255),
    room_number VARCHAR(50),
    has_room BOOLEAN NOT NULL DEFAULT TRUE,
    phone VARCHAR(50),
    notes TEXT,
    guest_fcm_token VARCHAR(500),
    guest_fcm_token_expires_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'ACCEPTED', 'COMPLETED', 'CANCELLED', 'UNANSWERED')),
    cancelled_by VARCHAR(50),
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    accepted_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    timeout_at TIMESTAMP,
    response_time INTEGER,
    completion_time INTEGER
);

CREATE INDEX idx_requests_hotel ON shuttle_requests(hotel_id);
CREATE INDEX idx_requests_location ON shuttle_requests(location_id);
CREATE INDEX idx_requests_shuttle ON shuttle_requests(shuttle_id);
CREATE INDEX idx_requests_driver ON shuttle_requests(accepted_by_id);
CREATE INDEX idx_requests_status ON shuttle_requests(status);
CREATE INDEX idx_requests_room ON shuttle_requests(room_number);
CREATE INDEX idx_requests_requested_at ON shuttle_requests(requested_at);
```

#### 7. audit_trail

```sql
CREATE TABLE audit_trail (
    id BIGSERIAL PRIMARY KEY,
    hotel_id INTEGER NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES system_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_hotel ON audit_trail(hotel_id);
CREATE INDEX idx_audit_user ON audit_trail(user_id);
CREATE INDEX idx_audit_action ON audit_trail(action);
CREATE INDEX idx_audit_entity ON audit_trail(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_trail(created_at);
```

### Data Migration Strategy

#### MySQL to PostgreSQL Migration

**Phase 1: Schema Migration**

1. Export MySQL schema using `mysqldump --no-data`
2. Convert MySQL types to PostgreSQL equivalents:
   - `INT AUTO_INCREMENT` → `SERIAL`
   - `DATETIME` → `TIMESTAMP`
   - `ENUM` → `VARCHAR` with CHECK constraint
   - `TEXT` → `TEXT` (same)
3. Create PostgreSQL schema with Alembic migrations
4. Add indexes and constraints

**Phase 2: Data Migration**

1. Export data from MySQL: `mysqldump --no-create-info`
2. Transform data:
   - Convert datetime formats
   - Handle enum values
   - Escape special characters
3. Import to PostgreSQL using `COPY` command
4. Verify data integrity with row counts and checksums

**Phase 3: Validation**

1. Compare row counts for each table
2. Validate foreign key relationships
3. Test sample queries
4. Run application smoke tests

**Migration Script Example**:

```python
# scripts/migrate_mysql_to_postgres.py
import pymysql
import psycopg2
from datetime import datetime

def migrate_table(mysql_conn, pg_conn, table_name, transform_fn=None):
    """Migrate single table from MySQL to PostgreSQL"""
    mysql_cursor = mysql_conn.cursor(pymysql.cursors.DictCursor)
    pg_cursor = pg_conn.cursor()

    # Fetch all rows from MySQL
    mysql_cursor.execute(f"SELECT * FROM {table_name}")
    rows = mysql_cursor.fetchall()

    # Transform and insert into PostgreSQL
    for row in rows:
        if transform_fn:
            row = transform_fn(row)

        columns = ', '.join(row.keys())
        placeholders = ', '.join(['%s'] * len(row))
        values = tuple(row.values())

        pg_cursor.execute(
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
            values
        )

    pg_conn.commit()
    print(f"✅ Migrated {len(rows)} rows from {table_name}")
```

## API Endpoints

### Authentication Endpoints

```
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
POST   /api/v1/auth/change-password
GET    /api/v1/auth/me
```

### Location Endpoints

```
GET    /api/v1/locations              # List all locations
GET    /api/v1/locations/{id}         # Get location by ID
POST   /api/v1/locations              # Create location (Admin)
PUT    /api/v1/locations/{id}         # Update location (Admin)
DELETE /api/v1/locations/{id}         # Delete location (Admin)
GET    /api/v1/locations/qr/{qr_code} # Get location by QR code
POST   /api/v1/locations/{id}/qr      # Generate QR code (Admin)
```

### shuttle Endpoints

```
GET    /api/v1/shuttles                # List all shuttles
GET    /api/v1/shuttles/{id}           # Get shuttle by ID
POST   /api/v1/shuttles                # Create shuttle (Admin)
PUT    /api/v1/shuttles/{id}           # Update shuttle (Admin)
DELETE /api/v1/shuttles/{id}           # Delete shuttle (Admin)
PUT    /api/v1/shuttles/{id}/status    # Update shuttle status (Driver)
PUT    /api/v1/shuttles/{id}/location  # Update shuttle location (Driver)
```

### Request Endpoints

```
GET    /api/v1/requests               # List requests (filtered by role)
GET    /api/v1/requests/{id}          # Get request by ID
POST   /api/v1/requests               # Create request (Guest)
PUT    /api/v1/requests/{id}/accept   # Accept request (Driver)
PUT    /api/v1/requests/{id}/complete # Complete request (Driver)
PUT    /api/v1/requests/{id}/cancel   # Cancel request (Admin)
GET    /api/v1/requests/pending       # Get pending requests (Driver)
GET    /api/v1/requests/active        # Get active request (Driver)
```

### User Endpoints

```
GET    /api/v1/users                  # List users (Admin)
GET    /api/v1/users/{id}             # Get user by ID (Admin)
POST   /api/v1/users                  # Create user (Admin)
PUT    /api/v1/users/{id}             # Update user (Admin)
DELETE /api/v1/users/{id}             # Delete user (Admin)
PUT    /api/v1/users/{id}/fcm-token   # Update FCM token
```

### Report Endpoints

```
GET    /api/v1/reports/dashboard      # Dashboard statistics (Admin)
GET    /api/v1/reports/requests       # Request reports (Admin)
GET    /api/v1/reports/performance    # Performance metrics (Admin)
```

### Health Endpoints

```
GET    /health                        # Health check
GET    /health/db                     # Database health
GET    /health/ready                  # Readiness probe
```

## Authentication & Security

### JWT Authentication Flow

```
┌─────────┐                                    ┌─────────┐
│  Mobile │                                    │ Backend │
│   App   │                                    │   API   │
└────┬────┘                                    └────┬────┘
     │                                              │
     │  1. POST /auth/login                         │
     │  { username, password }                      │
     ├─────────────────────────────────────────────>│
     │                                              │
     │                    2. Verify credentials     │
     │                       Generate JWT tokens    │
     │                                              │
     │  3. { access_token, refresh_token, user }    │
     │<─────────────────────────────────────────────┤
     │                                              │
     │  4. Store tokens in AsyncStorage             │
     │                                              │
     │  5. API Request with Authorization header    │
     │  Authorization: Bearer {access_token}        │
     ├─────────────────────────────────────────────>│
     │                                              │
     │                    6. Verify JWT             │
     │                       Extract user info      │
     │                                              │
     │  7. Response                                 │
     │<─────────────────────────────────────────────┤
     │                                              │
     │  8. Access token expired                     │
     │  POST /auth/refresh                          │
     │  { refresh_token }                           │
     ├─────────────────────────────────────────────>│
     │                                              │
     │  9. { access_token, refresh_token }          │
     │<─────────────────────────────────────────────┤
```

### JWT Token Structure

**Access Token** (expires: 1 hour):

```json
{
  "sub": "user_id",
  "username": "driver1",
  "role": "driver",
  "hotel_id": 1,
  "exp": 1699999999,
  "type": "access"
}
```

**Refresh Token** (expires: 30 days):

```json
{
  "sub": "user_id",
  "exp": 1702591999,
  "type": "refresh"
}
```

### Security Measures

#### 1. Password Security

- Bcrypt hashing with salt rounds: 12
- Minimum password length: 8 characters
- Password complexity requirements (optional)
- Password change on first login (optional)

#### 2. API Security

- HTTPS only (TLS 1.2+)
- CORS configuration (whitelist origins)
- Rate limiting: 100 requests/minute per IP
- Input validation with Pydantic
- SQL injection protection (ORM)
- XSS protection (sanitize inputs)

#### 3. Token Security

- Secure storage (AsyncStorage with encryption)
- Token rotation on refresh
- Automatic logout on token expiration
- Revoke tokens on logout

#### 4. Role-Based Access Control (RBAC)

```python
# Dependency for role checking
async def require_role(required_roles: List[str]):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = get_current_user()
            if current_user.role not in required_roles:
                raise HTTPException(403, "Forbidden")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
@router.post("/locations")
@require_role(["admin"])
async def create_location(...):
    pass
```

## Push Notifications

### Firebase Cloud Messaging (FCM) Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile App                            │
│  ┌────────────────────────────────────────────────┐     │
│  │  1. Initialize FCM                              │     │
│  │  2. Request notification permission             │     │
│  │  3. Get FCM token                               │     │
│  │  4. Send token to backend                       │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           │ POST /users/{id}/fcm-token
                           │ { fcm_token }
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend API                           │
│  ┌────────────────────────────────────────────────┐     │
│  │  1. Store FCM token in database                 │     │
│  │  2. On new request: Get driver tokens           │     │
│  │  3. Send notification via Firebase Admin SDK    │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Firebase Admin SDK
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Firebase Cloud Messaging                    │
│  ┌────────────────────────────────────────────────┐     │
│  │  1. Validate token                              │     │
│  │  2. Queue notification                          │     │
│  │  3. Deliver to device                           │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           │ Push Notification
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Mobile Device                         │
│  ┌────────────────────────────────────────────────┐     │
│  │  1. Receive notification                        │     │
│  │  2. Show notification banner                    │     │
│  │  3. Play sound/vibration                        │     │
│  │  4. On tap: Open app to request detail          │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### FCM Notification Types

#### 1. New Request (Driver)

```json
{
  "notification": {
    "title": "🔔 Yeni shuttle Çağrısı",
    "body": "Oda 305 - Havuz Alanı"
  },
  "data": {
    "type": "new_request",
    "request_id": "123",
    "location_name": "Havuz Alanı",
    "room_number": "305"
  }
}
```

#### 2. Request Accepted (Guest)

```json
{
  "notification": {
    "title": "✅ shuttle Kabul Edildi",
    "body": "shuttle size doğru geliyor"
  },
  "data": {
    "type": "request_accepted",
    "request_id": "123",
    "shuttle_code": "B01"
  }
}
```

#### 3. Request Completed (Guest)

```json
{
  "notification": {
    "title": "🎉 shuttle Ulaştı",
    "body": "İyi yolculuklar!"
  },
  "data": {
    "type": "request_completed",
    "request_id": "123"
  }
}
```

### FCM Service Implementation

**Backend (Python)**:

```python
# app/services/fcm_service.py
from firebase_admin import messaging, credentials, initialize_app
import firebase_admin

class FCMService:
    _app = None

    @classmethod
    def initialize(cls, credentials_path: str):
        """Initialize Firebase Admin SDK"""
        if not cls._app:
            cred = credentials.Certificate(credentials_path)
            cls._app = initialize_app(cred)

    @classmethod
    async def send_notification(
        cls,
        token: str,
        title: str,
        body: str,
        data: dict = None
    ) -> bool:
        """Send FCM notification to single device"""
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='shuttle_requests'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1
                        )
                    )
                )
            )

            response = messaging.send(message)
            return True
        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return False

    @classmethod
    async def send_multicast(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: dict = None
    ) -> int:
        """Send FCM notification to multiple devices"""
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens
        )

        response = messaging.send_multicast(message)
        return response.success_count
```

**Mobile App (TypeScript)**:

```typescript
// src/services/notificationService.ts
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";

export class NotificationService {
  static async registerForPushNotifications(): Promise<string | null> {
    if (!Device.isDevice) {
      console.log("Push notifications only work on physical devices");
      return null;
    }

    // Request permission
    const { status: existingStatus } =
      await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.log("Permission not granted for push notifications");
      return null;
    }

    // Get FCM token
    const token = (await Notifications.getExpoPushTokenAsync()).data;

    // Configure notification channel (Android)
    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("shuttle_requests", {
        name: "shuttle Requests",
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        sound: "default",
      });
    }

    return token;
  }

  static setupNotificationHandlers(
    onNotificationReceived: (notification: any) => void,
    onNotificationTapped: (response: any) => void
  ) {
    // Handle notification received while app is in foreground
    Notifications.addNotificationReceivedListener(onNotificationReceived);

    // Handle notification tapped
    Notifications.addNotificationResponseReceivedListener(onNotificationTapped);
  }
}
```

## WebSocket Real-Time Updates

### WebSocket Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Mobile App                            │
│  ┌────────────────────────────────────────────────┐     │
│  │  1. Connect to WebSocket on app start           │     │
│  │  2. Join room based on role                     │     │
│  │     - Driver: hotel_{id}_drivers                │     │
│  │     - Admin: hotel_{id}_admin                   │     │
│  │     - Guest: request_{id}                       │     │
│  │  3. Listen for events                           │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           │ WebSocket Connection
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend API                           │
│  ┌────────────────────────────────────────────────┐     │
│  │  WebSocket Manager                              │     │
│  │  - Connection management                        │     │
│  │  - Room management                              │     │
│  │  - Event broadcasting                           │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### WebSocket Events

#### 1. Connection Events

```typescript
// Client connects
socket.emit("join_room", {
  hotel_id: 1,
  role: "driver",
  user_id: 5,
});

// Server acknowledges
socket.on("room_joined", (data) => {
  console.log("Joined room:", data.room);
});
```

#### 2. Request Events

```typescript
// New request created (to drivers)
socket.on("new_request", (data) => {
  // data: { request_id, location_name, room_number, ... }
  showNotification("New shuttle request");
  refreshRequestList();
});

// Request accepted (to guest and admin)
socket.on("request_accepted", (data) => {
  // data: { request_id, shuttle_code, driver_name }
  updateRequestStatus("accepted");
});

// Request completed (to all)
socket.on("request_completed", (data) => {
  // data: { request_id, shuttle_id }
  updateRequestStatus("completed");
});
```

#### 3. shuttle Status Events

```typescript
// shuttle status changed (to admin)
socket.on("shuttle_status_changed", (data) => {
  // data: { shuttle_id, status, location_id }
  updateshuttleOnMap(data);
});

// Driver logged in/out (to admin)
socket.on("driver_logged_in", (data) => {
  // data: { driver_id, shuttle_id }
  updateDriverStatus(data);
});
```

### WebSocket Implementation

**Backend (FastAPI)**:

```python
# app/websocket/manager.py
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)

    def disconnect(self, websocket: WebSocket, room: str):
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)

    async def broadcast_to_room(self, room: str, message: dict):
        if room in self.active_connections:
            for connection in self.active_connections[room]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

# app/api/v1/websocket.py
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "default")
    try:
        while True:
            data = await websocket.receive_json()
            # Handle incoming messages
            if data.get('type') == 'join_room':
                room = data.get('room')
                await manager.connect(websocket, room)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "default")
```

**Mobile App (TypeScript)**:

```typescript
// src/services/websocketService.ts
import io from "socket.io-client";

export class WebSocketService {
  private socket: any = null;

  connect(url: string, token: string) {
    this.socket = io(url, {
      auth: { token },
      transports: ["websocket"],
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
    });
  }

  joinRoom(hotelId: number, role: string, userId: number) {
    const room =
      role === "admin" ? `hotel_${hotelId}_admin` : `hotel_${hotelId}_drivers`;

    this.socket.emit("join_room", { room, user_id: userId });
  }

  on(event: string, callback: (data: any) => void) {
    this.socket.on(event, callback);
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Geçersiz veri",
    "details": [
      {
        "field": "room_number",
        "message": "Oda numarası gereklidir"
      }
    ],
    "timestamp": "2024-11-16T10:30:00Z",
    "request_id": "abc123"
  }
}
```

### Error Codes

| Code                 | HTTP Status | Description              |
| -------------------- | ----------- | ------------------------ |
| VALIDATION_ERROR     | 400         | Input validation failed  |
| UNAUTHORIZED         | 401         | Authentication required  |
| FORBIDDEN            | 403         | Insufficient permissions |
| NOT_FOUND            | 404         | Resource not found       |
| CONFLICT             | 409         | Resource conflict        |
| BUSINESS_LOGIC_ERROR | 422         | Business rule violation  |
| RATE_LIMIT_EXCEEDED  | 429         | Too many requests        |
| INTERNAL_ERROR       | 500         | Server error             |

### Error Handling Strategy

**Backend**:

```python
# app/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.state.request_id
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Bir hata oluştu. Lütfen tekrar deneyin.",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

**Mobile App**:

```typescript
// src/utils/errorHandler.ts
export class ErrorHandler {
  static handle(error: any): string {
    if (error.response) {
      // API error response
      const errorData = error.response.data?.error;
      if (errorData) {
        return errorData.message;
      }
      return "Bir hata oluştu";
    } else if (error.request) {
      // Network error
      return "İnternet bağlantınızı kontrol edin";
    } else {
      // Other errors
      return error.message || "Beklenmeyen bir hata oluştu";
    }
  }

  static showError(error: any) {
    const message = this.handle(error);
    Alert.alert("Hata", message);
  }
}
```

## Testing Strategy

### Backend Testing

#### 1. Unit Tests (pytest)

```python
# tests/test_auth_service.py
import pytest
from app.services.auth_service import AuthService
from app.models.user import SystemUser

def test_login_success(db_session):
    # Create test user
    user = SystemUser(
        username='testuser',
        hotel_id=1,
        role='driver',
        full_name='Test User'
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    # Test login
    result = AuthService.login('testuser', 'password123')
    assert result is not None
    assert result.username == 'testuser'

def test_login_invalid_password(db_session):
    with pytest.raises(UnauthorizedException):
        AuthService.login('testuser', 'wrongpassword')
```

#### 2. Integration Tests

```python
# tests/test_api_requests.py
from fastapi.testclient import TestClient

def test_create_request(client: TestClient, auth_headers):
    response = client.post(
        '/api/v1/requests',
        json={
            'location_id': 1,
            'room_number': '305',
            'guest_name': 'John Doe'
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data['location_id'] == 1
    assert data['status'] == 'PENDING'
```

#### 3. Load Tests (locust)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class shuttleCallUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post('/api/v1/auth/login', json={
            'username': 'driver1',
            'password': 'password'
        })
        self.token = response.json()['access_token']

    @task(3)
    def get_pending_requests(self):
        self.client.get(
            '/api/v1/requests/pending',
            headers={'Authorization': f'Bearer {self.token}'}
        )

    @task(1)
    def accept_request(self):
        self.client.put(
            '/api/v1/requests/1/accept',
            json={'shuttle_id': 1},
            headers={'Authorization': f'Bearer {self.token}'}
        )
```

### Mobile App Testing

#### 1. Component Tests (Jest + React Native Testing Library)

```typescript
// src/modules/guest/__tests__/QRScanner.test.tsx
import { render, fireEvent } from "@testing-library/react-native";
import QRScanner from "../components/QRScanner";

describe("QRScanner", () => {
  it("should call onScan when QR code is detected", () => {
    const onScan = jest.fn();
    const { getByTestId } = render(<QRScanner onScan={onScan} />);

    // Simulate QR code scan
    fireEvent(getByTestId("qr-scanner"), "onBarCodeScanned", {
      data: "LOC_001",
    });

    expect(onScan).toHaveBeenCalledWith("LOC_001");
  });
});
```

#### 2. Integration Tests

```typescript
// src/modules/auth/__tests__/login.integration.test.ts
import { renderHook, act } from "@testing-library/react-hooks";
import { useAuth } from "../hooks/useAuth";

describe("Login Integration", () => {
  it("should login successfully and store token", async () => {
    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login("driver1", "password");
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toBeDefined();
  });
});
```

#### 3. E2E Tests (Detox)

```typescript
// e2e/guest-flow.e2e.ts
describe("Guest Flow", () => {
  beforeAll(async () => {
    await device.launchApp();
  });

  it("should complete shuttle request flow", async () => {
    // Scan QR code
    await element(by.id("scan-qr-button")).tap();
    await element(by.id("qr-scanner")).tap();

    // Fill request form
    await element(by.id("room-number-input")).typeText("305");
    await element(by.id("guest-name-input")).typeText("John Doe");
    await element(by.id("submit-button")).tap();

    // Verify success message
    await expect(element(by.text("shuttle çağrınız alındı"))).toBeVisible();
  });
});
```

## Deployment Strategy

### Backend Deployment (Docker)

**Dockerfile**:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**docker-compose.yml**:

```yaml
version: "3.8"

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: shuttlecall
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@db:5432/shuttlecall
      JWT_SECRET: ${JWT_SECRET}
      FCM_CREDENTIALS_PATH: /app/firebase-credentials.json
    volumes:
      - ./firebase-credentials.json:/app/firebase-credentials.json
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  postgres_data:
```

### Mobile App Deployment (Expo EAS)

**eas.json**:

```json
{
  "cli": {
    "version": ">= 3.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "app-bundle"
      },
      "ios": {
        "buildConfiguration": "Release"
      }
    }
  },
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "./google-play-service-account.json",
        "track": "internal"
      },
      "ios": {
        "appleId": "your-apple-id@example.com",
        "ascAppId": "1234567890",
        "appleTeamId": "ABCD123456"
      }
    }
  }
}
```

**Build Commands**:

```bash
# Development build
eas build --profile development --platform android

# Production build
eas build --profile production --platform all

# Submit to stores
eas submit --platform android
eas submit --platform ios
```

### Environment Configuration

**Backend (.env)**:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/shuttlecall

# JWT
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Firebase
FCM_CREDENTIALS_PATH=./firebase-credentials.json

# CORS
CORS_ORIGINS=http://localhost:19000,exp://192.168.1.100:19000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
```

**Mobile App (app.config.js)**:

```javascript
export default {
  expo: {
    name: "shuttle Call",
    slug: "shuttle-call",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    splash: {
      image: "./assets/splash.png",
      resizeMode: "contain",
      backgroundColor: "#1BA5A8",
    },
    assetBundlePatterns: ["**/*"],
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.shuttlecall.app",
      infoPlist: {
        NSCameraUsageDescription:
          "QR kod okumak için kamera erişimi gereklidir",
      },
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#1BA5A8",
      },
      package: "com.shuttlecall.app",
      permissions: ["CAMERA"],
      googleServicesFile: "./google-services.json",
    },
    plugins: [
      [
        "expo-camera",
        {
          cameraPermission: "QR kod okumak için kamera erişimi gereklidir",
        },
      ],
      [
        "expo-notifications",
        {
          icon: "./assets/notification-icon.png",
          color: "#1BA5A8",
        },
      ],
    ],
    extra: {
      apiUrl: process.env.API_URL || "http://localhost:8000",
      eas: {
        projectId: "your-project-id",
      },
    },
  },
};
```

## Performance Optimization

### Backend Optimizations

#### 1. Database Query Optimization

```python
# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload

requests = db.query(shuttleRequest)\
    .options(
        joinedload(shuttleRequest.location),
        joinedload(shuttleRequest.shuttle),
        joinedload(shuttleRequest.accepted_by_driver)
    )\
    .filter_by(hotel_id=hotel_id)\
    .all()
```

#### 2. Connection Pooling

```python
# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### 3. Caching (Redis)

```python
# app/utils/cache.py
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, db=0)

def cache_get(key: str):
    value = redis_client.get(key)
    return json.loads(value) if value else None

def cache_set(key: str, value: any, ttl: int = 300):
    redis_client.setex(key, ttl, json.dumps(value))
```

#### 4. Response Compression

```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Mobile App Optimizations

#### 1. Image Optimization

```typescript
// Use optimized image formats
import { Image } from "expo-image";

<Image
  source={{ uri: imageUrl }}
  contentFit="cover"
  transition={200}
  cachePolicy="memory-disk"
/>;
```

#### 2. List Virtualization

```typescript
// Use FlatList for large lists
import { FlatList } from "react-native";

<FlatList
  data={requests}
  renderItem={({ item }) => <RequestCard request={item} />}
  keyExtractor={(item) => item.id.toString()}
  initialNumToRender={10}
  maxToRenderPerBatch={10}
  windowSize={5}
  removeClippedSubviews={true}
/>;
```

#### 3. Code Splitting

```typescript
// Lazy load screens
import { lazy, Suspense } from "react";

const AdminDashboard = lazy(() => import("./screens/AdminDashboard"));

<Suspense fallback={<LoadingSpinner />}>
  <AdminDashboard />
</Suspense>;
```

#### 4. API Request Optimization

```typescript
// Use RTK Query for caching and deduplication
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

export const api = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({ baseUrl: API_URL }),
  tagTypes: ["Request", "shuttle", "Location"],
  endpoints: (builder) => ({
    getRequests: builder.query({
      query: () => "/requests",
      providesTags: ["Request"],
      keepUnusedDataFor: 60, // Cache for 60 seconds
    }),
  }),
});
```

## Monitoring and Logging

### Backend Monitoring

#### 1. Structured Logging

```python
# app/utils/logger.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
        }
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        return json.dumps(log_data)

logger = logging.getLogger('shuttlecall')
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

#### 2. Performance Monitoring

```python
# app/middleware/performance.py
import time
from fastapi import Request

@app.middleware("http")
async def add_performance_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time}s")

    return response
```

### Mobile App Monitoring

#### 1. Error Tracking (Sentry)

```typescript
// src/utils/sentry.ts
import * as Sentry from "sentry-expo";

Sentry.init({
  dsn: "your-sentry-dsn",
  enableInExpoDevelopment: false,
  debug: __DEV__,
});

// Usage
try {
  await api.createRequest(data);
} catch (error) {
  Sentry.captureException(error);
  throw error;
}
```

#### 2. Analytics

```typescript
// src/utils/analytics.ts
import * as Analytics from "expo-firebase-analytics";

export const logEvent = (eventName: string, params?: object) => {
  Analytics.logEvent(eventName, params);
};

// Usage
logEvent("request_created", { location_id: 1 });
```

## Migration Checklist

### Pre-Migration

- [ ] Backup MySQL database
- [ ] Set up PostgreSQL database
- [ ] Configure Firebase project
- [ ] Set up development environment
- [ ] Create test accounts

### Migration Phase

- [ ] Run database migration script
- [ ] Verify data integrity
- [ ] Deploy backend API
- [ ] Test API endpoints
- [ ] Build mobile app (development)
- [ ] Test mobile app features

### Post-Migration

- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Fix critical bugs
- [ ] Deploy to production

### Rollback Plan

- [ ] Keep Flask app running in parallel
- [ ] Database backup restoration procedure
- [ ] DNS/routing rollback steps
- [ ] Communication plan for users
