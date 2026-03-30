from neo4j import GraphDatabase

# ⚠️ PASTE YOUR NEO4J CREDENTIALS HERE
URI = "neo4j+s://ec88683c.databases.neo4j.io"
AUTH = ("neo4j", "LD9Pey_3gguoA35o8CPss_cckS6jJV1sVrBABsN-mJ8")

def verify_resistance_mechanisms(drug_class: str = "fluoroquinolone antibiotic"):
    """
    Queries the CARD database to find HOW the bacteria is resisting the drug.
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
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