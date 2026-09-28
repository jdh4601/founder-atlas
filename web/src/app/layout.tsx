import Link from "next/link";
import type { Metadata } from "next";
import { BrowseNavLink } from "@/components/BrowseNavLink";
import { SettingsMenu } from "@/components/SettingsMenu";
import { THEME_BOOT_SCRIPT } from "@/lib/preferenceKeys";
import "./globals.css";

export const metadata: Metadata = {
  title: "Founder Atlas",
  description: "부딪힌 문제에 대한 YC·a16z·Paul Graham의 조언을 모아 보여주는 개인용 아카이브",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // The boot script sets data-theme before hydration, so the attribute may differ from the server HTML.
    <html lang="ko" className="h-full" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOT_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col bg-paper text-ink">
        <header className="sticky top-0 z-10 border-b border-line bg-paper/90 backdrop-blur">
          <div className="mx-auto flex max-w-[1100px] items-center justify-between px-5 py-3">
            <Link href="/" className="text-[15px] font-semibold tracking-tight">
              Founder Atlas
            </Link>
            <nav className="flex items-center gap-1 sm:gap-3">
              <BrowseNavLink sectionId="keywords">키워드</BrowseNavLink>
              <BrowseNavLink sectionId="contents">콘텐츠</BrowseNavLink>
              <SettingsMenu />
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
