"use client";

import React from "react";
import { AlertCircle, Zap, Pill, ShoppingCart, ShieldAlert, PackageCheck, Truck } from "lucide-react";
import CopilotChat from "./CopilotChat";

interface RecommendationStageProps {
  strategy: string;
  isLoading: boolean;
  pharmacist?: any;
  procurement?: any;
  patientProfile?: any;
}

export default function RecommendationStage({
  strategy,
  isLoading,
  pharmacist,
  procurement,
  patientProfile,
}: RecommendationStageProps) {
  return (
    <div className="flex-1 bg-slate-50 dark:bg-slate-950 border-l border-r border-slate-200 dark:border-slate-800 flex flex-col items-center justify-start p-8 overflow-y-auto custom-scrollbar">
      
      {isLoading && (
        <div className="w-full h-full flex flex-col items-center justify-center">
          <div className="w-full max-w-md space-y-6 animate-pulse">
            <div className="space-y-4">
              <div className="h-12 bg-slate-200 dark:bg-slate-700 rounded-lg" />
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6" />
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-4/5" />
            </div>
            <div className="flex justify-center pt-4">
              <div className="inline-flex gap-2">
                <div className="w-3 h-3 bg-indigo-500 rounded-full animate-pulse" />
                <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: "0.1s" }} />
                <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
              </div>
            </div>
          </div>
        </div>
      )}

      {!isLoading && !strategy && (
        <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-16 h-16 bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto border border-slate-300 dark:border-slate-700">
            <AlertCircle className="w-8 h-8 text-slate-400 dark:text-slate-500" />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Awaiting Patient Data
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 max-w-xs">
              Enter clinical data to generate an AI-driven therapeutic strategy and trigger autonomous supply chain checks.
            </p>
          </div>
        </div>
      )}

      {!isLoading && strategy && (
        <div className="w-full max-w-3xl space-y-6 pb-10 mt-4">
          
          <div className="bg-white dark:bg-slate-900 rounded-2xl border-2 border-emerald-400 dark:border-emerald-500/50 border-l-4 dark:border-l-emerald-400 shadow-lg overflow-hidden backdrop-blur">
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
            <div className="p-6">
              <p className="text-[15px] leading-relaxed text-slate-800 dark:text-slate-100 font-medium whitespace-pre-wrap">
                {strategy}
              </p>
            </div>
          </div>

          {(pharmacist?.status || procurement?.status) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-md">
                <div className="bg-indigo-50 dark:bg-indigo-900/10 px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
                  <Pill className="w-4 h-4 text-indigo-500" />
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Pharmacy Verification
                  </h4>
                </div>
                <div className="p-5 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500 dark:text-slate-400">Formulary Status</span>
                    <span className={`text-xs font-bold px-2 py-1 rounded ${pharmacist?.formulary?.includes("Approved") ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"}`}>
                      {pharmacist?.formulary || "Unknown"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500 dark:text-slate-400">Unit Cost (USD)</span>
                    <span className="text-sm font-mono font-bold text-slate-700 dark:text-slate-200">
                      ${pharmacist?.cost_usd?.toFixed(2) || "0.00"}
                    </span>
                  </div>
                  
                  {pharmacist?.warnings?.length > 0 && (
                    <div className="mt-4 p-3 bg-rose-50 dark:bg-rose-900/10 border border-rose-200 dark:border-rose-900/50 rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                        <span className="text-[11px] font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider">Interaction Warnings</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {pharmacist.warnings.map((w: string) => (
                          <span key={w} className="text-[10px] bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300 px-2 py-0.5 rounded-full border border-rose-200 dark:border-rose-800">
                            {w.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-md flex flex-col">
                <div className="bg-blue-50 dark:bg-blue-900/10 px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
                  <ShoppingCart className="w-4 h-4 text-blue-500" />
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                    Supply Chain ERP
                  </h4>
                </div>
                
                <div className="p-5 flex-1 flex flex-col justify-center">
                  {procurement?.status === "ORDER_GENERATED" ? (
                    <div className="space-y-3">
                      <div className="flex items-start gap-3 p-3 bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/50 rounded-lg">
                        <Truck className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-[11px] font-bold text-amber-700 dark:text-amber-500 uppercase">Auto-Replenishment Triggered</p>
                          <p className="text-xs text-amber-600 dark:text-amber-400/80 mt-1">{procurement.alert}</p>
                        </div>
                      </div>
                      <div className="bg-slate-50 dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 p-3 text-xs font-mono space-y-1.5">
                        <div className="flex justify-between"><span className="text-slate-500">PO Number:</span><span className="font-bold text-blue-600 dark:text-blue-400">{procurement.po_number}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Order Qty:</span><span className="text-slate-700 dark:text-slate-300">{procurement.quantity} units</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Total Auth:</span><span className="text-slate-700 dark:text-slate-300">${procurement.total_cost_usd?.toFixed(2)}</span></div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center text-center space-y-2 py-4">
                      <div className="w-10 h-10 bg-emerald-50 dark:bg-emerald-900/20 rounded-full flex items-center justify-center mb-2">
                        <PackageCheck className="w-5 h-5 text-emerald-500" />
                      </div>
                      <p className="text-[13px] font-bold text-slate-700 dark:text-slate-200">Inventory Sufficient</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Current Stock: {procurement?.current_stock || 0} units</p>
                    </div>
                  )}
                </div>
              </div>

            </div>
          )}

          <CopilotChat 
            patientProfile={patientProfile} 
            strategy={strategy} 
            selectedDrug={procurement?.drug || pharmacist?.drug || ""} 
          />
          
          <div className="text-center text-xs text-slate-400 mt-8">
            System processed via Multi-Agent LLM Orchestration
          </div>
        </div>
      )}
    </div>
  );
}