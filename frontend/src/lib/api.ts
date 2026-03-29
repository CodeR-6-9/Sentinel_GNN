import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

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
    risk_factors_validated: boolean;
    factors_verified: string[];
    clinical_guideline: string;
    guidelines_matched: number;
    confidence_score: number;
    additional_context: string;
  };
  strategy: string;
  trace: string[];
}

/**
 * Sends a POST request to the backend API to analyze a bacterial isolate with patient context.
 *
 * @param isolateId - The unique identifier of the bacterial isolate
 * @param patientProfile - Patient demographics for epidemiological risk assessment
 * @returns Promise resolving to the analysis response with epidemiological context
 * @throws Error if the API request fails
 */
export async function analyzeIsolate(
  isolateId: string,
  patientProfile: PatientProfile
): Promise<AnalyzeResponse> {
  try {
    const response = await axios.post<AnalyzeResponse>(
      `${API_BASE_URL}/api/analyze`,
      {
        isolate_id: isolateId,
        patient_profile: patientProfile,
      }
    );
    return response.data;
  } catch (error) {
    console.error("Error analyzing isolate:", error);
    throw error;
  }
}
