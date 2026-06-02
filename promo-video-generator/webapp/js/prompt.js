/* prompt.js — 홍보영상(promo-video.v1) system prompt + payload.
 * Ported from promo-video-generator/agents/prompts/promo.md. */

const PROMO_PROMPT = `Create a 30-45 second middle-school retreat (수련회) promo plan.

Output rules:
1. Respond with only one JSON object (no markdown fences).
2. "format": "promo-video.v1".
3. Total storyboard.cuts[].duration_seconds sum between 30 and 45.
4. Each cut: id, duration_seconds, scene_description, visual_type ("video_ai" or "image_ai"), video_prompt, image_prompt, subtitle, narration.
5. narration.full_script = concatenation of segment texts.
6. subtitles array with cut_id, text, start_seconds, end_seconds (no gaps).
7. Korean, youth-appropriate, energetic but not cheesy. Align CTA/hook with intake.theme.

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

function buildIntake({ theme, body, audience }) {
  return { theme: theme, body_text: body || '', audience: audience || '중등부', emphasis: theme, volume: '45', locale: 'ko' };
}

function buildPayload(intake) {
  return {
    intake,
    teaching_downstream: null,
    praise_downstream: null,
    lesson_plan: null,
    required_format: 'promo-video.v1',
    constraints: { duration_seconds_min: 30, duration_seconds_max: 45, target: 'middle_school_retreat_promo', visual_delivery: 'video_ai_per_cut' },
  };
}
