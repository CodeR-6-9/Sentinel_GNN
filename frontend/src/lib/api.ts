import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export interface PatientProfile {
  Age: number;
  Hospital_before: boolean;
  Infection_Freq: number;
  Penicillin_Allergy?: boolean;
  Renal_Impaired?: boolean;
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
  pharmacist_review?: {
    status: string;
    formulary: string;
    warnings: string[];
    cost_usd: number;
  };
  procurement_order?: {
    status: string;
    po_number?: string;
    drug?: string;
    quantity?: number;
    total_cost_usd?: number;
    lead_time_days?: number;
    alert?: string;
    current_stock?: number;
  };
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