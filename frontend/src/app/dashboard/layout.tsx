"use client";

import { useSession } from "next-auth/react";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import { signOut } from "next-auth/react";

const NAV = [
  { href: "/dashboard", label: "Overview", icon: "⬡" },
  { href: "/dashboard/google", label: "Google Account", icon: "G" },
  { href: "/dashboard/knowledge-base", label: "Knowledge Base", icon: "◈" },
  { href: "/dashboard/permissions", label: "Permissions", icon: "⛨" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status === "unauthenticated") router.push("/");
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#1a1a2e] text-white">
        Loading...
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#1a1a2e] text-white">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-white/10 bg-[#16213e] flex flex-col">
        <div className="px-5 py-6 border-b border-white/10">
          <h1 className="text-lg font-bold text-white">Clubmate AI</h1>
          <p className="text-xs text-slate-400 mt-0.5">Admin Dashboard</p>
        </div>

        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  active
                    ? "bg-[#5865F2] text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="px-4 py-4 border-t border-white/10">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-7 w-7 rounded-full bg-[#5865F2] flex items-center justify-center text-xs font-bold">
              {session?.user?.name?.[0] ?? "?"}
            </div>
            <span className="text-sm text-slate-300 truncate">{session?.user?.name}</span>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/" })}
            className="w-full rounded-lg bg-white/5 px-3 py-1.5 text-sm text-slate-400 hover:bg-white/10 hover:text-white transition"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}
