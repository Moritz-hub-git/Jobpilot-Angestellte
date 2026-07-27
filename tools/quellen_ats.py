#!/usr/bin/env python3
"""Watchlist-Karriere-Feeds abfragen (offizielle öffentliche ATS-Endpunkte: Greenhouse, Lever,
Personio, SmartRecruiters, Recruitee, Ashby). --probe testet unbekannte Slugs und schreibt
Ergebnisse nach tools/ats_status.yaml (watchlist.yaml bleibt handkuratiert)."""
import argparse
import re
import sys

from qlib import ROOT, ROHDATEN, Gesehen, get, heute, load_yaml, save_yaml

STATUS_DATEI = ROOT / "tools" / "ats_status.yaml"

RELEVANZ = re.compile(
    r"\b(ai|artificial|k(ü|ue)nstliche|\bki\b|machine learning|\bml\b|llm|gen\s?ai|data|digital|"
    r"product manager|product lead|head of|lead|leiter|director|vp|principal|transformation|strategy)\b", re.I)


def hole(typ, slug):
    """Liefert (jobs, None) oder (None, fehler). jobs: Liste {titel, ort, url, id}."""
    try:
        if typ == "greenhouse":
            r = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            return [{"id": str(j["id"]), "titel": j.get("title"),
                     "ort": (j.get("location") or {}).get("name"), "url": j.get("absolute_url")}
                    for j in r.json().get("jobs", [])], None
        if typ == "lever":
            r = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            return [{"id": j.get("id"), "titel": j.get("text"),
                     "ort": (j.get("categories") or {}).get("location"), "url": j.get("hostedUrl")}
                    for j in r.json()], None
        if typ == "personio":
            r = get(f"https://{slug}.jobs.personio.de/search.json")
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            return [{"id": str(j.get("id")), "titel": j.get("name"), "ort": j.get("office"),
                     "url": f"https://{slug}.jobs.personio.de/job/{j.get('id')}"}
                    for j in r.json()], None
        if typ == "smartrecruiters":
            r = get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100")
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            return [{"id": j.get("id"), "titel": j.get("name"),
                     "ort": ((j.get("location") or {}).get("city")),
                     "url": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}"}
                    for j in r.json().get("content", [])], None
        if typ == "recruitee":
            r = get(f"https://{slug}.recruitee.com/api/offers/")
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            return [{"id": str(j.get("id")), "titel": j.get("title"), "ort": j.get("location"),
                     "url": j.get("careers_url")}
                    for j in r.json().get("offers", [])], None
        if typ == "ashby":
            r = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
            if r.status_code != 200:
                return None, f"HTTP {r.status_code}"
            return [{"id": j.get("id"), "titel": j.get("title"), "ort": j.get("location"),
                     "url": j.get("jobUrl") or j.get("applyUrl")}
                    for j in r.json().get("jobs", [])], None
    except Exception as e:
        return None, str(e)[:80]
    return None, "typ unbekannt"


def slug_varianten(name, slug):
    n = re.sub(r"[^a-z0-9]+", "", (name or "").lower())
    n2 = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    kandidaten = [slug, n, n2, n2.replace("-", "")]
    return [k for i, k in enumerate(kandidaten) if k and k not in kandidaten[:i]]


def probe_firma(name, slug):
    """Alle ATS-Typen × Slug-Varianten durchtesten; erster Treffer gewinnt."""
    for t in ("greenhouse", "personio", "ashby", "lever", "smartrecruiters", "recruitee"):
        for s in slug_varianten(name, slug):
            jobs, _ = hole(t, s)
            if jobs:
                return {"typ": t, "slug": s, "verifiziert": heute(), "jobs_beim_test": len(jobs)}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="unbekannte/vermutete Slugs über alle ATS-Typen testen")
    args = ap.parse_args()

    wl = load_yaml(ROOT / "watchlist.yaml", {})
    status = load_yaml(STATUS_DATEI, {})
    gesehen, neu = Gesehen(), []
    firmen = wl.get("firmen", [])

    if args.probe:
        from concurrent.futures import ThreadPoolExecutor
        kandidaten = [f for f in firmen
                      if not (status.get(f["name"]) or {}).get("typ")
                      and (f.get("ats") or {}).get("status") in ("fehlt", "vermutet")]
        with ThreadPoolExecutor(max_workers=10) as ex:
            ergebnisse = ex.map(lambda f: (f["name"], probe_firma(f["name"], (f.get("ats") or {}).get("slug"))), kandidaten)
        for name, res in ergebnisse:
            if res:
                status[name] = res
                print(f"PROBE ✓ {name}: {res['typ']}/{res['slug']} ({res['jobs_beim_test']} Jobs)")
            else:
                status.setdefault(name, {})["letzte_probe"] = heute()

    for f in firmen:
        name, ats = f.get("name"), f.get("ats") or {}
        eintrag = status.get(name) or {}
        if eintrag.get("typ") == "keins":  # bereinigter Fehltreffer / kein öffentlicher Feed
            continue
        if eintrag.get("typ"):  # verifiziert (heute oder früher)
            typ, slug = eintrag["typ"], eintrag["slug"]
        elif ats.get("status") == "bestaetigt" and ats.get("typ") not in (None, "unbekannt", "keins"):
            typ, slug = ats["typ"], ats["slug"]
        else:
            continue

        jobs, err = hole(typ, slug)
        if jobs is None:
            print(f"WARN {name} ({typ}/{slug}): {err}", file=sys.stderr)
            continue
        for j in jobs:
            if not j.get("titel") or not RELEVANZ.search(j["titel"]):
                continue
            key = f"{typ}:{slug}:{j['id']}"
            if gesehen.ist_neu("ats", key, f"{j['titel']} @ {name}"):
                neu.append({"firma": name, "typ": typ, **j})

    gesehen.save()
    save_yaml(STATUS_DATEI, status)
    if neu:
        save_yaml(ROHDATEN / f"ats_{heute()}.yaml", {"quelle": "ats", "datum": heute(), "neu": neu})
    print(f"ATS-Watchlist: {len(neu)} NEUE relevante Treffer → jobs/rohdaten/ats_{heute()}.yaml")
    for e in neu[:60]:
        print(f"  NEU: {e['titel']} | {e['firma']} | {e.get('ort')}")
    if len(neu) > 60:
        print(f"  … und {len(neu) - 60} weitere (siehe YAML)")


if __name__ == "__main__":
    main()
