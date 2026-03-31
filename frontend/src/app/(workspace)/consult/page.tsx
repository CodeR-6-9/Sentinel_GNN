"use client";

import React from "react";
import { MessageSquare, Zap } from "lucide-react";

/**
 * AI Consultation Module (Placeholder for v2.0)
 *
 * This module will provide:
 * - LLM-powered ID specialist chat
 * - Real-time consultation interface
 * - Case discussion with AI physician assistant
 * - Evidence-based recommendation refinement
 * - Voice interface support
 *
 * Coming in v2.0
 */

export default function ConsultPage() {
  return (
    <div className="w-full h-full flex items-center justify-center p-8">
      <div className="max-w-md text-center space-y-6">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 flex items-center justify-center border-2 border-purple-200 dark:border-purple-800">
            <MessageSquare className="w-10 h-10 text-purple-600 dark:text-purple-400" />
          </div>
        </div>

        {/* Content */}
        <div className="space-y-3">
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            AI Consultation
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
            LLM-powered ID specialist chat for real-time clinical discussions
            and evidence-based recommendation refinement.
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
            "💬 ID specialist LLM chat interface",
            "🎙️ Voice input/output support",
            "📚 Evidence-based case discussion",
            "🔄 Recommendation refinement loop",
            "📋 Session history & export",
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
