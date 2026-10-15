import json

from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import dictionaries
from .models import Extraction, Product

PAGE_SIZE = 25
ATTENTION = ["unknown", "review", "conflict"]
TABS = [("attention", "Требуют внимания"), ("review", "Сомнительные"), ("conflict", "Конфликты"),
        ("unknown", "Неизвестные"), ("ok", "ОК"), ("fixed", "Исправленные"), ("all", "Все")]


def _options_map():
    """(категория, атрибут) -> допустимые значения из справочника, для подсказок при правке."""
    out = {}
    for c in dictionaries.load()["categories"]:
        for a in c["attributes"]:
            if a["type"] == "enum" and a["values"]:
                out[(c["name"].lower(), a["name"].lower())] = [v["value"] for v in a["values"]]
    return out


def results_page(request):
    tab = request.GET.get("tab", "attention")
    if tab not in dict(TABS):
        tab = "attention"
    category = request.GET.get("category", "")
    attribute = request.GET.get("attribute", "")
    q = request.GET.get("q", "").strip()

    counts = {r["status"]: r["n"] for r in Extraction.objects.values("status").annotate(n=Count("id"))}
    tab_counts = {k: counts.get(k, 0) for k in ("review", "conflict", "unknown", "ok", "fixed")}
    tab_counts["attention"] = sum(counts.get(s, 0) for s in ATTENTION)
    tab_counts["all"] = sum(counts.values())

    qs = Extraction.objects.select_related("product")
    if tab == "attention":
        qs = qs.filter(status__in=ATTENTION)
    elif tab != "all":
        qs = qs.filter(status=tab)
    if category:
        qs = qs.filter(product__category=category)
    if attribute:
        qs = qs.filter(attribute=attribute)
    if q:
        qs = qs.filter(Q(product__title__icontains=q) | Q(value__icontains=q) | Q(raw_value__icontains=q))
    qs = qs.order_by("confidence", "id") if tab in ("attention", "review", "conflict", "unknown") else qs.order_by("-id")

    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    opts = _options_map()
    for e in page:
        e.options = json.dumps(opts.get((e.product.category.lower(), e.attribute.lower()), []), ensure_ascii=False)

    params = request.GET.copy()
    params.pop("page", None)
    base_query = params.urlencode()

    def tab_url(key):
        p = request.GET.copy()
        p.pop("page", None)
        p["tab"] = key
        return "?" + p.urlencode()

    return render(request, "results.html", {
        "page": page, "tab": tab, "q": q, "category": category, "attribute": attribute,
        "tabs": [{"key": k, "label": l, "count": tab_counts[k], "url": tab_url(k)} for k, l in TABS],
        "categories": Product.objects.exclude(category="").values_list("category", flat=True).distinct().order_by("category"),
        "attributes": Extraction.objects.values_list("attribute", flat=True).distinct().order_by("attribute"),
        "base_query": base_query,
    })


@require_POST
def result_update(request, pk):
    """Подтвердить или исправить значение вручную."""
    e = get_object_or_404(Extraction, pk=pk)
    try:
        body = json.loads(request.body)
    except ValueError:
        return JsonResponse({"ok": False, "error": "Неверный запрос"}, status=400)

    action = body.get("action")
    if action == "confirm":
        if not e.value:
            return JsonResponse({"ok": False, "error": "Нельзя подтвердить пустое значение"}, status=400)
        e.status = "ok"
    elif action == "edit":
        value = str(body.get("value", "")).strip()[:500]
        if not value:
            return JsonResponse({"ok": False, "error": "Введите значение"}, status=400)
        if not e.auto_value:
            e.auto_value = e.value          # сохраняем ответ алгоритма: пригодится для обучения и правил
        e.value, e.status, e.method = value, "fixed", "manual"
    else:
        return JsonResponse({"ok": False, "error": "Неизвестное действие"}, status=400)

    e.reviewed_at = timezone.now()
    e.save()
    return JsonResponse({
        "ok": True, "status": e.status, "value": e.value,
        "status_badge": render_to_string("partials/status_badge.html", {"status": e.status}),
        "method_badge": render_to_string("partials/method_badge.html", {"method": e.method}),
    })