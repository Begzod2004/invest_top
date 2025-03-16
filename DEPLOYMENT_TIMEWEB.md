# Timeweb Cloud ga Deployment Qilish

Bu qo'llanma Top Invest loyihasini Timeweb Cloud serveriga o'rnatish uchun ko'rsatmalarni o'z ichiga oladi.

## 1. Timeweb Cloud da Docker Container yaratish

1. [Timeweb Cloud](https://timeweb.cloud/) saytiga kiring va ro'yxatdan o'ting yoki hisobingizga kiring.
2. "Konteynerlar" bo'limiga o'ting va yangi Docker konteyner yarating.
3. Konteyner sozlamalarini quyidagicha o'rnating:
   - Nomi: `top-invest`
   - Operatsion tizim: `Docker`
   - Tasvir (Image): `Docker Hub` dan
   - Tasvir nomi: `your-dockerhub-username/top-invest:latest`
   - Port: `8000`
   - Xotira: Kamida 2GB RAM va 10GB disk

## 2. Loyihani tayyorlash

1. Loyihani Docker Hub ga yuklash uchun tayyorlang:

```bash
# Loyiha papkasiga o'ting
cd top-invest-1/backend

# Docker image yarating
docker build -t your-dockerhub-username/top-invest:latest .

# Docker Hub ga push qiling
docker login
docker push your-dockerhub-username/top-invest:latest
```

2. `.env` faylini sozlang:

```
# Django secret key
SECRET_KEY=xavfsiz-kalit-yarating

# Debug mode
DEBUG=False

# Allowed hosts
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.timeweb.cloud

# Database configuration
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Celery configuration
CELERY_BROKER_URL=memory://

# Telegram Bot settings
BOT_TOKEN=your-telegram-bot-token
CHANNEL_ID=your-telegram-channel-id

# CORS settings
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

## 3. Timeweb Cloud da konteyner sozlamalari

1. Timeweb Cloud panelida yaratilgan konteynerga o'ting.
2. "Sozlamalar" bo'limida quyidagi muhit o'zgaruvchilarini qo'shing:

   - Yuqoridagi `.env` faylidagi barcha o'zgaruvchilarni qo'shing.

3. "Tomlar" (Volumes) bo'limida quyidagi tomlarni qo'shing:
   - `/app/db.sqlite3` - ma'lumotlar bazasi uchun
   - `/app/media` - media fayllar uchun
   - `/app/payment_screenshots` - to'lov skrinshotlari uchun

## 4. Domain va SSL sozlamalari

1. Timeweb Cloud panelida "Domenlar" bo'limiga o'ting.
2. Domeningizni qo'shing va uni Docker konteyneringizga yo'naltiring.
3. SSL sertifikatini yoqing.

## 5. Admin foydalanuvchi yaratish

1. Timeweb Cloud panelida konteyner terminaliga kiring.
2. Quyidagi buyruqni bajaring:

```bash
python manage.py createsuperuser
```

3. So'ralgan ma'lumotlarni kiriting (foydalanuvchi nomi, email, parol).

## 6. Tekshirish

1. Brauzeringizda `https://your-domain.timeweb.cloud/admin/` manzilini oching.
2. Yaratilgan admin hisobi bilan tizimga kiring.
3. Barcha funksiyalar to'g'ri ishlayotganini tekshiring.

## Xatoliklarni bartaraf etish

### Django va Jazzmin versiyalari muammosi

Agar `TemplateSyntaxError: Invalid filter: 'length_is'` xatosi chiqsa, Django va Jazzmin versiyalari mos kelmasligidan bo'lishi mumkin. Bu holda:

```bash
# requirements.txt faylida Django va Jazzmin versiyalarini o'zgartiring
# Django 5.x o'rniga Django 4.2.x ishlatish kerak
Django==4.2.10
django-jazzmin==2.4.0
```

### Ma'lumotlar bazasi muammolari

Agar ma'lumotlar bazasi bilan bog'liq muammolar yuzaga kelsa:

```bash
# Migratsiyalarni qayta ishga tushirish
python manage.py migrate --fake-initial
```

### Statik fayllar muammolari

Statik fayllar yuklanmasa:

```bash
# Statik fayllarni qayta yig'ish
python manage.py collectstatic --noinput
```

### Konteyner ishga tushmasa

Konteyner loglarini tekshiring:

```bash
# Timeweb Cloud panelida "Loglar" bo'limiga o'ting
```

## Zaxira nusxa olish

Ma'lumotlar bazasining zaxira nusxasini olish:

```bash
# Konteyner terminalida
cp /app/db.sqlite3 /app/db.sqlite3.backup
```

## Yangilanishlar

Yangi versiyani o'rnatish:

1. Yangi Docker image yarating va Docker Hub ga yuklang.
2. Timeweb Cloud panelida konteyner sozlamalariga o'ting.
3. "Yangilash" tugmasini bosing va yangi tasvir versiyasini tanlang.
