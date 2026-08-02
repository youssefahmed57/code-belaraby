"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  CreditCard, Upload, Phone, AlertCircle, CheckCircle2, Clock,
  FileText, ShieldCheck, ArrowRight, MessageCircle
} from "lucide-react";

export default function StudentPaymentsPage() {
  const [courses, setCourses] = useState<any[]>([]);
  const [myPayments, setMyPayments] = useState<any[]>([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("instapay");
  const [senderIdentifier, setSenderIdentifier] = useState("");
  const [amountSubmitted, setAmountSubmitted] = useState("180");
  const [studentNote, setStudentNote] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [resCourses, resPayments] = await Promise.all([
          api.get("/courses"),
          api.get("/payments/my-payments")
        ]);
        setCourses(resCourses.data);
        setMyPayments(resPayments.data);
        if (resCourses.data.length > 0) {
          setSelectedCourse(resCourses.data[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    }
    fetchData();
  }, []);

  const handleCreateOrderAndUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("يرجى اختيار صورة الإيصال أو ملف PDF.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // 1. Create order
      const resOrder = await api.post("/payments/order", {
        course_id: selectedCourse,
        payment_method: paymentMethod
      });
      const paymentId = resOrder.data.id;

      // 2. Upload receipt
      const formData = new FormData();
      formData.append("payment_id", paymentId);
      formData.append("sender_identifier", senderIdentifier);
      formData.append("amount_submitted", amountSubmitted);
      if (studentNote) formData.append("student_note", studentNote);
      formData.append("file", file);

      const resUpload = await api.post("/payments/upload-receipt", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      setSuccess(`تم رفع الإيصال بنجاح لطلب الدفع ${resUpload.data.reference_code}. وهو الآن قيد المراجعة بواسطة الإدارة.`);
      setFile(null);
      setSenderIdentifier("");

      // Refresh list
      const resMy = await api.get("/payments/my-payments");
      setMyPayments(resMy.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "فشل إرسال طلب الدفع. يرجى المحاولة لاحقاً.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-navy-900 text-white p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-white">تأكيد الاشتراك والمدفوعات</h1>
            <p className="text-slate-400 text-sm mt-1">تأكيد الدفع عبر انستا باي أو فودافون كاش ومتابعة حالة الطلبات</p>
          </div>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-300 text-xs font-bold transition-colors"
          >
            العودة للوحة التحكم
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Form Column */}
          <div className="lg:col-span-7 p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-brand-blue" />
              رفع إيصال تحويل جديد
            </h3>

            {/* Payment instructions box */}
            <div className="p-4 rounded-2xl bg-navy-950 border border-slate-800 space-y-2 text-xs text-slate-300">
              <div className="font-bold text-cyan-400 text-sm">بيانات التحويل المباشرة:</div>
              <div>• <strong>انستا باي (InstaPay):</strong> 01001340533</div>
              <div>• <strong>فودافون كاش (Vodafone Cash):</strong> 01001340533</div>
              <div className="text-slate-400 pt-1">يرجى الاحتفاظ بصورة الشاشة (Screenshot) وتأكيد البيانات أدناه:</div>
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {success && (
              <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-sm flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <span>{success}</span>
              </div>
            )}

            <form onSubmit={handleCreateOrderAndUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">الكورس المراد الاشتراك به</label>
                <select
                  value={selectedCourse}
                  onChange={(e) => setSelectedCourse(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} — ({c.discount_price || c.price} ج.م)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">وسيلة التحويل</label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                  >
                    <option value="instapay">انستا باي (InstaPay)</option>
                    <option value="vodafone_cash">فودافون كاش</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">المبلغ المحوّل (ج.م)</label>
                  <input
                    type="number"
                    required
                    value={amountSubmitted}
                    onChange={(e) => setAmountSubmitted(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">رقم هاتف المحوّل أو حساب انستا باي</label>
                <input
                  type="text"
                  required
                  value={senderIdentifier}
                  onChange={(e) => setSenderIdentifier(e.target.value)}
                  placeholder="مثال: 01011111111 أو username@instapay"
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">صورة الإيصال (PNG, JPG, PDF)</label>
                <input
                  type="file"
                  required
                  accept="image/png, image/jpeg, application/pdf"
                  onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full px-4 py-2.5 rounded-xl bg-navy-900 border border-slate-700 text-slate-300 file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-brand-blue file:text-white hover:file:bg-brand-blueHover"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-sm shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Upload className="w-4 h-4" />
                {loading ? "جاري رفع الإيصال..." : "إرسال الإيصال للمراجعة"}
              </button>
            </form>
          </div>

          {/* Previous Payments History */}
          <div className="lg:col-span-5 space-y-4">
            <h3 className="text-xl font-bold text-white">سجل طلبات الدفع الأخيرة</h3>
            {myPayments.length === 0 ? (
              <div className="p-8 rounded-3xl glass-panel border border-slate-800 text-center text-slate-400 text-xs">
                لا توجد طلبات دفع سابقة.
              </div>
            ) : (
              myPayments.map((p) => (
                <div key={p.id} className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-brand-blue font-bold">{p.reference_code}</span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      p.status === "approved" ? "bg-green-500/20 text-green-400" :
                      p.status === "pending_review" ? "bg-amber-500/20 text-amber-400" : "bg-brand-red/20 text-brand-red"
                    }`}>
                      {p.status === "approved" ? "مقبول ومفعل" :
                       p.status === "pending_review" ? "قيد المراجعة" : "مرفوض"}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300">
                    <div>المبلغ: <strong>{p.amount_submitted || p.amount_expected} ج.م</strong></div>
                    <div>الوسيلة: {p.payment_method === "instapay" ? "انستا باي" : "فودافون كاش"}</div>
                  </div>
                  {p.rejection_reason && (
                    <div className="p-3 rounded-lg bg-brand-red/10 border border-brand-red/20 text-brand-red text-xs">
                      السبب: {p.rejection_reason}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
