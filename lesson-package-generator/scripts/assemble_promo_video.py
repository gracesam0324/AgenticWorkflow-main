#!/usr/bin/env python3
"""Assemble promo-video.v1 into MP4 with ffmpeg (images/video cuts + TTS + music).

Expects:
  promo_dir/storyboard.json (or promo_video.v1.json)
  promo_dir/assets/cut_XX.mp4 or cut_XX.png
  promo_dir/subtitles.srt

Usage:
  python scripts/assemble_promo_video.py --promo-dir outputs/promo
  python scripts/assemble_promo_video.py --promo-dir outputs/promo --music outputs/praise/audio/song.mp3
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        msg = "ffmpeg not found in PATH"
        raise RuntimeError(msg)
    return path


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")


def _load_package(promo_dir: Path) -> dict[str, Any]:
    pkg = promo_dir / "promo_video.v1.json"
    if not pkg.is_file():
        raise FileNotFoundError(f"No promo_video.v1.json in {promo_dir}")
    return json.loads(pkg.read_text(encoding="utf-8"))


def _placeholder_png(path: Path, text: str, size: tuple[int, int] = (1920, 1080)) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        path.write_bytes(b"")
        return

    img = Image.new("RGB", size, color=(30, 41, 59))
    draw = ImageDraw.Draw(img)
    draw.text((80, size[1] // 2 - 20), text[:80], fill=(226, 232, 240))
    img.save(path)


def _resolve_cut_asset(assets_dir: Path, cut_id: int) -> Path | None:
    for ext in (".mp4", ".png", ".jpg", ".webp"):
        p = assets_dir / f"cut_{cut_id:02d}{ext}"
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def _segment_from_asset(
    ffmpeg: str,
    asset: Path,
    duration: float,
    out_path: Path,
    work: Path,
) -> None:
    w, h = 1920, 1080
    if asset.suffix.lower() == ".mp4":
        _run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(asset),
                "-t",
                str(duration),
                "-vf",
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                "-r",
                "30",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(out_path),
            ]
        )
    else:
        _run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-i",
                str(asset),
                "-t",
                str(duration),
                "-vf",
                f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
                "-r",
                "30",
                "-pix_fmt",
                "yuv420p",
                str(out_path),
            ]
        )


def _generate_tts_segments(
    package: dict[str, Any],
    work: Path,
    voice: str,
) -> Path | None:
    """Concat narration WAV; return path or None if TTS unavailable."""
    segments = package.get("narration", {}).get("segments", [])
    if not segments:
        return None

    try:
        import asyncio
        import edge_tts
    except ImportError:
        return None

    async def _one(text: str, out: Path) -> None:
        comm = edge_tts.Communicate(text, voice)
        await comm.save(str(out))

    async def _all() -> list[Path]:
        paths: list[Path] = []
        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue
            out = work / f"tts_{seg.get('cut_id', len(paths)):02d}.mp3"
            await _one(text, out)
            paths.append(out)
        return paths

    tts_files = asyncio.run(_all())
    if not tts_files:
        return None

    list_file = work / "tts_list.txt"
    list_file.write_text(
        "\n".join(f"file '{f.resolve().as_posix()}'" for f in tts_files) + "\n",
        encoding="utf-8",
    )
    narration_mp3 = work / "narration.mp3"
    _run(
        [
            _ffmpeg(),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(narration_mp3),
        ]
    )
    return narration_mp3


def assemble(
    promo_dir: Path,
    music_path: Path | None = None,
    voice: str = "ko-KR-SunHiNeural",
    skip_tts: bool = False,
) -> Path:
    ffmpeg = _ffmpeg()
    package = _load_package(promo_dir)
    cuts = package.get("storyboard", {}).get("cuts", [])
    assets_dir = promo_dir / "assets"
    output_dir = promo_dir / "output"
    output_dir.mkdir(exist_ok=True)
    final_path = output_dir / "promo_final.mp4"

    with tempfile.TemporaryDirectory(prefix="promo_asm_") as tmp:
        work = Path(tmp)
        segment_paths: list[Path] = []

        for cut in cuts:
            cid = int(cut["id"])
            dur = float(cut.get("duration_seconds", 5))
            asset = _resolve_cut_asset(assets_dir, cid)
            if asset is None:
                asset = work / f"placeholder_{cid:02d}.png"
                _placeholder_png(asset, cut.get("subtitle", f"Cut {cid}"))
            seg_out = work / f"seg_{cid:02d}.mp4"
            _segment_from_asset(ffmpeg, asset, dur, seg_out, work)
            segment_paths.append(seg_out)

        concat_list = work / "concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.resolve().as_posix()}'" for p in segment_paths) + "\n",
            encoding="utf-8",
        )
        video_only = work / "video_only.mp4"
        _run(
            [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c",
                "copy",
                str(video_only),
            ]
        )

        srt = promo_dir / "subtitles.srt"
        if srt.is_file():
            video_sub = work / "video_sub.mp4"
            srt_esc = srt.resolve().as_posix().replace("\\", "/").replace(":", "\\:")
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_only),
                    "-vf",
                    f"subtitles='{srt_esc}'",
                    "-c:a",
                    "copy",
                    str(video_sub),
                ]
            )
            video_only = video_sub

        narration_audio: Path | None = None
        if not skip_tts:
            narration_audio = _generate_tts_segments(package, work, voice)

        if narration_audio and music_path and music_path.is_file():
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_only),
                    "-i",
                    str(narration_audio),
                    "-i",
                    str(music_path),
                    "-filter_complex",
                    "[1:a]volume=1.0[n];[2:a]volume=0.25[m];[n][m]amix=inputs=2:duration=first[a]",
                    "-map",
                    "0:v",
                    "-map",
                    "[a]",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(final_path),
                ]
            )
        elif narration_audio:
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_only),
                    "-i",
                    str(narration_audio),
                    "-map",
                    "0:v",
                    "-map",
                    "1:a",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(final_path),
                ]
            )
        elif music_path and music_path.is_file():
            _run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(video_only),
                    "-i",
                    str(music_path),
                    "-map",
                    "0:v",
                    "-map",
                    "1:a",
                    "-c:v",
                    "copy",
                    "-c:a",
                    "aac",
                    "-shortest",
                    str(final_path),
                ]
            )
        else:
            shutil.copy2(video_only, final_path)

    return final_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble promo MP4 with ffmpeg")
    parser.add_argument("--promo-dir", type=Path, default=PROJECT_ROOT / "outputs" / "promo")
    parser.add_argument("--music", type=Path, default=None)
    parser.add_argument("--voice", default="ko-KR-SunHiNeural")
    parser.add_argument("--skip-tts", action="store_true")
    args = parser.parse_args()

    music = args.music
    if music is None:
        default_music = PROJECT_ROOT / "outputs" / "praise" / "audio" / "song.mp3"
        if default_music.is_file():
            music = default_music

    out = assemble(args.promo_dir, music, args.voice, args.skip_tts)
    print(json.dumps({"assembled_mp4": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
