import os

# ==============================
# 🔹 TRAIN FUNCTION (UPDATED)
# ==============================

def train_model(csv_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"📊 Loading dataset from {csv_path}...")
    
    # Handle both CSV and Excel safely
    if csv_path.endswith('.xlsx'):
        df = pd.read_excel(csv_path)
    else:
        df = pd.read_csv(csv_path)

    # --- THE ROSETTA STONE DATA CLEANING ---
    df.columns = df.columns.str.strip()
    
    # Extract Age & Gender from 'age/gender' if it exists in the raw data
    if 'age/gender' in df.columns:
        df['Age'] = df['age/gender'].astype(str).str.extract(r'(\d+)').astype(float)
        df['Gender_Str'] = df['age/gender'].astype(str).str.extract(r'([M|F|m|f])')
        df['Gender'] = df['Gender_Str'].map({'M': 1, 'm': 1, 'F': 0, 'f': 0})
    
    # Map Yes/No to 1/0
    bool_map = {'Yes': 1, 'yes': 1, True: 1, 'True': 1, 'No': 0, 'no': 0, False: 0, 'False': 0}
    for col in ['Diabetes', 'Hospital_before', 'Hypertension']:
        if col in df.columns:
            df[col] = df[col].map(bool_map)
            
    if 'Infection_Freq' in df.columns:
        df['Infection_Freq'] = pd.to_numeric(df['Infection_Freq'], errors='coerce')
    
    # Map Target Variable (CIP resistance)
    target_map = {'R': 1, 'S': 0, 'I': 1, 1: 1, 0: 0} 
    if 'CIP' in df.columns:
        df['CIP'] = df['CIP'].map(target_map)
    
    # Drop NaNs safely now that everything is mapped
    feature_cols = ['Age', 'Gender', 'Diabetes', 'Hospital_before', 'Hypertension', 'Infection_Freq']
    df_clean = df.dropna(subset=feature_cols + ['CIP']).copy()
    
    print(f"✅ Cleaned dataset size: {len(df_clean)} rows")

    # --- PREPARE TENSORS ---
    X = df_clean[feature_cols].values
    Y = df_clean['CIP'].values
    X_eng = engineer_features(X)

    # SMOTE
    smote = SMOTE(random_state=42, sampling_strategy=0.8)
    X_res, Y_res = smote.fit_resample(X_eng, Y)

    x_train = torch.tensor(X_res, dtype=torch.float).to(device)
    y_train = torch.tensor(Y_res, dtype=torch.float).unsqueeze(1).to(device)

    x_eval = torch.tensor(X_eng, dtype=torch.float).to(device)
    y_eval = torch.tensor(Y, dtype=torch.float).unsqueeze(1).to(device)

    # --- MODEL SETUP ---
    model = SentinelMLP().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
    criterion = HybridLoss()

    print("🚀 Training started...")

    for epoch in range(101):
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
                print(f"Epoch {epoch:3d} | Loss: {loss.item():.4f} | Recall: {rec:.3f}")

    # --- SAVE MODEL ---
    save_dir = "app/models"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "sentinel_gnn_best.pth")
    
    torch.save(model.state_dict(), save_path)
    print(f"🎉 SUCCESS! Model saved locally as {save_path}")

    return model
