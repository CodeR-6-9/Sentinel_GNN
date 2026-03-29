from typing import TypedDict, Any


class AgentState(TypedDict):
    """
    Defines the state for the LangGraph epidemiological orchestration layer.
    
    Attributes:
        isolate_id: Unique identifier for the bacterial isolate being analyzed.
        patient_profile: Dictionary containing patient demographics (Age, Gender, Diabetes, Hospital_before).
        ml_prediction: Dictionary containing GNN model output (prediction, confidence, risk_factors).
        kg_verification: Dictionary containing clinical guideline verification results.
        strategy: Final clinical recommendation string.
        trace: List of log messages tracking agent actions throughout the workflow.
    """
    isolate_id: str
    patient_profile: dict
    ml_prediction: dict
    kg_verification: dict
    strategy: str
    trace: list[str]
