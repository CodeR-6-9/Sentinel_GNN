import os
import json
import asyncio
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

# The Pharmacy Inventory Route for the Global Dashboard
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


# The Main Analysis Route for the Doctor's Dashboard
@app.post("/api/analyze")
async def analyze_patient(data: AnalysisRequest):
    """
    Main Entry Point: Orchestrates the LangGraph agent execution.
    """
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
    
    final_state = sentinel_agent.invoke(initial_state)
    
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


# ==========================================================
# AI Chatbot Consultation Route
# ==========================================================
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatContext(BaseModel):
    patient_profile: Optional[Dict[str, Any]] = None
    strategy: Optional[str] = None
    drug: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    context: Optional[ChatContext] = None

@app.post("/api/chat")
async def chat_with_specialist(request: ChatRequest):
    user_msg = request.message.lower()
    await asyncio.sleep(1.5) # Simulate AI typing
    
    # -------------------------------------------------------------
    #  CONTEXT AWARENESS LOGIC
    # -------------------------------------------------------------
    patient = request.context.patient_profile if request.context and request.context.patient_profile else {}
    selected_drug = request.context.drug if request.context and request.context.drug else "the selected drug"
    age = patient.get("Age", "unknown")
    allergy = "a Penicillin allergy" if str(patient.get("Penicillin_Allergy", "")).lower() == "true" else "no known allergies"
    
    # ==========================================================
    #  MOCK AI RESPONSES (Reads the Patient Context!)
    # ==========================================================
    if "history" in user_msg or "prior" in user_msg or "constraint" in user_msg:
        reply = f"Noted. I see this patient is {age} years old with {allergy}. If there is additional cardiac history (like prolonged QT intervals), we should avoid Fluoroquinolones entirely. Should I recalculate the primary therapy to prioritize a Carbapenem instead of {selected_drug}?"
    elif "alternative" in user_msg or "kidney" in user_msg or "renal" in user_msg:
        reply = f"Given the patient's profile (Age {age}), if their renal function drops, {selected_drug} will require strict dose adjustment. A safer alternative for severe renal impairment without compromising efficacy against this resistant strain would be Aztreonam. Shall I check pharmacy stock for Aztreonam?"
    else:
        reply = f"I've analyzed the strategy recommending {selected_drug} for this {age}-year-old patient. Based on the {allergy} and the infection history, this is currently the safest empiric choice. What specific adjustments or constraints would you like to add?"

    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    # Start the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)