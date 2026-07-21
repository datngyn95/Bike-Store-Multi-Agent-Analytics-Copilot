import type { Metadata } from "next";

import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Bike Store - Trợ lý phân tích",
  description: "Giao diện phân tích Bike Store và trợ lý đa tác nhân tiếng Việt."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
