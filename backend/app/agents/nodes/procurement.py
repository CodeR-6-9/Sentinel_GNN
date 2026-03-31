import os
import json
import uuid
import time
import re
from datetime import datetime
from app.schemas.analysis_types import AgentState

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
INVENTORY_PATH = os.path.join(backend_root, "data", "pharmacy_inventory.json")

# ============================================================================
#     EXTERNAL API SIMULATOR
# ============================================================================
def execute_external_order(drug_name: str, quantity: int, total_cost: float) -> dict:
    """
    Simulates sending an HTTP POST request to a B2B Pharma Supplier API.
    """
    print(f"  🌐 [NETWORK] Connecting to Supplier API (B2B Pharma Gateway)...")
    time.sleep(1.5) # Simulate network latency for the terminal output
    
    # The exact payload a real supplier API would expect
    api_payload = {
        "hospital_id": "HOSP-9942-A",
        "billing_ref": "FIN-DEPT-Q3",
        "shipping_address": "Loading Dock B, Main Hospital Campus",
        "items": [
            {
                "ndc_code": f"NDC-{uuid.uuid4().hex[:6].upper()}",
                "medication": drug_name,
                "quantity_vials": quantity,
                "authorized_price_usd": total_cost
            }
        ],
        "priority": "URGENT_MEDICAL",
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"  📤 [POST] Payload Transmitted: \n{json.dumps(api_payload, indent=2)}")
    time.sleep(1) # Simulating server processing
    
    # Mocking the 200 OK response from the supplier
    confirmation_code = f"SUPPLIER-ACK-{str(uuid.uuid4())[:8].upper()}"
    print(f"  📥 [200 OK] Order Confirmed. Ref: {confirmation_code}")
    
    return {
        "status": "success",
        "supplier_ref": confirmation_code,
        "eta": "24-48 Hours"
    }

# ============================================================================
# THE PROCUREMENT AGENT
# ============================================================================
def procurement_node(state: AgentState) -> AgentState:
    print("\n📦 [DEBUG] Procurement Node: Checking Supply Chain Logistics...")
    
    selected_drug = state.get("selected_drug", "").upper().strip()
    
    # 🛡️ BULLETPROOF FAILSAFE: Auto-extract from text if state dropped it
    if not selected_drug and state.get("strategy"):
        match = re.search(r"•\s*([A-Za-z]+)", state["strategy"])
        if match:
            selected_drug = match.group(1).upper().strip()
            print(f"  🛡️ [FAILSAFE] Procurement auto-extracted drug: {selected_drug}")
    
    if not selected_drug:
        state["procurement_order"] = {"status": "Skipped"}
        return state

    try:
        with open(INVENTORY_PATH, "r") as f:
            full_db = json.load(f)
            inventory = full_db["inventory"]
            
        drug_data = inventory.get(selected_drug)
        if not drug_data:
            return state

        stock = drug_data["stock_vials"]
        threshold = drug_data["critical_threshold"]
        
        # AUTONOMOUS DECISION LOGIC
        if stock <= threshold:
            order_qty = 50 # Standard reorder block
            po_number = f"PO-{str(uuid.uuid4())[:8].upper()}"
            total_cost = order_qty * drug_data["cost_per_vial_usd"]
            
            # 1. EXECUTE EXTERNAL API ORDER
            api_response = execute_external_order(selected_drug, order_qty, total_cost)
            
            # 2. UPDATE LOCAL ERP DATABASE (Write back to JSON)
            inventory[selected_drug]["stock_vials"] += order_qty
            with open(INVENTORY_PATH, "w") as f:
                json.dump(full_db, f, indent=4)
            print(f"  💾 [DATABASE] Internal ERP Updated. New Stock: {inventory[selected_drug]['stock_vials']}")

            # 3. UPDATE STATE FOR FRONTEND UI
            state["procurement_order"] = {
                "status": "ORDER_GENERATED",
                "po_number": po_number,
                "drug": selected_drug,
                "quantity": order_qty,
                "total_cost_usd": total_cost,
                "lead_time_days": drug_data["supplier_lead_time_days"],
                "alert": f"CRITICAL STOCK: {stock} remaining. Autonomous API order successful. Ref: {api_response['supplier_ref']}"
            }
            state["trace"].append(f"✓ Procurement: Stock critical ({stock}). Auto-ordered via API. Conf: {api_response['supplier_ref']}")
            
        else:
            state["procurement_order"] = {
                "status": "STOCK_SUFFICIENT",
                "current_stock": stock
            }
            state["trace"].append(f"✓ Procurement: Stock levels healthy ({stock} vials).")
            print(f"  ✅ Stock healthy: {stock} vials available.")
            
    except Exception as e:
        state["trace"].append(f"✗ Procurement Error: {str(e)}")
        
    print(f"✅ [DEBUG] Procurement Node: Complete")
    return state