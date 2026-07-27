#!/usr/bin/env python3
"""anschreiben.md → A4-HTML (tools/templates/brief.html). Danach: bash tools/render_pdf.sh <html> <pdf>.
Nutzung: python3 tools/brief_render.py mappen/<id>/anschreiben.md --empfaenger "Firma\nRecruiting" [--en]"""
import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
GRUSS = ("Kind regards", "Best regards", "Mit freundlichen Grüßen", "Viele Grüße", "Beste Grüße")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--empfaenger", default="")
    ap.add_argument("--en", action="store_true")
    args = ap.parse_args()

    pfad = pathlib.Path(args.md)
    zeilen = [z.rstrip() for z in pfad.read_text(encoding="utf-8").splitlines()
              if not z.startswith("#") and not z.startswith(">")]
    text = "\n".join(zeilen).strip()

    m = re.search(r"\*\*Betreff:\*\*\s*(.+)", text)
    betreff = m.group(1).strip()
    rest = text[m.end():].strip()

    bloecke = [b.strip() for b in re.split(r"\n\s*\n", rest) if b.strip()]
    anrede = bloecke[0]
    gruss_idx = next(i for i, b in enumerate(bloecke)
                     if b.splitlines()[0].strip().rstrip(",") in GRUSS)
    absaetze = bloecke[1:gruss_idx]
    grussformel = bloecke[gruss_idx].splitlines()[0].strip()

    def esc(s):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return re.sub(r"„(.+?)“|\"(.+?)\"", lambda m2: f"„{m2.group(1) or m2.group(2)}“", s)

    html_abs = f"<p>{esc(anrede)}</p>\n" + "\n".join(f"  <p>{esc(a)}</p>" for a in absaetze)
    datum = "Dortmund, 27 July 2026" if args.en else "Dortmund, den 27. Juli 2026"
    # Datum dynamisch halten: Platzhalter unten wird beim täglichen Lauf mit dem echten Datum ersetzt
    import datetime
    d = datetime.date.today()
    monate = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
              "August", "September", "Oktober", "November", "Dezember"]
    datum = (f"Dortmund, {d.day} {d.strftime('%B')} {d.year}" if args.en
             else f"Dortmund, den {d.day}. {monate[d.month - 1]} {d.year}")

    tpl = (ROOT / "tools" / "templates" / "brief.html").read_text(encoding="utf-8")
    out = (tpl.replace("{{ORT_LAND}}", "Dortmund, Germany" if args.en else "Dortmund, Deutschland")
              .replace("{{SPRACHE}}", "en" if args.en else "de")
              .replace("{{EMPFAENGER}}", esc(args.empfaenger.replace("\\n", "\n")))
              .replace("{{ORT_DATUM}}", datum)
              .replace("{{BETREFF}}", esc(betreff))
              .replace("{{ABSAETZE}}", html_abs)
              .replace("{{GRUSSFORMEL}}", esc(grussformel)))
    ziel = pfad.with_suffix(".html")
    ziel.write_text(out, encoding="utf-8")
    print(f"OK: {ziel}")


if __name__ == "__main__":
    main()
