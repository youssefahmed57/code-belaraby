"use client";

import Link from "next/link";
import { ShieldCheck, FileText, ArrowRight } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Link href="/" className="p-2 rounded-xl bg-navy-800 text-slate-300 hover:text-white transition-colors">
          <ArrowRight className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-extrabold text-white">الشروط والأحكام وسياسة الاستخدام</h1>
          <p className="text-sm text-slate-400">منصة كود جيرني أكاديمي (Code Journey Academy)</p>
        </div>
      </div>

      <div className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-6 text-slate-300 text-sm leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-blue" />
            1. القبول بالشروط
          </h2>
          <p>
            بمجرد إنشاء حسابك أو استخدام منصة كود جيرني أكاديمي، فإنك تقر بالموافقة الكاملة على جميع الشروط والأحكام الموضحة هنا وعلى الامتثال للقوانين واللوائح المنظمة.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-blue" />
            2. حساب الطالب والمسؤولية
          </h2>
          <p>
            يلتزم الطالب بتقديم بيانات صحيحة ومحدثة عند التسجيل (شاملة الاسم ورقم الهاتف المصري). الحساب شخصي ولا يجوز مشاركة بيانات الدخول مع أي طرف آخر.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-blue" />
            3. حقوق الملكية الفكرية
          </h2>
          <p>
            جميع المحاضرات المرئية، الأكواد البرمجية، والاختبارات المتاحة بالمنصة هي ملكية فكرية حصرية للمحاضر يوسف أحمد صبحي عابدين. يمنع منعا باتا تسجيل المحاضرات أو إعادة توزيعها.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-brand-blue" />
            4. سياسة الدفع والاشتراكات
          </h2>
          <p>
            يتم تفعيل اشتراك الكورسات بعد مراجعة إيصال التحويل اليدوي (عبر InstaPay أو فودافون كاش) وتأكيد الطلب من إدارة المنصة خلال مدة أقصاها 24 ساعة.
          </p>
        </section>
      </div>
    </div>
  );
}
