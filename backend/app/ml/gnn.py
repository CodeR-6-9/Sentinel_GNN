import os
import re
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# =====================================================================
# 1. THE MODEL ARCHITECTURE (Must exactly match the training script)
# =====================================================================
class ResBlock(nn.Module):
    def __init__(self, dim, dropout=0.25):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim), nn.BatchNorm1d(dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(dim, dim), nn.BatchNorm1d(dim),
        )
    def forward(self, x): 
        return F.relu(x + self.net(x))

class SentinelMLP(nn.Module):
    def __init__(self, in_dim=4, hidden=128, dropout=0.25): 
        super().__init__()
        self.internal_dim = in_dim + 4 
        self.enc = nn.Sequential(nn.Linear(self.internal_dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU())
        self.res1 = ResBlock(hidden, dropout)
        self.res2 = ResBlock(hidden, dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden, 32), nn.BatchNorm1d(32), nn.ReLU(), nn.Linear(32, 1)
        )
        
    def forward(self, x): 
        # The model internally calculates the interaction features now!
        age_freq = x[:, 1] * x[:, 3]
        hosp_freq = x[:, 2] * x[:, 3]
        age_hosp = x[:, 1] * x[:, 2]
        risk_factor = x[:, 1] * x[:, 2] * x[:, 3]
        
        x_engineered = torch.cat([
            x, age_freq.unsqueeze(1), hosp_freq.unsqueeze(1), 
            age_hosp.unsqueeze(1), risk_factor.unsqueeze(1)
        ], dim=1)
        
        return self.head(self.res2(self.res1(self.enc(x_engineered))))

# =====================================================================
# 2. GLOBAL TRAINING STATISTICS & THRESHOLD
# =====================================================================
# ⚠️ IMPORTANT: Update these values to match the exact output 
# from your final terminal execution of train.py!
AGE_MEAN = 45.6321
AGE_STD = 24.8873
FREQ_MEAN = 1.5143
FREQ_STD = 1.0219

# The dynamic threshold found by the training script (e.g., 0.68)
THRESHOLD = 0.68 

# =====================================================================
# 3. PRODUCTION FEATURE ENGINEERING
# =====================================================================
def preprocess_features(features: list, encoder_classes: np.ndarray) -> np.ndarray:
    """
    Transforms the 4 API features into the normalized array the model expects.
    Expected input: [Souches (str), Age (float), Hospital_before (bool/int), Infection_Freq (float)]
    """
    # 1. Clean and Encode the Bacteria Strain (Souches)
    souche_str = str(features[0]).lower().strip()
    souche_str = re.sub(r'^s\d+\s+', '', souche_str).strip() # Remove "s123 " prefix if present
    
    if souche_str in encoder_classes:
        souche_encoded = np.where(encoder_classes == souche_str)[0][0]
    else:
        # Fallback to the most common class or 0 if it's a completely unseen bacteria
        print(f"⚠️ Warning: Unseen bacteria strain '{souche_str}'. Defaulting to encoded ID 0.")
        souche_encoded = 0 
        
    # 2. Extract remaining features
    age = float(features[1])
    hosp = 1.0 if features[2] in [1, '1', True, 'Yes', 'yes'] else 0.0
    freq = float(features[3])

    # 3. Normalize numerical features using training statistics
    age_n = (age - AGE_MEAN) / (AGE_STD + 1e-8)
    freq_n = (freq - FREQ_MEAN) / (FREQ_STD + 1e-8)

    # Return the clean 4-element array (Model handles the interaction math internally)
    return np.array([souche_encoded, age_n, hosp, freq_n], dtype=np.float32)

# =====================================================================
# 4. INFERENCE FUNCTION
# =====================================================================
def run_gnn_inference(features: list) -> dict:
    """Runs the 4 features through the optimized SentinelMLP model."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "sentinel_gnn_best.pth")
        encoder_path = os.path.join(script_dir, "strain_encoder_classes.npy")
        
        # Load the translation dictionary for bacteria names
        encoder_classes = np.load(encoder_path, allow_pickle=True)
        
        # Preprocess features
        X_clean = preprocess_features(features, encoder_classes)
        
        # Initialize and Load Model
        model = SentinelMLP(in_dim=4)
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
        
        # CRITICAL: Set to eval mode to freeze BatchNorm layers
        model.eval()
        
        with torch.no_grad():
            input_tensor = torch.from_numpy(X_clean).float().unsqueeze(0)
            
            logits = model(input_tensor)
            probability = torch.sigmoid(logits).item()
            
            # Use the optimized THRESHOLD instead of 0.5
            is_resistant = bool(probability >= THRESHOLD)
            
        return {
            "prediction": 1 if is_resistant else 0,
            "is_resistant": is_resistant,
            "confidence": round(probability * 100, 2)
        }
        
    except Exception as e:
        print(f"❌ ML Inference Error: {e}")
        return {"prediction": 0, "is_resistant": False, "confidence": 0.0}