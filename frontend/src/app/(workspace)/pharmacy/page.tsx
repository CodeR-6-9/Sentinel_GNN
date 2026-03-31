"use client";

import React from "react";
import { BarChart3, Zap } from "lucide-react";

/**
 * Pharmacy Database Module (Placeholder for v2.0)
 *
 * This module will provide:
 * - Drug interaction checker
 * - Availability & cost database
 * - Agentic AI procurement system
 * - Inventory management
 *
 * Coming in v2.0
 */

export default function PharmacyPage() {
  return (
    <div className="w-full h-full flex items-center justify-center p-8">
      <div className="max-w-md text-center space-y-6">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-100 to-cyan-100 dark:from-blue-900/30 dark:to-cyan-900/30 flex items-center justify-center border-2 border-blue-200 dark:border-blue-800">
            <BarChart3 className="w-10 h-10 text-blue-600 dark:text-blue-400" />
          </div>
        </div>

        {/* Content */}
        <div className="space-y-3">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Pharmacy Database
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
            Agentic AI procurement system with real-time drug availability, cost
            optimization, and interaction checking.
          </p>
        </div>

        {/* Button */}
        <button
          disabled
          className="w-full px-6 py-3 bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 font-semibold rounded-lg cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Zap className="w-4 h-4" />
          Coming in v2.0
        </button>

        {/* Divider */}
        <div className="flex items-center my-4">
          <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
          <span className="px-3 text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">
            Planned Features
          </span>
          <div className="flex-1 h-px bg-slate-200 dark:bg-slate-800" />
        </div>

        {/* Feature List */}
        <div className="text-left space-y-2">
          {[
            "📦 Drug inventory management",
            "💰 Cost optimization engine",
            "⚠️ Drug interaction checker",
            "🏥 Hospital formulary integration",
            "🤖 Agentic procurement AI",
          ].map((feature) => (
            <div
              key={feature}
              className="text-sm text-slate-600 dark:text-slate-400 flex items-start gap-2"
            >
              <span className="mt-0.5">{feature}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
