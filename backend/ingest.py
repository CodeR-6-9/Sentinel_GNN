import os
import pandas as pd
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Paths
DATA_DIR = "./data"
CHROMA_PATH = "./chroma_db"

def build_vector_db():
    documents = []
    
    # ==========================================
    # 1. INGEST CLINICAL GUIDELINES (CSV)
    # ==========================================
    csv_path = os.path.join(DATA_DIR, "Guidelines_and_Protocols.csv")
    if os.path.exists(csv_path):
        print("📊 Loading Clinical Guidelines CSV...")
        df_csv = pd.read_csv(csv_path).fillna("None")
        for index, row in df_csv.iterrows():
            content = (
                f"CLINICAL GUIDELINE - Infection: {row.get('Infection_Type', 'Unknown')} | "
                f"Pathogen: {row.get('Pathogen', 'Unknown')}.\n"
                f"First Line Treatment: {row.get('First_Line_Treatment', 'None')}.\n"
                f"Second Line Treatment: {row.get('Second_Line_Treatment', 'None')}.\n"
                f"Contraindications: {row.get('Contraindications', 'None')}.\n"
                f"Dosage: {row.get('Dosage_Recommendations', 'None')}."
            )
            doc = Document(page_content=content, metadata={"source": "Clinical_Guidelines", "type": "treatment"})
            documents.append(doc)
    else:
        print("⚠️ Guidelines_and_Protocols.csv not found, skipping...")

    # ==========================================
    # 2. INGEST GENOMIC DATA (CARD ARO TSV)
    # ==========================================
    aro_path = os.path.join(DATA_DIR, "aro.tsv")
    if os.path.exists(aro_path):
        print("🧬 Loading Genomic Definitions (aro.tsv)...")
        df_aro = pd.read_csv(aro_path, sep='\t').fillna("None")
        for index, row in df_aro.iterrows():
            content = (
                f"GENOMIC KNOWLEDGE - Gene Name: {row.get('Name', 'Unknown')} (CARD Short Name: {row.get('CARD Short Name', 'Unknown')}).\n"
                f"Accession ID: {row.get('Accession', 'Unknown')}.\n"
                f"Description & Mechanism: {row.get('Description', 'None')}."
            )
            doc = Document(page_content=content, metadata={"source": "CARD_Genomic_DB", "type": "gene_definition"})
            documents.append(doc)
    else:
        print("⚠️ aro.tsv not found, skipping...")
        
    # ==========================================
    # 3. INGEST RESISTANCE MECHANISMS (ARO INDEX TSV)
    # ==========================================
    # Note: Using your exact filename!
    index_path = os.path.join(DATA_DIR, "aro_index (1).tsv")
    if os.path.exists(index_path):
        print("🦠 Loading Resistance Mappings (aro_index (1).tsv)...")
        df_index = pd.read_csv(index_path, sep='\t').fillna("None")
        for index, row in df_index.iterrows():
            content = (
                f"RESISTANCE MAPPING - Gene: {row.get('ARO Name', 'Unknown')}.\n"
                f"Gene Family: {row.get('AMR Gene Family', 'Unknown')}.\n"
                f"Drug Class Resisted: {row.get('Drug Class', 'Unknown')}.\n"
                f"Resistance Mechanism: {row.get('Resistance Mechanism', 'Unknown')}."
            )
            doc = Document(page_content=content, metadata={"source": "CARD_Index", "type": "resistance_mapping"})
            documents.append(doc)
    else:
        print("⚠️ aro_index (1).tsv not found, skipping...")

    # ==========================================
    # 4. BUILD THE DATABASE
    # ==========================================
    if len(documents) == 0:
        print("❌ No data found! Make sure your files are in the ./data/ folder.")
        return

    print(f"🧠 Creating Vector Database with {len(documents)} documents...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)
        
    Chroma.from_documents(
        documents=documents, 
        embedding=embeddings, 
        persist_directory=CHROMA_PATH
    )
    print(f"✅ Brain upgrade complete! Your AI now knows {len(documents)} clinical and genomic rules.")

if __name__ == "__main__":
    build_vector_db()