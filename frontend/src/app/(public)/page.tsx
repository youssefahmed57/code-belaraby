"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Code2, CheckCircle2, PlayCircle, Terminal, MessageCircle,
  Sparkles, Award, ArrowLeft, GraduationCap, ShieldCheck, ChevronDown, Phone, Mail, MapPin,
  BookOpen, Clock, Zap, ArrowUpRight
} from "lucide-react";

export default function HomePage() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const whatsappMessage = encodeURIComponent(
    "السلام عليكم، أرغب في الاستفسار عن كورسات البرمجة للصف الأول والثاني الثانوي."
  );

  return (
    <div className="relative overflow-hidden">
      {/* Subtle Background glowing shapes */}
      <div className="absolute top-0 right-1/4 w-[450px] h-[450px] bg-brand-blue/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-1/3 left-10 w-[350px] h-[350px] bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Floating WhatsApp CTA */}
      <a
        href={`https://wa.me/201001340533?text=${whatsappMessage}`}
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-50 p-3.5 min-h-[44px] min-w-[44px] rounded-full bg-emerald-500 hover:bg-emerald-600 text-white shadow-xl shadow-emerald-500/30 transition-all hover:scale-105 flex items-center justify-center gap-2 group"
        title="تواصل معنا عبر الواتساب"
      >
        <MessageCircle className="w-6 h-6" />
        <span className="max-w-0 overflow-hidden whitespace-nowrap group-hover:max-w-xs transition-all duration-300 text-xs font-bold pl-1">
          تواصل واتساب مباشر
        </span>
      </a>

      {/* 1. Hero Section (Two Column Compact Layout) */}
      <section className="relative py-12 md:py-16 border-b border-slate-800/60 bg-navy-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            
            {/* Right Column: Arabic Headline & Description */}
            <div className="lg:col-span-7 space-y-5 text-right">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-blue/10 border border-brand-blue/30 text-brand-blue text-xs font-bold glow-blue">
                <Sparkles className="w-4 h-4" />
                <span>المنصة التعليمية الأولى لبرمجة الثانوية العامة</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white leading-tight">
                ابدأ رحلتك في عالم البرمجة <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-blue via-cyan-400 to-blue-500">بلغة Python</span>
              </h1>

              <p className="text-sm sm:text-base text-slate-200 leading-relaxed max-w-2xl">
                مناهج برمجية مبسطة مخصصة لطلاب الصف الأول والثاني الثانوي والمبتدئين في مصر، تمكنك من التفكير المنطقي وكتابة الكود واجتياز التحديات بنجاح.
              </p>

              <div className="flex flex-wrap items-center gap-3.5 pt-1">
                <Link
                  href="/register"
                  className="px-6 py-3.5 min-h-[44px] rounded-xl bg-gradient-to-r from-brand-blue via-blue-600 to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-sm shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] flex items-center justify-center gap-2"
                >
                  <span>ابسط رحلتك واحجز الآن</span>
                  <ArrowLeft className="w-4 h-4" />
                </Link>

                <Link
                  href="/courses"
                  className="px-6 py-3.5 min-h-[44px] rounded-xl bg-navy-900 hover:bg-navy-800 text-slate-100 hover:text-white font-semibold text-sm border border-slate-800 transition-colors flex items-center justify-center gap-2"
                >
                  <PlayCircle className="w-4 h-4 text-cyan-400" />
                  <span>تصفح الكورسات</span>
                </Link>
              </div>

              {/* Trust Indicators */}
              <div className="pt-5 grid grid-cols-3 gap-3 border-t border-slate-800/80 max-w-xl">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-brand-blue/10 border border-brand-blue/30 flex items-center justify-center shrink-0">
                    <Terminal className="w-3.5 h-3.5 text-brand-blue" />
                  </div>
                  <div className="text-xs">
                    <p className="font-bold text-white">تطبيق عملي</p>
                    <p className="text-slate-300">محرر Monaco مدمج</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-cyan-400/10 border border-cyan-400/30 flex items-center justify-center shrink-0">
                    <Zap className="w-3.5 h-3.5 text-cyan-400" />
                  </div>
                  <div className="text-xs">
                    <p className="font-bold text-white">تصحيح آلي</p>
                    <p className="text-slate-300">Judge0 Sandbox</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-amber-400/10 border border-amber-400/30 flex items-center justify-center shrink-0">
                    <Award className="w-3.5 h-3.5 text-amber-400" />
                  </div>
                  <div className="text-xs">
                    <p className="font-bold text-white">دعم 24/7</p>
                    <p className="text-slate-300">متابعة واتساب</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Left Column: Code Preview Card */}
            <div className="lg:col-span-5">
              <div className="rounded-2xl glass-card p-5 border border-slate-800 shadow-xl relative">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
                  <div className="flex items-center gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></div>
                    <div className="w-2.5 h-2.5 rounded-full bg-green-500/80"></div>
                  </div>
                  <span className="text-xs font-mono text-slate-300">lesson_01_variables.py</span>
                </div>

                <div className="bg-navy-950 rounded-xl p-4 font-mono text-xs text-slate-200 space-y-1.5 dir-ltr text-left border border-slate-800/80">
                  <p className="text-slate-400"># كورس البرمجة للصف الأول الثانوي</p>
                  <p><span className="text-purple-400">student_name</span> = <span className="text-emerald-400">"طالب كود جيرني"</span></p>
                  <p><span className="text-purple-400">score</span> = <span className="text-cyan-400">100</span></p>
                  <p className="pt-1"><span className="text-blue-400">if</span> score &gt;= <span className="text-cyan-400">50</span>:</p>
                  <p className="pl-4 text-emerald-400">print("مبروك لقد اجتزت التحدي بنجاح!")</p>
                </div>

                <div className="mt-3 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>حالة التنفيذ: Accepted (100%)</span>
                  </div>
                  <span className="text-slate-300 font-mono">0.04s</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 2. Instructor Section (Subtle Background Alternation) */}
      <section id="instructor" className="scroll-mt-24 py-12 md:py-16 bg-navy-900/60 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-1.5">عن المحاضر والخبرات</h2>
            <p className="text-slate-300 text-xs sm:text-sm">تعرف على المحاضر يوسف أحمد صبحي عابدين ورؤية الأكاديمية</p>
          </div>

          <div className="glass-card p-6 md:p-10 rounded-3xl border border-slate-800 shadow-lg">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-4 text-center space-y-3">
                <div className="w-32 h-32 mx-auto rounded-3xl bg-gradient-to-tr from-brand-blue to-cyan-400 p-1 shadow-xl">
                  <div className="w-full h-full bg-navy-950 rounded-[22px] flex items-center justify-center">
                    <GraduationCap className="w-14 h-14 text-cyan-400" />
                  </div>
                </div>
                <h3 className="text-xl md:text-2xl font-black text-white">يوسف أحمد صبحي عابدين</h3>
                <p className="text-xs sm:text-sm font-semibold text-brand-blue">خريج كلية الحاسبات والذكاء الاصطناعي</p>
                <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-950 border border-slate-800 text-xs text-slate-200">
                  <ShieldCheck className="w-4 h-4 text-green-400" />
                  <span>محاضر معتمد لمناهج الثانوي</span>
                </div>
              </div>

              <div className="lg:col-span-8 space-y-4 text-slate-200 leading-relaxed text-right">
                <h3 className="text-lg md:text-xl font-bold text-white">رؤيتنا في تبسيط علوم الحاسب للمرحلة الثانوية</h3>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                  نهدف بالمنصة إلى نقل الطالب المصري من مجرد حفظ المفاهيم والنظريات، إلى كتابة الكود البرمجي بنفسه وتجربة الأخطاء وإصلاحها وحل المشكلات بطرق منطقية تفاعلية.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                  <div className="p-4 rounded-xl bg-navy-950/80 border border-slate-800/80 flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-brand-blue shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-white text-xs sm:text-sm">تطبيق عملي مباشر</h4>
                      <p className="text-xs text-slate-300">محرر كود Monaco مدمج في كل درس لتجربة الكود فوراً.</p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-navy-950/80 border border-slate-800/80 flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-bold text-white text-xs sm:text-sm">متابعة الاشتراكات</h4>
                      <p className="text-xs text-slate-300">تفعيل فوري عبر فودافون كاش وانستا باي بكل سهولة.</p>
                    </div>
                  </div>
                </div>

                <div className="pt-1 flex flex-wrap gap-4 text-xs font-semibold text-slate-300">
                  <span>للتواصل المباشر: <strong className="text-white font-mono" dir="ltr">01001340533</strong></span>
                  <span>•</span>
                  <span>رقم إضافي: <strong className="text-white font-mono" dir="ltr">01008168639</strong></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Pricing and Courses Section */}
      <section id="pricing" className="scroll-mt-24 py-12 md:py-16 bg-navy-950 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-1.5">باقات الأسعار</h2>
            <p className="text-slate-300 text-xs sm:text-sm max-w-xl mx-auto">اختر الكورس المناسب لصفك الدراسي وابدأ التعلم الفوري</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
            {/* Course Card 1 */}
            <div className="glass-card p-6 md:p-8 rounded-3xl border border-slate-800 glass-card-hover h-full flex flex-col justify-between space-y-5">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 rounded-full bg-brand-blue/20 text-brand-blue text-xs font-bold border border-brand-blue/30">
                    الصف الأول الثانوي
                  </span>
                  <div className="text-left">
                    <span className="text-2xl font-black text-white">180 <span className="text-xs text-slate-300 font-normal">ج.م</span></span>
                    <span className="text-xs text-slate-400 line-through block">250 ج.م</span>
                  </div>
                </div>

                <h3 className="text-xl font-bold text-white">البرمجة والذكاء الاصطناعي – Python</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  كورس شامل لتأسيس طلاب أولى ثانوي في لغة Python، الجمل الشرطية، الحلقات التكرارية، وبناء حاسبة برمجية وتطبيقات عملي.
                </p>

                <div className="flex items-center gap-4 text-xs text-slate-300 border-t border-b border-slate-800/80 py-3">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-brand-blue" />
                    <span>8 أسابيع</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <BookOpen className="w-4 h-4 text-cyan-400" />
                    <span>12 درس عملي</span>
                  </div>
                </div>

                <ul className="space-y-2 text-xs text-slate-200">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-blue shrink-0" />
                    <span>المتغيرات وأنواع البيانات Python</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-blue shrink-0" />
                    <span>الشروط واختيار القرارات If / Else</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-blue shrink-0" />
                    <span>تحديات برمجية واختبارات تفاعلية</span>
                  </li>
                </ul>
              </div>

              <Link
                href="/courses/python-first-secondary"
                className="w-full py-3.5 min-h-[44px] rounded-xl bg-brand-blue hover:bg-brand-blueHover text-white font-bold text-center text-sm shadow-md transition-all flex items-center justify-center gap-1"
              >
                <span>تفاصيل الكورس والتسجيل</span>
                <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Course Card 2 */}
            <div className="glass-card p-6 md:p-8 rounded-3xl border border-slate-800 glass-card-hover h-full flex flex-col justify-between space-y-5">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="px-3 py-1 rounded-full bg-cyan-400/20 text-cyan-400 text-xs font-bold border border-cyan-400/30">
                    الصف الثاني الثانوي (توضيحي)
                  </span>
                  <div className="text-left">
                    <span className="text-2xl font-black text-white">220 <span className="text-xs text-slate-300 font-normal">ج.م</span></span>
                    <span className="text-xs text-slate-400 line-through block">300 ج.م</span>
                  </div>
                </div>

                <h3 className="text-xl font-bold text-white">تطوير المواقع وتأسيس الويب</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  مقدمة احترافية في HTML5 و CSS3 و JavaScript لبناء الصفحات وتصميم واجهات تفاعلية جذابة.
                </p>

                <div className="flex items-center gap-4 text-xs text-slate-300 border-t border-b border-slate-800/80 py-3">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-cyan-400" />
                    <span>10 أسابيع</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <BookOpen className="w-4 h-4 text-cyan-400" />
                    <span>15 درس عملي</span>
                  </div>
                </div>

                <ul className="space-y-2 text-xs text-slate-200">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                    <span>هيكلة مواقع الويب باستخدام HTML5</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                    <span>تنسيق الصفحات والألوان CSS3</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0" />
                    <span>التفاعلية والبرمجة بـ JavaScript</span>
                  </li>
                </ul>
              </div>

              <Link
                href="/courses/web-second-secondary-demo"
                className="w-full py-3.5 min-h-[44px] rounded-xl bg-navy-900 hover:bg-navy-800 text-cyan-400 font-bold border border-slate-800 text-center text-sm transition-all flex items-center justify-center gap-1"
              >
                <span>تصفح المحتوى التوضيحي</span>
                <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>

          </div>
        </div>
      </section>

      {/* 4. How it Works Section */}
      <section id="how-it-works" className="scroll-mt-24 py-12 md:py-16 bg-navy-900/60 border-b border-slate-800/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-1.5">كيف نعمل</h2>
            <p className="text-slate-300 text-xs sm:text-sm max-w-xl mx-auto">4 خطوات بسيطة تبدأ بها رحلتك البرمجية معنا</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-2.5">
              <div className="w-11 h-11 rounded-2xl bg-brand-blue/20 text-brand-blue flex items-center justify-center font-black text-lg mx-auto">1</div>
              <h3 className="text-sm font-bold text-white">أنشئ حسابك</h3>
              <p className="text-xs text-slate-300 leading-relaxed">سجل بياناتك ورقم هاتفك المصري بضغطات بسيطة.</p>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-2.5">
              <div className="w-11 h-11 rounded-2xl bg-cyan-400/20 text-cyan-400 flex items-center justify-center font-black text-lg mx-auto">2</div>
              <h3 className="text-sm font-bold text-white">اختر الكورس والدفع</h3>
              <p className="text-xs text-slate-300 leading-relaxed">ارفع إيصال التحويل عبر فودافون كاش أو انستا باي.</p>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-2.5">
              <div className="w-11 h-11 rounded-2xl bg-purple-400/20 text-purple-400 flex items-center justify-center font-black text-lg mx-auto">3</div>
              <h3 className="text-sm font-bold text-white">التعلم والتطبيق</h3>
              <p className="text-xs text-slate-300 leading-relaxed">شاهد الشرح وطبق الكود بداخل محرر Monaco المعزول.</p>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 text-center space-y-2.5">
              <div className="w-11 h-11 rounded-2xl bg-emerald-400/20 text-emerald-400 flex items-center justify-center font-black text-lg mx-auto">4</div>
              <h3 className="text-sm font-bold text-white">التقييم والفتح الآلي</h3>
              <p className="text-xs text-slate-300 leading-relaxed">اجتز الكويز ليفتح لك الدرس التالي تلقائياً.</p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. FAQ Section */}
      <section id="faq" className="scroll-mt-24 py-12 md:py-16 bg-navy-950 border-b border-slate-800/60">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-1.5">الأسئلة الشائعة</h2>
            <p className="text-slate-300 text-xs sm:text-sm">أكثر الأسئلة تكراراً حول كيفية التسجيل واجتياز التحديات</p>
          </div>

          <div className="space-y-3">
            {[
              {
                q: "كيف يمكنني دفع قيمة الاشتراك والدخول للكورس؟",
                a: "بعد إنشاء الحساب واختيار الكورس، يمكنك التحويل عبر انستا باي أو فودافون كاش على رقم المنصة (01001340533)، ثم رفع صورة الإيصال ليتم تفعيل الكورس لك فوراً."
              },
              {
                q: "هل الكود يشتغل على الموبايل أم يفضل كمبيوتر؟",
                a: "محرر الكود بالمنصة متوافق مع الموبايل والتابلت والكمبيوتر، مما يتيح لك حل التحديات البرمجية من أي جهاز."
              },
              {
                q: "كيف يفتح الدرس التالي تلقائياً؟",
                a: "يفتح الدرس التالي فور مشاهدتك لـ 80% من الفيديو، قراءة الشرح النظري، واجتياز كويز الدرس بنسبة 70% أو أكثر."
              }
            ].map((faq, idx) => (
              <div key={idx} className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full p-4 md:p-5 text-right font-bold text-white flex items-center justify-between hover:text-brand-blue transition-colors text-xs sm:text-sm min-h-[44px]"
                >
                  <span>{faq.q}</span>
                  <ChevronDown className={`w-5 h-5 text-slate-300 transition-transform ${openFaq === idx ? "rotate-180 text-brand-blue" : ""}`} />
                </button>
                {openFaq === idx && (
                  <div className="px-4 md:px-5 pb-4 text-slate-300 text-xs leading-relaxed border-t border-slate-800/60 pt-3">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 6. Dedicated Contact Section */}
      <section id="contact" className="scroll-mt-24 py-12 md:py-16 bg-navy-900/60">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold text-white mb-1.5">تواصل معنا</h2>
            <p className="text-slate-300 text-xs sm:text-sm">فريق الدعم والمدرس المباشر في خدمتك طوال الأسبوع</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
              <Phone className="w-6 h-6 text-brand-blue mx-auto" />
              <h3 className="font-bold text-white text-xs sm:text-sm">الاتصال والواتساب</h3>
              <p className="text-xs text-slate-300 font-mono" dir="ltr">01001340533 / 01008168639</p>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
              <Mail className="w-6 h-6 text-cyan-400 mx-auto" />
              <h3 className="font-bold text-white text-xs sm:text-sm">البريد الإلكتروني</h3>
              <p className="text-xs text-slate-300 font-mono">support@codejourney.academy</p>
            </div>

            <div className="glass-card p-5 rounded-2xl border border-slate-800 space-y-2">
              <MapPin className="w-6 h-6 text-amber-400 mx-auto" />
              <h3 className="font-bold text-white text-xs sm:text-sm">العنوان والمقر</h3>
              <p className="text-xs text-slate-300">جمهورية مصر العربية</p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
