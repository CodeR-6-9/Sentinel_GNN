"""
Predictor Agent Node

ML inference on patient epidemiological profile using SentinelMLP.
"""

import logging
from app.schemas.analysis_types import AgentState

from app.ml.gnn import run_gnn_inference

logger = logging.getLogger(__name__)


# ============================================================================
# NODE 1: ML PREDICTOR AGENT
# ============================================================================

def predictor_node(state: AgentState) -> AgentState:
    """
    Node 1: ML Predictor Agent - SentinelMLP with Gradient-Based XAI
    
    Calls production PyTorch MLP inference with patient epidemiological profile.
    
    Feature Mapping:
    - Converts Pydantic PatientProfile to 6-value list: 
      [Age, Gender (1.0/2.0/3.0), Diabetes, Hospital_before, Hypertension, Infection_Freq]
    - Calls run_gnn_inference() which returns:
      {prediction (0/1), probability, driving_factors, threshold_used}
    - Converts prediction 1→"Resistant", 0→"Susceptible"
    
    Args:
        state: Current AgentState from LangGraph
    
    Returns:
        Updated AgentState with ml_prediction populated and trace appended
    """
    try:
        print("\n📊 [DEBUG] Predictor Node: Starting ML inference...")
        patient_profile = state["patient_profile"]
        isolate_id = state["isolate_id"]
        print(f"  Isolate: {isolate_id}")
        
        # Extract patient features from PatientProfile
        age = float(patient_profile.get("Age", 50))
        gender_raw = patient_profile.get("Gender", "Other")
        diabetes = float(patient_profile.get("Diabetes", False))
        hospital_before = float(patient_profile.get("Hospital_before", False))
        hypertension = float(patient_profile.get("Hypertension", False))
        infection_freq = float(patient_profile.get("Infection_Freq", 0))
        
        # Map Gender to numerical encoding:
        # "M" or "Male" → 1.0, "F" or "Female" → 2.0, "O" or "Other" → 3.0
        gender_mapping = {
            "M": 1.0, "Male": 1.0,
            "F": 2.0, "Female": 2.0,
            "O": 3.0, "Other": 3.0
        }
        gender_encoded = gender_mapping.get(gender_raw, 3.0)  # Default to 3.0 (Other)
        
        # Prepare 6-feature list for production model
        features = [age, gender_encoded, diabetes, hospital_before, hypertension, infection_freq]
        
        # Call production SentinelMLP inference
        logger.info(f"Invoking SentinelMLP for {isolate_id}")
        print(f"  Features (6-element): [Age={age}, Gender={gender_encoded}, Diabetes={diabetes}, Hospital_before={hospital_before}, Hypertension={hypertension}, Infection_Freq={infection_freq}]")
        print(f"  → Calling run_gnn_inference()...")
        result = run_gnn_inference(features)
        print(f"  ← Result: prediction={result.get('prediction')}, confidence={result.get('probability'):.2%}")
        
        # Extract results from model output
        prediction_code = result["prediction"]  # 1 (Resistant) or 0 (Susceptible)
        probability = result["probability"]
        driving_factors = result["driving_factors"]
        
        # Convert prediction code to string
        prediction_str = "Resistant" if prediction_code == 1 else "Susceptible"
        
        # Populate ML prediction results
        state["ml_prediction"] = {
            "is_resistant": prediction_code == 1,
            "prediction": prediction_str,
            "confidence": float(probability),
            "risk_factors": driving_factors if isinstance(driving_factors, list) else []
        }
        
        # Business Logic: Moderate confidence warning
        if prediction_code == 1 and 0.77 <= probability <= 0.85:
            warning_msg = (
                f"Model detected resistance patterns with moderate confidence "
                f"({probability:.2%}); clinical correlation advised."
            )
            state["trace"].append(warning_msg)
            logger.warning(warning_msg)
        
        # Standard trace log
        risk_factors_str = ', '.join(driving_factors) if driving_factors else 'None'
        state["trace"].append(
            f"✓ ML Predictor: {prediction_str} (confidence: {probability:.2%}) | "
            f"Driving factors: {risk_factors_str}"
        )
        print(f"✅ [DEBUG] Predictor Node: Complete")
        
        return state
    
    except Exception as e:
        error_msg = f"Predictor Node Error: {str(e)}"
        logger.error(error_msg)
        state["trace"].append(f"✗ {error_msg}")
        state["ml_prediction"] = {
            "is_resistant": False,
            "prediction": "Error",
            "confidence": 0.0,
            "risk_factors": []
        }
        return state