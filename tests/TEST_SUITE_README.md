# Buggy Call System - Test Suite

## 📋 Genel Bakış

Bu test suite, Buggy Call sisteminin tüm kritik fonksiyonlarını test eder. Testler 4 ana kategoriye ayrılmıştır:

1. **Driver Workflow Tests** - Sürücü iş akışları
2. **Guest Workflow Tests** - Misafir iş akışları  
3. **Session Management Tests** - Oturum yönetimi
4. **Integration Tests** - Uçtan uca entegrasyon testleri

## 🚀 Testleri Çalıştırma

### Tüm Testleri Çalıştır
```bash
python tests/run_tests.py
```

### Kategorik Test Çalıştırma
```bash
# Sadece driver testleri
python tests/run_tests.py --driver

# Sadece guest testleri
python tests/run_tests.py --guest

# Sadece session testleri
python tests/run_tests.py --session

# Sadece integration testleri
python tests/run_tests.py --integration
```

### Verbose Mod
```bash
python tests/run_tests.py --verbose
```

### Test Özeti
```bash
python tests/run_tests.py --summary
```

## 📁 Test Dosyaları

### 1. test_driver_workflow.py
**Amaç:** Sürücü iş akışlarını test eder

**Test Senaryoları:**
- ✅ İlk giriş lokasyon kontrolü
- ✅ Lokasyon güncelleme
- ✅ Talep kabul etme workflow
- ✅ Görev tamamlama workflow
- ✅ Race condition koruması
- ✅ Meşgul driver kontrolü

**Örnek Test:**
```python
def test_accept_request_workflow(self, client, setup_test_data):
    """Test complete request acceptance workflow"""
    # Login and set location
    # Accept request
    # Verify buggy status changed to busy
    # Verify request was updated
```

### 2. test_guest_workflow.py
**Amaç:** Misafir iş akışlarını test eder

**Test Senaryoları:**
- ✅ QR kod URL oluşturma
- ✅ Location ID parsing
- ✅ Oda numarası ile talep oluşturma
- ✅ Oda numarası olmadan talep oluşturma
- ✅ Status tracking sayfası
- ✅ Geçersiz lokasyon handling
- ✅ Eksik alan validasyonu

**Örnek Test:**
```python
def test_create_request_with_room_number(self, client, setup_test_data):
    """Test creating request with room number"""
    response = client.post('/api/requests', json={
        'hotel_id': data['hotel'].id,
        'location_id': data['location'].id,
        'guest_name': 'Test Guest',
        'room_number': '101',
        'guest_count': 2
    })
    assert response.status_code == 201
```

### 3. test_session_management.py
**Amaç:** Oturum yönetimini test eder

**Test Senaryoları:**
- ✅ Admin oturum görüntüleme
- ✅ Non-admin erişim engelleme
- ✅ Oturum sonlandırma
- ✅ Geçersiz oturum handling
- ✅ Zaten sonlandırılmış oturum kontrolü
- ✅ Logout cleanup

**Örnek Test:**
```python
def test_admin_can_terminate_session(self, client, setup_test_data):
    """Test that admin can terminate user sessions"""
    # Create driver session
    # Login as admin
    # Terminate driver session
    # Verify session was terminated
```

### 4. test_integration.py
**Amaç:** Uçtan uca entegrasyon testlerini çalıştırır

**Test Senaryoları:**
- ✅ Tam guest-to-driver workflow
- ✅ Multi-driver race condition
- ✅ Admin session management workflow
- ✅ Real-time status tracking

**Örnek Test:**
```python
def test_complete_guest_to_driver_workflow(self, client, setup_complete_scenario):
    """Test complete workflow from guest request to driver completion"""
    # Step 1: Guest creates request
    # Step 2: Driver accepts request
    # Step 3: Driver completes request
    # Step 4: Driver sets new location
```

## 🔧 Test Configuration (conftest.py)

Test ortamı yapılandırması ve fixtures:

### Fixtures
- `app` - Test uygulaması
- `client` - Test client
- `db_session` - Database session
- `setup_test_data` - Test verileri

### Örnek Fixture Kullanımı
```python
@pytest.fixture
def setup_test_data(self, app, db_session):
    """Setup test data for tests"""
    hotel = Hotel(name="Test Hotel", ...)
    db_session.add(hotel)
    db_session.commit()
    return {'hotel': hotel}
```

## 📊 Test Kapsamı

### API Endpoints
- ✅ `/api/driver/set-location` - Sürücü lokasyon güncelleme
- ✅ `/api/driver/accept-request/<id>` - Talep kabul etme
- ✅ `/api/driver/complete-request/<id>` - Talep tamamlama
- ✅ `/api/admin/sessions` - Aktif oturumları görüntüleme
- ✅ `/api/admin/sessions/<id>/terminate` - Oturum sonlandırma
- ✅ `/api/requests` - Talep oluşturma
- ✅ `/api/requests/<id>` - Talep durumu sorgulama

### Business Logic
- ✅ Request acceptance workflow
- ✅ Request completion workflow
- ✅ Race condition prevention
- ✅ Buggy status management
- ✅ Location tracking
- ✅ Session management

### Security
- ✅ Authorization checks
- ✅ Session validation
- ✅ Admin-only endpoints
- ✅ Single device enforcement

### User Experience
- ✅ QR code workflow
- ✅ Real-time status updates
- ✅ Location modal flow
- ✅ Error handling

## 🎯 Test Metrikleri

### Toplam Test Sayısı
- **Driver Workflow:** 6 test
- **Guest Workflow:** 8 test
- **Session Management:** 6 test
- **Integration:** 4 test
- **TOPLAM:** 24+ test senaryosu

### Kapsanan Modüller
- ✅ Authentication & Authorization
- ✅ Request Management
- ✅ Buggy Management
- ✅ Location Management
- ✅ Session Management
- ✅ QR Code Service

## 🐛 Hata Ayıklama

### Test Başarısız Olursa

1. **Verbose mod ile çalıştır:**
```bash
python tests/run_tests.py --verbose
```

2. **Tek bir test dosyası çalıştır:**
```bash
python -m pytest tests/test_driver_workflow.py -v
```

3. **Belirli bir test çalıştır:**
```bash
python -m pytest tests/test_driver_workflow.py::TestDriverWorkflow::test_accept_request_workflow -v
```

4. **Database durumunu kontrol et:**
```python
# Test içinde
print(f"Buggy status: {buggy.status}")
print(f"Request status: {request.status}")
```

## 📝 Yeni Test Ekleme

### Adımlar:
1. İlgili test dosyasını aç
2. Yeni test metodu ekle
3. `setup_test_data` fixture'ını kullan
4. Assert'ler ile doğrula
5. Testi çalıştır

### Örnek:
```python
def test_new_feature(self, client, setup_test_data):
    """Test new feature description"""
    data = setup_test_data
    
    # Arrange
    # ... setup code
    
    # Act
    response = client.post('/api/endpoint', json={...})
    
    # Assert
    assert response.status_code == 200
    result = response.get_json()
    assert result['success'] is True
```

## ✅ Test Checklist

Yeni özellik eklerken kontrol edilmesi gerekenler:

- [ ] Happy path test edildi mi?
- [ ] Error cases test edildi mi?
- [ ] Authorization kontrolleri test edildi mi?
- [ ] Race conditions kontrol edildi mi?
- [ ] Database state doğru mu?
- [ ] Response format doğru mu?
- [ ] Status codes doğru mu?

## 🔗 İlgili Dökümanlar

- [API Documentation](../docs/API.md)
- [Database Schema](../docs/DATABASE.md)
- [Architecture](../docs/ARCHITECTURE.md)

## 📞 Destek

Test ile ilgili sorularınız için:
- GitHub Issues
- Development Team

---

**Son Güncelleme:** 2024
**Test Framework:** pytest
**Python Version:** 3.8+
