import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

# =====================================================================
# 1. THE MODEL ARCHITECTURE 
# =====================================================================
class ResBlock(nn.Module):
    def __init__(self, dim, dropout=0.30):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim),
            nn.BatchNorm1d(dim),
        )
    def forward(self, x):
        return F.relu(x + self.net(x))

class SentinelMLP(nn.Module):
    def __init__(self, in_dim=10, hidden=256, dropout=0.30):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU()
        )
        self.res1 = ResBlock(hidden, dropout)
        self.res2 = ResBlock(hidden, dropout)
        self.res3 = ResBlock(hidden, dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )
    def forward(self, x):
        return self.head(self.res3(self.res2(self.res1(self.enc(x)))))


# =====================================================================
# 2. GLOBAL TRAINING STATISTICS
# =====================================================================
# These values ensure single-patient API requests are normalized 
# against the exact distribution the model learned during training.
AGE_MEAN = 45.6321
AGE_STD = 24.8886
FREQ_MEAN = 1.5143
FREQ_STD = 1.0220

RISK_MEAN = 1.2582
RISK_STD = 0.8973

# =====================================================================
# 3. PRODUCTION FEATURE ENGINEERING
# =====================================================================
def engineer_features_inference(features: list):
    """Transforms the 6 API features into the 10 features the model expects."""
    # Features = [Age, Gender, Diabetes, Hospital_before, Hypertension, Infection_Freq]
    age = features[0]
    gender = features[1]
    diabetes = features[2]
    hosp = features[3]
    hyper = features[4]
    freq = features[5]

    # Use hardcoded training statistics
    age_n = (age - AGE_MEAN) / (AGE_STD + 1e-8)
    freq_n = (freq - FREQ_MEAN) / (FREQ_STD + 1e-8)

    # Calculate Risk
    risk = diabetes + hosp + hyper + (1.0 if freq > 1 else 0.0)
    risk_n = (risk - RISK_MEAN) / (RISK_STD + 1e-8)

    # Build the 10-element array exactly as the model expects
    X_eng = np.array([
        age_n, gender, diabetes, hosp, hyper, freq_n,
        risk_n, 
        diabetes * hosp, 
        age_n * risk_n, 
        freq_n * hosp
    ], dtype=np.float32)
    
    return X_eng

# =====================================================================
# 4. INFERENCE FUNCTION
# =====================================================================
def run_gnn_inference(features: list) -> dict:
    """Runs the 10-feature array through the SentinelMLP model."""
    try:
        # Expand 6 features to 10
        engineered_features = engineer_features_inference(features)
        
        # Load Model
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "sentinel_gnn_best.pth")
        
        model = SentinelMLP(in_dim=10)
        model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
        
        # CRITICAL: Set to eval mode to freeze BatchNorm layers!
        model.eval()
        
        with torch.no_grad():
            # FIX 1: Cleanly convert numpy array to tensor without the warning
            input_tensor = torch.from_numpy(engineered_features).float().unsqueeze(0)
            
            logits = model(input_tensor)
            probability = torch.sigmoid(logits).item()
            
            # Determine if resistant (Threshold > 0.5)
            is_resistant = bool(probability > 0.5)
            
        # FIX 2: Return the exact Dictionary format the Predictor Node expects!
        return {
            "prediction": 1 if is_resistant else 0,
            "is_resistant": is_resistant,
            "confidence": round(probability * 100, 2) # Converts 0.854 to 85.40
        }
        
    except Exception as e:
        print(f"❌ ML Inference Error: {e}")
        return {"prediction": 0, "is_resistant": False, "confidence": 0.0}