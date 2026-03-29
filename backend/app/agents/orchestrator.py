from langgraph.graph import StateGraph, END
from app.agents.state import AgentState


def mock_gnn_call(isolate_id: str, patient_profile: dict) -> dict:
    """
    Mock GNN prediction function for epidemiological patient graph.
    In production, this would call the actual PyTorch patient risk model.
    
    Considers patient risk factors:
    - Age, Diabetes, Hypertension, Hospital_before → baseline resistance risk
    - Infection_Freq → high infection frequency increases resistance risk
    
    Args:
        isolate_id: Bacterial isolate identifier.
        patient_profile: Dict with Age, Gender, Diabetes, Hypertension, Hospital_before, Infection_Freq.
        
    Returns:
        Dictionary with prediction results including confidence and contributing risk factors.
    """
    # Simulate risk calculation based on patient factors
    risk_score = 0.0
    contributing_factors = []
    
    # Calculate risk based on patient profile
    if patient_profile.get("Hospital_before"):
        risk_score += 0.25
        contributing_factors.append("Hospital_before")
    
    if patient_profile.get("Diabetes"):
        risk_score += 0.20
        contributing_factors.append("Diabetes")
    
    if patient_profile.get("Hypertension"):
        risk_score += 0.15
        contributing_factors.append("Hypertension")
    
    infection_freq = patient_profile.get("Infection_Freq", 0)
    if infection_freq > 3:
        risk_score += 0.20
        contributing_factors.append("High_Infection_Freq")
    
    age = patient_profile.get("Age", 50)
    if age > 70:
        risk_score += 0.10
        contributing_factors.append("Advanced_Age")
    
    # Normalize confidence to 0.7-0.95 range
    confidence = min(0.95, max(0.70, risk_score + 0.40))
    
    return {
        "is_resistant": confidence > 0.80,
        "prediction": "Resistant" if confidence > 0.80 else "Susceptible",
        "confidence": round(confidence, 2),
        "risk_factors": contributing_factors
    }


def predictor_node(state: AgentState) -> AgentState:
    """
    Node 1: Predictor Agent
    Runs GNN model inference based on patient risk profile.
    
    Args:
        state: Current AgentState.
        
    Returns:
        Updated AgentState with ml_prediction and trace.
    """
    isolate_id = state["isolate_id"]
    patient_profile = state["patient_profile"]
    
    # Call mock GNN with patient profile
    ml_result = mock_gnn_call(isolate_id, patient_profile)
    
    # Update state
    state["ml_prediction"] = ml_result
    state["trace"].append(
        f"GNN predicted resistance with confidence {ml_result['confidence']:.2f} "
        f"based on patient risk factors: {', '.join(ml_result['risk_factors'])}"
    )
    
    return state


def verifier_node(state: AgentState) -> AgentState:
    """
    Node 2: Verifier Agent
    Verifies patient risk factors against clinical epidemiological guidelines.
    
    Args:
        state: Current AgentState with ml_prediction populated.
        
    Returns:
        Updated AgentState with kg_verification and trace.
    """
    # Extract risk factors from ML prediction
    risk_factors = state["ml_prediction"].get("risk_factors", [])
    patient_profile = state["patient_profile"]
    
    # Simulate clinical guideline verification for epidemiological factors
    clinical_guideline_verification = {
        "risk_factors_validated": True,
        "factors_verified": risk_factors,
        "clinical_guideline": "CDC/WHO antimicrobial stewardship protocol",
        "guidelines_matched": 3,  # Number of clinical guidelines matched
        "confidence_score": 0.88,
        "additional_context": f"Age: {patient_profile.get('Age')}, "
                            f"Hospital_History: {patient_profile.get('Hospital_before', False)}"
    }
    
    # Update state
    state["kg_verification"] = clinical_guideline_verification
    state["trace"].append(
        f"Verified patient risk factors against clinical guidelines. "
        f"Found {clinical_guideline_verification['guidelines_matched']} matching epidemiological protocols. "
        f"Guideline: {clinical_guideline_verification['clinical_guideline']}"
    )
    
    return state


def strategist_node(state: AgentState) -> AgentState:
    """
    Node 3: Strategist Agent
    Generates clinical strategy based on ML prediction and knowledge graph verification.
    
    Args:
        state: Current AgentState with ml_prediction and kg_verification.
        
    Returns:
        Updated AgentState with strategy and trace.
    """
    prediction_confidence = state["ml_prediction"].get("confidence", 0.0)
    kg_confidence = state["kg_verification"].get("confidence_score", 0.0)
    
    # Generate clinical strategy
    combined_confidence = (prediction_confidence + kg_confidence) / 2
    
    if combined_confidence > 0.85:
        clinical_strategy = (
            "STRONG RECOMMENDATION: Switch to alternative antibiotics. "
            "Collateral Sensitivity Analysis suggests Fluoroquinolones as backup therapy. "
            "Monitor for horizontal gene transfer."
        )
    else:
        clinical_strategy = (
            "MODERATE RECOMMENDATION: Consider combination therapy. "
            "Further phenotypic testing recommended before final decision."
        )
    
    # Update state
    state["strategy"] = clinical_strategy
    state["trace"].append(
        f"Generated clinical strategy based on combined confidence ({combined_confidence:.2f}): {clinical_strategy}"
    )
    
    return state


# Build the LangGraph state machine
def build_sentinel_graph():
    """
    Constructs and compiles the Sentinel-GNN LangGraph orchestration graph.
    
    The graph follows a linear pipeline:
    predictor_node -> verifier_node -> strategist_node -> END
    
    Returns:
        Compiled graph executable.
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("predictor", predictor_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("strategist", strategist_node)
    
    # Set entry point
    graph.set_entry_point("predictor")
    
    # Add edges
    graph.add_edge("predictor", "verifier")
    graph.add_edge("verifier", "strategist")
    graph.add_edge("strategist", END)
    
    # Compile
    return graph.compile()


# Compile the graph into executable form
sentinel_graph = build_sentinel_graph()
