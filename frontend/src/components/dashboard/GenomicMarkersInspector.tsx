"use client";

import React from "react";
import AgentTrace from "@/components/chat/AgentTrace";
import { TrendingUp, Database } from "lucide-react";

interface GenomicMarkersInspectorProps {
  riskFactors: string[];
  mlPrediction: {
    prediction: string;
    confidence: number;
  } | null;
  traceList: string[];
}

/**
 * Genomic Markers Inspector (Right Panel - 25% width)
 *
 * PURPOSE: Display CARD database resistance markers for clinician verification
 * CHANGES from EvidenceInspector:
 * - Removed 3D Scene component (doctors need data, not graphics)
 * - Added "Detected Genomic Markers" card with monospaced list
 * - Cleaner, scannable layout for clinical decisions
 * - Dark mode support with proper color contrast
 */

export default function GenomicMarkersInspector({
  riskFactors,
  mlPrediction,
  traceList,
}: GenomicMarkersInspectorProps) {
  const isResistant = mlPrediction?.prediction === "Resistant";

  return (
    <div className="flex-none w-1/4 bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-slate-200 dark:border-slate-800">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Evidence Inspector
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Explainable AI Analysis
        </p>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto flex flex-col space-y-4 p-4">
        {/* ML Prediction Section */}
        {mlPrediction && (
          <div className="bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                ML Prediction
              </span>
              <span
                className={`text-sm font-bold px-2.5 py-1 rounded-md ${
                  isResistant
                    ? "bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300"
                    : "bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300"
                }`}
              >
                {mlPrediction.prediction}
              </span>
            </div>

            {/* Confidence Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-600 dark:text-slate-400">
                  Confidence
                </span>
                <span className="text-xs font-mono text-slate-700 dark:text-slate-300">
                  {(mlPrediction.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-slate-300 dark:bg-slate-700 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isResistant
                      ? "bg-gradient-to-r from-red-500 to-rose-500"
                      : "bg-gradient-to-r from-emerald-500 to-green-500"
                  }`}
                  style={{ width: `${mlPrediction.confidence * 100}%` }}
                />
              </div>
            </div>

            {/* Prediction Source */}
            <div className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1 mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
              <TrendingUp className="w-3 h-3 flex-shrink-0" />
              <span>Neural network trained on 50K+ AMR profiles</span>
            </div>
          </div>
        )}

        {/* Detected Genomic Markers (CARD) - NEW: No 3D Scene */}
        <div className="bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
            <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
              Detected Genomic Markers (CARD)
            </p>
          </div>

          {riskFactors.length > 0 ? (
            <div className="space-y-1">
              {riskFactors.map((factor) => (
                <div
                  key={factor}
                  className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300 font-mono"
                >
                  <span className="text-indigo-600 dark:text-indigo-400 font-bold">
                    ▸
                  </span>
                  <span className="break-words">{factor}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 dark:text-slate-400 italic py-2">
              No resistance markers identified.
            </div>
          )}
        </div>

        {/* Agent Trace Section */}
        {traceList.length > 0 && (
          <div className="flex-1 bg-slate-100 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden flex flex-col min-h-0">
            <div className="flex-shrink-0 px-4 py-3 border-b border-slate-200 dark:border-slate-700">
              <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
                Execution Trace
              </p>
            </div>
            <div className="flex-1 overflow-y-auto">
              <AgentTrace traces={traceList} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
