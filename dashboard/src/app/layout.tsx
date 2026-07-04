import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Medico District Admin",
  description:
    "District-level healthcare facility monitoring dashboard — live operational data, alerts, and analytics.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">
        {/* ── Top navigation bar ────────────────────────────────────────── */}
        <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-900/80 backdrop-blur-md">
          <div className="mx-auto flex max-w-screen-2xl items-center justify-between px-6 py-3">
            {/* Logo + wordmark */}
            <Link
              href="/"
              className="flex items-center gap-2.5 text-slate-100 hover:text-indigo-300 transition-colors"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-lg shadow-indigo-500/30">
                <svg
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="h-4 w-4"
                >
                  <path d="M10.75 10.818v2.614A3.13 3.13 0 0 0 11.888 13c.482-.315.612-.648.612-.875 0-.227-.13-.56-.612-.875a3.13 3.13 0 0 0-1.138-.432ZM8.33 8.62c.053.055.115.11.184.164.208.208.44.177.651.082V5.5a2.75 2.75 0 0 0-1.625 1.136c-.08.12-.if.251-.12.388a.78.78 0 0 0 .91.596Zm1.67 4.46c-.124.196-.283.37-.473.516a2.716 2.716 0 0 1-.498.293A3.75 3.75 0 1 1 10 6.25v6.83Z" />
                  <path
                    fillRule="evenodd"
                    d="M9.25 1a8.25 8.25 0 1 0 0 16.5A8.25 8.25 0 0 0 9.25 1ZM2.5 9.25a6.75 6.75 0 1 1 13.5 0 6.75 6.75 0 0 1-13.5 0Z"
                    clipRule="evenodd"
                  />
                </svg>
              </span>
              <div className="flex flex-col leading-none">
                <span className="text-sm font-bold tracking-tight">Medico</span>
                <span className="text-[10px] font-medium text-slate-500 tracking-widest uppercase">
                  District Admin
                </span>
              </div>
            </Link>

            {/* Right side */}
            <nav className="flex items-center gap-4 text-sm text-slate-400">
              <Link
                href="/"
                className="hover:text-slate-100 transition-colors"
              >
                Facilities
              </Link>
              <span className="h-4 w-px bg-slate-700" />
              <span className="rounded-full border border-indigo-700/50 bg-indigo-900/40 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-indigo-300">
                Live
              </span>
            </nav>
          </div>
        </header>

        {/* ── Page content ──────────────────────────────────────────────── */}
        <main className="mx-auto max-w-screen-2xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
