import pandas as pd
from neo4j import GraphDatabase
import os

# Use your .env credentials or paste them here
URI = os.getenv("NEO4J_URI", "neo4j+s://your-id.aps1.cleardb.net")
AUTH = ("neo4j", "your-password")

def build_knowledge_graph():
    print(" Loading CARD Database (aro_index.tsv)...")
    
    # Read TSV and drop rows missing critical AMR info
    df = pd.read_csv("aro_index.tsv", sep="\t", on_bad_lines='skip')
    df = df.dropna(subset=['ARO Name', 'Drug Class', 'Resistance Mechanism'])
    
    data_payload = []
    for _, row in df.iterrows():
        data_payload.append({
            "gene_name": str(row['ARO Name']).strip(),
            "family": str(row['AMR Gene Family']).strip(),
            "mechanism": str(row['Resistance Mechanism']).strip(),
            "drug_classes": str(row['Drug Class']).strip()
        })

    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    # Optimized Cypher Query
    cypher_query = """
    UNWIND $data AS row
    
    // 1. Create/Update Gene Node
    MERGE (g:Gene {name: row.gene_name})
    SET g.family = row.family
    
    // 2. Create/Update Mechanism Node
    MERGE (m:Mechanism {name: row.mechanism})
    MERGE (g)-[:USES_MECHANISM]->(m)
    
    // 3. Split and Link Drug Classes
    WITH g, row, split(row.drug_classes, ';') AS drugs
    UNWIND drugs AS drug_name
    WITH g, trim(drug_name) AS clean_drug
    WHERE clean_drug <> ""
    MERGE (d:DrugClass {name: clean_drug})
    MERGE (g)-[:CONFERS_RESISTANCE_TO]->(d)
    """
    
    print(f" Ingesting {len(data_payload)} records into Neo4j...")
    
    try:
        with driver.session() as session:
            session.run(cypher_query, data=data_payload)
        print(" Success! Your AMR Knowledge Graph is live.")
    except Exception as e:
        print(f" Ingestion Failed: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    build_knowledge_graph()