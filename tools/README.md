# Runbook — Täglicher Arbeitstag (Vera)

> Das hier ist der dokumentierte Tagesablauf, den die geplante Aufgabe referenziert. Jede frische Session arbeitet ihn von oben nach unten ab. Alle Skripte laufen aus dem Repo-Root: `python3 tools/<skript>.py`.

## 0 · Kontext laden (immer zuerst)

Lesen: `AGENT_PROFILE.md` → `CLAUDE.md` → `career/preferences.md` (Scoring-Rubrik v2 + KO-Kriterien!) → `notes/entscheidungen.md` → `notes/journal.md` (letzte Einträge) → `notes/feedback.md` → `jobs/jobs.yaml` (Pipeline-Stand).

## 1 · Quellen ziehen

```
python3 tools/quellen_ba.py            # Arbeitsagentur-API (Query-Set unten), schreibt jobs/rohdaten/
python3 tools/quellen_arbeitnow.py     # Arbeitnow-Board
python3 tools/quellen_ats.py           # Watchlist-Karriere-Feeds (Greenhouse/Personio/…)
python3 tools/quellen_ats.py --probe   # 1×/Woche: unbekannte ATS-Slugs testen, watchlist.yaml aktualisieren
```

Die Skripte deduplizieren gegen `jobs/rohdaten/gesehen.yaml` und geben NUR NEUES kompakt aus. Zusätzlich **Websuche-Sweeps** (Agent, kein Skript — Funde immer auf der Firmen-Karriereseite verifizieren, AGB-Regel beachten):

- `"Head of AI" Jobs Deutschland` · `"AI Lead" OR "KI-Leiter" Stellenangebot` · `"Leiter Digitalisierung und KI"` · `"AI Product Manager" Deutschland` · `"VP AI" OR "Director AI" Germany` — jeweils auf die letzten Tage eingegrenzt.

## 2 · Triage & Scoring (Kopfarbeit — Regeln in career/preferences.md)

1. **KO-Filter zuerst:** Sperrliste (gesamte thyssenkrupp-Gruppe!), Beratung unterhalb PM-Einstieg, sicher < 100k Gesamtpaket, reine Koordination ohne Mandat, Pampa ohne Ausgleich.
2. Für Plausible: **Volltext archivieren** → `jobs/archiv/<id>/posting.md` — mit Meta-Kopf inkl. **Arbeitsort/Adresse aus den Quelldaten**. Anzeigen verschwinden — Volltext ist Pflicht, BEVOR bewertet wird. Vor Mappen-Fertigstellung: Firmensitz/Adresse extern verifizieren (Impressum/Register) — Lektor-Learning vom 27.07.
3. Score nach Rubrik v2 (Gewichte in preferences.md), 2–3 Sätze Begründung, **Konfidenz** (hoch/mittel/niedrig + warum). Eintrag in `jobs/jobs.yaml` (Schema: Kopfkommentar dort).
4. Kurz-Recherche pro ernstem Kandidaten: Firmen-Gesundheit, Kultur-Signale (kununu-Muster, Anzeigen-Sprache), Gehaltsindizien, Stadt-Kosten.

## 3 · Mappen bauen (Score ≥ 7,5, keine offene KO-Frage)

Pro Empfehlung `mappen/<id>/`: `analyse.md` (Warum-passt-es · Gehaltseinschätzung · Risiken · Diskretions-Hinweise) · `anschreiben.md` (Sprache der Anzeige; Deutsch: Du-Präferenz laut style.md) · `cv.md` (Variante des Master-CV `career/cv/cv-master.md`, auf die Stelle zugespitzt) · PDFs: HTML aus `tools/templates/` füllen → `bash tools/render_pdf.sh <html> <pdf>` (prüft 1-Seitigkeit automatisch).

**Pflicht: Lektor-Prüfung** (Subagent nach `.claude/agents/lektor.md`) vor Fertigstellung. Auflagen einarbeiten. Fakten-Lücken als `[KLÄREN: …]` stehen lassen — nie raten.

## 4 · Pipeline pflegen

`jobs/jobs.yaml` Status aktualisieren; bei `gesendet` ≥ 12 Tage ohne Reaktion: Follow-up-Entwurf in `mappen/<id>/followup.md` (NICHT senden — nichts verlässt das Haus). Fristen aus Anzeigen im Blick behalten.

## 5 · Übersicht & Abschluss

```
python3 tools/uebersicht.py            # generiert UEBERSICHT.md + dashboard/index.html aus jobs.yaml
python3 tools/artifact_build.py        # generiert dashboard/artifact.html (interaktives Cockpit)
```

Dann das Cockpit-Artifact auf **dieselbe URL** republishen (URL + Regeln: `notes/entscheidungen.md`, D13). Steht das Artifact-Tool in der Session nicht zur Verfügung: `artifact.html` trotzdem committen — die nächste interaktive Session republisht.

Dann: Journal-Eintrag (3–5 Zeilen) → committen, pushen (Branch gemäß Session-Vorgabe) → Statusnachricht an Moritz, beginnend mit „[B]": 3 Sätze — was ist neu, was steht aus, was brauche ich von ihm.

## Unverhandelbar (Kurzfassung, Details in CLAUDE.md)

Fakten-Gate (nur career/-Belegtes) · Nichts verlässt das Haus · kein Scraping von LinkedIn/Xing/StepStone, keine Login-Simulation, kein Bot-Schutz-Umgehen · Sperrliste = ganze thyssenkrupp-Gruppe · Diskretion (keine E-Mail-Benachrichtigungen an Firmenadresse) · mit Moritz Deutsch.
