"use client";

import React, { useState, useEffect } from "react";
import { 
  Pill, AlertTriangle, CheckCircle, DollarSign, 
  ShoppingCart, ShieldAlert, RefreshCw, Activity
} from "lucide-react";

export default function PharmacyPage() {
  const [inventory, setInventory] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchInventory = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/inventory");
      const data = await res.json();
      setInventory(data);
    } catch (error) {
      console.error("Failed to fetch inventory:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  return (
    <div className="w-full h-full bg-slate-50 dark:bg-slate-950 p-8 overflow-y-auto custom-scrollbar">
      
      {/* --- HEADER --- */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
            <Activity className="w-6 h-6 text-indigo-500" />
            Pharmacy & Supply Chain ERP
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Live inventory tracking, formulary management, and autonomous AI procurement.
          </p>
        </div>
        <button 
          onClick={fetchInventory}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-indigo-500" : ""}`} />
          Sync ERP
        </button>
      </div>

      {/* --- KPI CARDS --- */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
            <Pill className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Managed Drugs</p>
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {inventory ? Object.keys(inventory).length : "-"}
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-rose-200 dark:border-rose-900/30 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-rose-50 dark:bg-rose-900/20 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-rose-600 dark:text-rose-400" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Critical Stock Alerts</p>
            <p className="text-2xl font-bold text-rose-600 dark:text-rose-400">
              {inventory ? Object.values(inventory).filter((d: any) => (d.stock_vials || 0) <= (d.critical_threshold || 0)).length : "-"}
            </p>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-emerald-200 dark:border-emerald-900/30 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
            <ShoppingCart className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">Autonomous Agents</p>
            <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
              Active <span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span></span>
            </p>
          </div>
        </div>
      </div>

      {/* --- INVENTORY TABLE --- */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
          <h2 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
            Live Formulary & Inventory Data
          </h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-900/80 text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <th className="p-4 font-semibold">Medication</th>
                <th className="p-4 font-semibold">Stock Level</th>
                <th className="p-4 font-semibold">Formulary Status</th>
                <th className="p-4 font-semibold">Unit Cost</th>
                <th className="p-4 font-semibold">DDI Warnings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-sm text-slate-500 animate-pulse">
                    Connecting to Hospital ERP...
                  </td>
                </tr>
              ) : inventory ? (
                Object.entries(inventory).map(([drugName, data]: [string, any]) => {
                  // Safely handle missing numerical data
                  const stock = data.stock_vials || 0;
                  const threshold = data.critical_threshold || 0;
                  const isCritical = stock <= threshold;
                  
                  // Safely handle string data to prevent the .includes crash
                  const formularyStatus = data.formulary_status || "Unknown";
                  const isApproved = formularyStatus.includes("Approved");
                  
                  return (
                    <tr key={drugName} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                      {/* Name */}
                      <td className="p-4 font-bold text-slate-800 dark:text-slate-200">
                        {drugName}
                      </td>
                      
                      {/* Stock Level */}
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-bold font-mono ${isCritical ? "text-rose-600 dark:text-rose-400" : "text-slate-700 dark:text-slate-300"}`}>
                            {stock}
                          </span>
                          <span className="text-xs text-slate-400">/ {threshold} min</span>
                          {isCritical && <AlertTriangle className="w-4 h-4 text-rose-500" />}
                        </div>
                        {isCritical && (
                          <div className="text-[10px] text-rose-500 mt-1 font-semibold uppercase">
                            Auto-PO Pending
                          </div>
                        )}
                      </td>

                      {/* Formulary Status */}
                      <td className="p-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-bold uppercase tracking-wider ${
                          isApproved 
                            ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" 
                            : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                        }`}>
                          {isApproved ? <CheckCircle className="w-3 h-3" /> : <ShieldAlert className="w-3 h-3" />}
                          {formularyStatus.replace(/_/g, " ")}
                        </span>
                      </td>

                      {/* Cost */}
                      <td className="p-4">
                        <div className="flex items-center gap-1 text-slate-700 dark:text-slate-300">
                          <DollarSign className="w-4 h-4 text-slate-400" />
                          <span className="font-mono font-bold text-sm">{(data.cost_per_vial_usd || 0).toFixed(2)}</span>
                        </div>
                      </td>

                      {/* DDI Warnings */}
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {data.ddi_flags && data.ddi_flags.length > 0 ? (
                            data.ddi_flags.map((flag: string) => (
                              <span key={flag} className="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2 py-1 rounded border border-slate-200 dark:border-slate-700">
                                {flag.replace(/_/g, " ")}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-400 italic">None</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}