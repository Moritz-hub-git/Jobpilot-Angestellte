#!/usr/bin/env python3
"""Baut das interaktive Karriere-Cockpit (eine selbst-enthaltene HTML-Seite) aus den Repo-Daten:
jobs/jobs.yaml + mappen/<id>/{analyse,anschreiben,cv}.md + jobs/archiv/<id>/posting.md + notes/feedback.md
+ jobs/rohdaten/gesehen.yaml (Quellen-Zähler).
Ausgabe: dashboard/artifact.html — als privates Claude-Artifact veröffentlicht (URL: notes/entscheidungen.md, D13).
Layout v2 (Feedback Moritz 27.07.): Master-Detail — kompakte Zeilen, gruppiert nach Handlungsbedarf,
alles Tiefe erst nach Klick; Quellen im Fuß transparent."""
import datetime
import html
import re

from qlib import ROOT, heute, load_yaml

STATUS_META = {
    "neu":       ("Neu", "st-info"),
    "bewertet":  ("Bewertet", "st-info"),
    "empfohlen": ("Empfohlen", "st-action"),
    "mappe":     ("Review nötig", "st-action"),
    "gesendet":  ("Gesendet", "st-info"),
    "antwort":   ("Antwort da", "st-good"),
    "interview": ("Interview", "st-good"),
    "angebot":   ("Angebot", "st-good"),
    "verworfen": ("Verworfen", "st-dead"),
    "absage":    ("Absage", "st-bad"),
    "ghosting":  ("Ghosting", "st-dead"),
}
GRUPPEN = [
    ("Dein Review", ("mappe", "empfohlen")),
    ("Laufende Bewerbungen", ("gesendet", "antwort", "interview", "angebot")),
    ("In Beobachtung", ("neu", "bewertet")),
    ("Aussortiert — mit Begründung", ("verworfen", "absage", "ghosting")),
]
AKTIV = ("neu", "bewertet", "empfohlen", "mappe", "gesendet", "antwort", "interview", "angebot")

QUELLE_LABEL = {"ba": "Arbeitsagentur", "arbeitnow": "Arbeitnow", "websuche": "Websuche", "moritz": "von Moritz"}


def quelle_label(q):
    q = str(q or "")
    if q.startswith("ats:"):
        return f"Karrierefeed ({q.split(':', 1)[1]})"
    return QUELLE_LABEL.get(q, q)


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def md2html(text):
    """Kleiner Markdown-Renderer: Überschriften, Fett, Links, Listen, Tabellen, Blockquote, HR."""
    def inline(s):
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"\*(.+?)\*", r"<i>\1</i>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
        return s

    out, i = [], 0
    zeilen = text.splitlines()
    while i < len(zeilen):
        z = zeilen[i]
        if not z.strip():
            i += 1; continue
        if z.startswith("#"):
            tief = len(z) - len(z.lstrip("#"))
            if tief == 1:
                i += 1; continue  # Dokumenttitel unterdrücken (Zeile hat eigenen Titel)
            out.append(f"<h4>{inline(z.lstrip('#').strip())}</h4>"); i += 1
        elif z.strip() in ("---", "***"):
            out.append("<hr>"); i += 1
        elif z.startswith(">"):
            blk = []
            while i < len(zeilen) and zeilen[i].startswith(">"):
                blk.append(zeilen[i].lstrip("> ").strip()); i += 1
            out.append(f"<blockquote>{inline(' '.join(blk))}</blockquote>")
        elif z.strip().startswith(("- ", "* ", "• ")):
            items = []
            while i < len(zeilen) and zeilen[i].strip().startswith(("- ", "* ", "• ")):
                items.append(f"<li>{inline(zeilen[i].strip()[2:].strip())}</li>"); i += 1
            out.append(f"<ul>{''.join(items)}</ul>")
        elif z.strip().startswith("|"):
            rows = []
            while i < len(zeilen) and zeilen[i].strip().startswith("|"):
                rows.append([c.strip() for c in zeilen[i].strip().strip("|").split("|")]); i += 1
            if len(rows) >= 2 and set("".join(rows[1])) <= set("-: |"):
                kopf, body = rows[0], rows[2:]
            else:
                kopf, body = None, rows
            t = ["<div class='tblwrap'><table>"]
            if kopf:
                t.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in kopf) + "</tr>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</table></div>")
            out.append("".join(t))
        else:
            absatz = [z.strip()]
            i += 1
            while i < len(zeilen) and zeilen[i].strip() and not re.match(r"^(#|\||>|- |\* |---)", zeilen[i].strip()):
                absatz.append(zeilen[i].strip()); i += 1
            out.append(f"<p>{inline(' '.join(absatz))}</p>")
    return "\n".join(out)


def datei(pfad):
    p = ROOT / pfad
    return p.read_text(encoding="utf-8") if p.exists() else None


def sub_details(titel, inhalt_html):
    return f"<details class='sub'><summary>{esc(titel)}</summary><div class='dbody'>{inhalt_html}</div></details>"


def tage_seit(d):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(str(d))).days
    except Exception:
        return None


def job_zeile(j):
    st = j.get("status", "neu")
    label, klasse = STATUS_META.get(st, (st, "st-info"))
    mid = j.get("id", "")
    score = j.get("score")
    score_txt = f"{score:.1f}".replace(".", ",") if isinstance(score, (int, float)) else "–"

    innen = [f"<p class='beg'>{esc(j.get('begruendung', '')).strip()}</p>"]
    if j.get("ko"):
        innen.append(f"<p class='ko'>KO: {esc(j['ko'])}</p>")
    innen.append(
        "<p class='links'>"
        f"<a href='{esc(j.get('url'))}' target='_blank' rel='noopener'>Anzeige online öffnen ↗</a>"
        f"<span class='mut'> · Konfidenz: {esc(j.get('konfidenz', '—'))} · Quelle: {esc(quelle_label(j.get('quelle')))}"
        f" · entdeckt {esc(j.get('entdeckt'))}</span></p>")
    for name, pfad in (("Analyse — Warum · Gehalt · Risiken", f"mappen/{mid}/analyse.md"),
                       ("Anschreiben (Entwurf im Wortlaut)", f"mappen/{mid}/anschreiben.md"),
                       ("CV-Variante (Delta zum Master)", f"mappen/{mid}/cv.md")):
        inhalt = datei(pfad)
        if inhalt:
            innen.append(sub_details(name, md2html(inhalt)))
    posting = datei(f"jobs/archiv/{mid}/posting.md")
    if posting:
        innen.append(sub_details("Original-Anzeige (archivierter Volltext)", md2html(posting)))

    return f"""
<details class="jobrow" id="job-{esc(mid)}" data-status="{esc(st)}">
  <summary>
    <span class="score">{score_txt}</span>
    <span class="jmain"><b>{esc(j.get('firma'))}</b><span class="rolle">{esc(j.get('rolle'))}</span>
      <span class="jmeta">{esc(j.get('standort'))}</span></span>
    <span class="pill {klasse}">{esc(label)}</span>
  </summary>
  <div class="jbody">{''.join(innen)}</div>
</details>"""


def main():
    jobs = (load_yaml(ROOT / "jobs" / "jobs.yaml", {}) or {}).get("jobs") or []
    jobs = sorted([j for j in jobs if j], key=lambda j: -(j.get("score") or 0))
    n_aktiv = len([j for j in jobs if j.get("status") in AKTIV])
    n_mappen = len([j for j in jobs if j.get("status") == "mappe"])
    n_woche = len([j for j in jobs if (lambda t: t is not None and t <= 7)(tage_seit(j.get("entdeckt")))])

    # Handeln erforderlich
    handeln = []
    for j in jobs:
        if j.get("status") == "mappe":
            handeln.append((j["firma"], f"Mappe reviewen — Score {str(j.get('score')).replace('.', ',')}", f"#job-{esc(j['id'])}"))
        if j.get("status") == "empfohlen":
            handeln.append((j["firma"], "Empfehlung ansehen", f"#job-{esc(j['id'])}"))
        if j.get("status") == "gesendet":
            t = tage_seit(j.get("gesendet_am"))
            if t is not None and t >= 12:
                handeln.append((j["firma"], f"Follow-up freigeben ({t} Tage ohne Antwort)", f"#job-{esc(j['id'])}"))
    handeln_html = "".join(
        f"<li><a href='{link}'><b>{esc(f)}</b> — {esc(txt)}</a></li>" for f, txt, link in handeln
    ) or "<li class='mut'>Nichts offen. Genieß den Tag.</li>"

    # Klärpunkte
    fb = datei("notes/feedback.md")
    klaeren = []
    if fb and "## Offene Kalibrier-Fragen" in fb:
        for z in fb.split("## Offene Kalibrier-Fragen", 1)[1].splitlines():
            m = re.match(r"^\s*\d+\.\s+(.*)", z)
            if m:
                klaeren.append(m.group(1))
    klaeren_html = "".join(f"<li>{md2html(k)[3:-4]}</li>" for k in klaeren)

    # Gruppen
    gruppen_html = []
    for titel, stati in GRUPPEN:
        drin = [j for j in jobs if j.get("status") in stati]
        if not drin:
            continue
        zeilen = "".join(job_zeile(j) for j in drin)
        gruppen_html.append(f"<h3 class='gruppe'>{esc(titel)} <span class='anz'>{len(drin)}</span></h3>{zeilen}")

    # Quellen (Zähler aus gesehen.yaml)
    gesehen = load_yaml(ROOT / "jobs" / "rohdaten" / "gesehen.yaml", {}) or {}
    n_ba, n_an, n_ats = (len(gesehen.get(k, {})) for k in ("ba", "arbeitnow", "ats"))
    ats_status = load_yaml(ROOT / "tools" / "ats_status.yaml", {}) or {}
    n_feeds = len([v for v in ats_status.values() if v.get("typ") and v.get("typ") != "keins"])
    wl = load_yaml(ROOT / "watchlist.yaml", {}) or {}
    n_wl = len(wl.get("firmen", []))
    quellen_html = f"""
  <li><b>Arbeitsagentur-Jobsuche</b> (offizielle API der BA) — Führungs-/KI-Query-Set, täglich · bisher {n_ba} Titel gesichtet</li>
  <li><b>Karriereseiten-Feeds der Watchlist</b> — {n_wl} kuratierte Firmen, davon {n_feeds} Feeds verifiziert
      (Greenhouse, Personio, SmartRecruiters, Lever, Recruitee, Ashby — offizielle öffentliche Schnittstellen) · bisher {n_ats} relevante Titel</li>
  <li><b>Arbeitnow</b> (freies Job-Board mit API, DE-Fokus) — bisher {n_an} KI-relevante Titel</li>
  <li><b>Websuche-Sweeps</b> („Head of AI", „AI Lead", „Leiter KI" × Deutschland) — ab dem nächsten Tageslauf; Funde werden auf der Firmenseite verifiziert</li>
  <li><b>Über dich</b>: LinkedIn-/Xing-/StepStone-Alerts leitest du formlos weiter (AGB-Regel: dort kein automatisierter Zugriff) — fertige Suchstrings bereite ich dir vor</li>"""

    tag_nr = max(1, (datetime.date.today() - datetime.date(2026, 7, 27)).days + 1)
    seite = f"""<title>Jobpilot — Karriere-Cockpit</title>
<style>
:root {{
  --bg:#F5F8F7; --surface:#FFFFFF; --ink:#182420; --mut:#5C6E68; --line:#DCE5E2;
  --accent:#0B6B5D; --accent-ink:#FFFFFF;
  --act:#9A4E00; --act-bg:#FFF3E4; --good:#166A3B; --good-bg:#E4F3E9;
  --bad:#9E2B22; --bad-bg:#FBEAE8; --info:#2B5D8F; --info-bg:#E8F0F8; --dead:#6B7672; --dead-bg:#EDF0EF;
}}
@media (prefers-color-scheme: dark) {{ :root {{
  --bg:#111917; --surface:#182220; --ink:#E5EEEA; --mut:#8FA39C; --line:#27332F;
  --accent:#3AA78F; --accent-ink:#0C1512;
  --act:#F0A24B; --act-bg:#33270F; --good:#5CC08A; --good-bg:#12291A;
  --bad:#E8867D; --bad-bg:#331512; --info:#7FB1DE; --info-bg:#152435; --dead:#8A9792; --dead-bg:#222B28;
}} }}
:root[data-theme="light"] {{
  --bg:#F5F8F7; --surface:#FFFFFF; --ink:#182420; --mut:#5C6E68; --line:#DCE5E2;
  --accent:#0B6B5D; --accent-ink:#FFFFFF;
  --act:#9A4E00; --act-bg:#FFF3E4; --good:#166A3B; --good-bg:#E4F3E9;
  --bad:#9E2B22; --bad-bg:#FBEAE8; --info:#2B5D8F; --info-bg:#E8F0F8; --dead:#6B7672; --dead-bg:#EDF0EF;
}}
:root[data-theme="dark"] {{
  --bg:#111917; --surface:#182220; --ink:#E5EEEA; --mut:#8FA39C; --line:#27332F;
  --accent:#3AA78F; --accent-ink:#0C1512;
  --act:#F0A24B; --act-bg:#33270F; --good:#5CC08A; --good-bg:#12291A;
  --bad:#E8867D; --bad-bg:#331512; --info:#7FB1DE; --info-bg:#152435; --dead:#8A9792; --dead-bg:#222B28;
}}
* {{ box-sizing:border-box; margin:0; }}
body {{ background:var(--bg); color:var(--ink); font:16px/1.55 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
       padding:0 14px 64px; overflow-wrap:anywhere; }}
.shell {{ max-width:720px; margin:0 auto; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
code {{ font:.85em ui-monospace,"SF Mono","Cascadia Code",Consolas,monospace; background:var(--dead-bg); padding:1px 5px; border-radius:4px; }}
.eyebrow {{ font:600 11px/1 ui-monospace,"SF Mono",Consolas,monospace; letter-spacing:.14em; text-transform:uppercase; color:var(--mut); }}
header.top {{ padding:26px 0 14px; border-bottom:2px solid var(--ink); }}
header.top h1 {{ font-size:24px; letter-spacing:-.01em; text-wrap:balance; }}
header.top h1 b {{ color:var(--accent); }}
.standzeile {{ display:flex; flex-wrap:wrap; gap:5px 16px; margin-top:8px; color:var(--mut); font-size:13px; }}
.standzeile span b {{ color:var(--ink); font-variant-numeric:tabular-nums; }}
section {{ margin-top:26px; }}
section > h2 {{ font-size:14.5px; margin-bottom:10px; display:flex; align-items:baseline; gap:10px; }}
section > h2 .eyebrow {{ font-size:10.5px; }}
.karte {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:13px 16px; }}
ul.act {{ list-style:none; display:flex; flex-direction:column; gap:8px; }}
ul.act li {{ padding-left:12px; border-left:3px solid var(--act); font-size:14.5px; }}
ul.act a {{ color:var(--ink); }} ul.act a b {{ color:var(--accent); }}
.mut {{ color:var(--mut); }}
h3.gruppe {{ font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--mut);
            margin:20px 0 8px; display:flex; align-items:center; gap:8px; }}
h3.gruppe .anz {{ background:var(--dead-bg); color:var(--mut); border-radius:999px; padding:1px 8px;
                 font-variant-numeric:tabular-nums; }}
.jobrow {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; margin-bottom:8px; }}
.jobrow[data-status="mappe"], .jobrow[data-status="empfohlen"] {{ border-left:4px solid var(--act); }}
.jobrow > summary {{ display:flex; align-items:center; gap:12px; padding:11px 14px; cursor:pointer; list-style:none; }}
.jobrow > summary::-webkit-details-marker {{ display:none; }}
.jobrow > summary::after {{ content:"▸"; color:var(--mut); margin-left:2px; }}
.jobrow[open] > summary::after {{ content:"▾"; }}
.jobrow[open] > summary {{ border-bottom:1px solid var(--line); }}
.score {{ font:700 19px/1 ui-monospace,"SF Mono",Consolas,monospace; font-variant-numeric:tabular-nums;
         color:var(--accent); min-width:2.2em; text-align:right; }}
.jmain {{ flex:1; min-width:0; display:flex; flex-direction:column; gap:1px; }}
.jmain b {{ font-size:15px; }}
.rolle {{ font-size:13px; color:var(--ink); opacity:.85; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.jmeta {{ font-size:12px; color:var(--mut); }}
.pill {{ font-size:11.5px; font-weight:600; padding:3px 9px; border-radius:999px; white-space:nowrap; }}
.st-action {{ background:var(--act-bg); color:var(--act); }}
.st-good {{ background:var(--good-bg); color:var(--good); }}
.st-bad {{ background:var(--bad-bg); color:var(--bad); }}
.st-info {{ background:var(--info-bg); color:var(--info); }}
.st-dead {{ background:var(--dead-bg); color:var(--dead); }}
.jbody {{ padding:12px 16px 14px; }}
.beg {{ font-size:14.5px; }}
.ko {{ margin-top:8px; font-size:13.5px; color:var(--bad); }}
.links {{ margin-top:10px; font-size:13px; }}
details.sub {{ margin-top:10px; border:1px solid var(--line); border-radius:8px; background:var(--bg); }}
details.sub summary {{ cursor:pointer; padding:8px 13px; font-size:13.5px; font-weight:600; color:var(--mut); list-style:none; }}
details.sub summary::-webkit-details-marker {{ display:none; }}
details.sub summary::before {{ content:"▸ "; color:var(--accent); }}
details.sub[open] summary::before {{ content:"▾ "; }}
.dbody {{ padding:2px 15px 13px; font-size:14px; }}
.dbody h4 {{ margin:12px 0 5px; font-size:12.5px; text-transform:uppercase; letter-spacing:.05em; color:var(--mut); }}
.dbody p {{ margin:7px 0; }}
.dbody ul {{ margin:7px 0 7px 20px; }} .dbody li {{ margin:3px 0; }}
.dbody blockquote {{ border-left:3px solid var(--line); padding-left:12px; color:var(--mut); margin:8px 0; font-size:13px; }}
.dbody hr {{ border:0; border-top:1px solid var(--line); margin:12px 0; }}
.tblwrap {{ overflow-x:auto; margin:8px 0; }}
.tblwrap table {{ border-collapse:collapse; font-size:13px; min-width:420px; }}
.tblwrap th, .tblwrap td {{ border:1px solid var(--line); padding:6px 9px; text-align:left; vertical-align:top; }}
.tblwrap th {{ color:var(--mut); font-weight:600; }}
ol.klaeren {{ margin-left:20px; display:flex; flex-direction:column; gap:8px; font-size:14px; }}
ul.quellen {{ list-style:none; display:flex; flex-direction:column; gap:9px; font-size:13.5px; }}
ul.quellen li {{ padding-left:12px; border-left:3px solid var(--line); }}
footer {{ margin-top:36px; padding-top:14px; border-top:1px solid var(--line); color:var(--mut); font-size:12.5px; }}
footer p {{ margin:4px 0; }}
summary:focus-visible, a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
@media (prefers-reduced-motion: no-preference) {{
  .jbody, .dbody {{ animation:auf .12s ease-out; }}
  @keyframes auf {{ from {{ opacity:.4; }} to {{ opacity:1; }} }} }}
</style>
<div class="shell">
<header class="top">
  <p class="eyebrow">Jobpilot · privat — Link nicht weitergeben</p>
  <h1>Karriere-Cockpit <b>Moritz</b></h1>
  <div class="standzeile">
    <span>Stand <b>{heute()}</b></span>
    <span>geprüft (7 T) <b>{n_woche}</b></span>
    <span>Review offen <b>{n_mappen}</b></span>
    <span>Pipeline aktiv <b>{n_aktiv}</b></span>
    <span>Probezeit-Tag <b>{tag_nr}</b>/14</span>
  </div>
</header>

<section id="handeln">
  <h2><span class="eyebrow">Deine ≤ 15 Minuten</span>Handeln erforderlich</h2>
  <div class="karte"><ul class="act">{handeln_html}</ul></div>
</section>

<section id="stellen">
  <h2><span class="eyebrow">Zeile antippen = alles Weitere</span>Stellen</h2>
  {''.join(gruppen_html)}
</section>

<section id="klaeren">
  <h2><span class="eyebrow">Kurz von dir</span>Offene Klärpunkte</h2>
  <div class="karte"><ol class="klaeren">{klaeren_html or '<li class="mut">Keine.</li>'}</ol></div>
</section>

<section id="quellen">
  <h2><span class="eyebrow">Woher die Stellen kommen</span>Quellen</h2>
  <div class="karte"><ul class="quellen">{quellen_html}</ul></div>
</section>

<footer>
  <p><b>Wo liegt was?</b> Versandfertige PDFs: Repo <code>mappen/&lt;id&gt;/</code> · Datenbestand: <code>jobs/jobs.yaml</code> (versioniert in Git) ·
     Volltext-Archiv: <code>jobs/archiv/</code> · Regeln &amp; Log: <code>notes/</code></p>
  <p>Aktualisiert von Vera nach jedem Arbeitstag (dieselbe URL). Nichts wird ohne dich versendet — Feedback einfach als Nachricht („Feedback: …").</p>
</footer>
</div>
<script>
function openTarget() {{
  if (!location.hash) return;
  const el = document.getElementById(location.hash.slice(1));
  if (el && el.tagName === "DETAILS") {{ el.open = true; el.scrollIntoView({{block: "start"}}); }}
}}
addEventListener("hashchange", openTarget);
addEventListener("load", openTarget);
</script>
"""
    ziel = ROOT / "dashboard" / "artifact.html"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(seite, encoding="utf-8")
    print(f"OK: {ziel} ({len(seite) // 1024} KB, {len(jobs)} Stellen, {len(handeln)} Handlungspunkte)")


if __name__ == "__main__":
    main()
