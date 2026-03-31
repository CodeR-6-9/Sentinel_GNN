import os
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import recall_score, precision_score, f1_score, roc_auc_score, accuracy_score
from imblearn.over_sampling import SMOTE

# ==========================================
# 1. MODEL ARCHITECTURE
# ==========================================
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
        age_freq = x[:, 1] * x[:, 3]
        hosp_freq = x[:, 2] * x[:, 3]
        age_hosp = x[:, 1] * x[:, 2]
        risk_factor = x[:, 1] * x[:, 2] * x[:, 3]
        
        x_engineered = torch.cat([
            x, age_freq.unsqueeze(1), hosp_freq.unsqueeze(1), 
            age_hosp.unsqueeze(1), risk_factor.unsqueeze(1)
        ], dim=1)
        
        return self.head(self.res2(self.res1(self.enc(x_engineered))))

class OptimizedLoss(nn.Module):
    def __init__(self, pos_weight=2.5):
        super().__init__()
        self.pw = torch.tensor([pos_weight])
    def forward(self, logits, targets):
        return F.binary_cross_entropy_with_logits(logits, targets, pos_weight=self.pw.to(logits.device))

# ==========================================
# 2. TRAINING PIPELINE
# ==========================================
def train_model(csv_path, save_dir):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚙️ Using device: {device}")
    
    # 1. Load Data
    print("📂 Loading data...")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    
    # 2. Preprocessing
    if 'age/gender' in df.columns:
        df['Age'] = df['age/gender'].astype(str).str.extract(r'(\d+)').astype(float)
    
    bool_map = {'Yes': 1, 'yes': 1, 'True': 1, 'No': 0, 'no': 0, 'False': 0}
    if 'Hospital_before' in df.columns:
        df['Hospital_before'] = df['Hospital_before'].astype(str).map(bool_map)
        
    if 'Infection_Freq' in df.columns:
        df['Infection_Freq'] = pd.to_numeric(df['Infection_Freq'], errors='coerce')
        
    target_map = {'R': 1, 'r': 1, 'Intermediate': 1, 'i': 1, '1': 1, 1: 1, 'S': 0, 's': 0, '0': 0, 0: 0} 
    if 'CIP' in df.columns:
        df['CIP'] = df['CIP'].astype(str).str.strip().map(target_map)
    
    df_clean = df.dropna(subset=['Souches', 'Age', 'Hospital_before', 'Infection_Freq', 'CIP']).copy()
    
    # Clean strain names
    df_clean['Souches'] = df_clean['Souches'].astype(str).str.lower().str.replace(r'^s\d+\s+', '', regex=True).str.strip()
    
    # Encode strains and save the mapping for the backend
    le = LabelEncoder()
    df_clean['Souches_Encoded'] = le.fit_transform(df_clean['Souches'])
    os.makedirs(save_dir, exist_ok=True)
    np.save(os.path.join(save_dir, "strain_encoder_classes.npy"), le.classes_)

    # 3. Feature Scaling
    X = df_clean[['Souches_Encoded', 'Age', 'Hospital_before', 'Infection_Freq']].values.astype(np.float32)
    age_mean, age_std = X[:, 1].mean(), X[:, 1].std()
    freq_mean, freq_std = X[:, 3].mean(), X[:, 3].std()
    
    X[:, 1] = (X[:, 1] - age_mean) / (age_std + 1e-8)
    X[:, 3] = (X[:, 3] - freq_mean) / (freq_std + 1e-8)
    Y = df_clean['CIP'].values.astype(np.float32)

    # 4. Handle Imbalance
    print("⚖️ Balancing classes with SMOTE...")
    smote = SMOTE(random_state=42, sampling_strategy=0.8)
    X_res, Y_res = smote.fit_resample(X, Y)

    x_train = torch.tensor(X_res).to(device)
    y_train = torch.tensor(Y_res).unsqueeze(1).to(device)
    x_eval = torch.tensor(X).to(device)
    y_eval = torch.tensor(Y).unsqueeze(1).to(device)

    # 5. Initialize Model
    model = SentinelMLP(in_dim=4).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-4)
    criterion = OptimizedLoss()

    # 6. Training Loop
    print("🚀 Training Fully Optimized Model...")
    for epoch in range(150):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(x_train), y_train)
        loss.backward()
        optimizer.step()

    # 7. Evaluation & Threshold Tuning
    model.eval()
    with torch.no_grad():
        probs = torch.sigmoid(model(x_eval)).cpu().numpy().flatten()
        y_true = y_eval.cpu().numpy().flatten()
        
    best_t, best_f1, final_acc, final_rec = 0.5, 0, 0, 0
    for t in np.arange(0.3, 0.8, 0.01): 
        preds = (probs >= t).astype(int)
        acc = accuracy_score(y_true, preds)
        rec = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)
        
        if rec >= 0.75: # Safety Floor
            if f1 > best_f1:
                best_f1, best_t, final_acc, final_rec = f1, t, acc, rec

    print(f"\n FINAL OPTIMIZED RESULTS:")
    print(f"   Optimal Threshold: {best_t:.2f}")
    print(f"    Accuracy:       {final_acc:.2f}")
    print(f"   Recall:         {final_rec:.2f}")
    print(f"   AUC-ROC:        {roc_auc_score(y_true, probs):.2f}")
    
    # 8. Save Model Weights
    model_path = os.path.join(save_dir, "sentinel_gnn_best.pth")
    torch.save(model.state_dict(), model_path)
    print(f"\n💾 Model weights saved to: {model_path}")
    print(f"💾 Strain encoder saved to: {os.path.join(save_dir, 'strain_encoder_classes.npy')}")
    
    print("\n--- ⚠️ SCALING PARAMETERS (Update your gnn.py with these!) ---")
    print(f"AGE_MEAN = {age_mean:.4f}")
    print(f"AGE_STD  = {age_std:.4f}")
    print(f"FREQ_MEAN = {freq_mean:.4f}")
    print(f"FREQ_STD  = {freq_std:.4f}")
    print(f"THRESHOLD = {best_t:.2f}")
    print("-------------------------------------------------------------------\n")

# ==========================================
# 3. CLI EXECUTION
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the Sentinel CIP Resistance Model")
    parser.add_argument("--csv_path", type=str, required=True, help="Path to the training CSV file")
    parser.add_argument("--save_dir", type=str, default="./models", help="Directory to save the outputs")
    
    args = parser.parse_args()
    
    train_model(args.csv_path, args.save_dir)