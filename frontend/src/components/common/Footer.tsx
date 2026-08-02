import Link from "next/link";
import { Code2, Phone, Mail, MapPin, ShieldCheck } from "lucide-react";

export default function Footer() {
  return (
    <footer className="bg-navy-950 border-t border-slate-800/80 text-slate-300 text-sm pt-14 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 md:gap-10">
          
          {/* Brand Column */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-blue to-cyan-400 p-0.5 shadow-md">
                <div className="w-full h-full bg-navy-950 rounded-[10px] flex items-center justify-center">
                  <Code2 className="w-5 h-5 text-brand-blue" />
                </div>
              </div>
              <span className="text-xl font-bold text-white tracking-tight">كود جيرني أكاديمي</span>
            </Link>
            <p className="text-xs leading-relaxed text-slate-300">
              المنصة التعليمية الأولى المتخصصة لطلاب المرحلة الثانوية في مصر. نبسط علوم الحاسب والبرمجة والتفكير المنطقي بالتطبيق العملي المباشر.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900 border border-slate-800 text-xs text-slate-200">
              <ShieldCheck className="w-4 h-4 text-green-400" />
              <span>منهج ثانوي مصري معتمد</span>
            </div>
          </div>

          {/* Quick Navigation Links */}
          <div className="space-y-3">
            <h4 className="text-white font-bold text-base tracking-wide">الروابط السريعة</h4>
            <ul className="space-y-2.5 text-xs text-slate-300">
              <li><Link href="/courses" className="hover:text-brand-blue transition-colors py-1 block">الكورسات والمناهج المتاحة</Link></li>
              <li><Link href="/#instructor" className="hover:text-brand-blue transition-colors py-1 block">عن المحاضر والخبرات</Link></li>
              <li><Link href="/#pricing" className="hover:text-brand-blue transition-colors py-1 block">باقات الأسعار والاشتراكات</Link></li>
              <li><Link href="/#how-it-works" className="hover:text-brand-blue transition-colors py-1 block">طريقة الشرح ونظام التعلم</Link></li>
            </ul>
          </div>

          {/* Legal Policies */}
          <div className="space-y-3">
            <h4 className="text-white font-bold text-base tracking-wide">السياسات والدعم</h4>
            <ul className="space-y-2.5 text-xs text-slate-300">
              <li><Link href="/terms" className="hover:text-brand-blue transition-colors py-1 block">الشروط والأحكام وسياسة الاستخدام</Link></li>
              <li><Link href="/privacy" className="hover:text-brand-blue transition-colors py-1 block">سياسة الخصوصية وحماية البيانات</Link></li>
              <li><Link href="/refund" className="hover:text-brand-blue transition-colors py-1 block">سياسة الاسترجاع والاسترداد</Link></li>
              <li><Link href="/#faq" className="hover:text-brand-blue transition-colors py-1 block">الأسئلة الشائعة</Link></li>
              <li><Link href="/#contact" className="hover:text-brand-blue transition-colors py-1 block">تواصل معنا المباشر</Link></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="space-y-3">
            <h4 className="text-white font-bold text-base tracking-wide">التواصل والإدارة</h4>
            <ul className="space-y-3 text-xs text-slate-300">
              <li className="flex items-center gap-3">
                <Phone className="w-4 h-4 text-brand-blue shrink-0" />
                <span dir="ltr" className="font-mono text-slate-200">01001340533 / 01008168639</span>
              </li>
              <li className="flex items-center gap-3">
                <Mail className="w-4 h-4 text-cyan-400 shrink-0" />
                <span className="font-mono text-slate-200">support@codejourney.academy</span>
              </li>
              <li className="flex items-center gap-3">
                <MapPin className="w-4 h-4 text-amber-400 shrink-0" />
                <span>جمهورية مصر العربية</span>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-400 gap-4">
          <p>© {new Date().getFullYear()} كود جيرني أكاديمي. جميع الحقوق محفوظة للمحاضر يوسف أحمد صبحي عابدين.</p>
          <div className="flex gap-6">
            <Link href="/terms" className="hover:text-slate-300 transition-colors">الشروط</Link>
            <Link href="/privacy" className="hover:text-slate-300 transition-colors">الخصوصية</Link>
            <Link href="/refund" className="hover:text-slate-300 transition-colors">الاسترجاع</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
