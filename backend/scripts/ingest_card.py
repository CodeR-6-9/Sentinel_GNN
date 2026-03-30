import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

def build_knowledge_graph():
    if not all([URI, USERNAME, PASSWORD]):
        print("❌ Error: Missing Neo4j credentials in .env")
        return

    # Set up paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    aro_path = os.path.join(backend_root, "data", "aro.tsv")
    index_path = os.path.join(backend_root, "data", "aro_index.tsv")
    
    print(f"📂 Checking data files...")
    try:
        # Load the Encyclopedia (Descriptions)
        df_aro = pd.read_csv(aro_path, sep="\t", on_bad_lines='skip')
        desc_map = df_aro.set_index('Accession')['Description'].to_dict()

        # Load the Master Index
        df_idx = pd.read_csv(index_path, sep="\t", on_bad_lines='skip')
        df_idx = df_idx.dropna(subset=['ARO Name', 'Drug Class', 'Resistance Mechanism'])

        data_payload = []
        for _, row in df_idx.iterrows():
            aro_id = str(row['ARO Accession']).strip()
            data_payload.append({
                "gene_name": str(row['ARO Name']).strip(),
                "family": str(row['AMR Gene Family']).strip(),
                "mechanism": str(row['Resistance Mechanism']).strip(),
                "drug_classes": str(row['Drug Class']).strip(),
                "description": desc_map.get(aro_id, "Description currently unavailable."),
                "aro_id": aro_id
            })
            
    except Exception as e:
        print(f"❌ Data Loading Error: {e}")
        return

    print(f"🔌 Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    cypher_query = """
    UNWIND $data AS row
    MERGE (g:Gene {name: row.gene_name})
    SET g.family = row.family,
        g.description = row.description,
        g.aro_id = row.aro_id
    MERGE (m:Mechanism {name: row.mechanism})
    MERGE (g)-[:USES_MECHANISM]->(m)
    WITH g, row, split(row.drug_classes, ';') AS drugs
    UNWIND drugs AS drug_name
    WITH g, trim(drug_name) AS clean_drug
    WHERE clean_drug <> ""
    MERGE (d:DrugClass {name: clean_drug})
    MERGE (g)-[:CONFERS_RESISTANCE_TO]->(d)
    """
    
    print(f"🚀 Ingesting {len(data_payload)} rich nodes into Neo4j...")
    try:
        with driver.session() as session:
            session.run(cypher_query, data=data_payload)
        print("✅ Success! Your Knowledge Graph now has biological context.")
    except Exception as e:
        print(f"❌ Ingestion Failed: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    build_knowledge_graph()