import React from "react";
import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/dashboard", icon: "🏠" },
  { label: "Chat", to: "/chat", icon: "💬" },
  { label: "Intelligence", to: "/intelligence", icon: "📊" },
  { label: "BIM Viewer", to: "/bim", icon: "🏗️" },
  { label: "Documents", to: "/documents", icon: "📁" },
  { label: "Actions", to: "/actions", icon: "✅" },
  { label: "Analytics", to: "/analytics", icon: "📈" },
  { label: "Settings", to: "/settings", icon: "⚙️" },
];

export default function Sidebar() {
  return (
    <aside className="w-full max-w-xs border-r border-gray-200 bg-white p-6">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-wide text-[#a67c52]">Diriyah AI</p>
        <h2 className="text-lg font-semibold text-gray-900">Workspace</h2>
        <p className="mt-1 text-sm text-gray-500">Navigate your delivery overview.</p>
      </div>

      <nav className="space-y-1" aria-label="Primary">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-4 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-[#f5eee6] text-[#8a5b2d]"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`
            }
          >
            <span className="text-base">{item.icon}</span>
            <span className="flex-1">{item.label}</span>
            <span aria-hidden className="text-xs text-gray-400">→</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-8 rounded-xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Next checkpoint</p>
        <p className="mt-2 text-sm font-medium text-gray-900">Executive steering review</p>
        <p className="mt-1 text-xs text-gray-500">Tomorrow · 09:00 AM (GMT+3)</p>
      </div>

      <div className="mt-4 rounded-xl border border-[#a67c52]/20 bg-[#f6efe6] p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-[#a67c52]">Demo Features</p>
        <p className="mt-1 text-xs text-gray-600">
          Explore AI-powered document classification, BIM viewing, and project forecasting.
        </p>
      </div>
    </aside>
  );
}
