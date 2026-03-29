from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.orchestrator import sentinel_graph


class PatientProfile(BaseModel):
    """Patient demographics for epidemiological risk assessment."""
    Age: int
    Gender: str
    Diabetes: bool
    Hospital_before: bool


class AnalyzeRequest(BaseModel):
    """
    Request model for epidemiological antimicrobial resistance analysis.
    
    Attributes:
        isolate_id: Unique identifier for the bacterial isolate to analyze.
        patient_profile: Patient demographics (Age, Gender, Diabetes, Hospital_before).
    """
    isolate_id: str
    patient_profile: PatientProfile


router = APIRouter()


@router.post("/")
async def analyze(request: AnalyzeRequest) -> dict:
    """
    Analyze a bacterial isolate with epidemiological context for antimicrobial resistance.
    
    Invokes the Sentinel-GNN LangGraph orchestrator which:
    1. Runs GNN-based resistance prediction using patient risk factors
    2. Verifies predictions against clinical epidemiological guidelines
    3. Generates clinical strategy with personalized recommendations
    
    Args:
        request: AnalyzeRequest containing isolate_id and patient_profile.
        
    Returns:
        Full AgentState dictionary containing:
        - isolate_id: Input isolate identifier
        - patient_profile: Input patient demographics
        - ml_prediction: GNN model output with risk factors
        - kg_verification: Clinical guideline verification results
        - strategy: Personalized clinical recommendation
        - trace: Audit log of agent actions
    """
    # Initialize state with user input
    initial_state = {
        "isolate_id": request.isolate_id,
        "patient_profile": request.patient_profile.dict(),
        "ml_prediction": {},
        "kg_verification": {},
        "strategy": "",
        "trace": []
    }
    
    # Invoke the compiled LangGraph
    result = sentinel_graph.invoke(initial_state)
    
    return result
