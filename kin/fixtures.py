"""Synthetic fixture: ground-truth documents rendered to HTML, PDF and PNG.

Each `fixtures/documents/<id>.json` holds the fields a correct transcription should read (they
double as source spans: every value is printed verbatim), approved excerpts, categories and the
expected per-role views. Templates live in `fixtures/templates/`; `make fixtures` writes
`fixtures/renders/`. Rendering needs the `data` extra (`make setup-data`).
"""

from __future__ import annotations

import html
import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT = Path("fixtures")


def load_documents(root: Path = ROOT) -> list[dict[str, Any]]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((Path(root) / "documents").glob("*.json"))
    ]


def load_expected(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((Path(root) / "expected.json").read_text(encoding="utf-8"))


def render_html(doc: dict[str, Any], root: Path = ROOT) -> str:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

    env = Environment(
        loader=FileSystemLoader(Path(root) / "templates"),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=StrictUndefined,
    )
    return env.get_template(f"{doc['type']}.html.j2").render(doc=doc)


def printed_text(markup: str) -> str:
    """Visible text of rendered HTML, whitespace collapsed (for span checks)."""
    body = re.sub(r"(?is)<(style|title)\b.*?</\1>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()


def strings(value: Any) -> Iterator[str]:
    """Every string leaf of a field value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def render_all(root: Path = ROOT, dpi: int = 150) -> list[Path]:
    """Write `<id>.pdf` and `<id>-p<n>.png` for every document; return the written paths."""
    import pypdfium2 as pdfium
    from weasyprint import HTML

    out = Path(root) / "renders"
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for doc in load_documents(root):
        for stale in out.glob(f"{doc['id']}-p*.png"):
            stale.unlink()
        pdf_path = out / f"{doc['id']}.pdf"
        HTML(string=render_html(doc, root), base_url=str(Path(root) / "templates")).write_pdf(
            pdf_path
        )
        written.append(pdf_path)
        pdf = pdfium.PdfDocument(str(pdf_path))
        for i in range(len(pdf)):
            png_path = out / f"{doc['id']}-p{i + 1}.png"
            pdf[i].render(scale=dpi / 72).to_pil().save(png_path, optimize=True)
            written.append(png_path)
        pdf.close()
    return written
