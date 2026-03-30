from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, TypedDict
from langgraph.graph import StateGraph, END

# Import our Engines
from app.models.gnn import run_gnn_inference
from app.db.neo4j_client import verify_resistance_mechanisms

app = FastAPI(title="Sentinel-GNN Agent API")

# --- 1. DATA MODELS ---
class PatientData(BaseModel):
    features: List[float]  # [Age, Gender, Diabetes, Hospital_before, Hypertension, Infection_Freq]

class AgentState(TypedDict):
    features: List[float]
    gnn_prediction: int
    gnn_probability: float
    driving_factors: List[str]
    card_verification: str
    final_report: dict

# --- 2. LANGGRAPH NODES ---
def predict_node(state: AgentState):
    """Runs the PyTorch GAT model"""
    result = run_gnn_inference(state["features"])
    return {
        "gnn_prediction": result["prediction"],
        "gnn_probability": result["probability"],
        "driving_factors": result["driving_factors"]
    }

def verify_node(state: AgentState):
    """Cross-references prediction with Neo4j CARD database"""
    if state["gnn_prediction"] == 1:
        # If resistant, check CARD for Ciprofloxacin (fluoroquinolone) mechanisms
        verification = verify_resistance_mechanisms("fluoroquinolone antibiotic")
    else:
        verification = "Patient predicted susceptible. Standard antibiotic protocols apply."
    return {"card_verification": verification}

def strategist_node(state: AgentState):
    """Formats the final payload for the 3D Next.js UI"""
    report = {
        "status": "Resistant 🚨" if state["gnn_prediction"] == 1 else "Susceptible ✅",
        "confidence": f"{state['gnn_probability'] * 100:.1f}%",
        "highlight_nodes": state["driving_factors"],  # Tells Three.js which nodes to glow pink!
        "clinical_context": state["card_verification"]
    }
    return {"final_report": report}

# --- 3. BUILD THE GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("Predictor", predict_node)
workflow.add_node("Verifier", verify_node)
workflow.add_node("Strategist", strategist_node)

workflow.set_entry_point("Predictor")
workflow.add_edge("Predictor", "Verifier")
workflow.add_edge("Verifier", "Strategist")
workflow.add_edge("Strategist", END)

sentinel_agent = workflow.compile()

# --- 4. FASTAPI ENDPOINT ---
@app.post("/analyze")
def analyze_patient(data: PatientData):
    """The endpoint the Next.js UI will call"""
    initial_state = {"features": data.features}
    
    # Run the LangGraph agent!
    result = sentinel_agent.invoke(initial_state)
    
    return result["final_report"]