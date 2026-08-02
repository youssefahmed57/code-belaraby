"use client";

import Link from "next/link";
import { RefreshCw, ArrowRight, CheckCircle2 } from "lucide-react";

export default function RefundPage() {
  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Link href="/" className="p-2 rounded-xl bg-navy-800 text-slate-300 hover:text-white transition-colors">
          <ArrowRight className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-extrabold text-white">سياسة الاسترجاع والاسترداد</h1>
          <p className="text-sm text-slate-400">منصة كود جيرني أكاديمي (Code Journey Academy)</p>
        </div>
      </div>

      <div className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-6 text-slate-300 text-sm leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-brand-blue" />
            1. شروط استرداد الرسوم
          </h2>
          <p>
            يمكن للطلاب المطالبة باسترداد كامل رسوم الاشتراك خلال 48 ساعة من تاريخ تفعيل الكورس بشرط عدم تجاوز نسبة مشاهدة المحتوى 15%.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-brand-blue" />
            2. طريقة طلب الاسترجاع
          </h2>
          <p>
            يتم تقديم طلب الاسترجاع بالتواصل المباشر مع إدارة المنصة عبر الواتساب على الرقم الرسمي `01001340533` وإرفاق بيانات الحساب وإيصال التحويل.
          </p>
        </section>
      </div>
    </div>
  );
}
