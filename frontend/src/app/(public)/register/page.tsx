"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { User, Phone, Lock, BookOpen, AlertCircle, CheckCircle2 } from "lucide-react";

export default function RegisterPage() {
  const [form, setForm] = useState({
    arabic_name: "",
    phone_number: "",
    email: "",
    password: "",
    password_confirm: "",
    grade_level: "first_secondary",
    parent_name: "",
    parent_phone: "",
    agree_terms: false
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.agree_terms) {
      setError("يجب الموافقة على شروط الاستخدام وسياسة الخصوصية.");
      return;
    }
    if (form.password !== form.password_confirm) {
      setError("كلمات المرور غير متطابقة.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await api.post("/auth/register", form);
      const { access_token, user, role } = res.data;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("user_info", JSON.stringify({ ...user, role }));

      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(err.response?.data?.detail || "تعذر إنشاء الحساب. يرجى التأكد من أن رقم الهاتف جديد ولم يُسجل من قبل.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-xl w-full space-y-8 glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl relative">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-white">إنشاء حساب طالب جديد</h2>
          <p className="mt-2 text-sm text-slate-400">انضم إلى أكاديمية كود جيرني وابدأ التعلم العملي اليوم</p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">اسم الطالب بالكامل (عربي)</label>
              <input
                id="arabic_name"
                type="text"
                required
                value={form.arabic_name}
                onChange={(e) => setForm({ ...form, arabic_name: e.target.value })}
                placeholder="أحمد محمود السيد"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">رقم هاتف الطالب (واتساب)</label>
              <input
                id="phone_number"
                type="text"
                required
                value={form.phone_number}
                onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                placeholder="01011111111"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">الصف الدراسي</label>
              <select
                id="grade_level"
                value={form.grade_level}
                onChange={(e) => setForm({ ...form, grade_level: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue transition-colors"
              >
                <option value="first_secondary">الصف الأول الثانوي</option>
                <option value="second_secondary">الصف الثاني الثانوي</option>
                <option value="beginner">مبتدئ في البرمجة</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">البريد الإلكتروني (اختياري)</label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="student@example.com"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">كلمة المرور</label>
              <input
                id="password"
                type="password"
                required
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">تأكيد كلمة المرور</label>
              <input
                id="password_confirm"
                type="password"
                required
                value={form.password_confirm}
                onChange={(e) => setForm({ ...form, password_confirm: e.target.value })}
                placeholder="••••••••"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
              />
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <input
              type="checkbox"
              id="terms"
              checked={form.agree_terms}
              onChange={(e) => setForm({ ...form, agree_terms: e.target.checked })}
              className="w-4 h-4 rounded border-slate-700 bg-navy-900 text-brand-blue focus:ring-brand-blue"
            />
            <label htmlFor="terms" className="text-xs text-slate-400">
              أوافق على الشروط والأحكام وسياسة الخصوصية الخاصة بالمنصة.
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-base shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? "جاري إنشاء الحساب..." : "تأكيد وإنشاء الحساب"}
          </button>
        </form>
      </div>
    </div>
  );
}
