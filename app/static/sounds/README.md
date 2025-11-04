# Bildirim Sesleri

Bu klasör push bildirim sesleri için kullanılır.

## Ses Dosyası Ekleme

1. **notification.mp3** - Misafir talebi bildirimi için kullanılır
   - Önerilen süre: 1-3 saniye
   - Format: MP3, OGG veya WAV
   - Boyut: Maksimum 100KB (hızlı yükleme için)

## Ses Dosyası Kaynakları

Ücretsiz bildirim sesleri için:
- https://notificationsounds.com/
- https://freesound.org/
- https://mixkit.co/free-sound-effects/notification/

## Örnek Kullanım

```python
# Python'da bildirim gönderirken
NotificationService.send_notification(
    subscription_info=driver.push_subscription,
    title="🔔 Yeni Buggy Talebi",
    body="Lokasyon - Oda: 101",
    sound="/static/sounds/notification.mp3",
    vibrate=[200, 100, 200, 100, 200]
)
```

## Not

- Ses dosyası eklenmezse bildirim sessiz gönderilir
- Tarayıcı autoplay politikası nedeniyle ilk bildirimde ses çalmayabilir
- Kullanıcı etkileşiminden sonra sesler düzgün çalışır
