from fastapi import FastAPI
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.quality_checker import analyze_dialog

app = FastAPI(title="Sales Quality AI Audit")

@app.post("/analyze_call", response_model=AnalyzeResponse)
async def analyze_call(payload: AnalyzeRequest):
    report = analyze_dialog(payload.dialog_text, payload.content_mode)
    return AnalyzeResponse(**report)
