#!/usr/bin/env python3
"""Arbeitnow-Job-Board (freie API, deutschlandfokussiert) — KI-relevante Rollen herausfiltern."""
import html
import re
import sys

from qlib import Gesehen, ROHDATEN, get, heute, save_yaml, sperrliste_treffer

API = "https://www.arbeitnow.com/api/job-board-api"

TITEL_MUSTER = re.compile(
    r"\b(ai|artificial intelligence|k(ü|ue)nstliche intelligenz|\bki\b|machine learning|\bml\b|llm|gen\s?ai|"
    r"data science|head of data|chief ai|digitalisierung)\b", re.I)


def main():
    gesehen, neu, seite = Gesehen(), [], API
    for _ in range(6):
        try:
            r = get(seite)
            r.raise_for_status()
            j = r.json()
        except Exception as e:
            print(f"WARN: {e}", file=sys.stderr)
            break
        for it in j.get("data", []):
            titel = it.get("title", "")
            if not TITEL_MUSTER.search(titel):
                continue
            slug, firma = it.get("slug"), it.get("company_name", "")
            eintrag = {
                "slug": slug, "titel": titel, "firma": firma,
                "ort": it.get("location"), "remote": it.get("remote"),
                "tags": it.get("tags"), "url": it.get("url"),
                "beschreibung": html.unescape(it.get("description", ""))[:20000],
            }
            if sperrliste_treffer(firma):
                eintrag["SPERRLISTE"] = True
            if gesehen.ist_neu("arbeitnow", slug, f"{titel} @ {firma}"):
                neu.append(eintrag)
        seite = (j.get("links") or {}).get("next")
        if not seite:
            break

    gesehen.save()
    if neu:
        save_yaml(ROHDATEN / f"arbeitnow_{heute()}.yaml", {"quelle": "arbeitnow", "datum": heute(), "neu": neu})
    print(f"Arbeitnow: {len(neu)} NEUE KI-relevante Treffer")
    for e in neu:
        flag = " ⛔SPERRLISTE" if e.get("SPERRLISTE") else ""
        print(f"  NEU: {e['titel']} | {e['firma']} | {e['ort']}{flag}")


if __name__ == "__main__":
    main()
