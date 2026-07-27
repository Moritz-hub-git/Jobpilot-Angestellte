#!/usr/bin/env bash
# HTML → einseitiges A4-PDF via Chromium headless. Bricht mit Warnung ab, wenn >1 Seite.
# Nutzung: bash tools/render_pdf.sh eingabe.html ausgabe.pdf [--mehrseitig-ok]
set -euo pipefail
IN="$1"; OUT="$2"; MULTI="${3:-}"
BIN=/opt/pw-browsers/chromium
"$BIN" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf="$OUT" "file://$(realpath "$IN")" 2>/dev/null
SEITEN=$(python3 - "$OUT" <<'EOF'
import sys
from pypdf import PdfReader
print(len(PdfReader(sys.argv[1]).pages))
EOF
)
echo "→ $OUT ($SEITEN Seite(n))"
if [ "$SEITEN" != "1" ] && [ "$MULTI" != "--mehrseitig-ok" ]; then
  echo "FEHLER: $SEITEN Seiten statt 1 — Inhalt kürzen oder Layout anpassen." >&2
  exit 2
fi
