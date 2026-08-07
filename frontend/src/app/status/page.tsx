"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw, Activity, ShieldCheck, Server } from "lucide-react";

interface ServiceStatus {
  name: string;
  status: string;
  latency_ms?: number;
  message?: string;
}

interface StatusResponse {
  platform_name: string;
  status: string;
  last_updated: string;
  services: ServiceStatus[];
}

export default function StatusPage() {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/status/public`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
      } else {
        setData(null);
      }
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const isOperational = data?.status === "operational";

  return (
    <div className="min-h-screen bg-navy-950 text-white font-cairo py-12 px-4 sm:px-6 lg:px-8 dir-rtl">
      <div className="max-w-3xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-blue/10 border border-brand-blue/20 text-brand-blue text-xs font-semibold">
            <Activity className="w-4 h-4 animate-pulse" />
            حالة النظام والخدمات السحابية
          </div>
          <h1 className="text-3xl font-extrabold text-white">منصة كود بالعربي - مركز الحالة المباشر</h1>
          <p className="text-slate-400 text-sm">متابعة لحظية ومباشرة لجودة استجابة الخوادم وقواعد البيانات</p>
        </div>

        {/* Global Banner */}
        <div className={`p-6 rounded-2xl border flex items-center justify-between ${
          isOperational 
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400" 
            : "bg-amber-500/10 border-amber-500/30 text-amber-400"
        }`}>
          <div className="flex items-center gap-3">
            {isOperational ? (
              <CheckCircle2 className="w-8 h-8 shrink-0 text-emerald-400" />
            ) : (
              <AlertTriangle className="w-8 h-8 shrink-0 text-amber-400" />
            )}
            <div>
              <h2 className="text-lg font-bold text-white">
                {isOperational ? "جميع الخدمات تعمل بكفاءة تامة" : "انخفاض مؤقت أو صيانة مجدولة في بعض الخدمات"}
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                آخر تحديث: {data ? new Date(data.last_updated).toLocaleTimeString("ar-EG") : "جاري الفحص..."}
              </p>
            </div>
          </div>
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="p-2.5 rounded-xl bg-navy-900 border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 transition-colors"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Individual Services Grid */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-400 px-1">تفاصيل المكونات والخدمات</h3>
          
          {data?.services ? (
            data.services.map((svc, idx) => {
              const ok = svc.status === "operational";
              return (
                <div key={idx} className="p-4 rounded-xl bg-navy-900/60 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Server className="w-5 h-5 text-brand-blue" />
                    <div>
                      <h4 className="text-sm font-semibold text-white">{svc.name}</h4>
                      {svc.message && <p className="text-xs text-slate-400 mt-0.5">{svc.message}</p>}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {svc.latency_ms !== undefined && (
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {svc.latency_ms} ms
                      </span>
                    )}
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                      ok ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}>
                      <span className={`w-2 h-2 rounded-full ${ok ? "bg-emerald-400 animate-ping" : "bg-amber-400"}`}></span>
                      {ok ? "متاح ويعمل" : "تحت الصيانة"}
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-6 text-center text-slate-400 text-sm">جاري تحميل حالة الأنظمة...</div>
          )}
        </div>

        {/* Footer Link */}
        <div className="text-center pt-4">
          <Link href="/" className="text-xs text-brand-blue hover:underline">
            العودة إلى الصفحة الرئيسية لمنصة كود بالعربي
          </Link>
        </div>

      </div>
    </div>
  );
}
