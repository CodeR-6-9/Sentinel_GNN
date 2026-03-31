"use client";

import React, { useState } from "react";
import { analyzeIsolate, AnalyzeResponse, PatientProfile } from "@/lib/api";
import PatientIntakeSidebar from "@/components/dashboard/PatientIntakeSidebar";
import RecommendationStage from "@/components/dashboard/RecommendationStage";
// NOTE: Make sure the import name matches the file you updated in the last step!
import EvidenceInspector from "@/components/dashboard/EvidenceInspector"; 

export default function AnalyzePage() {
  // --- 1. STATE MANAGEMENT ---
  const [isolateId, setIsolateId] = useState<string>("");
  const [patientProfile, setPatientProfile] = useState<PatientProfile>({
    Age: 65,
    Hospital_before: true,
    Infection_Freq: 0,
    Penicillin_Allergy: false,
    Renal_Impaired: false,
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

  // 🎯 NEW STATE: To hold the Neo4j genomic data
  const [kgVerification, setKgVerification] = useState<any>(null);

  /**
   * Unified handler for both isolateId and patientProfile changes
   */
  const handleChange = (
    field: keyof PatientProfile | "isolateId",
    value: unknown
  ) => {
    if (field === "isolateId") {
      setIsolateId(value as string);
      setError(null);
    } else {
      setPatientProfile((prev) => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  /**
   * Handle the Run Analysis button click
   */
  const handleRunAnalysis = async () => {
    if (!isolateId.trim()) {
      setError("Please enter a Bacterial Strain (Isolate ID)");
      return;
    }

    setIsLoading(true);
    setError(null);
    setTraceList([]);
    setRiskFactors([]);
    setStrategy("");
    setMlPrediction(null);
    setKgVerification(null); // Reset Neo4j data on new run

    try {
      const response: AnalyzeResponse = await analyzeIsolate(
        isolateId,
        patientProfile
      );

      // --- 2. UPDATE STATE FROM API RESPONSE ---
      setTraceList(response.trace);
      setRiskFactors(response.ml_prediction.risk_factors || []);
      setStrategy(response.strategy);
      setMlPrediction({
        prediction: response.ml_prediction.prediction,
        confidence: response.ml_prediction.confidence,
      });

      // 🎯 CAPTURE THE NEO4J DATA HERE
      setKgVerification(response.kg_verification);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to analyze isolate. Ensure the backend is running."
      );
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full h-full bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white flex overflow-hidden">
      {/* Left Panel: Patient Intake Sidebar (25%) */}
      <PatientIntakeSidebar
        isolateId={isolateId}
        patientProfile={patientProfile}
        onChange={handleChange}
        onRunAnalysis={handleRunAnalysis}
        isLoading={isLoading}
        error={error}
      />

      {/* Center Panel: Recommendation Stage (50%) - Action-First */}
      <RecommendationStage strategy={strategy} isLoading={isLoading} />

      {/* Right Panel: Evidence Inspector (25%) */}
      {/* 🎯 PASS THE NEW STATE TO THE INSPECTOR */}
      <EvidenceInspector
        riskFactors={riskFactors}
        mlPrediction={mlPrediction}
        traceList={traceList}
        kg_verification={kgVerification} 
      />
    </div>
  );
}