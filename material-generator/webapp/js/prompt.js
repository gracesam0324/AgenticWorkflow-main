/* prompt.js — 교보재(teaching-materials.v1) system prompt + payload.
 * Ported from material-generator/agents/prompts/material.md. */

const MATERIAL_PROMPT = `You create middle school (중등부) teaching resources as structured JSON only.

Output rules:
1. Respond with a single JSON object — no markdown fences, no commentary.
2. "format": "teaching-materials.v1". "meta.target_grade_band": "middle_school".
3. Include all four components: intro_game, discussion, activity, worksheet.
4. Include slides array (5-8 slides) with order, title, bullets, speaker_notes, image_slot.
5. For every suggested illustration use exactly: [IMG: description] embedded in strings.
6. Language: Korean, middle-school reading level.
7. worksheet.sections must be printable (clear headings, fill-in blanks).
8. summary.key_message must align with intake.theme and body_text.

JSON shape:
{
  "format": "teaching-materials.v1",
  "meta": { "target_grade_band": "middle_school", "locale": "ko" },
  "intake": { "body_text": "", "theme": "", "audience": "" },
  "summary": { "title": "", "key_message": "", "duration_minutes": 45 },
  "components": {
    "intro_game": { "title": "", "duration_minutes": 0, "materials": [], "steps": [], "leader_notes": "" },
    "discussion": { "format": "", "duration_minutes": 0, "questions": [], "leader_notes": "" },
    "activity": { "title": "", "duration_minutes": 0, "steps": [], "debrief": [] },
    "worksheet": { "title": "", "sections": [{ "heading": "", "body": "" }], "leader_answer_key": "" }
  },
  "slides": [{ "order": 1, "title": "", "bullets": [], "speaker_notes": "", "image_slot": "[IMG: ...]" }]
}`;

function buildIntake({ body, theme, audience, volume }) {
  return {
    body_text: body,
    theme: theme,
    audience: audience || '중등부',
    volume: volume || '45',
    emphasis: theme,
    locale: 'ko',
  };
}

function buildPayload(intake) {
  return {
    intake,
    lesson_plan: null,
    required_format: 'teaching-materials.v1',
    target_grade_band: 'middle_school',
  };
}
