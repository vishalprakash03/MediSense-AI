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
        className="fixed left-4 top-4 z-30 rounded-xl border border-gray-200 bg-white px-3 py-2 text-lg shadow-sm md:hidden"
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
      <aside className={`fixed inset-y-0 left-0 z-40 flex min-h-screen w-64 shrink-0 flex-col border-r border-gray-100 bg-white p-5 transition-transform duration-200 md:static md:translate-x-0 ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      }`}>
        <button
          type="button"
          aria-label="Close navigation menu"
          onClick={closeMenu}
          className="absolute right-3 top-3 rounded-lg px-2 py-1 text-gray-500 md:hidden"
        >
          ×
        </button>
      <div className="flex items-center gap-2 mb-8 px-2">
        <span className="text-2xl">🩺</span>
        <span className="font-semibold text-lg text-brand-700">MediSense AI</span>
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
                  ? "bg-brand-50 text-brand-700"
                  : "text-gray-600 hover:bg-gray-50"
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
        className="mt-4 text-sm text-gray-500 hover:text-red-600 px-4 py-2 text-left"
      >
        ⏻ Log out
      </button>
      </aside>
    </>
  );
}
