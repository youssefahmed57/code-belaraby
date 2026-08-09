"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import {
  PlayCircle, BookOpen, Code2, HelpCircle, CheckCircle2, Lock,
  ChevronRight, ArrowRight, RefreshCw, Send, Clock, Award, AlertCircle
} from "lucide-react";

// Dynamically import Monaco Editor to avoid SSR hydration mismatches
const Editor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

export default function LessonReaderPage({ params }: { params: { id: string } }) {
  const [activeTab, setActiveTab] = useState<"video" | "theory" | "coding" | "quiz">("video");
  const [lesson, setLesson] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState<string>("# اكتب كود Python هنا\ndaily = int(input())\nprint('Total:', daily * 7)\n");
  const [execResult, setExecResult] = useState<any>(null);
  const [running, setRunning] = useState(false);

  // Quiz state
  const [quizAttempt, setQuizAttempt] = useState<any>(null);
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});
  const [quizResult, setQuizResult] = useState<any>(null);

  const [studentInfo, setStudentInfo] = useState<{ name: string; phone: string }>({
    name: "طالب كود بالعربي",
    phone: "01000000000"
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("user_info");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setStudentInfo({
            name: parsed.arabic_name || parsed.full_name || "طالب كود بالعربي",
            phone: parsed.phone_number || "01000000000"
          });
        } catch (e) {
          console.error("Error parsing user info:", e);
        }
      }
    }
  }, []);

  const [videoStreamUrl, setVideoStreamUrl] = useState<string>("");

  useEffect(() => {
    async function fetchLesson() {
      try {
        const res = await api.get(`/lessons/${params.id}`);
        setLesson(res.data);

        // Fetch signed playback info for lesson video
        const videoAssetId = res.data?.video_asset_id || "demo_video_lesson_1";
        try {
          const vRes = await api.get(`/videos/token/${videoAssetId}`);
          if (vRes.data?.stream_url) {
            setVideoStreamUrl(vRes.data.stream_url);
          }
        } catch (vErr) {
          console.error("Signed video token fetch error:", vErr);
        }
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchLesson();
  }, [params.id]);

  const handleRunCode = async () => {
    setRunning(true);
    setExecResult(null);
    try {
      const res = await api.post("/coding-problems/run", {
        language: "python",
        code: code,
        stdin: "20\n"
      });
      setExecResult(res.data);
    } catch (err: any) {
      setExecResult({ status: "Error", stderr: "فشل تشغيل الكود في الخادم." });
    } finally {
      setRunning(false);
    }
  };

  const handleSubmitChallenge = async () => {
    if (!lesson?.coding_problem) return;
    setRunning(true);
    try {
      const res = await api.post("/coding-problems/submit", {
        problem_id: lesson.coding_problem.id,
        lesson_id: lesson.id,
        language: "python",
        code: code
      });
      setExecResult(res.data);
    } catch (err: any) {
      setExecResult({ status: "Error", stderr: "فشل تسليم الحل." });
    } finally {
      setRunning(false);
    }
  };

  const handleStartQuiz = async () => {
    if (!lesson?.quiz) return;
    try {
      const res = await api.post(`/quizzes/${lesson.quiz.id}/start`);
      setQuizAttempt(res.data);
    } catch (err: any) {
      alert(err.response?.data?.detail || "تعذر بدء الاختبار.");
    }
  };

  const handleSubmitQuiz = async () => {
    if (!quizAttempt) return;
    const formattedAnswers = Object.entries(quizAnswers).map(([qId, optId]) => ({
      question_id: qId,
      selected_option_ids: [optId]
    }));

    try {
      const res = await api.post("/quizzes/attempts/submit", {
        attempt_id: quizAttempt.attempt_id,
        answers: formattedAnswers
      });
      setQuizResult(res.data);
    } catch (err: any) {
      alert("فشل تسليم الاختبار.");
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

  return (
    <div className="min-h-screen bg-navy-900 text-white flex flex-col">
      {/* Lesson Header Navigation */}
      <header className="glass-panel border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="p-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-300 transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-white">{lesson?.title}</h1>
            <p className="text-xs text-slate-400">الوحدة الأولى: أساسيات لغة Python</p>
          </div>
        </div>

        {/* Unlocking Progress Threshold Pills */}
        <div className="hidden lg:flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800 border border-slate-700 text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-brand-blue" />
            <span>مشاهدة الفيديو: 80%</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800 border border-slate-700 text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-green-400" />
            <span>الشرح النظري: مكتمل</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800 border border-slate-700 text-slate-300">
            <CheckCircle2 className="w-4 h-4 text-amber-400" />
            <span>التطبيق العملي: تم الحل</span>
          </div>
        </div>
      </header>

      {/* Main Tabs Navigation */}
      <div className="border-b border-slate-800/80 bg-navy-950/60 px-4 sm:px-6 flex items-center gap-2 overflow-x-auto whitespace-nowrap scrollbar-none py-1 shrink-0">
        <button
          onClick={() => setActiveTab("video")}
          className={`px-4 sm:px-5 py-3 text-xs sm:text-sm font-bold border-b-2 flex items-center gap-2 transition-colors shrink-0 ${
            activeTab === "video"
              ? "border-brand-blue text-brand-blue"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <PlayCircle className="w-4 h-4" />
          فيديو الدرس
        </button>

        <button
          onClick={() => setActiveTab("theory")}
          className={`px-4 sm:px-5 py-3 text-xs sm:text-sm font-bold border-b-2 flex items-center gap-2 transition-colors shrink-0 ${
            activeTab === "theory"
              ? "border-brand-blue text-brand-blue"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <BookOpen className="w-4 h-4" />
          الشرح النظري
        </button>

        <button
          onClick={() => setActiveTab("coding")}
          className={`px-4 sm:px-5 py-3 text-xs sm:text-sm font-bold border-b-2 flex items-center gap-2 transition-colors shrink-0 ${
            activeTab === "coding"
              ? "border-cyan-400 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <Code2 className="w-4 h-4" />
          التحدي العملي
        </button>

        <button
          onClick={() => setActiveTab("quiz")}
          className={`px-4 sm:px-5 py-3 text-xs sm:text-sm font-bold border-b-2 flex items-center gap-2 transition-colors shrink-0 ${
            activeTab === "quiz"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-slate-400 hover:text-white"
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          كويز الدرس
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-grow p-3 sm:p-6">
        {/* Tab 1: Video Player */}
        {activeTab === "video" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="aspect-video w-full rounded-2xl sm:rounded-3xl overflow-hidden glass-panel border border-slate-800 relative bg-black">
              <iframe
                src={videoStreamUrl || `/api/v1/videos/stream-mock/demo_video_lesson_1?token=mock_signed_token&student_name=${encodeURIComponent(studentInfo.name)}&student_phone=${encodeURIComponent(studentInfo.phone)}`}
                className="w-full h-full border-0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <div className="p-4 sm:p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
              <h3 className="text-base sm:text-lg font-bold text-white">متابعة مشاهدة الفيديو</h3>
              <p className="text-xs text-slate-400">
                ملاحظة هامة: يجب مشاهدة 80% على الأقل من مدة الفيديو حتى يُحتسب متطلب المشاهدة تلقائياً في حسابك.
              </p>
            </div>
          </div>
        )}

        {/* Tab 2: Theory Reader */}
        {activeTab === "theory" && (
          <div className="max-w-4xl mx-auto p-4 sm:p-8 rounded-2xl sm:rounded-3xl glass-panel border border-slate-800 space-y-6">
            <div
              className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed"
              dangerouslySetInnerHTML={{ __html: lesson?.rich_content || "<p>لا يوجد محتوى نظري.</p>" }}
            />
            <div className="pt-6 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => alert("تم تعليم الجزء النظري كمكتمل!")}
                className="w-full sm:w-auto px-6 py-3 rounded-xl bg-brand-blue hover:bg-brand-blueHover text-white font-bold text-xs sm:text-sm shadow-lg shadow-blue-500/20 transition-colors flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" />
                تأكيد قراءة الشرح النظري
              </button>
            </div>
          </div>
        )}

        {/* Tab 3: Monaco Code Editor & Practical Challenge */}
        {activeTab === "coding" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-6 min-h-[70vh]">
            {/* Problem Statement Panel */}
            <div className="lg:col-span-5 p-6 rounded-3xl glass-panel border border-slate-800 space-y-4 overflow-y-auto">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">
                  {lesson?.coding_problem?.title || "تحدي برجمي عملي"}
                </h3>
                <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-xs font-bold">
                  سهل • 10 نقاط
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                {lesson?.coding_problem?.arabic_statement}
              </p>
              <div className="p-4 rounded-xl bg-navy-950 border border-slate-800 text-xs font-mono text-cyan-300">
                <div>الإدخال المتوقع (stdin): 20</div>
                <div>المخرجات المتوقعة (stdout): Total: 140</div>
              </div>
            </div>

            {/* Monaco Editor Panel */}
            <div className="lg:col-span-7 rounded-3xl glass-panel border border-slate-800 overflow-hidden flex flex-col">
              <div className="bg-navy-950 px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300">محرر كود Python</span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleRunCode}
                    disabled={running}
                    className="px-4 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-white text-xs font-bold border border-slate-700 transition-colors flex items-center gap-2"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${running ? "animate-spin" : ""}`} />
                    تشغيل (Run)
                  </button>
                  <button
                    onClick={handleSubmitChallenge}
                    disabled={running}
                    className="px-5 py-2 rounded-lg bg-brand-blue hover:bg-brand-blueHover text-white text-xs font-bold shadow-lg shadow-blue-500/25 transition-colors flex items-center gap-2"
                  >
                    <Send className="w-3.5 h-3.5" />
                    تسليم الكود (Submit)
                  </button>
                </div>
              </div>

              <div className="flex-grow min-h-[300px]">
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  theme="vs-dark"
                  value={code}
                  onChange={(val) => setCode(val || "")}
                  options={{
                    fontSize: 14,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    automaticLayout: true
                  }}
                />
              </div>

              {/* Execution Console Output Panel */}
              <div className="bg-navy-950 border-t border-slate-800 p-4 h-40 overflow-y-auto font-mono text-xs">
                <div className="text-slate-400 mb-1">شاشة المخرجات (Console Output):</div>
                {running && <div className="text-cyan-400">جاري إرسال الكود وتفيذه في بيئة مخصصة...</div>}
                {execResult && (
                  <div>
                    <div className={`font-bold ${execResult.status === "Accepted" || execResult.status === "ACCEPTED" ? "text-green-400" : "text-brand-red"}`}>
                      الحالة: {execResult.status}
                    </div>
                    {execResult.stdout && <pre className="text-white mt-1">{execResult.stdout}</pre>}
                    {execResult.stderr && <pre className="text-brand-red mt-1">{execResult.stderr}</pre>}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Quiz Modal / Assessment Panel */}
        {activeTab === "quiz" && (
          <div className="max-w-3xl mx-auto p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
            {!quizAttempt && !quizResult && (
              <div className="text-center space-y-4 py-8">
                <Award className="w-16 h-16 text-amber-400 mx-auto" />
                <h3 className="text-2xl font-bold text-white">{lesson?.quiz?.title || "اختبار قصير"}</h3>
                <p className="text-sm text-slate-400 max-w-md mx-auto">
                  درجة النجاح المطلوبة 70% فتح الدرس التالي. مدة الاختبار 10 دقائق والمحاولات المتاحة 3 محاولات.
                </p>
                <button
                  onClick={handleStartQuiz}
                  className="px-8 py-3.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-bold text-base shadow-xl shadow-amber-500/25 transition-all"
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
                    المتبقي: 09:45
                  </span>
                </div>

                {quizAttempt.questions.map((q: any, idx: number) => (
                  <div key={q.id} className="p-6 rounded-2xl bg-navy-950 border border-slate-800 space-y-4">
                    <h4 className="font-bold text-white text-base">
                      {idx + 1}. {q.text}
                    </h4>
                    <div className="space-y-2.5">
                      {q.options.map((opt: any) => (
                        <label
                          key={opt.id}
                          className="flex items-center gap-3 p-3.5 rounded-xl bg-navy-900 border border-slate-800 hover:border-slate-700 cursor-pointer text-xs font-semibold text-slate-300"
                        >
                          <input
                            type="radio"
                            name={`q_${q.id}`}
                            value={opt.id}
                            onChange={() => setQuizAnswers({ ...quizAnswers, [q.id]: opt.id })}
                            className="w-4 h-4 text-brand-blue"
                          />
                          <span>{opt.text}</span>
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
                  {quizResult.passed ? "تهانينا! لقد اجتزت الاختبار بنجاح 🎉" : "للأسف لم تتجاوز نسبة 70% المطلوبة"}
                </h3>
                <p className="text-xs text-slate-400">
                  الدرجة: {quizResult.score} / {quizResult.percentage}%
                </p>
                {quizResult.passed && (
                  <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-xs font-bold">
                    تم فتح الدرس التالي تلقائياً! يمكنك الانتقال إليه الآن.
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
