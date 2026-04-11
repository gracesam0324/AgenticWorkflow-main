import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Autobiography Generator Dashboard",
  description: "AI-powered autobiography generation pipeline dashboard",
};

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/interviews", label: "Interviews" },
  { href: "/story-bible", label: "Story Bible" },
  { href: "/chapters", label: "Chapters" },
  { href: "/quality", label: "Quality" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold text-indigo-600">
                  AutoBiography
                </span>
                <span className="text-sm text-gray-400">Pipeline Dashboard</span>
              </div>
              <div className="flex gap-1">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
