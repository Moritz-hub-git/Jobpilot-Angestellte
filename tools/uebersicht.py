#!/usr/bin/env python3
"""Generiert UEBERSICHT.md (GitHub, mobil) und dashboard/index.html aus jobs/jobs.yaml. Nie von Hand editieren."""
import datetime
import html as H
import pathlib
import re

from qlib import ROOT, heute, load_yaml

STATUS_REIHE = ["neu", "bewertet", "empfohlen", "mappe", "gesendet", "antwort", "interview", "angebot"]
ENDE = ["verworfen", "absage", "ghosting"]


def klaeren_punkte():
    punkte = []
    for pfad in list((ROOT / "mappen").rglob("*.md")) + [ROOT / "career" / "cv" / "notizen.md"]:
        if not pfad.exists():
            continue
        for m in re.finditer(r"\[KLÄREN:([^\]]+)\]", pfad.read_text(encoding="utf-8")):
            punkte.append((str(pfad.relative_to(ROOT)), m.group(1).strip()))
    return punkte


def tage_seit(datum):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(str(datum))).days
    except Exception:
        return None


def main():
    jobs = (load_yaml(ROOT / "jobs" / "jobs.yaml", {}) or {}).get("jobs") or []
    jobs = [j for j in jobs if j]
    nach_status = {s: [j for j in jobs if j.get("status") == s] for s in STATUS_REIHE + ENDE}
    aktiv = [j for j in jobs if j.get("status") not in ENDE]

    handeln = []
    for j in nach_status["mappe"]:
        handeln.append(("Mappe reviewen", f"{j['firma']} — {j['rolle']} (Score {j.get('score')}): `{j.get('mappe')}`"))
    for j in nach_status["gesendet"]:
        t = tage_seit(j.get("gesendet_am"))
        if t is not None and t >= 12:
            handeln.append(("Follow-up freigeben", f"{j['firma']} — {j['rolle']} ({t} Tage ohne Antwort)"))
    for j in nach_status["empfohlen"]:
        handeln.append(("Empfehlung ansehen", f"{j['firma']} — {j['rolle']} (Score {j.get('score')})"))
    for pfad, txt in klaeren_punkte():
        handeln.append(("Klären", f"{txt} _(→ {pfad})_"))

    woche = [j for j in jobs
             if (lambda t: t is not None and t <= 7)(tage_seit(j.get("entdeckt")))]
    zahlen = {
        "geprüft (7 Tage)": len(woche),
        "davon bewertet": len([j for j in woche if j.get("score") is not None]),
        "Mappen aktiv": len(nach_status["mappe"]),
        "Pipeline aktiv": len(aktiv),
        "verworfen (7 Tage)": len([j for j in woche if j.get("status") == "verworfen"]),
    }

    bewertete = sorted([j for j in jobs if j.get("score") is not None and j.get("status") in ("bewertet", "empfohlen", "mappe")],
                       key=lambda j: -(j.get("score") or 0))

    # ---------- UEBERSICHT.md ----------
    md = [f"# Übersicht — Stand {heute()}", "",
          "> Generiert aus `jobs/jobs.yaml` (`python3 tools/uebersicht.py`). Komfort-Ansicht: `dashboard/index.html`.", "",
          "## 🔴 Handeln erforderlich (deine ≤ 15 Minuten)", ""]
    if handeln:
        for art, txt in handeln:
            md.append(f"- **{art}:** {txt}")
    else:
        md.append("- Nichts. Genieß den Tag.")
    md += ["", "## Zahlen", "", "| " + " | ".join(zahlen) + " |",
           "|" + "---|" * len(zahlen),
           "| " + " | ".join(str(v) for v in zahlen.values()) + " |", "",
           "## Bewertete Stellen (aktiv, nach Score)", ""]
    if bewertete:
        md.append("| Score | Firma | Rolle | Ort | Status | Konfidenz |")
        md.append("|---|---|---|---|---|---|")
        for j in bewertete:
            md.append(f"| **{j.get('score')}** | {j['firma']} | [{j['rolle']}]({j.get('url','')}) | "
                      f"{j.get('standort','')} | {j.get('status')} | {j.get('konfidenz','')} |")
        md.append("")
        for j in bewertete:
            md.append(f"**{j['firma']} — {j['rolle']}** (Score {j.get('score')}, Konfidenz {j.get('konfidenz')}):  \n"
                      f"{j.get('begruendung','').strip()}  \n"
                      f"↳ Volltext: `{j.get('archiv','—')}`" + (f" · Mappe: `{j.get('mappe')}`" if j.get("mappe") else ""))
            md.append("")
    else:
        md.append("Noch keine bewerteten Stellen.")
    ausgeschieden = [j for j in jobs if j.get("status") in ENDE]
    if ausgeschieden:
        md += ["## Ausgeschieden (Kurzbegründung)", ""]
        for j in ausgeschieden:
            grund = j.get("ko") or j.get("begruendung", "")
            md.append(f"- {j['firma']} — {j['rolle']}: {j.get('status')} — {grund}")
    (ROOT / "UEBERSICHT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---------- dashboard/index.html ----------
    def esc(x):
        return H.escape(str(x if x is not None else ""))

    farben = {"neu": "#8899aa", "bewertet": "#5b7fd4", "empfohlen": "#7c5bd4", "mappe": "#d48a2f",
              "gesendet": "#2f9dd4", "antwort": "#2fb04c", "interview": "#1e9e63", "angebot": "#0f8a4f",
              "verworfen": "#99a", "absage": "#c0564f", "ghosting": "#99a"}
    zeilen = "".join(
        f"<tr><td class='sc'>{esc(j.get('score'))}</td><td><b>{esc(j['firma'])}</b><br>"
        f"<a href='{esc(j.get('url'))}'>{esc(j['rolle'])}</a></td><td>{esc(j.get('standort'))}</td>"
        f"<td><span class='badge' style='background:{farben.get(j.get('status'), '#888')}'>{esc(j.get('status'))}</span></td>"
        f"<td class='beg'>{esc(j.get('begruendung'))}<br><i>Konfidenz: {esc(j.get('konfidenz'))}</i></td></tr>"
        for j in bewertete)
    handeln_html = "".join(f"<li><b>{esc(a)}:</b> {esc(t)}</li>" for a, t in handeln) or "<li>Nichts offen.</li>"
    kacheln = "".join(f"<div class='tile'><div class='num'>{v}</div><div class='lbl'>{esc(k)}</div></div>"
                      for k, v in zahlen.items())
    pipeline_html = "".join(
        f"<div class='stage'><span class='badge' style='background:{farben[s]}'>{s}</span> {len(nach_status[s])}</div>"
        for s in STATUS_REIHE)
    html_doc = f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Jobpilot — Übersicht {heute()}</title><style>
:root {{ --bg:#fff; --fg:#1c2330; --mut:#5c6675; --card:#f4f6f9; --line:#e2e6ec; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#12161d; --fg:#e8ecf2; --mut:#9aa5b3; --card:#1b212b; --line:#2a3340; }} }}
* {{ box-sizing:border-box }} body {{ margin:0; font:16px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--fg); padding:16px; }}
h1 {{ font-size:1.35rem; margin:.2rem 0 1rem }} h2 {{ font-size:1.05rem; margin:1.4rem 0 .5rem; color:var(--mut); text-transform:uppercase; letter-spacing:.04em }}
.tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px }}
.tile {{ background:var(--card); border-radius:12px; padding:12px }} .num {{ font-size:1.6rem; font-weight:700 }} .lbl {{ color:var(--mut); font-size:.8rem }}
.stage {{ display:inline-block; margin:4px 8px 4px 0; color:var(--mut) }}
.badge {{ color:#fff; border-radius:999px; padding:2px 10px; font-size:.78rem; white-space:nowrap }}
ul.act {{ background:var(--card); border-radius:12px; padding:14px 14px 14px 32px; margin:0 }} ul.act li {{ margin:.35rem 0 }}
table {{ border-collapse:collapse; width:100%; margin-top:.5rem }} td {{ border-top:1px solid var(--line); padding:10px 8px; vertical-align:top }}
td.sc {{ font-size:1.25rem; font-weight:800; width:2.5rem }} td.beg {{ color:var(--mut); font-size:.9rem; min-width:200px }}
a {{ color:inherit }} .wrap {{ overflow-x:auto }} footer {{ color:var(--mut); font-size:.8rem; margin-top:2rem }}
</style></head><body>
<h1>🧭 Jobpilot — {heute()}</h1>
<h2>Handeln erforderlich</h2><ul class="act">{handeln_html}</ul>
<h2>Zahlen (7 Tage)</h2><div class="tiles">{kacheln}</div>
<h2>Pipeline</h2><div>{pipeline_html}</div>
<h2>Bewertete Stellen</h2><div class="wrap"><table>{zeilen or '<tr><td>Noch keine.</td></tr>'}</table></div>
<footer>Generiert von Vera · Quelle: jobs/jobs.yaml · Mappen unter mappen/&lt;id&gt;/</footer>
</body></html>"""
    dash = ROOT / "dashboard"
    dash.mkdir(exist_ok=True)
    (dash / "index.html").write_text(html_doc, encoding="utf-8")
    print(f"OK: UEBERSICHT.md + dashboard/index.html ({len(jobs)} Jobs, {len(handeln)} Handlungspunkte)")


if __name__ == "__main__":
    main()
