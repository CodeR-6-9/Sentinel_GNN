from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# --- 1. IMPORT PRODUCTION NODES ---
from app.agents.nodes.predictor import predictor_node
from app.agents.nodes.strategist import strategist_node
from app.agents.nodes.verifier import verifier_node 

app = FastAPI(title="Sentinel-GNN Agent API")

# --- 🛡️ CORS MIDDLEWARE ---
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATA MODELS (Aligned with Frontend) ---
class PatientProfile(BaseModel):
    Age: int
    Hospital_before: bool
    Infection_Freq: int
    Penicillin_Allergy: Optional[bool] = False
    Renal_Impaired: Optional[bool] = False

class AnalysisRequest(BaseModel):
    isolate_id: str
    patient_profile: PatientProfile

# This is the shared "brain" that passes data between nodes
class AgentState(TypedDict):
    isolate_id: str
    patient_profile: Dict[str, Any]
    ml_prediction: Dict[str, Any]
    kg_verification: Dict[str, Any]
    strategy: str
    trace: List[str]

# --- 3. BUILD THE MULTI-AGENT GRAPH ---
workflow = StateGraph(AgentState)

# Add our production nodes
workflow.add_node("Predictor", predictor_node)
workflow.add_node("Verifier", verifier_node)
workflow.add_node("Strategist", strategist_node)

# --- ⛓️ DEFINE THE SEQUENTIAL FLOW ---
workflow.set_entry_point("Predictor")

# Step 1: Predictor (ML) -> Verifier (Genomic DB)
workflow.add_edge("Predictor", "Verifier")

# Step 2: Verifier (Genomic DB) -> Strategist (Clinical Logic)
workflow.add_edge("Verifier", "Strategist") 

# Step 3: Strategist -> Finalize
workflow.add_edge("Strategist", END)

# Compile the final agent
sentinel_agent = workflow.compile()

# --- 4. FASTAPI ENDPOINT ---
@app.post("/api/analyze")
async def analyze_patient(data: AnalysisRequest):
    """
    Main Entry Point: Orchestrates the LangGraph agent execution.
    """
    # Initialize the state with incoming request data
    initial_state: AgentState = {
        "isolate_id": data.isolate_id,
        "patient_profile": data.patient_profile.dict(),
        "ml_prediction": {},
        "kg_verification": {"validated": False, "genes": [], "details": []}, 
        "strategy": "",
        "trace": []
    }
    
    # Run the full agent pipeline (Predictor -> Verifier -> Strategist)
    final_state = sentinel_agent.invoke(initial_state)
    
    # Return the unified payload expected by the Next.js Frontend
    return {
        "isolate_id": final_state["isolate_id"],
        "patient_profile": final_state["patient_profile"],
        "ml_prediction": final_state["ml_prediction"],
        "kg_verification": final_state["kg_verification"],
        "strategy": final_state["strategy"],
        "trace": final_state["trace"]
    }

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)