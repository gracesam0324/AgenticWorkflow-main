/* prompt.js — 찬양(praise-worship.v1) system prompt + payload.
 * Ported from anthem-generator/agents/prompts/anthem.md. */

const ANTHEM_PROMPT = `Create 100% original Korean worship lyrics for middle school (중등부) plus one Suno-ready music prompt.

Rules:
1. Respond with only one JSON object (no markdown fences).
2. "format": "praise-worship.v1".
3. Lyrics structure: verse1 -> chorus -> verse2 -> chorus -> bridge -> chorus. No copied hymns.
4. Korean, middle-school vocabulary, singable lines (4-8 syllables preferred).
5. music_generation: exactly one prompt_combined string for Suno custom mode; plus prompt_structured with genre, mood, bpm (int), vocal, instruments, style_tags.
6. Do not claim to generate audio — delivery: "external", provider "suno".
7. Align with intake.theme; echo body_text theme without quoting the whole passage in every line.

JSON shape:
{
  "format": "praise-worship.v1",
  "meta": { "target_grade_band": "middle_school", "audio_provider": "suno", "lyrics_original": true },
  "inputs": { "body_text": "", "theme": "", "audience": "", "key_message": "" },
  "song": {
    "title": "",
    "structure": ["verse1","chorus","verse2","chorus","bridge","chorus"],
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
    "provider": "suno", "delivery": "external", "prompt_combined": "",
    "prompt_structured": { "genre": "", "mood": "", "bpm": 90, "vocal": "", "instruments": "", "style_tags": [] }
  },
  "leader_notes": { "when_to_use": "", "suggested_key": "", "tempo": "", "teaching_tip": "" }
}`;

function buildIntake({ body, theme, audience }) {
  return { body_text: body, theme: theme, audience: audience || '중등부', emphasis: theme, volume: '45', locale: 'ko' };
}

function buildPayload(intake) {
  return {
    intake,
    teaching_downstream: null,
    lesson_plan: null,
    required_format: 'praise-worship.v1',
    requirements: {
      original_lyrics_only: true,
      structure: ['verse1', 'chorus', 'verse2', 'chorus', 'bridge', 'chorus'],
      grade_band: 'middle_school',
      music_prompt_provider: 'suno',
      single_combined_music_prompt: true,
    },
  };
}
