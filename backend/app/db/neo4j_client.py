import os
from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def verify_resistance_mechanisms(drug_class: str = "fluoroquinolone antibiotic"):
    """
    Queries the CARD database to find HOW the bacteria is resisting the drug.
    """
    # Safety check: Ensure environment variables are loaded
    if not all([URI, USERNAME, PASSWORD]):
        return "Configuration error: Missing Neo4j credentials in environment variables."
        
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    query = """
    MATCH (g:Gene)-[:CONFERS_RESISTANCE_TO]->(d:DrugClass {name: $drug_class})
    MATCH (g)-[:USES_MECHANISM]->(m:Mechanism)
    RETURN m.name AS mechanism, COUNT(g) AS gene_count
    ORDER BY gene_count DESC LIMIT 3
    """
    
    try:
        with driver.session() as session:
            result = session.run(query, drug_class=drug_class)
            records = [f"{record['mechanism']} ({record['gene_count']} known genes)" for record in result]
            
        if not records:
            return "No specific mechanisms found in CARD graph."
            
        return f"CARD Database Verification: Known resistance mechanisms for this drug class include: {', '.join(records)}."
    except Exception as e:
        return f"Database error: {str(e)}"
    finally:
        driver.close()