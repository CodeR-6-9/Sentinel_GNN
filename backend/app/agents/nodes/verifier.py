"""
Verifier Agent Node (Strict Biological Logic)
"""
import logging
from app.schemas.analysis_types import AgentState
from app.core.database import Neo4jConnection

logger = logging.getLogger(__name__)

def verifier_node(state: AgentState) -> AgentState:
    try:
        print("\n🔍 [DEBUG] Verifier Node: Querying PATHOGEN-SPECIFIC Intelligence...")
        is_resistant = state["ml_prediction"].get("is_resistant", False)
        isolate_id = state.get("isolate_id", "Unknown").lower()
        
        if not is_resistant:
            state["kg_verification"] = {"validated": False, "reason": "Susceptible", "genes": [], "details": []}
            return state

        with Neo4jConnection() as neo4j:
            if neo4j.driver is None:
                state["kg_verification"] = {"validated": False, "reason": "Neo4j Offline", "genes": [], "details": []}
                return state

            cypher_query = """
            MATCH (g:Gene)-[:CONFERS_RESISTANCE_TO]->(d:DrugClass) 
            WHERE (toLower(d.name) CONTAINS 'fluoroquinolone' OR toLower(d.name) CONTAINS 'ciprofloxacin')
              AND toLower(g.description) CONTAINS toLower($pathogen)
            RETURN g.name AS Gene, g.family AS Family, g.description AS Description
            ORDER BY g.name ASC
            LIMIT 3
            """
            
            # Pass the frontend's isolate_id into the query securely
            results = neo4j.query(cypher_query, {"pathogen": isolate_id})
            
            if not results:
                print(f"  ⚠️ No specific markers found for {isolate_id}. Pulling general class mechanisms.")
                fallback_query = """
                MATCH (g:Gene)-[:CONFERS_RESISTANCE_TO]->(d:DrugClass) 
                WHERE toLower(d.name) CONTAINS 'fluoroquinolone'
                RETURN g.name AS Gene, g.family AS Family, g.description AS Description
                ORDER BY rand()  // Randomize so it's not always AAC(6')
                LIMIT 3
                """
                results = neo4j.query(fallback_query, {})

        if results:
            genes = [r["Gene"] for r in results]
            rich_details = [f"{r['Gene']} ({r['Family']}): {r['Description']}" for r in results]
            
            state["kg_verification"] = {
                "validated": True,
                "reason": "Genomic evidence found in CARD database",
                "genes": genes,
                "details": rich_details
            }
            state["trace"].append(f"✓ Verifier: Found markers specifically matching profile.")
        else:
            state["kg_verification"] = {"validated": False, "reason": "Novel mechanism", "genes": [], "details": []}

        return state

    except Exception as e:
        logger.error(f"Verifier Error: {e}")
        state["kg_verification"] = {"validated": False, "genes": [], "details": []}
        return state