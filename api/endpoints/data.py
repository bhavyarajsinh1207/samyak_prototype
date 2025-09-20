# api/endpoints/data.py
from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
from scipy import stats
from api.schemas import DataAnalysisRequest, DataAnalysisResponse

router = APIRouter()

@router.post("/data/analyze", response_model=DataAnalysisResponse)
async def analyze_data(request: DataAnalysisRequest):
    """
    Perform various data analysis operations
    """
    try:
        df = pd.DataFrame(request.data)
        results = {}

        if request.analysis_type == "stats":
            # Statistical summary
            numeric_cols = df.select_dtypes(include=np.number).columns
            if len(numeric_cols) > 0:
                stats_df = df[numeric_cols].describe().T
                stats_df['median'] = df[numeric_cols].median()
                stats_df['variance'] = df[numeric_cols].var()
                stats_df['skewness'] = df[numeric_cols].apply(lambda x: stats.skew(x.dropna()))
                stats_df['kurtosis'] = df[numeric_cols].apply(lambda x: stats.kurtosis(x.dropna()))
                results = stats_df.to_dict()
            else:
                results = {"message": "No numeric columns for statistical analysis"}

        elif request.analysis_type == "missing":
            # Missing values analysis
            missing = df.isna().sum()
            missing_pct = (missing / len(df)) * 100
            results = {
                "missing_counts": missing.to_dict(),
                "missing_percentages": missing_pct.to_dict(),
                "total_missing": int(missing.sum())
            }

        elif request.analysis_type == "correlation":
            # Correlation matrix
            numeric_cols = df.select_dtypes(include=np.number).columns
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr()
                results = corr_matrix.to_dict()
            else:
                results = {"message": "Need at least 2 numeric columns for correlation"}

        elif request.analysis_type == "overview":
            # Data overview
            results = {
                "shape": df.shape,
                "columns": list(df.columns),
                "data_types": df.dtypes.astype(str).to_dict(),
                "numeric_columns": list(df.select_dtypes(include=np.number).columns),
                "categorical_columns": list(df.select_dtypes(exclude=np.number).columns),
                "total_missing": int(df.isna().sum().sum()),
                "duplicates": int(df.duplicated().sum())
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown analysis type: {request.analysis_type}")

        return DataAnalysisResponse(
            analysis_type=request.analysis_type,
            results=results,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data analysis failed: {str(e)}")