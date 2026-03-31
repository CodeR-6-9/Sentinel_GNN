"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  MessageSquare,
  Sun,
  Moon,
  CheckCircle2,
  Menu,
  X,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    href: "/analyze",
    label: "Patient Analysis",
    icon: <Activity className="w-5 h-5" />,
  },
  {
    href: "/pharmacy",
    label: "Pharmacy Database",
    icon: <BarChart3 className="w-5 h-5" />,
  },
  {
    href: "/consult",
    label: "AI Consultation",
    icon: <MessageSquare className="w-5 h-5" />,
  },
];

const pageLabels: Record<string, string> = {
  "/analyze": "Patient Analysis Dashboard",
  "/pharmacy": "Pharmacy Database",
  "/consult": "AI Consultation",
};

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isDarkMode, setIsDarkMode] = useState<boolean | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Initialize theme from localStorage on client-side
  useEffect(() => {
    // Check localStorage first
    const savedTheme = localStorage.getItem("theme");
    let prefersDark: boolean;

    if (savedTheme === "dark") {
      prefersDark = true;
    } else if (savedTheme === "light") {
      prefersDark = false;
    } else {
      // Check system preference if no saved theme
      prefersDark =
        window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    }

    // Apply theme immediately
    applyTheme(prefersDark);
    setIsDarkMode(prefersDark);
  }, []);

  const applyTheme = (dark: boolean) => {
    const html = document.documentElement;
    if (dark) {
      html.classList.add("dark");
      document.body.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      html.classList.remove("dark");
      document.body.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  const toggleTheme = () => {
    if (isDarkMode === null) return;
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    applyTheme(newTheme);
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  // Get current page title
  const currentPageLabel = pageLabels[pathname] || "Sentinel-GNN";

  // Render loading state while theme is initializing
  if (isDarkMode === null) {
    return (
      <div className="h-screen w-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <div className="text-slate-600 dark:text-slate-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white flex overflow-hidden">
      {/* Sidebar - Responsive */}
      <aside
        className={`${
          isSidebarOpen ? "w-64" : "w-0"
        } flex-none bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col shadow-sm transition-all duration-300 overflow-hidden`}
      >
        {/* Logo */}
        <div className="flex-shrink-0 px-6 py-6 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-cyan-600 dark:text-cyan-500 flex-shrink-0" />
            <span className="text-lg font-bold text-slate-900 dark:text-white whitespace-nowrap">
              SentinelGNN
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            AMR Decision Support
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors whitespace-nowrap ${
                  isActive
                    ? "bg-cyan-50 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 font-medium"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                {item.icon}
                <span className="text-sm">{item.label}</span>
                {isActive && (
                  <div className="ml-auto w-2 h-2 rounded-full bg-cyan-600 dark:bg-cyan-400 flex-shrink-0" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer - Doctor Profile & Theme Toggle */}
        <div className="flex-shrink-0 border-t border-slate-200 dark:border-slate-800 p-4 space-y-4">
          {/* Doctor Profile */}
          <div className="bg-slate-100 dark:bg-slate-800 rounded-lg p-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-cyan-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                SC
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                  Dr. Sarah Chen
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  ID Specialist
                </p>
              </div>
            </div>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors text-sm font-medium text-slate-700 dark:text-slate-300 whitespace-nowrap"
          >
            {isDarkMode ? (
              <>
                <Sun className="w-4 h-4 flex-shrink-0" />
                <span>Light Mode</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 flex-shrink-0" />
                <span>Dark Mode</span>
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="flex-shrink-0 h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 md:px-8 shadow-sm">
          {/* Hamburger Menu */}
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
            aria-label="Toggle menu"
          >
            {isSidebarOpen ? (
              <X className="w-6 h-6 text-slate-600 dark:text-slate-400" />
            ) : (
              <Menu className="w-6 h-6 text-slate-600 dark:text-slate-400" />
            )}
          </button>

          <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
            {currentPageLabel}
          </h1>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/30 rounded-full border border-emerald-200 dark:border-emerald-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
              <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">
                System Online
              </span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-slate-50 dark:bg-slate-950">
          {children}
        </main>
      </div>
    </div>
  );
}
