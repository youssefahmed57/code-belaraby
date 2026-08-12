"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  Code2,
  HelpCircle,
  PlayCircle,
  RefreshCw,
  Send,
} from "lucide-react";

import { fetchCurrentUser } from "@/lib/auth";
import { api } from "@/lib/api";


const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });


function sanitizeHtml(content: string): string {
  if (!content) return "";
  let clean = content.replace(/<(script|iframe|object|embed|form|style)[^>]*>[\s\S]*?<\/\1>/gi, "");
  clean = clean.replace(/<(script|iframe|object|embed|form)[^>]*\/>/gi, "");
  clean = clean.replace(/\s+on\w+\s*=\s*["'][^"']*["']/gi, "");
  clean = clean.replace(/\s+on\w+\s*=\s*\S+/gi, "");
  clean = clean.replace(/href\s*=\s*["']javascript:[^"']*["']/gi, 'href="#"');
  clean = clean.replace(/src\s*=\s*["']javascript:[^"']*["']/gi, 'src=""');
  return clean;
}


export default function LessonReaderPage() {
  const params = useParams<{ id: string }>();
  const lessonId = Array.isArray(params?.id) ? params.id[0] : params?.id;
  const [activeTab, setActiveTab] = useState<"video" | "theory" | "coding" | "quiz">("video");
  const [lesson, setLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [execResult, setExecResult] = useState<any>(null);
  const [quizAttempt, setQuizAttempt] = useState<any>(null);
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});
  const [quizResult, setQuizResult] = useState<any>(null);
  const [videoPlayback, setVideoPlayback] = useState<any>(null);
  const [lessonError, setLessonError] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const lastProgressSentAt = useRef(0);

  const selectedLanguage = useMemo(() => {
    const supported = lesson?.coding_problem?.supported_languages || [];
    if (supported.includes("python")) return "python";
    return supported[0] || "python";
  }, [lesson]);

  const loadLesson = async () => {
    if (!lessonId) {
      setLesson(null);
      setLessonError("تعذر تحديد الدرس المطلوب.");
      setLoading(false);
      return;
    }

    try {
      setLessonError(null);
      const lessonResponse = await api.get(`/lessons/${lessonId}`);
      const lessonData = lessonResponse.data;
      const supportedLanguages = lessonData?.coding_problem?.supported_languages || [];
      const preferredLanguage = supportedLanguages.includes("python")
        ? "python"
        : supportedLanguages[0] || "python";
      setLesson(lessonData);
      setCode(
        lessonData?.coding_problem?.starter_code?.[preferredLanguage]
        || lessonData?.coding_problem?.starter_code?.python
        || ""
      );
      setQuizAttempt(null);
      setQuizResult(null);

      if (lessonData?.video_asset_id) {
        const playbackResponse = await api.get(
          `/videos/token/${lessonData.video_asset_id}?lesson_id=${lessonData.id}`
        );
        setVideoPlayback(playbackResponse.data);
      } else {
        setVideoPlayback(null);
      }
    } catch (error: any) {
      console.error(error);
      setLessonError(error?.response?.data?.detail || "تعذر تحميل الدرس الحالي.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchCurrentUser().then((user) => {
      if (!active) return;
      if (!user) {
        window.location.href = "/login";
        return;
      }
      loadLesson();
    });
    return () => {
      active = false;
    };
  }, [lessonId]);

  useEffect(() => {
    if (!lesson?.coding_problem) return;
    const starter = lesson.coding_problem.starter_code?.[selectedLanguage]
      || lesson.coding_problem.starter_code?.python
      || "";
    setCode(starter);
  }, [lesson?.coding_problem, selectedLanguage]);

  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      if (event.data?.type !== "lesson-video-progress" || !lesson) return;
      await sendVideoProgress(event.data.currentPosition, event.data.duration);
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [lesson]);

  async function sendVideoProgress(currentPosition: number, duration: number) {
    if (!lesson?.video_asset_id || !lesson?.id) return;
    const now = Date.now();
    if (now - lastProgressSentAt.current < 5000) return;
    lastProgressSentAt.current = now;
    try {
      await api.post("/videos/progress", {
        lesson_id: lesson.id,
        video_id: lesson.video_asset_id,
        current_position: Number(currentPosition.toFixed(2)),
        duration: Number(duration.toFixed(2)),
      });
      const refreshed = await api.get(`/lessons/${lesson.id}`);
      setLesson(refreshed.data);
    } catch (error) {
      console.error("Video progress update failed:", error);
    }
  }

  const handleTheoryComplete = async () => {
    try {
      await api.post(`/lessons/${lessonId}/complete-theory`);
      setLesson((prev: any) => prev ? { ...prev, theory_completed: true } : prev);
    } catch (err: any) {
      alert(err?.response?.data?.detail || "حدث خطأ في تسجيل إتمام النظري.");
    }
  };

  const handleRunCode = async () => {
    setRunning(true);
    setExecResult(null);
    try {
      const response = await api.post("/coding-problems/run", {
        language: selectedLanguage,
        code,
        stdin: lesson?.coding_problem?.examples?.[0]?.input || "",
      });
      setExecResult(response.data);
    } catch (error: any) {
      setExecResult({ status: "Error", stderr: error?.response?.data?.detail || "فشل تشغيل الكود." });
    } finally {
      setRunning(false);
    }
  };

  const handleSubmitChallenge = async () => {
    if (!lesson?.coding_problem) return;
    setRunning(true);
    try {
      const response = await api.post("/coding-problems/submit", {
        problem_id: lesson.coding_problem.id,
        language: selectedLanguage,
        code,
      });
      setExecResult(response.data);
      await loadLesson();
    } catch (error: any) {
      setExecResult({ status: "Error", stderr: error?.response?.data?.detail || "فشل تسليم الحل." });
    } finally {
      setRunning(false);
    }
  };

  const handleStartQuiz = async () => {
    if (!lesson?.quiz) return;
    try {
      const response = await api.post(`/quizzes/${lesson.quiz.id}/start`);
      setQuizAttempt(response.data);
      setQuizAnswers({});
      setQuizResult(null);
    } catch (error: any) {
      alert(error?.response?.data?.detail || "تعذر بدء الاختبار.");
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quizAttempt) return;
    try {
      const response = await api.post("/quizzes/attempts/submit", {
        attempt_id: quizAttempt.attempt_id,
        answers: Object.entries(quizAnswers).map(([questionId, optionId]) => ({
          question_id: questionId,
          selected_option_ids: optionId ? [optionId] : [],
        })),
      });
      setQuizResult(response.data);
      await loadLesson();
    } catch (error: any) {
      alert(error?.response?.data?.detail || "فشل تسليم الاختبار.");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900 text-white flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-brand-blue border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">جاري فتح الدرس وتأكيد الصلاحيات...</p>
        </div>
      </div>
    );
  }

  if (!lesson || lessonError) {
    return (
      <div className="min-h-screen bg-navy-900 text-white flex items-center justify-center p-6">
        <div className="max-w-lg rounded-3xl glass-panel border border-slate-800 p-8 text-center space-y-4">
          <h2 className="text-2xl font-bold text-white">تعذر فتح الدرس</h2>
          <p className="text-sm text-slate-400">{lessonError || "الدرس غير متاح حالياً."}</p>
          <Link href="/dashboard" className="inline-flex px-6 py-3 rounded-xl bg-brand-blue text-white font-bold">
            العودة إلى لوحة الطالب
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-navy-900 text-white flex flex-col">
      <header className="glass-panel border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-300 transition-colors">
            <ChevronRight className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white">{lesson.title}</h1>
            <p className="text-xs text-slate-400">الإنجاز الحالي: {lesson.progress?.status || "in_progress"}</p>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800 border border-slate-700 text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-brand-blue" />
            <span>مشاهدة الفيديو: {lesson.progress?.video_watched_percentage || 0}%</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800 border border-slate-700 text-slate-300">
            <CheckCircle2 className={`w-4 h-4 ${lesson.progress?.theory_completed ? "text-green-400" : "text-slate-500"}`} />
            <span>الشرح النظري: {lesson.progress?.theory_completed ? "مكتمل" : "غير مكتمل"}</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800 border border-slate-700 text-slate-300">
            <CheckCircle2 className={`w-4 h-4 ${lesson.progress?.practical_passed ? "text-amber-400" : "text-slate-500"}`} />
            <span>التطبيق العملي: {lesson.progress?.practical_passed ? "تم الحل" : "بانتظار الحل"}</span>
          </div>
        </div>
      </header>

      <div className="border-b border-slate-800/80 bg-navy-950/60 px-4 sm:px-6 flex items-center gap-2 overflow-x-auto whitespace-nowrap py-1 shrink-0">
        {[
          { id: "video", label: "فيديو الدرس", icon: PlayCircle, accent: "brand-blue" },
          { id: "theory", label: "الشرح النظري", icon: BookOpen, accent: "brand-blue" },
          { id: "coding", label: "التحدي العملي", icon: Code2, accent: "cyan-400" },
          { id: "quiz", label: "كويز الدرس", icon: HelpCircle, accent: "amber-400" },
        ].map((tab) => {
          const Icon = tab.icon;
          const selected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 sm:px-5 py-3 text-xs sm:text-sm font-bold border-b-2 flex items-center gap-2 transition-colors shrink-0 ${
                selected ? `border-${tab.accent} text-${tab.accent}` : "border-transparent text-slate-400 hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="flex-grow p-3 sm:p-6">
        {activeTab === "video" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="aspect-video w-full rounded-2xl sm:rounded-3xl overflow-hidden glass-panel border border-slate-800 relative bg-black">
              {videoPlayback?.player_type === "hls" && videoPlayback?.manifest_url ? (
                <video
                  controls
                  className="w-full h-full"
                  src={videoPlayback.manifest_url}
                  onTimeUpdate={(event) => sendVideoProgress(event.currentTarget.currentTime, event.currentTarget.duration || 0)}
                  onPause={(event) => sendVideoProgress(event.currentTarget.currentTime, event.currentTarget.duration || 0)}
                  onEnded={(event) => sendVideoProgress(event.currentTarget.duration || 0, event.currentTarget.duration || 0)}
                />
              ) : videoPlayback?.stream_url ? (
                <iframe
                  src={videoPlayback.stream_url}
                  className="w-full h-full border-0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-slate-400 text-sm">
                  لا يوجد فيديو مرفوع لهذا الدرس حالياً.
                </div>
              )}
            </div>
            <div className="p-4 sm:p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
              <h3 className="text-base sm:text-lg font-bold text-white">متابعة مشاهدة الفيديو</h3>
              <p className="text-xs text-slate-400">
                يجب مشاهدة {lesson.required_video_percentage}% على الأقل حتى يُحتسب متطلب الفيديو تلقائياً.
              </p>
            </div>
          </div>
        )}

        {activeTab === "theory" && (
          <div className="max-w-4xl mx-auto p-4 sm:p-8 rounded-2xl sm:rounded-3xl glass-panel border border-slate-800 space-y-6">
            <div
              className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: sanitizeHtml(lesson.rich_content || "<p>لا يوجد محتوى نظري.</p>") }}
            />
            <div className="pt-6 border-t border-slate-800 flex justify-end">
              <button
                onClick={handleTheoryComplete}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-brand-blue hover:bg-brand-blueHover text-white font-bold text-xs sm:text-sm shadow-lg shadow-blue-500/20 transition-colors flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" />
                تأكيد قراءة الشرح النظري
              </button>
            </div>
          </div>
        )}

        {activeTab === "coding" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6 min-h-[70vh]">
            <div className="lg:col-span-5 p-6 rounded-3xl glass-panel border border-slate-800 space-y-4 overflow-y-auto">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">
                  {lesson.coding_problem?.title || "لا يوجد تحدٍ برمجي لهذا الدرس"}
                </h3>
                {lesson.coding_problem && (
                  <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold">
                    {lesson.coding_problem.difficulty} • {lesson.coding_problem.time_limit_seconds}s
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {lesson.coding_problem?.arabic_statement || "تم تعطيل جزء البرمجة لهذا الدرس حالياً."}
              </p>
            </div>

            <div className="lg:col-span-7 rounded-3xl glass-panel border border-slate-800 overflow-hidden flex flex-col">
              <div className="bg-navy-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300">محرر كود {selectedLanguage}</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRunCode}
                    disabled={running || !lesson.coding_problem}
                    className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-white text-xs font-bold border border-slate-700 transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${running ? "animate-spin" : ""}`} />
                    تشغيل
                  </button>
                  <button
                    onClick={handleSubmitChallenge}
                    disabled={running || !lesson.coding_problem}
                    className="px-5 py-2 rounded-lg bg-brand-blue hover:bg-brand-blueHover text-white text-xs font-bold shadow-lg shadow-blue-500/25 transition-colors flex items-center gap-2 disabled:opacity-50"
                  >
                    <Send className="w-3.5 h-3.5" />
                    تسليم الحل
                  </button>
                </div>
              </div>

              <div className="flex-grow min-h-[300px]">
                <Editor
                  height="100%"
                  defaultLanguage={selectedLanguage}
                  theme="vs-dark"
                  value={code}
                  onChange={(value) => setCode(value || "")}
                  options={{ fontSize: 14, minimap: { enabled: false }, scrollBeyondLastLine: false, automaticLayout: true }}
                />
              </div>

              <div className="bg-navy-950 border-t border-slate-800 p-4 h-40 overflow-y-auto font-mono text-xs">
                <div className="text-slate-400 mb-1">المخرجات:</div>
                {running && <div className="text-cyan-400">جارٍ إرسال الكود وتنفيذه داخل البيئة المعزولة...</div>}
                {execResult && (
                  <div>
                    <div className={`font-bold ${String(execResult.status).toLowerCase().includes("accept") ? "text-green-400" : "text-brand-red"}`}>
                      الحالة: {execResult.status}
                    </div>
                    {execResult.stdout && <pre className="text-white mt-1 whitespace-pre-wrap">{execResult.stdout}</pre>}
                    {execResult.stderr && <pre className="text-brand-red mt-1 whitespace-pre-wrap">{execResult.stderr}</pre>}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "quiz" && (
          <div className="max-w-3xl mx-auto p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
            {!quizAttempt && !quizResult && (
              <div className="text-center space-y-4 py-8">
                <Award className="w-16 h-16 text-amber-400 mx-auto" />
                <h3 className="text-2xl font-bold text-white">{lesson.quiz?.title || "لا يوجد اختبار لهذا الدرس"}</h3>
                {lesson.quiz && (
                  <p className="text-sm text-slate-400 max-w-md mx-auto">
                    مدة الاختبار {lesson.quiz.time_limit_minutes} دقيقة وعدد المحاولات المسموح به {lesson.quiz.allowed_attempts}.
                  </p>
                )}
                <button
                  onClick={handleStartQuiz}
                  disabled={!lesson.quiz}
                  className="px-8 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-base shadow-xl shadow-amber-500/25 transition-all disabled:opacity-50"
                >
                  بدء حل الاختبار الآن
                </button>
              </div>
            )}

            {quizAttempt && !quizResult && (
              <div className="space-y-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                  <span className="text-sm font-bold text-white">الأسئلة ({quizAttempt.questions.length})</span>
                  <span className="text-xs text-amber-400 font-mono flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    الحد الزمني: {lesson.quiz?.time_limit_minutes} دقيقة
                  </span>
                </div>
                {quizAttempt.questions.map((question: any, index: number) => (
                  <div key={question.id} className="p-6 rounded-2xl bg-navy-950 border border-slate-800 space-y-4">
                    <h4 className="font-bold text-white text-base">
                      {index + 1}. {question.text}
                    </h4>
                    <div className="space-y-2.5">
                      {(question.options || []).map((option: any) => (
                        <label key={option.id} className="flex items-center gap-3 p-3.5 rounded-xl bg-navy-900 border border-slate-800 hover:border-slate-700 cursor-pointer text-xs font-semibold text-slate-300">
                          <input
                            type="radio"
                            name={`q_${question.id}`}
                            value={option.id}
                            checked={quizAnswers[question.id] === option.id}
                            onChange={() => setQuizAnswers((current) => ({ ...current, [question.id]: option.id }))}
                            className="w-4 h-4 text-brand-blue"
                          />
                          <span>{option.text}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                <button
                  onClick={handleSubmitQuiz}
                  className="w-full py-4 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 text-white font-bold text-base shadow-xl transition-all"
                >
                  تسليم نتائج الاختبار
                </button>
              </div>
            )}

            {quizResult && (
              <div className="text-center space-y-4 py-6">
                <div className={`w-20 h-20 rounded-full mx-auto flex items-center justify-center text-3xl font-extrabold ${quizResult.passed ? "bg-green-500/20 text-green-400 border border-green-500/40" : "bg-brand-red/20 text-brand-red border border-brand-red/40"}`}>
                  {quizResult.percentage}%
                </div>
                <h3 className="text-2xl font-bold text-white">
                  {quizResult.passed ? "تم اجتياز الاختبار بنجاح" : quizResult.status === "timed_out" ? "انتهى وقت الاختبار" : "لم يتم اجتياز الاختبار"}
                </h3>
                <p className="text-xs text-slate-400">
                  الدرجة: {quizResult.score} | الحالة: {quizResult.status}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
