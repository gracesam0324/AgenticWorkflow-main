/* prompts.js — step system prompts + user payloads ported from
 * lesson-package-generator/agents/prompts/* and scripts/*_generate.py.
 * Browser build: every step instructs strict JSON output. */

const PROMPTS = {};

PROMPTS.step1_lesson_plan = `You are an expert curriculum designer for Korean church youth (middle/high school).
Design a complete, time-boxed, teach-ready lesson plan from the intake.
A teacher must be able to run the entire session using ONLY this plan.

Output STRICT JSON only — no markdown fences, no prose. Shape:
{
  "step_id": "step1_lesson_plan",
  "format": "lesson-plan.v1",
  "meta": { "volume_minutes": <int>, "target_grade_band": "middle_school", "locale": "ko" },
  "intake_ref": { "body_text": "...", "audience": "...", "volume": "...", "emphasis": "..." },
  "sections": {
    "learning_objectives": ["...", "..."],
    "introduction": "...",
    "body_development": "...",
    "key_message": "...",
    "application": "...",
    "discussion_questions": ["...", "...", "..."],
    "closing": "...",
    "time_allocation": [ { "segment": "도입", "minutes": <int> } ]
  }
}

Hard requirements (validated):
1. All eight sections present and non-empty.
2. learning_objectives >= 2 measurable outcomes.
3. discussion_questions >= 3, ordered individual -> group.
4. key_message: one memorable takeaway (1-3 sentences).
5. body_development anchored to body_text with >= 3 explicit references; >= 80 chars.
6. time_allocation minutes sum = volume_minutes (within +-5).
7. emphasis reflected in key_message or application.
8. Vocabulary appropriate for audience (middle-school by default).
Write all content in Korean. Output JSON only.`;

PROMPTS.step2_teaching = `You create middle school (중등부) teaching resources as structured JSON only.

Output rules:
1. Respond with a single JSON object — no markdown fences, no commentary.
2. "format": "teaching-materials.v1". "meta.target_grade_band": "middle_school".
3. Include all four components: intro_game, discussion, activity, worksheet.
4. Include slides array (5-8 slides) with order, title, bullets, speaker_notes, image_slot.
5. For every suggested illustration use exactly: [IMG: description] embedded in strings.
6. Language: Korean, middle-school reading level.
7. worksheet.sections must be printable (clear headings, fill-in blanks).
8. summary.key_message must align with lesson_plan.sections.key_message and body_text.

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

PROMPTS.step3_praise = `Create 100% original Korean worship lyrics for middle school (중등부) plus one Suno-ready music prompt.

Rules:
1. Respond with only one JSON object (no markdown fences).
2. "format": "praise-worship.v1".
3. Lyrics structure: verse1 -> chorus -> verse2 -> chorus -> bridge -> chorus. No copied hymns.
4. Korean, middle-school vocabulary, singable lines (4-8 syllables preferred).
5. music_generation: exactly one prompt_combined string for Suno custom mode; plus prompt_structured with genre, mood, bpm (int), vocal, instruments, style_tags.
6. Do not claim to generate audio — delivery: "external", provider "suno".
7. Align with lesson_plan.sections.key_message and intake.theme; echo body_text theme without quoting the whole passage in every line.

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

PROMPTS.step4_promo = `Create a 30-45 second middle-school retreat (수련회) promo plan.

Output rules:
1. Respond with only one JSON object (no markdown fences).
2. "format": "promo-video.v1".
3. Total storyboard.cuts[].duration_seconds sum between 30 and 45.
4. Each cut: id, duration_seconds, scene_description, visual_type ("video_ai" or "image_ai"), video_prompt, image_prompt, subtitle, narration.
5. narration.full_script = concatenation of segment texts.
6. subtitles array with cut_id, text, start_seconds, end_seconds (no gaps).
7. Korean, youth-appropriate, energetic but not cheesy. Align CTA/hook with lesson_plan key_message and learning_objectives.

JSON shape:
{
  "format": "promo-video.v1",
  "meta": { "total_duration_seconds": 38, "aspect_ratio": "16:9" },
  "inputs": { "theme": "", "body_text": "", "audience": "", "key_message": "" },
  "narration": { "full_script": "", "language": "ko-KR", "segments": [{ "id": "n1", "cut_id": 1, "text": "", "duration_seconds": 5 }] },
  "subtitles": [{ "cut_id": 1, "text": "", "start_seconds": 0, "end_seconds": 5 }],
  "storyboard": { "cuts": [{ "id": 1, "duration_seconds": 5, "scene_description": "", "visual_type": "video_ai", "video_prompt": "", "image_prompt": "", "subtitle": "", "narration": "" }] },
  "cta": { "text": "", "on_screen": "" }
}`;

/* ---- user payload builders (mirror scripts/*_generate.py) ---- */

function payloadStep1(intake) {
  return {
    intake,
    required_format: 'lesson-plan.v1',
    target_grade_band: 'middle_school',
    volume_minutes: parseMinutes(intake.volume),
  };
}

function payloadStep2(intake, lessonPlan) {
  return {
    intake,
    lesson_plan: lessonPlan,
    required_format: 'teaching-materials.v1',
    target_grade_band: 'middle_school',
  };
}

function payloadStep3(intake, lessonPlan, teaching) {
  return {
    intake,
    lesson_plan: lessonPlan,
    teaching_downstream: teaching ? teachingDownstream(teaching) : null,
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

function payloadStep4(intake, lessonPlan, teaching, praise) {
  return {
    intake,
    lesson_plan: lessonPlan,
    teaching_downstream: teaching ? teachingDownstream(teaching) : null,
    praise_downstream: praise ? praiseDownstream(praise) : null,
    required_format: 'promo-video.v1',
    constraints: { duration_seconds_min: 30, duration_seconds_max: 45, target: 'middle_school_retreat_promo', visual_delivery: 'video_ai_per_cut' },
  };
}

/* slim downstream payloads (mirror build_downstream_payload) */
function teachingDownstream(t) {
  return {
    format: t.format,
    key_message: t.summary && t.summary.key_message,
    theme: t.intake && t.intake.theme,
    discussion_questions: (t.components && t.components.discussion && t.components.discussion.questions) || [],
  };
}
function praiseDownstream(p) {
  const song = p.song || {};
  const chorus = (song.lyrics && song.lyrics.chorus && song.lyrics.chorus.lines) || [];
  return {
    format: p.format,
    song_title: song.title || '',
    key_message: (p.inputs && p.inputs.key_message) || '',
    chorus_preview: chorus.slice(0, 4),
    suno_prompt: (p.music_generation && p.music_generation.prompt_combined) || '',
  };
}

/* parse "80" / "45분×2" -> minutes (mirror lesson_plan_contract.parse_minutes) */
function parseMinutes(volume) {
  if (volume == null) return 45;
  if (typeof volume === 'number') return volume;
  const text = String(volume);
  const combo = text.match(/(\d+)\s*분?\s*[×xX*]\s*(\d+)/);
  if (combo) return parseInt(combo[1], 10) * parseInt(combo[2], 10);
  const m = text.match(/\d+/);
  return m ? parseInt(m[0], 10) : 45;
}
