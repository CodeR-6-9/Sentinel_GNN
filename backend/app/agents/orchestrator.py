from langgraph.graph import StateGraph, END
from app.agents.state import AgentState


def mock_gnn_call(isolate_id: str) -> dict:
    """
    Mock GNN prediction function.
    In production, this would call the actual PyTorch GNN model.
    
    Args:
        isolate_id: Bacterial isolate identifier.
        
    Returns:
        Dictionary with prediction results including confidence and top genes.
    """
    return {
        "is_resistant": True,
        "prediction": "Resistant",
        "confidence": 0.92,
        "top_genes": ["blaCTX-M-15", "mecA"]
    }


def predictor_node(state: AgentState) -> AgentState:
    """
    Node 1: Predictor Agent
    Runs GNN model inference and updates ml_prediction in state.
    
    Args:
        state: Current AgentState.
        
    Returns:
        Updated AgentState with ml_prediction and trace.
    """
    isolate_id = state["isolate_id"]
    
    # Call mock GNN
    ml_result = mock_gnn_call(isolate_id)
    
    # Update state
    state["ml_prediction"] = ml_result
    state["trace"].append(
        f"GNN predicted resistance with confidence {ml_result['confidence']:.2f}. "
        f"Top genes: {', '.join(ml_result['top_genes'])}"
    )
    
    return state


def verifier_node(state: AgentState) -> AgentState:
    """
    Node 2: Verifier Agent
    Queries knowledge graph (Neo4j) to verify GNN predictions against CARD database.
    
    Args:
        state: Current AgentState with ml_prediction populated.
        
    Returns:
        Updated AgentState with kg_verification and trace.
    """
    # Extract top genes from ML prediction
    top_genes = state["ml_prediction"].get("top_genes", [])
    
    # Simulate Neo4j Knowledge Graph verification
    kg_verification_result = {
        "genes_found_in_card": True,
        "genes_verified": top_genes,
        "resistance_mechanism": "Beta-lactam and Methicillin resistance",
        "literature_support": 24,
        "confidence_score": 0.88
    }
    
    # Update state
    state["kg_verification"] = kg_verification_result
    state["trace"].append(
        f"Queried CARD database. Found {kg_verification_result['literature_support']} literature sources. "
        f"Verified resistance mechanism: {kg_verification_result['resistance_mechanism']}"
    )
    
    return state


def strategist_node(state: AgentState) -> AgentState:
    """
    Node 3: Strategist Agent
    Generates clinical strategy based on ML prediction and knowledge graph verification.
    
    Args:
        state: Current AgentState with ml_prediction and kg_verification.
        
    Returns:
        Updated AgentState with strategy and trace.
    """
    prediction_confidence = state["ml_prediction"].get("confidence", 0.0)
    kg_confidence = state["kg_verification"].get("confidence_score", 0.0)
    
    # Generate clinical strategy
    combined_confidence = (prediction_confidence + kg_confidence) / 2
    
    if combined_confidence > 0.85:
        clinical_strategy = (
            "STRONG RECOMMENDATION: Switch to alternative antibiotics. "
            "Collateral Sensitivity Analysis suggests Fluoroquinolones as backup therapy. "
            "Monitor for horizontal gene transfer."
        )
    else:
        clinical_strategy = (
            "MODERATE RECOMMENDATION: Consider combination therapy. "
            "Further phenotypic testing recommended before final decision."
        )
    
    # Update state
    state["strategy"] = clinical_strategy
    state["trace"].append(
        f"Generated clinical strategy based on combined confidence ({combined_confidence:.2f}): {clinical_strategy}"
    )
    
    return state


# Build the LangGraph state machine
def build_sentinel_graph():
    """
    Constructs and compiles the Sentinel-GNN LangGraph orchestration graph.
    
    The graph follows a linear pipeline:
    predictor_node -> verifier_node -> strategist_node -> END
    
    Returns:
        Compiled graph executable.
    """
    graph = StateGraph(AgentState)
    
    # Add nodes
    graph.add_node("predictor", predictor_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("strategist", strategist_node)
    
    # Set entry point
    graph.set_entry_point("predictor")
    
    # Add edges
    graph.add_edge("predictor", "verifier")
    graph.add_edge("verifier", "strategist")
    graph.add_edge("strategist", END)
    
    # Compile
    return graph.compile()


# Compile the graph into executable form
sentinel_graph = build_sentinel_graph()
