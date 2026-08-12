"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { AlertCircle, Check, Eye, EyeOff, KeyRound } from "lucide-react";

import { api } from "@/lib/api";


function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = useMemo(() => searchParams.get("token") || "", [searchParams]);

  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const isMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const passwordsMatch = password.length > 0 && password === passwordConfirm;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (loading) return;
    if (!token) {
      setError("رابط إعادة التعيين غير صالح أو ناقص.");
      return;
    }
    if (!isMinLength || !hasNumber) {
      setError("كلمة المرور يجب أن تكون 8 أحرف على الأقل وتحتوي على رقم واحد على الأقل.");
      return;
    }
    if (!passwordsMatch) {
      setError("كلمتا المرور غير متطابقتين.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await api.post("/auth/reset-password", {
        token,
        new_password: password,
        password_confirm: passwordConfirm,
      });
      setSuccessMessage(response.data?.message || "تم تحديث كلمة المرور بنجاح.");
      window.setTimeout(() => {
        router.push("/login");
      }, 1200);
    } catch (err: any) {
      setError(err.response?.data?.detail || "تعذر إعادة تعيين كلمة المرور بهذا الرابط.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full glass-panel p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-extrabold text-white">تعيين كلمة مرور جديدة</h1>
          <p className="text-sm text-slate-400">أنشئ كلمة مرور جديدة ثم سجّل الدخول من جديد.</p>
        </div>

        {!token ? (
          <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm">
            رابط إعادة التعيين غير صالح أو منتهي الصلاحية.
          </div>
        ) : null}

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
            <label className="block text-xs font-bold text-slate-300 mb-2">كلمة المرور الجديدة</label>
            <div className="relative">
              <input
                id="reset_password"
                type={showPassword ? "text" : "password"}
                required
                dir="ltr"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pl-10 pr-10 text-left"
                placeholder="••••••••"
              />
              <KeyRound className="w-5 h-5 text-slate-500 absolute left-3 top-3.5" />
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                className="absolute right-3 top-3.5 text-slate-400 hover:text-white"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-2">تأكيد كلمة المرور</label>
            <div className="relative">
              <input
                id="reset_password_confirm"
                type={showPasswordConfirm ? "text" : "password"}
                required
                dir="ltr"
                value={passwordConfirm}
                onChange={(event) => setPasswordConfirm(event.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors pr-10 text-left"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPasswordConfirm((current) => !current)}
                className="absolute right-3 top-3.5 text-slate-400 hover:text-white"
              >
                {showPasswordConfirm ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {password.length > 0 ? (
            <div className="p-3 rounded-xl bg-navy-900 border border-slate-800 text-xs space-y-1.5">
              <div className="flex items-center gap-2 text-slate-300">
                <Check className={`w-4 h-4 ${isMinLength ? "text-emerald-400" : "text-slate-500"}`} />
                <span className={isMinLength ? "text-emerald-400" : "text-slate-400"}>8 أحرف على الأقل</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Check className={`w-4 h-4 ${hasNumber ? "text-emerald-400" : "text-slate-500"}`} />
                <span className={hasNumber ? "text-emerald-400" : "text-slate-400"}>تحتوي على رقم واحد على الأقل</span>
              </div>
              <div className="flex items-center gap-2 text-slate-300">
                <Check className={`w-4 h-4 ${passwordsMatch ? "text-emerald-400" : "text-slate-500"}`} />
                <span className={passwordsMatch ? "text-emerald-400" : "text-slate-400"}>كلمتا المرور متطابقتان</span>
              </div>
            </div>
          ) : null}

          <button
            type="submit"
            disabled={loading || !token}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-base shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50"
          >
            {loading ? "جارٍ تحديث كلمة المرور..." : "تحديث كلمة المرور"}
          </button>
        </form>

        <Link href="/login" className="inline-flex items-center gap-2 text-sm text-brand-blue hover:underline">
          العودة إلى تسجيل الدخول
        </Link>
      </div>
    </div>
  );
}


export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-slate-400">جارٍ تحميل الصفحة...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
