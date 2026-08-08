"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Users, CreditCard, CheckCircle2, XCircle, Download, ShieldAlert,
  Clock, DollarSign, Eye, RefreshCw, AlertCircle
} from "lucide-react";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [pendingPayments, setPendingPayments] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<string | null>(null);

  // Review modal state
  const [reviewPaymentId, setReviewPaymentId] = useState<string | null>(null);
  const [reviewAction, setReviewAction] = useState<"approve" | "reject">("approve");
  const [reviewNote, setReviewNote] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  const [unauthorized, setUnauthorized] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setUnauthorized(false);
    try {
      const [resM, resP, resS] = await Promise.all([
        api.get("/admin/metrics"),
        api.get("/payments/admin/list?status_filter=pending_review"),
        api.get("/admin/students")
      ]);
      setMetrics(resM.data);
      setPendingPayments(resP.data);
      setStudents(resS.data);
    } catch (err: any) {
      if (err?.response?.status === 403 || err?.response?.status === 401) {
        setUnauthorized(true);
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleExecuteReview = async () => {
    if (!reviewPaymentId) return;
    setSubmittingReview(true);
    try {
      await api.post("/payments/admin/review", {
        payment_id: reviewPaymentId,
        action: reviewAction,
        review_note: reviewNote,
        rejection_reason: reviewAction === "reject" ? rejectionReason : undefined
      });
      setReviewPaymentId(null);
      setReviewNote("");
      setRejectionReason("");
      await loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || "فشل تنفيذ عملية مراجعة الدفع.");
    } finally {
      setSubmittingReview(false);
    }
  };

  const handlePreviewReceipt = async (fileKey: string) => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "https://a12tqtb1zoht2490gpbgg0ea.72.62.148.31.sslip.io/api/v1";
    try {
      const res = await api.post(`/payments/admin/generate-preview-url?file_key=${encodeURIComponent(fileKey)}`);
      let rawUrl = res.data.preview_url || res.data.signed_url || `/payments/preview?token=${res.data.token}`;
      if (rawUrl.startsWith("/")) {
        const serverOrigin = apiBase.replace(/\/api\/v1\/?$/, "");
        rawUrl = `${serverOrigin}${rawUrl}`;
      }
      setSelectedReceipt(rawUrl);
    } catch {
      setSelectedReceipt(`${apiBase}/payments/preview?token=${encodeURIComponent(fileKey)}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900 text-white flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-brand-red border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-400 text-sm">جاري فتح لوحة التحكم الإدارية...</p>
        </div>
      </div>
    );
  }

  if (unauthorized) {
    return (
      <div className="min-h-screen bg-navy-900 text-white flex items-center justify-center p-4">
        <div id="unauthorized_notice" className="max-w-md w-full p-8 rounded-3xl glass-panel border border-brand-red/40 text-center space-y-4">
          <ShieldAlert className="w-16 h-16 text-brand-red mx-auto" />
          <h2 className="text-2xl font-bold text-white">غير مصرح بالدخول</h2>
          <p className="text-slate-400 text-sm">عفواً، هذه الصفحة مخصصة للإدارة فقط ولا يملك حسابك الصلاحية لدخولها.</p>
          <Link
            href="/dashboard"
            className="inline-block px-6 py-3 rounded-xl bg-brand-blue hover:bg-blue-600 font-bold text-white transition-colors"
          >
            العودة للوحة التحكم
          </Link>
        </div>
      </div>
    );
  }

  const exportCsvUrl = `${process.env.NEXT_PUBLIC_API_URL || "https://a12tqtb1zoht2490gpbgg0ea.72.62.148.31.sslip.io/api/v1"}/admin/export-csv`;

  return (
    <div className="min-h-screen bg-navy-900 text-white p-4 sm:p-6 lg:p-8 space-y-8">
      {/* Admin Top Navigation Header */}
      <div className="flex items-center justify-between p-6 rounded-3xl glass-panel border border-brand-red/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-red/20 border border-brand-red/40 flex items-center justify-center text-brand-red font-bold">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white">لوحة الإدارة والتحكم (Admin Panel)</h1>
            <p className="text-xs text-slate-400">مراجعة طلـبات المدفوعات وتفعيل اشتراكات الطلاب وتنزيل التقارير</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <a
            href={exportCsvUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2.5 rounded-xl bg-navy-800 hover:bg-navy-700 border border-slate-700 text-white text-xs font-bold flex items-center gap-2 transition-colors"
          >
            <Download className="w-4 h-4 text-cyan-400" />
            تصدير تقرير الطلاب (CSV)
          </a>
          <Link
            href="/dashboard"
            className="px-4 py-2.5 rounded-xl bg-brand-blue hover:bg-brand-blueHover text-white text-xs font-bold transition-colors"
          >
            واجهة الطالب
          </Link>
        </div>
      </div>

      {/* High Level Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>إجمالي الطلاب المسجلين</span>
            <Users className="w-4 h-4 text-brand-blue" />
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics?.total_students || 0}</div>
        </div>

        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>الاشتراكات النشطة</span>
            <CheckCircle2 className="w-4 h-4 text-green-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics?.active_enrolments || 0}</div>
        </div>

        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>طلبات مدفوعات تنتظر المراجعة</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400">{metrics?.pending_payments || 0}</div>
        </div>

        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>إجمالي الإيرادات المعتمدة</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{metrics?.approved_revenue || 0} ج.م</div>
        </div>
      </div>

      {/* Pending Payments Drawer / Review Table */}
      <div className="p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-amber-400" />
            طلبات مدفوعات الانستا باي وفودافون كاش المعلقة ({pendingPayments.length})
          </h2>
          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {pendingPayments.length === 0 ? (
          <div className="p-8 rounded-2xl bg-navy-950 border border-slate-800/80 text-center text-slate-400 text-xs">
            لا توجد طلبات مدفوعات معلقة حالياً.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right text-xs">
              <thead className="bg-navy-950 text-slate-400 font-bold border-b border-slate-800">
                <tr>
                  <th className="p-4">مرجع الطلب</th>
                  <th className="p-4">اسم الطالب / الرقم</th>
                  <th className="p-4">وسيلة التحويل</th>
                  <th className="p-4">المبلغ المتوقع / المحول</th>
                  <th className="p-4">الإيصال المرفوق</th>
                  <th className="p-4">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {pendingPayments.map((p) => (
                  <tr key={p.id} className="hover:bg-navy-800/40">
                    <td className="p-4 font-mono font-bold text-brand-blue">{p.reference_code}</td>
                    <td className="p-4">
                      <div className="font-bold text-white">{p.sender_identifier || "طالب"}</div>
                      <div className="text-[10px] text-slate-400">{p.created_at?.slice(0, 10)}</div>
                    </td>
                    <td className="p-4 font-semibold text-slate-300">
                      {p.payment_method === "instapay" ? "انستا باي" : "فودافون كاش"}
                    </td>
                    <td className="p-4 font-bold text-white">
                      {p.amount_submitted || p.amount_expected} ج.م
                    </td>
                    <td className="p-4">
                      {p.receipt_file_key ? (
                        <button
                          onClick={() => handlePreviewReceipt(p.receipt_file_key)}
                          className="px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-cyan-400 border border-slate-700 flex items-center gap-1 font-bold"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          معاينة الإيصال
                        </button>
                      ) : (
                        <span className="text-slate-500">لا يوجد</span>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setReviewPaymentId(p.id);
                            setReviewAction("approve");
                          }}
                          className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-bold flex items-center gap-1"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          قبول وتفعيل
                        </button>
                        <button
                          onClick={() => {
                            setReviewPaymentId(p.id);
                            setReviewAction("reject");
                          }}
                          className="px-3 py-1.5 rounded-lg bg-brand-red hover:bg-brand-redHover text-white font-bold flex items-center gap-1"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          رفض
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Registered Students Table */}
      <div className="p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Users className="w-5 h-5 text-brand-blue" />
          قائمة الطلاب المسجلين بالمنصة ({students.length})
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-right text-xs">
            <thead className="bg-navy-950 text-slate-400 font-bold border-b border-slate-800">
              <tr>
                <th className="p-4">اسم الطالب</th>
                <th className="p-4">رقم الهاتف</th>
                <th className="p-4">الصف الدراسي</th>
                <th className="p-4">الحالة</th>
                <th className="p-4">تاريخ التسجيل</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {students.map((s) => (
                <tr key={s.id} className="hover:bg-navy-800/40">
                  <td className="p-4 font-bold text-white">{s.arabic_name}</td>
                  <td className="p-4 font-mono dir-ltr text-right text-slate-300">{s.phone_number}</td>
                  <td className="p-4 text-slate-300">
                    {s.grade_level === "first_secondary" ? "الصف الأول الثانوي" : "الصف الثاني الثانوي"}
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 rounded-full bg-green-500/20 text-green-400 font-bold">
                      {s.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-400">{s.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Modal */}
      {reviewPaymentId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full glass-panel p-8 rounded-3xl border border-slate-800 space-y-6">
            <h3 className="text-xl font-bold text-white">
              {reviewAction === "approve" ? "تأكيد قبول طلب الدفع وتفعيل الكورس" : "تأكيد رفض طلب الدفع"}
            </h3>

            {reviewAction === "reject" ? (
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">سبب الرفض (إجباري):</label>
                <textarea
                  rows={3}
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="مثال: لم يتم العثور على التحويل المالي أو الإيصال غير واضح..."
                  className="w-full p-3 rounded-xl bg-navy-950 border border-slate-700 text-white text-xs"
                />
              </div>
            ) : (
              <p className="text-xs text-slate-300">
                بمجرد الموافقة، سيتم تغيير حالة طلب الدفع إلى <strong>مقبول (Approved)</strong> وإنشاء اشتراك فعال للطالب فوراً في الكورس مع إرسال إشعار داخلي.
              </p>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setReviewPaymentId(null)}
                className="px-4 py-2 rounded-xl bg-navy-800 text-slate-300 text-xs font-bold"
              >
                إلغاء
              </button>
              <button
                onClick={handleExecuteReview}
                disabled={submittingReview}
                className={`px-6 py-2 rounded-xl text-white text-xs font-bold shadow-lg ${
                  reviewAction === "approve" ? "bg-emerald-500 hover:bg-emerald-600" : "bg-brand-red hover:bg-brand-redHover"
                }`}
              >
                {submittingReview ? "جاري التنفيذ..." : "تأكيد الإجراء"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Receipt Image Preview Modal */}
      {selectedReceipt && (
        <div
          onClick={() => setSelectedReceipt(null)}
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 cursor-pointer"
        >
          <div className="max-w-2xl w-full p-2 glass-panel rounded-2xl relative" onClick={(e) => e.stopPropagation()}>
            <img src={selectedReceipt} alt="إيصال الدفع" className="w-full max-h-[80vh] object-contain rounded-xl" />
            <button
              onClick={() => setSelectedReceipt(null)}
              className="absolute top-4 right-4 p-2 rounded-full bg-navy-950 text-white font-bold"
            >
              ✕
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
