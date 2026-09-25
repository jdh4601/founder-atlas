import Link from "next/link";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Founder Atlas",
  description: "부딪힌 문제에 대한 YC·a16z·Paul Graham의 조언을 모아 보여주는 개인용 아카이브",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full">
      <body className="min-h-full flex flex-col bg-paper text-ink">
        <header className="border-b border-line">
          <div className="mx-auto flex max-w-[1100px] items-center justify-between px-5 py-4">
            <Link href="/" className="text-[15px] font-semibold tracking-tight">
              Founder Atlas
            </Link>
            <Link
              href="/map"
              className="text-[14px] text-ink-muted transition-colors hover:text-ink"
            >
              전체 지도
            </Link>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
