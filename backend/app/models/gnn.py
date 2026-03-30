import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import os

# 1. Define the exact same Architecture used in Colab Cell 6
class ResBlock(nn.Module):
    def __init__(self, dim, dropout=0.30):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim), nn.BatchNorm1d(dim), nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(dim, dim), nn.BatchNorm1d(dim),
        )
    def forward(self, x):
        return F.relu(x + self.net(x))

class SentinelMLP(nn.Module):
    def __init__(self, in_dim=10, hidden=256, dropout=0.30):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU()
        )
        self.res1 = ResBlock(hidden, dropout)
        self.res2 = ResBlock(hidden, dropout)
        self.res3 = ResBlock(hidden, dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden, 64), nn.BatchNorm1d(64), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(64, 1)
        )
    def forward(self, x):
        return self.head(self.res3(self.res2(self.res1(self.enc(x)))))

# 2. Setup Paths and Clinical Threshold
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# IMPORTANT: Make sure you renamed your downloaded file to 'sentinel_gin_best.pth' or update this:
MODEL_PATH = os.path.join(BASE_DIR, "sentinel_gin_best.pth")
CLINICAL_THRESHOLD = 0.77  # From your Colab Cell 7 output

model = SentinelMLP()
# Load weights (using cpu for the web server)
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=True))
model.eval()

# 3. The New Inference Function
def run_gnn_inference(raw_features: list):
    """
    raw_features: [Age, Gender, Diabetes, Hospital_before, Hypertension, Infection_Freq]
    """
    # Population stats used for normalization (Matching Colab)
    # Note: These are approximates based on your dataset spread
    age_mean, age_std = 49.8, 18.2 
    freq_mean, freq_std = 2.1, 1.4
    risk_mean, risk_std = 1.8, 0.9

    age, gen, diab, hosp, hyper, freq = raw_features

    # Feature Engineering (Mapping 6 raw inputs to the 10 the model needs)
    age_n = (age - age_mean) / age_std
    freq_n = (freq - freq_mean) / freq_std
    risk = diab + hosp + hyper + (1.0 if freq > 1 else 0.0)
    risk_n = (risk - risk_mean) / risk_std

    # Prepare input tensor (10 features)
    X_eng = np.array([[
        age_n, gen, diab, hosp, hyper, freq_n,
        risk_n, (diab * hosp), (age_n * risk_n), (freq_n * hosp)
    ]], dtype=np.float32)

    x_tensor = torch.tensor(X_eng)
    x_tensor.requires_grad_(True) # Keep for Explainability (XAI)

    # Predict
    logits = model(x_tensor)
    prob = torch.sigmoid(logits).item()
    
    # XAI: Backward pass to see which of the 10 features moved the needle
    logits.backward()
    importance = x_tensor.grad.abs().squeeze().numpy()
    
    # Map the importance back to the original 6 categories for the UI
    # We take the importance of the engineered versions of the base features
    base_feature_names = ["Age", "Gender", "Diabetes", "Hospital_before", "Hypertension", "Infection_Freq"]
    # Indices 0-5 in X_eng correspond directly to the raw 6 features
    top_indices = np.argsort(importance[:6])[::-1]
    driving_factors = [base_feature_names[i] for i in top_indices[:3]]

    prediction = 1 if prob >= CLINICAL_THRESHOLD else 0

    return {
        "prediction": prediction,
        "probability": prob,
        "driving_factors": driving_factors,
        "threshold_used": CLINICAL_THRESHOLD
    }