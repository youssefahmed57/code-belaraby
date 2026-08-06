import sys
import os
from datetime import datetime, timedelta

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SyncSessionLocal, Base, sync_engine
from app.core.security import get_password_hash
from app.db.models import (
    User, Role, Permission, RolePermission, UserRole, Course, CourseInstructor,
    Module, Lesson, LessonBlock, VideoAsset, Quiz, Question, QuestionOption,
    QuizQuestion, CodingProblem, TestCase, PlatformSettings, Enrolment, Payment,
    LessonProgress, CourseProgress
)

def seed_db():
    print("Creating all tables in database...")
    Base.metadata.create_all(bind=sync_engine)
    session = SyncSessionLocal()

    try:
        print("Seeding Roles and Permissions...")
        roles = {
            "super_admin": "مدير للنظام بشرط المراقبة الكاملة والتحكم بالإعدادات",
            "admin": "مدير المنصة لمراجعة المدفوعات والطلاب والدورات",
            "instructor": "محاضر لإدارة الدورات والدروس والأسئلة",
            "student": "طالب لمتابعة الدروس وحل الاختبارات والتحديات"
        }
        
        role_objs = {}
        for r_name, r_desc in roles.items():
            existing = session.query(Role).filter_by(name=r_name).first()
            if not existing:
                r_obj = Role(name=r_name, description=r_desc)
                session.add(r_obj)
                session.commit()
                session.refresh(r_obj)
                role_objs[r_name] = r_obj
            else:
                role_objs[r_name] = existing

        admin_pass = os.getenv("ADMIN_DEFAULT_PASSWORD", "AdminPass123!@#")
        instructor_pass = os.getenv("INSTRUCTOR_DEFAULT_PASSWORD", "InstructorPass123!@#")
        student_pass = os.getenv("STUDENT_DEFAULT_PASSWORD", "StudentPass123!@#")

        print("Seeding Users...")
        # Super Admin / Instructor Default User
        super_admin_user = session.query(User).filter_by(phone_number="01001340533").first()
        if not super_admin_user:
            super_admin_user = User(
                arabic_name="يوسف أحمد صبحي عابدين",
                phone_number="01001340533",
                email="admin@codejourney.eg",
                hashed_password=get_password_hash(admin_pass),
                grade_level="all",
                status="active"
            )
            session.add(super_admin_user)
            session.commit()
            session.refresh(super_admin_user)
            
            # Add roles
            session.add(UserRole(user_id=super_admin_user.id, role_id=role_objs["super_admin"].id))
            session.add(UserRole(user_id=super_admin_user.id, role_id=role_objs["instructor"].id))
            session.commit()
        else:
            super_admin_user.hashed_password = get_password_hash(admin_pass)
            super_admin_user.failed_login_attempts = 0
            super_admin_user.locked_until = None
            session.commit()

        # Instructor User
        instructor_user = session.query(User).filter_by(phone_number="01008168639").first()
        if not instructor_user:
            instructor_user = User(
                arabic_name="محاضر مساعد - كود بالعربي",
                phone_number="01008168639",
                email="youssef@codejourney.eg",
                hashed_password=get_password_hash(instructor_pass),
                grade_level="all",
                status="active"
            )
            session.add(instructor_user)
            session.commit()
            session.refresh(instructor_user)
            session.add(UserRole(user_id=instructor_user.id, role_id=role_objs["instructor"].id))
            session.commit()
        else:
            instructor_user.hashed_password = get_password_hash(instructor_pass)
            instructor_user.failed_login_attempts = 0
            instructor_user.locked_until = None
            session.commit()

        # Demo Student 1 (Active Enrolment)
        student1 = session.query(User).filter_by(phone_number="01011111111").first()
        if not student1:
            student1 = User(
                arabic_name="أحمد محمود السيد",
                phone_number="01011111111",
                email="student1@codejourney.eg",
                hashed_password=get_password_hash(student_pass),
                grade_level="first_secondary",
                parent_name="محمود السيد",
                parent_phone="01099999991",
                status="active"
            )
            session.add(student1)
            session.commit()
            session.refresh(student1)
            session.add(UserRole(user_id=student1.id, role_id=role_objs["student"].id))
            session.commit()
        else:
            student1.hashed_password = get_password_hash(student_pass)
            student1.failed_login_attempts = 0
            student1.locked_until = None
            session.commit()

        # Demo Student 2 (Pending Payment)
        student2 = session.query(User).filter_by(phone_number="01022222222").first()
        if not student2:
            student2 = User(
                arabic_name="مريم خالد علي",
                phone_number="01022222222",
                email="student2@codejourney.eg",
                hashed_password=get_password_hash(student_pass),
                grade_level="first_secondary",
                status="active"
            )
            session.add(student2)
            session.commit()
            session.refresh(student2)
            session.add(UserRole(user_id=student2.id, role_id=role_objs["student"].id))
            session.commit()
        else:
            student2.hashed_password = get_password_hash(student_pass)
            student2.failed_login_attempts = 0
            student2.locked_until = None
            session.commit()

        # Demo Student 3 (No Enrolment)
        student3 = session.query(User).filter_by(phone_number="01033333333").first()
        if not student3:
            student3 = User(
                arabic_name="عمر الشريف حسن",
                phone_number="01033333333",
                email="student3@codejourney.eg",
                hashed_password=get_password_hash(student_pass),
                grade_level="second_secondary",
                status="active"
            )
            session.add(student3)
            session.commit()
            session.refresh(student3)
            session.add(UserRole(user_id=student3.id, role_id=role_objs["student"].id))
            session.commit()
        else:
            student3.hashed_password = get_password_hash(student_pass)
            student3.failed_login_attempts = 0
            student3.locked_until = None
            session.commit()

        print("Seeding Platform Settings...")
        default_settings = {
            "platform_name": "منصة كود بالعربي",
            "instructor_name": "يوسف أحمد صبحي عابدين",
            "instructor_qualification": "خريج كلية الحاسبات والذكاء الاصطناعي",
            "instructor_photo": "/images/instructor.png",
            "primary_phone": "01001340533",
            "secondary_phone": "01008168639",
            "whatsapp_phone": "01001340533",
            "instapay_account": "01001340533",
            "vodafone_cash_number": "01001340533",
            "currency": "جنية مصري",
            "default_passing_score": 70.0,
            "default_video_percentage": 80.0,
            "support_email": "support@codejourney.eg",
            "theme_mode": "dark",
            "primary_color": "#3B82F6",
            "accent_color": "#EF4444"
        }

        for key, val in default_settings.items():
            existing = session.query(PlatformSettings).filter_by(key=key).first()
            if not existing:
                session.add(PlatformSettings(key=key, value=val, description=f"إعداد {key}"))
        session.commit()

        print("Seeding Courses...")
        course1 = session.query(Course).filter_by(slug="python-first-secondary").first()
        if not course1:
            course1 = Course(
                title="البرمجة والذكاء الاصطناعي – الصف الأول الثانوي",
                slug="python-first-secondary",
                short_description="كورس شامل لتأسيس طلاب أولى ثانوي في لغة Python والتفكير البرمجي السليم وكتابة أول برنامج.",
                full_description="""منهج متكامل مصمم خصيصاً لطلاب الصف الأول الثانوي في مصر. نتعلم فيه أساسيات لغة Python، التعامل مع المتغيرات، الجمل الشرطية، الحلقات التكرارية، وبناء تطبيقات ومشاريع حقيقية تخدم المنهج الدراسي وتفتح لك آفاق البرمجة والذكاء الاصطناعي.""",
                grade_level="first_secondary",
                instructor_id=super_admin_user.id,
                price=250.0,
                discount_price=180.0,
                duration_hours=12.0,
                estimated_learning_hours=20.0,
                requirements=["جهاز كمبيوتر أو هاتف ذكي", "شغف بالتعلم والتفكير المنطقي"],
                learning_outcomes=[
                    "فهم المتغيرات وأنواع البيانات الأساسية في Python",
                    "كتابة شروط برمجية اتخاذ القرار If/Else",
                    "استخدام الحلقات التكرارية For و While",
                    "بناء حاسبة مصروف برمجية ومشاريع تفاعلية"
                ],
                status="published",
                visibility="public"
            )
            session.add(course1)
            session.commit()
            session.refresh(course1)

        # Demo Course 2 (Second Secondary)
        course2 = session.query(Course).filter_by(slug="web-second-secondary-demo").first()
        if not course2:
            course2 = Course(
                title="تطوير الموقع وتأسيس الويب – الصف الثاني الثانوي (توضيحي)",
                slug="web-second-secondary-demo",
                short_description="مقدمة في HTML و CSS و JavaScript لبناء مواقع تفاعلية جذابة.",
                full_description="محتوى توضيحي تجريبي يوضح هيكلة الدروس الخاصة بالصف الثاني الثانوي.",
                grade_level="second_secondary",
                instructor_id=super_admin_user.id,
                price=300.0,
                discount_price=220.0,
                duration_hours=15.0,
                status="published",
                visibility="public"
            )
            session.add(course2)
            session.commit()
            session.refresh(course2)

        print("Seeding Modules & Video Assets...")
        mod1 = session.query(Module).filter_by(course_id=course1.id, order=1).first()
        if not mod1:
            mod1 = Module(
                course_id=course1.id,
                title="أساسيات لغة Python",
                description="الوحدة الأولى: المدخل التجريبي إلى عالم المتغيرات والشروط والحلقات التكرارية.",
                order=1,
                status="published"
            )
            session.add(mod1)
            session.commit()
            session.refresh(mod1)

        # Video Assets
        v_asset1 = session.query(VideoAsset).filter_by(title="درس المتغيرات وأنواع البيانات").first()
        if not v_asset1:
            v_asset1 = VideoAsset(
                title="درس المتغيرات وأنواع البيانات",
                provider="local",
                external_video_id="demo_video_lesson_1",
                duration_seconds=600,
                thumbnail_url="/images/video_thumb_1.jpg"
            )
            session.add(v_asset1)
            session.commit()
            session.refresh(v_asset1)

        print("Seeding Lesson 1...")
        lesson1 = session.query(Lesson).filter_by(module_id=mod1.id, order=1).first()
        if not lesson1:
            lesson1 = Lesson(
                module_id=mod1.id,
                title="المتغيرات وأنواع البيانات (Variables & Data Types)",
                slug="variables-and-data-types",
                description="تعلم كيفية تخزين البيانات في الذاكرة باستخدام المتغيرات والتعامل مع الأرقام والنصوص.",
                learning_objectives=["تعريف المتغير", "التمييز بين Integer, Float, String", "طباعة القيم وقراءتها"],
                rich_content="""
<h3>ما هو المتغير (Variable)؟</h3>
<p>المتغير هو عبارة عن مكان محجوز في ذاكرة الكمبيوتر (RAM) نضع فيه قيمة معينة لنسترجعها أو نعدل عليها لاحقاً.</p>

<div class="tip-box">
  <strong>ملاحظة هامة:</strong> في لغة Python، لا نحتاج لتحديد نوع المتغير يدوياً؛ بل تتعرف عليه اللغة تلقائياً!
</div>

<h4>أنواع البيانات الأساسية:</h4>
<ul>
  <li><code>int</code>: الأرقام الصحيحة مثل <code>age = 16</code></li>
  <li><code>float</code>: الأرقام العشرية مثل <code>score = 95.5</code></li>
  <li><code>str</code>: النصوص بين اقتباس مثل <code>name = "أحمد"</code></li>
  <li><code>bool</code>: القيم المنطقية <code>True</code> أو <code>False</code></li>
</ul>

<h4>مثال توضيحي:</h4>
<pre><code class="language-python">
# تعريف المتغيرات
student_name = "يوسف"
age = 16
grade = 98.5
is_passed = True

print("اسم الطالب:", student_name)
print("العمر:", age)
</code></pre>
""",
                video_asset_id=v_asset1.id,
                estimated_duration_minutes=25,
                order=1,
                passing_score=70.0,
                preview_status=True,
                publishing_status="published",
                required_video_percentage=80.0,
                required_practical_submission=True,
                required_quiz_pass=True
            )
            session.add(lesson1)
            session.commit()
            session.refresh(lesson1)

        print("Seeding Coding Problem for Lesson 1...")
        prob1 = session.query(CodingProblem).filter_by(lesson_id=lesson1.id).first()
        if not prob1:
            prob1 = CodingProblem(
                title="حاسبة المصروف الأسبوعي",
                arabic_statement="""اكتب برنامج بلغة Python يقوم بحساب إجمالي المصروف الأسبوعي لطالب.
يستقبل البرنامج دخل الطالب في اليوم الأول ودخله في باقي أيام الأسبوع السبعة ثم يطبع الناتج إجمالي المصروف.

المطلوب:
1. قراءة المصروف اليومي كعدد صحيح من الإدخال (input).
2. ضرب المصروف اليومي في 7.
3. طباعة الجملة: Total: [الناتج]""",
                difficulty="easy",
                course_id=course1.id,
                module_id=mod1.id,
                lesson_id=lesson1.id,
                starter_code={"python": "# اكتب كود Python هنا\ndaily = int(input())\n# احسب واطبع الناتج\n"},
                input_format="عدد صحيح يمثل المصروف اليومي",
                output_format="Total: [المجموع]",
                time_limit_seconds=2.0,
                memory_limit_mb=128,
                points=10
            )
            session.add(prob1)
            session.commit()
            session.refresh(prob1)

            # Test cases
            tc1 = TestCase(
                problem_id=prob1.id,
                input_data="20\n",
                expected_output="Total: 140",
                is_public=True,
                order=1,
                explanation="20 × 7 = 140"
            )
            tc2 = TestCase(
                problem_id=prob1.id,
                input_data="50\n",
                expected_output="Total: 350",
                is_public=False,
                order=2,
                explanation="50 × 7 = 350"
            )
            session.add_all([tc1, tc2])
            session.commit()

        print("Seeding Quiz for Lesson 1...")
        quiz1 = session.query(Quiz).filter_by(lesson_id=lesson1.id).first()
        if not quiz1:
            quiz1 = Quiz(
                title="اختبار قصير: المتغيرات وأنواع البيانات",
                description="اختبار مكون من 5 أسئلة لقياس مدى فهمك لدرس المتغيرات.",
                course_id=course1.id,
                module_id=mod1.id,
                lesson_id=lesson1.id,
                passing_score=70.0,
                time_limit_minutes=10,
                allowed_attempts=3,
                is_required=True
            )
            session.add(quiz1)
            session.commit()
            session.refresh(quiz1)

            # Questions
            q1 = Question(
                course_id=course1.id,
                lesson_id=lesson1.id,
                title="نوع المتغير الرقمي الصحيح",
                question_text="ما هو نوع البيانات المستخدم لتخزين الأعداد الصحيحة في Python؟",
                question_type="single_mcq",
                difficulty="easy",
                points=1.0,
                explanation="int هو الاختصار البرمجي لـ Integer بالأعداد الصحيحة."
            )
            session.add(q1)
            session.commit()
            session.refresh(q1)
            session.add_all([
                QuestionOption(question_id=q1.id, option_text="int", is_correct=True, order=1),
                QuestionOption(question_id=q1.id, option_text="float", is_correct=False, order=2),
                QuestionOption(question_id=q1.id, option_text="str", is_correct=False, order=3),
                QuestionOption(question_id=q1.id, option_text="bool", is_correct=False, order=4),
            ])

            q2 = Question(
                course_id=course1.id,
                lesson_id=lesson1.id,
                title="دالة الطباعة",
                question_text="أي دالة نستخدمها لطباعة المخرجات على الشاشة؟",
                question_type="single_mcq",
                difficulty="easy",
                points=1.0,
                explanation="تستخدم print() للطباعة في Python."
            )
            session.add(q2)
            session.commit()
            session.refresh(q2)
            session.add_all([
                QuestionOption(question_id=q2.id, option_text="print()", is_correct=True, order=1),
                QuestionOption(question_id=q2.id, option_text="input()", is_correct=False, order=2),
                QuestionOption(question_id=q2.id, option_text="output()", is_correct=False, order=3),
                QuestionOption(question_id=q2.id, option_text="echo()", is_correct=False, order=4),
            ])

            # Connect quiz questions
            session.add_all([
                QuizQuestion(quiz_id=quiz1.id, question_id=q1.id, order=1),
                QuizQuestion(quiz_id=quiz1.id, question_id=q2.id, order=2),
            ])
            session.commit()

        print("Seeding Lesson 2...")
        lesson2 = session.query(Lesson).filter_by(module_id=mod1.id, order=2).first()
        if not lesson2:
            lesson2 = Lesson(
                module_id=mod1.id,
                title="الشروط واتخاذ القرار (If Statements)",
                slug="if-statements-and-decisions",
                description="تعلم استخدام If و Else لاتخاذ القرارات في البرنامج بناءً على الشروط.",
                rich_content="<h4>الجمل الشرطية If/Else</h4><p>تسمح لنا الجمل الشرطية بتنفيذ كود معين فقط عند تحقق شرط محدد.</p>",
                estimated_duration_minutes=30,
                order=2,
                passing_score=70.0,
                publishing_status="published"
            )
            session.add(lesson2)
            session.commit()
            session.refresh(lesson2)

        print("Seeding Lesson 3...")
        lesson3 = session.query(Lesson).filter_by(module_id=mod1.id, order=3).first()
        if not lesson3:
            lesson3 = Lesson(
                module_id=mod1.id,
                title="الحلقات التكرارية (Loops)",
                slug="loops-and-iterations",
                description="تعلم تكرار الأوامر باستخدام For Loop و While Loop في Python.",
                rich_content="<h4>الحلقات التكرارية</h4><p>نستخدم الحلقات عند الحاجة لتكرار تنفيذ كود عدد من المرات.</p>",
                estimated_duration_minutes=35,
                order=3,
                passing_score=70.0,
                publishing_status="published"
            )
            session.add(lesson3)
            session.commit()

        print("Seeding Active Enrolment for Student 1...")
        enrol1 = session.query(Enrolment).filter_by(student_id=student1.id, course_id=course1.id).first()
        if not enrol1:
            enrol1 = Enrolment(
                student_id=student1.id,
                course_id=course1.id,
                status="active",
                source="admin_assignment",
                access_start=datetime.utcnow(),
                access_expiry=datetime.utcnow() + timedelta(days=365)
            )
            session.add(enrol1)
            session.commit()

            # Add progress
            lp1 = LessonProgress(
                student_id=student1.id,
                lesson_id=lesson1.id,
                status="available",
                theory_opened=True
            )
            session.add(lp1)
            session.commit()

        print("Seeding Pending Payment for Student 2...")
        pay2 = session.query(Payment).filter_by(student_id=student2.id, course_id=course1.id).first()
        if not pay2:
            pay2 = Payment(
                reference_code="PAY-100200300",
                student_id=student2.id,
                course_id=course1.id,
                amount_expected=180.0,
                amount_submitted=180.0,
                payment_method="instapay",
                sender_identifier="01022222222",
                receipt_file_key="receipts/demo_receipt.png",
                student_note="تم التحويل عن طريق انستا باي",
                status="pending_review",
                submitted_at=datetime.utcnow()
            )
            session.add(pay2)
            session.commit()

        print("Seed completed successfully!")
    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        session.close()

if __name__ == "__main__":
    seed_db()
