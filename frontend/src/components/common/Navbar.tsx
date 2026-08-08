"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Code2, LogOut, LayoutDashboard, Shield, Menu, X, ChevronLeft } from "lucide-react";

export default function Navbar() {
  const [user, setUser] = useState<any>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const userInfo = localStorage.getItem("user_info");
    if (userInfo) {
      try {
        setUser(JSON.parse(userInfo));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_info");
    window.location.href = "/";
  };

  return (
    <nav className="sticky top-0 z-50 bg-navy-950/90 backdrop-blur-md border-b border-slate-800/80 transition-all h-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Brand Logo */}
          <Link href="/" className="flex items-center gap-3.5 group">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-brand-blue via-cyan-400 to-blue-600 p-0.5 shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform duration-300">
              <div className="w-full h-full bg-navy-950 rounded-[14px] flex items-center justify-center">
                <Code2 className="w-6 h-6 text-brand-blue group-hover:rotate-12 transition-transform duration-300" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-lg sm:text-xl font-black tracking-tight text-white flex items-center gap-1.5">
                كود بالعربي <span className="text-brand-blue text-[10px] sm:text-[11px] px-2 py-0.5 rounded-full bg-brand-blue/10 border border-brand-blue/30 font-bold">&lt;/&gt;</span>
              </span>
              <span className="text-[11px] font-medium text-slate-400 hidden sm:block">منصة تخصصية لبرمجة الثانوية العامة</span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <div className="hidden lg:flex items-center gap-7 text-[15px] font-semibold text-slate-200">
            <Link href="/" className="hover:text-brand-blue transition-colors py-1">الرئيسية</Link>
            <Link href="/courses" className="hover:text-brand-blue transition-colors py-1">الكورسات المتاحة</Link>
            <Link href="/#instructor" className="hover:text-brand-blue transition-colors py-1">عن المحاضر</Link>
            <Link href="/#pricing" className="hover:text-brand-blue transition-colors py-1">باقات الأسعار</Link>
            <Link href="/#how-it-works" className="hover:text-brand-blue transition-colors py-1">كيف نعمل</Link>
            <Link href="/#faq" className="hover:text-brand-blue transition-colors py-1">الأسئلة الشائعة</Link>
            <Link href="/#contact" className="hover:text-brand-blue transition-colors py-1">تواصل معنا</Link>
          </div>

          {/* Auth Controls */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                {user.role === "admin" || user.role === "super_admin" ? (
                  <Link
                    href="/admin"
                    className="flex items-center gap-2 px-4 py-2.5 min-h-[44px] rounded-xl bg-brand-red/10 border border-brand-red/30 text-brand-red font-bold text-xs hover:bg-brand-red/20 transition-all shadow-sm"
                  >
                    <Shield className="w-4 h-4" />
                    لوحة الإدارة
                  </Link>
                ) : null}

                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-4 py-2.5 min-h-[44px] rounded-xl bg-brand-blue/10 border border-brand-blue/30 text-brand-blue font-bold text-xs hover:bg-brand-blue/20 transition-all shadow-sm"
                >
                  <LayoutDashboard className="w-4 h-4" />
                  لوحة الطالب
                </Link>

                <button
                  onClick={handleLogout}
                  className="p-2.5 min-h-[44px] min-w-[44px] rounded-xl bg-navy-900 border border-slate-800 hover:bg-red-500/20 text-slate-300 hover:text-red-400 transition-colors flex items-center justify-center"
                  title="تسجيل الخروج"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  href="/login"
                  className="px-5 py-2.5 min-h-[44px] rounded-xl border border-slate-800 bg-navy-900/80 hover:bg-navy-800 text-sm font-bold text-slate-100 hover:text-white transition-all flex items-center justify-center"
                >
                  تسجيل الدخول
                </Link>
                <Link
                  href="/register"
                  className="px-5 py-2.5 min-h-[44px] rounded-xl bg-gradient-to-r from-brand-blue via-blue-600 to-cyan-500 hover:from-brand-blueHover hover:to-cyan-600 text-white font-bold text-sm shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] flex items-center justify-center gap-1.5"
                >
                  <span>حساب جديد</span>
                  <ChevronLeft className="w-4 h-4" />
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="lg:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2.5 min-h-[44px] min-w-[44px] rounded-xl bg-navy-900 border border-slate-800 text-slate-200 hover:text-white flex items-center justify-center"
              aria-label="القائمة"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden bg-navy-950/95 backdrop-blur-xl border-b border-slate-800 px-6 pt-4 pb-8 space-y-6">
          <div className="flex flex-col space-y-4 font-semibold text-slate-200 text-[15px] pt-2">
            <Link href="/" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">الرئيسية</Link>
            <Link href="/courses" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">الكورسات المتاحة</Link>
            <Link href="/#instructor" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">عن المحاضر</Link>
            <Link href="/#pricing" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">باقات الأسعار</Link>
            <Link href="/#how-it-works" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">كيف نعمل</Link>
            <Link href="/#faq" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">الأسئلة الشائعة</Link>
            <Link href="/#contact" onClick={() => setMobileMenuOpen(false)} className="hover:text-brand-blue py-1">تواصل معنا</Link>
          </div>

          <div className="pt-4 border-t border-slate-800/80 flex flex-col gap-3">
            {user ? (
              <>
                <Link
                  href="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full py-3.5 min-h-[44px] rounded-xl bg-brand-blue text-white font-bold text-center text-sm shadow-md flex items-center justify-center"
                >
                  لوحة الطالب
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full py-3.5 min-h-[44px] rounded-xl bg-navy-900 border border-slate-800 text-red-400 font-bold text-center text-sm flex items-center justify-center"
                >
                  تسجيل الخروج
                </button>
              </>
            ) : (
              <div className="grid grid-cols-2 gap-3">
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-3.5 min-h-[44px] rounded-xl bg-navy-900 border border-slate-800 text-slate-100 font-bold text-center text-sm flex items-center justify-center"
                >
                  تسجيل الدخول
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="py-3.5 min-h-[44px] rounded-xl bg-brand-blue text-white font-bold text-center text-sm shadow-md flex items-center justify-center"
                >
                  حساب جديد
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
