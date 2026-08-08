"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { User, Phone, Lock, BookOpen, AlertCircle, CheckCircle2, Eye, EyeOff, Check, X } from "lucide-react";

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

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Live password validation criteria
  const isMinLength = form.password.length >= 8;
  const hasNumber = /\d/.test(form.password);
  const isMatching = form.password.length > 0 && form.password === form.password_confirm;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    if (!form.agree_terms) {
      setError("يرجى الموافقة على الشروط والأحكام وسياسة الخصوصية للمتابعة.");
      return;
    }
    if (!isMinLength || !hasNumber) {
      setError("يرجى التأكد من استيفاء شروط كلمة المرور (8 أحرف وتحتوي على رقم).");
      return;
    }
    if (!isMatching) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const cleanData = {
        ...form,
        phone_number: form.phone_number.trim(),
        email: form.email.trim()
      };
      const res = await api.post("/auth/register", cleanData);
      const { access_token, user, role } = res.data;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("user_info", JSON.stringify({ ...user, role }));

      setSuccessMsg("✓ تم إنشاء حسابك بنجاح! جاري نقلك إلى لوحة الطالب...");
      setTimeout(() => {
        window.location.href = "/dashboard";
      }, 1500);
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
          <p className="mt-2 text-sm text-slate-400">انضم إلى كود بالعربي وابدأ رحلتك في البرمجة اليوم</p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-3 font-bold">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{successMsg}</span>
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
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors text-right"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">رقم هاتف الطالب (واتساب)</label>
              <input
                id="phone_number"
                type="text"
                required
                dir="ltr"
                value={form.phone_number}
                onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                placeholder="01011111111"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors text-left"
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
                dir="ltr"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="student@example.com"
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors text-left"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">كلمة المرور</label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  dir="ltr"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pr-10 text-left"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3.5 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">تأكيد كلمة المرور</label>
              <div className="relative">
                <input
                  id="password_confirm"
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  dir="ltr"
                  value={form.password_confirm}
                  onChange={(e) => setForm({ ...form, password_confirm: e.target.value })}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pr-10 text-left"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-3.5 text-slate-400 hover:text-white"
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>

          {/* Live Password Rules Indicator */}
          {form.password.length > 0 && (
            <div className="p-3 rounded-xl bg-navy-900 border border-slate-800 text-xs space-y-1.5">
              <p className="font-bold text-slate-300 mb-1">متطلبات كلمة المرور:</p>
              <div className="flex items-center gap-2">
                {isMinLength ? <Check className="w-4 h-4 text-emerald-400" /> : <X className="w-4 h-4 text-slate-500" />}
                <span className={isMinLength ? "text-emerald-400" : "text-slate-400"}>8 أحرف على الأقل</span>
              </div>
              <div className="flex items-center gap-2">
                {hasNumber ? <Check className="w-4 h-4 text-emerald-400" /> : <X className="w-4 h-4 text-slate-500" />}
                <span className={hasNumber ? "text-emerald-400" : "text-slate-400"}>تحتوي على رقم واحد على الأقل</span>
              </div>
              <div className="flex items-center gap-2">
                {isMatching ? <Check className="w-4 h-4 text-emerald-400" /> : <X className="w-4 h-4 text-slate-500" />}
                <span className={isMatching ? "text-emerald-400" : "text-slate-400"}>كلمتا المرور متطابقتان</span>
              </div>
            </div>
          )}

          {/* Restyled Custom Checkbox with Real Policy Links */}
          <div className="flex items-start gap-3 pt-2">
            <input
              type="checkbox"
              id="terms"
              checked={form.agree_terms}
              onChange={(e) => setForm({ ...form, agree_terms: e.target.checked })}
              className="mt-0.5 w-4 h-4 rounded border-slate-700 bg-navy-900 text-brand-blue focus:ring-brand-blue shrink-0 cursor-pointer"
            />
            <label htmlFor="terms" className="text-xs text-slate-300 leading-relaxed cursor-pointer select-none">
              أوافق على{" "}
              <Link href="/terms" target="_blank" className="text-brand-blue font-bold hover:underline">
                الشروط والأحكام
              </Link>{" "}
              و{" "}
              <Link href="/privacy" target="_blank" className="text-brand-blue font-bold hover:underline">
                سياسة الخصوصية
              </Link>{" "}
              الخاصة بـ كود بالعربي.
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
