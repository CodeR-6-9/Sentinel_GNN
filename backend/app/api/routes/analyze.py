from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.orchestrator import sentinel_graph


class AnalyzeRequest(BaseModel):
    """
    Request model for antimicrobial resistance analysis.
    
    Attributes:
        isolate_id: Unique identifier for the bacterial isolate to analyze.
    """
    isolate_id: str


router = APIRouter()


@router.post("/")
async def analyze(request: AnalyzeRequest) -> dict:
    """
    Analyze a bacterial isolate for antimicrobial resistance.
    
    Invokes the Sentinel-GNN LangGraph orchestrator which:
    1. Runs GNN-based resistance prediction
    2. Verifies predictions against CARD knowledge graph
    3. Generates clinical strategy with collateral sensitivity analysis
    
    Args:
        request: AnalyzeRequest containing isolate_id.
        
    Returns:
        Full AgentState dictionary containing:
        - isolate_id: Input isolate identifier
        - ml_prediction: GNN model output
        - kg_verification: Knowledge graph verification results
        - strategy: Clinical recommendation
        - trace: Audit log of agent actions
    """
    # Initialize state with user input
    initial_state = {
        "isolate_id": request.isolate_id,
        "ml_prediction": {},
        "kg_verification": {},
        "strategy": "",
        "trace": []
    }
    
    # Invoke the compiled LangGraph
    result = sentinel_graph.invoke(initial_state)
    
    return result
