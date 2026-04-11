#!/usr/bin/env python3
"""
Book Build Pipeline — Pandoc-based PDF and EPUB generation

Assembles all approved chapters into a complete manuscript, then produces:
1. PDF via XeLaTeX with custom memoir template (screen A5 or print 6x9)
2. EPUB3 with custom CSS, cover image, and Dublin Core metadata
3. Combined markdown manuscript (single file)
4. Print-ready PDF variant for Amazon KDP / IngramSpark (optional)

Usage:
    python3 scripts/build_book.py --project-dir . --format pdf
    python3 scripts/build_book.py --project-dir . --format epub
    python3 scripts/build_book.py --project-dir . --format all
    python3 scripts/build_book.py --project-dir . --format all --draft
    python3 scripts/build_book.py --project-dir . --format print   # 6x9 KDP-ready
    python3 scripts/build_book.py --project-dir . --format all --validate

Prerequisites:
    - pandoc (>= 3.0)
    - xelatex (for PDF — from TeX Live or MacTeX)
    - Fonts: EB Garamond (preferred) or TeX Gyre Termes (fallback)
    - epubcheck (optional, for EPUB validation)

Exit codes:
    0 — build successful
    1 — missing prerequisites or build failure
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------

def check_prerequisites(formats: list[str]) -> list[str]:
    """Check that required tools are installed."""
    missing = []

    # Always need pandoc
    try:
        result = subprocess.run(
            ["pandoc", "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            missing.append("pandoc")
        else:
            version_line = result.stdout.split("\n")[0]
            print(f"  Found: {version_line}", file=sys.stderr)
    except FileNotFoundError:
        missing.append("pandoc (install: brew install pandoc)")

    # XeLaTeX for PDF
    if any(f in formats for f in ("pdf", "print", "all")):
        try:
            result = subprocess.run(
                ["xelatex", "--version"], capture_output=True, text=True
            )
            if result.returncode != 0:
                missing.append("xelatex")
        except FileNotFoundError:
            missing.append("xelatex (install: brew install --cask mactex)")

    # epubcheck for validation
    if "validate" in formats:
        epubcheck_found = False
        # Try direct command
        try:
            result = subprocess.run(
                ["epubcheck", "--version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                epubcheck_found = True
        except FileNotFoundError:
            pass

        # Try java -jar fallback
        if not epubcheck_found:
            try:
                result = subprocess.run(
                    ["java", "-version"], capture_output=True, text=True
                )
                if result.returncode != 0:
                    missing.append("epubcheck (install: brew install epubcheck)")
            except FileNotFoundError:
                missing.append(
                    "epubcheck (install: brew install epubcheck)"
                )

    return missing


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def load_json(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def read_text(path: str) -> str | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Chapter Discovery
# ---------------------------------------------------------------------------

def find_approved_chapters(
    project_dir: str, include_drafts: bool = False
) -> list[dict]:
    """Find all chapters ready for building, in order."""
    chapters_dir = os.path.join(project_dir, "outputs", "chapters")
    if not os.path.isdir(chapters_dir):
        return []

    # Load state to check approval status
    state = None
    # §21.6: .claude/state.yaml is the SOLE authoritative SOT
    state_path = os.path.join(project_dir, ".claude", "state.yaml")
    if not os.path.isfile(state_path):
        state_path = os.path.join(project_dir, "state.yaml")  # legacy fallback
    try:
        import yaml

        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
    except (ImportError, FileNotFoundError, Exception):
        state = None

    chapters_status = {}
    if state:
        workflow = state.get("workflow", state)
        chapters_status = workflow.get("chapters", {})

    # Find latest version of each chapter
    pattern = re.compile(r"ch(\d{2})_draft_v(\d+)\.md$")
    latest: dict[int, int] = {}

    for f in os.listdir(chapters_dir):
        m = pattern.match(f)
        if m:
            ch_num = int(m.group(1))
            version = int(m.group(2))
            if ch_num not in latest or version > latest[ch_num]:
                latest[ch_num] = version

    chapters = []
    for ch_num in sorted(latest.keys()):
        version = latest[ch_num]
        ch_key = f"ch-{ch_num}"
        status = chapters_status.get(ch_key, {}).get("status", "drafted")

        # Only include approved chapters unless --draft flag
        if not include_drafts and status not in ("approved", "final"):
            print(
                f"  Skipping chapter {ch_num} (status: {status}, not approved)",
                file=sys.stderr,
            )
            continue

        prose_path = os.path.join(
            chapters_dir, f"ch{ch_num:02d}_draft_v{version}.md"
        )
        prose = read_text(prose_path)
        if prose:
            chapters.append(
                {
                    "chapter_number": ch_num,
                    "version": version,
                    "status": status,
                    "path": prose_path,
                    "content": prose,
                }
            )

    return chapters


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

def load_metadata(project_dir: str) -> dict:
    """Load book metadata from epub-metadata.yaml or story bible."""
    metadata = {
        "title": "Untitled Autobiography",
        "author": ["Unknown Author"],
        "date": str(date.today().year),
        "lang": "en",
    }

    # Try epub-metadata.yaml first
    meta_path = os.path.join(project_dir, "templates", "epub-metadata.yaml")
    try:
        import yaml

        with open(meta_path, "r", encoding="utf-8") as f:
            meta_yaml = yaml.safe_load(f)
        if meta_yaml:
            metadata.update({k: v for k, v in meta_yaml.items() if v})
    except (ImportError, FileNotFoundError, Exception):
        pass

    # Fall back to story bible
    sb_path = os.path.join(
        project_dir, "outputs", "story-bible", "story_bible.json"
    )
    sb = load_json(sb_path)
    if sb:
        sb_meta = sb.get("meta", {})
        if sb_meta.get("title"):
            metadata.setdefault("title", sb_meta["title"])
        subject = sb.get("subject", {})
        if subject.get("full_name"):
            metadata.setdefault("author", [subject["full_name"]])

    return metadata


# ---------------------------------------------------------------------------
# Manuscript Assembly
# ---------------------------------------------------------------------------

def assemble_manuscript(chapters: list[dict], metadata: dict) -> str:
    """Combine all chapters into a single markdown manuscript."""
    parts = []

    # YAML front matter
    parts.append("---")
    for key, value in metadata.items():
        if isinstance(value, list):
            parts.append(f"{key}:")
            for item in value:
                parts.append(f'  - "{item}"')
        elif isinstance(value, bool):
            parts.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, str) and "\n" in value:
            parts.append(f"{key}: |")
            for line in value.split("\n"):
                parts.append(f"  {line}")
        else:
            if isinstance(value, str):
                parts.append(f'{key}: "{value}"')
            else:
                parts.append(f"{key}: {value}")
    parts.append("---\n")

    # Chapters
    for ch in chapters:
        content = ch["content"]

        # Normalize scene breaks: convert "---" between paragraphs
        # to a horizontal rule (Pandoc standard). The Lua filter
        # (scene-breaks.lua) then converts HR to \scenebreak for LaTeX
        # or styled <div> for EPUB.
        lines = content.split("\n")
        processed_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped in ("---", "***", "* * *", "- - -"):
                # Check context: if between paragraphs (not YAML front matter
                # or headers), keep as horizontal rule
                prev_is_para = (
                    i > 0
                    and lines[i - 1].strip()
                    and not lines[i - 1].strip().startswith("#")
                )
                next_is_para = (
                    i < len(lines) - 1
                    and lines[i + 1].strip()
                    and not lines[i + 1].strip().startswith("#")
                )
                if prev_is_para or next_is_para:
                    # Use standard Pandoc horizontal rule (three or more
                    # hyphens with blank lines around)
                    processed_lines.append("")
                    processed_lines.append("---")
                    processed_lines.append("")
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)

        parts.append("\n".join(processed_lines))
        parts.append("\n\n")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Build: PDF (screen / A5)
# ---------------------------------------------------------------------------

def build_pdf(
    manuscript_path: str,
    output_path: str,
    project_dir: str,
    metadata: dict,
) -> bool:
    """Build PDF using pandoc + xelatex + memoir template."""
    template_path = os.path.join(project_dir, "templates", "memoir.latex")

    cmd = [
        "pandoc",
        manuscript_path,
        "-o",
        output_path,
        "--pdf-engine=xelatex",
        f"--template={template_path}",
        "--top-level-division=chapter",
        "--number-sections=false",
        "--wrap=auto",
    ]

    # TOC
    if metadata.get("toc", True):
        cmd.append("--toc")
        toc_depth = metadata.get("toc-depth", 1)
        cmd.append(f"--toc-depth={toc_depth}")

    # Lua filters
    lua_dir = os.path.join(project_dir, "templates", "lua")
    for lua_filter in ["scene-breaks.lua", "dropcaps.lua", "epigraphs.lua"]:
        filter_path = os.path.join(lua_dir, lua_filter)
        if os.path.isfile(filter_path):
            cmd.extend(["--lua-filter", filter_path])

    # Graphics path
    graphics_path = metadata.get("graphics-path", "")
    if graphics_path:
        cmd.extend(["-V", f"graphics-path={graphics_path}"])

    # CJK support
    if metadata.get("cjk", False):
        cmd.extend(["-V", "cjk=true"])

    # Micro-typography
    if metadata.get("microtypography", False):
        cmd.extend(["-V", "microtypography=true"])

    # Line spacing
    line_stretch = metadata.get("line-stretch", "")
    if line_stretch:
        cmd.extend(["-V", f"line-stretch={line_stretch}"])

    # Bibliography
    bib = metadata.get("bibliography", "")
    if bib and os.path.isfile(os.path.join(project_dir, bib)):
        cmd.extend(["--citeproc", f"--bibliography={bib}"])
        csl = metadata.get("csl", "")
        if csl:
            cmd.extend([f"--csl={csl}"])

    print(f"  Building PDF (screen): {os.path.basename(output_path)}", file=sys.stderr)
    print(f"  Command: {' '.join(cmd[:6])}...", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"  PDF build FAILED:\n{result.stderr[:3000]}", file=sys.stderr)
            return False

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(
            f"  PDF built successfully: {output_path} ({size_mb:.1f} MB)",
            file=sys.stderr,
        )
        return True

    except subprocess.TimeoutExpired:
        print("  PDF build timed out (> 5 minutes)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(
            "  pandoc not found — install with: brew install pandoc",
            file=sys.stderr,
        )
        return False


# ---------------------------------------------------------------------------
# Build: PDF (print / 6x9 KDP)
# ---------------------------------------------------------------------------

def build_print_pdf(
    manuscript_path: str,
    output_path: str,
    project_dir: str,
    metadata: dict,
) -> bool:
    """Build print-ready PDF using 6x9 memoir-print template."""
    template_path = os.path.join(project_dir, "templates", "memoir-print.latex")

    if not os.path.isfile(template_path):
        print(
            f"  Print template not found: {template_path}",
            file=sys.stderr,
        )
        return False

    cmd = [
        "pandoc",
        manuscript_path,
        "-o",
        output_path,
        "--pdf-engine=xelatex",
        f"--template={template_path}",
        "--top-level-division=chapter",
        "--number-sections=false",
        "--wrap=auto",
    ]

    # TOC
    if metadata.get("toc", True):
        cmd.append("--toc")
        toc_depth = metadata.get("toc-depth", 1)
        cmd.append(f"--toc-depth={toc_depth}")

    # Lua filters
    lua_dir = os.path.join(project_dir, "templates", "lua")
    for lua_filter in ["scene-breaks.lua", "dropcaps.lua", "epigraphs.lua"]:
        filter_path = os.path.join(lua_dir, lua_filter)
        if os.path.isfile(filter_path):
            cmd.extend(["--lua-filter", filter_path])

    # Inner margin (varies by page count)
    inner_margin = metadata.get("inner-margin", "0.75in")
    cmd.extend(["-V", f"inner-margin={inner_margin}"])

    # Graphics path
    graphics_path = metadata.get("graphics-path", "")
    if graphics_path:
        cmd.extend(["-V", f"graphics-path={graphics_path}"])

    # CJK support
    if metadata.get("cjk", False):
        cmd.extend(["-V", "cjk=true"])

    # Bibliography
    bib = metadata.get("bibliography", "")
    if bib and os.path.isfile(os.path.join(project_dir, bib)):
        cmd.extend(["--citeproc", f"--bibliography={bib}"])
        csl = metadata.get("csl", "")
        if csl:
            cmd.extend([f"--csl={csl}"])

    print(
        f"  Building PDF (print 6x9): {os.path.basename(output_path)}",
        file=sys.stderr,
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"  Print PDF build FAILED:\n{result.stderr[:3000]}", file=sys.stderr)
            return False

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(
            f"  Print PDF built successfully: {output_path} ({size_mb:.1f} MB)",
            file=sys.stderr,
        )
        return True

    except subprocess.TimeoutExpired:
        print("  Print PDF build timed out (> 5 minutes)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(
            "  pandoc not found — install with: brew install pandoc",
            file=sys.stderr,
        )
        return False


# ---------------------------------------------------------------------------
# Build: EPUB
# ---------------------------------------------------------------------------

def build_epub(
    manuscript_path: str,
    output_path: str,
    project_dir: str,
    metadata: dict,
) -> bool:
    """Build EPUB3 using pandoc with custom CSS."""
    css_path = os.path.join(project_dir, "templates", "epub.css")

    cmd = [
        "pandoc",
        manuscript_path,
        "-o",
        output_path,
        "-t",
        "epub3",
        "--top-level-division=chapter",
        "--number-sections=false",
        "--wrap=auto",
        "--epub-chapter-level=1",
    ]

    # TOC
    if metadata.get("toc", True):
        cmd.append("--toc")
        toc_depth = metadata.get("toc-depth", 1)
        cmd.append(f"--toc-depth={toc_depth}")

    # CSS
    if os.path.isfile(css_path):
        cmd.extend(["--css", css_path])

    # Cover image
    cover = metadata.get("cover-image", "")
    if cover:
        cover_abs = (
            cover
            if os.path.isabs(cover)
            else os.path.join(project_dir, cover)
        )
        if os.path.isfile(cover_abs):
            cmd.extend(["--epub-cover-image", cover_abs])
        else:
            print(
                f"  Warning: cover image not found: {cover}",
                file=sys.stderr,
            )

    # Lua filters (scene-breaks and epigraphs work for EPUB too)
    lua_dir = os.path.join(project_dir, "templates", "lua")
    for lua_filter in ["scene-breaks.lua", "epigraphs.lua"]:
        filter_path = os.path.join(lua_dir, lua_filter)
        if os.path.isfile(filter_path):
            cmd.extend(["--lua-filter", filter_path])

    # Bibliography
    bib = metadata.get("bibliography", "")
    if bib and os.path.isfile(os.path.join(project_dir, bib)):
        cmd.extend(["--citeproc", f"--bibliography={bib}"])
        csl = metadata.get("csl", "")
        if csl:
            cmd.extend([f"--csl={csl}"])

    print(
        f"  Building EPUB: {os.path.basename(output_path)}", file=sys.stderr
    )

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"  EPUB build FAILED:\n{result.stderr[:3000]}", file=sys.stderr)
            return False

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(
            f"  EPUB built successfully: {output_path} ({size_mb:.1f} MB)",
            file=sys.stderr,
        )
        return True

    except subprocess.TimeoutExpired:
        print("  EPUB build timed out (> 2 minutes)", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(
            "  pandoc not found — install with: brew install pandoc",
            file=sys.stderr,
        )
        return False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_epub(epub_path: str) -> dict:
    """Validate EPUB using epubcheck. Returns validation results."""
    result_info = {"valid": False, "errors": 0, "warnings": 0, "messages": []}

    if not os.path.isfile(epub_path):
        result_info["messages"].append(f"EPUB file not found: {epub_path}")
        return result_info

    try:
        result = subprocess.run(
            ["epubcheck", epub_path],
            capture_output=True,
            text=True,
            timeout=60,
        )

        result_info["valid"] = result.returncode == 0
        output = result.stdout + result.stderr

        # Parse error/warning counts
        for line in output.split("\n"):
            if "error" in line.lower():
                result_info["errors"] += 1
            if "warning" in line.lower():
                result_info["warnings"] += 1
            if line.strip():
                result_info["messages"].append(line.strip())

        status = "PASSED" if result_info["valid"] else "FAILED"
        print(
            f"  EPUB validation: {status} "
            f"({result_info['errors']} errors, "
            f"{result_info['warnings']} warnings)",
            file=sys.stderr,
        )

    except FileNotFoundError:
        print(
            "  epubcheck not found — skipping validation "
            "(install: brew install epubcheck)",
            file=sys.stderr,
        )
        result_info["messages"].append("epubcheck not installed")
    except subprocess.TimeoutExpired:
        result_info["messages"].append("epubcheck timed out")

    return result_info


def validate_pdf(pdf_path: str) -> dict:
    """Basic PDF validation checks."""
    result_info = {"valid": False, "checks": []}

    if not os.path.isfile(pdf_path):
        result_info["checks"].append("PDF file not found")
        return result_info

    size_bytes = os.path.getsize(pdf_path)

    # Check file size (KDP max 650 MB)
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > 650:
        result_info["checks"].append(
            f"FAIL: File size {size_mb:.1f} MB exceeds KDP limit of 650 MB"
        )
    else:
        result_info["checks"].append(
            f"OK: File size {size_mb:.1f} MB (KDP limit: 650 MB)"
        )

    # Check if file is valid PDF (magic bytes)
    try:
        with open(pdf_path, "rb") as f:
            header = f.read(5)
            if header == b"%PDF-":
                result_info["checks"].append("OK: Valid PDF header")
            else:
                result_info["checks"].append("FAIL: Invalid PDF header")
    except OSError:
        result_info["checks"].append("FAIL: Cannot read PDF file")

    # Try pdfinfo if available
    try:
        result = subprocess.run(
            ["pdfinfo", pdf_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if any(
                    k in line
                    for k in ["Page size", "Pages", "PDF version"]
                ):
                    result_info["checks"].append(f"INFO: {line.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try pdffonts to check embedded fonts
    try:
        result = subprocess.run(
            ["pdffonts", pdf_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if len(lines) > 2:
                unembedded = [
                    l
                    for l in lines[2:]
                    if l.strip() and "no" in l.lower().split()[-1:]
                ]
                if unembedded:
                    result_info["checks"].append(
                        f"WARN: {len(unembedded)} font(s) may not be embedded"
                    )
                else:
                    result_info["checks"].append(
                        "OK: All fonts appear to be embedded"
                    )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        result_info["checks"].append(
            "SKIP: pdffonts not available (install poppler-utils)"
        )

    result_info["valid"] = not any(
        c.startswith("FAIL") for c in result_info["checks"]
    )

    status = "PASSED" if result_info["valid"] else "ISSUES FOUND"
    print(f"  PDF validation: {status}", file=sys.stderr)
    for check in result_info["checks"]:
        print(f"    {check}", file=sys.stderr)

    return result_info


# ---------------------------------------------------------------------------
# Image DPI Check
# ---------------------------------------------------------------------------

def check_image_dpi(project_dir: str, min_dpi: int = 300) -> list[dict]:
    """Check DPI of images in assets directory. Requires ImageMagick."""
    issues = []
    photos_dir = os.path.join(project_dir, "assets", "photos")

    if not os.path.isdir(photos_dir):
        return issues

    try:
        identify_cmd = shutil.which("identify")
        if not identify_cmd:
            return issues

        for f in os.listdir(photos_dir):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".tiff", ".tif")):
                fpath = os.path.join(photos_dir, f)
                try:
                    result = subprocess.run(
                        [
                            "identify",
                            "-format",
                            "%x %y",
                            "-units",
                            "PixelsPerInch",
                            fpath,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        parts = result.stdout.strip().split()
                        if len(parts) >= 2:
                            x_dpi = float(parts[0])
                            y_dpi = float(parts[1])
                            if x_dpi < min_dpi or y_dpi < min_dpi:
                                issues.append(
                                    {
                                        "file": f,
                                        "x_dpi": x_dpi,
                                        "y_dpi": y_dpi,
                                        "required": min_dpi,
                                    }
                                )
                except (subprocess.TimeoutExpired, ValueError):
                    pass

    except Exception:
        pass

    if issues:
        print(
            f"  Warning: {len(issues)} image(s) below {min_dpi} DPI:",
            file=sys.stderr,
        )
        for issue in issues:
            print(
                f"    {issue['file']}: {issue['x_dpi']:.0f}x{issue['y_dpi']:.0f} DPI",
                file=sys.stderr,
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build book from chapter drafts"
    )
    parser.add_argument(
        "--project-dir", default=".", help="Project root directory"
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "epub", "print", "markdown", "all"],
        default="all",
        help="Output format(s) to build",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Include non-approved chapters (for preview builds)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation checks on output files",
    )
    parser.add_argument(
        "--check-images",
        action="store_true",
        help="Check image DPI for print readiness",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    build_dir = os.path.join(project_dir, "outputs", "builds")
    os.makedirs(build_dir, exist_ok=True)

    print("=" * 60, file=sys.stderr)
    print("  BOOK BUILD PIPELINE", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Check prerequisites
    formats_needed = [args.format]
    if args.validate:
        formats_needed.append("validate")
    if any(f in formats_needed for f in ("pdf", "print", "all")):
        missing = check_prerequisites(formats_needed)
        if missing:
            print(
                f"\nMissing prerequisites: {', '.join(missing)}",
                file=sys.stderr,
            )
            if args.format in ("pdf", "print"):
                sys.exit(1)
            else:
                print(
                    "  Skipping PDF build; will attempt other formats",
                    file=sys.stderr,
                )

    # Find chapters
    print(f"\nScanning chapters...", file=sys.stderr)
    chapters = find_approved_chapters(project_dir, include_drafts=args.draft)
    if not chapters:
        print("No chapters found for building.", file=sys.stderr)
        print(
            "  Use --draft to include non-approved chapters.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Found {len(chapters)} chapter(s):", file=sys.stderr)
    for ch in chapters:
        word_count = len(ch["content"].split())
        print(
            f"  Ch {ch['chapter_number']:02d} v{ch['version']} "
            f"({ch['status']}, {word_count:,} words)",
            file=sys.stderr,
        )

    # Load metadata
    metadata = load_metadata(project_dir)
    print(f"\nBook: {metadata.get('title', 'Untitled')}", file=sys.stderr)
    print(
        f"Author: {', '.join(metadata.get('author', ['Unknown']))}",
        file=sys.stderr,
    )

    # Check images if requested
    if args.check_images:
        print(f"\nChecking image DPI...", file=sys.stderr)
        check_image_dpi(project_dir)

    # Assemble manuscript
    print(f"\nAssembling manuscript...", file=sys.stderr)
    manuscript = assemble_manuscript(chapters, metadata)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Always write combined markdown
    manuscript_path = os.path.join(build_dir, f"manuscript_{timestamp}.md")
    with open(manuscript_path, "w", encoding="utf-8") as f:
        f.write(manuscript)

    # Also write a "latest" copy
    latest_manuscript = os.path.join(build_dir, "manuscript_latest.md")
    shutil.copy2(manuscript_path, latest_manuscript)
    print(f"  Manuscript: {manuscript_path}", file=sys.stderr)

    results = {"manuscript": manuscript_path, "chapters": len(chapters)}
    formats_built = ["markdown"]
    validation_results = {}

    # Build PDF (screen)
    if args.format in ("pdf", "all"):
        print(f"\n--- PDF (screen) ---", file=sys.stderr)
        pdf_path = os.path.join(build_dir, f"book_{timestamp}.pdf")
        if build_pdf(manuscript_path, pdf_path, project_dir, metadata):
            results["pdf"] = pdf_path
            formats_built.append("pdf")
            shutil.copy2(pdf_path, os.path.join(build_dir, "book_latest.pdf"))
            if args.validate:
                validation_results["pdf"] = validate_pdf(pdf_path)

    # Build PDF (print / 6x9)
    if args.format in ("print", "all"):
        print(f"\n--- PDF (print 6x9) ---", file=sys.stderr)
        print_path = os.path.join(build_dir, f"book_print_{timestamp}.pdf")
        if build_print_pdf(
            manuscript_path, print_path, project_dir, metadata
        ):
            results["print_pdf"] = print_path
            formats_built.append("print")
            shutil.copy2(
                print_path, os.path.join(build_dir, "book_print_latest.pdf")
            )
            if args.validate:
                validation_results["print_pdf"] = validate_pdf(print_path)

    # Build EPUB
    if args.format in ("epub", "all"):
        print(f"\n--- EPUB ---", file=sys.stderr)
        epub_path = os.path.join(build_dir, f"book_{timestamp}.epub")
        if build_epub(manuscript_path, epub_path, project_dir, metadata):
            results["epub"] = epub_path
            formats_built.append("epub")
            shutil.copy2(
                epub_path, os.path.join(build_dir, "book_latest.epub")
            )
            if args.validate:
                validation_results["epub"] = validate_epub(epub_path)

    # Final report
    total_words = sum(len(ch["content"].split()) for ch in chapters)
    results["total_words"] = total_words
    results["formats_built"] = formats_built
    results["build_time"] = datetime.now().isoformat()
    if validation_results:
        results["validation"] = validation_results

    # Write build manifest
    manifest_path = os.path.join(
        build_dir, f"build_manifest_{timestamp}.json"
    )
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'=' * 60}", file=sys.stderr)
    print(f"  BUILD COMPLETE", file=sys.stderr)
    print(f"{'=' * 60}", file=sys.stderr)
    print(f"  Formats: {', '.join(formats_built)}", file=sys.stderr)
    print(f"  Total words: {total_words:,}", file=sys.stderr)
    print(f"  Manifest: {manifest_path}", file=sys.stderr)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
