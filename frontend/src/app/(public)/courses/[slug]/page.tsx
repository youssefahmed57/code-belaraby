"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { BookOpen, CheckCircle, Lock, PlayCircle, FileCode, ShieldCheck, ChevronLeft, UserCheck, AlertCircle } from "lucide-react";

interface Lesson {
  id: string;
  title: string;
  slug: string;
  video_duration_seconds?: number;
}

interface Module {
  id: string;
  title: string;
  lessons: Lesson[];
}

interface CourseDetails {
  id: string;
  title: string;
  slug: string;
  description: string;
  grade_level: string;
  price: number;
  instructor_name: string;
  modules: Module[];
}

export default function CourseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string;

  const [course, setCourse] = useState<CourseDetails | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCourseDetails() {
      if (!slug) return;
      try {
        const res = await api.get(`/courses/${slug}`);
        setCourse(res.data);
      } catch (err: any) {
        setError("الكورس المطلوب غير موجود أو غير متاح حالياً.");
      } finally {
        setLoading(false);
      }
    }
    fetchCourseDetails();
  }, [slug]);

  const handleEnroll = () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
    } else {
      router.push("/dashboard/payments");
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-blue"></div>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center text-center p-4">
        <AlertCircle className="w-16 h-16 text-brand-red mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">{error || "عفواً، الكورس غير موجود"}</h2>
        <Link href="/courses" className="mt-4 px-6 py-2.5 rounded-xl bg-brand-blue text-white font-bold">
          العودة للكتالوج
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8 space-y-10 max-w-7xl mx-auto">
      {/* Hero Details */}
      <div className="glass-panel p-8 md:p-12 rounded-3xl border border-slate-800 relative overflow-hidden">
        <div className="max-w-3xl space-y-6">
          <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-brand-blue/20 text-brand-blue border border-brand-blue/30">
            {course.grade_level === "first_secondary" ? "الصف الأول الثانوي" : "الصف الثاني الثانوي"}
          </span>
          <h1 className="text-3xl md:text-5xl font-black text-white leading-tight">
            {course.title}
          </h1>
          <p className="text-slate-300 text-base md:text-lg leading-relaxed">
            {course.description}
          </p>

          <div className="flex flex-wrap items-center gap-6 text-sm text-slate-400 pt-2">
            <div className="flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-brand-blue" />
              <span>المحاضر: {course.instructor_name || "يوسف أحمد صبحي عابدين"}</span>
            </div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-green-400" />
              <span>متابعة وتصحيح عملي مع الطالب</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grid: Syllabus + Enrollment Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Course Modules & Lessons (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-2xl font-bold text-white">منهج ومحتويات الكورس</h2>

          {course.modules && course.modules.length > 0 ? (
            course.modules.map((module, mIdx) => (
              <div key={module.id} className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
                <div className="bg-navy-900/80 p-4 px-6 border-b border-slate-800 flex justify-between items-center">
                  <h3 className="font-bold text-white text-base">
                    الوحدة {mIdx + 1}: {module.title}
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">
                    {module.lessons?.length || 0} دروس
                  </span>
                </div>

                <div className="divide-y divide-slate-800/50">
                  {module.lessons && module.lessons.map((lesson, lIdx) => (
                    <div key={lesson.id} className="p-4 px-6 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
                      <div className="flex items-center gap-3">
                        <PlayCircle className="w-5 h-5 text-brand-blue shrink-0" />
                        <div>
                          <p className="text-sm font-semibold text-slate-200">{lesson.title}</p>
                        </div>
                      </div>
                      <Lock className="w-4 h-4 text-slate-500 shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p className="text-slate-400 text-sm">سيتم إضافة محتوى الدروس قريباً.</p>
          )}
        </div>

        {/* Enrollment Card Sidebar (1 Col) */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-3xl border border-slate-800 sticky top-24 space-y-6 shadow-2xl">
            <div className="space-y-2">
              <span className="text-xs text-slate-400">سعر الكورس والتفعيل</span>
              <div className="text-3xl font-black text-white">
                {course.price} <span className="text-sm text-slate-400 font-normal">جنيه مصري</span>
              </div>
            </div>

            <ul className="space-y-3 text-sm text-slate-300">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                <span>وصول كامل لكافة المحاضرات والكويزات</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                <span>تطبيق عملي ومحرر كود Monaco معزول</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400 shrink-0" />
                <span>دفع يدوي فوري عبر InstaPay أو فودافون كاش</span>
              </li>
            </ul>

            <button
              onClick={handleEnroll}
              className="w-full py-4 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-base shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2"
            >
              <span>اشترك الآن وتفعل فوراً</span>
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
