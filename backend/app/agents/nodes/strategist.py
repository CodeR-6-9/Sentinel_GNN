"""
Strategist Agent Node

Recommends alternative antibiotics based on local epidemiological data.
"""

import os
import logging
import pandas as pd
from app.schemas.analysis_types import AgentState

logger = logging.getLogger(__name__)

# Resolve the absolute path to the backend root directory (3 levels up from this file in nodes/)
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


# ============================================================================
# NODE 3: STRATEGIST AGENT (PANDAS / LOCAL DATASET)
# ============================================================================

def strategist_node(state: AgentState) -> AgentState:
    """
    Node 3: Strategist Agent
    
    Recommends alternative antibiotics based on local epidemiological data.
    Strategy:
    - Load local CSV: 'data/location_stats.csv'
    - If ML predicted Resistant to CIP:
      * Find antibiotic with lowest mean resistance across dataset
      * Recommend as safer alternative
    
    CSV Expected Format:
    Location, IMIPENEM, CEFTAZIDIME, GENTAMICIN, AUGMENTIN, CIPROFLOXACIN
    
    Args:
        state: Current AgentState with ml_prediction and kg_verification
    
    Returns:
        Updated AgentState with strategy populated and trace appended
    """
    try:
        print("\n💊 [DEBUG] Strategist Node: Analyzing local epidemiological data...")
        prediction = state["ml_prediction"].get("prediction", "Unknown")
        print(f"  ML Prediction: {prediction}")
        
        # If not resistant, provide conservative recommendation
        if prediction != "Resistant":
            state["strategy"] = (
                "Clinical Recommendation: Continue with current antibiotic regimen. "
                "Organism appears susceptible based on epidemiological modeling."
            )
            state["trace"].append(
                "✓ Strategist: Conservative recommendation (non-resistant prediction)"
            )
            return state
        
        # Load local dataset using absolute backend_root path
        csv_path = os.path.join(backend_root, "data", "location_stats.csv")
        print(f"  CSV Path: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.warning(f"CSV not found at {csv_path}")
            print(f"  ❌ CSV file not found")
            state["strategy"] = (
                "Clinical Recommendation: Refer to institutional antibiograms. "
                "Local dataset unavailable."
            )
            state["trace"].append(
                f"⚠ Strategist: Local dataset not found at {csv_path}"
            )
            return state
        
        print(f"  ✅ CSV file loaded successfully")
        
        # Load and analyze resistance data
        print(f"  → Reading CSV file...")
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded dataset with {len(df)} records from {csv_path}")
        print(f"  ✅ Dataset loaded: {len(df)} location records")
        
        # Define antibiotic columns (exclude Location and CIPROFLOXACIN)
        drug_columns = [
            col for col in df.columns
            if col not in ["Location", "CIPROFLOXACIN"]
        ]
        print(f"  Available alternatives: {drug_columns}")
        
        if not drug_columns:
            state["strategy"] = (
                "Clinical Recommendation: Unable to parse antibiotic dataset. "
                "Refer to CARD database and clinical guidelines."
            )
            state["trace"].append("⚠ Strategist: No drug columns found in dataset")
            return state
        
        # Calculate mean resistance for each drug (lower is better)
        drug_resistance_means = {}
        for drug in drug_columns:
            try:
                mean_resistance_raw = pd.to_numeric(df[drug], errors="coerce").mean()
                
                # Check if values are decimals (0-1) or already percentages (1-100)
                # Decimals need multiplication by 100; percentages don't
                if mean_resistance_raw < 1.0:
                    # Values are decimals (e.g., 0.22) - multiply by 100
                    mean_resistance_pct = mean_resistance_raw * 100
                else:
                    # Values are already percentages (e.g., 22.0) - use as is
                    mean_resistance_pct = mean_resistance_raw
                
                # Cap at 100.0 and format
                mean_resistance_pct = min(100.0, mean_resistance_pct)
                drug_resistance_means[drug] = mean_resistance_pct
            except Exception as e:
                logger.warning(f"Error processing {drug}: {e}")
                continue
        
        # Find safest alternative (lowest resistance)
        if drug_resistance_means:
            print(f"  → Analyzing resistance rates across {len(drug_resistance_means)} alternatives:")
            for drug, rate in sorted(drug_resistance_means.items(), key=lambda x: x[1]):
                print(f"     • {drug}: {rate:.1f}%")
            
            safest_drug = min(
                drug_resistance_means.items(),
                key=lambda x: x[1]
            )
            drug_name, resistance_pct = safest_drug
            
            # Format percentage to 1 decimal place (e.g., "22.6%")
            resistance_str = f"{resistance_pct:.1f}%"
            
            print(f"  ✅ Recommendation: {drug_name} ({resistance_str} local resistance)")
            
            state["strategy"] = (
                f"Clinical Recommendation: CIPROFLOXACIN resistance detected. "
                f"Switch to {drug_name} (local resistance rate: {resistance_str}). "
                f"Verify susceptibility via AST before administration."
            )
            
            state["trace"].append(
                f"✓ Strategist: Recommended alternative: {drug_name} "
                f"(local resistance: {resistance_str})"
            )
            print(f"  ✅ Recommended: {drug_name} ({resistance_str})")
        else:
            state["strategy"] = (
                "Clinical Recommendation: Resistance detected. "
                "Refer to institutional antibiogram and/or infectious disease specialist."
            )
            state["trace"].append("⚠ Strategist: Unable to calculate drug resistance means")
            print(f"  ⚠️ Unable to calculate resistance means")
        
        print(f"✅ [DEBUG] Strategist Node: Complete")
        return state
    
    except Exception as e:
        error_msg = f"Strategist Node Error: {str(e)}"
        logger.error(error_msg)
        state["trace"].append(f"✗ {error_msg}")
        state["strategy"] = (
            f"Clinical Recommendation: Processing error ({str(e)}). "
            f"Refer to institutional guidelines and specialist consultation."
        )
        return state
