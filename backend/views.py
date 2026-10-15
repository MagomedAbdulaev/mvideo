import json
import urllib.request

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .context_processors import NAV
from .forms import SettingsForm
from django.conf import settings

from django.views.decorators.http import require_GET, require_POST
from . import app_settings, dictionaries, eda


def index(request):
    # Заглушки: позже заменим данными из БД и extractor
    ctx = {
        "stats": [
            {"label": "Обработано товаров", "value": "12 548", "delta": "+12%", "hint": "к прошлой неделе", "up": True, "good": True},
            {"label": "Точность (F1)", "value": "0.892", "delta": "+6%", "hint": "", "up": True, "good": True},
            {"label": "Покрытие атрибутов", "value": "87.4%", "delta": "+4%", "hint": "", "up": True, "good": True},
            {"label": "Ошибки (на проверку)", "value": "532", "delta": "-18%", "hint": "", "up": False, "good": True},
        ],
        "chart": {
            "labels": ["7 окт", "8 окт", "9 окт", "10 окт", "11 окт", "12 окт", "13 окт"],
            "processed": [4500, 7000, 6500, 9000, 8200, 10500, 12000],
            "review": [3800, 5200, 4600, 6400, 5400, 7100, 8300],
        },
        "tasks": [
            {"name": "Смартфоны", "count": "1 248", "status": "done", "label": "Завершено"},
            {"name": "Ноутбуки", "count": "987", "status": "running", "label": "В процессе"},
            {"name": "Наушники", "count": "542", "status": "done", "label": "Завершено"},
            {"name": "Телевизоры", "count": "843", "status": "queued", "label": "Ожидание"},
        ],
    }
    return render(request, "index.html", ctx)


def stub(request):
    """Временная страница для разделов, до которых ещё не дошли."""
    name = request.resolver_match.url_name
    title = next((i["label"] for i in NAV if i["name"] == name), "Раздел")
    return render(request, "stub.html", {"title": title})


def settings_page(request):
    if request.method == "POST":
        if "reset" in request.POST:
            app_settings.reset()
            messages.success(request, "Настройки сброшены к значениям по умолчанию")
            return redirect("settings")
        form = SettingsForm(request.POST)
        if form.is_valid():
            app_settings.save(form.cleaned_data)
            messages.success(request, "Настройки сохранены")
            return redirect("settings")
        messages.error(request, "Настройки не сохранены: проверьте выделенные поля")
    else:
        form = SettingsForm(initial=app_settings.load())
    return render(request, "settings.html", {"form": form, "defaults": app_settings.defaults()})


@require_GET
def ollama_check(request):
    """Проверяет доступность Ollama и возвращает список установленных моделей."""
    url = (request.GET.get("url") or app_settings.load()["ollama_base_url"]).rstrip("/")
    if not url.startswith(("http://", "https://")):
        return JsonResponse({"ok": False, "error": "Некорректный адрес"}, status=400)
    key = settings.EXTRACTOR.get("OLLAMA_API_KEY", "")
    is_cloud = url.startswith("https://ollama.com")
    req = urllib.request.Request(url + "/api/tags")
    if key and is_cloud:  # ключ отправляем только в облако Ollama
        req.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.load(resp)
        return JsonResponse({"ok": True, "models": [m["name"] for m in data.get("models", [])],
                             "cloud": is_cloud, "has_key": bool(key)})
    except Exception:
        return JsonResponse({"ok": False, "error": "Не удалось подключиться к Ollama"})


def dictionaries_page(request):
    return render(request, "dictionaries.html", {"data": dictionaries.load()})


@require_POST
def dictionaries_save(request):
    try:
        dictionaries.save(json.loads(request.body))
    except ValueError as e:        # сюда попадает и json.JSONDecodeError
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    return JsonResponse({"ok": True})

def eda_page(request):
    if request.method == "POST":
        f = request.FILES.get("dataset")
        if not f:
            messages.error(request, "Выберите файл")
        else:
            try:
                eda.save_and_analyze(f)
                messages.success(request, "Файл загружен, анализ готов")
            except ValueError as e:
                messages.error(request, str(e))
        return redirect("eda")
    return render(request, "eda.html", {"report": eda.load_report()})


@require_GET
def eda_by_category(request):
    try:
        return JsonResponse({"ok": True, "data": eda.by_category(request.GET.get("col", ""))})
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
