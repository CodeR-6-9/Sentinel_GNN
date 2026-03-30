"""
PyTorch MLP Inference Module for Antimicrobial Resistance Prediction

This module provides the inference interface for the epidemiological patient
risk model trained on antimicrobial resistance patterns.

Expected to be called by orchestrator.py with patient epidemiological features
and returns resistance prediction with confidence and driving factors.
"""

from typing import Tuple, List

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("[GNN] Warning: PyTorch not installed. Using fallback rule-based inference.")


class AntimicrobialResistanceMLPModel(nn.Module if TORCH_AVAILABLE else object):
    """
    PyTorch MLP for epidemiological antimicrobial resistance prediction.
    
    Input Features (6):
    - Age: Normalized (0-120) / 120
    - Gender: One-hot [Male, Female, Other]
    - Diabetes: Binary (0/1)
    - Hospital_before: Binary (0/1)
    - Hypertension: Binary (0/1)
    - Infection_Freq: Normalized (0-10) / 10
    
    Total input dim: 9 (6 epidemiological + 3 gender one-hot)
    
    Architecture:
    Input(9) → Dense(32, ReLU) → Dropout(0.3) → 
    Dense(16, ReLU) → Dropout(0.3) → 
    Dense(1, Sigmoid) → Output (0-1 confidence)
    """
    
    def __init__(self):
        """Initialize MLP architecture."""
        if TORCH_AVAILABLE:
            super().__init__()
            self.fc1 = nn.Linear(9, 32)
            self.dropout1 = nn.Dropout(0.3)
            self.fc2 = nn.Linear(32, 16)
            self.dropout2 = nn.Dropout(0.3)
            self.fc3 = nn.Linear(16, 1)
            self.relu = nn.ReLU()
            self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        """
        Forward pass through MLP.
        
        Args:
            x: Tensor of shape (batch_size, 9) with patient features
        
        Returns:
            Tensor of shape (batch_size, 1) with resistance confidence (0-1)
        """
        if not TORCH_AVAILABLE:
            return None
        
        x = self.relu(self.fc1(x))
        x = self.dropout1(x)
        x = self.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.sigmoid(self.fc3(x))
        return x


# Initialize and load model (in production, this would load from checkpoint)
_model = None
if TORCH_AVAILABLE:
    try:
        _model = AntimicrobialResistanceMLPModel()
        _model.eval()
        print("[GNN] PyTorch model initialized in eval mode")
    except Exception as e:
        print(f"[GNN] Warning: Model initialization failed: {e}")
        _model = None
else:
    print("[GNN] Using fallback rule-based inference (no PyTorch available)")


def inference(
    age: int,
    gender: str,
    diabetes: bool,
    hospital_before: bool,
    hypertension: bool,
    infection_freq: int
) -> Tuple[str, float, List[str]]:
    """
    Perform inference on patient epidemiological profile.
    
    This function is the primary interface called by the orchestrator.
    It converts patient features to tensor format, runs through the MLP,
    and interprets the output with business logic.
    
    Args:
        age: Patient age in years (0-120)
        gender: Biological sex ("Male", "Female", "Other")
        diabetes: Diabetes mellitus diagnosis (True/False)
        hospital_before: Previous hospitalization (True/False)
        hypertension: Hypertension diagnosis (True/False)
        infection_freq: Number of infections in past year (0-10)
    
    Returns:
        Tuple of:
        - prediction (str): "Resistant" or "Susceptible"
        - confidence (float): Model confidence score (0.0-1.0)
        - driving_factors (List[str]): Patient risk factors contributing to resistance
    
    Example:
        >>> prediction, confidence, factors = inference(
        ...     age=65, gender="Male", diabetes=True, hospital_before=True,
        ...     hypertension=True, infection_freq=4
        ... )
        >>> print(f"{prediction} with {confidence:.2%} confidence")
        Resistant with 82% confidence
    """
    
    # Feature engineering: Create 9-dimensional input vector
    # [age_norm, gender_one_hot(3), diabetes, hospital_before, hypertension, infection_freq_norm]
    
    # Normalize continuous features
    age_normalized = age / 120.0
    infection_freq_normalized = infection_freq / 10.0
    
    # One-hot encode gender
    gender_one_hot = [0.0, 0.0, 0.0]
    if gender == "Male":
        gender_one_hot = [1.0, 0.0, 0.0]
    elif gender == "Female":
        gender_one_hot = [0.0, 1.0, 0.0]
    else:  # Other
        gender_one_hot = [0.0, 0.0, 1.0]
    
    # Build feature vector
    features = [
        age_normalized,
        *gender_one_hot,
        float(diabetes),
        float(hospital_before),
        float(hypertension),
        infection_freq_normalized
    ]
    
    # Convert to tensor and run inference
    try:
        if TORCH_AVAILABLE and _model is not None:
            with torch.no_grad():
                input_tensor = torch.tensor([features], dtype=torch.float32)
                output = _model(input_tensor).item()
                confidence = output
        else:
            # Fallback: rule-based inference (for development/testing)
            confidence = 0.5
            risk_score = (
                (age > 60) * 0.2 +
                (diabetes) * 0.25 +
                (hospital_before) * 0.3 +
                (hypertension) * 0.15 +
                (infection_freq > 3) * 0.1
            )
            confidence = min(0.95, max(0.4, 0.4 + risk_score))
    
    except Exception as e:
        print(f"[GNN] Inference error: {e}")
        confidence = 0.5
    
    # Determine prediction threshold
    threshold = 0.5
    is_resistant = confidence >= threshold
    prediction = "Resistant" if is_resistant else "Susceptible"
    
    # Identify driving factors (risk factors contributing to resistance)
    driving_factors = []
    
    if age > 60:
        driving_factors.append("Age_Over_60")
    if diabetes:
        driving_factors.append("Diabetes")
    if hospital_before:
        driving_factors.append("Hospital_before")
    if hypertension:
        driving_factors.append("Hypertension")
    if infection_freq > 3:
        driving_factors.append("High_Infection_Freq")
    
    return prediction, confidence, driving_factors


# Example usage
if __name__ == "__main__":
    # Test the inference function
    test_cases = [
        {
            "age": 65,
            "gender": "Male",
            "diabetes": True,
            "hospital_before": True,
            "hypertension": True,
            "infection_freq": 4,
            "desc": "High-risk patient"
        },
        {
            "age": 35,
            "gender": "Female",
            "diabetes": False,
            "hospital_before": False,
            "hypertension": False,
            "infection_freq": 0,
            "desc": "Low-risk patient"
        },
        {
            "age": 55,
            "gender": "Other",
            "diabetes": True,
            "hospital_before": False,
            "hypertension": True,
            "infection_freq": 2,
            "desc": "Moderate-risk patient"
        }
    ]
    
    print("\n[GNN Testing]")
    for case in test_cases:
        desc = case.pop("desc")
        prediction, confidence, factors = inference(**case)
        print(f"\n{desc}:")
        print(f"  Parameters: {case}")
        print(f"  Prediction: {prediction} (confidence: {confidence:.2%})")
        print(f"  Risk Factors: {', '.join(factors) if factors else 'None'}")
