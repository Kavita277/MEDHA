from pydantic import BaseModel
from typing import List
from app.schemas.risk_history_schema import RiskHistoryChronological

class TrendResponse(BaseModel):
    current_dds: float
    average_dds: float
    highest_dds: float
    lowest_dds: float
    trend: str
    last_7_predictions: List[RiskHistoryChronological]
