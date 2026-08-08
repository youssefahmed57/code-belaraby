"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  BookOpen, Award, Flame, CheckCircle2, PlayCircle,
  FileCode, Clock, Sparkles, ArrowLeft, Layers
} from "lucide-react";

export default function StudentDashboard() {
  const [user, setUser] = useState<any>(null);
  const [summary, setSummary] = useState<any>({
    active_enrolment_count: 0,
    completed_lessons: 0,
    total_lessons: 0,
    average_quiz_score: 0,
    learning_streak_days: 0,
    courses: [],
    suggested_courses: []
  });
  const [payments, setPayments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("user_info");
      if (!stored) {
        window.location.href = "/login";
        return;
      }
      setUser(JSON.parse(stored));
    }

    async function fetchData() {
      try {
        const [resSummary, resPayments] = await Promise.all([
          api.get("/dashboard/summary"),
          api.get("/payments/my-payments")
        ]);
        setSummary(resSummary.data);
        setPayments(resPayments.data);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900 text-white p-8 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-brand-blue border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">جاري تحميل لوحة التحكم...</p>
        </div>
      </div>
    );
  }

  const latestPayment = payments.length > 0 ? payments[0] : null;

  const getExpiryText = (c: any) => {
    if (c.access_expiry) {
      try {
        const date = new Date(c.access_expiry);
        return `متاح حتى ${date.toLocaleDateString("ar-EG", { year: "numeric", month: "long", day: "numeric" })}`;
      } catch {
        return `متاح حتى ${c.access_expiry}`;
      }
    }
    return c.access_duration_days === 365 ? "صلاحية سنة كاملة" : `صلاحية ${c.access_duration_days || 365} يوم`;
  };

  return (
    <div className="min-h-screen bg-navy-900 text-white p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Welcome Header */}
        <div className="p-8 rounded-3xl glass-panel border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="space-y-2 z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-blue/10 border border-brand-blue/30 text-brand-blue text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5" />
              مرحباً بك في كود بالعربي
            </div>
            <h1 className="text-3xl font-extrabold text-white">
              أهلاً بك، {user?.arabic_name || "عزيزي الطالب"} 👋
            </h1>
            <p className="text-slate-400 text-sm">
              واصل تعلم البرمجة وحل التحديات لبناء مستقبل مشرق في الحاسبات والذكاء الاصطناعي.
            </p>
          </div>

          <div className="flex items-center gap-4 z-10">
            <Link
              href="/dashboard/playground"
              className="px-5 py-3 rounded-xl bg-navy-800 hover:bg-navy-700 border border-slate-700 text-white text-sm font-bold flex items-center gap-2 transition-colors"
            >
              <FileCode className="w-4 h-4 text-cyan-400" />
              محرر الكود المستقل
            </Link>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-brand-blue/20 flex items-center justify-center text-brand-blue">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-white">{summary.active_enrolment_count}</div>
              <div className="text-xs text-slate-400">الكورسات المشترك بها</div>
            </div>
          </div>

          <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center text-amber-500">
              <Flame className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-white">{summary.learning_streak_days} أيام</div>
              <div className="text-xs text-slate-400">سلسلة التعلم (Streak)</div>
            </div>
          </div>

          <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center text-green-500">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-white">{summary.completed_lessons}/{summary.total_lessons}</div>
              <div className="text-xs text-slate-400">الدروس المكتملة</div>
            </div>
          </div>

          <div className="p-6 rounded-2xl glass-panel border border-slate-800 flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-extrabold text-white">{summary.average_quiz_score}%</div>
              <div className="text-xs text-slate-400">متوسط درجات الاختبارات</div>
            </div>
          </div>
        </div>

        {/* Payment Status Notification Banner */}
        {latestPayment && latestPayment.status === "pending_review" && (
          <div className="p-6 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-4 text-amber-400">
            <Clock className="w-6 h-6 shrink-0 mt-1" />
            <div>
              <h4 className="font-bold text-base text-white">طلب الدفع قيد المراجعة ({latestPayment.reference_code})</h4>
              <p className="text-xs text-slate-300 mt-1">
                تم استلام إيصال التحويل بمبلغ {latestPayment.amount_submitted} ج.م وجاري مراجعته وتأكيده بواسطة الإدارة لتفعيل الكورس فوراً.
              </p>
            </div>
          </div>
        )}

        {/* Active Courses Section */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">الكورسات المتاحة والمفعلة</h2>
            <Link href="/courses" className="text-xs font-bold text-brand-blue hover:underline">
              عرض كافـة الكورسات
            </Link>
          </div>

          {summary.courses.length === 0 ? (
            <div className="p-8 rounded-3xl glass-panel border border-slate-800 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-navy-800 flex items-center justify-center mx-auto text-slate-400">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">لا توجد كورسات مفعلة حالياً</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                قم بالاشتراك في أحد الكورسات المتاحة لبدء رحلة التعلم وحل التحديات البرمجية.
              </p>
              <Link
                href="/courses"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-blue hover:bg-brand-blueHover text-white text-xs font-bold transition-colors"
              >
                تصفح الكورسات المتاحة
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {summary.courses.map((c: any) => (
                <div key={c.id} className="p-6 rounded-3xl glass-panel border border-slate-800 hover:border-brand-blue/40 transition-all flex flex-col justify-between space-y-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="px-3 py-1 rounded-full bg-brand-blue/20 text-brand-blue text-xs font-bold">
                        {c.grade_level === "first_secondary" ? "الصف الأول الثانوي" : "الصف الثاني الثانوي"}
                      </span>
                      <span className="text-xs font-semibold text-slate-400">
                        {getExpiryText(c)}
                      </span>
                    </div>
                    <h3 className="text-xl font-bold text-white">{c.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{c.short_description}</p>

                    {/* Progress Bar */}
                    <div className="space-y-1.5 pt-2">
                      <div className="flex items-center justify-between text-xs font-bold">
                        <span className="text-slate-300">نسبة الإنجاز</span>
                        <span className="text-brand-blue">{c.progress_percentage}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-navy-950 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-brand-blue to-cyan-400 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, Math.max(0, c.progress_percentage))}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <Link
                      href={`/dashboard/lessons/${c.next_lesson_slug || 'variables-and-data-types'}`}
                      className="px-6 py-3 rounded-xl bg-brand-blue hover:bg-brand-blueHover text-white font-bold text-sm shadow-lg shadow-blue-500/20 transition-colors flex items-center gap-2"
                    >
                      <PlayCircle className="w-4 h-4" />
                      متابعة التعلم
                    </Link>

                    {/* Status Badge */}
                    <div className="px-4 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" />
                      الاشتراك مفعّل
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Suggested / Promotional Courses Section */}
        {summary.suggested_courses && summary.suggested_courses.length > 0 && (
          <div className="space-y-6 pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-amber-400" />
                <h2 className="text-xl font-bold text-white">كورسات مقترحة</h2>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {summary.suggested_courses.map((sc: any) => (
                <div key={sc.id} className="p-6 rounded-3xl glass-panel border border-slate-800/80 hover:border-amber-500/30 transition-all flex flex-col justify-between space-y-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold">
                        {sc.grade_level === "first_secondary" ? "الصف الأول الثانوي" : "الصف الثاني الثانوي"}
                      </span>
                      <span className="text-sm font-extrabold text-emerald-400">
                        {sc.discount_price || sc.price} ج.م
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-white">{sc.title}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{sc.short_description}</p>
                  </div>

                  <div className="pt-2">
                    <Link
                      href={`/courses/${sc.slug}`}
                      className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-700 border border-slate-700 text-white font-bold text-xs transition-colors flex items-center justify-center gap-2"
                    >
                      عرض تفاصيل الكورس
                      <ArrowLeft className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
