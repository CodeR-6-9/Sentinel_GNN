import pandas as pd
from neo4j import GraphDatabase

# Paste your Neo4j credentials here
URI = "neo4j+s://<YOUR_AURA_DB_URI>"
AUTH = ("neo4j", "<YOUR_PASSWORD>")

def build_knowledge_graph():
    print("Loading CARD Database TSV files...")
    # Read the aro_index.tsv which contains the relationships
    df = pd.read_csv("aro_index.tsv", sep="\t", on_bad_lines='skip')
    
    # We only need rows where we have both a Gene and a Drug Class
    df = df.dropna(subset=['ARO Name', 'Drug Class', 'Resistance Mechanism'])
    
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    # Cypher query to build the graph: (Gene) -[:CONFERS_RESISTANCE_TO]-> (Drug)
    # and (Gene) -[:USES_MECHANISM]-> (Mechanism)
    cypher_query = """
    UNWIND $data AS row
    
    // Create Gene Node
    MERGE (g:Gene {name: row.`ARO Name`})
    SET g.amr_family = row.`AMR Gene Family`
    
    // Create Mechanism Node
    MERGE (m:Mechanism {name: row.`Resistance Mechanism`})
    
    // Link Gene to Mechanism
    MERGE (g)-[:USES_MECHANISM]->(m)
    
    // Drug Classes are often separated by semicolons in the TSV
    WITH g, row, split(row.`Drug Class`, ';') AS drugs
    UNWIND drugs AS drug_name
    
    // Create Drug Node
    MERGE (d:DrugClass {name: trim(drug_name)})
    
    // Link Gene to Drug
    MERGE (g)-[:CONFERS_RESISTANCE_TO]->(d)
    """
    
    # Convert dataframe to list of dicts for Neo4j injection
    data_payload = df[['ARO Name', 'AMR Gene Family', 'Drug Class', 'Resistance Mechanism']].to_dict('records')
    
    print(f"Ingesting {len(data_payload)} resistance genes into Neo4j...")
    
    with driver.session() as session:
        session.run(cypher_query, data=data_payload)
        
    print("✅ Symbolic Engine built! Your Neo4j Knowledge Graph is ready.")
    driver.close()

if __name__ == "__main__":
    build_knowledge_graph()