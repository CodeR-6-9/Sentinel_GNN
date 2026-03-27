from typing import TypedDict, Any


class AgentState(TypedDict):
    """
    Defines the state for the LangGraph orchestration layer.
    
    Attributes:
        isolate_id: Unique identifier for the bacterial isolate being analyzed.
        ml_prediction: Dictionary containing GNN model output (prediction, confidence, top_genes).
        kg_verification: Dictionary containing knowledge graph verification results.
        strategy: Final clinical recommendation string.
        trace: List of log messages tracking agent actions throughout the workflow.
    """
    isolate_id: str
    ml_prediction: dict
    kg_verification: dict
    strategy: str
    trace: list[str]
