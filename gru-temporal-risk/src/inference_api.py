from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import torch
import joblib
from typing import List

from src.model import GRUModel
from src.preprocessing import apply_scaler

app = FastAPI(title="MEDHA GRU Temporal Risk Inference API")

# Load models and scalers on startup
MODEL_PATH = "models/best_gru_model.pth"
SCALER_PATH = "models/scaler.joblib"
CALIBRATOR_PATH = "models/calibrator.joblib"
THRESHOLD = 0.15 # Best threshold found during testing

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
scaler = None
calibrator = None

@app.on_event("startup")
def load_assets():
    global model, scaler, calibrator
    try:
        scaler = joblib.load(SCALER_PATH)
        calibrator = joblib.load(CALIBRATOR_PATH)
        # 72 is the number of features the model was trained on
        model = GRUModel(input_size=72).to(device)
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
        model.eval()
        print("Model, scaler, and calibrator loaded successfully.")
    except Exception as e:
        print(f"Error loading assets: {e}")

class SequenceInput(BaseModel):
    # Expects a sequence of length 7, each with 72 features
    features: List[List[float]] 

@app.post("/predict")
def predict_risk(data: SequenceInput):
    if not model or not scaler or not calibrator:
        raise HTTPException(status_code=500, detail="Models not loaded properly.")
    
    # Validate shape
    sequence = np.array(data.features, dtype=np.float32)
    if sequence.shape != (7, 72):
        raise HTTPException(status_code=400, detail=f"Expected shape (7, 72), got {sequence.shape}")
        
    # Reshape for 3D model [batch=1, timesteps=7, features=72]
    sequence_3d = np.expand_dims(sequence, axis=0)
    
    # 1. Scale
    scaled_sequence = apply_scaler(scaler, sequence_3d)
    
    # 2. PyTorch Prediction
    with torch.no_grad():
        tensor_input = torch.from_numpy(scaled_sequence).to(device)
        raw_prob = torch.sigmoid(model(tensor_input)).cpu().numpy().flatten()
        
    # 3. Calibrate
    calibrated_prob = calibrator.predict_proba(raw_prob.reshape(-1, 1))[:, 1][0]
    
    # 4. Threshold
    prediction = int(calibrated_prob >= THRESHOLD)
    
    return {
        "temporal_risk_score": float(calibrated_prob),
        "prediction": prediction,
        "threshold_used": THRESHOLD
    }
