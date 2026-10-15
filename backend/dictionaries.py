"""
Справочники: категории, их атрибуты и допустимые значения с синонимами.
Хранятся в data/dictionaries.json. Пока файла нет, отдаётся пример (seed).
В алгоритме читать так:  from backend import dictionaries;  data = dictionaries.load()
Точный перечень обязательных полей придёт вместе с датасетом, тогда seed можно заменить.
"""
import json
import secrets

from django.conf import settings

TYPES = {"enum", "number", "text"}


def _path():
    return settings.DATA_DIR / "dictionaries.json"


def _attr(key, name, type_, unit="", required=True, values=None):
    return {"key": key, "name": name, "type": type_, "unit": unit, "required": required, "values": values or []}


COLORS = [
    {"value": "чёрный", "synonyms": ["черный", "black"]},
    {"value": "белый", "synonyms": ["white"]},
    {"value": "красный", "synonyms": ["алый", "red"]},
    {"value": "синий", "synonyms": ["blue"]},
    {"value": "серый", "synonyms": ["grey", "gray"]},
]


def seed():
    phone_brands = [
        {"value": "Samsung", "synonyms": ["самсунг"]},
        {"value": "Apple", "synonyms": ["эпл"]},
        {"value": "Xiaomi", "synonyms": ["сяоми"]},
        {"value": "Honor", "synonyms": ["хонор"]},
    ]
    laptop_brands = [
        {"value": "ASUS", "synonyms": ["асус"]},
        {"value": "Lenovo", "synonyms": ["леново"]},
        {"value": "HP", "synonyms": ["хп"]},
        {"value": "Apple", "synonyms": ["эпл"]},
    ]
    return {"categories": [
        {"id": "smartphones", "name": "Смартфоны", "attributes": [
            _attr("brand", "Бренд", "enum", values=phone_brands),
            _attr("model", "Модель", "text"),
            _attr("storage", "Объём памяти", "number", "ГБ"),
            _attr("screen", "Диагональ экрана", "number", "дюйм"),
            _attr("battery", "Ёмкость батареи", "number", "мА·ч"),
            _attr("color", "Цвет", "enum", values=COLORS),
        ]},
        {"id": "laptops", "name": "Ноутбуки", "attributes": [
            _attr("brand", "Бренд", "enum", values=laptop_brands),
            _attr("cpu", "Процессор", "text"),
            _attr("ram", "Объём оперативной памяти", "number", "ГБ"),
            _attr("storage", "Накопитель", "number", "ГБ"),
            _attr("screen", "Диагональ", "number", "дюйм"),
            _attr("color", "Цвет", "enum", values=COLORS),
        ]},
    ]}


def load() -> dict:
    try:
        return json.loads(_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return seed()


def _s(x, n=100):
    return str(x if x is not None else "").strip()[:n]


def validate(data) -> dict:
    """Проверяет и очищает структуру. При ошибке бросает ValueError с понятным текстом."""
    try:
        if not isinstance(data, dict) or not isinstance(data.get("categories"), list):
            raise ValueError("Неверный формат данных")
        cats, seen_c = [], set()
        for c in data["categories"]:
            name = _s(c.get("name"))
            if not name:
                raise ValueError("У категории пустое название")
            if name.lower() in seen_c:
                raise ValueError(f"Категория «{name}» уже есть")
            seen_c.add(name.lower())
            attrs, seen_a = [], set()
            for a in c.get("attributes", []):
                an = _s(a.get("name"))
                if not an:
                    raise ValueError(f"В категории «{name}» есть атрибут без названия")
                if an.lower() in seen_a:
                    raise ValueError(f"Атрибут «{an}» повторяется в категории «{name}»")
                seen_a.add(an.lower())
                t = a.get("type")
                if t not in TYPES:
                    raise ValueError(f"Неизвестный тип у атрибута «{an}»")
                values = []
                if t == "enum":
                    for v in a.get("values", []):
                        val = _s(v.get("value"))
                        if val:
                            syn = [s for s in (_s(x) for x in v.get("synonyms", [])) if s]
                            values.append({"value": val, "synonyms": syn})
                attrs.append({"key": _s(a.get("key"), 40) or "a" + secrets.token_hex(4), "name": an, "type": t,
                              "unit": _s(a.get("unit"), 20) if t == "number" else "",
                              "required": bool(a.get("required")), "values": values})
            cats.append({"id": _s(c.get("id"), 40) or "c" + secrets.token_hex(4), "name": name, "attributes": attrs})
        return {"categories": cats}
    except (AttributeError, TypeError):
        raise ValueError("Неверный формат данных")


def save(data: dict) -> dict:
    clean = validate(data)
    _path().parent.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    return clean