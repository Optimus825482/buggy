# Railway Environment Variables

Bu dosya Railway deployment için gerekli environment variable'ları listeler.

## Zorunlu Variables

### Database (Otomatik - Railway MySQL Service)
```
MYSQL_PUBLIC_URL=mysql://user:password@host:port/railway
```
**Not:** Bu Railway MySQL service tarafından otomatik olarak sağlanır.

### Application Security
```
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
```
**Önemli:** Bu değerleri mutlaka değiştirin! Güçlü, rastgele string'ler kullanın.

### Flask Environment
```
FLASK_ENV=production
```

## Opsiyonel Variables

### Admin User Configuration
```
ADMIN_PASSWORD=518518
ADMIN_EMAIL=admin@buggycall.com
```
**Default:** Password: `518518`, Email: `admin@buggycall.com`

### Hotel Configuration
```
HOTEL_NAME=Buggy Call Hotel
HOTEL_CODE=HOTEL01
INITIAL_BUGGY_COUNT=5
```
**Default:** Hotel name: "Buggy Call Hotel", Code: "HOTEL01", 5 buggies

### CORS Configurat