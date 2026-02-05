from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.quality_checker import analyze_dialog
from app.services.transcriber import transcribe_audio, download_audio_to_temp
import tempfile
import os

app = FastAPI(title="Sales Quality AI Audit")

templates = Jinja2Templates(directory="templates")

@app.post("/analyze_call", response_model=AnalyzeResponse)
async def analyze_call(payload: AnalyzeRequest):
    report = analyze_dialog(payload.dialog_text, payload.content_mode)
    return AnalyzeResponse(**report)

@app.post("/analyze_audio_call", response_model=AnalyzeResponse)
async def analyze_audio_call(
    audio: UploadFile = File(...),
    content_mode: str = "Manager +",
):
    # 1. Сохраняем во временный файл
    suffix = os.path.splitext(audio.filename)[1] or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        data = await audio.read()
        tmp.write(data)

    try:
        # 2. Аудио -> текст
        dialog_text = transcribe_audio(tmp_path)

        # 3. Текст -> нейро-контроль качества
        report = analyze_dialog(dialog_text, content_mode)
        return AnalyzeResponse(**report)
    finally:
        # 4. Чистим временный файл
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

class AnalyzeAudioByUrlRequest(BaseModel):
    file_url: str
    content_mode: str = "Manager +"


@app.post("/analyze_audio_by_url", response_model=AnalyzeResponse)
async def analyze_audio_by_url(payload: AnalyzeAudioByUrlRequest):
    tmp_path, _ = download_audio_to_temp(payload.file_url)

    try:
        dialog_text = transcribe_audio(tmp_path)
        report = analyze_dialog(dialog_text, payload.content_mode)
        return AnalyzeResponse(**report)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "result": None})


@app.post("/web/analyze", response_class=HTMLResponse)
async def web_analyze(
    request: Request,
    dialog_text: str = Form(""),
    content_mode: str = Form("Manager +"),
    audio: UploadFile | None = File(None),
):
    tmp_path = None
    try:
        if audio and audio.filename:
            suffix = os.path.splitext(audio.filename)[1] or ".mp3"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp_path = tmp.name
                data = await audio.read()
                tmp.write(data)
            dialog = transcribe_audio(tmp_path)
        else:
            dialog = dialog_text or ""

        report = analyze_dialog(dialog, content_mode) if dialog.strip() else {
            "total_score": 0.0,
            "criteria": {},
            "summary": "Диалог не был передан. Введите текст или загрузите аудио.",
            "recommendations": "",
            "raw_model_output": None,
        }

        result = AnalyzeResponse(**report)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "result": result},
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
