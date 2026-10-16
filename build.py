"""Build index.html for GitHub Pages from src/page.html.

src/page.html is the page exactly as it is published as a Claude Artifact:
no doctype, head or body of its own, because the Artifact host wraps it in
a skeleton with a small reset. GitHub Pages serves files as they are, so
this script adds the same skeleton and reset around it.

    python3 build.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "page.html"
OUT = ROOT / "index.html"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="Load your holdings by ISIN and weight. Eight AI committee members propose and rate trades, and the CIO rules with new weights, limit prices and expiry.">
<style>
:root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; font: 14px/1.4 system-ui, -apple-system, sans-serif; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""


def build() -> None:
    page = SRC.read_text(encoding="utf-8")
    cut = page.index("</style>") + len("</style>")
    head, body = page[:cut], page[cut:]
    OUT.write_text(f"{HEAD}{head}\n</head>\n<body>{body}\n</body>\n</html>\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
