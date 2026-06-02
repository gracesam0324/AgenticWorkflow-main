"""Write praise-worship.v1 artifacts (lyrics MD, Suno prompt files)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def render_full_lyrics_md(package: dict[str, Any]) -> str:
    song = package.get("song", {})
    lines = [
        f"# {song.get('title', '찬양')}",
        "",
        f"*{song.get('copyright_notice', '')}*",
        "",
    ]
    if song.get("scripture_anchor"):
        lines.extend([f"> 본문 맥락: {song['scripture_anchor']}", ""])

    order = song.get("structure", list(song.get("lyrics", {}).keys()))
    lyrics = song.get("lyrics", {})
    for key in order:
        block = lyrics.get(key, {})
        if not block:
            continue
        label = block.get("label", key)
        lines.append(f"## {label}")
        for ln in block.get("lines", []):
            lines.append(ln)
        if block.get("repeat"):
            lines.append("_(반복)_")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_leader_notes_md(package: dict[str, Any]) -> str:
    notes = package.get("leader_notes", {})
    mg = package.get("music_generation", {})
    lines = [
        "# 인도자 노트",
        "",
        f"- **사용 시점**: {notes.get('when_to_use', '')}",
        f"- **조성**: {notes.get('suggested_key', '')}",
        f"- **템포**: {notes.get('tempo', '')}",
        f"- **팁**: {notes.get('teaching_tip', '')}",
        "",
        "## 음원 받기 (Suno)",
        "",
    ]
    for step in mg.get("workflow", []):
        lines.append(f"- {step}")
    lines.append("")
    lines.append(f"프롬프트 파일: `music/suno_prompt.txt`")
    return "\n".join(lines) + "\n"


def write_praise_artifacts(package: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    lyrics_dir = output_dir / "lyrics"
    music_dir = output_dir / "music"
    audio_dir = output_dir / "audio"
    lyrics_dir.mkdir(exist_ok=True)
    music_dir.mkdir(exist_ok=True)
    audio_dir.mkdir(exist_ok=True)

    (lyrics_dir / "full_lyrics.md").write_text(
        render_full_lyrics_md(package), encoding="utf-8"
    )
    (output_dir / "leader_notes.md").write_text(
        render_leader_notes_md(package), encoding="utf-8"
    )

    mg = package.get("music_generation", {})
    (music_dir / "suno_prompt.txt").write_text(
        mg.get("prompt_combined", "") + "\n", encoding="utf-8"
    )
    (music_dir / "music_prompt.json").write_text(
        json.dumps(mg.get("prompt_structured", {}), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (audio_dir / "README.txt").write_text(
        "Place Suno-generated audio here as song.mp3 after external generation.\n",
        encoding="utf-8",
    )

    return {
        "package_json": "praise_worship.v1.json",
        "downstream_json": "praise_worship.downstream.json",
        "manifest_json": "praise_worship.manifest.json",
        "lyrics_md": str((lyrics_dir / "full_lyrics.md").relative_to(output_dir)),
        "suno_prompt_txt": str((music_dir / "suno_prompt.txt").relative_to(output_dir)),
        "music_prompt_json": str((music_dir / "music_prompt.json").relative_to(output_dir)),
        "leader_notes_md": "leader_notes.md",
        "audio_placeholder": str((audio_dir / "README.txt").relative_to(output_dir)),
    }
