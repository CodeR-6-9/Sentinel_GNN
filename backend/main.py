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

# --- AI & ENVIRONMENT IMPORTS ---
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# Load credentials from .env
load_dotenv() 

app = FastAPI(title="Sentinel-GNN Agent API")

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DATA MODELS ---
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

workflow.add_node("Predictor", predictor_node)
workflow.add_node("Verifier", verifier_node)
workflow.add_node("Strategist", strategist_node)
workflow.add_node("Pharmacist", pharmacist_node)      
workflow.add_node("Procurement", procurement_node)    

# SEQUENTIAL FLOW: ML -> Genomic DB -> Clinical Logic -> Safety/Cost -> Supply Chain
workflow.set_entry_point("Predictor")
workflow.add_edge("Predictor", "Verifier")
workflow.add_edge("Verifier", "Strategist") 
workflow.add_edge("Strategist", "Pharmacist")        
workflow.add_edge("Pharmacist", "Procurement")        
workflow.add_edge("Procurement", END)                

sentinel_agent = workflow.compile()

# --- 4. FASTAPI ENDPOINTS ---

@app.get("/api/inventory")
async def get_inventory():
    backend_root = os.path.abspath(os.path.dirname(__file__))
    inventory_path = os.path.join(backend_root, "data", "pharmacy_inventory.json")
    try:
        with open(inventory_path, "r") as f:
            db = json.load(f)
            return db["inventory"]
    except Exception as e:
        return {"error": f"Could not load inventory: {str(e)}"}

@app.post("/api/analyze")
async def analyze_patient(data: AnalysisRequest):
    is_mrsa = "MRSA" in data.isolate_id.upper()
    
    initial_state: AgentState = {
        "isolate_id": data.isolate_id,
        "patient_profile": data.patient_profile.model_dump(),
        "ml_prediction": {
            "is_resistant": True,
            "prediction": "Resistant",
            "confidence": 0.98,
            "risk_factors": ["High Infection Frequency", "Prior Hospitalization"]
        } if is_mrsa else {}, 
        "kg_verification": {"validated": False, "genes": [], "details": []}, 
        "strategy": "",
        "trace": ["⚠️ System Alert: Potential MRSA Path Activated"] if is_mrsa else [],
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

# --- 5. AI CHATBOT (RAG) ---
my_groq_key = os.getenv("GROQ_API_KEY")
# Using the updated, working Groq model
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.2, api_key=my_groq_key)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

backend_root = os.path.abspath(os.path.dirname(__file__))
chroma_path = os.path.join(backend_root, "chroma_db")

# Wrap in try/except so the server doesn't crash if DB isn't built
try:
    vector_store = Chroma(persist_directory=chroma_path, embedding_function=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
except Exception as e:
    print(f"⚠️ Warning: ChromaDB not loaded properly: {e}")
    retriever = None

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    context: Optional[Dict[str, Any]] = None

@app.post("/api/chat")
async def chat_with_specialist(request: ChatRequest):
    print("\n--- 🚨 INCOMING CHAT REQUEST ---")
    print(f"Message: {request.message}")
    print(f"Context Received: {request.context}")
    print(f"History Length: {len(request.history) if request.history else 0} messages")
    print("--------------------------------\n")

    user_msg = request.message
    
    # 1. BULLETPROOF CONTEXT HANDLING
    patient = {}
    if request.context:
        if "patient_profile" in request.context:
            patient = request.context["patient_profile"]
        else:
            patient = request.context
            
    # 2. RAG RETRIEVAL
    medical_context = ""
    if retriever:
        try:
            docs = retriever.invoke(user_msg)
            medical_context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"Retrieval error: {e}")
            
    # 3. BULLETPROOF HISTORY HANDLING
    formatted_history = []
    if request.history:
        for msg in request.history:
            role = msg.get("role", "").lower()
            text = msg.get("content") or msg.get("text") or ""
            
            if role == "user":
                formatted_history.append(HumanMessage(content=text))
            elif role in ["assistant", "model", "ai"]:
                formatted_history.append(AIMessage(content=text))
    
    # 4. PROMPT WITH HISTORY INJECTED
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are Sentinel, a clinical AI Copilot. You have full access to this patient's digital twin: {patient_profile}. Use this medical knowledge if relevant: {medical_context}."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{user_message}")
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "patient_profile": str(patient),
            "medical_context": medical_context,
            "chat_history": formatted_history,
            "user_message": user_msg
        })
        return {"reply": response.content}
    except Exception as e:
        return {"reply": f"AI processing error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)