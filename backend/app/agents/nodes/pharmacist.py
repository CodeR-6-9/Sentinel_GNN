import os
import json
import re
from app.schemas.analysis_types import AgentState

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
INVENTORY_PATH = os.path.join(backend_root, "data", "pharmacy_inventory.json")

def pharmacist_node(state: AgentState) -> AgentState:
    print("\n⚕️ [DEBUG] Pharmacist Node: Verifying Formulary and Interactions...")
    
    selected_drug = state.get("selected_drug", "").upper().strip()
    
    if not selected_drug and state.get("strategy"):
        match = re.search(r"•\s*([A-Za-z]+)", state["strategy"])
        if match:
            selected_drug = match.group(1).upper().strip()
            print(f"  🛡️ [FAILSAFE] Pharmacist auto-extracted drug: {selected_drug}")
    
    if not selected_drug:
        state["pharmacist_review"] = {"status": "Skipped", "reason": "No drug selected."}
        return state

    try:
        with open(INVENTORY_PATH, "r") as f:
            db = json.load(f)["inventory"]
            
        drug_data = db.get(selected_drug)
        if not drug_data:
            state["trace"].append(f"⚠ Pharmacist: '{selected_drug}' not found in inventory DB.")
            state["pharmacist_review"] = {"status": "Unknown", "formulary": "Unlisted"}
            return state

        # Check Formulary Status
        formulary = drug_data["formulary_status"]
        status_msg = "Approved" if "Approved" in formulary else "Requires ID Specialist Approval"
        
        # Simulated DDI (Drug-Drug Interaction) Check
        # In a real app, this would check the patient's active med list.
        warnings = drug_data.get("ddi_flags", [])
        
        state["pharmacist_review"] = {
            "status": status_msg,
            "formulary": formulary,
            "warnings": warnings,
            "cost_usd": drug_data["cost_per_vial_usd"]
        }
        
        state["trace"].append(f"✓ Pharmacist: Formulary checked ({status_msg}). Cost: ${drug_data['cost_per_vial_usd']}/vial.")
        print(f"  ✅ Formulary: {formulary} | Cost: ${drug_data['cost_per_vial_usd']}")
        
    except Exception as e:
        state["trace"].append(f"✗ Pharmacist Error: {str(e)}")
        print(f"  ❌ Pharmacist Error: {str(e)}")
        
    return state