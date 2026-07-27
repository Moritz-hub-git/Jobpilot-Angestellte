# Entscheidungslog — Vera

> Zweck: Jede Session startet ohne Gedächtnis. Hier stehen die Architektur- und Prozess-Entscheidungen mit Begründung. Bei Widerspruch zwischen diesem Log und `CLAUDE.md`/`career/` gilt: CLAUDE.md (Regeln) > career/ (Fakten) > dieses Log (Arbeitsweise).

## 2026-07-27 — Gründungsentscheidungen (Tag 1, Freigabe durch Moritz liegt vor)

### D1 · Datenhaltung: `jobs/jobs.yaml` als einzige maschinenlesbare Wahrheit
YAML (pyyaml 6.0.1 verfügbar), weil menschenlesbar, kommentierbar, diff-freundlich. `UEBERSICHT.md` und `dashboard/index.html` werden ausschließlich per `tools/uebersicht.py` daraus generiert — nie von Hand editieren, sonst Drift.

### D2 · PDF-Erzeugung: HTML → Chromium headless
`/opt/pw-browsers/chromium --headless --print-to-pdf` mit `@page { size: A4 }`. Getestet, funktioniert. Wrapper: `tools/render_pdf.sh`. Fallback: LibreOffice (installiert). Einseitigkeit wird nach jedem Render geprüft (Seitenzahl-Check im Wrapper).

### D3 · Tägliche Aufgabe: 04:00 UTC, Benachrichtigung NUR Push, KEINE E-Mail
06:00 Berlin im Sommer (CEST), 05:00 im Winter. **E-Mail-Benachrichtigung bewusst deaktiviert:** Moritz' hinterlegte Adresse ist die Firmenadresse bei thyssenkrupp nucera — Jobsuche-Mails dorthin wären ein Diskretionsrisiko (Regel 4). Push aufs Handy ist ok.

### D4 · Quellen-Konflikt-Politik: Dossier schlägt Alt-CV
`career/dossier.md` (kuratiert, mit Fakten-Gates, Stand 27.07.2026) gewinnt bei jedem Widerspruch gegen den hochgeladenen Alt-CV (`career/cv/CV_2025_intern.pdf`). Claims, die NUR im Alt-CV stehen, sind erst nach Moritz' Bestätigung verwendbar → `[KLÄREN]`. Konkrete Funde siehe `career/cv/notizen.md`.

### D5 · Sperrliste operationalisiert
KO-Filter fasst „thyssenkrupp nucera + verbundene Unternehmen" als: **gesamte thyssenkrupp-Gruppe** (Konzernmutter ist Mehrheitsaktionärin → verbunden). Wettbewerber (Sunfire, Enapter, H-TEC …) sind NICHT gesperrt, bekommen aber ein Diskretions-Flag in der Analyse (Branche redet). Grenzfälle → Moritz fragen, nicht anfassen.

### D6 · ID-Schema & Status-Flow
ID: `YYYY-MM-DD-firma-rolle-kurz` (Datum = Entdeckung). Status-Flow: `neu → bewertet → empfohlen → mappe → gesendet → antwort → interview → angebot` | Endzustände: `verworfen`, `absage`, `ghosting`. Follow-up-Entwurf ab 12 Tagen in `gesendet` ohne Reaktion.

### D7 · Mappen-Schwelle
Mappe wird gebaut ab Score ≥ 7,5 UND keine offene KO-Frage. 3–5 Mappen/Woche sind das Ziel — bei mehr Kandidaten entscheidet der Score, Rest bleibt `empfohlen` mit Begründung in der Übersicht. Ausnahme: Im Kalibrier-/Probelauf-Kontext darf eine Mappe knapp unterhalb gebaut werden, wenn die Analyse das explizit ausweist (angewendet am 27.07. bei Kelvion, 7,4).

### D8 · Branch-Handling
Diese Onboarding-Session arbeitet auf `claude/onboarding-setup-pmkcer` (Session-Vorgabe). Tägliche automatische Sessions folgen der Branch-Vorgabe ihrer eigenen Session; das Repo-Ziel ist, dass Moritz Stände regelmäßig nach `main` merged.

### D9 · Scoring ist Kopfarbeit, keine Skript-Arbeit
`tools/` liefert Rohdaten (Quellen ziehen, dedupe, KO-Vorfilter). Score, Begründung und Konfidenz vergebe ICH pro Stelle nach `career/preferences.md` (Rubrik v2). Kein Auto-Scoring — die Rubrik verlangt Urteil (Mandat einschätzen, Kultur-Signale, Stadt-Bewertung).

### D10 · Websuche-Sweeps gehören dem Agenten, nicht den Skripten
Query-Sets für WebSearch stehen im Runbook (`tools/README.md`). Jeder Fund wird auf der Firmen-Karriereseite verifiziert und erst dann archiviert/bewertet.

### D11 · Titel-Sichtung ≠ Prüfung
Die Quellen-Skripte liefern täglich Dutzende Titel; die gelten als *gesichtet* (dedupliziert in `jobs/rohdaten/gesehen.yaml`), nicht als *geprüft*. In `jobs/jobs.yaml` landen nur ernsthaft geprüfte Stellen: Volltext gelesen, Rubrik angewendet, Score + Konfidenz + Begründung. So bleibt die „bewertete Jobliste" ein Qualitätsversprechen, keine Halde.

### D12 · ATS-Probe-Hygiene
`--probe` kann Namensvettern treffen (am 27.07.: „personio"/„rtl"/„zeiss" auf fremden ATS mit 1–7 Jobs). Verdächtige Treffer (sehr wenige Jobs, Firmenname passt nicht zu Jobtiteln) in `tools/ats_status.yaml` auf `typ: keins` setzen und den echten Kanal per Websuche klären.
