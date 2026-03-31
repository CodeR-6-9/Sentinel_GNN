"use client";

import React from "react";
import AgentTrace from "@/components/chat/AgentTrace";
import { BrainCircuit, Dna, Activity, AlertCircle, CheckCircle2 } from "lucide-react";

interface EvidenceInspectorProps {
  riskFactors: string[];
  mlPrediction: {
    prediction: string;
    confidence: number;
  } | null;
  traceList: string[];
  kg_verification?: {
    validated: boolean;
    genes: string[];
    details: string[];
    reason: string;
  };
}

export default function EvidenceInspector({
  mlPrediction,
  traceList,
  kg_verification,
}: EvidenceInspectorProps) {
  const isResistant = mlPrediction?.prediction === "Resistant";

  return (
    <div className="flex-none w-1/4 bg-white dark:bg-slate-950 border-l border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden shadow-xl z-10">
      
      {/* 🏥 HEADER (Fixed at the top) */}
      <div className="flex-shrink-0 p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2 uppercase tracking-wide">
          <Activity className="w-4 h-4 text-blue-600 dark:text-cyan-500" />
          Clinical Evidence
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5">
          AI Reasoning & Genomic Corroboration
        </p>
      </div>

      {/* 📜 SCROLLABLE CONTENT (The whole panel scrolls smoothly now) */}
      <div className="flex-1 overflow-y-auto p-5 space-y-8 custom-scrollbar pb-10">
        
        {/* --- 1. ML INFERENCE CARD --- */}
        {mlPrediction && (
          <section className="space-y-3 flex-shrink-0">
            <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
              <BrainCircuit className="w-3.5 h-3.5" />
              Primary ML Inference
            </h3>
            
            <div className={`rounded-xl border p-4 ${
              isResistant 
                ? "bg-red-50 dark:bg-red-950/20 border-red-100 dark:border-red-900/50" 
                : "bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/50"
            }`}>
              <div className="flex justify-between items-start mb-4">
                <span className={`text-sm font-bold ${
                  isResistant ? "text-red-700 dark:text-red-400" : "text-emerald-700 dark:text-emerald-400"
                }`}>
                  {mlPrediction.prediction}
                </span>
                {isResistant ? (
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-500" />
                ) : (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-500" />
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-600 dark:text-slate-400 font-medium">Model Confidence</span>
                  <span className={`font-mono font-bold ${isResistant ? "text-red-700 dark:text-red-400" : "text-emerald-700 dark:text-emerald-400"}`}>
                    {(mlPrediction.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                {/* Segmented Medical Progress Bar */}
                <div className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden flex">
                  <div 
                    className={`h-full transition-all duration-1000 ${isResistant ? "bg-red-500" : "bg-emerald-500"}`}
                    style={{ width: `${mlPrediction.confidence * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </section>
        )}

        {/* --- 2. NEO4J GENOMIC VERIFICATION --- */}
        <section className="space-y-3 flex-shrink-0">
          <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
            <Dna className="w-3.5 h-3.5" />
            Knowledge Graph (CARD)
          </h3>
          
          {kg_verification?.validated && kg_verification.genes.length > 0 ? (
            <div className="space-y-3">
              {kg_verification.details.map((detail, idx) => (
                <div key={idx} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-3 shadow-sm">
                  <div className="inline-block px-2 py-1 bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 rounded text-[11px] font-bold text-indigo-700 dark:text-indigo-400 font-mono mb-2">
                    {kg_verification.genes[idx]}
                  </div>
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                    {detail}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-slate-50 dark:bg-slate-900/50 border border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-5 text-center">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {isResistant 
                  ? "Querying CARD database for specific mutation markers..." 
                  : "No resistance markers detected. ML corroborates susceptible profile."}
              </p>
            </div>
          )}
        </section>

        {/* --- 3. AGENTIC AUDIT TRAIL --- */}
        <section className="space-y-3 flex-shrink-0">
          <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
            <Activity className="w-3.5 h-3.5" />
            System Audit Trail
          </h3>
          <div className="bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-inner p-2">
            {traceList && traceList.length > 0 ? (
              <AgentTrace traces={traceList} />
            ) : (
              <div className="h-24 flex items-center justify-center p-4">
                <span className="text-xs text-slate-400 italic text-center">Awaiting execution...</span>
              </div>
            )}
          </div>
        </section>

      </div>
    </div>
  );
}