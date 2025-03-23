# TOP INVEST - FRONTEND INTEGRATSIYA DOKUMENTATSIYASI

## Umumiy ma'lumot
Ushbu hujjat Top Invest backend API bilan integratsiya qilish uchun frontend dasturchilar uchun to'liq ma'lumotlarni o'z ichiga oladi. Bu yerda autentifikatsiya, mavjud API endpointlar, ma'lumotlar strukturasi va API so'rovlari hamda javoblari misollari keltirilgan.

## Asosiy URL
- Rivojlantirish muhiti: `http://127.0.0.1:8000/`
- Ishlab chiqarish muhiti: `https://your-production-domain.com/` (keyinchalik yangilanadi)

## Autentifikatsiya
API JWT (JSON Web Token) autentifikatsiyasidan foydalanadi.

### Autentifikatsiya endpointlari

#### 1. Token olish
- **URL**: `/api/token/`
- **Metod**: `POST`
- **So'rov tanasi**:
```json
{
  "username": "foydalanuvchi_nomi",
  "password": "parol"
}
```
- **Javob**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### 2. Tokenni yangilash
- **URL**: `/api/token/refresh/`
- **Metod**: `POST`
- **So'rov tanasi**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
- **Javob**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Autentifikatsiyadan foydalanish
Autentifikatsiya talab qiladigan so'rovlar uchun JWT tokenni Authorization sarlavhasiga qo'shing:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## API Endpointlar

### Foydalanuvchilar

#### 1. Foydalanuvchi profilini olish
- **URL**: `/users/api/profile/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi
- **Javob**:
```json
{
  "id": 1,
  "user_id": 123456789,
  "telegram_user_id": 123456789,
  "first_name": "Anvar",
  "last_name": "Qodirov",
  "phone_number": "+998901234567",
  "is_admin": false,
  "is_blocked": false,
  "is_subscribed": true,
  "referral_code": "uuid-string",
  "created_at": "2025-03-16T12:00:00Z",
  "updated_at": "2025-03-16T12:00:00Z"
}
```

### To'lovlar

#### 1. Barcha to'lovlarni ko'rish
- **URL**: `/payments/api/payments/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**:
```json
[
  {
    "id": 1,
    "user": {
      "id": 1,
      "user_id": 123456789,
      "first_name": "Anvar",
      "last_name": "Qodirov"
    },
    "amount": "100000.00",
    "payment_method": "uzcard",
    "payment_method_display": "💳 Uzcard",
    "status": "pending_approval",
    "status_display": "Kutilmoqda",
    "screenshot": "https://example.com/screenshots/payment1.jpg",
    "created_at": "2025-03-16T12:00:00Z",
    "updated_at": "2025-03-16T12:00:00Z",
    "updated_admin": null
  }
]
```

#### 2. To'lov yaratish
- **URL**: `/payments/api/payments/`
- **Metod**: `POST`
- **Autentifikatsiya**: Talab qilinadi
- **So'rov tanasi**:
```json
{
  "amount": "100000.00",
  "payment_method": "uzcard",
  "screenshot": "base64_kodlangan_rasm_yoki_url"
}
```
- **Javob**: Yuqoridagi to'lov obyekti bilan bir xil

#### 3. To'lov tafsilotlarini olish
- **URL**: `/payments/api/payments/{id}/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi
- **Javob**: Yuqoridagi to'lov obyekti bilan bir xil

#### 4. To'lovni tasdiqlash
- **URL**: `/payments/api/approve/{payment_id}/`
- **Metod**: `POST`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**:
```json
{
  "success": true,
  "message": "To'lov muvaffaqiyatli tasdiqlandi",
  "payment": {
    "id": 1,
    "status": "approved",
    "status_display": "Tasdiqlangan",
    "updated_at": "2025-03-16T12:30:00Z",
    "updated_admin": 1
  }
}
```

#### 5. To'lovni rad etish
- **URL**: `/payments/api/reject/{payment_id}/`
- **Metod**: `POST`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**:
```json
{
  "success": true,
  "message": "To'lov rad etildi",
  "payment": {
    "id": 1,
    "status": "declined",
    "status_display": "Rad etilgan",
    "updated_at": "2025-03-16T12:30:00Z",
    "updated_admin": 1
  }
}
```

#### 6. Kutilayotgan to'lovlarni olish
- **URL**: `/payments/api/pending/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**: Kutilayotgan to'lovlar ro'yxati

#### 7. Tasdiqlangan to'lovlarni olish
- **URL**: `/payments/api/approved/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**: Tasdiqlangan to'lovlar ro'yxati

#### 8. Rad etilgan to'lovlarni olish
- **URL**: `/payments/api/declined/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**: Rad etilgan to'lovlar ro'yxati

### Obunalar

#### 1. Obuna rejalarini ko'rish
- **URL**: `/subscriptions/api/plans/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinmaydi
- **Javob**:
```json
[
  {
    "id": 1,
    "title": "Oddiy reja",
    "price": "50000.00",
    "duration_days": 30,
    "is_active": true,
    "created_at": "2025-03-16T12:00:00Z",
    "updated_at": "2025-03-16T12:00:00Z"
  }
]
```

#### 2. Foydalanuvchi obunalarini olish
- **URL**: `/subscriptions/api/user-subscriptions/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi
- **Javob**:
```json
[
  {
    "id": 1,
    "user": {
      "id": 1,
      "first_name": "Anvar",
      "last_name": "Qodirov"
    },
    "subscription_plan": {
      "id": 1,
      "title": "Oddiy reja",
      "price": "50000.00",
      "duration_days": 30
    },
    "amount_paid": "50000.00",
    "status": "active",
    "created_at": "2025-03-16T12:00:00Z",
    "expires_at": "2025-04-15T12:00:00Z"
  }
]
```

### Signallar

#### 1. Barcha signallarni ko'rish
- **URL**: `/signals/api/signals/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi (Faqat obuna bo'lgan foydalanuvchilar)
- **Javob**:
```json
[
  {
    "id": 1,
    "instrument": "BTC/USDT",
    "order_type": "buy",
    "target_position": "45000.00",
    "stop_loss": "44000.00",
    "take_profit": "48000.00",
    "is_posted": true,
    "created_at": "2025-03-16T12:00:00Z"
  }
]
```

### Dashboard (Admin)

#### 1. Dashboard statistikasini olish
- **URL**: `/dashboard/api/statistics/`
- **Metod**: `GET`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **Javob**:
```json
{
  "total_users": 100,
  "subscribed_users": 50,
  "active_users": 80,
  "daily_stats": {
    "labels": ["2025-03-10", "2025-03-11", "2025-03-12", "2025-03-13", "2025-03-14", "2025-03-15", "2025-03-16"],
    "data": [5, 7, 3, 10, 8, 12, 6]
  },
  "top_referrers": [
    {
      "first_name": "Anvar",
      "last_name": "Qodirov",
      "ref_count": 15
    }
  ]
}
```

#### 2. Ommaviy xabar yuborish
- **URL**: `/dashboard/api/broadcast/`
- **Metod**: `POST`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **So'rov tanasi**:
```json
{
  "recipient_type": "all", // Variantlar: "all" (barchaga), "subscribed" (obunachilarga), "active" (faol foydalanuvchilarga)
  "message": "Assalomu alaykum, bu ommaviy xabar!"
}
```
- **Javob**:
```json
{
  "success": true,
  "message": "Xabar muvaffaqiyatli yuborildi",
  "success_count": 95,
  "error_count": 5
}
```

## Ma'lumotlar modellari

### Foydalanuvchi
```json
{
  "id": 1,
  "user_id": 123456789,
  "telegram_user_id": 123456789,
  "image_url": "https://example.com/profile.jpg",
  "first_name": "Anvar",
  "last_name": "Qodirov",
  "phone_number": "+998901234567",
  "is_admin": false,
  "is_blocked": false,
  "is_subscribed": true,
  "referral_code": "uuid-string",
  "referred_by": null,
  "temp_data": {},
  "created_at": "2025-03-16T12:00:00Z",
  "updated_at": "2025-03-16T12:00:00Z"
}
```

### To'lov
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "user_id": 123456789,
    "first_name": "Anvar",
    "last_name": "Qodirov"
  },
  "amount": "100000.00",
  "payment_method": "uzcard", // Variantlar: "uzcard", "humo", "visa", "mastercard"
  "payment_method_display": "💳 Uzcard",
  "status": "pending_approval", // Variantlar: "pending_approval", "approved", "declined", "error"
  "status_display": "Kutilmoqda",
  "screenshot": "https://example.com/screenshots/payment1.jpg",
  "created_at": "2025-03-16T12:00:00Z",
  "updated_at": "2025-03-16T12:00:00Z",
  "updated_admin": null
}
```

### Obuna rejasi
```json
{
  "id": 1,
  "title": "Oddiy reja",
  "price": "50000.00",
  "duration_days": 30,
  "is_active": true,
  "created_at": "2025-03-16T12:00:00Z",
  "updated_at": "2025-03-16T12:00:00Z"
}
```

### Obuna
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "first_name": "Anvar",
    "last_name": "Qodirov"
  },
  "subscription_plan": {
    "id": 1,
    "title": "Oddiy reja",
    "price": "50000.00",
    "duration_days": 30
  },
  "amount_paid": "50000.00",
  "status": "active", // Variantlar: "pending", "waiting_admin", "active", "expired", "rejected"
  "payment_screenshot": "https://example.com/screenshots/payment1.jpg",
  "created_at": "2025-03-16T12:00:00Z",
  "expires_at": "2025-04-15T12:00:00Z"
}
```

### Signal
```json
{
  "id": 1,
  "instrument": "BTC/USDT",
  "order_type": "buy", // Variantlar: "buy" (sotib olish), "sell" (sotish)
  "target_position": "45000.00",
  "stop_loss": "44000.00",
  "take_profit": "48000.00",
  "is_posted": true,
  "created_at": "2025-03-16T12:00:00Z"
}
```

## Xatolarni boshqarish

API standart HTTP status kodlarini qaytaradi:

- `200 OK`: So'rov muvaffaqiyatli bajarildi
- `201 Created`: Resurs muvaffaqiyatli yaratildi
- `400 Bad Request`: Noto'g'ri so'rov parametrlari
- `401 Unauthorized`: Autentifikatsiya talab qilinadi yoki muvaffaqiyatsiz
- `403 Forbidden`: Ruxsat berilmagan
- `404 Not Found`: Resurs topilmadi
- `500 Internal Server Error`: Server xatosi

Xato javoblari quyidagi formatda bo'ladi:
```json
{
  "error": true,
  "message": "Xato tavsifi",
  "details": {} // Qo'shimcha ma'lumotlar (ixtiyoriy)
}
```

## Sahifalash

Ro'yxat endpointlari quyidagi so'rov parametrlari bilan sahifalashni qo'llab-quvvatlaydi:
- `page`: Sahifa raqami (standart: 1)
- `page_size`: Har bir sahifadagi elementlar soni (standart: 10, maksimal: 100)

Sahifalangan javoblar quyidagi formatda bo'ladi:
```json
{
  "count": 100,
  "next": "http://example.com/api/endpoint/?page=2",
  "previous": null,
  "results": [
    // Elementlar massivi
  ]
}
```

## Filtrlash va saralash

Ko'pgina ro'yxat endpointlari filtrlash va saralashni qo'llab-quvvatlaydi:

### Filtrlash
Natijalarni filtrlash uchun so'rov parametrlaridan foydalaning:
```
/payments/api/payments/?status=pending_approval
/signals/api/signals/?order_type=buy
```

### Saralash
Natijalarni saralash uchun `ordering` parametridan foydalaning:
```
/payments/api/payments/?ordering=-created_at
/signals/api/signals/?ordering=instrument
```
Kamayish tartibida saralash uchun `-` prefiksini qo'shing.

## Webhook integratsiyasi

Tizim muhim hodisalar haqida webhook xabarnomalarini qo'llab-quvvatlaydi:

### To'lov holati o'zgarishi
- **URL**: Admin sozlamalarida sozlanadi
- **Metod**: `POST`
- **So'rov tanasi**:
```json
{
  "event": "payment_status_changed",
  "payment_id": 1,
  "old_status": "pending_approval",
  "new_status": "approved",
  "timestamp": "2025-03-16T12:30:00Z"
}
```

### Obuna holati o'zgarishi
- **URL**: Admin sozlamalarida sozlanadi
- **Metod**: `POST`
- **So'rov tanasi**:
```json
{
  "event": "subscription_status_changed",
  "subscription_id": 1,
  "user_id": 1,
  "old_status": "pending",
  "new_status": "active",
  "timestamp": "2025-03-16T12:30:00Z"
}
```

## Rivojlantirish eslatmalari

1. Barcha API so'rovlari `Content-Type: application/json` sarlavhasini o'z ichiga olishi kerak.
2. Sana/vaqt qiymatlari UTC vaqt mintaqasida ISO 8601 formatida.
3. API URL yo'li orqali versiyalangan. Joriy versiya v1.
4. Fayl yuklash uchun (masalan, to'lov skrinshoti), multipart/form-data kodlashdan foydalaning.
5. API tasdiqlangan domenlardan cross-origin so'rovlar uchun CORS-ni qo'llab-quvvatlaydi.

## Testlash

Interaktiv API testlash uchun `/swagger/` manzilida Swagger UI hujjatlari mavjud.

## Qo'llab-quvvatlash

API haqida texnik yordam yoki savollar uchun murojaat qiling:
- Email: support@topinvest.com
- Telegram: @topinvest_support

## Telegram bot integratsiyasi

Telegram bot bilan integratsiya qilish uchun quyidagi endpointlardan foydalanishingiz mumkin:

### 1. Telegram orqali autentifikatsiya
- **URL**: `/users/auth/login/`
- **Metod**: `POST`
- **So'rov tanasi**:
```json
{
  "auth_data": "{\"id\":123456789,\"first_name\":\"Anvar\",\"last_name\":\"Qodirov\",\"username\":\"anvar\",\"photo_url\":\"https://t.me/i/userpic/320/anvar.jpg\",\"auth_date\":1647427200,\"hash\":\"hash_qiymati\"}"
}
```
- **Javob**:
```json
{
  "message": "Authentication successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "telegram_id": 123456789,
    "first_name": "Anvar",
    "last_name": "Qodirov",
    "username": "anvar"
  }
}
```

### 2. Foydalanuvchiga xabar yuborish
- **URL**: `/users/api/users/{user_id}/send-message/`
- **Metod**: `POST`
- **Autentifikatsiya**: Talab qilinadi (Faqat admin)
- **So'rov tanasi**:
```json
{
  "message": "Assalomu alaykum, bu shaxsiy xabar!"
}
```
- **Javob**:
```json
{
  "status": "success",
  "message": "Xabar Anvar ga muvaffaqiyatli yuborildi"
}
```

## Mobil ilovalar uchun qo'shimcha ma'lumotlar

### iOS va Android uchun tavsiyalar

1. **Token saqlash**: JWT tokenlarni xavfsiz saqlash uchun KeyChain (iOS) yoki EncryptedSharedPreferences (Android) dan foydalaning.
2. **Oflayn rejim**: Muhim ma'lumotlarni lokal bazada saqlang va internet aloqasi tiklanganda sinxronlashtiring.
3. **Xatoliklarni qayta ishlash**: Barcha API so'rovlarini try-catch bloklari bilan o'rab oling va foydalanuvchiga tushunarli xato xabarlarini ko'rsating.
4. **Rasmlar keshi**: To'lov skrinshoti va profil rasmlarini keshda saqlash uchun SDWebImage (iOS) yoki Glide (Android) kutubxonalaridan foydalaning.

### Xavfsizlik tavsiyalari

1. **SSL Pinning**: Man-in-the-middle hujumlarini oldini olish uchun SSL pinning-ni amalga oshiring.
2. **Tokenlarni yangilash**: Access token muddati tugashidan oldin refresh token orqali yangilang.
3. **Logout**: Foydalanuvchi tizimdan chiqqanda barcha tokenlarni o'chirib tashlang.
4. **Biometrik autentifikatsiya**: Qo'shimcha xavfsizlik uchun Touch ID/Face ID (iOS) yoki Fingerprint/Face Unlock (Android) ni qo'llab-quvvatlang.

## Tez-tez so'raladigan savollar

### 1. API bilan qanday ulanaman?
Avval `/users/auth/login/` endpointi orqali autentifikatsiyadan o'ting va olingan JWT tokenni keyingi so'rovlar uchun saqlang.

### 2. To'lovni qanday amalga oshiraman?
1. `/subscriptions/api/plans/` endpointidan mavjud obuna rejalarini oling
2. `/payments/api/payments/` endpointiga to'lov ma'lumotlarini POST qiling
3. To'lov tasdiqlangandan so'ng, foydalanuvchi obunasi avtomatik faollashtiriladi

### 3. Signallarni qanday olaman?
Obuna bo'lgan foydalanuvchilar `/signals/api/signals/` endpointi orqali barcha signallarni olishlari mumkin.

### 4. Referral tizimi qanday ishlaydi?
Har bir foydalanuvchiga noyob referral kodi beriladi. Yangi foydalanuvchi ro'yxatdan o'tishda ushbu kodni ko'rsatsa, u sizning referralingiz sifatida belgilanadi.

### 5. Webhook xabarnomalarini qanday sozlayman?
Admin panelidagi sozlamalar bo'limida webhook URL manzillarini ko'rsating. Tizim muhim hodisalar haqida ushbu URL manziliga POST so'rovlarini yuboradi.
