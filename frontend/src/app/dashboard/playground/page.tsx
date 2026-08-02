"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { Play, ChevronRight, RefreshCw, Code2, Trash2, CheckCircle2, AlertTriangle, Clock } from "lucide-react";

// Client-only dynamic import of Monaco Editor with SSR disabled
const Editor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] bg-navy-950 flex flex-col items-center justify-center text-slate-400 gap-3 border border-slate-800">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-blue"></div>
      <span className="text-xs font-mono">جاري تحميل محرر Monaco...</span>
    </div>
  ),
});

export default function PlaygroundPage() {
  const [language, setLanguage] = useState<string>("python");
  const [code, setCode] = useState<string>('print("hello")');
  const codeRef = useRef<string>(code);
  codeRef.current = code;

  const [stdin, setStdin] = useState<string>("");
  const stdinRef = useRef<string>(stdin);
  stdinRef.current = stdin;

  const [stdout, setStdout] = useState<string>("");
  const [stderr, setStderr] = useState<string>("");
  const [executionStatus, setExecutionStatus] = useState<string>("");
  const [executionTime, setExecutionTime] = useState<number | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const updateCode = (newCode: string) => {
    codeRef.current = newCode;
    setCode(newCode);
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      (window as any).__setPlaygroundCode = (newCode: string) => {
        updateCode(newCode);
      };
    }
  }, []);

  const handleRun = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setStdout("");
    setStderr("");
    setExecutionStatus("");
    setExecutionTime(null);

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
      setExecutionStatus(data.status || "Accepted");
      setStdout(data.stdout || "");
      setStderr(data.stderr || "");
      setExecutionTime(data.execution_time_seconds ?? data.execution_time ?? 0.0);
    } catch (err: any) {
      setExecutionStatus("Internal Execution Error");
      setStderr(err.response?.data?.detail || "حدث خطأ غير متوقع أثناء تنفيذ الكود.");
    } finally {
      setIsRunning(false);
    }
  };

  const handleClearOutput = () => {
    setStdout("");
    setStderr("");
    setExecutionStatus("");
    setExecutionTime(null);
  };

  return (
    <div className="min-h-screen bg-navy-950 text-white flex flex-col font-cairo">
      {/* Header */}
      <header className="glass-panel border-b border-slate-800 px-4 sm:px-6 py-3 flex items-center justify-between h-16 shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 rounded-xl bg-navy-900 border border-slate-800 text-slate-300 hover:text-white transition-colors">
            <ChevronRight className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-blue/20 border border-brand-blue/30 flex items-center justify-center">
              <Code2 className="w-4 h-4 text-brand-blue" />
            </div>
            <h1 className="text-base font-bold text-white hidden sm:block">محرر الكود المستقل (Code Playground)</h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={language}
            onChange={(e) => {
              const lang = e.target.value;
              setLanguage(lang);
              if (lang === "python") updateCode('print("hello")');
              else updateCode('console.log("hello");');
            }}
            className="px-3 py-2 rounded-xl bg-navy-900 border border-slate-700 text-xs font-bold text-cyan-400 focus:outline-none"
          >
            <option value="python">Python 3.11</option>
            <option value="javascript">JavaScript (Node)</option>
          </select>

          <button
            onClick={handleRun}
            disabled={isRunning}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-xs shadow-md transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>جاري التشغيل...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>تشغيل الكود (Run)</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Container */}
      <div className="flex-grow grid grid-cols-1 lg:grid-cols-12 gap-0 min-h-[calc(100vh-4rem)]">
        {/* Monaco Editor Container (LTR) */}
        <div className="lg:col-span-8 border-b lg:border-b-0 lg:border-l border-slate-800 flex flex-col bg-navy-950">
          <div dir="ltr" className="w-full flex-grow min-h-[450px] lg:min-h-[600px] text-left">
            <Editor
              height="100%"
              language={language}
              theme="vs-dark"
              value={code}
              onChange={(val) => updateCode(val || "")}
              options={{
                automaticLayout: true,
                fontSize: 15,
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
        <div className="lg:col-span-4 bg-navy-950 p-4 sm:p-6 flex flex-col gap-5 overflow-y-auto">
          {/* Stdin Area */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="stdin" className="text-xs font-bold text-slate-300">
                مدخلات الكود (Standard Input - Stdin):
              </label>
            </div>
            <textarea
              id="stdin"
              dir="ltr"
              rows={3}
              value={stdin}
              onChange={(e) => setStdin(e.target.value)}
              placeholder="اكتب البيانات المراد قراءتها بواسطة input() هنا..."
              className="w-full p-3 rounded-xl bg-navy-900 border border-slate-800 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-brand-blue text-left"
            />
          </div>

          {/* Execution Result Area */}
          <div className="flex-grow flex flex-col space-y-2 min-h-[250px]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300">مخرجات التنفيذ (Execution Result):</span>
              {(stdout || stderr || executionStatus) && (
                <button
                  onClick={handleClearOutput}
                  className="text-[11px] text-slate-400 hover:text-red-400 transition-colors flex items-center gap-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>مسح النتائج</span>
                </button>
              )}
            </div>

            <div className="flex-grow p-4 rounded-xl bg-navy-900 border border-slate-800 font-mono text-xs flex flex-col justify-between overflow-y-auto">
              {isRunning ? (
                <div className="text-cyan-400 animate-pulse flex items-center gap-2 p-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>جاري تشغيل الكود في البيئة المعزولة...</span>
                </div>
              ) : !executionStatus ? (
                <div className="text-slate-500 text-center py-10">
                  اضغط على "تشغيل الكود" لرؤية النتيجة والمخرجات هنا.
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
                        حالة التنفيذ: {executionStatus}
                      </span>
                    </div>

                    {executionTime !== null && (
                      <div className="flex items-center gap-1 text-[11px] text-slate-400">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{executionTime}s</span>
                      </div>
                    )}
                  </div>

                  {/* Stdout Output */}
                  {stdout && (
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 font-sans block">Standard Output:</span>
                      <pre dir="ltr" className="p-3 rounded-lg bg-navy-950 text-slate-100 text-left font-mono whitespace-pre-wrap border border-slate-800/80">
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
    </div>
  );
}
