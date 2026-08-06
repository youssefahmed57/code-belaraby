# دليل النشر والتطبيق التلقائي لبيئة المماثلة (Code Belaraby - Staging Deployment Runbook)

هذا المستند هو الدليل الرسمي والهندسي لنشر بيئة المماثلة **Staging** لمنصة **كود بالعربي (Code Belaraby)** على خادم VPS مستقل يعمل بنظام **Ubuntu / Debian Linux**.

---

## 📋 المتطلبات والبيئة المستهدفة

* **Domain (الواجهة الأمامية)**: `STAGING_FRONTEND_DOMAIN` (مستضافة على Vercel).
* **API Domain (الواجهة الخلفية)**: `STAGING_API_DOMAIN` (مستضافة على الـ VPS).
* **النظام الشغال**: Ubuntu 22.04 / 24.04 LTS.
* **المكونات الداخلية**: Docker Compose, PostgreSQL 15.6, Redis 7.2, FastAPI Backend, Nginx Proxy.

---

## 🛡️ توضيح أمني هام بخصوص معالج الأكواد (Code Playground Sandbox)

بناءً على التكوين الأمني المعين لبيئة Staging (`ALLOW_LOCAL_RUNNER_IN_PROD=false`):
* محرر الأكواد في منصة الطالب لن يسمح بتشغيل الأكواد محلياً عبر `subprocess` مباشر لحماية سيرفر Staging المتاح على الإنترنت من أي تعليمات ضارة.
* محاولة تشغيل الكود ستُرجع خطأ `RuntimeError: Local subprocess code execution is disabled in production environment for security`.
* **هذا سلوك أمني مقصود وليس خطأ برمجياً**. لتشغيل الأكواد في Staging مستقبلاً، يتم ربط خدمة **Judge0 Sandbox** معزولة عبر تزويد متغير `JUDGE0_URL`.

---

## 🛠️ الخطوة 1: تثبيت المتطلبات الأساسية و Docker Engine على الـ VPS

قم بتسجيل الدخول إلى سيرفر الـ VPS عبر SSH وتنفيذ الأوامر التالية بالترتيب لتثبيت Docker Engine رسمياً من مستودع Docker و Nginx:

```bash
# 1. تحديث حزم النظام وتثبيت المتطلبات الأساسية
sudo apt update && sudo apt install -y ca-certificates curl gnupg lsb-release git nginx certbot python3-certbot-nginx

# 2. إضافة مفتاح ومستودع Docker الرسمي على Ubuntu
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. تثبيت Docker Engine وحزم Docker Compose V2 الرسمية
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 4. تفعيل وتشغيل خدمة Docker بعد اكتمال التثبيت
sudo systemctl enable --now docker
docker --version
docker compose version
```

---

## 🔑 الخطوة 2: إنشاء مفتاح Deploy Key وربطه بمستودع GitHub

```bash
# 1. إنشاء دليل المفاتيح
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# 2. إنشاء مفتاح SSH معزول للمستودع
ssh-keygen -t ed25519 -C "code-belaraby-staging-vps" -f /root/.ssh/code_belaraby_deploy -N ""

# 3. عرض المفتاح العام ونسخه
cat /root/.ssh/code_belaraby_deploy.pub
```

قم بنسخ السطر كاملاً الذي يبدأ بـ `ssh-ed25519` وإضافته في مستودع GitHub:
* افتح `https://github.com/EljokesX/code-belaraby` -> **Settings** -> **Deploy keys** -> **Add deploy key**.
* Title: `Code Belaraby Staging VPS`
* Key: الصق المفتاح العام (مع ترك `Allow write access` **غير مفعلة**).

ثم اضبط إعدادات SSH على السيرفر:

```bash
cat > /root/.ssh/config <<'EOF'
Host github-code-belaraby
    HostName github.com
    User git
    IdentityFile /root/.ssh/code_belaraby_deploy
    IdentitiesOnly yes
EOF

chmod 600 /root/.ssh/config
chmod 600 /root/.ssh/code_belaraby_deploy

# إضافة بصمة GitHub
ssh-keyscan github.com >> /root/.ssh/known_hosts
chmod 600 /root/.ssh/known_hosts

# اختبـار الاتصال مع GitHub
ssh -T github-code-belaraby
```

---

## 📦 الخطوة 3: سحب فرع Staging من المستودع الخاص

```bash
# 1. إنشاء مجلد التطبيق
mkdir -p /opt/code-belaraby
cd /opt/code-belaraby

# 2. سحب فرع staging فقط
git clone --branch staging --single-branch git@github-code-belaraby:EljokesX/code-belaraby.git app

# 3. الدخول إلى مجلد المشروع وتأكيد النطاق
cd /opt/code-belaraby/app
git status
git branch -vv
```

---

## 🔐 الخطوة 4: إنشاء ملف البيئة `.env.staging`

نسخ قالب البيئة وإنشاء ملف التكوين الحقيقي:

```bash
cp .env.staging.example .env.staging
nano .env.staging
```

قم بتعديل قيم المتغيرات التالية بكلمات مرور وأسرار عشوائية جديدة:
* `SECRET_KEY`: قيمة عشوائية (32 حرفاً على الأقل).
* `CSRF_SECRET`: قيمة عشوائية (32 حرفاً على الأقل).
* `POSTGRES_PASSWORD`: كلمة مرور قوية لقاعدة البيانات.
* `ADMIN_DEFAULT_PASSWORD`: كلمة مرور جديدة لحساب Super Admin.
* `INSTRUCTOR_DEFAULT_PASSWORD`: كلمة مرور جديدة لحساب Instructor.
* `STUDENT_DEFAULT_PASSWORD`: كلمة مرور جديدة لحسابات الطلاب.
* `ALLOW_LOCAL_RUNNER_IN_PROD=false` (تأكيد معالج الأمان).
* `RUN_SEED=false` (اتركه false لمنع إعادة التأسيس وتوليد حسابات جديدة إلا عند الحاجة الأولى فقط).

---

## 🐳 الخطوة 5: فحص وبناء حاويات Docker

```bash
# 1. التحقق من بناء التركيبة وتوافق التنسيق دون أخطاء
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging config

# 2. تشغيل الحاويات في الخفاء مع إجراء Rebuild
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up -d --build --remove-orphans
```

---

## 🗄️ الخطوة 6: تشغيل ترحيلات قاعدة البيانات (Alembic Migrations)

```bash
# تشغيل Alembic لمرة واحدة فقط لإنشاء الجداول والتحديثات
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T backend python -m alembic upgrade head

# اختياري (لأول نشر فقط إن رغبت في تعبئة البيانات التجريبية الأولية):
# docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T backend python app/db/seed.py
```

---

## 🔍 الخطوة 7: مراجعة سجلات الحاويات (Logs Audit)

```bash
# عرض سجلات جميع الخدمات للتأكد من عدم وجود أخطاء في التشغيل
docker compose -f docker-compose.yml -f docker-compose.staging.yml logs -f --tail=50
```

تأكد أن سجلات `backend` تظهر:
`INFO: Application startup complete.`

---

## 🌐 الخطوة 8: إعداد Nginx وإصدار شهادة SSL (عند تجهيز الـ DNS)

بعد توجيه A Record الخاص بـ `STAGING_API_DOMAIN` إلى IP سيرفر الـ VPS:

```bash
# 1. نسخ وتعديل اسم الدومين في ملف Nginx
sudo cp deploy/nginx/staging.conf /etc/nginx/sites-available/staging.conf
sudo sed -i 's/STAGING_API_DOMAIN/api-staging.yourdomain.com/g' /etc/nginx/sites-available/staging.conf
sudo ln -sf /etc/nginx/sites-available/staging.conf /etc/nginx/sites-enabled/

# 2. فحص سلامة إعدادات Nginx
sudo nginx -t

# 3. إعادة تحميل Nginx
sudo systemctl reload nginx

# 4. إصدار شهادة SSL يدويًا بعد التأكد من توجيه الدومين للـ VPS IP
sudo certbot --nginx -d api-staging.yourdomain.com
```

---

## 🧪 الخطوة 9: تشغيل اختبارات الدخان (Staging Smoke Tests)

يمكنك تشغيل اختبارات Smoke للتأكد من استجابة النظام:

```bash
# فحص استجابة Health و Ready Probes على الـ VPS
curl -i http://127.0.0.1:8000/api/v1/health
curl -i http://127.0.0.1:8000/api/v1/ready
```

---

## 🔄 الخطوة 10: خطة التراجع الفوري (Rollback Procedure)

عند وجود خلل غير متوقع بعد النشر:

```bash
# 1. التراجع إلى الـ Commit السابق
cd /opt/code-belaraby/app
git checkout HEAD~1

# 2. إعادة تشغيل الحاويات
docker compose -f docker-compose.yml -f docker-compose.staging.yml --env-file .env.staging up -d --build

# 3. استعادة أحدث نسخة احتياطية لسجل البيانات إذا لزم الأمر
./scripts/restore_db.sh ./backups/backup_staging_YYYYMMDD_HHMMSS.sql staging
```
