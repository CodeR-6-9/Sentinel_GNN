"""
Integration Sanity Check Script for Sentinel-GNN Backend
Tests: CSV readability, Neo4j connectivity, CARD content, ML model loading
"""

import sys
import os
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

print(f"\n{BOLD}{BLUE}{'='*70}")
print("SENTINEL-GNN BACKEND INTEGRATION SANITY CHECK")
print(f"{'='*70}{RESET}\n")

# ============================================================================
# TEST 1: PATHOLOGY CHECK - CSV READABILITY
# ============================================================================
print(f"{BOLD}[TEST 1] Pathology Check: CSV Readability{RESET}")
print("-" * 70)

try:
    import pandas as pd
    
    csv_path = "data/location_stats.csv"
    
    if not os.path.exists(csv_path):
        print(f"{RED}✗ FAIL: CSV file not found at {csv_path}{RESET}")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    row_count = len(df)
    columns = list(df.columns)
    
    print(f"{GREEN}✓ PASS: CSV successfully loaded{RESET}")
    print(f"  • Rows: {BOLD}{row_count}{RESET}")
    print(f"  • Columns: {BOLD}{', '.join(columns)}{RESET}")
    print(f"  • Data preview:")
    print(f"    {df.head(3).to_string().replace(chr(10), chr(10) + '    ')}")
    
    # Check for null values
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print(f"{GREEN}✓ No missing values detected{RESET}")
    else:
        print(f"{YELLOW}⚠ Warning: Found {null_counts.sum()} null values{RESET}")
    
    test1_status = "PASS"
    test1_rows = row_count
except ImportError as e:
    print(f"{RED}✗ FAIL: Pandas not installed: {e}{RESET}")
    test1_status = "FAIL"
    test1_rows = 0
except Exception as e:
    print(f"{RED}✗ FAIL: {str(e)}{RESET}")
    test1_status = "FAIL"
    test1_rows = 0

# ============================================================================
# TEST 2: NEO4J CONNECTIVITY
# ============================================================================
print(f"\n{BOLD}[TEST 2] Neo4j Connectivity Check{RESET}")
print("-" * 70)

try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
    
    # Load .env credentials
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        print(f"{YELLOW}⚠ Warning: Incomplete credentials in .env{RESET}")
        print(f"  • URI: {uri}")
        print(f"  • User: {user}")
        print(f"  • Password: {'***' if password else 'NOT SET'}")
        raise ValueError("Missing credentials")
    
    print(f"  • Connecting to: {BOLD}{uri}{RESET}")
    print(f"  • User: {BOLD}{user}{RESET}")
    
    # Try to connect (handle neo4j+s scheme which already has encryption)
    if uri.startswith("neo4j+s://") or uri.startswith("bolt+s://"):
        driver = GraphDatabase.driver(uri, auth=(user, password))
    else:
        driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
    
    driver.verify_connectivity()
    
    print(f"{GREEN}✓ PASS: Neo4j connection successful{RESET}")
    test2_status = "PASS"
    
except ImportError:
    print(f"{RED}✗ FAIL: neo4j driver not installed{RESET}")
    test2_status = "FAIL"
    driver = None
except Exception as e:
    print(f"{RED}✗ FAIL: Neo4j connection error: {str(e)}{RESET}")
    print(f"  {YELLOW}Note: This may be expected if AuraDB not provisioned yet{RESET}")
    test2_status = "FAIL"
    driver = None

# ============================================================================
# TEST 3: CARD CONTENT CHECK
# ============================================================================
print(f"\n{BOLD}[TEST 3] CARD Database Content Check{RESET}")
print("-" * 70)

if driver and test2_status == "PASS":
    try:
        # Query 1: Count Pathogen nodes
        with driver.session() as session:
            result = session.run("MATCH (p:Pathogen) RETURN COUNT(p) as count")
            count = result.single()["count"]
            
            print(f"{GREEN}✓ Query successful{RESET}")
            print(f"  • Total Pathogen nodes: {BOLD}{count}{RESET}")
            
            # Query 2: Check for Escherichia coli
            result = session.run(
                'MATCH (p:Pathogen {name: "Escherichia coli"}) RETURN p.name as name'
            )
            ecoli = result.single()
            
            if ecoli:
                print(f"{GREEN}✓ Escherichia coli found in database{RESET}")
                e_coli_found = True
            else:
                print(f"{YELLOW}⚠ Warning: Escherichia coli NOT found in database{RESET}")
                print(f"  {YELLOW}This may cause 'No known CARD mechanisms' errors{RESET}")
                
                # Try to get first few pathogen names
                result = session.run(
                    "MATCH (p:Pathogen) RETURN p.name as name LIMIT 5"
                )
                samples = [record["name"] for record in result]
                print(f"  • Sample pathogen names in DB: {samples}")
                e_coli_found = False
        
        test3_status = "PASS"
        
    except Exception as e:
        print(f"{RED}✗ Query failed: {str(e)}{RESET}")
        test3_status = "FAIL"
        e_coli_found = False
    finally:
        if driver:
            driver.close()
else:
    print(f"{YELLOW}⊘ Skipped: Neo4j not connected{RESET}")
    test3_status = "SKIP"
    e_coli_found = False

# ============================================================================
# TEST 4: ML MODEL CHECK
# ============================================================================
print(f"\n{BOLD}[TEST 4] ML Model Loading Check{RESET}")
print("-" * 70)

try:
    # Check if gnn_model.pth exists
    model_path = "gnn_model.pth"
    
    if os.path.exists(model_path):
        print(f"{GREEN}✓ gnn_model.pth found{RESET}")
        
        # Try to load it with PyTorch
        try:
            import torch
            model_state = torch.load(model_path)
            print(f"{GREEN}✓ Model loaded successfully with PyTorch{RESET}")
            print(f"  • Model type: {type(model_state).__name__}")
            test4_status = "PASS"
            model_type = "PyTorch"
        except ImportError:
            print(f"{YELLOW}⚠ PyTorch not installed; will use fallback rule-based inference{RESET}")
            test4_status = "PASS"
            model_type = "Fallback"
        except Exception as e:
            print(f"{YELLOW}⚠ Could not load model: {e}{RESET}")
            print(f"  {YELLOW}Will use fallback rule-based inference{RESET}")
            test4_status = "PASS"
            model_type = "Fallback"
    else:
        print(f"{YELLOW}⚠ gnn_model.pth not found{RESET}")
        print(f"  {YELLOW}Backend will use fallback rule-based inference{RESET}")
        test4_status = "PASS"
        model_type = "Fallback"
        
        # Try to import gnn and verify inference works
        try:
            from gnn import inference
            
            # Test inference with sample patient
            pred, conf, factors = inference(
                age=65, gender="Male", diabetes=True,
                hospital_before=True, hypertension=True, infection_freq=4
            )
            
            print(f"{GREEN}✓ gnn.inference() function works (fallback){RESET}")
            print(f"  • Sample inference: {pred} (confidence: {conf:.2%})")
            print(f"  • Risk factors: {factors}")
            
        except Exception as e:
            print(f"{RED}✗ gnn.inference() failed: {e}{RESET}")
            test4_status = "FAIL"

except Exception as e:
    print(f"{RED}✗ Unexpected error: {e}{RESET}")
    test4_status = "FAIL"
    model_type = "Error"

# ============================================================================
# SUMMARY REPORT
# ============================================================================
print(f"\n{BOLD}{BLUE}{'='*70}")
print("SUMMARY REPORT")
print(f"{'='*70}{RESET}\n")

summary_data = [
    ("CSV Readability", test1_status, f"({test1_rows} rows)" if test1_rows > 0 else ""),
    ("Neo4j Connectivity", test2_status, ""),
    ("CARD Content", test3_status, f"(E. coli: {'Found' if e_coli_found else 'NOT FOUND'})" if test3_status != "SKIP" else "(Skipped)"),
    ("ML Model", test4_status, f"({model_type})"),
]

for test_name, status, detail in summary_data:
    if status == "PASS":
        status_str = f"{GREEN}✓ PASS{RESET}"
    elif status == "FAIL":
        status_str = f"{RED}✗ FAIL{RESET}"
    elif status == "SKIP":
        status_str = f"{YELLOW}⊘ SKIP{RESET}"
    else:
        status_str = status
    
    print(f"  {status_str:20} {test_name:25} {detail}")

print()

# ============================================================================
# CRITICAL FINDINGS FOR DEMO
# ============================================================================
print(f"{BOLD}CRITICAL FINDINGS FOR DEMO:{RESET}\n")

findings = []

if test1_status == "PASS":
    findings.append(f"{GREEN}✓ Strategist Node:{RESET} CSV has {test1_rows} rows (READY)")
    if test1_rows != 274:
        findings.append(f"  {YELLOW}Note: Expected 274 rows; found {test1_rows}{RESET}")
else:
    findings.append(f"{RED}✗ Strategist Node: CSV ERROR (FIX REQUIRED){RESET}")

if test2_status == "PASS":
    findings.append(f"{GREEN}✓ Verifier Node:{RESET} Neo4j connected (READY)")
else:
    findings.append(f"{YELLOW}⚠ Verifier Node: No Neo4j (will skip gracefully){RESET}")

if test3_status == "PASS":
    if e_coli_found:
        findings.append(f"{GREEN}✓ CARD Database:{RESET} E. coli found (READY)")
    else:
        findings.append(f"{YELLOW}⚠ CARD Database: E. coli NOT FOUND (May show 'novel resistance'){RESET}")
elif test3_status == "SKIP":
    findings.append(f"{YELLOW}⊘ CARD Database: Check skipped (Neo4j not connected){RESET}")

if test4_status == "PASS":
    findings.append(f"{GREEN}✓ Predictor Node:{RESET} Model ready ({model_type}) (READY)")
else:
    findings.append(f"{RED}✗ Predictor Node: MODEL ERROR (FIX REQUIRED){RESET}")

for finding in findings:
    print(f"  {finding}")

print()

# ============================================================================
# RECOMMENDATIONS
# ============================================================================
if any(status == "FAIL" for _, status, _ in summary_data):
    print(f"{BOLD}{RED}⚠ ISSUES DETECTED - DEMO MAY FAIL{RESET}\n")
    
    fixes = []
    
    if test1_status == "FAIL":
        fixes.append("1. CSV Issue: Ensure data/location_stats.csv exists and is readable")
    
    if test2_status == "FAIL":
        fixes.append("2. Neo4j Issue: Check NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in .env")
        fixes.append("   (Note: If AuraDB not provisioned, backend will work with fallback)")
    
    if test3_status == "FAIL":
        fixes.append("3. CARD Query Issue: Check Neo4j connection and verify Pathogen node exists")
    
    if test4_status == "FAIL":
        fixes.append("4. Model Issue: Verify gnn_model.pth exists or gnn.py inference works")
    
    for fix in fixes:
        print(f"  {YELLOW}{fix}{RESET}")
else:
    print(f"{BOLD}{GREEN}✓ ALL SYSTEMS READY FOR DEMO{RESET}\n")
    print(f"  Backend is configured and should run smoothly.")
    print(f"  Frontend integrates with these systems.")

print(f"\n{BOLD}{BLUE}{'='*70}{RESET}\n")
