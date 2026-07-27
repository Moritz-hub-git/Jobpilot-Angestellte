#!/usr/bin/env python3
"""Arbeitsagentur-Jobsuche (offizielle API, bund.dev-dokumentiert): KI-Führungs- und Produktrollen."""
import argparse
import base64
import re
import sys

from qlib import Gesehen, ROHDATEN, get, heute, save_yaml, sperrliste_treffer

RELEVANT = re.compile(r"(\bai\b|\bki\b|artificial|k(ü|ue)nstlich|machine learning|\bml\b|llm|gen\s?ai|data|digital)", re.I)

API = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
KEY = {"X-API-Key": "jobboerse-jobsuche"}

QUERIES = [
    "Head of AI",
    "Head of Artificial Intelligence",
    "AI Lead",
    "Leiter Künstliche Intelligenz",
    "Leiter Digitalisierung KI",
    "AI Product Manager",
    "Product Manager KI",
    "AI Transformation Manager",
    "Director Artificial Intelligence",
    "VP Artificial Intelligence",
]


def suche(was: str, tage: int):
    items, page = [], 1
    while page <= 3:
        r = get(f"{API}/pc/v4/jobs", headers=dict(KEY),
                params={"was": was, "size": 100, "page": page, "veroeffentlichtseit": tage, "angebotsart": 1})
        r.raise_for_status()
        batch = r.json().get("stellenangebote", []) or []
        items += batch
        if len(batch) < 100:
            break
        page += 1
    return items


def detail(refnr: str):
    """Volltext-Detail; Endpunkt-Varianten durchprobieren."""
    b64 = base64.urlsafe_b64encode(refnr.encode()).decode().rstrip("=")
    for pfad in (f"{API}/pc/v4/jobdetails/{b64}",):
        try:
            r = get(pfad, headers=dict(KEY))
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tage", type=int, default=3, help="veroeffentlichtseit (Tage)")
    ap.add_argument("--volltext", action="store_true", help="Details für neue Treffer laden")
    args = ap.parse_args()

    gesehen, alle, neu = Gesehen(), {}, []
    for q in QUERIES:
        try:
            for it in suche(q, args.tage):
                ref = it.get("refnr")
                if ref and ref not in alle:
                    it["_query"] = q
                    alle[ref] = it
        except Exception as e:
            print(f"WARN Query '{q}': {e}", file=sys.stderr)

    for ref, it in alle.items():
        firma = it.get("arbeitgeber", "")
        eintrag = {
            "refnr": ref,
            "titel": it.get("titel") or it.get("beruf"),
            "firma": firma,
            "ort": (it.get("arbeitsort") or {}).get("ort"),
            "region": (it.get("arbeitsort") or {}).get("region"),
            "veroeffentlicht": it.get("aktuelleVeroeffentlichungsdatum"),
            "externeUrl": it.get("externeUrl"),
            "url": f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}",
            "query": it["_query"],
        }
        if sperrliste_treffer(firma):
            eintrag["SPERRLISTE"] = True
        if gesehen.ist_neu("ba", ref, f"{eintrag['titel']} @ {firma}"):
            if args.volltext and not eintrag.get("SPERRLISTE") and RELEVANT.search(eintrag.get("titel") or ""):
                d = detail(ref)
                if d:
                    eintrag["beschreibung"] = d.get("stellenbeschreibung")
                    eintrag["arbeitszeit"] = d.get("arbeitszeitmodelle")
                    eintrag["befristung"] = d.get("befristung")
            neu.append(eintrag)

    gesehen.save()
    if neu:
        save_yaml(ROHDATEN / f"ba_{heute()}.yaml", {"quelle": "ba", "datum": heute(), "neu": neu})
    print(f"BA: {len(alle)} Treffer gesamt, {len(neu)} NEU (Zeitraum {args.tage} Tage) → jobs/rohdaten/ba_{heute()}.yaml")
    for e in neu[:40]:
        flag = " ⛔SPERRLISTE" if e.get("SPERRLISTE") else ""
        print(f"  NEU: {e['titel']} | {e['firma']} | {e['ort']} | {e['refnr']}{flag}")
    if len(neu) > 40:
        print(f"  … und {len(neu) - 40} weitere (siehe YAML)")


if __name__ == "__main__":
    main()
