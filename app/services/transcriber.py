import os
import tempfile
from typing import Tuple
from openai import OpenAI
import requests
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)


def transcribe_audio(file_path: str) -> str:
    """
    Превращает аудио в текст с помощью Whisper.
    Ожидает локальный путь к файлу (mp3, wav и т.п.).
    Возвращает строку с текстом диалога.
    """
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",  # вернёт просто строку
        )
    # в режиме response_format="text" transcription уже строка
    return transcription

def download_audio_to_temp(url: str) -> Tuple[str, str]:
    """
    Скачивает аудио по URL во временный файл.
    Возвращает (tmp_path, filename).
    """
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()

    # Попробуем угадать расширение
    filename = url.split("/")[-1] or "audio"
    _, ext = os.path.splitext(filename)
    if not ext:
        ext = ".mp3"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            tmp.write(chunk)
    tmp_path = tmp.name
    tmp.close()

    return tmp_path, filename
