import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd

from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import recall_score
from imblearn.over_sampling import SMOTE

# ==============================
# 🔹 MODEL (KEEP SAME AS COLAB)
# =======================do i need to download th=======

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

# ==============================
# 🔹 FEATURE ENGINEERING
# ==============================

def engineer_features(Xmat):
    age_mean, age_std = Xmat[:,0].mean(), Xmat[:,0].std() + 1e-8
    freq_mean, freq_std = Xmat[:,5].mean(), Xmat[:,5].std() + 1e-8

    age_n = (Xmat[:,0] - age_mean) / age_std
    freq_n = (Xmat[:,5] - freq_mean) / freq_std

    risk = Xmat[:,2] + Xmat[:,3] + Xmat[:,4] + (Xmat[:,5] > 1).astype(float)
    risk_n = (risk - risk.mean()) / (risk.std() + 1e-8)

    return np.stack([
        age_n, Xmat[:,1], Xmat[:,2], Xmat[:,3], Xmat[:,4], freq_n,
        risk_n, Xmat[:,2]*Xmat[:,3], age_n*risk_n, freq_n*Xmat[:,3]
    ], axis=1)

# ==============================
# 🔹 LOSS FUNCTION
# ==============================

class HybridLoss(nn.Module):
    def __init__(self, pos_weight=5.0, alpha=0.75, gamma=2.0):
        super().__init__()
        self.pw = torch.tensor([pos_weight])
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits, targets):
        pw = self.pw.to(logits.device)
        wbce = F.binary_cross_entropy_with_logits(
            logits, targets, pos_weight=pw, reduction='none'
        )

        prob = torch.sigmoid(logits)
        p_t = prob * targets + (1 - prob) * (1 - targets)
        a_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)

        focal = (a_t * (1 - p_t) ** self.gamma * wbce).mean()
        return 0.7 * focal + 0.3 * wbce.mean()

# ==============================
# 🔹 TRAIN FUNCTION
# ==============================

def train_model(csv_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("📊 Loading dataset...")
    df = pd.read_csv(csv_path)

    # BASIC CLEANING (simplified version)
    df = df.dropna()

    # Example features (adjust if needed)
    feature_cols = ['Age', 'Gender', 'Diabetes', 'Hospital_before', 'Hypertension', 'Infection_Freq']
    X = df[feature_cols].values
    Y = df['CIP'].values

    # Feature engineering
    X_eng = engineer_features(X)

    # SMOTE
    smote = SMOTE(random_state=42, sampling_strategy=0.8)
    X_res, Y_res = smote.fit_resample(X_eng, Y)

    x_train = torch.tensor(X_res, dtype=torch.float).to(device)
    y_train = torch.tensor(Y_res, dtype=torch.float).unsqueeze(1).to(device)

    x_eval = torch.tensor(X_eng, dtype=torch.float).to(device)
    y_eval = torch.tensor(Y, dtype=torch.float).unsqueeze(1).to(device)

    # Model
    model = SentinelMLP().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = HybridLoss()

    print("🚀 Training started...")

    for epoch in range(100):
        model.train()

        optimizer.zero_grad()
        loss = criterion(model(x_train), y_train)
        loss.backward()
        optimizer.step()

        if epoch % 20 == 0:
            model.eval()
            with torch.no_grad():
                preds = (torch.sigmoid(model(x_eval)) > 0.5).float()
                rec = recall_score(y_eval.cpu(), preds.cpu())
                print(f"Epoch {epoch} | Loss: {loss.item():.4f} | Recall: {rec:.3f}")

    # SAVE MODEL
    save_path = "app/models/sentinel_gnn_best.pth"
    torch.save(model.state_dict(), save_path)

    print(f"✅ Model saved at {save_path}")

    return model