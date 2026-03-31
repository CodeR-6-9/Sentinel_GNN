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
    Node 1: ML Predictor Agent - SentinelMLP
    
    Calls production PyTorch MLP inference with patient epidemiological profile.
    """
    try:
        print("\n📊 [DEBUG] Predictor Node: Starting ML inference...")
        patient_profile = state["patient_profile"]
        isolate_id = state["isolate_id"]
        print(f"  Isolate: {isolate_id}")
        
        # Extract patient features from PatientProfile
        age = float(patient_profile.get("Age", 50))
        gender_raw = patient_profile.get("Gender", "M")
        diabetes = float(patient_profile.get("Diabetes", False))
        hospital_before = float(patient_profile.get("Hospital_before", False))
        hypertension = float(patient_profile.get("Hypertension", False))
        infection_freq = float(patient_profile.get("Infection_Freq", 0))
        
        # 🔥 CRITICAL FIX: Map Gender exactly as the training script did (M=1.0, F=0.0)
        gender_mapping = {
            "M": 1.0, "Male": 1.0, "m": 1.0,
            "F": 0.0, "Female": 0.0, "f": 0.0,
            "O": 0.0, "Other": 0.0
        }
        gender_encoded = gender_mapping.get(gender_raw, 0.0)  # Default to 0.0
        
        # Prepare 6-feature list for production model
        features = [age, gender_encoded, diabetes, hospital_before, hypertension, infection_freq]
        
        # Call production SentinelMLP inference
        logger.info(f"Invoking SentinelMLP for {isolate_id}")
        print(f"  Features (6-element): [Age={age}, Gender={gender_encoded}, Diabetes={diabetes}, Hospital_before={hospital_before}, Hypertension={hypertension}, Infection_Freq={infection_freq}]")
        print(f"  → Calling run_gnn_inference()...")
        
        result = run_gnn_inference(features)
        
        # 🛡️ THE BULLETPROOF EXTRACTION: Use .get() with safe defaults
        prediction_code = result.get("prediction", 0)  # 1 (Resistant) or 0 (Susceptible)
        
        # Handle if confidence comes as 85.0 (percentage) or 0.85 (decimal)
        raw_conf = result.get("confidence", 0.0)
        probability = result.get("probability", raw_conf / 100 if raw_conf > 1 else raw_conf)
        
        # MLP doesn't have driving factors yet, default to empty list
        driving_factors = result.get("driving_factors", [])
        
        print(f"  ← Result: prediction={prediction_code}, confidence={probability:.2%}")
        
        # Convert prediction code to string
        prediction_str = "Resistant" if prediction_code == 1 else "Susceptible"
        
        # Populate ML prediction results
        state["ml_prediction"] = {
            "is_resistant": prediction_code == 1,
            "prediction": prediction_str,
            "confidence": float(probability),
            "risk_factors": driving_factors
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
        print(f"❌ {error_msg}")
        state["trace"].append(f"✗ {error_msg}")
        state["ml_prediction"] = {
            "is_resistant": False,
            "prediction": "Error",
            "confidence": 0.0,
            "risk_factors": []
        }
        return state