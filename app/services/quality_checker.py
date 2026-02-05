import re
from typing import Dict, Any, List
from openai import OpenAI
from app.core.config import settings
from app.services.prompts import BASE_PROMPT

client = OpenAI(api_key=settings.openai_api_key)


def split_dialog(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap if overlap > 0 else end

    return chunks


def build_prompt(dialog_chunk: str, content_mode: str) -> str:
    return (
        f"{BASE_PROMPT}\n\n"
        f"Режим анализа: {content_mode}.\n"
        f"Анализируй следующий фрагмент диалога менеджера с клиентом:\n\n"
        f"{dialog_chunk}\n\n"
        f"Сформируй ответ строго в виде структурированного, хорошо читаемого текста."
    )


def call_model(prompt: str) -> str:
    response = client.responses.create(
        model=settings.model_name,
        input=prompt,
        temperature=settings.temperature,
    )
    # универсальный способ получить текст из responses API
    try:
        return response.output[0].content[0].text
    except Exception:
        return str(response)


def parse_quality_response(raw_text: str) -> Dict[str, Any]:
    score = 0.0

    # Поддерживаем и "quality:", и "качество:"
    m = re.search(r"(quality|качество)\s*:\s*(\d{1,3}|nan)", raw_text, re.IGNORECASE)
    if m:
        val = m.group(2)
        if val.lower() != "nan":
            try:
                n = int(val)
                if 0 <= n <= 100:
                    score = float(n)
            except ValueError:
                pass

    parts = re.split(r"(?i)первый отчет:|first report:|второй отчет:|second report:|третий отчет:|third report:", raw_text)
    summary_text = raw_text
    recommendations_text = ""

    if len(parts) >= 4:
        first = parts[1].strip()
        # second = parts[2].strip()  # пока не используем
        third = parts[3].strip()
        summary_text = first
        recommendations_text = third

    return {
        "total_score": score,
        "criteria": {},
        "summary": summary_text,
        "recommendations": recommendations_text,
        "raw_model_output": raw_text,
    }


def analyze_dialog(dialog_text: str, content_mode: str) -> Dict[str, Any]:
    chunks = split_dialog(
        dialog_text,
        settings.chunk_size,
        settings.chunk_overlap,
    )
    if not chunks:
        return {
            "total_score": 0.0,
            "criteria": {},
            "summary": "Диалог пустой или не распознан.",
            "recommendations": "",
            "raw_model_output": None,
        }

    chunks = chunks[: settings.num_fragment]

    reports: List[Dict[str, Any]] = []
    for ch in chunks:
        prompt = build_prompt(ch, content_mode)
        raw = call_model(prompt)
        report = parse_quality_response(raw)
        reports.append(report)

    if not reports:
        return {
            "total_score": 0.0,
            "criteria": {},
            "summary": "",
            "recommendations": "",
            "raw_model_output": None,
        }

    avg_score = sum(r["total_score"] for r in reports) / len(reports)
    summary = "\n\n".join(r["summary"] for r in reports)

    return {
        "total_score": avg_score,
        "criteria": reports[0]["criteria"],
        "summary": summary,
        "recommendations": "",
        "raw_model_output": reports,
    }
