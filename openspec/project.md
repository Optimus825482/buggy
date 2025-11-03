# Project Context

## Purpose
**Buggy Call** is a professional Progressive Web App (PWA) designed to manage internal transportation requests within hotels. The system digitizes and optimizes hotel buggy services through QR code technology, enabling:

- **Guests**: Quickly call buggies by scanning QR codes at various hotel locations
- **Drivers**: Manage incoming requests and communicate real-time location status
- **Administrators**: Monitor all operations, manage resources, and generate detailed reports

**Core Value Propositions:**
- Fast and easy access via QR codes (no app installation required)
- Real-time coordination through WebSocket connections
- Complete traceability with comprehensive audit trails
- Mobile-first design with full PWA capabilities
- Multi-platform support (iOS, Android, Desktop browsers)

## Tech Stack

### Backend
- **Flask 3.0+** - Core web framework
- **SQLAlchemy 3.1+** - ORM and database abstraction
- **Flask-Migrate 4.0+** - Database migrations (Alembic)
- **Flask-JWT-Extended 4.5+** - JWT authentication
- **Flask-SocketIO 5.3+** - Real-time WebSocket communication
- **Flask-CORS 4.0+** - Cross-origin resource sharing
- **Marshmallow 3.20+** - Serialization and validation

### Database
- **MySQL 8.0+** (Production) / **SQLite** (Development)
- **PyMySQL 1.1+** - Python MySQL driver
- **InnoDB Engine** - ACID transactions and foreign key support

### Security & Authentication
- **bcrypt 4.1+** - Password hashing (PBKDF2-SHA256)
- **cryptography 41.0+** - Additional encryption utilities
- **JWT tokens** - Stateless authentication (1 hour access, 30 day refresh)

### QR Code & Media
- **qrcode 7.4+** - QR code generation (High error correction)
- **Pillow 10.1+** - Image processing and manipulation

### Push Notifications
- **pywebpush 1.14+** - Web Push Protocol implementation
- **VAPID** - Voluntary Application Server Identification

### Real-time Communication
- **python-socketio 5.10+** - Socket.IO protocol
- **eventlet 0.33+** - Concurrent networking library

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling (Grid, Flexbox, CSS Variables)
- **Vanilla JavaScript ES6+** - No framework dependencies
- **Socket.IO Client 4.6+** - Real-time client library
- **html5-qrcode** - QR code scanner for guests

### PWA Features
- **Service Worker** - Offline caching and background sync
- **Web App Manifest** - Installation prompts and app metadata
- **Web Push API** - Native-like notifications
- **IndexedDB** - Client-side storage

### Production Server
- **Gunicorn 21.2+** - WSGI HTTP Server
- **eventlet workers** - For WebSocket support

### Development Tools
- **python-dotenv 1.0+** - Environment variable management
- **pytz 2023.3+** - Timezone handling
- **python-dateutil 2.8+** - Date/time utilities

## Project Conventions

### Code Style

#### Python Backend
- **PEP 8** compliance for all Python code
- **Type hints** encouraged for function signatures
- **Docstrings** required for all classes and public methods (Google style)
- **4 spaces** for indentation (no tabs)
- **Line length**: Maximum 120 characters
- **Import order**: Standard library → Third-party → Local imports

**Naming Conventions:**
- `snake_case` for functions, methods, and variables
- `PascalCase` for class names
- `UPPER_CASE` for constants
- Private methods prefixed with `_`
- Database tables: `snake_case` plural (e.g., `system_users`, `buggy_requests`)
- Model classes: `PascalCase` singular (e.g., `SystemUser`, `BuggyRequest`)

**Example:**
```python
class SystemUser(db.Model, BaseModel):
    """System User model (Admin and Driver)"""
    
    __tablename__ = 'system_users'
    
    def set_password(self, password: str) -> None:
        """Set password hash using bcrypt"""
        self.password_hash = generate_password_hash(password)
```

#### JavaScript Frontend
- **ES6+** modern JavaScript syntax
- **camelCase** for variables and functions
- **PascalCase** for classes and constructors
- **UPPER_CASE** for constants
- **2 spaces** for indentation
- **Semicolons** required
- **Template literals** preferred over string concatenation
- **Arrow functions** for callbacks and short functions
- **Async/await** preferred over raw promises

#### CSS
- **BEM methodology** for component styling (Block__Element--Modifier)
- **CSS Variables** for theme colors and reusable values
- **Mobile-first** approach with min-width media queries
- **Class names**: `kebab-case`
- Custom properties prefixed with `--`

**Theme Colors (from logo):**
```css
:root {
  --primary-color: #1BA5A8;    /* Turquoise */
  --accent-color: #F28C38;      /* Orange */
  --dark-color: #2C3E50;        /* Dark Gray */
  --light-color: #ECF0F1;       /* Light Gray */
  --success-color: #27AE60;     /* Green */
  --danger-color: #E74C3C;      /* Red */
}
```

### Architecture Patterns

#### Project Structure
```
app/
├── models/        # SQLAlchemy models (Database layer)
├── schemas/       # Marshmallow schemas (Validation layer)
├── routes/        # Flask blueprints (Controller layer)
├── services/      # Business logic layer
├── utils/         # Helper functions and decorators
├── websocket/     # WebSocket event handlers
└── static/        # Frontend assets (CSS, JS, images)
```

#### Design Patterns
1. **MVC Architecture** - Model-View-Controller separation
2. **Blueprint Pattern** - Modular route organization by role (`auth`, `admin`, `driver`, `guest`)
3. **Factory Pattern** - App creation via `create_app()` function
4. **Service Layer Pattern** - Business logic separated from routes
5. **Repository Pattern** - Database operations abstracted in services
6. **Decorator Pattern** - Authentication and authorization via decorators

#### Key Architectural Decisions
- **Session-based auth** for web UI + **JWT tokens** for API
- **WebSocket rooms** organized by hotel_id and user roles
- **Role-based access control (RBAC)** with decorator enforcement
- **Audit trail** automatically logged for all critical operations
- **QR codes** uniquely generated per location (format: `LOC{hotel_id}{sequence:04d}`)
- **Soft deletes** considered for critical entities (via `is_active` flags)
- **Timezone aware** timestamps (defaults to `Europe/Istanbul`)

#### Database Design Principles
- **Foreign key constraints** with CASCADE/SET NULL policies
- **Composite indexes** for frequently filtered combinations (e.g., `hotel_id + status`)
- **ENUM types** for fixed value sets (status, roles)
- **Timestamps** on all tables (`created_at`, `updated_at`)
- **Connection pooling** configured (pool_size=10, max_overflow=20)

### Testing Strategy

#### Test Coverage Goals
- **Unit Tests**: 80%+ coverage target
- **Integration Tests**: All API endpoints
- **E2E Tests**: Critical user flows

#### Test Types
1. **Unit Tests** (pytest)
   - Model validations
   - Service layer business logic
   - Helper functions
   - Serializers/schemas

2. **Integration Tests** (pytest-flask)
   - API endpoint responses
   - Database transactions
   - Authentication flows
   - Permission checks

3. **End-to-End Tests** (Selenium/Playwright)
   - Admin: Login → Create location → Generate QR code
   - Guest: Scan QR → Call buggy → Track status
   - Driver: Login → Accept request → Complete

4. **Performance Tests** (JMeter/Locust)
   - 100+ concurrent users
   - Response time < 200ms (p95)
   - WebSocket connection stability

#### Test Organization
```
tests/
├── unit/          # Model and service tests
├── integration/   # API endpoint tests
└── e2e/          # Browser automation tests
```

#### Test Commands
```bash
# Run all tests with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_models.py

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/
```

### Git Workflow

#### Branching Strategy
- **main** - Production-ready code
- **develop** - Integration branch for features
- **feature/** - New features (`feature/qr-generation`)
- **bugfix/** - Bug fixes (`bugfix/auth-token-expiry`)
- **hotfix/** - Critical production fixes

#### Commit Convention
Follow **Conventional Commits** format:
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples:**
```
feat(admin): add location QR code bulk download
fix(websocket): handle driver disconnect gracefully
docs(api): update authentication endpoint docs
```

#### Pull Request Process
1. Create feature branch from `develop`
2. Make changes with conventional commits
3. Write/update tests
4. Ensure all tests pass
5. Create PR to `develop` with description
6. Code review required before merge
7. Squash merge to keep history clean

## Domain Context

### Hotel Transportation Management
**Buggy Call** operates in the hospitality industry, specifically managing internal vehicle requests within hotel properties. Key domain concepts:

#### Roles & Responsibilities
1. **System Administrator**
   - Hotel management staff
   - Configures locations, buggies, and drivers
   - Monitors operations and generates reports
   - Has full system access

2. **Buggy Driver**
   - Hotel transportation staff
   - Operates assigned buggy vehicle
   - Accepts and completes guest requests
   - Updates real-time location status

3. **Hotel Guest**
   - Anonymous/unauthenticated users
   - Scans QR codes to request transportation
   - Can optionally provide room number
   - Tracks request status in real-time

#### Business Entities
- **Hotel**: Multi-tenant system (each hotel is isolated)
- **Location**: Physical pickup points (lobby, pool, restaurant, etc.)
- **Buggy**: Golf cart-style vehicles with assigned drivers
- **Request**: Transportation service request from guest to driver

#### Request Lifecycle
```
PENDING → ACCEPTED → COMPLETED
   ↓
CANCELLED (by guest or admin)
```

#### Performance Metrics
- **Response Time**: Time from request to driver acceptance
- **Completion Time**: Time from acceptance to arrival
- **Availability Rate**: % of time buggies are available
- **Request Volume**: Requests per hour/day/location

#### Operational Constraints
- Buggies can only accept one active request at a time
- QR codes are location-specific and non-transferable
- Guest requests expire after 15 minutes if not accepted
- Drivers must be online to receive requests
- Multi-hotel support (data isolation by hotel_id)

## Important Constraints

### Technical Constraints
1. **Browser Compatibility**
   - Chrome 90+ (Android, Desktop)
   - Safari 14+ (iOS, macOS)
   - Firefox 88+ (Desktop)
   - Edge 90+ (Desktop)
   - No IE11 support

2. **Mobile Requirements**
   - Camera access required for QR scanning (guests)
   - Notification permissions required (drivers)
   - Minimum screen size: 320px width
   - Touch-optimized UI (44px minimum touch targets)

3. **Network Requirements**
   - WebSocket connection required for real-time features
   - Graceful degradation if WebSocket fails
   - Minimum bandwidth: 1 Mbps recommended
   - 4G/LTE or better for mobile users

4. **Database Constraints**
   - MySQL 8.0+ required for production
   - UTF8MB4 encoding for emoji support
   - InnoDB engine required (ACID compliance)
   - Regular backups required (RPO: 24 hours)

5. **Security Constraints**
   - HTTPS mandatory in production
   - TLS 1.2+ required
   - Password minimum 8 characters
   - JWT tokens expire after 1 hour (access)
   - Session timeout after 24 hours inactivity

### Business Constraints
1. **Multi-tenancy**: Complete data isolation between hotels
2. **Audit Requirements**: All critical operations must be logged
3. **Privacy**: Guest data minimized (optional room numbers only)
4. **Uptime Target**: 99.5% availability during business hours
5. **Response Time SLA**: < 2 seconds for page loads

### Scalability Constraints
- **Current Design**: Single server deployment
- **Concurrent Users**: Tested for 100+ simultaneous connections
- **WebSocket Connections**: Limited by server resources
- **Database**: Connection pool max 30 connections
- **Future**: Ready for horizontal scaling with Redis session store

## External Dependencies

### Required Services
1. **None** - System is fully self-contained
   - No external APIs required
   - No third-party authentication providers
   - No cloud services dependencies

### Optional Enhancements
1. **Redis** (recommended for production)
   - Session storage for multi-server deployments
   - WebSocket message queue
   - Rate limiting counters
   - Cache layer

2. **Email Service** (SMTP)
   - Password reset functionality
   - Admin notifications
   - Weekly reports
   - Currently configured for Gmail SMTP

3. **SMS Service** (future)
   - Driver notifications fallback
   - Guest confirmation messages

### Infrastructure Requirements
1. **Web Server**
   - Nginx/Apache as reverse proxy
   - SSL/TLS termination
   - Static file serving
   - WebSocket proxy support

2. **Database Server**
   - MySQL 8.0+ with InnoDB
   - Automated backups
   - Regular maintenance windows

3. **SSL Certificate**
   - Let's Encrypt (free) or commercial
   - Automatic renewal recommended
   - Required for PWA features and push notifications

### Development Dependencies
- **Git** - Version control
- **Python 3.8+** - Runtime environment
- **Node.js/npm** (optional) - For frontend tooling
- **MySQL Workbench/DBeaver** - Database management
- **Postman/Insomnia** - API testing

### Monitoring & Logging (recommended)
- **Sentry** - Error tracking
- **Application Performance Monitoring** - Optional
- **Uptime monitoring** - Pingdom/UptimeRobot
- **Log aggregation** - ELK stack or similar
