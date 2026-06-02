# Step 3 — Praise / Worship (찬양) · praise-worship.v1

Create **100% original** Korean worship lyrics for **middle school (중등부)** plus **one** Suno-ready music prompt.

## Inputs

- `intake`: `body_text` (본문), `theme` (테마), `audience`
- `teaching_downstream`: output from step 1 (교보재) — use `key_message`, `theme`, `discussion_questions` for alignment
- `lesson_plan`: optional

## Rules

1. Respond with **only one JSON object** (no markdown fences).
2. `"format": "praise-worship.v1"`.
3. Lyrics: **verse1 → chorus → verse2 → chorus → bridge → chorus**. No copied existing hymns.
4. Language: Korean, middle-school vocabulary, singable lines (4–8 syllables per line preferred).
5. `music_generation`: exactly **one** `prompt_combined` string for Suno custom mode; plus `prompt_structured` with `genre`, `mood`, `bpm` (integer), `vocal`, `instruments`, `style_tags`.
6. Do **not** claim to generate audio — `delivery: "external"`, provider `suno`.
7. Align with `teaching_downstream.key_message` and `intake.theme`; echo `body_text` theme without quoting entire passage verbatim in every line.

## JSON shape

```json
{
  "format": "praise-worship.v1",
  "meta": { "target_grade_band": "middle_school", "audio_provider": "suno", "lyrics_original": true },
  "inputs": { "body_text": "", "theme": "", "audience": "", "key_message": "" },
  "song": {
    "title": "",
    "structure": ["verse1", "chorus", "verse2", "chorus", "bridge", "chorus"],
    "lyrics": {
      "verse1": { "label": "1절", "lines": [] },
      "chorus": { "label": "후렴", "lines": [], "repeat": true },
      "verse2": { "label": "2절", "lines": [] },
      "bridge": { "label": "브릿지", "lines": [] }
    },
    "scripture_anchor": "",
    "copyright_notice": ""
  },
  "music_generation": {
    "provider": "suno",
    "delivery": "external",
    "prompt_combined": "",
    "prompt_structured": { "genre": "", "mood": "", "bpm": 90, "vocal": "", "instruments": "", "style_tags": [] },
    "workflow": []
  },
  "leader_notes": { "when_to_use": "", "suggested_key": "", "tempo": "", "teaching_tip": "" }
}
```
