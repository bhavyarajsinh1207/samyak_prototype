# api/schemas.py
from pydantic import BaseModel

class PredictionRequest(BaseModel):
    data: list[list[float]] # Example: [[feature1, feature2], [f3, f4]]

class PredictionResponse(BaseModel):
    predictions: list[float] # Example: [0.8, 0.2] or [123.45]

class KpiCalculationRequest(BaseModel):
    dataframe: dict # Dictionary representing a DataFrame (e.g., {col1: [v1,v2], col2: [v3,v4]})
    expression: str # Excel-like expression, e.g., "=SUM(Sales)"

class KpiCalculationResponse(BaseModel):
    kpi_name: str = "Calculated KPI"
    value: float | str # Can be float or string depending on KPI type