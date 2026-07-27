#!/usr/bin/env python3
"""Baut das interaktive Karriere-Cockpit (eine selbst-enthaltene HTML-Seite) aus den Repo-Daten:
jobs/jobs.yaml + mappen/<id>/{analyse,anschreiben,cv}.md + jobs/archiv/<id>/posting.md + notes/feedback.md.
Ausgabe: dashboard/artifact.html — wird als privates Claude-Artifact veröffentlicht (URL in notes/entscheidungen.md, D13)."""
import datetime
import html
import pathlib
import re

from qlib import ROOT, heute, load_yaml

STATUS_META = {
    "neu":       ("Neu", "st-neutral"),
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
AKTIV = ("neu", "bewertet", "empfohlen", "mappe", "gesendet", "antwort", "interview", "angebot")


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
        if z.startswith("###"):
            out.append(f"<h4>{inline(z.lstrip('#').strip())}</h4>"); i += 1
        elif z.startswith("##"):
            out.append(f"<h4>{inline(z.lstrip('#').strip())}</h4>"); i += 1
        elif z.startswith("#"):
            i += 1  # Dokumenttitel unterdrücken (Karte hat eigenen Titel)
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


def details(titel, inhalt_html, offen=False):
    o = " open" if offen else ""
    return (f"<details{o}><summary>{esc(titel)}</summary>"
            f"<div class='dbody'>{inhalt_html}</div></details>")


def tage_seit(d):
    try:
        return (datetime.date.today() - datetime.date.fromisoformat(str(d))).days
    except Exception:
        return None


def main():
    jobs = (load_yaml(ROOT / "jobs" / "jobs.yaml", {}) or {}).get("jobs") or []
    jobs = sorted([j for j in jobs if j], key=lambda j: -(j.get("score") or 0))
    n_aktiv = len([j for j in jobs if j.get("status") in AKTIV])
    n_mappen = len([j for j in jobs if j.get("status") == "mappe"])
    n_woche = len([j for j in jobs if (lambda t: t is not None and t <= 7)(tage_seit(j.get("entdeckt")))])
    n_verworfen = len([j for j in jobs if j.get("status") == "verworfen"])

    # Handeln erforderlich
    handeln = []
    for j in jobs:
        if j.get("status") == "mappe":
            handeln.append((f"Mappe reviewen: {j['firma']}", f"#job-{esc(j['id'])}",
                            f"Score {j.get('score')} — Analyse, Anschreiben und Original unten in der Karte"))
        if j.get("status") == "gesendet":
            t = tage_seit(j.get("gesendet_am"))
            if t is not None and t >= 12:
                handeln.append((f"Follow-up freigeben: {j['firma']}", f"#job-{esc(j['id'])}", f"{t} Tage ohne Antwort"))
    fb = datei("notes/feedback.md")
    klaeren = []
    if fb and "## Offene Kalibrier-Fragen" in fb:
        for z in fb.split("## Offene Kalibrier-Fragen", 1)[1].splitlines():
            m = re.match(r"^\s*\d+\.\s+(.*)", z)
            if m:
                klaeren.append(m.group(1))

    # Job-Karten
    karten = []
    for j in jobs:
        st = j.get("status", "neu")
        label, klasse = STATUS_META.get(st, (st, "st-neutral"))
        blocks = [f"<p class='beg'>{esc(j.get('begruendung', '')).strip()}</p>"]
        if j.get("ko"):
            blocks.append(f"<p class='ko'>KO: {esc(j['ko'])}</p>")
        mid = j.get("id", "")
        for name, pfad in (("Analyse (Warum · Gehalt · Risiken)", f"mappen/{mid}/analyse.md"),
                           ("Anschreiben (Entwurf)", f"mappen/{mid}/anschreiben.md"),
                           ("CV-Variante (Delta zum Master)", f"mappen/{mid}/cv.md")):
            inhalt = datei(pfad)
            if inhalt:
                blocks.append(details(name, md2html(inhalt)))
        posting = datei(f"jobs/archiv/{mid}/posting.md")
        if posting:
            blocks.append(details("Original-Anzeige (archivierter Volltext)", md2html(posting)))
        quelle_zeile = " · ".join(x for x in (
            esc(j.get("standort")), f"Quelle: {esc(j.get('quelle'))}",
            f"entdeckt {esc(j.get('entdeckt'))}",
            f"Konfidenz: {esc(j.get('konfidenz'))}" if j.get("konfidenz") else "") if x)
        score = j.get("score")
        karten.append(f"""
<article class="job" id="job-{esc(mid)}" data-status="{esc(st)}">
  <div class="jobkopf">
    <div class="score">{esc(f"{score:.1f}" if isinstance(score, float) else score) if score is not None else "–"}</div>
    <div class="jobtitel">
      <h3>{esc(j.get('firma'))}</h3>
      <p class="rolle"><a href="{esc(j.get('url'))}" target="_blank" rel="noopener">{esc(j.get('rolle'))}</a></p>
      <p class="meta">{quelle_zeile}</p>
    </div>
    <span class="pill {klasse}">{esc(label)}</span>
  </div>
  {''.join(blocks)}
</article>""")

    handeln_html = "".join(
        f"<li><a href='{link}'><b>{esc(t)}</b></a><span class='mut'> — {esc(sub)}</span></li>"
        for t, link, sub in handeln) or "<li class='mut'>Nichts offen. Genieß den Tag.</li>"
    klaeren_html = "".join(f"<li>{md2html(k)[3:-4]}</li>" for k in klaeren)

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
       padding:0 16px 64px; overflow-wrap:anywhere; }}
.shell {{ max-width:760px; margin:0 auto; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
code {{ font:.85em ui-monospace,"SF Mono","Cascadia Code",Consolas,monospace; background:var(--dead-bg); padding:1px 5px; border-radius:4px; }}
.eyebrow {{ font:600 11px/1 ui-monospace,"SF Mono",Consolas,monospace; letter-spacing:.14em; text-transform:uppercase; color:var(--mut); }}
header.top {{ padding:28px 0 18px; border-bottom:2px solid var(--ink); }}
header.top h1 {{ font-size:26px; letter-spacing:-.01em; text-wrap:balance; }}
header.top h1 b {{ color:var(--accent); }}
.standzeile {{ display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:8px; color:var(--mut); font-size:13.5px; }}
.standzeile span b {{ color:var(--ink); font-variant-numeric:tabular-nums; }}
section {{ margin-top:30px; }}
section > h2 {{ font-size:15px; margin-bottom:12px; display:flex; align-items:baseline; gap:10px; }}
section > h2 .eyebrow {{ font-size:11px; }}
.karte {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:16px 18px; }}
ul.act {{ list-style:none; display:flex; flex-direction:column; gap:10px; }}
ul.act li {{ padding-left:14px; border-left:3px solid var(--act); }}
.mut {{ color:var(--mut); }}
.tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(140px,45%),1fr)); gap:10px; }}
.tile {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.tile .num {{ font-size:30px; font-weight:700; font-variant-numeric:tabular-nums; line-height:1.1; }}
.tile .lbl {{ font-size:12.5px; color:var(--mut); margin-top:2px; }}
.filter {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:14px; }}
.chip {{ border:1px solid var(--line); background:var(--surface); color:var(--mut); border-radius:999px;
        padding:5px 14px; font-size:13.5px; cursor:pointer; }}
.chip[aria-pressed="true"] {{ background:var(--accent); border-color:var(--accent); color:var(--accent-ink); }}
.chip:focus-visible, summary:focus-visible, a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.jobs {{ display:flex; flex-direction:column; gap:14px; }}
.job {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:16px 18px; min-width:0; }}
.job[data-status="mappe"] {{ border-left:4px solid var(--act); }}
.jobkopf {{ display:flex; gap:14px; align-items:flex-start; }}
.score {{ font:700 26px/1.15 ui-monospace,"SF Mono",Consolas,monospace; font-variant-numeric:tabular-nums;
         color:var(--accent); min-width:2.1em; }}
.jobtitel {{ flex:1; min-width:0; }}
.jobtitel h3 {{ font-size:16.5px; }}
.rolle {{ font-size:14.5px; }}
.meta {{ font-size:12.5px; color:var(--mut); margin-top:2px; }}
.pill {{ font-size:12px; font-weight:600; padding:4px 10px; border-radius:999px; white-space:nowrap; }}
.st-action {{ background:var(--act-bg); color:var(--act); }}
.st-good {{ background:var(--good-bg); color:var(--good); }}
.st-bad {{ background:var(--bad-bg); color:var(--bad); }}
.st-info {{ background:var(--info-bg); color:var(--info); }}
.st-neutral, .st-dead {{ background:var(--dead-bg); color:var(--dead); }}
.beg {{ margin-top:10px; font-size:14.5px; }}
.ko {{ margin-top:8px; font-size:13.5px; color:var(--bad); }}
details {{ margin-top:10px; border:1px solid var(--line); border-radius:8px; background:var(--bg); }}
summary {{ cursor:pointer; padding:9px 14px; font-size:13.5px; font-weight:600; color:var(--mut); list-style:none; }}
summary::before {{ content:"▸ "; color:var(--accent); }}
details[open] summary::before {{ content:"▾ "; }}
.dbody {{ padding:4px 16px 14px; font-size:14px; }}
.dbody h4 {{ margin:12px 0 6px; font-size:13px; }} .dbody p {{ margin:7px 0; }}
.dbody ul {{ margin:7px 0 7px 20px; }} .dbody li {{ margin:3px 0; }}
.dbody blockquote {{ border-left:3px solid var(--line); padding-left:12px; color:var(--mut); margin:8px 0; }}
.dbody hr {{ border:0; border-top:1px solid var(--line); margin:12px 0; }}
.tblwrap {{ overflow-x:auto; margin:8px 0; }}
.tblwrap table {{ border-collapse:collapse; font-size:13px; min-width:420px; }}
.tblwrap th, .tblwrap td {{ border:1px solid var(--line); padding:6px 9px; text-align:left; vertical-align:top; }}
.tblwrap th {{ color:var(--mut); font-weight:600; }}
ol.klaeren {{ margin-left:20px; display:flex; flex-direction:column; gap:8px; font-size:14.5px; }}
footer {{ margin-top:40px; padding-top:16px; border-top:1px solid var(--line); color:var(--mut); font-size:13px; }}
footer p {{ margin:4px 0; }}
@media (prefers-reduced-motion: no-preference) {{ details .dbody {{ animation:auf .12s ease-out; }}
  @keyframes auf {{ from {{ opacity:.4; }} to {{ opacity:1; }} }} }}
</style>
<div class="shell">
<header class="top">
  <p class="eyebrow">Jobpilot · privat — Link nicht weitergeben</p>
  <h1>Karriere-Cockpit <b>Moritz</b></h1>
  <div class="standzeile">
    <span>Stand <b>{heute()}</b></span><span>Pipeline aktiv <b>{n_aktiv}</b></span>
    <span>Probezeit-Tag <b>{max(1, (datetime.date.today() - datetime.date(2026, 7, 27)).days + 1)}</b>/14</span>
  </div>
</header>

<section id="handeln">
  <h2><span class="eyebrow">Deine ≤ 15 Minuten</span>Handeln erforderlich</h2>
  <div class="karte"><ul class="act">{handeln_html}</ul></div>
</section>

<section id="zahlen">
  <h2><span class="eyebrow">7 Tage</span>Kennzahlen</h2>
  <div class="tiles">
    <div class="tile"><div class="num">{n_woche}</div><div class="lbl">Stellen ernsthaft geprüft</div></div>
    <div class="tile"><div class="num">{n_mappen}</div><div class="lbl">Mappen zum Review</div></div>
    <div class="tile"><div class="num">{n_aktiv}</div><div class="lbl">aktiv in der Pipeline</div></div>
    <div class="tile"><div class="num">{n_verworfen}</div><div class="lbl">verworfen (mit Begründung)</div></div>
  </div>
</section>

<section id="stellen">
  <h2><span class="eyebrow">nach Score</span>Geprüfte Stellen</h2>
  <div class="filter" role="group" aria-label="Filter">
    <button class="chip" data-f="alle" aria-pressed="true">Alle</button>
    <button class="chip" data-f="aktiv" aria-pressed="false">Aktiv</button>
    <button class="chip" data-f="mappe" aria-pressed="false">Mappen</button>
    <button class="chip" data-f="raus" aria-pressed="false">Aussortiert</button>
  </div>
  <div class="jobs">{''.join(karten)}</div>
</section>

<section id="klaeren">
  <h2><span class="eyebrow">Kurz von dir</span>Offene Klärpunkte</h2>
  <div class="karte"><ol class="klaeren">{klaeren_html or '<li class="mut">Keine.</li>'}</ol></div>
</section>

<footer>
  <p><b>Wo liegt was?</b> Versandfertige PDFs: <code>mappen/&lt;id&gt;/</code> · Volltext-Archiv: <code>jobs/archiv/</code> ·
     Schnellblick im Repo: <code>UEBERSICHT.md</code> · Regeln &amp; Log: <code>notes/</code></p>
  <p>Aktualisiert von Vera nach jedem Arbeitstag. Nichts wird ohne dich versendet — Feedback einfach als Nachricht („Feedback: …").</p>
</footer>
</div>
<script>
const chips = document.querySelectorAll(".chip"), karten = document.querySelectorAll(".job");
const AKTIV = {list(AKTIV)!r};
chips.forEach(c => c.addEventListener("click", () => {{
  chips.forEach(x => x.setAttribute("aria-pressed", x === c ? "true" : "false"));
  const f = c.dataset.f;
  karten.forEach(k => {{
    const s = k.dataset.status;
    k.style.display = (f === "alle" || (f === "aktiv" && AKTIV.includes(s)) ||
                       (f === "mappe" && s === "mappe") ||
                       (f === "raus" && !AKTIV.includes(s))) ? "" : "none";
  }});
}}));
</script>
"""
    ziel = ROOT / "dashboard" / "artifact.html"
    ziel.parent.mkdir(exist_ok=True)
    ziel.write_text(seite, encoding="utf-8")
    print(f"OK: {ziel} ({len(seite) // 1024} KB, {len(jobs)} Stellen, {len(handeln)} Handlungspunkte)")


if __name__ == "__main__":
    main()
