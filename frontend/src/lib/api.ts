import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export interface PatientProfile {
  Age: number;
  Gender: string;
  Diabetes: boolean;
  Hospital_before: boolean;
  Hypertension: boolean;
  Infection_Freq: number;
}

export interface AnalyzeResponse {
  isolate_id: string;
  patient_profile: PatientProfile;
  ml_prediction: {
    is_resistant: boolean;
    prediction: string;
    confidence: number;
    risk_factors: string[];
  };
  kg_verification: {
    validated: boolean;
    reason: string;
    mechanisms_found: number;
    genes: string[];
    mechanisms?: string[];
    antibiotic?: string;
    note?: string;
  };
  strategy: string;
  trace: string[];
}

export async function analyzeIsolate(
  isolateId: string,
  patientProfile: PatientProfile
): Promise<AnalyzeResponse> {
  console.log("🚦 1. analyzeIsolate function triggered!");
  console.log(`🎯 2. Target Backend URL: ${API_BASE_URL}/api/analyze`);
  console.log("📦 3. Payload:", { isolate_id: isolateId, patient_profile: patientProfile });

  try {
    const response = await axios.post<AnalyzeResponse>(
      `${API_BASE_URL}/api/analyze`,
      {
        isolate_id: isolateId,
        patient_profile: patientProfile,
      },
      {
        // Force timeout after 10 seconds so it doesn't hang infinitely
        timeout: 10000, 
      }
    );
    
    console.log("✅ 4. Response received from Python:", response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
        console.error("❌ AXIOS ERROR:", error.message);
        console.error("❌ STATUS:", error.response?.status);
        console.error("❌ DETAILS:", error.response?.data);
    } else {
        console.error("❌ UNKNOWN ERROR:", error);
    }
    throw error;
  }
}