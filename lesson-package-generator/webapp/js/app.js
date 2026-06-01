/* app.js — UI wiring: settings, generate flow, progress, tabs, downloads, copy. */

const $ = (sel) => document.querySelector(sel);
let LAST = null;          // last pipeline result
let abortCtrl = null;

const STEPS = [
  { id: 'plan', label: '① 수업안 설계', icon: '📋' },
  { id: 'teaching', label: '② 교보재', icon: '🎲' },
  { id: 'praise', label: '③ 찬양', icon: '🎵' },
  { id: 'promo', label: '④ 홍보영상', icon: '🎬' },
  { id: 'check', label: '⑤ 자기검수', icon: '✅' },
];

/* ---------- Toast ---------- */
let toastTimer;
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2200);
}

/* ---------- Settings modal ---------- */
function openSettings() {
  $('#apiKeyInput').value = Config.getKey();
  $('#modelSelect').value = Config.getModel();
  $('#settingsModal').hidden = false;
}
function closeSettings() { $('#settingsModal').hidden = true; }

$('#settingsBtn').addEventListener('click', openSettings);
$('#settingsModal').addEventListener('click', (e) => { if (e.target.hasAttribute('data-close')) closeSettings(); });
$('#settingsSave').addEventListener('click', () => {
  Config.setKey($('#apiKeyInput').value);
  Config.setModel($('#modelSelect').value);
  closeSettings();
  toast('설정을 저장했습니다.');
});

/* ---------- Progress ---------- */
function buildProgress(opts) {
  const ul = $('#progressList');
  ul.innerHTML = '';
  STEPS.forEach((s) => {
    const skipped = (s.id === 'teaching' && !opts.teaching) || (s.id === 'praise' && !opts.praise) || (s.id === 'promo' && !opts.promo);
    const li = document.createElement('li');
    li.className = 'progress__item ' + (skipped ? 'st-skip' : 'st-pending');
    li.id = 'prog-' + s.id;
    li.innerHTML = `<span class="progress__icon">${skipped ? '–' : s.icon}</span>
      <span><span class="progress__label">${s.label}</span><br><span class="progress__detail">${skipped ? '건너뜀' : '대기 중'}</span></span>`;
    ul.appendChild(li);
  });
}
function setStep(id, status, detail) {
  const li = $('#prog-' + id);
  if (!li) return;
  const step = STEPS.find((s) => s.id === id);
  li.className = 'progress__item st-' + (status === 'active' ? 'active' : status === 'done' ? 'done' : status === 'error' ? 'error' : status === 'skip' ? 'skip' : 'pending');
  const icon = li.querySelector('.progress__icon');
  const det = li.querySelector('.progress__detail');
  if (status === 'active') { icon.innerHTML = '<span class="spinner"></span>'; det.textContent = '생성 중…'; }
  else if (status === 'done') { icon.textContent = '✓'; det.textContent = detail || '완료'; }
  else if (status === 'error') { icon.textContent = '✗'; det.textContent = detail || '실패'; }
  else if (status === 'skip') { icon.textContent = '–'; det.textContent = '건너뜀'; }
}

/* ---------- Generate flow ---------- */
$('#genForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!Config.hasKey()) { toast('먼저 ⚙️에서 API 키를 입력하세요.'); openSettings(); return; }

  const intake = {
    body_text: $('#bodyText').value.trim(),
    theme: $('#theme').value.trim(),
    emphasis: $('#theme').value.trim(),
    audience: $('#audience').value.trim(),
    volume: $('#volume').value.trim(),
    locale: 'ko',
  };
  const opts = { teaching: $('#optTeaching').checked, praise: $('#optPraise').checked, promo: $('#optPromo').checked };

  $('#inputSection').hidden = true;
  $('#resultSection').hidden = true;
  $('#progressSection').hidden = false;
  buildProgress(opts);
  $('#cancelBtn').hidden = true;

  abortCtrl = new AbortController();
  try {
    LAST = await runPipeline(intake, opts, setStep, abortCtrl.signal);
    showResults(LAST);
  } catch (err) {
    const active = STEPS.find((s) => $('#prog-' + s.id) && $('#prog-' + s.id).classList.contains('st-active'));
    if (active) setStep(active.id, 'error', err.message || '오류');
    toast(err.message || '생성 중 오류가 발생했습니다.');
    $('#cancelBtn').hidden = false;
    if (err.code === 'NO_KEY' || err.code === 'AUTH') openSettings();
  }
});

$('#cancelBtn').addEventListener('click', resetToInput);
$('#newBtn').addEventListener('click', resetToInput);
function resetToInput() {
  if (abortCtrl) abortCtrl.abort();
  $('#progressSection').hidden = true;
  $('#resultSection').hidden = true;
  $('#inputSection').hidden = false;
}

/* ---------- Results ---------- */
function showResults(r) {
  Render.reset();
  $('#progressSection').hidden = true;
  $('#resultSection').hidden = false;

  const ir = r.lessonPlan.intake_ref || {};
  $('#resultMeta').textContent = `${ir.audience || ''} · ${(r.lessonPlan.meta && r.lessonPlan.meta.volume_minutes) || ''}분 · 강조: ${ir.emphasis || ''} · 자기검수 ${r.selfCheck.verdict}`;

  $('#panel-plan').innerHTML = Render.plan(r.lessonPlan);
  $('#panel-teaching').innerHTML = Render.teaching(r.teaching);
  $('#panel-praise').innerHTML = Render.praise(r.praise);
  $('#panel-promo').innerHTML = Render.promo(r.promo);
  $('#panel-check').innerHTML = Render.check(r.selfCheck);

  switchTab('plan');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ---------- Tabs ---------- */
$('#tabs').addEventListener('click', (e) => {
  const btn = e.target.closest('.tab'); if (!btn) return;
  switchTab(btn.dataset.tab);
});
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === name));
  ['plan', 'teaching', 'praise', 'promo', 'check'].forEach((n) => { $('#panel-' + n).hidden = n !== name; });
}

/* ---------- Download + copy (event delegation) ---------- */
function slug() {
  const theme = (LAST && LAST.intake.theme) || 'lesson';
  return theme.replace(/[^\w가-힣]+/g, '_').slice(0, 20);
}
function download(filename, text, type = 'application/json') {
  const blob = new Blob([text], { type: type + ';charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}
const DL = {
  'plan-json': () => download(`${slug()}_수업안.json`, JSON.stringify(LAST.lessonPlan, null, 2)),
  'plan-md': () => download(`${slug()}_수업안.md`, Render.planMarkdown(LAST.lessonPlan), 'text/markdown'),
  'teaching-json': () => download(`${slug()}_교보재.json`, JSON.stringify(LAST.teaching, null, 2)),
  'praise-json': () => download(`${slug()}_찬양.json`, JSON.stringify(LAST.praise, null, 2)),
  'praise-lyrics': () => download(`${slug()}_가사.md`, Render.praiseLyricsMarkdown(LAST.praise), 'text/markdown'),
  'promo-json': () => download(`${slug()}_홍보영상.json`, JSON.stringify(LAST.promo, null, 2)),
  'promo-srt': () => download(`${slug()}_자막.srt`, Render.promoSrt(LAST.promo), 'text/plain'),
};
$('#downloadAllBtn').addEventListener('click', () => {
  if (!LAST) return;
  download(`${slug()}_패키지.json`, JSON.stringify({
    intake: LAST.intake, lesson_plan: LAST.lessonPlan, teaching: LAST.teaching,
    praise: LAST.praise, promo: LAST.promo, self_check: LAST.selfCheck,
  }, null, 2));
});

document.addEventListener('click', (e) => {
  const dl = e.target.closest('[data-dl]');
  if (dl && DL[dl.dataset.dl]) { DL[dl.dataset.dl](); toast('다운로드를 시작합니다.'); return; }
  const cp = e.target.closest('[data-copy]');
  if (cp) {
    const text = Render.getCopy(Number(cp.dataset.copy));
    navigator.clipboard.writeText(text).then(() => toast('프롬프트를 복사했습니다.')).catch(() => toast('복사 실패'));
  }
});

/* ---------- First-run hint ---------- */
if (!Config.hasKey()) {
  setTimeout(() => toast('시작하려면 ⚙️에서 Anthropic API 키를 입력하세요.'), 600);
}
