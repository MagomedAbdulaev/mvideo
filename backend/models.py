from django.db import models


class Product(models.Model):
    """Карточка товара. Исходный текст хранится как есть и не меняется."""
    external_id = models.CharField("ID во внешней системе", max_length=100, blank=True, db_index=True)
    category = models.CharField("Категория", max_length=100, blank=True, db_index=True)
    title = models.TextField("Заголовок", blank=True)
    description = models.TextField("Описание", blank=True)
    seller_attrs = models.TextField("Атрибуты продавца", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title[:60] or f"Товар {self.pk}"


class Extraction(models.Model):
    """Один извлечённый атрибут карточки."""
    STATUS_CHOICES = [
        ("ok", "ОК"),
        ("review", "Требует проверки"),
        ("conflict", "Конфликт"),
        ("unknown", "Неизвестно"),
        ("fixed", "Исправлено"),
    ]
    METHOD_CHOICES = [("regex", "Regex"), ("llm", "LLM"), ("hybrid", "Гибрид"), ("manual", "Вручную")]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="extractions")
    attribute = models.CharField("Атрибут", max_length=100, db_index=True)
    raw_value = models.CharField("Исходное значение", max_length=500, blank=True)
    value = models.CharField("Нормализованное значение", max_length=500, blank=True)
    auto_value = models.CharField("Значение алгоритма до ручной правки", max_length=500, blank=True)
    confidence = models.FloatField("Уверенность", default=0.0)
    method = models.CharField("Способ", max_length=10, choices=METHOD_CHOICES, default="regex")
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default="review", db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["product", "attribute"], name="uniq_product_attribute")]
        ordering = ["id"]

    def __str__(self):
        return f"{self.attribute}: {self.value or '—'}"