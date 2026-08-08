"use client";

import Link from "next/link";
import { Shield, ArrowRight, Lock } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-8">
      <div className="flex items-center gap-4">
        <Link href="/" className="p-2 rounded-xl bg-navy-800 text-slate-300 hover:text-white transition-colors">
          <ArrowRight className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-3xl font-extrabold text-white">سياسة الخصوصية وحماية البيانات</h1>
          <p className="text-sm text-slate-400">منصة كود بالعربي (Code Belaraby) • <span className="text-brand-blue font-medium">آخر تحديث: أغسطس 2026</span></p>
        </div>
      </div>

      <div className="glass-panel p-8 rounded-3xl border border-slate-800 space-y-6 text-slate-300 text-sm leading-relaxed">
        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-brand-blue" />
            1. البيانات التي نجمعها
          </h2>
          <p>
            نجمع البيانات الضرورية لتقديم الخدمة التعليمية فقط، وتتضمن: الاسم الثلاثي، رقم هاتف الواتساب المصري، الصف الدراسي، وسجلات تقدم الكورسات والإيصالات المرفوعة.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-brand-blue" />
            2. كيفية استخدام البيانات
          </h2>
          <p>
            تُستخدم بياناتك لإنشاء حساب الطالب، تفعيل الاشتراكات، حفظ تقدمك في الدروس والكويزات، والتواصل المباشر بشأن الدعم الفني والمحتوى التعليمي.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Lock className="w-5 h-5 text-brand-blue" />
            3. حماية البيانات والأمان
          </h2>
          <p>
            نلتزم بتطبيق وسائل تقنية وتنظيمية معتمدة ومناسبة لحماية بيانات المستخدمين وتأمين بيانات تسجيل الدخول ومنع الوصول غير المصرح به إليها.
          </p>
        </section>
      </div>
    </div>
  );
}
