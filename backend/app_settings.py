"""
Настройки, которые можно менять из интерфейса.
Значения по умолчанию берутся из settings.EXTRACTOR, изменения лежат в data/settings.json.
В алгоритме читать так:  from backend import app_settings;  cfg = app_settings.load()
"""
import json

from django.conf import settings


def defaults() -> dict:
    e = settings.EXTRACTOR
    return {
        "ollama_base_url": e["OLLAMA_BASE_URL"],
        "ollama_model": e["OLLAMA_MODEL"],
        "ollama_timeout": e["OLLAMA_TIMEOUT"],
        "ollama_temperature": e["OLLAMA_TEMPERATURE"],
        "use_llm": e["USE_LLM"],
        "confidence_high": e["CONFIDENCE_HIGH"],
        "confidence_low": e["CONFIDENCE_LOW"],
        "batch_max_rows": e["BATCH_MAX_ROWS"],
    }


def _path():
    return settings.DATA_DIR / "settings.json"


def load() -> dict:
    data = defaults()
    try:
        saved = json.loads(_path().read_text(encoding="utf-8"))
        data.update({k: v for k, v in saved.items() if k in data})
    except (FileNotFoundError, ValueError):
        pass
    return data


def save(values: dict) -> None:
    clean = {k: v for k, v in values.items() if k in defaults()}
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")


def reset() -> None:
    try:
        _path().unlink()
    except FileNotFoundError:
        pass