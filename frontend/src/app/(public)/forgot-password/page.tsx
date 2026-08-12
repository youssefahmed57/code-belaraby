"use client";

import Link from "next/link";
import { useState } from "react";
import { AlertCircle, ArrowLeft, Mail } from "lucide-react";

import { api } from "@/lib/api";


export default function ForgotPasswordPage() {
  const [identifier, setIdentifier] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (loading) return;

    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await api.post("/auth/forgot-password", { identifier: identifier.trim() });
      setSuccessMessage(
        response.data?.message ||
          "إذا كان الحساب موجوداً، فسيتم إرسال تعليمات إعادة تعيين كلمة المرور إلى وسيلة التواصل المسجلة."
      );
    } catch (err: any) {
      setError(err.response?.data?.detail || "تعذر إرسال طلب إعادة التعيين حالياً.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-extrabold text-white">إعادة تعيين كلمة المرور</h1>
          <p className="text-sm text-slate-400">
            أدخل البريد الإلكتروني أو رقم الهاتف المسجل وسنرسل لك تعليمات إعادة التعيين.
          </p>
        </div>

        {error ? (
          <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        {successMessage ? (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm">
            {successMessage}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-2">البريد الإلكتروني أو رقم الهاتف</label>
            <div className="relative">
              <input
                id="forgot_identifier"
                type="text"
                required
                dir="ltr"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pl-10 text-left"
                placeholder="student@example.com"
              />
              <Mail className="w-5 h-5 text-slate-500 absolute left-3 top-3.5" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-base shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50"
          >
            {loading ? "جارٍ الإرسال..." : "إرسال تعليمات إعادة التعيين"}
          </button>
        </form>

        <Link href="/login" className="inline-flex items-center gap-2 text-sm text-brand-blue hover:underline">
          <ArrowLeft className="w-4 h-4" />
          العودة إلى تسجيل الدخول
        </Link>
      </div>
    </div>
  );
}
