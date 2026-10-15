"""
Разведочный анализ данных (EDA): поля, пропуски, распределения.
Загруженный датасет лежит в data/dataset.csv|json, готовый отчёт в data/eda.json.
Для следующих модулей:  eda.dataset_path(), eda.read_dataset(path)
"""
import io
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings

TOP = 15                      # сколько значений показывать в топе
RARE = 10                     # категория с меньшим числом строк считается редкой
GUESS = ("категор", "category", "type", "тип")


def _dir() -> Path:
    return Path(settings.DATA_DIR)


def dataset_path():
    return next(iter(sorted(_dir().glob("dataset.*"))), None)


def _r(x) -> float:
    return round(float(x), 2)


def _missing(s: pd.Series) -> pd.Series:
    """Пропуск: NaN или пустая строка."""
    return s.isna() | s.map(lambda x: isinstance(x, str) and not x.strip())


def read_dataset(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    if path.suffix == ".json":
        text = raw.decode("utf-8-sig", errors="replace")
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):                      # {"items": [...]} -> берём первый список
                obj = next((v for v in obj.values() if isinstance(v, list)), [obj])
            df = pd.json_normalize(obj)                    # вложенные словари становятся колонками a.b
        except ValueError:
            try:
                df = pd.read_json(io.StringIO(text), lines=True)   # JSON Lines
            except ValueError:
                raise ValueError("Не удалось прочитать JSON")
    else:
        df = None
        for enc in ("utf-8-sig", "cp1251"):
            try:
                df = pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding=enc)
                break
            except UnicodeDecodeError:
                continue
            except Exception:
                raise ValueError("Не удалось прочитать CSV")
        if df is None:
            raise ValueError("Не удалось определить кодировку CSV")
    df.columns = [str(c) for c in df.columns]
    return df


def column_report(name, s: pd.Series) -> dict:
    n = len(s)
    miss = _missing(s)
    m = int(miss.sum())
    sv = s[~miss]
    info = {"name": str(name), "missing": m,
            "missing_pct": round(100 * m / n, 1) if n else 0.0,
            "missing_w": int(round(100 * m / n)) if n else 0}

    if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
        v = sv.astype(float)
        v = v[np.isfinite(v)]
        info.update(kind="number", unique=int(v.nunique()))
        if len(v):
            counts, edges = np.histogram(v, bins=10)
            mx = int(counts.max()) or 1
            info["stats"] = {"min": _r(v.min()), "max": _r(v.max()), "mean": _r(v.mean()), "median": _r(v.median())}
            info["hist"] = [{"label": f"{_r(edges[i])}–{_r(edges[i + 1])}", "count": int(c),
                             "pct": int(round(100 * c / mx))} for i, c in enumerate(counts)]
        return info

    st = sv.astype(str)
    uniq = int(st.nunique())
    lens = st.str.len()
    is_text = bool(len(st)) and (lens.mean() > 40 or (uniq / len(st) > 0.5 and uniq > 50))
    info.update(kind="text" if is_text else "category", unique=uniq)
    if len(st):
        info["len"] = {"mean": _r(lens.mean()), "median": _r(lens.median()), "max": int(lens.max())}
        if not is_text:
            vc = st.value_counts().head(TOP)
            mx = int(vc.iloc[0])
            info["top"] = [{"value": str(k)[:80], "count": int(c), "pct": int(round(100 * c / mx))}
                           for k, c in vc.items()]
    return info


def analyze(df: pd.DataFrame, filename: str) -> dict:
    n, k = len(df), len(df.columns)
    cols = [column_report(c, df[c]) for c in df.columns]
    cells = n * k
    missing = sum(c["missing"] for c in cols)
    cat_cols = [c["name"] for c in cols if c["kind"] == "category"]
    guess = next((c for c in cat_cols if any(g in c.lower() for g in GUESS)), "")
    return {
        "filename": filename,
        "created": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "rows": n, "cols": k,
        "duplicates": int(df.astype(str).duplicated().sum()),
        "completeness": round(100 * (1 - missing / cells), 1) if cells else 0.0,
        "columns": cols,
        "category_cols": cat_cols,
        "category_guess": guess,
    }


def save_and_analyze(file) -> dict:
    ext = Path(file.name).suffix.lower()
    if ext not in (".csv", ".json"):
        raise ValueError("Поддерживаются файлы CSV и JSON")
    d = _dir()
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("dataset.*"):
        old.unlink()
    path = d / f"dataset{ext}"
    with open(path, "wb") as out:
        for chunk in file.chunks():
            out.write(chunk)
    try:
        df = read_dataset(path)
        if df.empty:
            raise ValueError("В файле нет данных")
    except ValueError:
        path.unlink(missing_ok=True)
        raise
    report = analyze(df, file.name)
    (d / "eda.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    return report


def load_report():
    try:
        return json.loads((_dir() / "eda.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return None


def by_category(col: str) -> dict:
    """Размер категорий и средняя доля пропусков по ним: видно, где качество хуже."""
    path = dataset_path()
    if path is None:
        raise ValueError("Датасет не загружен")
    df = read_dataset(path)
    if col not in df.columns:
        raise ValueError("Такого поля нет в датасете")
    key = df[col].astype(str).replace({"nan": "(пусто)"})
    miss = pd.DataFrame({c: _missing(df[c]) for c in df.columns if c != col})
    avg = (miss.mean(axis=1).groupby(key).mean() * 100) if not miss.empty else pd.Series(0.0, index=key.unique())
    vc = key.value_counts()
    mx = int(vc.iloc[0])

    def row(name, tail):
        return {"name": str(name)[:80], "rows": int(vc[name]), "pct": max(1, int(round(100 * vc[name] / mx))),
                "missing": round(float(avg.get(name, 0.0)), 1), "tail": tail}

    head = [row(n, False) for n in vc.index[:10]]
    tail = [row(n, True) for n in vc.index[10:][-5:][::-1]]
    return {"column": col, "total": int(len(vc)), "rare": int((vc < RARE).sum()),
            "rare_threshold": RARE, "rows": head + tail}