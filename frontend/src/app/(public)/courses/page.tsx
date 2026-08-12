"use client";

import Link from "next/link";
import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { BookOpen, Search, Clock, Award, ChevronLeft, UserCheck, RefreshCw, AlertCircle } from "lucide-react";

interface Course {
  id: string;
  title: string;
  slug: string;
  description: string;
  grade_level: string;
  price: number;
  discount_price?: number | null;
  instructor_name: string;
  cover_image_url?: string;
  total_modules?: number;
  total_lessons?: number;
}

function CoursesContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const initialGrade = searchParams.get("grade") || "all";
  const initialQuery = searchParams.get("q") || "";

  const [courses, setCourses] = useState<Course[]>([]);
  const [filteredCourses, setFilteredCourses] = useState<Course[]>([]);
  const [gradeFilter, setGradeFilter] = useState<string>(initialGrade);
  const [searchQuery, setSearchQuery] = useState<string>(initialQuery);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  const fetchCourses = async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await api.get("/courses");
      setCourses(res.data);
      setFilteredCourses(res.data);
    } catch (err) {
      console.error("Failed to fetch courses catalog:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    let result = courses;
    if (gradeFilter !== "all") {
      result = result.filter((c) => c.grade_level === gradeFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (c) =>
          c.title.toLowerCase().includes(q) ||
          c.description.toLowerCase().includes(q)
      );
    }
    setFilteredCourses(result);

    // Sync URL parameters
    const params = new URLSearchParams();
    if (gradeFilter !== "all") params.set("grade", gradeFilter);
    if (searchQuery.trim()) params.set("q", searchQuery.trim());
    const newQueryStr = params.toString();
    const newUrl = newQueryStr ? `/courses?${newQueryStr}` : "/courses";
    router.replace(newUrl, { scroll: false });
  }, [gradeFilter, searchQuery, courses]);

  const getGradeBadge = (grade: string) => {
    switch (grade) {
      case "first_secondary":
        return "الصف الأول الثانوي";
      case "second_secondary":
        return "الصف الثاني الثانوي";
      default:
        return "جميع المستويات";
    }
  };

  return (
    <div className="min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-extrabold text-white sm:text-5xl">
            كتالوج الكورسات والمسارات البرمجية
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            مناهج برمجية مخصصة لطلاب المرحلة الثانوية في مصر مع تطبيق عملي مباشر ومتابعة شخصية
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row gap-4 justify-between items-center">
          <div className="relative w-full md:w-96">
            <input
              type="text"
              placeholder="ابحث عن كورس أو مادة دراسية..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 pr-11 rounded-xl bg-navy-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-brand-blue transition-colors"
            />
            <Search className="w-5 h-5 text-slate-500 absolute right-3.5 top-3.5" />
          </div>

          <div className="flex gap-2 w-full md:w-auto overflow-x-auto pb-2 md:pb-0">
            <button
              onClick={() => setGradeFilter("all")}
              className={`px-4 py-2.5 rounded-xl font-medium text-sm transition-all shrink-0 ${
                gradeFilter === "all"
                  ? "bg-brand-blue text-white shadow-lg shadow-blue-500/20"
                  : "bg-navy-800 text-slate-400 hover:text-white"
              }`}
            >
              جميع الصفوف
            </button>
            <button
              onClick={() => setGradeFilter("first_secondary")}
              className={`px-4 py-2.5 rounded-xl font-medium text-sm transition-all shrink-0 ${
                gradeFilter === "first_secondary"
                  ? "bg-brand-blue text-white shadow-lg shadow-blue-500/20"
                  : "bg-navy-800 text-slate-400 hover:text-white"
              }`}
            >
              الصف الأول الثانوي
            </button>
            <button
              onClick={() => setGradeFilter("second_secondary")}
              className={`px-4 py-2.5 rounded-xl font-medium text-sm transition-all shrink-0 ${
                gradeFilter === "second_secondary"
                  ? "bg-brand-blue text-white shadow-lg shadow-blue-500/20"
                  : "bg-navy-800 text-slate-400 hover:text-white"
              }`}
            >
              الصف الثاني الثانوي
            </button>
          </div>
        </div>

        {/* Courses Grid or Skeleton State */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-panel rounded-3xl border border-slate-800 p-6 space-y-4 animate-pulse">
                <div className="h-40 bg-navy-800 rounded-2xl"></div>
                <div className="h-6 bg-navy-800 rounded-lg w-3/4"></div>
                <div className="h-4 bg-navy-800 rounded-lg w-full"></div>
                <div className="h-4 bg-navy-800 rounded-lg w-2/3"></div>
                <div className="h-10 bg-navy-800 rounded-xl"></div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="py-16 text-center glass-panel rounded-2xl border border-slate-800 space-y-4 max-w-md mx-auto">
            <AlertCircle className="w-12 h-12 text-brand-red mx-auto" />
            <h3 className="text-xl font-bold text-white">تعذر تحميل الكورسات المتاحة</h3>
            <p className="text-slate-400 text-xs">يرجى التأكد من الاتصال بالإنترنت والمحاولة مجدداً.</p>
            <button
              onClick={fetchCourses}
              className="px-5 py-2.5 rounded-xl bg-brand-blue text-white font-bold text-xs inline-flex items-center gap-2 hover:bg-brand-blueHover transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span>إعادة المحاولة</span>
            </button>
          </div>
        ) : filteredCourses.length === 0 ? (
          <div className="py-20 text-center glass-panel rounded-2xl border border-slate-800">
            <BookOpen className="w-12 h-12 text-slate-500 mx-auto mb-3" />
            <h3 className="text-xl font-bold text-white mb-1">لا توجد كورسات مطابقة لفلتر البحث</h3>
            <p className="text-slate-400 text-sm">جرب اختيار صف آخر أو تغيير كلمة البحث.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredCourses.map((course) => (
              <div
                key={course.id}
                className="glass-panel rounded-3xl border border-slate-800 overflow-hidden flex flex-col justify-between hover:border-brand-blue/50 transition-all duration-300 group hover:-translate-y-1"
              >
                <div>
                  <div className="h-48 bg-gradient-to-br from-navy-800 to-slate-900 p-6 flex flex-col justify-between relative overflow-hidden">
                    <div className="absolute top-0 left-0 right-0 bottom-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-600/10 via-transparent to-transparent"></div>
                    <span className="inline-block px-3 py-1 rounded-full text-xs font-bold bg-brand-blue/20 text-brand-blue border border-brand-blue/30 w-fit">
                      {getGradeBadge(course.grade_level)}
                    </span>
                    <h3 className="text-xl font-bold text-white group-hover:text-brand-blue transition-colors line-clamp-2">
                      {course.title}
                    </h3>
                  </div>

                  <div className="p-6 space-y-4">
                    <p className="text-slate-400 text-sm line-clamp-3 leading-relaxed">
                      {course.description}
                    </p>

                    <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800 pt-4">
                      <div className="flex items-center gap-1.5">
                        <UserCheck className="w-4 h-4 text-brand-blue" />
                        <span>{course.instructor_name || "يوسف أحمد صبحي عابدين"}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Award className="w-4 h-4 text-yellow-500" />
                        <span>محتوى عملي تفاعلي</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-6 pt-0 space-y-4">
                  <div className="flex items-baseline justify-between">
                    <span className="text-xs text-slate-400">سعر الاشتراك</span>
                    <div className="text-left">
                      {course.discount_price != null ? (
                        <>
                          <div className="text-xs text-slate-500 line-through">{course.price} جنيه</div>
                          <span className="text-2xl font-black text-emerald-400">
                            {course.discount_price} <span className="text-xs text-slate-400 font-normal">جنية مصري</span>
                          </span>
                        </>
                      ) : (
                        <span className="text-2xl font-black text-white">
                          {course.price} <span className="text-xs text-slate-400 font-normal">جنية مصري</span>
                        </span>
                      )}
                    </div>
                  </div>

                  <Link
                    href={`/courses/${course.slug}`}
                    className="w-full py-3 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-sm shadow-lg shadow-blue-500/20 transition-all flex items-center justify-center gap-2 group"
                  >
                    <span>عرض تفاصيل الكورس</span>
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function CoursesPage() {
  return (
    <Suspense fallback={
      <div className="py-20 text-center text-slate-400 font-cairo">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-blue mx-auto mb-4"></div>
        جاري تحميل كتالوج الكورسات...
      </div>
    }>
      <CoursesContent />
    </Suspense>
  );
}
