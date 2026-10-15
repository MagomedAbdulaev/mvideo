"""Демо-данные для проверки интерфейса: python manage.py seed_demo [--clear]"""
import random

from django.core.management.base import BaseCommand

from backend.models import Extraction, Product

COLORS = [("чёрный", "black"), ("белый", "white"), ("красный", "алый"), ("синий", "blue"), ("серый", "grey")]
PHONE_BRANDS = ["Samsung", "Apple", "Xiaomi", "Honor"]
LAPTOP_BRANDS = ["ASUS", "Lenovo", "HP", "Apple"]
CPUS = ["Intel Core i5-1235U", "Intel Core i7-13700H", "AMD Ryzen 5 5500U", "Apple M2"]


class Command(BaseCommand):
    help = "Создаёт демонстрационные карточки и результаты извлечения (не настоящие данные)"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="сначала удалить все карточки")

    def handle(self, *args, **opts):
        if opts["clear"]:
            Product.objects.all().delete()
        rnd = random.Random(42)
        for i in range(45):
            kind = rnd.choice(["Смартфоны", "Ноутбуки", "Смартфоны"])
            color, color_raw = rnd.choice(COLORS)
            if kind == "Смартфоны":
                brand, mem, diag = rnd.choice(PHONE_BRANDS), rnd.choice([128, 256, 512]), rnd.choice(["6,1", "6,7", "6,4"])
                title = f"Смартфон {brand} Model-{rnd.randint(10, 99)} {mem} ГБ {color_raw}"
                desc = (f"Смартфон {brand}. Дисплей {diag} дюйма, память {mem} ГБ, аккумулятор {rnd.choice([4500, 5000])} мАч. "
                        f"Цвет: {color_raw}. Гарантия 12 месяцев.")
                specs = [("Бренд", brand, brand), ("Объём памяти", f"{mem} ГБ", f"{mem} ГБ"),
                         ("Диагональ экрана", f"{diag} дюйма", f"{diag.replace(',', '.')} дюйм"),
                         ("Ёмкость батареи", "5000 мАч", "5000 мА·ч"), ("Цвет", color_raw, color)]
            else:
                brand, cpu = rnd.choice(LAPTOP_BRANDS), rnd.choice(CPUS)
                title = f"Ноутбук {brand} {rnd.choice(['Vivobook', 'IdeaPad', 'Pavilion'])} 15 {color_raw}"
                desc = f"Ноутбук {brand}, процессор {cpu}, ОЗУ {rnd.choice([8, 16])} ГБ, SSD 512 ГБ, экран 15,6 дюйма. Цвет {color_raw}."
                specs = [("Бренд", brand, brand), ("Процессор", cpu, cpu), ("Объём оперативной памяти", "16 ГБ", "16 ГБ"),
                         ("Диагональ", "15,6 дюйма", "15.6 дюйм"), ("Цвет", color_raw, color)]
            p = Product.objects.create(external_id=f"demo-{i}", category=kind, title=title, description=desc,
                                       seller_attrs=f"Бренд: {brand}\nГарантия: 12 мес.")
            for attr, raw, val in specs:
                roll = rnd.random()
                if roll < 0.60:
                    st, conf, method, raw_v, v = "ok", rnd.uniform(0.88, 0.99), "regex", raw, val
                elif roll < 0.76:
                    st, conf, method, raw_v, v = "review", rnd.uniform(0.5, 0.8), "llm", raw, val
                elif roll < 0.88:
                    other = rnd.choice(COLORS)[0] if attr == "Цвет" else val + " (?)"
                    st, conf, method, raw_v, v = "conflict", rnd.uniform(0.55, 0.75), "hybrid", raw, other
                else:
                    st, conf, method, raw_v, v = "unknown", 0.0, "hybrid", "", ""
                Extraction.objects.create(product=p, attribute=attr, raw_value=raw_v, value=v, auto_value=v,
                                          confidence=round(conf, 2), method=method, status=st)
        self.stdout.write(self.style.SUCCESS("Демо-данные созданы"))