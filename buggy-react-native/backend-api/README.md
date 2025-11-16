# Shuttle Call Backend API

Modern shuttle çağırma sistemi için FastAPI tabanlı backend servisi.

## 🚀 Özellikler

- ⚡ FastAPI ile yüksek performanslı REST API
- 🗄️ PostgreSQL veritabanı (SQLAlchemy ORM)
- 🔐 JWT tabanlı authentication
- 📱 Firebase Cloud Messaging (FCM) push notifications
- 🔄 WebSocket ile real-time updates
- 🛡️ Rate limiting ve güvenlik önlemleri
- 📊 Connection pooling ve retry mekanizması
- 📝 Otomatik API dokümantasyonu (Swagger/ReDoc)

## 📋 Gereksinimler

- Python 3.10+
- PostgreSQL 14+
- Firebase service account credentials

## 🔧 Kurulum

### 1. Virtual Environment Oluştur

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Dependencies Yükle

```bash
pip install -r requirements.txt
```

### 3. Environment Variables Ayarla

```bash
# .env.example dosyasını kopyala
cp .env.example .env

# .env dosyasını düzenle ve değerleri doldur
```

**Önemli Environment Variables:**

- `DATABASE_URL`: PostgreSQL bağlantı URL'i
- `JWT_SECRET_KEY`: JWT token için secret key (min 32 karakter)
- `FIREBASE_SERVICE_ACCOUNT_BASE64`: Firebase service account JSON (base64 encoded)

### 4. PostgreSQL Database Oluştur

```sql
CREATE DATABASE shuttle_call_db;
CREATE USER shuttle_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE shuttle_call_db TO shuttle_user;
```

### 5. Database Migration (İleride)

```bash
# Alembic ile migration çalıştır
alembic upgrade head
```

## 🏃 Çalıştırma

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Dokümantasyonu

Uygulama çalıştıktan sonra:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🏗️ Proje Yapısı

```
backend-api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI uygulaması
│   ├── config.py         # Environment configuration
│   ├── database.py       # Database bağlantı yönetimi
│   ├── models/           # SQLAlchemy models (ileride)
│   ├── schemas/          # Pydantic schemas (ileride)
│   ├── api/              # API routes (ileride)
│   ├── services/         # Business logic (ileride)
│   └── core/             # Core utilities (ileride)
├── alembic/              # Database migrations (ileride)
├── tests/                # Test files (ileride)
├── .env                  # Environment variables (git'e ekleme!)
├── .env.example          # Environment variables template
├── requirements.txt      # Python dependencies
└── README.md
```

## 🔒 Güvenlik

- JWT token ile authentication
- Bcrypt ile password hashing
- Rate limiting (100 req/min)
- CORS yapılandırması
- SQL injection koruması (ORM)
- Input validation (Pydantic)

## 🧪 Testing (İleride)

```bash
pytest tests/
```

## 📝 Notlar

- `.env` dosyasını asla git'e commit etmeyin
- Production'da güçlü secret key'ler kullanın
- Database backup'larını düzenli alın
- Log dosyalarını izleyin

## 🤝 Katkıda Bulunma

1. Feature branch oluştur
2. Değişiklikleri commit et
3. Pull request aç

## 📄 Lisans

Özel proje - Tüm hakları saklıdır
