"""
Sentinel-GNN Analysis Orchestration API Route

Orchestrates a 3-node LangGraph pipeline:
1. Predictor Node: PyTorch MLP inference on patient epidemiological profile
2. Verifier Node: Neo4j CARD database validation of resistance mechanisms
3. Strategist Node: Local dataset analysis for alternative drug recommendations

Architecture: Pydantic Models → LangGraph State → Agent Nodes → FastAPI Response
"""

import os
import logging
from typing import TypedDict
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from langgraph.graph import StateGraph, END

try:
    from gnn import inference
except ImportError:
    # Mock inference for development
    def inference(age, gender, diabetes, hospital_before, hypertension, infection_freq):
        """Mock GNN inference function for development."""
        confidence = 0.82
        prediction = "Resistant" if hospital_before or infection_freq > 3 else "Susceptible"
        driving_factors = []
        if hospital_before:
            driving_factors.append("Hospital_before")
        if diabetes:
            driving_factors.append("Diabetes")
        if hypertension:
            driving_factors.append("Hypertension")
        if infection_freq > 3:
            driving_factors.append("High_Infection_Freq")
        return prediction, confidence, driving_factors

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ============================================================================
# PYDANTIC MODELS (DATA VALIDATION)
# ============================================================================

class PatientProfile(BaseModel):
    """
    Patient demographics for epidemiological risk assessment.
    
    Attributes:
        Age: Patient age in years (0-120)
        Gender: Biological sex category
        Diabetes: Diabetes mellitus diagnosis status
        Hospital_before: Previous hospitalization history
        Hypertension: Hypertension diagnosis status
        Infection_Freq: Number of infections in past year (0-10+)
    """
    Age: int = Field(ge=0, le=120, description="Patient age in years")
    Gender: str = Field(description="Biological sex (Male/Female/Other)")
    Diabetes: bool = Field(description="Type 2 Diabetes diagnosis")
    Hospital_before: bool = Field(description="Previous hospitalization history")
    Hypertension: bool = Field(description="Hypertension diagnosis")
    Infection_Freq: int = Field(ge=0, le=10, description="Infections in past year")


class AnalyzeRequest(BaseModel):
    """
    Request model for epidemiological antimicrobial resistance analysis.
    
    Attributes:
        isolate_id: Pathogen name (e.g., "Escherichia coli", "Staphylococcus aureus")
        patient_profile: Patient epidemiological risk factors
    """
    isolate_id: str = Field(min_length=1, max_length=100, description="Pathogen identifier")
    patient_profile: PatientProfile = Field(description="Patient demographics")


class AnalyzeResponse(BaseModel):
    """Response model containing full orchestration results."""
    patient_profile: dict
    isolate_id: str
    ml_prediction: dict
    kg_verification: dict
    strategy: str
    trace: list[str]
    timestamp: str


# ============================================================================
# LANGGRAPH STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """
    LangGraph state container for epidemiological resistance analysis pipeline.
    
    Fields flow through: Predictor → Verifier → Strategist → Response
    Each node reads and updates specific fields while preserving others.
    """
    patient_profile: dict
    isolate_id: str
    ml_prediction: dict
    kg_verification: dict
    strategy: str
    trace: list[str]


# ============================================================================
# NEO4J CONNECTION MANAGEMENT
# ============================================================================

class Neo4jConnection:
    """Context manager for Neo4j database connections."""
    
    def __init__(self):
        """Initialize Neo4j credentials from environment variables."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
    
    def __enter__(self):
        """Establish connection on context entry."""
        try:
            # For neo4j+s (AuraDB), don't pass encrypted parameter
            # For bolt://, encryption can be controlled
            if self.uri.startswith("neo4j+s://") or self.uri.startswith("bolt+s://"):
                self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            else:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    encrypted=False
                )
            self.driver.verify_connectivity()
            logger.info(f"Neo4j connected: {self.uri}")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Neo4j connection failed: {e}")
            self.driver = None
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection on context exit."""
        if self.driver:
            self.driver.close()
    
    def query(self, cypher: str, parameters: dict = None) -> list[dict]:
        """Execute Cypher query and return results."""
        if not self.driver:
            logger.warning("Neo4j driver unavailable; returning empty results")
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Cypher query failed: {e}")
            return []


# ============================================================================
# NODE 1: ML PREDICTOR AGENT
# ============================================================================

def predictor_node(state: AgentState) -> AgentState:
    """
    Node 1: ML Predictor Agent
    
    Calls PyTorch MLP inference with patient epidemiological profile.
    Business Logic:
    - If Resistant AND 0.77 <= confidence <= 0.85: Log moderate confidence warning
    - Maps driving_factors to ml_prediction['risk_factors'] for UI visualization
    
    Args:
        state: Current AgentState from LangGraph
    
    Returns:
        Updated AgentState with ml_prediction populated and trace appended
    """
    try:
        patient_profile = state["patient_profile"]
        isolate_id = state["isolate_id"]
        
        # Extract patient features for inference
        age = patient_profile.get("Age", 50)
        gender = patient_profile.get("Gender", "Other")
        diabetes = patient_profile.get("Diabetes", False)
        hospital_before = patient_profile.get("Hospital_before", False)
        hypertension = patient_profile.get("Hypertension", False)
        infection_freq = patient_profile.get("Infection_Freq", 0)
        
        # Call PyTorch MLP inference
        logger.info(f"Invoking MLP inference for {isolate_id}")
        prediction, confidence, driving_factors = inference(
            age=age,
            gender=gender,
            diabetes=diabetes,
            hospital_before=hospital_before,
            hypertension=hypertension,
            infection_freq=infection_freq
        )
        
        # Populate ML prediction results
        state["ml_prediction"] = {
            "is_resistant": prediction == "Resistant",
            "prediction": prediction,
            "confidence": float(confidence),
            "risk_factors": driving_factors if isinstance(driving_factors, list) else []
        }
        
        # Business Logic: Moderate confidence warning
        if prediction == "Resistant" and 0.77 <= confidence <= 0.85:
            warning_msg = (
                f"Model detected resistance patterns with moderate confidence "
                f"({confidence:.2f}); clinical correlation advised."
            )
            state["trace"].append(warning_msg)
            logger.warning(warning_msg)
        
        # Standard trace log
        state["trace"].append(
            f"✓ ML Predictor: {prediction} (confidence: {confidence:.2%}) | "
            f"Driving factors: {', '.join(driving_factors) if driving_factors else 'None'}"
        )
        
        return state
    
    except Exception as e:
        error_msg = f"Predictor Node Error: {str(e)}"
        logger.error(error_msg)
        state["trace"].append(f"✗ {error_msg}")
        state["ml_prediction"] = {
            "is_resistant": False,
            "prediction": "Error",
            "confidence": 0.0,
            "risk_factors": []
        }
        return state


# ============================================================================
# NODE 2: VERIFIER AGENT (NEO4J / CARD DATABASE)
# ============================================================================

def verifier_node(state: AgentState) -> AgentState:
    """
    Node 2: Verifier Agent
    
    Validates ML predictions against Neo4j CARD database.
    If ML predicted Resistance:
    - Query Neo4j for resistance mechanisms (genes, mechanisms)
    - Return biological mechanism validation or "novel resistance" flag
    
    Cypher Query:
    MATCH (p:Pathogen {name: $isolate_id})-[:CARRIES_GENE]->(g)
      -[:CONFERS_RESISTANCE_TO]->(d:Antibiotic {name: "CIPROFLOXACIN"})
    RETURN g.name AS Gene, g.mechanism AS Mechanism LIMIT 3
    
    Args:
        state: Current AgentState with ml_prediction populated
    
    Returns:
        Updated AgentState with kg_verification populated and trace appended
    """
    try:
        is_resistant = state["ml_prediction"].get("is_resistant", False)
        isolate_id = state["isolate_id"]
        
        if not is_resistant:
            state["kg_verification"] = {
                "validated": False,
                "reason": "ML prediction: Susceptible (no verification needed)",
                "mechanisms_found": 0,
                "genes": []
            }
            state["trace"].append(
                "⊘ Verifier: Skipped (ML predicted Susceptible)"
            )
            return state
        
        # Connect to Neo4j and query CARD database
        with Neo4jConnection() as neo4j:
            cypher_query = """
            MATCH (p:Pathogen {name: $isolate_id})-[:CARRIES_GENE]->(g)
              -[:CONFERS_RESISTANCE_TO]->(d:Antibiotic {name: "CIPROFLOXACIN"})
            RETURN g.name AS Gene, g.mechanism AS Mechanism
            LIMIT 3
            """
            
            results = neo4j.query(cypher_query, {"isolate_id": isolate_id})
        
        if results:
            # Found biological mechanisms in CARD
            genes = [r.get("Gene", "Unknown") for r in results]
            mechanisms = [r.get("Mechanism", "Unknown") for r in results]
            
            state["kg_verification"] = {
                "validated": True,
                "reason": "Resistance mechanisms found in CARD database",
                "mechanisms_found": len(results),
                "genes": genes,
                "mechanisms": mechanisms,
                "antibiotic": "CIPROFLOXACIN"
            }
            
            mechanism_str = "; ".join(mechanisms)
            gene_str = ", ".join(genes)
            state["trace"].append(
                f"✓ Verifier: Biological validation complete | "
                f"Mechanisms: {mechanism_str} | Genes: {gene_str}"
            )
        else:
            # No mechanisms found - possible novel resistance
            state["kg_verification"] = {
                "validated": False,
                "reason": "No known CARD mechanisms found for this isolate-drug combination",
                "mechanisms_found": 0,
                "genes": [],
                "note": "Possible novel resistance pattern"
            }
            
            state["trace"].append(
                f"⚠ Verifier: No known CARD mechanisms found for {isolate_id}. "
                f"Possible novel resistance."
            )
        
        return state
    
    except Exception as e:
        error_msg = f"Verifier Node Error: {str(e)}"
        logger.error(error_msg)
        state["trace"].append(f"✗ {error_msg}")
        state["kg_verification"] = {
            "validated": False,
            "reason": f"Database error: {str(e)}",
            "mechanisms_found": 0,
            "genes": []
        }
        return state


# ============================================================================
# NODE 3: STRATEGIST AGENT (PANDAS / LOCAL DATASET)
# ============================================================================

def strategist_node(state: AgentState) -> AgentState:
    """
    Node 3: Strategist Agent
    
    Recommends alternative antibiotics based on local epidemiological data.
    Strategy:
    - Load local CSV: 'data/location_stats.csv'
    - If ML predicted Resistant to CIP:
      * Find antibiotic with lowest mean resistance across dataset
      * Recommend as safer alternative
    
    CSV Expected Format:
    Location, IMIPENEM, CEFTAZIDIME, GENTAMICIN, AUGMENTIN, CIPROFLOXACIN
    
    Args:
        state: Current AgentState with ml_prediction and kg_verification
    
    Returns:
        Updated AgentState with strategy populated and trace appended
    """
    try:
        prediction = state["ml_prediction"].get("prediction", "Unknown")
        
        # If not resistant, provide conservative recommendation
        if prediction != "Resistant":
            state["strategy"] = (
                "Clinical Recommendation: Continue with current antibiotic regimen. "
                "Organism appears susceptible based on epidemiological modeling."
            )
            state["trace"].append(
                "✓ Strategist: Conservative recommendation (non-resistant prediction)"
            )
            return state
        
        # Load local dataset
        csv_path = "data/location_stats.csv"
        
        # Try both relative paths (from backend dir or from project root)
        if not os.path.exists(csv_path):
            csv_path = "backend/data/location_stats.csv"
        
        if not os.path.exists(csv_path):
            logger.warning(f"CSV not found at {csv_path}")
            state["strategy"] = (
                "Clinical Recommendation: Refer to institutional antibiograms. "
                "Local dataset unavailable."
            )
            state["trace"].append(
                f"⚠ Strategist: Local dataset not found at {csv_path}"
            )
            return state
        
        # Load and analyze resistance data
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded dataset with {len(df)} records from {csv_path}")
        
        # Define antibiotic columns (exclude Location and CIPROFLOXACIN)
        drug_columns = [
            col for col in df.columns
            if col not in ["Location", "CIPROFLOXACIN"]
        ]
        
        if not drug_columns:
            state["strategy"] = (
                "Clinical Recommendation: Unable to parse antibiotic dataset. "
                "Refer to CARD database and clinical guidelines."
            )
            state["trace"].append("⚠ Strategist: No drug columns found in dataset")
            return state
        
        # Calculate mean resistance for each drug (lower is better)
        drug_resistance_means = {}
        for drug in drug_columns:
            try:
                mean_resistance_raw = pd.to_numeric(df[drug], errors="coerce").mean()
                
                # Check if values are decimals (0-1) or already percentages (1-100)
                # Decimals need multiplication by 100; percentages don't
                if mean_resistance_raw < 1.0:
                    # Values are decimals (e.g., 0.22) - multiply by 100
                    mean_resistance_pct = mean_resistance_raw * 100
                else:
                    # Values are already percentages (e.g., 22.0) - use as is
                    mean_resistance_pct = mean_resistance_raw
                
                # Cap at 100.0 and format
                mean_resistance_pct = min(100.0, mean_resistance_pct)
                drug_resistance_means[drug] = mean_resistance_pct
            except Exception as e:
                logger.warning(f"Error processing {drug}: {e}")
                continue
        
        # Find safest alternative (lowest resistance)
        if drug_resistance_means:
            safest_drug = min(
                drug_resistance_means.items(),
                key=lambda x: x[1]
            )
            drug_name, resistance_pct = safest_drug
            
            # Format percentage to 1 decimal place (e.g., "22.6%")
            resistance_str = f"{resistance_pct:.1f}%"
            
            state["strategy"] = (
                f"Clinical Recommendation: CIPROFLOXACIN resistance detected. "
                f"Switch to {drug_name} (local resistance rate: {resistance_str}). "
                f"Verify susceptibility via AST before administration."
            )
            
            state["trace"].append(
                f"✓ Strategist: Recommended alternative: {drug_name} "
                f"(local resistance: {resistance_str})"
            )
        else:
            state["strategy"] = (
                "Clinical Recommendation: Resistance detected. "
                "Refer to institutional antibiogram and/or infectious disease specialist."
            )
            state["trace"].append("⚠ Strategist: Unable to calculate drug resistance means")
        
        return state
    
    except Exception as e:
        error_msg = f"Strategist Node Error: {str(e)}"
        logger.error(error_msg)
        state["trace"].append(f"✗ {error_msg}")
        state["strategy"] = (
            f"Clinical Recommendation: Processing error ({str(e)}). "
            f"Refer to institutional guidelines and specialist consultation."
        )
        return state


# ============================================================================
# LANGGRAPH COMPILATION
# ============================================================================

def build_sentinel_graph():
    """
    Compile Sentinel-GNN LangGraph orchestration pipeline.
    
    Pipeline Flow:
    Predictor (ML Inference)
        ↓
    Verifier (CARD Database)
        ↓
    Strategist (Local Dataset)
        ↓
    END
    
    Returns:
        Compiled graph executable
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("predictor", predictor_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("strategist", strategist_node)
    
    # Define flow
    graph.set_entry_point("predictor")
    graph.add_edge("predictor", "verifier")
    graph.add_edge("verifier", "strategist")
    graph.add_edge("strategist", END)
    
    # Compile
    return graph.compile()


# Instantiate compiled graph
sentinel_graph = build_sentinel_graph()


# ============================================================================
# FASTAPI ROUTE
# ============================================================================

router = APIRouter()


@router.post("/", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> dict:
    """
    Analyze bacterial isolate with epidemiological context.
    
    Orchestrates 3-node LangGraph pipeline:
    1. ML Predictor: PyTorch MLP inference on patient profile
    2. Verifier: Neo4j CARD database validation
    3. Strategist: Local dataset analysis for drug recommendations
    
    Request:
        POST /api/analyze
        {
            "isolate_id": "Escherichia coli",
            "patient_profile": {
                "Age": 65,
                "Gender": "Male",
                "Diabetes": true,
                "Hospital_before": true,
                "Hypertension": true,
                "Infection_Freq": 3
            }
        }
    
    Response:
        {
            "isolate_id": "Escherichia coli",
            "patient_profile": {...},
            "ml_prediction": {
                "is_resistant": true,
                "prediction": "Resistant",
                "confidence": 0.82,
                "risk_factors": ["Hospital_before", "Diabetes", "Hypertension"]
            },
            "kg_verification": {
                "validated": true,
                "mechanisms_found": 2,
                "genes": ["blaCTX-M-15", "acrAB"],
                ...
            },
            "strategy": "Clinical Recommendation: Switch to IMIPENEM...",
            "trace": [
                "✓ ML Predictor: Resistant (confidence: 82%) ...",
                "✓ Verifier: Biological validation complete ...",
                "✓ Strategist: Recommended alternative: IMIPENEM ..."
            ],
            "timestamp": "2026-03-30T14:23:45Z"
        }
    
    Args:
        request: AnalyzeRequest with isolate_id and patient_profile
    
    Returns:
        AnalyzeResponse with full orchestration results
    
    Raises:
        HTTPException: 400 if validation fails, 500 if execution fails
    """
    try:
        # Initialize LangGraph state
        initial_state: AgentState = {
            "patient_profile": request.patient_profile.dict(),
            "isolate_id": request.isolate_id,
            "ml_prediction": {},
            "kg_verification": {},
            "strategy": "",
            "trace": [f"Starting analysis for {request.isolate_id}..."]
        }
        
        logger.info(f"Analyzing isolate: {request.isolate_id}")
        
        # Invoke compiled LangGraph
        final_state = sentinel_graph.invoke(initial_state)
        
        # Construct response
        response = AnalyzeResponse(
            patient_profile=final_state["patient_profile"],
            isolate_id=final_state["isolate_id"],
            ml_prediction=final_state["ml_prediction"],
            kg_verification=final_state["kg_verification"],
            strategy=final_state["strategy"],
            trace=final_state["trace"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        logger.info(f"Analysis complete for {request.isolate_id}")
        return response.dict()
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

