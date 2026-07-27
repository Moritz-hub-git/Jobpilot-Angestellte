"""Gemeinsame Helfer für die Quellen-Skripte."""
import datetime
import pathlib

import requests
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROHDATEN = ROOT / "jobs" / "rohdaten"
GESEHEN = ROHDATEN / "gesehen.yaml"

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) JobRecherche/1.0 (privat, kontakt: me@moritz-schumacher.com)"}


def heute() -> str:
    return datetime.date.today().isoformat()


def load_yaml(path, default):
    p = pathlib.Path(path)
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f) or default
    return default


def save_yaml(path, data):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def get(url, timeout=25, **kw):
    kw.setdefault("headers", {}).update(UA)
    return requests.get(url, timeout=timeout, **kw)


class Gesehen:
    """Registry aller je gesehenen Quell-IDs → nur echtes Delta wird gemeldet."""

    def __init__(self):
        self.data = load_yaml(GESEHEN, {})

    def ist_neu(self, quelle: str, key: str, notiz: str = "") -> bool:
        bucket = self.data.setdefault(quelle, {})
        if key in bucket:
            return False
        bucket[key] = {"erstgesehen": heute(), "notiz": notiz[:120]}
        return True

    def save(self):
        save_yaml(GESEHEN, self.data)


def sperrliste_treffer(firma: str) -> bool:
    return "thyssenkrupp" in (firma or "").lower()
