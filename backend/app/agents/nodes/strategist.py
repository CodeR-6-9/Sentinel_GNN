"""
Strategist Agent Node (Dynamic Risk-Adjusted Logic)
"""
import os
import logging
import pandas as pd
from app.schemas.analysis_types import AgentState

logger = logging.getLogger(__name__)
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

def strategist_node(state: AgentState) -> AgentState:
    try:
        print("\n💊 [DEBUG] Strategist Node: Formulating Patient-Adjusted Strategy...")
        
        is_resistant = state["ml_prediction"].get("is_resistant", False)
        confidence = state["ml_prediction"].get("confidence", 0.0)
        patient_profile = state.get("patient_profile", {})
        
        csv_path = os.path.join(backend_root, "data", "location_stats.csv")
        if not os.path.exists(csv_path):
            state["strategy"] = "⚠️ ERROR: Local institutional antibiogram offline."
            return state
            
        df = pd.read_csv(csv_path)
        drug_columns = [col for col in df.columns if col.upper() not in ["LOCATION", "CIPROFLOXACIN"]]
        
        # Safety Constraints
        penicillin_allergy = str(patient_profile.get("Penicillin_Allergy", "False")).lower() == "true"
        renal_impaired = str(patient_profile.get("Renal_Impaired", "False")).lower() == "true"
        
        safe_drugs = []
        contraindicated = []
        
        for drug in drug_columns:
            drug_upper = drug.upper()
            if drug_upper == "AUGMENTIN" and penicillin_allergy:
                contraindicated.append(f"• {drug_upper} (Contraindicated: Penicillin Allergy)")
                continue
            if drug_upper == "GENTAMICIN" and renal_impaired:
                contraindicated.append(f"• {drug_upper} (Contraindicated: Nephrotoxicity Risk)")
                continue
            safe_drugs.append(drug)
            
        # DYNAMIC CLINICAL RISK ADJUSTMENT
        # Extract patient specific parameters
        infection_freq = int(patient_profile.get("Infection_Freq", 0))
        age = int(patient_profile.get("Age", 50))
        
        # Calculate Risk Multiplier (More prior infections = higher chance of multidrug resistance)
        risk_multiplier = 1.0 + (infection_freq * 0.12)  # 12% extra risk per prior infection
        if age > 65:
            risk_multiplier += 0.08  # Elderly baseline risk bump
            
        drug_stats = []
        for drug in safe_drugs:
            try:
                # 1. Get the base hospital average
                base_res = pd.to_numeric(df[drug], errors="coerce").mean()
                base_pct = base_res * 100 if base_res <= 1.0 else base_res
                
                # 2. Apply the Patient-Specific Risk Multiplier
                adjusted_pct = base_pct * risk_multiplier
                
                # Cap at 99.9% logically
                adjusted_pct = min(99.9, adjusted_pct)
                
                drug_stats.append({"name": drug.upper(), "rate": adjusted_pct})
            except:
                continue
                
        # Sort by safest (lowest adjusted resistance rate)
        drug_stats.sort(key=lambda x: x["rate"])
        
        # BUILD STRATEGY
        strategy_lines = []
        
        if not is_resistant:
            strategy_lines.append("🟢 CLINICAL STRATEGY: STANDARD THERAPY")
            strategy_lines.append("Organism likely susceptible. Continue standard CIPROFLOXACIN.")
        else:
            strategy_lines.append("🚨 CLINICAL STRATEGY: ESCALATION REQUIRED")
            strategy_lines.append(f"Ciprofloxacin resistance risk: {confidence:.1f}%.")
            
            if len(drug_stats) > 0:
                strategy_lines.append("\n✅ PRIMARY EMPIRIC THERAPY (Patient-Adjusted):")
                strategy_lines.append(f"• {drug_stats[0]['name']} ({drug_stats[0]['rate']:.1f}% adjusted risk)")
            
            if len(drug_stats) > 1:
                strategy_lines.append("\n⚠️ SECONDARY OPTION:")
                strategy_lines.append(f"• {drug_stats[1]['name']} ({drug_stats[1]['rate']:.1f}% adjusted risk)")
                
        if contraindicated:
            strategy_lines.append("\n🚫 CONTRAINDICATED (DO NOT PRESCRIBE):")
            strategy_lines.extend(contraindicated)
            
        state["strategy"] = "\n".join(strategy_lines)
        return state

    except Exception as e:
        logger.error(f"Strategist Error: {str(e)}")
        state["strategy"] = "⚠️ CLINICAL STRATEGY ERROR."
        return state