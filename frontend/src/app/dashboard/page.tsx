"use client";

import React, { useState } from "react";
import { AlertCircle, Zap, Play } from "lucide-react";
import Scene from "@/components/3d/Scene";
import AgentTrace from "@/components/chat/AgentTrace";
import { analyzeIsolate, AnalyzeResponse, PatientProfile } from "@/lib/api";

export default function DashboardPage() {
  // State Management
  const [isolateId, setIsolateId] = useState<string>("");
  const [patientProfile, setPatientProfile] = useState<PatientProfile>({
    Age: 65,
    Gender: "M",
    Diabetes: false,
    Hospital_before: true,
    Hypertension: false,
    Infection_Freq: 0,
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [traceList, setTraceList] = useState<string[]>([]);
  const [riskFactors, setRiskFactors] = useState<string[]>([]);
  const [strategy, setStrategy] = useState<string>("");
  const [mlPrediction, setMlPrediction] = useState<{
    prediction: string;
    confidence: number;
  } | null>(null);

  /**
   * Handle the Run Analysis button click
   */
  const handleRunAnalysis = async () => {
    if (!isolateId.trim()) {
      setError("Please enter an Isolate ID");
      return;
    }

    setIsLoading(true);
    setError(null);
    setTraceList([]);
    setRiskFactors([]);
    setStrategy("");
    setMlPrediction(null);

    try {
      const response: AnalyzeResponse = await analyzeIsolate(isolateId, patientProfile);

      // Update state with response data
      setTraceList(response.trace);
      setRiskFactors(response.ml_prediction.risk_factors);
      setStrategy(response.strategy);
      setMlPrediction({
        prediction: response.ml_prediction.prediction,
        confidence: response.ml_prediction.confidence,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to analyze isolate. Ensure the backend is running."
      );
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle input field changes
   */
  const handleIsolateIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIsolateId(e.target.value);
    setError(null);
  };

  const handlePatientProfileChange = (field: keyof PatientProfile, value: unknown) => {
    setPatientProfile((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <main className="w-screen h-screen bg-slate-950 text-white flex overflow-hidden">
      {/* Left Side: Fixed 3D Gene Network */}
      <div className="flex-1 rounded-lg overflow-hidden border border-slate-700 shadow-2xl m-6 mr-0">
        <Scene flaggedGenes={riskFactors} />
      </div>

      {/* Right Side: Scrollable Control Panel */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-4 p-6 pr-6">
          {/* Header */}
          <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg p-4 shadow-lg">
            <h1 className="text-xl font-bold">Sentinel-GNN</h1>
            <p className="text-xs text-cyan-100 mt-1">Epidemiological Risk Analysis</p>
          </div>

          {/* Isolate ID Input */}
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
            <label className="block text-xs font-semibold text-slate-400 mb-2">
              Isolate ID
            </label>
            <input
              type="text"
              value={isolateId}
              onChange={handleIsolateIdChange}
              placeholder="e.g., AMR_001"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            />
          </div>

          {/* Patient Profile Input */}
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700 space-y-3">
            <p className="text-xs font-semibold text-slate-400">Patient Profile</p>

            {/* Age */}
            <div>
              <label className="block text-xs text-slate-400 mb-1">Age</label>
              <input
                type="number"
                value={patientProfile.Age}
                onChange={(e) => handlePatientProfileChange("Age", parseInt(e.target.value) || 0)}
                min="0"
                max="120"
                className="w-full px-3 py-1 bg-slate-800 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            {/* Gender */}
            <div>
              <label className="block text-xs text-slate-400 mb-1">Gender</label>
              <select
                value={patientProfile.Gender}
                onChange={(e) => handlePatientProfileChange("Gender", e.target.value)}
                className="w-full px-3 py-1 bg-slate-800 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>

            {/* Diabetes */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="diabetes"
                checked={patientProfile.Diabetes}
                onChange={(e) => handlePatientProfileChange("Diabetes", e.target.checked)}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 focus:ring-2 focus:ring-cyan-500"
              />
              <label htmlFor="diabetes" className="text-xs text-slate-400">
                Diabetes
              </label>
            </div>

            {/* Hospital History */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="hospital"
                checked={patientProfile.Hospital_before}
                onChange={(e) => handlePatientProfileChange("Hospital_before", e.target.checked)}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 focus:ring-2 focus:ring-cyan-500"
              />
              <label htmlFor="hospital" className="text-xs text-slate-400">
                Previous Hospitalization
              </label>
            </div>

            {/* Hypertension */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="hypertension"
                checked={patientProfile.Hypertension}
                onChange={(e) => handlePatientProfileChange("Hypertension", e.target.checked)}
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 focus:ring-2 focus:ring-cyan-500"
              />
              <label htmlFor="hypertension" className="text-xs text-slate-400">
                Hypertension
              </label>
            </div>

            {/* Infection Frequency */}
            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Infection Frequency (Past Year)
              </label>
              <input
                type="range"
                value={patientProfile.Infection_Freq}
                onChange={(e) => handlePatientProfileChange("Infection_Freq", parseInt(e.target.value) || 0)}
                min="0"
                max="10"
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-500"
              />
              <p className="text-xs text-slate-500 mt-1 text-center">{patientProfile.Infection_Freq} infections</p>
            </div>
          </div>

          {/* Run Analysis Button */}
          <button
            onClick={handleRunAnalysis}
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded flex items-center justify-center gap-2 transition"
          >
            <Play className="w-4 h-4" />
            {isLoading ? "Analyzing..." : "Run Analysis"}
          </button>

          {/* Error Display */}
          {error && (
            <div className="bg-red-900/40 border border-red-600 rounded-lg p-3 flex gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-red-300">{error}</p>
            </div>
          )}

          {/* Results Section */}
          {mlPrediction && (
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-700 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-400">Prediction</span>
                <span
                  className={`text-sm font-bold ${
                    mlPrediction.prediction === "Resistant"
                      ? "text-red-400"
                      : "text-emerald-400"
                  }`}
                >
                  {mlPrediction.prediction}
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full"
                  style={{ width: `${mlPrediction.confidence * 100}%` }}
                />
              </div>
              <p className="text-xs text-slate-400">
                Confidence: <span className="text-cyan-400 font-mono">{(mlPrediction.confidence * 100).toFixed(1)}%</span>
              </p>
            </div>
          )}

          {/* Risk Factors Display */}
          {riskFactors.length > 0 && (
            <div className="bg-slate-900 rounded-lg p-3 border border-slate-700 space-y-2">
              <p className="text-xs font-semibold text-slate-400">Contributing Risk Factors</p>
              <div className="flex flex-wrap gap-2">
                {riskFactors.map((factor) => (
                  <span key={factor} className="px-2 py-1 bg-pink-600/30 border border-pink-500 rounded text-xs text-pink-200">
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Strategy Section */}
          {strategy && (
            <div className="bg-slate-900 rounded-lg p-3 border border-emerald-700 border-l-4 border-l-emerald-500">
              <div className="flex items-start gap-2">
                <Zap className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs">
                  <p className="font-semibold text-emerald-400 mb-1">Clinical Strategy</p>
                  <p className="text-slate-300 leading-relaxed">{strategy}</p>
                </div>
              </div>
            </div>
          )}

          {/* Agent Trace Section */}
          <div className="min-h-[320px] bg-slate-900/60 rounded-lg border border-slate-600 shadow-inner">
            <AgentTrace traces={traceList} />
          </div>
        </div>
      </main>
  );
}
