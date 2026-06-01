# Step 4 — Promo Video (홍보영상) · promo-video.v1

Create a **30–45 second** middle-school **retreat (수련회)** promo plan.

## Inputs

- `intake`: theme, body_text, audience
- `teaching_downstream`, `praise_downstream`: align message and tone

## Output rules

1. Respond with **only one JSON object** (no markdown fences).
2. `"format": "promo-video.v1"`.
3. Total `storyboard.cuts[].duration_seconds` sum **between 30 and 45**.
4. Each cut must include:
   - `id`, `duration_seconds`, `scene_description`
   - `visual_type`: `video_ai` or `image_ai`
   - `video_prompt` (for Runway/Pika/Kling etc.)
   - `image_prompt` (fallback still)
   - `subtitle`, `narration`
5. `narration.full_script` = concatenation of segment texts.
6. `subtitles` array with `cut_id`, `text`, `start_seconds`, `end_seconds` (no gaps).
7. Korean, youth-appropriate, energetic but not cheesy.

## JSON shape

```json
{
  "format": "promo-video.v1",
  "meta": { "total_duration_seconds": 38, "aspect_ratio": "16:9" },
  "inputs": { "theme": "", "body_text": "", "audience": "" },
  "narration": {
    "full_script": "",
    "language": "ko-KR",
    "segments": [{ "id": "n1", "cut_id": 1, "text": "", "duration_seconds": 5 }]
  },
  "subtitles": [{ "cut_id": 1, "text": "", "start_seconds": 0, "end_seconds": 5 }],
  "storyboard": {
    "cuts": [],
    "video_ai_workflow": []
  },
  "cta": { "text": "", "on_screen": "" },
  "assembly": { "tool": "ffmpeg", "script": "scripts/assemble_promo_video.py" }
}
```
