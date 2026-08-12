"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  CreditCard,
  DollarSign,
  Download,
  Eye,
  RefreshCw,
  ShieldAlert,
  Users,
  XCircle,
} from "lucide-react";

import { api } from "@/lib/api";

type PaymentDeltaStatus = "underpaid" | "exact" | "overpaid" | null;

type PendingPayment = {
  id: string;
  reference_code: string;
  sender_identifier?: string | null;
  created_at?: string | null;
  payment_method: string;
  amount_expected?: number | null;
  amount_submitted?: number | null;
  amount_difference?: number | null;
  amount_delta_status?: PaymentDeltaStatus;
  receipt_file_key?: string | null;
};

type StudentRow = {
  id: string;
  arabic_name: string;
  phone_number: string;
  grade_level: string;
  status: string;
  created_at?: string | null;
};

function getAmountStatusMeta(status: PaymentDeltaStatus) {
  switch (status) {
    case "underpaid":
      return {
        label: "UNDERPAID",
        className: "bg-brand-red/15 text-brand-red border border-brand-red/30",
      };
    case "overpaid":
      return {
        label: "OVERPAID",
        className: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
      };
    default:
      return {
        label: "EXACT",
        className: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
      };
  }
}

function formatAmount(value?: number | null) {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(2);
}

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [pendingPayments, setPendingPayments] = useState<PendingPayment[]>([]);
  const [students, setStudents] = useState<StudentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReceipt, setSelectedReceipt] = useState<string | null>(null);
  const [reviewPaymentId, setReviewPaymentId] = useState<string | null>(null);
  const [reviewAction, setReviewAction] = useState<"approve" | "reject">("approve");
  const [reviewNote, setReviewNote] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [unauthorized, setUnauthorized] = useState(false);

  const selectedPayment = useMemo(
    () => pendingPayments.find((payment) => payment.id === reviewPaymentId) || null,
    [pendingPayments, reviewPaymentId],
  );

  async function loadData() {
    setLoading(true);
    setUnauthorized(false);
    try {
      const [metricsResponse, pendingResponse, studentsResponse] = await Promise.all([
        api.get("/admin/metrics"),
        api.get("/payments/admin/list?status_filter=pending_review"),
        api.get("/admin/students"),
      ]);
      setMetrics(metricsResponse.data);
      setPendingPayments(pendingResponse.data);
      setStudents(studentsResponse.data);
    } catch (error: any) {
      if (error?.response?.status === 401 || error?.response?.status === 403) {
        setUnauthorized(true);
      }
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleExecuteReview() {
    if (!reviewPaymentId) return;
    setSubmittingReview(true);
    setReviewError(null);
    try {
      await api.post("/payments/admin/review", {
        payment_id: reviewPaymentId,
        action: reviewAction,
        review_note: reviewNote,
        rejection_reason: reviewAction === "reject" ? rejectionReason : undefined,
      });
      setReviewPaymentId(null);
      setReviewNote("");
      setRejectionReason("");
      await loadData();
    } catch (error: any) {
      setReviewError(error?.response?.data?.detail || "تعذر تنفيذ مراجعة طلب الدفع حالياً.");
    } finally {
      setSubmittingReview(false);
    }
  }

  async function handlePreviewReceipt(fileKey: string) {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    try {
      const response = await api.post(
        `/payments/admin/generate-preview-url?file_key=${encodeURIComponent(fileKey)}`,
      );
      let rawUrl =
        response.data.preview_url ||
        response.data.signed_url ||
        `/payments/preview?token=${response.data.token}`;
      if (rawUrl.startsWith("/")) {
        const serverOrigin = apiBase.replace(/\/api\/v1\/?$/, "");
        rawUrl = serverOrigin ? `${serverOrigin}${rawUrl}` : rawUrl;
      }
      setSelectedReceipt(rawUrl);
    } catch {
      setSelectedReceipt(null);
      setReviewError("تعذر إنشاء رابط معاينة مؤقت لهذا الإيصال حالياً.");
    }
  }

  const exportCsvUrl = `${process.env.NEXT_PUBLIC_API_URL || "/api/v1"}/admin/export-csv`;

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
        <div
          id="unauthorized_notice"
          className="max-w-md w-full p-8 rounded-3xl glass-panel border border-brand-red/40 text-center space-y-4"
        >
          <ShieldAlert className="w-16 h-16 text-brand-red mx-auto" />
          <h2 className="text-2xl font-bold text-white">غير مصرح بالدخول</h2>
          <p className="text-slate-400 text-sm">
            هذه الصفحة مخصصة للإدارة فقط ولا يملك حسابك الصلاحية للدخول إليها.
          </p>
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

  return (
    <div className="min-h-screen bg-navy-900 text-white p-4 sm:p-6 lg:p-8 space-y-8">
      <div className="flex items-center justify-between p-6 rounded-3xl glass-panel border border-brand-red/30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-red/20 border border-brand-red/40 flex items-center justify-center text-brand-red font-bold">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold text-white">لوحة الإدارة والتحكم</h1>
            <p className="text-xs text-slate-400">
              مراجعة طلبات المدفوعات، معاينة الإيصالات، وتفعيل الاشتراكات بأمان.
            </p>
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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold">
            <span>إجمالي حسابات الطلاب</span>
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
            <span>طلبات تنتظر المراجعة</span>
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

      <div className="p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-amber-400" />
            طلبات الدفع المعلقة ({pendingPayments.length})
          </h2>
          <button
            onClick={loadData}
            className="p-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {reviewError ? (
          <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{reviewError}</span>
          </div>
        ) : null}

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
                  <th className="p-4">الإيصال المرفوع</th>
                  <th className="p-4">الإجراءات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {pendingPayments.map((payment) => {
                  const amountMeta = getAmountStatusMeta(payment.amount_delta_status ?? "exact");
                  const underpaid = payment.amount_delta_status === "underpaid";
                  return (
                    <tr key={payment.id} className="hover:bg-navy-800/40">
                      <td className="p-4 font-mono font-bold text-brand-blue">{payment.reference_code}</td>
                      <td className="p-4">
                        <div className="font-bold text-white">{payment.sender_identifier || "طالب"}</div>
                        <div className="text-[10px] text-slate-400">{payment.created_at?.slice(0, 10)}</div>
                      </td>
                      <td className="p-4 font-semibold text-slate-300">
                        {payment.payment_method === "instapay" ? "انستا باي" : "فودافون كاش"}
                      </td>
                      <td className="p-4">
                        <div className="space-y-1">
                          <div className="font-bold text-white">المتوقع: {formatAmount(payment.amount_expected)} ج.م</div>
                          <div className="font-bold text-slate-300">المحول: {formatAmount(payment.amount_submitted)} ج.م</div>
                          <div className="flex items-center gap-2">
                            <span className="text-slate-400">الفرق: {formatAmount(payment.amount_difference)} ج.م</span>
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${amountMeta.className}`}>
                              {amountMeta.label}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        {payment.receipt_file_key ? (
                          <button
                            onClick={() => handlePreviewReceipt(payment.receipt_file_key!)}
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
                              setReviewPaymentId(payment.id);
                              setReviewAction("approve");
                              setReviewError(null);
                            }}
                            disabled={underpaid}
                            className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-bold flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                            title={underpaid ? "لا يمكن اعتماد دفعة أقل من المبلغ المطلوب." : undefined}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            قبول وتفعيل
                          </button>
                          <button
                            onClick={() => {
                              setReviewPaymentId(payment.id);
                              setReviewAction("reject");
                              setReviewError(null);
                            }}
                            className="px-3 py-1.5 rounded-lg bg-brand-red hover:bg-brand-redHover text-white font-bold flex items-center gap-1"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            رفض
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-navy-800/40">
                  <td className="p-4 font-bold text-white">{student.arabic_name}</td>
                  <td className="p-4 font-mono dir-ltr text-right text-slate-300">{student.phone_number}</td>
                  <td className="p-4 text-slate-300">
                    {student.grade_level === "first_secondary" ? "الصف الأول الثانوي" : "الصف الثاني الثانوي"}
                  </td>
                  <td className="p-4">
                    <span className="px-2.5 py-1 rounded-full bg-green-500/20 text-green-400 font-bold">
                      {student.status}
                    </span>
                  </td>
                  <td className="p-4 text-slate-400">{student.created_at?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {reviewPaymentId && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full glass-panel p-8 rounded-3xl border border-slate-800 space-y-6">
            <h3 className="text-xl font-bold text-white">
              {reviewAction === "approve" ? "تأكيد قبول طلب الدفع وتفعيل الكورس" : "تأكيد رفض طلب الدفع"}
            </h3>

            {selectedPayment ? (
              <div className="p-4 rounded-2xl bg-navy-950 border border-slate-800 text-xs text-slate-300 space-y-2">
                <div>المرجع: <span className="font-mono text-brand-blue">{selectedPayment.reference_code}</span></div>
                <div>المبلغ المتوقع: {formatAmount(selectedPayment.amount_expected)} ج.م</div>
                <div>المبلغ المحول: {formatAmount(selectedPayment.amount_submitted)} ج.م</div>
                <div>الفرق: {formatAmount(selectedPayment.amount_difference)} ج.م</div>
                <span className={`inline-flex px-2 py-1 rounded-full text-[10px] font-bold ${getAmountStatusMeta(selectedPayment.amount_delta_status ?? "exact").className}`}>
                  {getAmountStatusMeta(selectedPayment.amount_delta_status ?? "exact").label}
                </span>
              </div>
            ) : null}

            {reviewAction === "reject" ? (
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-2">سبب الرفض (إجباري):</label>
                <textarea
                  rows={3}
                  value={rejectionReason}
                  onChange={(event) => setRejectionReason(event.target.value)}
                  placeholder="مثال: الإيصال غير واضح أو لم يتم العثور على التحويل."
                  className="w-full p-3 rounded-xl bg-navy-950 border border-slate-700 text-white text-xs"
                />
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-slate-300">
                  بمجرد الموافقة سيتم تحويل الطلب إلى Approved وإنشاء اشتراك فعال للطالب إذا كانت قيمة التحويل كافية.
                </p>
                {selectedPayment?.amount_delta_status === "underpaid" ? (
                  <div className="p-3 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-xs">
                    لا يمكن اعتماد هذا الطلب لأنه أقل من المبلغ المطلوب للكورس.
                  </div>
                ) : null}
              </div>
            )}

            {reviewError ? (
              <div className="p-3 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-xs">
                {reviewError}
              </div>
            ) : null}

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => {
                  setReviewPaymentId(null);
                  setReviewError(null);
                }}
                className="px-4 py-2 rounded-xl bg-navy-800 text-slate-300 text-xs font-bold"
              >
                إلغاء
              </button>
              <button
                onClick={handleExecuteReview}
                disabled={submittingReview || (reviewAction === "approve" && selectedPayment?.amount_delta_status === "underpaid")}
                className={`px-6 py-2 rounded-xl text-white text-xs font-bold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed ${
                  reviewAction === "approve" ? "bg-emerald-500 hover:bg-emerald-600" : "bg-brand-red hover:bg-brand-redHover"
                }`}
              >
                {submittingReview ? "جاري التنفيذ..." : "تأكيد الإجراء"}
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedReceipt && (
        <div
          onClick={() => setSelectedReceipt(null)}
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 cursor-pointer"
        >
          <div
            className="max-w-2xl w-full p-2 glass-panel rounded-2xl relative"
            onClick={(event) => event.stopPropagation()}
          >
            <img src={selectedReceipt} alt="إيصال الدفع" className="w-full max-h-[80vh] object-contain rounded-xl" />
            <button
              onClick={() => setSelectedReceipt(null)}
              className="absolute top-4 right-4 p-2 rounded-full bg-navy-950 text-white font-bold"
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
