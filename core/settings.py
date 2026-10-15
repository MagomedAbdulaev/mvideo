"""
Настройки Django-проекта: AI-платформа обработки карточек товаров М.Видео.

Структура проекта (ожидается):
    manage.py
    core/              <- проект Django, этот файл лежит в core/settings.py
    backend/           <- приложение: страницы и представления (главная, process, batch, review, evaluation)
    backend/extractor/ <- алгоритм извлечения (обычный Python-пакет, не зависит от веб-интерфейса)
    templates/         <- base.html и partials
    static/            <- свои css/js
    data/              <- датасеты, предсказания (не в git)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------------------------------
# Хелперы для переменных окружения
# --------------------------------------------------------------------------
def env(name: str, default=None):
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --------------------------------------------------------------------------
# Базовые настройки
# --------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY") or "dev-insecure-key-change-me"
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")


# --------------------------------------------------------------------------
# Приложения и middleware
# --------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Проект
    "backend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"


# --------------------------------------------------------------------------
# Шаблоны (Django Templates + Tailwind через CDN)
# --------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Пороги уверенности и список страниц доступны во всех шаблонах
                "backend.context_processors.site",
            ],
        },
    },
]


# --------------------------------------------------------------------------
# База данных (SQLite для прототипа)
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------------------------------
# Пароли (для админки)
# --------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------------------------
# Локализация
# --------------------------------------------------------------------------
LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


# --------------------------------------------------------------------------
# Статика и медиа
# --------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"  # загруженные CSV, экспортированные результаты

# Каталог с датасетами, предсказаниями и метриками
DATA_DIR = BASE_DIR / "data"


# --------------------------------------------------------------------------
# Загрузка файлов (массовая обработка CSV)
# --------------------------------------------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024   # 20 МБ в памяти, больше уходит во временный файл
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000             # формы review могут быть большими


# --------------------------------------------------------------------------
# Настройки алгоритма извлечения (приложение extractor)
# Читаются в коде как: from django.conf import settings; settings.EXTRACTOR[...]
# --------------------------------------------------------------------------
EXTRACTOR = {
    # LLM через Ollama
    "OLLAMA_BASE_URL": env("OLLAMA_BASE_URL", "https://ollama.com"),
    "OLLAMA_MODEL": env("OLLAMA_MODEL", "qwen2.5:7b"),
    "OLLAMA_TIMEOUT": int(env("OLLAMA_TIMEOUT", 60)),   # секунд на один запрос
    "OLLAMA_TEMPERATURE": 0.0,                          # детерминизм: воспроизводимость результатов
    "OLLAMA_SEED": 42,
    "OLLAMA_API_KEY": env("OLLAMA_API_KEY", ""),

    # Пороги уверенности:
    #   >= HIGH   -> значение принимается автоматически (зелёный бейдж)
    #   >= LOW    -> сомнительное, уходит на проверку (жёлтый)
    #   <  LOW    -> считается неизвестным / на ручную проверку (красный)
    "CONFIDENCE_HIGH": float(env("CONFIDENCE_HIGH", 0.85)),
    "CONFIDENCE_LOW": float(env("CONFIDENCE_LOW", 0.60)),

    # Гибрид: LLM вызывается только для атрибутов, которые не закрыл Regex
    "USE_LLM": env_bool("EXTRACTOR_USE_LLM", True),

    # Пакетная обработка
    "BATCH_MAX_ROWS": int(env("BATCH_MAX_ROWS", 5000)),
}


# --------------------------------------------------------------------------
# Безопасность в продакшене
# --------------------------------------------------------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True


# --------------------------------------------------------------------------
# Логирование
# --------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        # Отдельный логгер для алгоритма: видно, где сработал Regex, а где LLM
        "extractor": {
            "handlers": ["console"],
            "level": env("EXTRACTOR_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}