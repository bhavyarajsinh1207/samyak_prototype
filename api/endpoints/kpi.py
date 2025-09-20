# api/endpoints/kpi.py
from fastapi import APIRouter, HTTPException
import pandas as pd
from api.schemas import KpiCalculationRequest, KpiCalculationResponse
from utils.excel_functions import apply_excel_function

router = APIRouter()

@router.post("/kpi", response_model=KpiCalculationResponse)
async def calculate_kpi(request: KpiCalculationRequest):
    """
    Calculate KPIs using Excel-like expressions
    """
    try:
        # Convert dict to pandas DataFrame
        df = pd.DataFrame(request.data)
        
        # Apply the Excel-like function
        kpi_value = apply_excel_function(request.expression, df)

        # Handle different return types
        if isinstance(kpi_value, pd.Series):
            kpi_value = kpi_value.tolist()
        elif hasattr(kpi_value, 'item'):  # numpy types
            kpi_value = kpi_value.item()
        
        return KpiCalculationResponse(
            kpi_name=request.kpi_name or "Calculated KPI",
            value=kpi_value,
            expression=request.expression,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI calculation failed: {str(e)}")

@router.get("/kpi/examples")
async def kpi_examples():
    """
    Get examples of supported Excel functions
    """
    examples = {
        "basic_math": [
            "=SUM(column_name)",
            "=AVERAGE(column_name)",
            "=MAX(column_name)",
            "=MIN(column_name)",
            "=COUNT(column_name)"
        ],
        "conditional": [
            "=IF(condition, true_value, false_value)",
            "=IF(column1 > 100, 'High', 'Low')"
        ],
        "advanced": [
            "=SUM(column1 * column2)",
            "=AVERAGE(IF(column1 > 0, column1, 0))"
        ]
    }
    
    return {"examples": examples}