"""
Sentinel-GNN LangGraph Orchestration Workflow Manager

Compiles and instantiates the 3-node LangGraph pipeline.
- Imports pre-built node implementations from app.agents.nodes
- Manages graph state transitions and execution flow
"""

from langgraph.graph import StateGraph, END

from app.schemas.analysis_types import AgentState
from app.agents.nodes.predictor import predictor_node
from app.agents.nodes.verifier import verifier_node
from app.agents.nodes.strategist import strategist_node


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
    
    Node Implementations:
    - predictor_node: PyTorch MLP inference (app.agents.nodes.predictor)
    - verifier_node: Neo4j CARD validation (app.agents.nodes.verifier)
    - strategist_node: CSV drug recommendations (app.agents.nodes.strategist)
    
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


# ============================================================================
# INSTANTIATE COMPILED GRAPH
# ============================================================================

# Pre-compile the graph at module load time for optimal performance
sentinel_graph = build_sentinel_graph()
