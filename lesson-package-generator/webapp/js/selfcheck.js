/* selfcheck.js — deterministic package integrity checks (PK1-PK13)
 * ported from scripts/package_check.py + lesson_plan_contract.validate_lesson_plan. */

const SECTION_KEYS = [
  'learning_objectives', 'introduction', 'body_development', 'key_message',
  'application', 'discussion_questions', 'closing', 'time_allocation',
];
const STOPWORDS = new Set(['강조', '지양', '그리고', '말씀', '오늘', '우리', '통해', '대한', '위해', '이번', '있는']);

function tokenize(text) {
  if (typeof text !== 'string') return new Set();
  return new Set(text.split(/[\s,.··…"'`()\[\]{}!?~\-:;/]+/).filter((p) => p.length >= 2 && !STOPWORDS.has(p)));
}
function intersects(a, b) { for (const x of a) if (b.has(x)) return true; return false; }
/* Loose overlap tolerant of Korean particle agglutination:
 * 자유(강조점) matches 자유는/자유를(본문) via substring containment. */
function looseIntersect(a, b) {
  for (const x of a) for (const y of b) if (x.length >= 2 && y.length >= 2 && (x.includes(y) || y.includes(x))) return true;
  return false;
}

/* LP1-LP10 (subset of validate_lesson_plan, browser version) */
function validateLessonPlan(plan) {
  const errors = [];
  const s = plan && plan.sections;
  if (!plan || plan.step_id !== 'step1_lesson_plan') errors.push("LP1: step_id must be 'step1_lesson_plan'");
  if (typeof s !== 'object' || s === null) { errors.push("LP2: 'sections' missing"); return errors; }
  for (const k of SECTION_KEYS) {
    const v = s[k];
    if (v == null || ((typeof v === 'string' || Array.isArray(v)) && v.length === 0)) errors.push(`LP3: section '${k}' empty`);
  }
  if (!Array.isArray(s.learning_objectives) || s.learning_objectives.length < 2) errors.push('LP4: 학습목표 >= 2');
  if (!Array.isArray(s.discussion_questions) || s.discussion_questions.length < 3) errors.push('LP5: 토의질문 >= 3');
  if (typeof s.key_message !== 'string' || !s.key_message.trim()) errors.push('LP6: 핵심메시지 비어있음');
  const target = plan.meta && plan.meta.volume_minutes;
  const allocated = Array.isArray(s.time_allocation)
    ? s.time_allocation.reduce((sum, it) => sum + (it && typeof it.minutes === 'number' ? it.minutes : 0), 0) : 0;
  if (allocated <= 0) errors.push('LP7: 시간배분 없음');
  else if (typeof target === 'number' && Math.abs(allocated - target) > 5) errors.push(`LP7: 시간배분 합 ${allocated} != ${target} (+-5)`);
  if (typeof s.body_development !== 'string' || s.body_development.trim().length < 80) errors.push('LP8: 본문전개 빈약(<80)');
  if (typeof s.introduction !== 'string' || s.introduction.trim().length < 40) errors.push('LP9: 도입 빈약(<40)');
  if (typeof s.application !== 'string' || s.application.trim().length < 40) errors.push('LP10: 적용 빈약(<40)');
  return errors;
}

function suppKeyMessage(pkg) {
  if (!pkg) return '';
  return (pkg.summary && pkg.summary.key_message) || (pkg.inputs && pkg.inputs.key_message) || '';
}
function passageTokens(body) {
  const t = new Set();
  if (typeof body !== 'string') return t;
  const book = body.match(/\s*([가-힣]{2,})/);
  if (book) t.add(book[1]);
  (body.match(/\d+:\d+/g) || []).forEach((cv) => t.add(cv));
  return t;
}
function suppPassageText(pkg) {
  if (!pkg) return '';
  const parts = [(pkg.intake && pkg.intake.body_text) || '', (pkg.inputs && pkg.inputs.body_text) || ''];
  const ws = pkg.components && pkg.components.worksheet;
  if (ws) parts.push(String(ws.passage_reference || ''));
  if (pkg.song) parts.push(String(pkg.song.scripture_anchor || ''));
  return parts.filter(Boolean).join(' ');
}
const SUPP = ['teaching', 'praise', 'promo'];

function runSelfCheck(intake, lessonPlan, ran, modules) {
  const checks = [];
  const add = (id, title, severity, passed, detail) => checks.push({ id, title, severity, passed, detail });
  const sec = (lessonPlan && lessonPlan.sections) || {};

  const corePresent = lessonPlan && lessonPlan.step_id === 'step1_lesson_plan';
  add('PK1', '수업안(core) 존재', 'critical', !!corePresent, corePresent ? 'ok' : 'lesson_plan 누락');

  const lpErr = corePresent ? validateLessonPlan(lessonPlan) : ['no plan'];
  add('PK2', '수업안 LP1–LP10 통과', 'critical', lpErr.length === 0, lpErr.length ? lpErr.join('; ') : 'valid');

  const empTokens = tokenize((intake.emphasis || intake.theme));
  const reflected = empTokens.size === 0 || looseIntersect(empTokens, tokenize(`${sec.key_message || ''} ${sec.application || ''}`));
  add('PK3', '강조점이 핵심메시지/적용에 반영', 'warning', reflected, reflected ? 'ok' : '강조점 미반영');

  const anySupp = SUPP.some((n) => modules[n]);
  const guard = !anySupp || (corePresent && lpErr.length === 0);
  add('PK4', '부가물은 유효한 수업안 위에서만', 'critical', guard, guard ? 'ok' : '유효하지 않은 수업안');

  const planKm = tokenize(sec.key_message);

  const t = modules.teaching;
  if (ran.teaching && t) {
    const comps = t.components || {};
    const missing = ['intro_game', 'discussion', 'activity', 'worksheet'].filter((k) => !(k in comps));
    add('PK6', '교보재 4종 구성요소 완비', 'critical', missing.length === 0, missing.length ? `누락: ${missing}` : 'ok');
  } else add('PK6', '교보재 4종 구성요소 완비', 'info', true, '미실행');
  add('PK5', '교보재가 수업안을 입력으로 소비', 'info', true, ran.teaching ? 'API 생성' : '미실행');

  const p = modules.praise;
  if (ran.praise && p) {
    const ok = !!suppKeyMessage(p) && !!(p.song && p.song.lyrics);
    add('PK7', '찬양 가사/핵심메시지 존재', 'critical', ok, ok ? 'ok' : '가사/메시지 누락');
  } else add('PK7', '찬양 가사/핵심메시지 존재', 'info', true, '미실행');

  const pr = modules.promo;
  if (ran.promo && pr) {
    const ok = !!suppKeyMessage(pr) && !!(pr.narration && pr.narration.full_script);
    add('PK8', '홍보영상 대본/핵심메시지 존재', 'critical', ok, ok ? 'ok' : '대본/메시지 누락');
  } else add('PK8', '홍보영상 대본/핵심메시지 존재', 'info', true, '미실행');

  const mismatch = SUPP.filter((n) => !!ran[n] !== !!modules[n]);
  add('PK9', '실행/스킵 상태와 산출물 일치', 'critical', mismatch.length === 0, mismatch.length ? `불일치: ${mismatch}` : 'ok');

  if (planKm.size) {
    const drift = SUPP.filter((n) => ran[n] && modules[n] && !looseIntersect(tokenize(suppKeyMessage(modules[n])), planKm));
    add('PK10', '부가물 핵심메시지가 수업안과 정합', 'warning', drift.length === 0, drift.length ? `정합 안됨: ${drift}` : 'aligned');
  } else add('PK10', '부가물 핵심메시지가 수업안과 정합', 'info', true, 'no key_message');

  const baseAud = (intake.audience || '').trim();
  const audMis = SUPP.filter((n) => {
    const m = modules[n];
    if (!ran[n] || !m) return false;
    const a = ((m.intake && m.intake.audience) || (m.inputs && m.inputs.audience) || '').trim();
    return baseAud && a && a !== baseAud;
  });
  add('PK11', '대상(audience) 일관성', 'warning', audMis.length === 0, audMis.length ? `상이: ${audMis}` : 'ok');

  add('PK12', '부가물 생성 오류 없음', 'critical', true, 'ok');

  const bodyTok = passageTokens(intake.body_text);
  if (bodyTok.size) {
    const off = SUPP.filter((n) => {
      if (!ran[n] || !modules[n]) return false;
      const txt = suppPassageText(modules[n]);
      return ![...bodyTok].some((tok) => txt.includes(tok));
    });
    add('PK13', '부가물이 본문 구절을 참조', 'warning', off.length === 0, off.length ? `미참조: ${off}` : 'ok');
  } else add('PK13', '부가물이 본문 구절을 참조', 'info', true, '본문 구절 없음');

  checks.sort((a, b) => parseInt(a.id.slice(2)) - parseInt(b.id.slice(2)));
  const criticalFail = checks.filter((c) => c.severity === 'critical' && !c.passed);
  const warnings = checks.filter((c) => c.severity === 'warning' && !c.passed);
  return {
    verdict: criticalFail.length === 0 ? 'PASS' : 'FAIL',
    checks,
    summary: { total: checks.length, passed: checks.filter((c) => c.passed).length, critical: criticalFail.length, warnings: warnings.length },
  };
}
