"""
Sentinel-GNN Analysis Orchestration API Route

FastAPI endpoint that orchestrates the 3-node LangGraph pipeline.

Imports:
- AnalyzeRequest, AnalyzeResponse, AgentState from app.schemas
- sentinel_graph (pre-compiled) from app.agents.workflow
"""

import logging
from datetime import datetime
from fastapi import APIRouter

from app.schemas.analysis_types import AnalyzeRequest, AnalyzeResponse, AgentState
from app.agents.workflow import sentinel_graph

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ============================================================================
# FASTAPI ROUTE
# ============================================================================

router = APIRouter()


@router.post("", response_model=AnalyzeResponse)
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
        print("\n🚀 [DEBUG] Request received at analyze route")
        print(f"  isolate_id: {request.isolate_id}")
        print(f"  patient_profile: {request.patient_profile.dict()}")
        
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
        print("\n⏳ [DEBUG] Invoking sentinel_graph...")
        
        # Invoke compiled LangGraph
        final_state = sentinel_graph.invoke(initial_state)
        print("\n✅ [DEBUG] sentinel_graph.invoke() completed successfully")
        
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
        
        logger.info(f"Analysis complete: {final_state['ml_prediction'].get('prediction', 'Unknown')}")
        return response.dict()
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

