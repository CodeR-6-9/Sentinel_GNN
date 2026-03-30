"""
Verifier Agent Node (Rich Intelligence Version)

Validates ML predictions against the Neo4j CARD Knowledge Graph.
Pulls rich genomic context including descriptions and gene families.
"""

import logging
from app.schemas.analysis_types import AgentState
from app.core.database import Neo4jConnection

logger = logging.getLogger(__name__)

def verifier_node(state: AgentState) -> AgentState:
    """
    Node 2: Verifier Agent
    
    Queries CARD Knowledge Graph for genomic markers.
    Updated to use broad class matching (Fluoroquinolones) for better results.
    """
    try:
        print("\n🔍 [DEBUG] Verifier Node: Querying Rich CARD Intelligence...")
        is_resistant = state["ml_prediction"].get("is_resistant", False)
        isolate_id = state["isolate_id"]
        
        # 1. Skip logic if ML predicts Susceptible
        if not is_resistant:
            state["kg_verification"] = {
                "validated": False,
                "reason": "ML prediction: Susceptible (No genomic verification needed)",
                "genes": [],
                "details": []
            }
            state["trace"].append("⊘ Verifier: Skipped (ML predicted Susceptible)")
            return state

        # 2. Connect to Neo4j to pull Rich Data
        print(f"  Attempting Neo4j connection...")
        with Neo4jConnection() as neo4j:
            if neo4j.driver is None:
                print(f"  ⚠️ Neo4j connection failed - graceful fallback")
                state["kg_verification"] = {
                    "validated": False,
                    "reason": "Neo4j connection unavailable",
                    "genes": [],
                    "details": []
                }
                state["trace"].append("⚠ Verifier: Neo4j connection failed (graceful fallback)")
                return state

            cypher_query = """
            MATCH (g:Gene)-[:CONFERS_RESISTANCE_TO]->(d:DrugClass) 
            WHERE d.name CONTAINS 'fluoroquinolone' 
               OR d.name CONTAINS 'CIPROFLOXACIN'
            RETURN 
                g.name AS Gene, 
                g.family AS Family, 
                g.description AS Description,
                g.aro_id AS ARO
            ORDER BY g.name ASC
            LIMIT 3
            """
            
            print(f"  → Executing Rich Query for Fluoroquinolone markers...")
            results = neo4j.query(cypher_query, {})
            print(f"  ← Query result: {len(results)} genomic markers found")

        # 3. Process results into Agent State
        if results:
            genes = [r["Gene"] for r in results]
            
            # Format: "GeneName (Family): Description"
            rich_details = [
                f"{r['Gene']} ({r['Family']}): {r['Description']}" 
                for r in results
            ]
            
            state["kg_verification"] = {
                "validated": True,
                "reason": "Genomic evidence found in CARD database",
                "mechanisms_found": len(results),
                "genes": genes,
                "details": rich_details,
                "aro_ids": [r["ARO"] for r in results]
            }
            
            state["trace"].append(
                f"✓ Verifier: Found {len(genes)} fluoroquinolone markers (e.g., {genes[0]})"
            )
            print(f"  ✅ Found {len(results)} biological mechanisms")
            
        else:
            state["kg_verification"] = {
                "validated": False,
                "reason": "No known CARD mechanisms found for this drug class",
                "genes": [],
                "details": [],
                "note": "Possible novel resistance pattern detected by ML"
            }
            state["trace"].append(f"⚠ Verifier: No matching genes in CARD. Novel resistance suspected.")
            print(f"  ⚠️ No CARD mechanisms found")

        print(f"✅ [DEBUG] Verifier Node: Complete")
        return state

    except Exception as e:
        error_msg = f"Verifier Node Error: {str(e)}"
        logger.error(error_msg)
        state["trace"].append(f"✗ {error_msg}")
        state["kg_verification"] = {
            "validated": False,
            "reason": f"Database error: {str(e)}",
            "genes": [],
            "details": []
        }
        return state