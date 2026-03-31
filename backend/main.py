import os
import json
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
from app.agents.nodes.pharmacist import pharmacist_node 
from app.agents.nodes.procurement import procurement_node 

app = FastAPI(title="Sentinel-GNN Agent API")

# ---  CORS MIDDLEWARE ---
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

# 🎯 UPGRADED STATE: Now includes Logistics memory
class AgentState(TypedDict):
    isolate_id: str
    patient_profile: Dict[str, Any]
    ml_prediction: Dict[str, Any]
    kg_verification: Dict[str, Any]
    strategy: str
    trace: List[str]
    selected_drug: str                 
    pharmacist_review: Dict[str, Any]   
    procurement_order: Dict[str, Any]   

# --- 3. BUILD THE MULTI-AGENT GRAPH ---
workflow = StateGraph(AgentState)

# Add our production nodes
workflow.add_node("Predictor", predictor_node)
workflow.add_node("Verifier", verifier_node)
workflow.add_node("Strategist", strategist_node)
workflow.add_node("Pharmacist", pharmacist_node)      
workflow.add_node("Procurement", procurement_node)    

# --- ⛓️ DEFINE THE SEQUENTIAL FLOW ---
workflow.set_entry_point("Predictor")

# Step 1: Predictor (ML) -> Verifier (Genomic DB)
workflow.add_edge("Predictor", "Verifier")
# Step 2: Verifier (Genomic DB) -> Strategist (Clinical Logic)
workflow.add_edge("Verifier", "Strategist") 
# Step 3: Strategist -> Pharmacist (Safety & Formulary)
workflow.add_edge("Strategist", "Pharmacist")         
# Step 4: Pharmacist -> Procurement (Supply Chain)
workflow.add_edge("Pharmacist", "Procurement")        
# Step 5: Procurement -> Finalize
workflow.add_edge("Procurement", END)                 

# Compile the final agent
sentinel_agent = workflow.compile()

# --- 4. FASTAPI ENDPOINTS ---

# 🎯 NEW: The Pharmacy Inventory Route for the Global Dashboard
@app.get("/api/inventory")
async def get_inventory():
    """Fetches the live pharmacy inventory for the frontend dashboard."""
    backend_root = os.path.abspath(os.path.dirname(__file__))
    inventory_path = os.path.join(backend_root, "data", "pharmacy_inventory.json")
    
    try:
        with open(inventory_path, "r") as f:
            db = json.load(f)
            return db["inventory"]
    except Exception as e:
        return {"error": f"Could not load inventory: {str(e)}"}


# 🎯 EXISTING: The Main Analysis Route for the Doctor's Dashboard
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
        "trace": [],
        "selected_drug": "",                 
        "pharmacist_review": {},             
        "procurement_order": {}              
    }
    
    # Run the full agent pipeline (Predictor -> Verifier -> Strategist -> Pharmacist -> Procurement)
    final_state = sentinel_agent.invoke(initial_state)
    
    # Return the unified payload expected by the Next.js Frontend
    return {
        "isolate_id": final_state["isolate_id"],
        "patient_profile": final_state["patient_profile"],
        "ml_prediction": final_state["ml_prediction"],
        "kg_verification": final_state["kg_verification"],
        "strategy": final_state["strategy"],
        "trace": final_state["trace"],
        "pharmacist_review": final_state.get("pharmacist_review", {}), 
        "procurement_order": final_state.get("procurement_order", {})  
    }

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)