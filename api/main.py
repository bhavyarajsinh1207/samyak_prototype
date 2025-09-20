# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.ai_models import load_model, predict_with_cnn
from utils.excel_functions import apply_excel_function # For KPI calculation via API

app = FastAPI(
    title="Data Analysis API",
    description="API for AI model inference and data analysis functions.",
    version="1.0.0"
)

# --- Model Loading (Global for efficiency) ---
# This assumes you have a pre-trained model saved in data/models
# You might need to adjust the model name and ensure it's available.
try:
    # Replace 'my_cnn_model' with the actual name of your saved model
    # You might need to specify input_shape and num_classes if your model requires it for loading
    # For Keras, load_model usually handles this if the model was saved correctly.
    global_trained_model = load_model("my_cnn_model")
    print("AI model loaded successfully for API.")
except Exception as e:
    global_trained_model = None
    print(f"Could not load AI model for API: {e}. Prediction endpoint will not be available.")

# --- Pydantic Models for Request/Response ---
class PredictionRequest(BaseModel):
    data: list[list[float]] # Expects a list of lists (e.g., [[feature1, feature2], [f3, f4]])
    # Add other fields if your model needs them (e.g., image_id, preprocessing flags)

class PredictionResponse(BaseModel):
    predictions: list[float] # Or list[list[float]] for multi-output/softmax probabilities

class KpiCalculationRequest(BaseModel):
    dataframe: dict # Dictionary representing a DataFrame (e.g., {col1: [v1,v2], col2: [v3,v4]})
    expression: str # Excel-like expression, e.g., "=SUM(Sales)"

class KpiCalculationResponse(BaseModel):
    kpi_name: str = "Calculated KPI"
    value: float | str # Can be float or string depending on KPI type

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Data Analysis API!"}

@app.post("/predict")
async def predict(request: PredictionRequest):
    if global_trained_model is None:
        raise HTTPException(status_code=503, detail="AI model not loaded. Cannot make predictions.")

    try:
        # Convert input data to numpy array, reshape if necessary for CNN
        input_data = np.array(request.data)
        # Assuming the model expects (samples, timesteps, features) or (samples, height, width, channels)
        # Adjust reshaping based on your model's input_shape
        if len(input_data.shape) == 2: # If it's tabular data (samples, features)
            input_data = input_data.reshape(input_data.shape[0], input_data.shape[1], 1) # Add channel dim for 1D CNN

        predictions = predict_with_cnn(global_trained_model, input_data)

        # Convert predictions to a list for JSON response
        # Handle softmax output for classification (return probabilities or argmax)
        if predictions.shape[-1] > 1: # Multi-class classification
            predictions_list = predictions.tolist() # Return probabilities
        else: # Binary classification or regression
            predictions_list = predictions.flatten().tolist() # Return single value per sample

        return PredictionResponse(predictions=predictions_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

@app.post("/calculate_kpi")
async def calculate_kpi(request: KpiCalculationRequest):
    try:
        # Convert dict to pandas DataFrame
        df = pd.DataFrame(request.dataframe)
        
        # Apply the Excel-like function
        kpi_value = apply_excel_function(request.expression, df)

        # Handle if the result is a pandas Series (e.g., from IF function)
        if isinstance(kpi_value, pd.Series):
            # For API, you might want to return the first value or an aggregation
            # Or modify apply_excel_function to always return a scalar for KPI
            kpi_value = kpi_value.iloc[0] if not kpi_value.empty else None

        return KpiCalculationResponse(value=kpi_value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {e}")

# To run this API:
# 1. Save it as api/main.py
# 2. Navigate to your project root in terminal
# 3. Run: uvicorn api.main:app --reload --port 8000
# (You can change the port)