"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, CreditCard, Upload } from "lucide-react";

import { api } from "@/lib/api";


type CourseItem = {
  id: string;
  title: string;
  price: number;
  discount_price?: number | null;
};

type PaymentItem = {
  id: string;
  course_id: string;
  reference_code: string;
  status: string;
  payment_method: string;
  amount_expected?: number | null;
  amount_submitted?: number | null;
  amount_difference?: number | null;
  amount_delta_status?: "underpaid" | "exact" | "overpaid" | null;
  rejection_reason?: string | null;
};

type PublicSettings = {
  instapay_number?: string;
  vodafone_cash_number?: string;
  payment_instructions?: string;
};

const REUSABLE_PAYMENT_STATUSES = new Set(["draft", "awaiting_receipt", "more_info_required"]);
const ALLOWED_RECEIPT_TYPES = ["image/jpeg", "image/png", "image/webp"];

function getEffectivePrice(course: CourseItem | undefined) {
  if (!course) return "";
  return String(course.discount_price ?? course.price);
}


export default function StudentPaymentsPage() {
  const [courses, setCourses] = useState<CourseItem[]>([]);
  const [myPayments, setMyPayments] = useState<PaymentItem[]>([]);
  const [settings, setSettings] = useState<PublicSettings>({});
  const [selectedCourse, setSelectedCourse] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("instapay");
  const [senderIdentifier, setSenderIdentifier] = useState("");
  const [amountSubmitted, setAmountSubmitted] = useState("");
  const [studentNote, setStudentNote] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [pendingPaymentId, setPendingPaymentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const selectedCourseData = useMemo(
    () => courses.find((course) => course.id === selectedCourse),
    [courses, selectedCourse],
  );

  const reusablePaymentByCourse = useMemo(() => {
    const mapping = new Map<string, PaymentItem>();
    for (const payment of myPayments) {
      if (REUSABLE_PAYMENT_STATUSES.has(payment.status) && !mapping.has(payment.course_id)) {
        mapping.set(payment.course_id, payment);
      }
    }
    return mapping;
  }, [myPayments]);

  const loadData = async () => {
    const [coursesResponse, paymentsResponse, settingsResponse] = await Promise.all([
      api.get("/courses"),
      api.get("/payments/my-payments"),
      api.get("/settings"),
    ]);
    setCourses(coursesResponse.data);
    setMyPayments(paymentsResponse.data);
    setSettings(settingsResponse.data || {});

    const firstCourseId = coursesResponse.data?.[0]?.id || "";
    setSelectedCourse((current) => current || firstCourseId);
  };

  useEffect(() => {
    loadData().catch(() => {
      setError("تعذر تحميل بيانات الدفع حالياً.");
    });
  }, []);

  useEffect(() => {
    if (!selectedCourseData) return;
    setAmountSubmitted(getEffectivePrice(selectedCourseData));
    const reusablePayment = reusablePaymentByCourse.get(selectedCourseData.id);
    setPendingPaymentId(reusablePayment?.id || null);
  }, [selectedCourseData, reusablePaymentByCourse]);

  const handleFileChange = (selectedFile: File | null) => {
    setFile(selectedFile);
    if (!selectedFile) return;
    if (!ALLOWED_RECEIPT_TYPES.includes(selectedFile.type)) {
      setError("يُسمح فقط برفع صور الإيصالات بصيغ JPG أو PNG أو WebP.");
      setFile(null);
    }
  };

  const handleCreateOrderAndUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!file) {
      setError("يرجى اختيار صورة الإيصال بصيغة JPG أو PNG أو WebP.");
      return;
    }
    if (!selectedCourse) {
      setError("يرجى اختيار الكورس أولاً.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    let reusablePaymentId = pendingPaymentId;
    try {
      if (!reusablePaymentId) {
        const orderResponse = await api.post("/payments/order", {
          course_id: selectedCourse,
          payment_method: paymentMethod,
        });
        reusablePaymentId = orderResponse.data.id;
        setPendingPaymentId(reusablePaymentId);
      }
      if (!reusablePaymentId) {
        throw new Error("Payment order was not created successfully.");
      }

      const formData = new FormData();
      formData.append("payment_id", reusablePaymentId);
      formData.append("sender_identifier", senderIdentifier);
      formData.append("amount_submitted", amountSubmitted);
      if (studentNote) {
        formData.append("student_note", studentNote);
      }
      formData.append("file", file);

      const uploadResponse = await api.post("/payments/upload-receipt", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setSuccess(`تم رفع الإيصال بنجاح لطلب الدفع ${uploadResponse.data.reference_code}. وهو الآن قيد المراجعة.`);
      setFile(null);
      setSenderIdentifier("");
      setStudentNote("");
      setPendingPaymentId(null);
      await loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || "فشل إرسال طلب الدفع. يمكنك إعادة المحاولة على نفس الطلب.");
    } finally {
      setLoading(false);
    }
  };

  const paymentDisplayNumber =
    paymentMethod === "instapay" ? settings.instapay_number : settings.vodafone_cash_number;

  return (
    <div className="min-h-screen bg-navy-900 text-white p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-white">تأكيد الاشتراك والمدفوعات</h1>
            <p className="text-slate-400 text-sm mt-1">رفع صورة الإيصال ومتابعة حالة الطلبات من داخل المنصة.</p>
          </div>
          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-xl bg-navy-800 hover:bg-navy-700 text-slate-300 text-xs font-bold transition-colors"
          >
            العودة للوحة التحكم
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7 p-8 rounded-3xl glass-panel border border-slate-800 space-y-6">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-brand-blue" />
              رفع إيصال تحويل جديد
            </h3>

            <div className="p-4 rounded-2xl bg-navy-950 border border-slate-800 space-y-2 text-xs text-slate-300">
              <div className="font-bold text-cyan-400 text-sm">بيانات التحويل:</div>
              <div>رقم InstaPay: {settings.instapay_number || "سيظهر بعد إعدادات المنصة"}</div>
              <div>رقم Vodafone Cash: {settings.vodafone_cash_number || "سيظهر بعد إعدادات المنصة"}</div>
              <div className="text-slate-400 pt-1">
                {settings.payment_instructions || "يرجى الاحتفاظ بصورة واضحة للإيصال ثم إدخال بيانات التحويل بدقة."}
              </div>
              {paymentDisplayNumber ? (
                <div className="text-emerald-300">الرقم الحالي للوسيلة المختارة: {paymentDisplayNumber}</div>
              ) : null}
            </div>

            {error ? (
              <div className="p-4 rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red text-sm flex items-center gap-3">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}

            {success ? (
              <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 text-sm flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <span>{success}</span>
              </div>
            ) : null}

            <form onSubmit={handleCreateOrderAndUpload} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">الكورس المراد الاشتراك به</label>
                <select
                  value={selectedCourse}
                  onChange={(event) => setSelectedCourse(event.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                >
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.title} — ({course.discount_price ?? course.price} ج.م)
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">وسيلة التحويل</label>
                  <select
                    value={paymentMethod}
                    onChange={(event) => setPaymentMethod(event.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                  >
                    <option value="instapay">انستا باي</option>
                    <option value="vodafone_cash">فودافون كاش</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">المبلغ المحول (ج.م)</label>
                  <input
                    type="number"
                    required
                    value={amountSubmitted}
                    onChange={(event) => setAmountSubmitted(event.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">رقم هاتف المحول أو حساب InstaPay</label>
                <input
                  type="text"
                  required
                  value={senderIdentifier}
                  onChange={(event) => setSenderIdentifier(event.target.value)}
                  placeholder="مثال: 01011111111 أو username@instapay"
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">صورة الإيصال (JPG / PNG / WebP)</label>
                <input
                  type="file"
                  required
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(event) => handleFileChange(event.target.files ? event.target.files[0] : null)}
                  className="w-full px-4 py-2.5 rounded-xl bg-navy-900 border border-slate-700 text-slate-300 file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-brand-blue file:text-white hover:file:bg-brand-blueHover"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-300 mb-1.5">ملاحظة إضافية (اختياري)</label>
                <textarea
                  rows={3}
                  value={studentNote}
                  onChange={(event) => setStudentNote(event.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-navy-900 border border-slate-700 text-white focus:outline-none focus:border-brand-blue"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-brand-blue to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-sm shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Upload className="w-4 h-4" />
                {loading ? "جارٍ رفع الإيصال..." : pendingPaymentId ? "إعادة رفع الإيصال على الطلب الحالي" : "إرسال الإيصال للمراجعة"}
              </button>
            </form>
          </div>

          <div className="lg:col-span-5 space-y-4">
            <h3 className="text-xl font-bold text-white">سجل طلبات الدفع الأخيرة</h3>
            {myPayments.length === 0 ? (
              <div className="p-8 rounded-3xl glass-panel border border-slate-800 text-center text-slate-400 text-xs">
                لا توجد طلبات دفع سابقة.
              </div>
            ) : (
              myPayments.map((payment) => (
                <div key={payment.id} className="p-6 rounded-2xl glass-panel border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-brand-blue font-bold">{payment.reference_code}</span>
                    <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-navy-800 text-slate-200">
                      {payment.status}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 space-y-1">
                    <div>المبلغ المطلوب: {payment.amount_expected ?? "-"} ج.م</div>
                    <div>المبلغ المحول: {payment.amount_submitted ?? "-"} ج.م</div>
                    {payment.amount_difference !== null && payment.amount_difference !== undefined ? (
                      <div>
                        الفرق: {payment.amount_difference} ج.م ({payment.amount_delta_status})
                      </div>
                    ) : null}
                  </div>
                  {payment.rejection_reason ? (
                    <div className="p-3 rounded-lg bg-brand-red/10 border border-brand-red/20 text-brand-red text-xs">
                      السبب: {payment.rejection_reason}
                    </div>
                  ) : null}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
