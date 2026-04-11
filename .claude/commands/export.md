---
description: "Trigger manuscript export (PDF + EPUB)"
---

# /export — Trigger Manuscript Export

Trigger the book build pipeline to produce PDF and EPUB from approved chapters.

## Execute These Steps

### Step 1: Read Pipeline State

Use the **Read tool** on `.claude/state.yaml`.

Extract:
- `workflow.current_step` — must be >= 9 for export
- `workflow.chapters` — all chapter entries with their status
- `workflow.build` — any previous build info

### Step 2: Verify All Chapters Are Approved

Iterate through all chapter entries in `workflow.chapters`. For each chapter, check that `status` is either `"approved"` or `"final"`.

- **If ANY chapter is not approved/final**:
  Output to user:
  ```
  Export blocked: Not all chapters are approved.

  Unapproved chapters:
    ch-{N}: {status}
    ch-{M}: {status}
    ...

  Action: Review and approve these chapters first, then re-run /export.
  ```
  **STOP here.**

- **If all approved/final**: Continue.

### Step 3: Verify Story Bible Exists

Use the **Glob tool** to check `outputs/story-bible/story_bible.json` exists.

- **If missing**: Report "Story Bible not found. It must exist before export." **STOP.**

### Step 4: Check Prerequisite Tools

Use the **Bash tool** to check for pandoc and xelatex:
```bash
pandoc --version 2>&1 | head -1; xelatex --version 2>&1 | head -1
```

Record availability. Missing tools affect which formats can be produced (see error handling).

### Step 5: Run Cross-Chapter Consistency Check

Use the **Bash tool**:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/validate_consistency.py --project-dir .
```

- **If critical issues found**: Display the report to user. Recommend fixing before export, but do NOT hard-stop — let user decide.
- **If clean or warnings only**: Continue.

### Step 6: Build Manuscript

Use the **Bash tool** to run the build:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && .venv/bin/python3 scripts/build_book.py --project-dir . --format all
```

This produces:
- `outputs/builds/book_latest.pdf` — Screen-optimized PDF (A5, memoir class)
- `outputs/builds/book_latest.epub` — EPUB3 with custom CSS
- `outputs/builds/manuscript.md` — Combined markdown manuscript
- Build manifest with word counts

**If pandoc is missing**: Fall back to markdown-only output.
**If xelatex is missing**: Skip PDF, produce EPUB + markdown only.

### Step 7: Post-Build Validation

Use the **Bash tool** to verify outputs:
```bash
cd /Users/cys/Desktop/AIagentsAutomation/Writingbook-AgenticWorkflow/autobiography-generator && ls -la outputs/builds/book_latest.pdf outputs/builds/book_latest.epub outputs/builds/manuscript.md 2>&1
```

Check each file exists and is non-empty (size > 0).

If epubcheck is available, run it:
```bash
epubcheck outputs/builds/book_latest.epub 2>&1
```

### Step 8: Update state.yaml (SOT)

Use the **Edit tool** on `.claude/state.yaml` to update:
```yaml
workflow:
  current_step: 9.5
  build:
    last_build_date: "{ISO 8601 timestamp}"
    pdf_path: "outputs/builds/book_latest.pdf"
    epub_path: "outputs/builds/book_latest.epub"
    build_status: "completed"
  export:
    status: "completed"
    output_paths:
      - "outputs/builds/book_latest.pdf"
      - "outputs/builds/book_latest.epub"
      - "outputs/builds/manuscript.md"
```

Only include paths for files that were actually produced (omit PDF path if xelatex was missing, etc.).

### Step 9: Display Report

Output the following directly to the user:

```
Export Complete
===============
PDF:        {path} ({file size})       [or "Skipped — XeLaTeX not available"]
EPUB:       {path} ({file size})       [or "Skipped — pandoc not available"]
Manuscript: {path} ({word count} words)
Chapters:   {count}
---------------
Next: H7 Final Approval — review the exported files and provide final sign-off.
```

## Arguments

None. Export format is controlled by `state.yaml.export.format` and tool availability.

## Error Handling

| Error | Tool to Use | Action |
|-------|-------------|--------|
| Unapproved chapters exist | Read tool on state.yaml | List them, abort export |
| pandoc not installed | Bash tool | Skip PDF/EPUB, produce markdown-only, warn user |
| xelatex not installed | Bash tool | Skip PDF, produce EPUB + markdown, warn user |
| build_book.py fails | Bash tool output | Display full error, attempt EPUB-only fallback |
| EPUB validation fails | Bash tool | Produce EPUB without validation, warn user |
| Story Bible missing | Glob tool | Report error, STOP |
| Consistency check finds critical issues | Bash tool output | Display report, ask user whether to proceed |

## Constraints

- The build pipeline includes front matter (title page, dedication, preface) and back matter (acknowledgments, about the author)
- Table of contents is auto-generated
- Chapter ordering follows the story bible chapter plan
- Font requirements: EB Garamond (preferred) or TeX Gyre Termes (fallback)
- This command writes to state.yaml ONLY after build succeeds (Step 7 validated)
