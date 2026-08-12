"use client";

import Link from "next/link";
import { useState } from "react";
import { AlertCircle, Eye, EyeOff, Lock, LogIn, Phone } from "lucide-react";

import { api } from "@/lib/api";
import { setStoredUser } from "@/lib/auth";


export default function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (loading) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.post("/auth/login", {
        identifier: identifier.trim(),
        password,
      });
      const { user, role } = response.data;
      setStoredUser({ ...user, role });

      if (role === "admin" || role === "super_admin") {
        window.location.href = "/admin";
      } else {
        window.location.href = "/dashboard";
      }
    } catch (err: any) {
      const status = err.response?.status;
      if (status === 401) {
        setError("رقم الهاتف أو كلمة المرور غير صحيحة.");
      } else if (status === 429) {
        setError(err.response?.data?.detail || "تم تأخير المحاولات مؤقتاً. يرجى المحاولة بعد قليل.");
      } else if (status >= 500) {
        setError("تعذر الاتصال بالخادم، يرجى المحاولة مرة أخرى.");
      } else {
        setError(err.response?.data?.detail || "فشل تسجيل الدخول. يرجى التحقق من البيانات والمحاولة مجدداً.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl relative">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-white">تسجيل الدخول</h2>
          <p className="mt-2 text-sm text-slate-400">أهلاً بك مجدداً في منصة كود بالعربي</p>
        </div>

        {error ? (
          <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-300 mb-2">رقم الهاتف أو البريد الإلكتروني</label>
              <div className="relative">
                <input
                  id="identifier"
                  type="text"
                  required
                  dir="ltr"
                  value={identifier}
                  onChange={(event) => setIdentifier(event.target.value)}
                  placeholder="01011111111"
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pl-10 text-left"
                />
                <Phone className="w-5 h-5 text-slate-500 absolute left-3 top-3.5" />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold text-slate-300">كلمة المرور</label>
                <Link href="/forgot-password" className="text-xs text-brand-blue hover:underline font-semibold">
                  نسيت كلمة المرور؟
                </Link>
              </div>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  dir="ltr"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="••••••••"
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pl-10 pr-10 text-left"
                />
                <Lock className="w-5 h-5 text-slate-500 absolute left-3 top-3.5" />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-3 top-3.5 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-base shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? "جارٍ تسجيل الدخول..." : "دخول الحساب"}
            <LogIn className="w-5 h-5" />
          </button>
        </form>

        <div className="text-center pt-2 border-t border-slate-800/80">
          <p className="text-xs text-slate-400">
            ليس لديك حساب بعد؟{" "}
            <Link href="/register" className="text-brand-blue font-bold hover:underline">
              إنشاء حساب جديد
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
