import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export interface AnalyzeResponse {
  isolate_id: string;
  ml_prediction: {
    is_resistant: boolean;
    prediction: string;
    confidence: number;
    top_genes: string[];
  };
  kg_verification: {
    genes_found_in_card: boolean;
    genes_verified: string[];
    resistance_mechanism: string;
    literature_support: number;
    confidence_score: number;
  };
  strategy: string;
  trace: string[];
}

/**
 * Sends a POST request to the backend API to analyze a bacterial isolate.
 *
 * @param isolateId - The unique identifier of the bacterial isolate
 * @returns Promise resolving to the analysis response containing predictions, verification, and strategy
 * @throws Error if the API request fails
 */
export async function analyzeIsolate(isolateId: string): Promise<AnalyzeResponse> {
  try {
    const response = await axios.post<AnalyzeResponse>(`${API_BASE_URL}/api/analyze`, {
      isolate_id: isolateId,
    });
    return response.data;
  } catch (error) {
    console.error("Error analyzing isolate:", error);
    throw error;
  }
}
