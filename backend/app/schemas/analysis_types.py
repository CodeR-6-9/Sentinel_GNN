"""
Sentinel-GNN Data Models

Contains all Pydantic validation models and LangGraph state definition.
No dependencies on other internal modules.
"""

from typing import TypedDict
from pydantic import BaseModel, Field


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
