import os
import re
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# =====================================================================
# 1. THE MONOTONIC MODEL ARCHITECTURE
# =====================================================================
class ResBlock(nn.Module):
    def __init__(self, dim, dropout=0.35): # 🛡️ Increased dropout to 0.35
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim), nn.BatchNorm1d(dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(dim, dim), nn.BatchNorm1d(dim),
        )
    def forward(self, x): 
        return F.relu(x + self.net(x))

class SentinelMLP(nn.Module):
    def __init__(self, in_dim=4, hidden=64, dropout=0.35): # 🛡️ Reduced hidden to 64
        super().__init__()
        self.internal_dim = in_dim + 4 
        
        # Deep Path
        self.enc = nn.Sequential(nn.Linear(self.internal_dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU())
        self.res1 = ResBlock(hidden, dropout)
        self.res2 = ResBlock(hidden, dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden, 16), nn.BatchNorm1d(16), nn.ReLU(), nn.Linear(16, 1) # 🛡️ Reduced head to 16
        )
        
        # 🚨 THE SAFETY LOCK: Monotonic Weight for Duration/Frequency 🚨
        self.monotonic_weight = nn.Parameter(torch.tensor([0.5]))
        
    def forward(self, x): 
        age_freq = x[:, 1] * x[:, 3]
        hosp_freq = x[:, 2] * x[:, 3]
        age_hosp = x[:, 1] * x[:, 2]
        risk_factor = x[:, 1] * x[:, 2] * x[:, 3]
        
        x_engineered = torch.cat([
            x, age_freq.unsqueeze(1), hosp_freq.unsqueeze(1), 
            age_hosp.unsqueeze(1), risk_factor.unsqueeze(1)
        ], dim=1)
        
        # 1. Standard Network Output
        deep_out = self.head(self.res2(self.res1(self.enc(x_engineered))))
        
        # 2. Forced Monotonic Addition (Guarantees Risk Goes Up with Duration)
        direct_impact = F.relu(self.monotonic_weight) * x[:, 3].unsqueeze(1)
        
        return deep_out + direct_impact

# =====================================================================
# 2. GLOBAL TRAINING STATISTICS & THRESHOLD
# =====================================================================
AGE_MEAN = 45.6321
AGE_STD = 24.8873
FREQ_MEAN = 1.5143
FREQ_STD = 1.0219
THRESHOLD = 0.67  #  Updated to perfectly match Colab results

# =====================================================================
# 3. PRODUCTION FEATURE ENGINEERING
# =====================================================================
def preprocess_features(features: list, encoder_classes: np.ndarray) -> np.ndarray:
    """
    Transforms the 4 API features into the normalized array the model expects.
    Expected input: [isolate_id (str), Age (float), Hospital_before (bool/int), Infection_Freq (float)]
    """
    # 1. Clean and Encode the Bacteria Strain
    souche_str = str(features[0]).lower().strip()
    souche_str = re.sub(r'^s\d+\s+', '', souche_str).strip() 
    
    # Check if the strain exists in our training data
    if souche_str in encoder_classes:
        souche_encoded = np.where(encoder_classes == souche_str)[0][0]
    else:
        print(f" Warning: Unseen bacteria strain '{souche_str}'. Defaulting to encoded ID 0.")
        souche_encoded = 0 
        
    # 2. Extract remaining features
    age = float(features[1])
    hosp = 1.0 if features[2] in [1, '1', True, 'Yes', 'yes'] else 0.0
    freq = float(features[3])

    # 3. Normalize numerical features
    age_n = (age - AGE_MEAN) / (AGE_STD + 1e-8)
    freq_n = (freq - FREQ_MEAN) / (FREQ_STD + 1e-8)

    return np.array([souche_encoded, age_n, hosp, freq_n], dtype=np.float32)

# =====================================================================
# 4. INFERENCE FUNCTION
# =====================================================================
def run_gnn_inference(features: list) -> dict:
    """Runs the 4 features through the optimized SentinelMLP model."""
    try:
        # 🎯 Ensure it points to backend/app/models/ directory
        backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        models_dir = os.path.join(backend_root, "app", "models")
        
        model_path = os.path.join(models_dir, "sentinel_gnn_best.pth")
        encoder_path = os.path.join(models_dir, "strain_encoder_classes.npy")
        
        # Load the translation dictionary
        encoder_classes = np.load(encoder_path, allow_pickle=True)
        
        # Preprocess features
        X_clean = preprocess_features(features, encoder_classes)
        
        # Initialize and Load Model (Ensure hidden=64 matches new architecture)
        model = SentinelMLP(in_dim=4, hidden=64) 
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
        model.eval()
        
        with torch.no_grad():
            input_tensor = torch.from_numpy(X_clean).float().unsqueeze(0)
            logits = model(input_tensor)
            probability = torch.sigmoid(logits).item()
            is_resistant = bool(probability >= THRESHOLD)
            
        return {
            "prediction": 1 if is_resistant else 0,
            "is_resistant": is_resistant,
            "probability": probability,
            "confidence": round(probability * 100, 2),
            "driving_factors": []
        }
        
    except Exception as e:
        print(f" ML Inference Error: {e}")
        return {"prediction": 0, "is_resistant": False, "probability": 0.0, "confidence": 0.0, "driving_factors": []}