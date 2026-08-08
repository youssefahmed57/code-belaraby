"use client";

import "./globals.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        retry: 1
      }
    }
  }));

  return (
    <html lang="ar" dir="rtl" className="dark">
      <head>
        <title>كود بالعربي | منصة تخصصية في تعليم البرمجة لطلاب المرحلة الثانوية</title>
        <meta name="description" content="منصة كود بالعربي المتخصصة في تدريس البرمجة والمناهج التفاعلية لطلاب المرحلة الثانوية بإشراف نخبة من المتخصصين." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-navy-900 text-white min-h-screen font-cairo antialiased">
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}
