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
        <title>منصة كود جيرني للبرمجة | Code Journey Academy</title>
        <meta name="description" content="منصة تعليمية متكاملة لتدريس البرمجة والذكاء الاصطناعي لطلاب المرحلة الثانوية في مصر." />
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
