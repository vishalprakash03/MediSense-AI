"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { logout } from "@/services/api";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "🏠" },
  { href: "/assistant", label: "AI Health Assistant", icon: "💬" },
  { href: "/monitoring", label: "Health Monitoring", icon: "📈" },
  { href: "/symptoms", label: "Symptoms & Notes", icon: "📝" },
  { href: "/history", label: "Prediction History", icon: "🗂️" },
  { href: "/profile", label: "Profile", icon: "👤" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  function closeMenu() {
    setIsOpen(false);
  }

  return (
    <>
      <button
        type="button"
        aria-label="Open navigation menu"
        onClick={() => setIsOpen(true)}
        className="fixed left-4 top-4 z-30 rounded-xl border border-teal-800 bg-slate-950 px-3 py-2 text-lg text-white shadow-lg md:hidden"
      >
        ☰
      </button>
      {isOpen && (
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={closeMenu}
          className="fixed inset-0 z-30 bg-slate-900/30 md:hidden"
        />
      )}
      <aside className={`fixed inset-y-0 left-0 z-40 flex min-h-screen w-64 shrink-0 flex-col border-r border-teal-800/70 bg-gradient-to-b from-slate-950 via-teal-950 to-cyan-950 p-5 text-white shadow-2xl transition-transform duration-200 md:static md:translate-x-0 ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}>
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={closeMenu}
          className="absolute right-3 top-3 rounded-lg px-2 py-1 text-teal-100 hover:bg-white/10 md:hidden"
        >
          ×
        </button>
      <div className="mb-8 flex items-center gap-3 rounded-2xl border border-white/15 bg-white/10 px-3 py-3 shadow-lg shadow-slate-950/20">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-teal-300 to-cyan-400 text-xl shadow-lg">🩺</span>
        <div>
          <span className="block text-lg font-semibold tracking-tight text-white">MediSense AI</span>
          <span className="text-[10px] font-semibold uppercase tracking-[0.18em] text-teal-200">Health companion</span>
        </div>
      </div>

      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeMenu}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                active
                  ? "bg-white text-teal-900 shadow-lg shadow-slate-950/20"
                  : "text-teal-50 hover:bg-white/10 hover:text-white"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={() => {
          logout();
          closeMenu();
          router.push("/login");
        }}
        className="mt-4 rounded-xl px-4 py-2 text-left text-sm text-teal-100 transition-colors hover:bg-red-500/15 hover:text-red-200"
      >
        ⏻ Log out
      </button>
      </aside>
    </>
  );
}
