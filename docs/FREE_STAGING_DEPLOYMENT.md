# دليل النشر التجريبي المجاني (Code Belaraby - Free Staging Deployment Guide)

هذا المستند يقدم الخطة التنفيذية لنشر بيئة المماثلة **Staging** لمنصة **كود بالعربي (Code Belaraby)** باستخدام الخدمات السحابية المجانية بالكامل (**Vercel + Render + Supabase + Upstash Redis**).

---

## 🏗️ المعمارية المجانية المستهدفة (Free Hosting Stack)

| المكون | الخدمة السحابية | النطاق / الرابط المتوقع |
| :--- | :--- | :--- |
| **الواجهة الأمامية (Frontend)** | Vercel Hobby (Next.js) | `https://code-belaraby-staging.vercel.app` |
| **الواجهة الخلفية (Backend)** | Render Free Web Service (FastAPI) | `https://code-belaraby-api.onrender.com` |
| **قاعدة البيانات (Database)** | Supabase Free PostgreSQL | `pooler.supabase.com` (Port 6543 / 5432) |
| **تخزين الإيصالات (Storage)** | Supabase Storage Private Bucket | `payment-receipts` |
| **التخزين المؤقت وطابور العمل** | Upstash Redis Free | `rediss://...upstash.io:6379` (TLS) |

---

## 📋 الخطوة 1: إعداد قاعدة البيانات وتخزين الإيصالات على Supabase (مجاناً)

1. افتح موقع [Supabase](https://supabase.com) وأنشئ مشروعاً جديداً باسم `code-belaraby-staging`.
2. اذهب إلى **Database Settings** -> **Connection String**:
   * انسخ رابط الاتصال التزامني `postgresql+psycopg2://...:5432/postgres` وضعه في `SYNC_DATABASE_URL`.
   * انسخ رابط الاتصال غير التزامني عبر Transaction Pooler `postgresql+asyncpg://...:6543/postgres` وضعه في `DATABASE_URL`.
3. اذهب إلى **Storage** -> **New Bucket**:
   * اسم الـ Bucket: `payment-receipts`.
   * اجعل الـ Bucket **Private** (تأكد أن خيار Public مغلق تماماً).
4. اذهب إلى **Project Settings** -> **API**:
   * انسخ `Project URL` وضعه في `SUPABASE_URL`.
   * انسخ `service_role` secret (المفتاح السري للإدارة) وضعه في `SUPABASE_SERVICE_ROLE_KEY`.

---

## 🔴 الخطوة 2: إنشاء ذاكرة Redis مجانية على Upstash

1. افتح [Upstash Console](https://console.upstash.com) وأنشئ **Redis Database** مجانية باسم `code-belaraby-redis`.
2. اختر المنطقة القريبة (مثل Frankfurt / EU).
3. من تفاصيل الـ Database، انسخ **UPSTASH_REDIS_REST_URL** أو رابط `rediss://...` الخاص بـ `redis-py` وضعه في `REDIS_URL`.

---

## 🚀 الخطوة 3: نشر الواجهة الخلفية (FastAPI) على Render Free Web Service

1. افتح [Render Dashboard](https://dashboard.render.com) واضغط **New** -> **Web Service**.
2. اربط حساب GitHub واختر مستودع `EljokesX/code-belaraby` والفرع `staging`.
3. اضبط الإعدادات التالية:
   * **Name**: `code-belaraby-api`
   * **Root Directory**: `backend`
   * **Runtime**: `Python 3`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `chmod +x ../scripts/render_start.sh && ../scripts/render_start.sh`
4. اذهب إلى **Environment Variables** وأضف المتغيرات التالية:
   * `ENVIRONMENT`: `staging`
   * `DEBUG`: `false`
   * `SECRET_KEY`: مفتاح سري عشوائي (32 حرفاً).
   * `CSRF_SECRET`: مفتاح CSRF عشوائي (32 حرفاً).
   * `SIGNED_URL_SECRET`: مفتاح توقيع الصور عشوائي (32 حرفاً).
   * `DATABASE_URL`: رابط Supabase asyncpg المنسوخ في الخطوة 1.
   * `SYNC_DATABASE_URL`: رابط Supabase psycopg2 المنسوخ في الخطوة 1.
   * `REDIS_URL`: رابط Upstash المنسوخ في الخطوة 2.
   * `SUPABASE_URL`: رابط المشروع في Supabase.
   * `SUPABASE_SERVICE_ROLE_KEY`: مفتاح service_role الخاص بـ Supabase.
   * `SUPABASE_STORAGE_BUCKET`: `payment-receipts`.
   * `ALLOWED_ORIGINS`: `["https://code-belaraby-staging.vercel.app"]` (رابط Vercel).
   * `SECURE_COOKIES`: `true`.
   * `ALLOW_LOCAL_RUNNER_IN_PROD`: `false`.
   * `RUN_SEED`: `false` (أو `true` لأول مرة فقط إن رغبت بتعبئة البيانات الأولية).
5. اضغط **Create Web Service**. سيتم تشغيل الترحيلات تلقائياً عبر `scripts/render_start.sh`.

---

## ⚡ الخطوة 4: نشر الواجهة الأمامية (Next.js) على Vercel Hobby

1. افتح [Vercel Dashboard](https://vercel.com) واضغط **Add New** -> **Project**.
2. اختر مستودع `EljokesX/code-belaraby` وفرع `staging`.
3. اضبط الإعدادات التالية:
   * **Root Directory**: اختر مجلد `frontend`.
   * **Framework Preset**: `Next.js`.
4. اذهب إلى **Environment Variables** وأضف:
   * `NEXT_PUBLIC_API_URL`: `https://code-belaraby-api.onrender.com/api/v1` (رابط Render المستخرج من الخطوة 3).
   * `NEXT_PUBLIC_APP_URL`: `https://code-belaraby-staging.vercel.app` (رابط Vercel الممنوح).
5. اضغط **Deploy**.

---

## 🔒 الإجراءات الأمنية والملاحظات المستهدفة

1. **السرية التامة للإيصالات**: يتم رفع الإيصالات مباشرة من الـ Backend إلى Supabase Storage Private Bucket دون إمكانية الوصول العلني إليها. يولد الـ Backend روابط مؤقتة مشفرة (`signedURL`) قصيرة المدة (5 دقائق) للأدمن فقط لمعاينة الصور.
2. **محرك تنفيذ الأكواد (Playground)**: موقوف مؤقتاً في البيئة الحية المجانية (`ALLOW_LOCAL_RUNNER_IN_PROD=false`) ويعرض للمستخدم رسالة واضحة: *"تشغيل الأكواد غير متاح مؤقتاً في النسخة التجريبية"*.
3. **الجلسات والـ Cookies عبر الدومينات المتعددة**: يتم الحفاظ على `SECURE_COOKIES=true` وتضمين `ALLOWED_ORIGINS` لرابط Vercel لمنع حجب طلبات CORS و Session Cookies بين Render و Vercel.
