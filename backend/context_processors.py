"""Данные, доступные во всех шаблонах: навигация, пользователь, пороги уверенности."""
from . import app_settings

# icon: path для SVG 24x24 (stroke)
NAV = [
    {"name": "index", "label": "Главная", "icon": "M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"},
    {"name": "process", "label": "Обработка товаров", "icon": "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"},
    {"name": "review", "label": "Результаты", "icon": "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"},
    {"name": "evaluation", "label": "Аналитика", "icon": "M3 3v18h18M7 15l4-4 3 3 5-6"},
    {"name": "eda", "label": "EDA", "icon": "M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16zM21 21l-4.3-4.3"},
    {"name": "dictionaries", "label": "Справочники", "icon": "M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5zM4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"},
    {"name": "settings", "label": "Настройки", "icon": "M4 6h10M18 6h2M4 12h2M10 12h10M4 18h12M14 4v4M8 10v4M16 16v4"},
]


def site(request):
    cfg = app_settings.load()
    return {
        "nav": NAV,
        "user_name": "Электрочанган",
        "user_first_name": "Электрочанган",
        "user_initials": "ЭЧ",
        "user_role": "Команда",
        "confidence": {
            "high": cfg["confidence_high"],
            "low": cfg["confidence_low"],
        },
    }