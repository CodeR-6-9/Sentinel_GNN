"use client";

import React from "react";
import { AlertCircle, Zap } from "lucide-react";

interface RecommendationStageProps {
  strategy: string;
  isLoading: boolean;
}

export default function RecommendationStage({
  strategy,
  isLoading,
}: RecommendationStageProps) {
  return (
    <div className="flex-1 bg-slate-50 dark:bg-slate-950 border-l border-r border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center p-8 overflow-hidden">
      {/* Loading State */}
      {isLoading && (
        <div className="w-full max-w-md space-y-6 animate-pulse">
          <div className="space-y-4">
            <div className="h-12 bg-slate-200 dark:bg-slate-700 rounded-lg" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-4/5" />
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
          </div>
          <div className="flex justify-center pt-4">
            <div className="inline-flex gap-2">
              <div className="w-3 h-3 bg-cyan-500 rounded-full animate-pulse" />
              <div
                className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"
                style={{ animationDelay: "0.1s" }}
              />
              <div
                className="w-3 h-3 bg-cyan-500 rounded-full animate-pulse"
                style={{ animationDelay: "0.2s" }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !strategy && (
        <div className="text-center space-y-4">
          <div className="w-16 h-16 bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto border border-slate-300 dark:border-slate-700">
            <AlertCircle className="w-8 h-8 text-slate-400 dark:text-slate-500" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Awaiting Patient Data
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xs">
              Enter patient clinical data in the left panel and click "Generate Strategy" to receive AI-driven therapeutic recommendations.
            </p>
          </div>
        </div>
      )}

      {/* Populated State - Hero Card */}
      {!isLoading && strategy && (
        <div className="w-full max-w-2xl">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border-2 border-emerald-400 dark:border-emerald-500/50 border-l-4 dark:border-l-emerald-400 shadow-lg overflow-hidden backdrop-blur">
            {/* Header Bar */}
            <div className="bg-emerald-50 dark:bg-emerald-900/20 px-6 py-4 border-b border-emerald-200 dark:border-emerald-500/30 flex items-center gap-3">
              <Zap className="w-6 h-6 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-emerald-700 dark:text-emerald-300 uppercase tracking-widest">
                  Clinical Recommendation
                </h4>
                <p className="text-xs text-emerald-600 dark:text-emerald-400/70">
                  Empiric Therapy Strategy
                </p>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              <p className="text-lg leading-relaxed text-slate-800 dark:text-slate-100 font-medium whitespace-pre-wrap">
                {strategy}
              </p>

              {/* Footer Accent */}
              <div className="mt-8 pt-6 border-t border-emerald-200 dark:border-emerald-500/20">
                <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400/80">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400" />
                  <span>AI-assisted, physician-reviewed decision support</span>
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer Badge */}
          <div className="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
            ⚠️ This recommendation is intended to support clinical decision-making. Final treatment decisions remain the responsibility of the prescribing physician.
          </div>
        </div>
      )}
    </div>
  );
}
