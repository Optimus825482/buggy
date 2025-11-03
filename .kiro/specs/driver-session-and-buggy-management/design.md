# Design Document

## Overview

Bu tasarım, sürücü oturum yönetimini basitleştirmek ve buggy tanımlama ekranına sürücü yönetimi özelliklerini eklemek için gerekli değişiklikleri tanımlar. Mevcut sistemde bulunan "çevrimdışı durumuna alma switch'i" kaldırılacak ve oturum kapatma işlemleri tamamen otomatik hale gelecektir. Ayrıca admin panelinde buggy'lere sürücü atama ve transfer işlemleri için yeni arayüzler eklenecektir.

## Architecture

### Affected Components

1. **Frontend (Templates)**
   - `templates/driver/dashboard.html` - Offline switch kaldırılacak
   - `templates/admin/buggies.html` - Sürücü atama ve transfer UI eklenecek

2. **Backend (API Routes)**
   - `app/routes/api.py` - Yeni endpoint'ler eklenecek:
     - `POST /api/admin/assign-driver-to-buggy` - Buggy'ye sürücü atama
     - `POST /api/admin/transfer-driver` - Sürücü transfer işlemi
   - Mevcut endpoint güncellenecek:
     - `POST /api/admin/close-driver-session/<driver_id>` - Zaten mevcut, değişiklik yok

3. **Backend (Auth Routes)**
   - `app/routes/auth.py` - Login işleminde oturum kapatma mantığı zaten mevcut

4. **Models**
   - `app/models/buggy.py` - Değişiklik yok (driver_id zaten var)
   - `app/models/session.py` - Değişiklik yok (is_active, revoked_at zaten var)

5. **Services**
   - `app/services/audit_service.py` - Yeni audit log tipleri eklenecek

## Components and Interfaces

### 1. Frontend Changes

#### Driver Dashboard - Offline Switch Removal

**Current State:**
- Sürücü dashboard'unda "Çevrimdışı Ol" toggle switch'i var
- Sürücü manuel olarak kendini offline yapabiliyor

**New State:**
- Toggle switch tamamen kaldırılacak
- Sadece "Çıkış Yap" butonu kalacak
- Oturum kapatma otomatik olacak (logout, başka sürücü login, admin kapatır)

**Implementation:**
```html
<!-- REMOVE THIS -->
<div class="offline-toggle">
  <label class="switch">
    <input type="checkbox" id="offline-switch">
    <span class="slider"></span>
  </label>
  <span>Çevrimdışı Ol</span>
</div>

<!-- KEEP ONLY THIS -->
<button onclick="logout()" class="btn btn-danger">
  <i class="fas fa-sign-out-alt"></i> Çıkış Yap
</button>
```

#### Admin Buggy Management - New Features

**Current State:**
- Buggy listesi gösteriliyor
- Sadece buggy bilgileri düzenlenebiliyor

**New State:**
- Her buggy için "Sürücü Ata" butonu
- Her sürücü için "Transfer Et" butonu
- Modal dialog'lar ile sürücü seçimi

**UI Components:**

1. **Buggy List Table Enhancement:**
```html
<table class="table">
  <thead>
    <tr>
      <th>Buggy Kodu</th>
      <th>Model</th>
      <th>Plaka</th>
      <th>Atanmış Sürücü</th>
      <th>Durum</th>
      <th>İşlemler</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>BUGGY-01</td>
      <td>Golf Cart</td>
      <td>34 ABC 123</td>
      <td>
        <span class="driver-name">Ahmet Yılmaz</span>
        <span class="badge badge-success">Aktif</span>
      </td>
      <td><span class="badge badge-info">MÜSAİT</span></td>
      <td>
        <button onclick="showAssignDriverModal(1)" class="btn btn-sm btn-primary">
          <i class="fas fa-user-plus"></i> Sürücü Ata
        </button>
        <button onclick="showTransferDriverModal(1)" class="btn btn-sm btn-warning">
          <i class="fas fa-exchange-alt"></i> Transfer Et
        </button>
      </td>
    </tr>
  </tbody>
</table>
```

2. **Assign Driver Modal:**
```html
<div id="assignDriverModal" class="modal">
  <div class="modal-content">
    <h3>Buggy'ye Sürücü Ata</h3>
    <p>Buggy: <strong id="assign-buggy-code"></strong></p>
    
    <label>Sürücü Seç:</label>
    <select id="assign-driver-select" class="form-control">
      <option value="">Sürücü Seçin</option>
      <!-- Atanmamış sürücüler listelenecek -->
    </select>
    
    <div class="modal-actions">
      <button onclick="assignDriver()" class="btn btn-primary">Ata</button>
      <button onclick="closeModal()" class="btn btn-secondary">İptal</button>
    </div>
  </div>
</div>
```

3. **Transfer Driver Modal:**
```html
<div id="transferDriverModal" class="modal">
  <div class="modal-content">
    <h3>Sürücü Transfer Et</h3>
    <p>Mevcut Sürücü: <strong id="transfer-driver-name"></strong></p>
    <p>Mevcut Buggy: <strong id="transfer-source-buggy"></strong></p>
    
    <label>Hedef Buggy:</label>
    <select id="transfer-target-buggy" class="form-control">
      <option value="">Buggy Seçin</option>
      <!-- Diğer buggy'ler listelenecek -->
    </select>
    
    <div class="alert alert-warning">
      <i class="fas fa-exclamation-triangle"></i>
      Aktif oturum varsa kapatılacak ve her iki buggy offline olacak.
    </div>
    
    <div class="modal-actions">
      <button onclick="transferDriver()" class="btn btn-warning">Transfer Et</button>
      <button onclick="closeModal()" class="btn btn-secondary">İptal</button>
    </div>
  </div>
</div>
```

### 2. Backend API Endpoints

#### New Endpoint: Assign Driver to Buggy

```python
@api_bp.route('/admin/assign-driver-to-buggy', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
@require_role('admin')
def assign_driver_to_buggy():
    """
    Assign a driver to a buggy
    
    Request Body:
    {
        "buggy_id": 1,
        "driver_id": 5
    }
    
    Response:
    {
        "success": true,
        "message": "Sürücü başarıyla atandı",
        "buggy": {...}
    }
    """
```

**Logic:**
1. Validate admin role
2. Get buggy and driver from database
3. Check if driver already assigned to another buggy (optional - allow multiple assignments)
4. Update `buggy.driver_id = driver_id`
5. Log action in audit trail
6. Return success response

#### New Endpoint: Transfer Driver

```python
@api_bp.route('/admin/transfer-driver', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
@require_role('admin')
def transfer_driver():
    """
    Transfer a driver from one buggy to another
    
    Request Body:
    {
        "driver_id": 5,
        "source_buggy_id": 1,
        "target_buggy_id": 2
    }
    
    Response:
    {
        "success": true,
        "message": "Sürücü başarıyla transfer edildi",
        "source_buggy": {...},
        "target_buggy": {...}
    }
    """
```

**Logic:**
1. Validate admin role
2. Get driver, source buggy, target buggy
3. Check if driver has active session
4. If active session exists:
   - Terminate session (set `is_active = False`, `revoked_at = now()`)
   - Set source buggy to OFFLINE
   - Set target buggy to OFFLINE
5. Update source buggy: `driver_id = None`
6. Update target buggy: `driver_id = driver_id`
7. Log transfer in audit trail with both buggy IDs
8. Emit WebSocket event if needed
9. Return success response

#### Existing Endpoint: Close Driver Session (No Changes)

```python
@api_bp.route('/admin/close-driver-session/<int:driver_id>', methods=['POST'])
@limiter.limit("20 per minute")
@require_login
@require_role('admin')
def close_driver_session(driver_id):
    """Already implemented - no changes needed"""
```

### 3. Session Management Logic

#### Automatic Session Termination Scenarios

**Scenario 1: Driver Logout**
- Location: `app/routes/auth.py` - `logout()` function
- Current implementation already handles this:
  ```python
  if user.role == UserRole.DRIVER and user.buggy:
      user.buggy.status = BuggyStatus.OFFLINE
  session.clear()
  ```
- No changes needed

**Scenario 2: Another Driver Logs In to Same Buggy**
- Location: `app/routes/auth.py` - `login()` function
- Current implementation already handles this:
  ```python
  # Close other active sessions for this buggy
  other_sessions = SessionModel.query.filter(
      SessionModel.user_id != user.id,
      SessionModel.is_active == True
  ).join(SystemUser).filter(
      SystemUser.buggy_id == user.buggy_id
  ).all()
  
  for other_session in other_sessions:
      other_session.is_active = False
      other_session.revoked_at = datetime.utcnow()
  ```
- No changes needed

**Scenario 3: Admin Terminates Session**
- Location: `app/routes/api.py` - `close_driver_session()` function
- Already implemented
- No changes needed

### 4. Data Models

#### Buggy Model (No Changes)
```python
class Buggy(db.Model):
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('system_users.id'))  # Already exists
    status = Column(Enum(BuggyStatus))  # AVAILABLE, BUSY, OFFLINE
    # ... other fields
```

#### Session Model (No Changes)
```python
class Session(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('system_users.id'))
    is_active = Column(Boolean, default=True)  # Already exists
    revoked_at = Column(DateTime)  # Already exists
    # ... other fields
```

#### SystemUser Model (No Changes)
```python
class SystemUser(db.Model):
    id = Column(Integer, primary_key=True)
    role = Column(Enum(UserRole))  # ADMIN, DRIVER
    buggy = relationship('Buggy', back_populates='driver', uselist=False)
    # ... other fields
```

## Error Handling

### Frontend Error Handling

1. **Assign Driver Errors:**
   - Driver already assigned to another buggy → Show warning, allow override
   - Buggy not found → Show error message
   - Network error → Show retry option

2. **Transfer Driver Errors:**
   - Target buggy has active driver → Show error, prevent transfer
   - Driver not found → Show error message
   - Network error → Show retry option

### Backend Error Handling

1. **Validation Errors (400):**
   - Missing required fields
   - Invalid buggy_id or driver_id
   - Target buggy already has active driver

2. **Authorization Errors (403):**
   - Non-admin trying to assign/transfer drivers
   - Driver trying to access admin endpoints

3. **Not Found Errors (404):**
   - Buggy not found
   - Driver not found

4. **Server Errors (500):**
   - Database transaction failures
   - Audit log failures (should not block main operation)

## Testing Strategy

### Unit Tests

1. **API Endpoint Tests:**
   - Test assign driver endpoint with valid data
   - Test assign driver with invalid buggy_id
   - Test assign driver with non-admin user
   - Test transfer driver endpoint with valid data
   - Test transfer driver with active session
   - Test transfer driver to buggy with active driver

2. **Session Management Tests:**
   - Test automatic session termination on logout
   - Test automatic session termination on another driver login
   - Test admin session termination

### Integration Tests

1. **End-to-End Scenarios:**
   - Admin assigns driver to buggy → Driver logs in → Verify buggy status
   - Driver A logs in → Driver B logs in to same buggy → Verify A's session closed
   - Admin transfers driver → Verify both buggies updated
   - Admin closes driver session → Verify buggy offline

### Manual Testing

1. **UI Testing:**
   - Verify offline switch removed from driver dashboard
   - Verify assign driver modal works correctly
   - Verify transfer driver modal works correctly
   - Verify real-time updates via WebSocket

2. **Audit Trail Testing:**
   - Verify all actions logged correctly
   - Verify audit logs contain all required information

## Security Considerations

1. **Authorization:**
   - Only admins can assign/transfer drivers
   - Only admins can close driver sessions
   - Drivers can only logout themselves

2. **Session Security:**
   - Session tokens remain secure
   - Terminated sessions cannot be reused
   - WebSocket events only sent to authorized rooms

3. **Audit Trail:**
   - All driver assignments logged
   - All transfers logged with source and target
   - All session terminations logged with reason

## Migration Plan

### Phase 1: Backend Implementation
1. Add new API endpoints for assign and transfer
2. Add audit log types
3. Test endpoints thoroughly

### Phase 2: Frontend Implementation
1. Remove offline switch from driver dashboard
2. Add assign driver modal to admin buggy management
3. Add transfer driver modal to admin buggy management
4. Add JavaScript functions for API calls

### Phase 3: Testing
1. Run unit tests
2. Run integration tests
3. Perform manual testing
4. Verify audit trail

### Phase 4: Deployment
1. Deploy backend changes
2. Deploy frontend changes
3. Monitor for errors
4. Verify all features working

## Rollback Plan

If issues occur:
1. Revert frontend changes (restore offline switch temporarily)
2. Disable new API endpoints
3. Investigate and fix issues
4. Redeploy with fixes

## Performance Considerations

1. **Database Queries:**
   - Use indexes on `buggy.driver_id` (already exists)
   - Use indexes on `session.is_active` (already exists)
   - Minimize N+1 queries with eager loading

2. **WebSocket Events:**
   - Only emit to relevant rooms
   - Batch updates if multiple changes

3. **Audit Logging:**
   - Async logging to avoid blocking main operations
   - Batch audit logs if needed

## Open Questions

1. **Multiple Driver Assignment:**
   - Should we allow multiple drivers assigned to same buggy? (Answer: Yes, but only one active at a time)
   - Current design supports this

2. **Transfer Confirmation:**
   - Should we require confirmation from driver before transfer? (Answer: No, admin decision is final)

3. **Notification:**
   - Should driver receive notification when transferred? (Answer: Optional, can be added later)
