"""Render teaching-materials.v1 to HTML worksheet, PDF, and slides."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

from .contract import IMG_PATTERN


def _esc(text: str) -> str:
    return html.escape(str(text))


def _render_img_placeholders(text: str) -> str:
    """Turn [IMG: desc] into visible print placeholders."""

    def repl(match: re.Match[str]) -> str:
        desc = match.group(1).strip()
        return (
            f'<figure class="img-placeholder">'
            f'<div class="img-box">IMAGE</div>'
            f'<figcaption>[IMG: {_esc(desc)}]</figcaption>'
            f"</figure>"
        )

    return IMG_PATTERN.sub(repl, text or "")


def _lines_to_html(text: str) -> str:
    if not text:
        return ""
    parts = []
    for line in str(text).splitlines():
        line = line.strip()
        if not line:
            parts.append("<br/>")
        else:
            parts.append(f"<p>{_render_img_placeholders(_esc(line))}</p>")
    return "\n".join(parts)


def _list_to_html(items: list[Any]) -> str:
    if not items:
        return ""
    lis = "".join(f"<li>{_render_img_placeholders(_esc(str(x)))}</li>" for x in items)
    return f"<ul>{lis}</ul>"


def render_worksheet_html(package: dict[str, Any]) -> str:
    intake = package.get("intake", {})
    ws = package.get("components", {}).get("worksheet", {})
    summary = package.get("summary", {})
    theme = intake.get("theme") or intake.get("emphasis", "수업")

    sections_html = []
    for sec in ws.get("sections", []):
        if not isinstance(sec, dict):
            continue
        sections_html.append(
            f"<section class='ws-section'>"
            f"<h2>{_esc(sec.get('heading', ''))}</h2>"
            f"{_lines_to_html(sec.get('body', ''))}"
            f"</section>"
        )

    ig = package.get("components", {}).get("intro_game", {})
    disc = package.get("components", {}).get("discussion", {})
    act = package.get("components", {}).get("activity", {})

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(ws.get('title', theme))} — 워크시트</title>
  <style>
    @page {{ size: A4; margin: 18mm; }}
    body {{ font-family: "Malgun Gothic", "Apple SD Gothic Neo", sans-serif; font-size: 11pt; line-height: 1.5; color: #111; }}
    h1 {{ font-size: 18pt; border-bottom: 2px solid #2c5282; padding-bottom: 6px; }}
    h2 {{ font-size: 13pt; color: #2c5282; margin-top: 1.2em; }}
    .meta {{ color: #444; font-size: 10pt; margin-bottom: 1em; }}
    .component {{ margin: 1em 0; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
    .img-placeholder {{ margin: 12px 0; text-align: center; }}
    .img-box {{ height: 120px; background: #f0f4f8; border: 2px dashed #94a3b8; display: flex; align-items: center; justify-content: center; color: #64748b; font-weight: bold; }}
    figcaption {{ font-size: 9pt; color: #475569; margin-top: 4px; }}
    .answer-key {{ font-size: 9pt; color: #666; border-top: 1px dashed #ccc; margin-top: 2em; padding-top: 8px; }}
  </style>
</head>
<body>
  <h1>{_esc(ws.get('title', '오늘의 수업 워크시트'))}</h1>
  <p class="meta">대상: {_esc(intake.get('audience', ''))} · 주제: {_esc(theme)} · 핵심: {_esc(summary.get('key_message', ''))}</p>

  <div class="component">
    <h2>도입게임 — {_esc(ig.get('title', ''))}</h2>
    <p>소요: {_esc(str(ig.get('duration_minutes', '')))}분 · 준비물: {_esc(', '.join(ig.get('materials', [])))}</p>
    {_list_to_html(ig.get('steps', []))}
  </div>

  <div class="component">
    <h2>토의</h2>
    <p>{_esc(disc.get('format', ''))} ({_esc(str(disc.get('duration_minutes', '')))}분)</p>
    {_list_to_html(disc.get('questions', []))}
  </div>

  <div class="component">
    <h2>활동 — {_esc(act.get('title', ''))}</h2>
    {_list_to_html(act.get('steps', []))}
    <h3>정리 질문</h3>
    {_list_to_html(act.get('debrief', []))}
  </div>

  <h2>학생용 워크시트</h2>
  {''.join(sections_html)}

  <p class="answer-key"><strong>교사용 참고:</strong> {_esc(ws.get('leader_answer_key', ''))}</p>
</body>
</html>
"""


def render_slides_html(package: dict[str, Any]) -> str:
    intake = package.get("intake", {})
    theme = intake.get("theme") or intake.get("emphasis", "수업")
    slides = package.get("slides", [])

    slide_divs = []
    for s in sorted(slides, key=lambda x: x.get("order", 0)):
        img = s.get("image_slot", "")
        img_html = _render_img_placeholders(img) if img else ""
        bullets = _list_to_html(s.get("bullets", []))
        slide_divs.append(
            f"""<section class="slide">
  <h2>{_esc(s.get('title', ''))}</h2>
  {bullets}
  {img_html}
  <aside class="notes">{_esc(s.get('speaker_notes', ''))}</aside>
</section>"""
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8"/>
  <title>{_esc(theme)} — 슬라이드</title>
  <style>
    body {{ font-family: "Malgun Gothic", sans-serif; margin: 0; background: #1e293b; }}
    .deck {{ max-width: 960px; margin: 0 auto; padding: 16px; }}
    .slide {{ background: #fff; border-radius: 12px; padding: 32px 40px; margin-bottom: 24px; min-height: 320px; box-shadow: 0 4px 20px rgba(0,0,0,.2); page-break-after: always; }}
    .slide h2 {{ color: #1e40af; font-size: 28pt; margin: 0 0 16px; }}
    .slide ul {{ font-size: 18pt; line-height: 1.6; }}
    .notes {{ font-size: 11pt; color: #64748b; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
    .img-placeholder .img-box {{ height: 140px; }}
    @media print {{ body {{ background: #fff; }} .slide {{ box-shadow: none; border: 1px solid #ccc; }} }}
  </style>
</head>
<body>
  <div class="deck">
    <h1 style="color:#fff;text-align:center;">{ _esc(theme) }</h1>
    {''.join(slide_divs)}
  </div>
</body>
</html>
"""


def html_to_pdf(html_content: str, pdf_path: Path) -> tuple[bool, str | None]:
    """Try xhtml2pdf; return (success, error_message)."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return False, "xhtml2pdf not installed"

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with pdf_path.open("wb") as out_file:
        status = pisa.CreatePDF(html_content, dest=out_file, encoding="utf-8")
    if status.err:
        return False, "xhtml2pdf reported errors"
    return True, None


def write_teaching_artifacts(
    package: dict[str, Any],
    output_dir: Path,
) -> dict[str, str]:
    """Write all files; return artifact path map (relative to output_dir)."""
    print_dir = output_dir / "print"
    slides_dir = output_dir / "slides"
    components_dir = output_dir / "components"
    print_dir.mkdir(parents=True, exist_ok=True)
    slides_dir.mkdir(parents=True, exist_ok=True)
    components_dir.mkdir(parents=True, exist_ok=True)

    worksheet_html = render_worksheet_html(package)
    slides_html = render_slides_html(package)

    ws_path = print_dir / "worksheet.html"
    slides_path = slides_dir / "slides.html"
    ws_path.write_text(worksheet_html, encoding="utf-8")
    slides_path.write_text(slides_html, encoding="utf-8")

    pdf_path = print_dir / "worksheet.pdf"
    pdf_ok, pdf_err = html_to_pdf(worksheet_html, pdf_path)

    paths: dict[str, str] = {
        "worksheet_html": str(ws_path.relative_to(output_dir)),
        "slides_html": str(slides_path.relative_to(output_dir)),
        "package_json": "teaching_materials.v1.json",
        "downstream_json": "teaching_materials.downstream.json",
        "manifest_json": "teaching_materials.manifest.json",
    }
    if pdf_ok:
        paths["worksheet_pdf"] = str(pdf_path.relative_to(output_dir))
    else:
        paths["worksheet_pdf"] = ""
        paths["worksheet_pdf_error"] = pdf_err or "unknown"

    # Component markdown for editors
    for name in ("intro_game", "discussion", "activity", "worksheet"):
        block = package.get("components", {}).get(name, {})
        md = _component_to_md(name, block)
        (components_dir / f"{name}.md").write_text(md, encoding="utf-8")
        paths[f"component_{name}"] = str((components_dir / f"{name}.md").relative_to(output_dir))

    return paths


def _component_to_md(name: str, block: dict[str, Any]) -> str:
    lines = [f"# {name}", ""]
    if name == "intro_game":
        lines.append(f"## {block.get('title', '')}")
        lines.append(f"- 시간: {block.get('duration_minutes')}분")
        lines.append(f"- 준비물: {', '.join(block.get('materials', []))}")
        lines.append("## 진행")
        lines.extend(f"- {s}" for s in block.get("steps", []))
    elif name == "discussion":
        lines.append(f"형식: {block.get('format', '')}")
        lines.append("## 질문")
        lines.extend(f"- {q}" for q in block.get("questions", []))
    elif name == "activity":
        lines.append(f"## {block.get('title', '')}")
        lines.extend(f"- {s}" for s in block.get("steps", []))
        lines.append("## 정리")
        lines.extend(f"- {d}" for d in block.get("debrief", []))
    elif name == "worksheet":
        lines.append(f"## {block.get('title', '')}")
        for sec in block.get("sections", []):
            lines.append(f"### {sec.get('heading', '')}")
            lines.append(sec.get("body", ""))
    lines.append(f"\n{block.get('leader_notes', block.get('leader_answer_key', ''))}")
    return "\n".join(lines) + "\n"
