"""Fetch UppaTop / company IP export for scoreboard (CSV or JSON URL)."""

from __future__ import annotations

import csv
import io
import json
import time
from typing import Any

import requests

_CACHE: dict[str, Any] = {"t": 0.0, "columns": [], "rows": [], "err": None}
TTL_SECONDS = 300


def _parse_json(text: str) -> list[dict] | None:
    data = json.loads(text)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return [dict(r) for r in data]
    if isinstance(data, dict):
        for key in ("rows", "data", "results", "report", "items", "records"):
            inner = data.get(key)
            if isinstance(inner, list) and inner and isinstance(inner[0], dict):
                return [dict(r) for r in inner]
        if all(not isinstance(v, (list, dict)) for v in data.values()):
            return [dict(data)]
    return None


def _parse_csv(text: str) -> list[dict]:
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except csv.Error:
        dialect = "excel"
    f = io.StringIO(text)
    reader = csv.DictReader(f, dialect=dialect)
    return [dict(row) for row in reader if any(v and str(v).strip() for v in row.values())]


def _normalize_rows(rows: list[dict], max_rows: int = 150) -> tuple[list[str], list[dict]]:
    if not rows:
        return [], []
    rows = rows[:max_rows]
    keys: list[str] = []
    seen: set[str] = set()
    for r in rows:
        for k in r:
            if k is None:
                continue
            ks = str(k).strip()
            if ks and ks not in seen:
                seen.add(ks)
                keys.append(ks)
    flat = [{k: (str(r.get(k, "") or "").strip()) for k in keys} for r in rows]
    return keys, flat


def load_uppa_export(url: str, bust_cache: bool = False) -> tuple[list[str], list[dict], str | None]:
    """
    GET the export URL; return (column_keys, rows, error_message).
    Rows are capped; values are strings for safe HTML display.
    """
    global _CACHE
    if not (url or "").strip():
        return [], [], None

    now = time.time()
    t0 = float(_CACHE.get("t") or 0)
    if not bust_cache and t0 > 0 and (now - t0) < TTL_SECONDS:
        if _CACHE.get("err"):
            return [], [], str(_CACHE["err"])
        return list(_CACHE.get("columns") or []), list(_CACHE.get("rows") or []), None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/csv,application/json,text/plain,*/*;q=0.8",
    }

    try:
        import config as _cfg

        token = (getattr(_cfg, "UPPA_IP_EXPORT_TOKEN", None) or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
    except Exception:
        pass

    try:
        r = requests.get(url.strip(), timeout=30, headers=headers)
        r.raise_for_status()
        text = r.text
        if not text or not text.strip():
            raise ValueError("Empty response")
        ct = (r.headers.get("Content-Type") or "").lower()
        rows: list[dict] | None = None
        try:
            if "json" in ct or text.lstrip().startswith(("{", "[")):
                rows = _parse_json(text)
        except json.JSONDecodeError:
            rows = None
        if rows is None:
            rows = _parse_csv(text)

        cols, flat = _normalize_rows(rows)
        _CACHE = {"t": now, "columns": cols, "rows": flat, "err": None}
        return cols, flat, None
    except Exception as e:
        msg = str(e)[:500]
        _CACHE = {"t": now, "columns": [], "rows": [], "err": msg}
        return [], [], msg
