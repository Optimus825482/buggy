# Requirements Document

## Introduction

Login sayfasında kullanıcı hatalı giriş yaptığında (yanlış kullanıcı adı veya şifre), hata mesajı toast bildirimi yerine modal dialog olarak gösterilecektir. Bu, kullanıcının hatayı daha net görmesini ve anlamasını sağlayacaktır.

## Glossary

- **Login System**: Kullanıcı kimlik doğrulama sistemi
- **Error Modal**: Hata mesajlarını gösteren modal dialog penceresi
- **Authentication Failure**: Kullanıcı adı veya şifre hatasından kaynaklanan giriş başarısızlığı

## Requirements

### Requirement 1

**User Story:** Kullanıcı olarak, hatalı giriş yaptığımda hatayı açıkça görebilmek için modal dialog ile bilgilendirilmek istiyorum.

#### Acceptance Criteria

1. WHEN kullanıcı yanlış kullanıcı adı veya şifre girdiğinde, THE Login System SHALL hata mesajını modal dialog içinde gösterecek
2. THE Error Modal SHALL hata mesajını Türkçe olarak gösterecek
3. THE Error Modal SHALL kullanıcının modalı kapatabilmesi için bir "Tamam" veya "Kapat" butonu içerecek
4. WHEN kullanıcı modal kapatma butonuna tıkladığında, THE Error Modal SHALL kapanacak ve kullanıcı login formuna geri dönecek
5. THE Error Modal SHALL ekranın ortasında, arka planı karartılmış (overlay) şekilde görünecek

### Requirement 2

**User Story:** Kullanıcı olarak, modal açıkken form alanlarına erişememeli ve sadece modalı kapatabilmeliyim.

#### Acceptance Criteria

1. WHILE Error Modal açıkken, THE Login System SHALL arka plandaki form elemanlarının tıklanmasını engelleyecek
2. WHEN kullanıcı modal dışına tıkladığında, THE Error Modal SHALL kapanacak
3. WHEN kullanıcı ESC tuşuna bastığında, THE Error Modal SHALL kapanacak
4. THE Error Modal SHALL açılırken ve kapanırken yumuşak animasyon (fade-in/fade-out) gösterecek

### Requirement 3

**User Story:** Geliştirici olarak, modal bileşeninin yeniden kullanılabilir olmasını istiyorum.

#### Acceptance Criteria

1. THE Error Modal SHALL base.html içinde global bir bileşen olarak tanımlanacak
2. THE Error Modal SHALL JavaScript fonksiyonu ile dinamik olarak açılıp kapatılabilecek
3. THE Error Modal SHALL farklı hata mesajlarını parametre olarak alabilecek
4. THE Error Modal SHALL mevcut BuggyCall.Utils namespace'i içinde tanımlanacak
