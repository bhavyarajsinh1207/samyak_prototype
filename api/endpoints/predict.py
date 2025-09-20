# api/endpoints/predict.py
from fastapi import APIRouter, HTTPException
import numpy as np
from api.schemas import PredictionRequest, PredictionResponse
from utils.ai_models import load_model, predict_with_cnn

router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(request: PredictionRequest):
    """
    Make predictions using trained AI models
    """
    try:
        # Load model (could be cached)
        model = load_model(request.model_name)
        if model is None:
            raise HTTPException(status_code=404, detail=f"Model '{request.model_name}' not found")

        # Convert input data to numpy array
        input_data = np.array(request.data)
        
        # Reshape if specified
        if request.reshape_dim:
            input_data = input_data.reshape(request.reshape_dim)
        elif len(input_data.shape) == 2:
            # Default reshape for 1D CNN
            input_data = input_data.reshape(input_data.shape[0], input_data.shape[1], 1)

        # Make predictions
        predictions = predict_with_cnn(model, input_data)

        # Convert predictions for response
        if predictions.shape[-1] > 1:  # Multi-class classification
            predictions_list = predictions.tolist()
        else:  # Binary classification or regression
            predictions_list = predictions.flatten().tolist()

        return PredictionResponse(
            predictions=predictions_list,
            model_used=request.model_name,
            input_shape=list(input_data.shape)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/models")
async def list_models():
    """
    List available trained models
    """
    import os
    model_dir = "data/models"
    models = []
    if os.path.exists(model_dir):
        models = [f.replace(".h5", "") for f in os.listdir(model_dir) if f.endswith(".h5")]
    
    return {"available_models": models, "count": len(models)}