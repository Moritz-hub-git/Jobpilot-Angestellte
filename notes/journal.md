# Journal — Vera (Karriere-Managerin von Moritz)

> Nach jedem Arbeitstag 3–5 Zeilen: was lief gut, was schlecht, was ändere ich.

## 2026-07-27 — Tag 1, Teil 2 (Freigabe erhalten → Aufbau + Probelauf)

- **Gut:** Voller Aufbau an einem Tag: Repo-Struktur, 3 Quellen-Kanäle live (BA-API mit Volltext-Details, Arbeitnow, 18 verifizierte ATS-Feeds), Master-CV (1 Seite, inkl. aktueller AI-Rolle), Übersicht/Dashboard-Generator, Lektor-Agent. Probelauf: 174+52+322 Treffer gesichtet, 7 Stellen ernsthaft geprüft, 2 Mappen gebaut (Sixt 7,9 — Anzeige von heute, Profildeckung außergewöhnlich; Kelvion 7,4 als Kalibrier-Grenzfall).
- **Schlecht:** BA-Detail-Endpunkt zuerst falsch geraten (kein Volltext im ersten Lauf — gefixt: `/pc/v4/jobdetails/`); ATS-Probe holte 3 Namensvettern (bereinigt, D12); CV/Briefe brauchten 3 Render-Anläufe bis einseitig; im Kelvion-Brief stand „von Herne aus" statt „nach Herne" — vor Review gefixt.
- **Ändere ich:** Fakten-Konflikte Alt-CV↔Dossier systematisch dokumentiert (`career/cv/notizen.md`) statt still zu entscheiden; Seiten-Check fest in `render_pdf.sh`; D11 eingeführt, damit die Jobliste ein Qualitätsversprechen bleibt und keine Halde wird.
- **Offen für morgen:** FLH-Firmenrecherche (Hochstufung oder Verwerfen), LinkedIn/Xing/StepStone-Suchstrings für Moritz vorbereiten, internationale Watchlist mit Moritz priorisieren, Moritz' Feedback zu den 2 Kalibrier-Mappen einarbeiten (`notes/feedback.md` anlegen).

## 2026-07-27 — Tag 1, Teil 1 (Onboarding, vor der Freigabe)

- Eingestellt. Name gewählt: **Vera.** Stellenprofil, Handbuch, Onboarding-Nachricht und das komplette Karriere-Dossier (`career/`, 5 Dateien) gelesen.
- Technik geprüft: Commit/Push auf `claude/onboarding-setup-pmkcer` ✅ · HTML→A4-PDF via Chromium headless ✅ · Quellen erreichbar: BA-Jobsuche-API ✅ (Erster Testtreffer: „Head of AI Solutions & Architecture", Kelvion, Herne — gutes Omen), Arbeitnow ✅, Greenhouse/Personio/SmartRecruiters ✅.
- Arbeitsplatz-Entwurf zur Freigabe geschickt; 3 Rückfragen gestellt (Ist-Paket/Titel · Du/Sie · CV-Basis). Moritz hat alles freigegeben, Ist-Paket bestätigt, Du-Präferenz festgelegt und seinen Alt-CV geliefert.
- Gefunden: `agents/lektor.md`-Vorlage fehlte im Repo → selbst angelegt (`.claude/agents/lektor.md`).
