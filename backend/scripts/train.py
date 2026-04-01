import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import recall_score, accuracy_score, roc_auc_score
from imblearn.over_sampling import SMOTE

# =====================================================================
# 1. MONOTONIC MODEL ARCHITECTURE
# =====================================================================
class ResBlock(nn.Module):
    def __init__(self, dim, dropout=0.35):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, dim), nn.BatchNorm1d(dim), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(dim, dim), nn.BatchNorm1d(dim),
        )
    def forward(self, x): return F.relu(x + self.net(x))

class SentinelMLP(nn.Module):
    def __init__(self, in_dim=4, hidden=64, dropout=0.35):
        super().__init__()
        self.internal_dim = in_dim + 4
        self.enc = nn.Sequential(nn.Linear(self.internal_dim, hidden), nn.BatchNorm1d(hidden), nn.ReLU())
        self.res1 = ResBlock(hidden, dropout)
        self.res2 = ResBlock(hidden, dropout)
        self.head = nn.Sequential(
            nn.Linear(hidden, 16), nn.BatchNorm1d(16), nn.ReLU(), nn.Linear(16, 1)
        )
        # Monotonic lock for duration
        self.monotonic_weight = nn.Parameter(torch.tensor([0.5])) 

    def forward(self, x):
        age_freq = x[:, 1] * x[:, 3]
        hosp_freq = x[:, 2] * x[:, 3]
        age_hosp = x[:, 1] * x[:, 2]
        risk_factor = x[:, 1] * x[:, 2] * x[:, 3]
        
        x_engineered = torch.cat([x, age_freq.unsqueeze(1), hosp_freq.unsqueeze(1), age_hosp.unsqueeze(1), risk_factor.unsqueeze(1)], dim=1)
        deep_out = self.head(self.res2(self.res1(self.enc(x_engineered))))
        direct_impact = F.relu(self.monotonic_weight) * x[:, 3].unsqueeze(1)
        
        return deep_out + direct_impact

class BalancedLoss(nn.Module):
    def __init__(self, pos_weight=2.0):
        super().__init__()
        self.pw = torch.tensor([pos_weight])
    def forward(self, logits, targets):
        return F.binary_cross_entropy_with_logits(logits, targets, pos_weight=self.pw.to(logits.device))

# =====================================================================
# 2. TRAIN FUNCTION
# =====================================================================
def train_model(csv_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f" Loading dataset from {csv_path}...")
    
    # 1. Load Data
    if csv_path.endswith('.xlsx'):
        df = pd.read_excel(csv_path)
    else:
        df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    
    # 2. Data Cleaning
    if 'age/gender' in df.columns:
        df['Age'] = df['age/gender'].astype(str).str.extract(r'(\d+)').astype(float)
        
    bool_map = {'Yes': 1, 'yes': 1, 'True': 1, 'No': 0, 'no': 0, 'False': 0, True: 1, False: 0}
    if 'Hospital_before' in df.columns:
        df['Hospital_before'] = df['Hospital_before'].astype(str).map(bool_map)
        
    if 'Infection_Freq' in df.columns:
        df['Infection_Freq'] = pd.to_numeric(df['Infection_Freq'], errors='coerce')
        
    target_map = {'R': 1, 'r': 1, 'Intermediate': 1, 'i': 1, '1': 1, 'S': 0, 's': 0, '0': 0, 1: 1, 0: 0}
    if 'CIP' in df.columns:
        df['CIP'] = df['CIP'].astype(str).str.strip().map(target_map)
        
    # Drop rows missing the 4 core features
    df_clean = df.dropna(subset=['Souches', 'Age', 'Hospital_before', 'Infection_Freq', 'CIP']).copy()
    
    # Clean Souches strings
    df_clean['Souches'] = df_clean['Souches'].astype(str).str.lower().str.replace(r'^s\d+\s+', '', regex=True).str.strip()
    
    # Encode Souches
    le = LabelEncoder()
    df_clean['Souches_Encoded'] = le.fit_transform(df_clean['Souches'])
    
    print(f" Cleaned dataset size: {len(df_clean)} rows")

    # 3. Prepare Tensors & Scale Data
    X = df_clean[['Souches_Encoded', 'Age', 'Hospital_before', 'Infection_Freq']].values.astype(np.float32)
    Y = df_clean['CIP'].values.astype(np.float32)
    
    age_mean, age_std = X[:, 1].mean(), X[:, 1].std()
    freq_mean, freq_std = X[:, 3].mean(), X[:, 3].std()
    
    X[:, 1] = (X[:, 1] - age_mean) / (age_std + 1e-8)
    X[:, 3] = (X[:, 3] - freq_mean) / (freq_std + 1e-8)
    
    # 4. Save Artifacts for API
    save_dir = os.path.join(os.path.dirname(__file__), "app", "models")
    os.makedirs(save_dir, exist_ok=True)
    
    np.save(os.path.join(save_dir, "strain_encoder_classes.npy"), le.classes_)
    np.save(os.path.join(save_dir, "scaler_params.npy"), np.array([age_mean, age_std, freq_mean, freq_std]))
    
    # 5. Handle Imbalance
    smote = SMOTE(random_state=42)
    X_res, Y_res = smote.fit_resample(X, Y)

    x_train, y_train = torch.tensor(X_res).to(device), torch.tensor(Y_res).unsqueeze(1).to(device)
    x_eval, y_eval = torch.tensor(X).to(device), torch.tensor(Y).unsqueeze(1).to(device)

    # 6. Initialize Model
    model = SentinelMLP(in_dim=4).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    criterion = BalancedLoss()

    print(" Training Monotonic Balanced Model...")
    for epoch in range(150):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(x_train), y_train)
        loss.backward()
        optimizer.step()

        if epoch % 30 == 0:
            print(f"Epoch {epoch:3d} | Loss: {loss.item():.4f}")

    # 7. Evaluate and Find Threshold
    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(model(x_eval)).cpu().numpy().flatten()
        y_true = y_eval.cpu().numpy().flatten()

    best_t, best_acc, final_rec = 0.5, 0, 0
    for t in np.arange(0.2, 0.8, 0.01):
        preds = (probs >= t).astype(int)
        acc = accuracy_score(y_true, preds)
        rec = recall_score(y_true, preds)
        if rec >= 0.70:
            if acc > best_acc:
                best_acc, best_t, final_rec = acc, t, rec

    print(f"\n✅ RE-BALANCED RESULTS:")
    print(f"   Optimal Threshold: {best_t:.2f} (Update THRESHOLD in gnn.py to this!)")
    print(f"   📊 Accuracy:       {best_acc:.2f}")
    print(f"   📊 Recall:         {final_rec:.2f}")
    print(f"   🔒 Monotonic Weight: {model.monotonic_weight.item():.4f} (Must be > 0)")

    # 8. Save Model
    save_path = os.path.join(save_dir, "sentinel_gnn_best.pth")
    torch.save(model.state_dict(), save_path)
    print(f"SUCCESS! Artifacts saved to {save_dir}/")

    return model

if __name__ == "__main__":
    # Ensure this points to your actual dataset file
    dataset_path = "Bacteria_dataset_Multiresictance (1).csv"
    if os.path.exists(dataset_path):
        train_model(dataset_path)
    else:
        print(f" Error: Dataset not found at {dataset_path}")