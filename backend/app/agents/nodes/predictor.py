"""
Predictor Agent Node

ML inference on patient epidemiological profile using SentinelMLP (4-Feature Pivot).
"""

import logging
from app.schemas.analysis_types import AgentState
from app.ml.gnn import run_gnn_inference

logger = logging.getLogger(__name__)

# ============================================================================
# NODE 1: ML PREDICTOR AGENT (4-FEATURE PIVOT)
# ============================================================================

def predictor_node(state: AgentState) -> AgentState:
    """
    Node 1: ML Predictor Agent - SentinelMLP
    
    Calls production PyTorch MLP inference with the 4-feature patient profile.
    Features: [isolate_id (String), Age, Hospital_before, Infection_Freq]
    """
    try:
        print("\n📊 [DEBUG] Predictor Node: Starting ML inference...")
        patient_profile = state["patient_profile"]
        isolate_id = state.get("isolate_id", "Unknown")
        print(f"  Isolate (Strain): {isolate_id}")
        
        # Extract the 3 Clinical Features
        age = float(patient_profile.get("Age", 50))
        hospital_before = float(patient_profile.get("Hospital_before", False))
        infection_freq = float(patient_profile.get("Infection_Freq", 0))
        
        # 🎯 FIX: Pass the raw string to GNN.py. Let GNN.py handle the translation!
        features = [isolate_id, age, hospital_before, infection_freq]
        
        logger.info(f"Invoking SentinelMLP for {isolate_id}")
        print(f"  Features (4-element): [Strain='{isolate_id}', Age={age}, Hospital_before={hospital_before}, Infection_Freq={infection_freq}]")
        print(f"  → Calling run_gnn_inference()...")
        
        # Run Inference
        result = run_gnn_inference(features)
        
        # Extract results safely
        prediction_code = result.get("prediction", 0)  
        probability = result.get("probability", 0.0)
        driving_factors = result.get("driving_factors", [])
        
        print(f"  ← Result: prediction={prediction_code}, confidence={probability:.2%}")
        
        # Convert prediction code to string
        prediction_str = "Resistant" if prediction_code == 1 else "Susceptible"
        
        # Populate ML prediction state
        state["ml_prediction"] = {
            "is_resistant": prediction_code == 1,
            "prediction": prediction_str,
            "confidence": float(probability),
            "risk_factors": driving_factors
        }
        
        # Business Logic: Moderate confidence warning
        if prediction_code == 1 and 0.45 <= probability <= 0.65:
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