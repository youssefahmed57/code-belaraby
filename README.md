# منصة كود بالعربي (Code Belaraby)

منصة تعليمية متكاملة بأسلوب عالمي ومصممة باللغة العربية (RTL) لتعليم البرمجة لطلاب المرحلة الثانوية في مصر (الصف الأول والصف الثاني الثانوي) والمبتدئين.

## 🚀 المميزات الرئيسية (Core Features)

1. **نظام الشرح والتطبيق**: دروس تفاعلية تدعم شرح نظري غني، فيديوهات محمية برموز مشفرة، كويزات، ومحرر كود Monaco مدمج.
2. **محرك تصحيح كود معزول**: بيئات `staging` و`production` تعتمد على Judge0 أو مزود عزل حقيقي، بينما يسمح بالمشغل المحلي غير الآمن فقط في `development` و`test` عند تفعيله صراحة.
3. **نظام فتح الدروس الأوتوماتيكي**: يفتح الدرس التالي فور مشاهدة 80% من الفيديو + قراءة النظري + حل التحدي + اجتياز الكويز بـ 70%.
4. **تأكيد المدفوعات اليدوية (InstaPay & Vodafone Cash)**: رفع إيصال الدفع متبوعاً بمراجعة وقبول الإدارة وتفعيل الاشتراك في قاعدة البيانات بشكل تزامني.
5. **لوحة تحكم إدارية شاملة**: مراجعة المدفوعات والمعاينة المباشرة للإيصالات، إدارة الطلاب، وتصدير التقارير بصيغة CSV.

---

## 💻 التشغيل المحلي السريع (Local Quickstart)

### 1. المتطلبات الأساسية
- Python 3.11+
- Node.js 18+ (أو npm)

### 2. تثبيت الحزم وتشغيل النظام
```bash
# 1. إعداد البيئة الخلفية (Backend)
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.lock
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

وفي نافذة مبوبة ثانية:
```bash
# 2. إعداد البيئة الأمامية (Frontend)
cd frontend
npm install
npm run dev
```

افتح المتصفح على: [http://localhost:3000](http://localhost:3000)

---

## 🐳 التشغيل باستخدام Docker Compose

```bash
docker-compose up --build -d
```

رابط المنصة بالكامل: [http://localhost](http://localhost)

---

## 🔑 حسابات الاختبار

يتم إنشاء بيانات الاختبار محليًا من خلال ملفات البيئة والـ Seed الآمن، ولا يتم نشر أسماء المستخدمين أو كلمات المرور داخل المستودع.

---

## 🧪 تشغيل الاختبارات الأوتوماتيكية (Automated Testing)

### اختـبارات الباك إند (Pytest):
```bash
cd backend
pytest -v
```

### اختـبارات E2E الشاملة (Playwright):
```bash
npx playwright test
```

---

## 📚 التوثيق التفصيلي (Documentation)
- [الهندسة المعمارية (docs/architecture.md)](file:///c:/Users/dell/Downloads/المنصه/docs/architecture.md)
- [قاعدة البيانات والـ ERD (docs/database.md)](file:///c:/Users/dell/Downloads/المنصه/docs/database.md)
- [توثيق الـ API (docs/api.md)](file:///c:/Users/dell/Downloads/المنصه/docs/api.md)
- [الأمان وصلاحيات المستخدمين (docs/security.md)](file:///c:/Users/dell/Downloads/المنصه/docs/security.md)
- [دليل المدفوعات والـ InstaPay (docs/payments.md)](file:///c:/Users/dell/Downloads/المنصه/docs/payments.md)
- [دليل المسؤول باللغة العربية (docs/admin-guide-ar.md)](file:///c:/Users/dell/Downloads/المنصه/docs/admin-guide-ar.md)
- [دليل الطالب باللغة العربية (docs/student-guide-ar.md)](file:///c:/Users/dell/Downloads/المنصه/docs/student-guide-ar.md)
