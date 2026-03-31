"use client";

import React from "react";
import { AlertCircle, Play } from "lucide-react";
import { PatientProfile } from "@/lib/api";

interface PatientIntakeSidebarProps {
  isolateId: string;
  patientProfile: PatientProfile;
  onChange: (field: keyof PatientProfile | "isolateId", value: unknown) => void;
  onRunAnalysis: () => void;
  isLoading: boolean;
  error: string | null;
}

export default function PatientIntakeSidebar({
  isolateId,
  patientProfile,
  onChange,
  onRunAnalysis,
  isLoading,
  error,
}: PatientIntakeSidebarProps) {
  const handleIsolateIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange("isolateId", e.target.value);
  };

  const handlePatientProfileChange = (field: keyof PatientProfile, value: unknown) => {
    onChange(field, value);
  };

  return (
    <div className="flex-none w-1/4 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden shadow-sm">
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b border-slate-200 dark:border-slate-800">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Patient Intake
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Clinical Data Entry
        </p>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto space-y-4 p-4">
        {/* Isolate ID Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-2">
            Bacterial Strain (Isolate ID)
          </label>
          <input
            type="text"
            value={isolateId}
            onChange={handleIsolateIdChange}
            placeholder="e.g., Escherichia coli"
            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
        </div>

        {/* Clinical History Section */}
        <div className="space-y-3 pt-2">
          <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
            Clinical History
          </p>

          {/* Age Input */}
          <div>
            <label className="block text-xs text-slate-600 dark:text-slate-400 mb-1.5 font-medium">
              Patient Age
            </label>
            <input
              type="number"
              value={patientProfile.Age}
              onChange={(e) =>
                handlePatientProfileChange("Age", parseInt(e.target.value) || 0)
              }
              min="0"
              max="120"
              className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-sm text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>

          {/* Prior Hospitalization Checkbox */}
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-3 rounded border border-slate-200 dark:border-slate-700">
            <input
              type="checkbox"
              id="hospital"
              checked={patientProfile.Hospital_before}
              onChange={(e) =>
                handlePatientProfileChange("Hospital_before", e.target.checked)
              }
              className="w-4 h-4 rounded border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 focus:ring-2 focus:ring-cyan-500 cursor-pointer"
            />
            <label
              htmlFor="hospital"
              className="text-sm text-slate-700 dark:text-slate-300 font-medium cursor-pointer"
            >
              Prior Hospitalization
            </label>
          </div>

          {/* Infection Frequency Slider */}
          <div>
            <label className="block text-xs text-slate-600 dark:text-slate-400 mb-2 font-medium">
              Prior Infections (Past 12 Months)
            </label>
            <input
              type="range"
              value={patientProfile.Infection_Freq}
              onChange={(e) =>
                handlePatientProfileChange(
                  "Infection_Freq",
                  parseInt(e.target.value) || 0
                )
              }
              min="0"
              max="10"
              className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 text-center font-mono">
              {patientProfile.Infection_Freq} infections
            </p>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-slate-200 dark:bg-slate-700 my-2" />

        {/* Prescribing Safeguards Section */}
        <div className="space-y-3 pt-2">
          <p className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">
            Prescribing Safeguards
          </p>

          {/* Penicillin Allergy - Pink/Red Accents */}
          <div className="flex items-start gap-2 bg-pink-50 dark:bg-pink-950/30 p-3 rounded border border-pink-200 dark:border-pink-900/50 hover:border-pink-300 dark:hover:border-pink-800 transition">
            <input
              type="checkbox"
              id="allergy"
              checked={patientProfile.Penicillin_Allergy || false}
              onChange={(e) =>
                handlePatientProfileChange(
                  "Penicillin_Allergy",
                  e.target.checked
                )
              }
              className="w-4 h-4 rounded border-pink-300 dark:border-pink-600 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-pink-500 accent-pink-500 cursor-pointer mt-0.5"
            />
            <label
              htmlFor="allergy"
              className="text-xs font-medium text-pink-700 dark:text-pink-300 cursor-pointer"
            >
              <span className="block font-semibold text-pink-800 dark:text-pink-200">
                Penicillin Allergy
              </span>
              <span className="text-pink-600 dark:text-pink-400/70 text-xs">
                (Contraindicates Beta-Lactams)
              </span>
            </label>
          </div>

          {/* Renal Impairment - Yellow/Orange Accents */}
          <div className="flex items-start gap-2 bg-yellow-50 dark:bg-yellow-950/30 p-3 rounded border border-yellow-200 dark:border-yellow-900/50 hover:border-yellow-300 dark:hover:border-yellow-800 transition">
            <input
              type="checkbox"
              id="renal"
              checked={patientProfile.Renal_Impaired || false}
              onChange={(e) =>
                handlePatientProfileChange("Renal_Impaired", e.target.checked)
              }
              className="w-4 h-4 rounded border-yellow-300 dark:border-yellow-600 bg-white dark:bg-slate-800 focus:ring-2 focus:ring-yellow-500 accent-yellow-500 cursor-pointer mt-0.5"
            />
            <label
              htmlFor="renal"
              className="text-xs font-medium text-yellow-700 dark:text-yellow-300 cursor-pointer"
            >
              <span className="block font-semibold text-yellow-800 dark:text-yellow-200">
                Renal Impairment
              </span>
              <span className="text-yellow-600 dark:text-yellow-400/70 text-xs">
                (Nephrotoxicity Risk)
              </span>
            </label>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-700 rounded-lg p-3 flex gap-2 mt-4">
            <AlertCircle className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-red-700 dark:text-red-300">{error}</p>
          </div>
        )}
      </div>

      {/* Generate Strategy Button - Fixed at bottom */}
      <div className="flex-shrink-0 p-4 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={onRunAnalysis}
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 disabled:from-slate-300 dark:disabled:from-slate-600 disabled:to-slate-300 dark:disabled:to-slate-600 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition shadow-md"
        >
          <Play className="w-4 h-4" />
          {isLoading ? "Analyzing..." : "Generate Strategy"}
        </button>
      </div>
    </div>
  );
}
