"use client";

import React from "react";
import { CheckCircle2, Terminal } from "lucide-react";

interface AgentTraceProps {
  traces: string[];
}

/**
 * AgentTrace Component
 *
 * Displays a sleek, dark-mode terminal-style log of agent actions.
 * Each trace entry is styled with a monospace font and a visual indicator icon.
 */
export default function AgentTrace({ traces }: AgentTraceProps) {
  return (
    <div className="w-full h-full bg-gradient-to-b from-slate-800/40 to-slate-900/60 rounded-lg border border-slate-600 p-4 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-600 sticky top-0">
        <Terminal className="w-5 h-5 text-cyan-400" />
        <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wide">
          Agent Execution Trace
        </h3>
      </div>

      {/* Trace Entries Container */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-2">
        {traces.length === 0 ? (
          <p className="text-slate-500 text-sm italic">
            Awaiting analysis execution...
          </p>
        ) : (
          traces.map((trace, index) => (
            <div
              key={index}
              className="flex gap-3 animate-in fade-in slide-in-from-left-4 duration-500"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Icon */}
              <div className="flex-shrink-0 pt-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>

              {/* Trace Text */}
              <p className="text-xs text-slate-300 leading-relaxed font-mono break-words">
                <span className="text-slate-500">[{String(index + 1).padStart(2, "0")}]</span>{" "}
                {trace}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {traces.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-600 sticky bottom-0 bg-gradient-to-t from-slate-900/60">
          <p className="text-xs text-slate-500">
            {traces.length} action{traces.length !== 1 ? "s" : ""} logged
          </p>
        </div>
      )}
    </div>
  );
}
