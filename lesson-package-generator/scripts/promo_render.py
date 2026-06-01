"""Write promo artifacts: storyboard JSON, SRT, narration MD, per-cut prompts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def render_srt(package: dict[str, Any]) -> str:
    lines: list[str] = []
    for i, sub in enumerate(package.get("subtitles", []), start=1):
        start = sub.get("start_seconds", 0)
        end = sub.get("end_seconds", start + 3)
        lines.append(str(i))
        lines.append(f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}")
        lines.append(sub.get("text", ""))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_narration_md(package: dict[str, Any]) -> str:
    nar = package.get("narration", {})
    lines = [
        f"# 내레이션 스크립트 — {package.get('inputs', {}).get('theme', '')}",
        "",
        f"**전체 ({package.get('meta', {}).get('total_duration_seconds', '?')}초)**",
        "",
        nar.get("full_script", ""),
        "",
        "## 컷별",
        "",
    ]
    for seg in nar.get("segments", []):
        lines.append(f"### Cut {seg.get('cut_id')}")
        lines.append(seg.get("text", ""))
        lines.append("")
    return "\n".join(lines)


def render_storyboard_md(package: dict[str, Any]) -> str:
    lines = ["# 스토리보드", ""]
    for cut in package.get("storyboard", {}).get("cuts", []):
        lines.append(f"## Cut {cut['id']} ({cut.get('duration_seconds')}s)")
        lines.append(f"- **장면**: {cut.get('scene_description')}")
        lines.append(f"- **자막**: {cut.get('subtitle')}")
        lines.append(f"- **영상 AI**: `{cut.get('video_prompt', '')}`")
        lines.append(f"- **이미지 fallback**: `{cut.get('image_prompt', '')}`")
        lines.append("")
    return "\n".join(lines)


def write_promo_artifacts(package: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = output_dir / "assets"
    assets.mkdir(exist_ok=True)
    prompts_dir = output_dir / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    output_sub = output_dir / "output"
    output_sub.mkdir(exist_ok=True)

    storyboard_path = output_dir / "storyboard.json"
    storyboard_path.write_text(
        json.dumps(package.get("storyboard", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (output_dir / "subtitles.srt").write_text(render_srt(package), encoding="utf-8")
    (output_dir / "narration_script.md").write_text(render_narration_md(package), encoding="utf-8")
    (output_dir / "storyboard.md").write_text(render_storyboard_md(package), encoding="utf-8")

    for cut in package.get("storyboard", {}).get("cuts", []):
        cid = int(cut["id"])
        prompt_text = (
            f"# Cut {cid} — {cut.get('visual_type', 'video_ai')}\n\n"
            f"## Scene\n{cut.get('scene_description')}\n\n"
            f"## Video AI prompt\n{cut.get('video_prompt', '')}\n\n"
            f"## Image fallback prompt\n{cut.get('image_prompt', '')}\n\n"
            f"## Subtitle\n{cut.get('subtitle')}\n\n"
            f"Save video as: assets/cut_{cid:02d}.mp4\n"
            f"Or image as: assets/cut_{cid:02d}.png\n"
        )
        (prompts_dir / f"cut_{cid:02d}_prompts.md").write_text(prompt_text, encoding="utf-8")

    (assets / "README.txt").write_text(
        "Place video AI outputs here:\n"
        "  cut_01.mp4, cut_02.mp4, ...\n"
        "Or still images:\n"
        "  cut_01.png, cut_02.png, ...\n"
        "Then run: python scripts/assemble_promo_video.py --promo-dir <this parent>\n",
        encoding="utf-8",
    )

    return {
        "package_json": "promo_video.v1.json",
        "downstream_json": "promo_video.downstream.json",
        "manifest_json": "promo_video.manifest.json",
        "storyboard_json": "storyboard.json",
        "subtitles_srt": "subtitles.srt",
        "narration_md": "narration_script.md",
        "storyboard_md": "storyboard.md",
        "assets_dir": "assets",
        "assembled_mp4": "output/promo_final.mp4",
    }
