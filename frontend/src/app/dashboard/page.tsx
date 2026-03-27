"use client";

import React, { useState } from "react";
import { AlertCircle, Zap, Play } from "lucide-react";
import Scene from "@/components/3d/Scene";
import AgentTrace from "@/components/chat/AgentTrace";
import { analyzeIsolate, AnalyzeResponse } from "@/lib/api";

export default function DashboardPage() {
  // State Management
  const [isolateId, setIsolateId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [traceList, setTraceList] = useState<string[]>([]);
  const [flaggedGenes, setFlaggedGenes] = useState<string[]>([]);
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
    setFlaggedGenes([]);
    setStrategy("");
    setMlPrediction(null);

    try {
      const response: AnalyzeResponse = await analyzeIsolate(isolateId);

      // Update state with response data
      setTraceList(response.trace);
      setFlaggedGenes(response.ml_prediction.top_genes);
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

  return (
    <main className="w-screen h-screen bg-slate-950 text-white overflow-hidden">
      {/* Grid Layout: 3D Canvas (Left) + Control Panel (Right) */}
      <div className="grid grid-cols-3 gap-6 h-full p-6">
        {/* Left Side: 3D Gene Network */}
        <div className="col-span-2 h-full rounded-lg overflow-hidden border border-slate-700 shadow-2xl">
          <Scene flaggedGenes={flaggedGenes} />
        </div>

        {/* Right Side: Control Panel */}
        <div className="col-span-1 flex flex-col gap-4 h-full">
          {/* Header */}
          <div className="bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg p-4 shadow-lg">
            <h1 className="text-xl font-bold">Sentinel-GNN</h1>
            <p className="text-xs text-cyan-100 mt-1">AMR Prediction & Discovery</p>
          </div>

          {/* Input Section */}
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

            {/* Run Analysis Button */}
            <button
              onClick={handleRunAnalysis}
              disabled={isLoading}
              className="w-full mt-3 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded flex items-center justify-center gap-2 transition"
            >
              <Play className="w-4 h-4" />
              {isLoading ? "Analyzing..." : "Run Analysis"}
            </button>
          </div>

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
          <div className="flex-1 min-h-0">
            <AgentTrace traces={traceList} />
          </div>
        </div>
      </div>
    </main>
  );
}
