from pydantic import BaseModel
from typing import Dict, Any

class AnalyzeRequest(BaseModel):
    dialog_text: str
    content_mode: str = "Client +"

class AnalyzeResponse(BaseModel):
    total_score: float
    criteria: Dict[str, float]
    summary: str
    recommendations: str
    raw_model_output: Any | None = None
