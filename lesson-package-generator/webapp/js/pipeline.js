/* pipeline.js — orchestration ported from scripts/orchestrator.py:run_pipeline.
 * intake -> step1 lesson_plan (MAIN) -> [teaching, praise, promo] -> step5 self-check.
 * Supplementary steps consume the frozen lesson_plan, chained like the CLI. */

async function runPipeline(intake, opts, onStep, signal) {
  const result = { intake, lessonPlan: null, teaching: null, praise: null, promo: null, selfCheck: null };

  // Step 1 — lesson plan (MAIN, mandatory)
  onStep('plan', 'active');
  const planText = await callClaude({ system: PROMPTS.step1_lesson_plan, user: payloadStep1(intake), signal });
  result.lessonPlan = normalizeLessonPlan(parseJsonResponse(planText), intake);
  const lpErrors = validateLessonPlan(result.lessonPlan);
  onStep('plan', 'done', lpErrors.length ? `검증 경고 ${lpErrors.length}건` : '8개 섹션 완성');

  // Step 2 — teaching (optional)
  if (opts.teaching) {
    onStep('teaching', 'active');
    const t = await callClaude({ system: PROMPTS.step2_teaching, user: payloadStep2(intake, result.lessonPlan), signal });
    result.teaching = parseJsonResponse(t);
    onStep('teaching', 'done', '도입게임·토의·활동·워크시트');
  } else onStep('teaching', 'skip', '건너뜀');

  // Step 3 — praise (optional)
  if (opts.praise) {
    onStep('praise', 'active');
    const p = await callClaude({ system: PROMPTS.step3_praise, user: payloadStep3(intake, result.lessonPlan, result.teaching), signal });
    result.praise = parseJsonResponse(p);
    onStep('praise', 'done', '오리지널 가사 + Suno 프롬프트');
  } else onStep('praise', 'skip', '건너뜀');

  // Step 4 — promo (optional)
  if (opts.promo) {
    onStep('promo', 'active');
    const v = await callClaude({ system: PROMPTS.step4_promo, user: payloadStep4(intake, result.lessonPlan, result.teaching, result.praise), signal });
    result.promo = parseJsonResponse(v);
    onStep('promo', 'done', '스토리보드 + 컷별 프롬프트');
  } else onStep('promo', 'skip', '건너뜀');

  // Step 5 — deterministic self-check (always)
  onStep('check', 'active');
  const ran = { teaching: !!opts.teaching, praise: !!opts.praise, promo: !!opts.promo };
  const modules = { teaching: result.teaching, praise: result.praise, promo: result.promo };
  result.selfCheck = runSelfCheck(intake, result.lessonPlan, ran, modules);
  onStep('check', result.selfCheck.verdict === 'PASS' ? 'done' : 'error',
    `판정 ${result.selfCheck.verdict} · 통과 ${result.selfCheck.summary.passed}/${result.selfCheck.summary.total}`);

  return result;
}

/* Ensure required envelope fields (mirror lesson_plan_generate._finalize). */
function normalizeLessonPlan(plan, intake) {
  plan.step_id = 'step1_lesson_plan';
  plan.format = 'lesson-plan.v1';
  plan.meta = plan.meta || {};
  if (plan.meta.volume_minutes == null) plan.meta.volume_minutes = parseMinutes(intake.volume);
  plan.intake_ref = plan.intake_ref || {
    body_text: intake.body_text, audience: intake.audience, volume: intake.volume, emphasis: intake.emphasis,
  };
  return plan;
}
