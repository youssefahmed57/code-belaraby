# 🚀 خطة التطوير المعمارية الجوهرية المعتمدة للإنتاج (Code Journey Academy Final Production Architectural Plan)

خطة معمارية شاملة ومعتمدة للإنتاج لمنصة **كود جيرني أكاديمي (Code Journey Academy)** مصممة على 6 مراحل منفصلة ومحكمة لضمان أعلى معايير الأمان، العزل الصارم، الاعتمادية، والفاعلية التعليمية.

---

## 🌟 المرحلة 0: تثبيت الأساس، التقسيم الهيكلي، والمراقبة التشغيلية (Phase 0: Infrastructure, Observability & CI/CD)

### 0.1 إعادة هيكلة حزمة الاختبارات (Modularized Test Suite)
تقسيم ملف `tests/test_backend.py` الموحد إلى وحدات اختبار متخصصة تحت مجلد `tests/`:
- `tests/auth/`: اختبارات الجلسات، التشفير، وقفل الحسابات.
- `tests/rbac/`: اختبارات الصلاحيات العامة والخاصة للكائنات (RBAC & OLA).
- `tests/payments/`: اختبارات المدفوعات، البصمة الرقمية، وتفكيك الصور.
- `tests/audit/`: اختبارات سجل العمليات المحصن المانع للتعديل.
- `tests/backups/`: اختبارات النسخ الاحتياطي والاستعادة على قواعد مؤقتة.
- `tests/coupons/`: اختبارات الكوبونات والتزامن.
- `tests/certificates/`: اختبارات إصدار الموثقات المانعة للتغيير والـ QR.
- `tests/progress/`: اختبارات التقدم الموزون وتتبع محطات المشاهدة.
- `tests/assignments/`: اختبارات الواجبات والمشاريع والتصحيح.
- `tests/execution/`: اختبارات عزل بيئة تشغيل الأكواد (Sandbox Engine).

### 0.2 بنية تتبع الهجرة الفردية والأدلة (Alembic Migrations & Indexing Engine)
- إنشاء ملفات Migration منفصلة ومستقلة لكل تغيير هيكلي مع فحص الترقية (`upgrade`) والتراجع (`downgrade`).
- إضافة الفهارس البرمجية الموجهة (`Indexes`) على الأعمدة التالية لرفع كفاءة الاستعلامات:
  - `payments.receipt_hash`
  - `certificates.certificate_code`
  - `coupons.code`
  - `user_sessions.user_id`
  - `audit_logs.created_at`
  - `lesson_progress.student_id + lesson_id`

### 0.3 نقاط فحص الجاهزية التشغيلية (Health & Readiness Probes)
- `/health`: فحص عمل التطبيق المباشر.
- `/ready`: فحص الاتصال الفعلي بقواعد البيانات PostgreSQL، Redis، وتوفر خدمات التنفيذ المعزولة.

### 0.4 المراقبة المركزية والتنبيهات التشغيلية (Observability & Alerting)
- إضافة `request_id` فريد لكل طلب وربطه بسجلات الـ API والـ Workers وخدمة تشغيل الأكواد.
- مراقبة معدلات أخطاء `4xx` و`5xx`، وزمن الاستجابة، وقياسات `p95` و`p99`.
- مراقبة اتصال PostgreSQL وRedis، وطول قائمة انتظار تشغيل الأكواد، واستهلاك المعالج والذاكرة ومساحة التخزين.
- إرسال تنبيه فوري عند فشل النسخ الاحتياطي، تكرار أخطاء Sandbox، أو انخفاض مساحة القرص.

### 0.5 مسار الدمج والنشر الآلي المحمي (Secure CI/CD Pipeline)
- تشغيل فحوصات `Lint`, `Type Check`, `Unit Tests`, `Integration Tests`, `E2E Tests`, واختبارات Alembic قبل الدمج أو النشر.
- فحص المكتبات وصور Docker بحثاً عن الثغرات الأمنية.
- اختبار `upgrade` و`downgrade` للهجرات على قاعدة جديدة وقاعدة من الإصدار السابق.
- منع النشر تلقائياً عند فشل أي فحص أساسي وتوفير آلية Rollback موثقة.

### 0.6 إدارة الأسرار وإعدادات البيئات (Secrets & Environment Configuration)
- فصل إعدادات `development`, `testing`, و `production`.
- منع رفع ملفات `.env` أو الأسرار إلى Git.
- تشغيل الإنتاج مع `DEBUG=false` ومنع إظهار Stack Traces للمستخدم.
- ضبط `CORS` على نطاقات المنصة المعتمدة فقط مع تدربك مفاتيح التشفير دورياً.

---

## 🔒 المرحلة 1A: الأمان الحرج، العزل الصارم، وحماية الجلسات (Phase 1A: Critical Security & Deep Isolation)

### 1A.1 إدارة الصلاحيات على مستوى الكائنات (Object-Level Authorization - OLA)
- تطبيق فحص ملكية الكائنات (OLA) كودياً بداخل الـ Backend:
  ```python
  if current_user.role == "instructor" and course.instructor_id != current_user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="غير مصرح لك بتعديل هذا الكورس.")
  ```
- منع كشف بيانات الإيصالات أو التقييمات بين الطلاب تماماً.

### 1A.2 سجل العمليات الإدارية المانع للتعديل (Immutable Append-Only Audit Logs)
- حظر عمليات التعديل والمسح (`UPDATE` / `DELETE`) نهائياً عبر Triggers وصلاحيات قواعد البيانات.
- تطهير حقول التغييرات قبل وبعد من كلمات المرور وتوكنات الجلسات.
- تخزين الهيكلة الكاملة: `actor_id`, `action`, `target_type`, `target_id`, `changes_before`, `changes_after`, `ip_address`, `user_agent`, `request_id`, `status`, `failure_reason`, `created_at`.

### 1A.3 بيئة تنفييد الأكواد المعزولة في طوابير وخوادم منفصلة (Asynchronous Sandbox Queue Worker)
- البنية المعتمدة: `Frontend -> FastAPI -> Redis Queue -> Execution Worker -> Ephemeral Container`.
- **ضوابط العزل**:
  - `read-only filesystem`, `non-root user`, `no-new-privileges`, network disabled.
  - حد زمن التنفيذ 5 ثوانٍ، الذاكرة 128MB، والـ PID limit لمنع هجمات الأفرعة.
  - حذف بيئة التنفيذ تلقائياً بعد الانتهاء وعدم إظهار الأخطاء الداخلية للطالب.

### 1A.4 حماية رفع الإيصالات وتفكيك الصور المتقدم (Receipt Security & EXIF Stripping)
- التثبت من الترويسات الثنائية (Magic Bytes) للصور، وإعادة فك ترميز الصورة وحفظها بصيغة آمنة وتجريد بيانات EXIF.
- رفض المطابقة التامة لـ SHA-256، وإتاحة تحذير المشرف مع تسجيل السبب والطلب السابق في السجل.
- توليد روابط معاينة موثقة وموقعة صلاحيتها من 1 إلى 5 دقائق فقط مع `Cache-Control: no-store`.

### 1A.5 أمان تسجيل الدخول وقفل الحسابات وحصانة الجلسات (Auth Lockout & Session Revocation)
- دمج تقييد المحاولات حسب عنوان الـ IP وتقييد المحاولات حسب اسم الحساب مع استخدام تأخير تدريجي وقفل مؤقت.
- تخزين بصمة أحادية الاتجاه للتوكن (`One-Way Hash`) لـ Reset Token، واستخدامه مرة واحدة صلاحيته 15-30 دقيقة.
- إبطال كافة الجلسات النشطة في قاعدة البيانات بعد تغيير كلمة المرور وتأمين الكوكيز بـ `HttpOnly`, `Secure`, `SameSite`.

---

## 📦 المرحلة 1B: النسخ الخارجية، معايير التعافي، وااختبارات الأداء (Phase 1B: Off-Site Backups, RPO/RTO & Load Criteria)

### 1B.1 أتمتة النسخ الاحتياطي بداخل العمال الخلفية (Background Backup Job Runner)
- تشغيل النسخ الاحتياطي بداخل Worker خلفي مستقل وتتبع الحالة دون حظر طلبات HTTP.
- اعتماد سكريبتات شل المتوافقة مع بيئات Linux و Docker (`backup_db.sh` و `restore_db.sh`).

### 1B.2 فحص الاستعادة بداخل قاعدة بيانات اختبارية مؤقتة (Isolated Temp DB Restore Test)
- إجراء فحص الاستعادة على قاعدة بيانات مؤقتة (`Temp DB`) وااختبار اكتمال السجلات ثم مسحها فوراً دون مس قاعدة الإنتاج.

### 1B.3 اختبارات الضغط والأداء المتوازية (Locust Performance Testing)
- إعداد سكريبت `locustfile.py` لتشغيل 100 طالب متزامن على الدخول، المحرر المعزول، والكويزات.

### 1B.4 النسخ الخارجية ومعايير التعافي (Off-Site Encrypted Backup, RPO & RTO)
- نقل نسخة مشفرة خارج خادم التطبيق بداخل Object Storage منفصل مع حفظ الـ `checksum`.
- فصل مفاتيح التشفير عن موقع تخزين ملفات النسخ الاحتياطية.
- اعتماد معايير الاستعادة: **`RPO <= 24h`** و **`RTO <= 2h`**.

### 1B.5 معايير قبول اختبارات الأداء (Performance Acceptance Thresholds)
- زمن استجابة Login p95 أقل من 800ms، Dashboard p95 أقل من 1.5s.
- نسبة الأخطاء أقل من 1% وعدم فقد أي إيصال دفع أو سجل تقدم تحت الضغط.

---

## 📚 المرحلة 2A: نظام تقدم الطالب وتحديات المحرر (Phase 2A: Weighted Progress & Code Sandbox)

### 2A.1 حساب التقدم الموزون وزر "أكمل من حيث توقفت" (Weighted Progress & Resume Button)
- أوزان التقدم: (الفيديو 40%، القراءة 10%، الكويز 20%، والتحدي البرمجي 30%).
- تتبع مشاهدة أجزاء الفيديو الفعلية (`Watch Segments`) وتخزين موقع المشاهدة الأخير.
- إضافة زر **"أكمل من حيث توقفت"** في أعلى لوحة الطالب للانتقال المباشر.

### 2A.2 نمط فك الدروس الإداري (Sequential vs Open Unlock Rules)
- دعم خيار فك الدروس التتابعي المشروط أو إتاحة جميع دروس الكورس المشترك فيه مباشرة دون ترتيب إجباري.

### 2A.3 محرر الكود والمسودات والاختبارات المخفية (Monaco Drafts & Hidden Tests)
- حفظ المسودات تلقائياً وإتاحة إعادة ضبط الحل والتلميحات.
- إجراء التقييم بداخل الـ Sandbox مقابل اختبارات مخفية (Hidden Tests) بدون تسريب الإجابة النموذجية.

---

## 📜 المرحلة 2B: الواجبات، الشهادات الموثقة، والكوبونات المانعة للتضارب (Phase 2B: Assignments, Certificates & Coupons)

### 2B.1 الواجبات والمشاريع المتقدمة (Assignments & GitHub Submissions)
- دعم تسليم المشاريع وعناوين GitHub والملفات المحمية مع معايير التقييم وملاحظات المدرس.

### 2B.2 الشهادات الموثقة المانعة للتزوير (Verifiable Certificates & Frozen Records)
- عدم إصدار الشهادة إلا بعد النجاح الكامل 100% والاختبار النهائي.
- تجميد اسم الطالب والكورس وقت الإصدار وتوليد رمز QR موثق ورابط تحقق عام بـ `/verify-certificate/[code]`.

### 2B.3 الكوبونات المتزامنة المانعة للتضارب (Atomic Coupons & Usage Isolation)
- تطبيق الكوبونات برمجياً باستخدام `Atomic Operations / DB Locking` لمنع القراءة المتوازية التي قد تتجاوز الحد الأقصى المسموح.

### 2B.4 مركز الإشعارات الموجهة (Targeted Broadcast Notifications)
- إرسال إشعارات داخلية موجهة لطالب محدد، صف دراسي، أو كورس معين.

---

## 🚀 المرحلة 3: المساعد الذكي، التحفيز، وتطبيق PWA (Phase 3: AI Tutor, Gamification & PWA)

### 3.1 المساعد التعليمي بالذكاء الاصطناعي (Course-Bounded AI Tutor & RAG)
- مساعد ذكي ببيئة RAG مقتصر على محتوى الكورس فقط، يوفر التلميحات ويرفض إعطاء الحل الكامل، مع قيود توكنات يومية.

### 3.2 نظام التحفيز غير القابل للتلاعب (XP Ledger & Gamification Badges)
- منح النقاط حصرياً من الـ Backend وتوثيق كل عملية بجدول سجل النقاط (`XP Ledger`).

### 3.3 تطبيق PWA والوضع الداكن/الفاتح (PWA Cache Exclusion & Theme Toggle)
- إضافة `manifest.json` و `service-worker.js` لتثبيت التطبيق واستثناء واجهات الإدارة والإيصالات من التخزين المؤقت.
- دعم خيار الثيم الفاتح والداكن.

---

## 🧪 خطة التحقق والاختبارات الموزعة (Distributed Verification Plan)

سيتم تنفيذ الاختبارات عبر المجلدات المخصصة:
- `python -m pytest tests/auth/`
- `python -m pytest tests/rbac/`
- `python -m pytest tests/payments/`
- `python -m pytest tests/execution/`
- `python -m pytest tests/backups/`
- `python -m pytest tests/coupons/`
- `python -m pytest tests/certificates/`
- `locust -f tests/locustfile.py`
