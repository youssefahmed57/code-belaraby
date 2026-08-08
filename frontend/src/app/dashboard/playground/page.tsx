"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import {
  Play, ChevronRight, RefreshCw, Code2, Trash2, CheckCircle2, AlertTriangle, Clock,
  Copy, RotateCcw, Terminal, FileCode, Sliders, Download, Maximize2, Minimize2,
  ZoomIn, ZoomOut, Sparkles, Check, FileText
} from "lucide-react";

// Client-only dynamic import of Monaco Editor with SSR disabled
const Editor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[400px] bg-navy-950 flex flex-col items-center justify-center text-slate-400 gap-3 border border-slate-800">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-blue"></div>
      <span className="text-xs font-mono">جاري تحميل محرر Monaco...</span>
    </div>
  ),
});

const DEFAULT_PYTHON_CODE = `# كورس البرمجة للصف الأول الثانوي - كود بالعربي
student_name = "أحمد"
score = 100

if score >= 50:
    print(f"مبروك يا {student_name}، لقد اجتزت التحدي بنجاح!")
else:
    print("حاول مرة أخرى في التحدي القادم.")
`;

const PYTHON_PRESETS = [
  {
    label: "طباعة نص",
    code: `# طباعة النصوص والمخرجات
print("أهلاً بك في منصة كود بالعربي!")
`
  },
  {
    label: "قراءة input",
    code: `# قراءة البيانات من المستخدم (stdin)
name = input("ادخل اسمك: ")
age = int(input("ادخل عمرك: "))
print(f"أهلاً {name}، عمرك {age} سنة.")
`,
    sampleStdin: "محمود\n16\n"
  },
  {
    label: "حلقة for",
    code: `# حلقة تكرار لحساب مجموع الأعداد
total = 0
for i in range(1, 6):
    total += i
    print(f"الخطوة {i}: المجموع الحالي = {total}")

print(f"المجموع النهائي = {total}")
`
  },
  {
    label: "شروط if-else",
    code: `# التحقق من التقدير الدراسي
degree = 85

if degree >= 90:
    print("التقدير: ممتاز (A+)")
elif degree >= 75:
    print("التقدير: جيد جداً (B)")
else:
    print("التقدير: يحتاج إلى تحسين")
`
  },
  {
    label: "قوائم Lists",
    code: `# التعامل مع القوائم والمصفوفات
grades = [95, 88, 72, 100, 64]
print(fn := f"عدد درجات الطلاب: {len(grades)}")
print(f"أعلى درجة: {max(grades)}")
print(f"متوسط الدرجات: {sum(grades) / len(grades):.1f}")
`
  },
  {
    label: "دوال Functions",
    code: `# تعريف استدعاء الدوال
def calculate_area(length, width):
    return length * width

area = calculate_area(10, 5)
print(f"مساحة المستطيل = {area} متر مربع")
`
  }
];

export default function PlaygroundPage() {
  const [language, setLanguage] = useState<string>("python");
  const [code, setCode] = useState<string>(DEFAULT_PYTHON_CODE);
  const codeRef = useRef<string>(code);
  codeRef.current = code;

  const [stdin, setStdin] = useState<string>("");
  const stdinRef = useRef<string>(stdin);
  stdinRef.current = stdin;

  const [stdout, setStdout] = useState<string>("");
  const [stderr, setStderr] = useState<string>("");
  const [executionStatus, setExecutionStatus] = useState<string>("");
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [memoryUsed, setMemoryUsed] = useState<number | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  // Interactive UI Extras
  const [fontSize, setFontSize] = useState<number>(14);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Mobile Navigation Tab State: 'code' | 'stdin' | 'output'
  const [activeTab, setActiveTab] = useState<"code" | "stdin" | "output">("code");

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const updateCode = (newCode: string) => {
    codeRef.current = newCode;
    setCode(newCode);
  };

  const handleRun = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setStdout("");
    setStderr("");
    setExecutionStatus("");
    setExecutionTime(null);
    setMemoryUsed(null);

    // Switch to output tab on mobile when running
    setActiveTab("output");

    const activeCode = codeRef.current;
    const activeStdin = stdinRef.current;

    try {
      const res = await api.post("/coding-problems/run", {
        language: language,
        source_code: activeCode,
        code: activeCode,
        stdin: activeStdin,
      });

      const data = res.data;
      const status = data.status || "Accepted";
      setExecutionStatus(status);
      setStdout(data.stdout || "");
      setStderr(data.stderr || "");
      setExecutionTime(data.execution_time_seconds ?? data.execution_time ?? 0.04);
      setMemoryUsed(data.memory_used_kb ? Math.round(data.memory_used_kb / 1024) : 8);

      if (status === "Accepted") {
        showToast("🎉 تم تنفيذ الكود بنجاح وبدون أخطاء!");
      }
    } catch (err: any) {
      setExecutionStatus("Internal Execution Error");
      setStderr(err.response?.data?.detail || "حدث خطأ غير متوقع أثناء تنفيذ الكود.");
    } finally {
      setIsRunning(false);
    }
  };

  // Keyboard shortcut Ctrl + Enter or Cmd + Enter to run code
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleRun();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleClearOutput = () => {
    setStdout("");
    setStderr("");
    setExecutionStatus("");
    setExecutionTime(null);
    setMemoryUsed(null);
    showToast("🧹 تم مسح مخرجات التنفيذ");
  };

  const handleResetCode = () => {
    if (language === "python") updateCode(DEFAULT_PYTHON_CODE);
    else updateCode('console.log("hello world");');
    showToast("↻ تم إعادة تعيين الكود إلى الوضع الافتراضي");
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    showToast("⧉ تم نسخ الكود المكتوب إلى الحافظة!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadCode = () => {
    const ext = language === "python" ? "py" : "js";
    const blob = new Blob([code], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `code_belaraby_script.${ext}`;
    link.click();
    URL.revokeObjectURL(url);
    showToast(`📥 تم تحميل الكود كملف script.${ext}`);
  };

  const handleLoadPreset = (preset: typeof PYTHON_PRESETS[0]) => {
    updateCode(preset.code);
    if (preset.sampleStdin) {
      setStdin(preset.sampleStdin);
    }
    showToast(`✨ تم تحميل نموذج "${preset.label}"`);
  };

  return (
    <div className={`min-h-screen bg-navy-950 text-white flex flex-col font-cairo select-none sm:select-auto ${isFullscreen ? "fixed inset-0 z-50 overflow-hidden" : ""}`}>
      {/* Interactive Toast Notification */}
      {toastMsg && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-5 py-2.5 rounded-2xl bg-gradient-to-r from-brand-blue to-cyan-500 text-white font-bold text-xs shadow-2xl border border-cyan-300/30 animate-bounce flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-200 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Desktop/Mobile Header Bar */}
      <header className="glass-panel border-b border-slate-800 px-3 sm:px-6 py-2.5 flex items-center justify-between h-14 sm:h-16 shrink-0 z-20">
        <div className="flex items-center gap-2 sm:gap-3">
          <Link href="/dashboard" className="p-1.5 sm:p-2 rounded-xl bg-navy-900 border border-slate-800 text-slate-300 hover:text-white transition-colors">
            <ChevronRight className="w-4 h-4 sm:w-5 sm:h-5" />
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-brand-blue/20 border border-brand-blue/30 flex items-center justify-center">
              <Code2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-brand-blue" />
            </div>
            <h1 className="text-sm sm:text-base font-bold text-white">محرر الكود التفاعلي</h1>
          </div>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2.5">
          {/* Font Size Zoom Controls */}
          <div className="hidden md:flex items-center gap-1 bg-navy-900 border border-slate-800 p-1 rounded-xl">
            <button
              onClick={() => setFontSize(Math.max(12, fontSize - 2))}
              className="p-1 text-slate-400 hover:text-white transition-colors text-xs font-bold px-2"
              title="تصغير الخط"
            >
              A-
            </button>
            <span className="text-[11px] font-mono text-cyan-400 px-1">{fontSize}px</span>
            <button
              onClick={() => setFontSize(Math.min(22, fontSize + 2))}
              className="p-1 text-slate-400 hover:text-white transition-colors text-xs font-bold px-2"
              title="تكبير الخط"
            >
              A+
            </button>
          </div>

          <select
            value={language}
            onChange={(e) => {
              const lang = e.target.value;
              setLanguage(lang);
              if (lang === "python") updateCode(DEFAULT_PYTHON_CODE);
              else updateCode('console.log("hello world");');
            }}
            className="px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-xl bg-navy-900 border border-slate-700 text-xs font-bold text-cyan-400 focus:outline-none cursor-pointer"
          >
            <option value="python">Python 3.11</option>
            <option value="javascript">JS (Node)</option>
          </select>

          <button
            onClick={handleCopyCode}
            className="p-1.5 sm:p-2.5 rounded-xl bg-navy-900 border border-slate-800 hover:bg-navy-800 text-slate-300 hover:text-white transition-colors"
            title="نسخ الكود"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>

          <button
            onClick={handleDownloadCode}
            className="p-1.5 sm:p-2.5 rounded-xl bg-navy-900 border border-slate-800 hover:bg-navy-800 text-slate-300 hover:text-white transition-colors"
            title="تحميل الملف"
          >
            <Download className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="hidden sm:flex p-2.5 rounded-xl bg-navy-900 border border-slate-800 hover:bg-navy-800 text-slate-300 hover:text-white transition-colors"
            title="ملء الشاشة"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>

          <button
            onClick={handleResetCode}
            className="p-1.5 sm:p-2.5 rounded-xl bg-navy-900 border border-slate-800 hover:bg-navy-800 text-slate-300 hover:text-white transition-colors"
            title="إعادة تعيين الكود"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={handleRun}
            disabled={isRunning}
            className="hidden sm:flex px-4 py-2 rounded-xl bg-gradient-to-r from-brand-blue via-cyan-500 to-blue-600 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-xs shadow-lg shadow-blue-500/25 transition-all items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.02]"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>جاري التنفيذ...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>تشغيل (Ctrl + Enter)</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Interactive Code Presets Toolbar Bar */}
      <div className="bg-navy-900/90 border-b border-slate-800 px-3 sm:px-6 py-2 flex items-center gap-2 overflow-x-auto whitespace-nowrap scrollbar-none shrink-0">
        <span className="text-slate-400 text-xs font-bold flex items-center gap-1 shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          نماذج جاهزة:
        </span>
        {PYTHON_PRESETS.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => handleLoadPreset(preset)}
            className="px-3 py-1 rounded-lg bg-navy-950 border border-slate-800 hover:border-brand-blue/50 text-slate-300 hover:text-white text-xs font-semibold transition-all hover:bg-navy-800 shrink-0"
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Mobile Interactive Tab Bar (< lg screens) */}
      <div className="lg:hidden flex items-center justify-around bg-navy-900 border-b border-slate-800 px-2 py-1.5 shrink-0 z-10">
        <button
          onClick={() => setActiveTab("code")}
          className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === "code"
              ? "bg-brand-blue text-white shadow-md shadow-blue-500/20"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>المحرر</span>
        </button>

        <button
          onClick={() => setActiveTab("stdin")}
          className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
            activeTab === "stdin"
              ? "bg-brand-blue text-white shadow-md shadow-blue-500/20"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>المدخلات</span>
          {stdin.trim() && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>}
        </button>

        <button
          onClick={() => setActiveTab("output")}
          className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1.5 relative ${
            activeTab === "output"
              ? "bg-brand-blue text-white shadow-md shadow-blue-500/20"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>النتيجة</span>
          {executionStatus && (
            <span
              className={`w-2 h-2 rounded-full ${
                executionStatus === "Accepted" ? "bg-emerald-400 animate-ping" : "bg-red-400"
              }`}
            ></span>
          )}
        </button>
      </div>

      {/* Main Container */}
      <div className="flex-grow grid grid-cols-1 lg:grid-cols-12 gap-0 min-h-[calc(100vh-8rem)] lg:min-h-[calc(100vh-6rem)] relative">
        {/* Monaco Editor Container */}
        <div
          className={`lg:col-span-8 border-b lg:border-b-0 lg:border-l border-slate-800 flex flex-col bg-navy-950 ${
            activeTab === "code" ? "flex" : "hidden lg:flex"
          }`}
        >
          <div dir="ltr" className="w-full flex-grow h-[calc(100vh-12rem)] lg:h-full lg:min-h-[600px] text-left">
            <Editor
              height="100%"
              language={language}
              theme="vs-dark"
              value={code}
              onChange={(val) => updateCode(val || "")}
              options={{
                automaticLayout: true,
                fontSize: fontSize,
                fontFamily: "Consolas, Monaco, monospace",
                minimap: { enabled: false },
                wordWrap: "on",
                lineNumbers: "on",
                scrollBeyondLastLine: false,
                tabSize: 4,
              }}
            />
          </div>
        </div>

        {/* Console Input / Output Sidebar */}
        <div
          className={`lg:col-span-4 bg-navy-950 p-4 sm:p-6 flex-col gap-5 overflow-y-auto ${
            activeTab !== "code" ? "flex" : "hidden lg:flex"
          }`}
        >
          {/* Stdin Area */}
          <div className={`space-y-2 ${activeTab === "output" ? "hidden lg:block" : "block"}`}>
            <div className="flex items-center justify-between">
              <div>
                <label htmlFor="stdin" className="text-xs font-bold text-white block">
                  مدخلات البرنامج
                </label>
                <span className="text-[10px] text-slate-400 block font-mono">Standard Input (stdin)</span>
              </div>
              <button
                onClick={() => setStdin("100\n200\n")}
                className="text-[11px] text-cyan-400 hover:underline"
              >
                + نص إدخال تجريبي
              </button>
            </div>
            <textarea
              id="stdin"
              dir="ltr"
              rows={4}
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
              placeholder="اكتب البيانات المراد قراءتها بواسطة input() هنا..."
              className="w-full p-3 rounded-xl bg-navy-900 border border-slate-800 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-brand-blue text-left transition-colors"
            />
          </div>

          {/* Execution Result Area */}
          <div className={`flex-grow flex-col space-y-2 min-h-[250px] ${activeTab === "stdin" ? "hidden lg:flex" : "flex"}`}>
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white block">نتيجة التنفيذ</span>
                <span className="text-[10px] text-slate-400 block font-mono">Execution Result</span>
              </div>
              {(stdout || stderr || executionStatus) && (
                <button
                  onClick={handleClearOutput}
                  className="text-[11px] text-slate-400 hover:text-red-400 transition-colors flex items-center gap-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>مسح</span>
                </button>
              )}
            </div>

            <div className="flex-grow p-4 rounded-xl bg-navy-900 border border-slate-800 font-mono text-xs flex flex-col justify-between overflow-y-auto">
              {isRunning ? (
                <div className="text-cyan-400 animate-pulse flex items-center gap-2 p-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>جاري تنفيذ الكود في البيئة المعزولة...</span>
                </div>
              ) : !executionStatus ? (
                <div className="text-slate-500 text-center py-10">
                  اضغط على زر "تشغيل الكود" لرؤية المخرجات المباشرة هنا.
                </div>
              ) : (
                <div className="space-y-4">
                  {/* Status Badge */}
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      {executionStatus === "Accepted" ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-red-400" />
                      )}
                      <span
                        className={`font-bold ${
                          executionStatus === "Accepted" ? "text-emerald-400" : "text-red-400"
                        }`}
                      >
                        {executionStatus === "Accepted" ? "✅ تم التنفيذ بنجاح" : "❌ خطأ أثناء التنفيذ"}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                      {executionTime !== null && (
                        <div className="flex items-center gap-1">
                          <Clock className="w-3.5 h-3.5" />
                          <span>{executionTime}s</span>
                        </div>
                      )}
                      {memoryUsed !== null && (
                        <span>| {memoryUsed} MB</span>
                      )}
                    </div>
                  </div>

                  {/* Stdout Output */}
                  {stdout && (
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 font-sans block">Standard Output:</span>
                      <pre dir="ltr" className="p-3 rounded-lg bg-navy-950 text-slate-100 text-left font-mono whitespace-pre-wrap border border-slate-800/80 selection:bg-brand-blue">
                        {stdout}
                      </pre>
                    </div>
                  )}

                  {/* Stderr Output */}
                  {stderr && (
                    <div className="space-y-1">
                      <span className="text-[10px] text-red-400 font-sans block">Standard Error:</span>
                      <pre dir="ltr" className="p-3 rounded-lg bg-red-950/30 text-red-400 text-left font-mono whitespace-pre-wrap border border-red-500/20">
                        {stderr}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Floating Action Button for Mobile Screens (< sm) */}
      <div className="sm:hidden fixed bottom-5 left-5 z-30">
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="px-5 py-3 rounded-full bg-gradient-to-r from-brand-blue via-cyan-500 to-blue-600 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-xs shadow-2xl shadow-blue-500/50 flex items-center gap-2 disabled:opacity-50 border border-cyan-300/30"
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>جاري التنفيذ...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>تشغيل الكود</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
