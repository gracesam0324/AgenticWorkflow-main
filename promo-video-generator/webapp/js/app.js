/* app.js — 홍보영상 생성기 UI: 설정·생성·렌더·다운로드. */

const $ = (s) => document.querySelector(s);
let LAST = null;
let abortCtrl = null;
let toastTimer;

function toast(msg) {
  const el = $('#toast');
  el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 2200);
}

function openSettings() { $('#apiKeyInput').value = Config.getKey(); $('#modelSelect').value = Config.getModel(); $('#settingsModal').hidden = false; }
function closeSettings() { $('#settingsModal').hidden = true; }
$('#settingsBtn').addEventListener('click', openSettings);
$('#settingsModal').addEventListener('click', (e) => { if (e.target.hasAttribute('data-close')) closeSettings(); });
$('#settingsSave').addEventListener('click', () => { Config.setKey($('#apiKeyInput').value); Config.setModel($('#modelSelect').value); closeSettings(); toast('설정을 저장했습니다.'); });

$('#genForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!Config.hasKey()) { toast('먼저 ⚙️에서 API 키를 입력하세요.'); openSettings(); return; }

  const intake = buildIntake({
    theme: $('#theme').value.trim(),
    body: $('#bodyText').value.trim(),
    audience: $('#audience').value.trim(),
  });

  $('#inputSection').hidden = true;
  $('#resultSection').hidden = true;
  $('#progressSection').hidden = false;
  $('#cancelBtn').hidden = true;
  $('#progDetail').textContent = 'Claude 호출 중…';

  abortCtrl = new AbortController();
  try {
    const raw = await callClaude({ system: PROMO_PROMPT, user: buildPayload(intake), signal: abortCtrl.signal });
    const pkg = parseJsonResponse(raw);
    if (pkg.format !== 'promo-video.v1') pkg.format = 'promo-video.v1';
    LAST = { intake, pkg };
    showResult();
  } catch (err) {
    toast(err.message || '생성 중 오류가 발생했습니다.');
    $('#progDetail').textContent = '실패: ' + (err.message || '오류');
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

function showResult() {
  $('#progressSection').hidden = true;
  $('#resultSection').hidden = false;
  const { intake, pkg } = LAST;
  $('#resultTitle').textContent = '홍보영상 기획';
  const dur = (pkg.meta && pkg.meta.total_duration_seconds) || '';
  $('#resultMeta').textContent = `${intake.audience} · 테마: ${intake.theme}${dur ? ' · ' + dur + '초' : ''}`;
  $('#result').innerHTML = Render.render(pkg);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function slug() { return ((LAST && LAST.intake.theme) || 'promo').replace(/[^\w가-힣]+/g, '_').slice(0, 20); }
function download(name, text, type = 'application/json') {
  const blob = new Blob([text], { type: type + ';charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
}
$('#dlJson').addEventListener('click', () => { if (LAST) { download(`${slug()}_홍보영상.json`, JSON.stringify(LAST.pkg, null, 2)); toast('다운로드를 시작합니다.'); } });
$('#dlSrt').addEventListener('click', () => { if (LAST) { download(`${slug()}_자막.srt`, Render.srt(LAST.pkg), 'text/plain'); toast('다운로드를 시작합니다.'); } });

document.addEventListener('click', (e) => {
  const cp = e.target.closest('[data-copy]');
  if (cp) navigator.clipboard.writeText(Render.getCopy(Number(cp.dataset.copy))).then(() => toast('프롬프트를 복사했습니다.')).catch(() => toast('복사 실패'));
});

if (!Config.hasKey()) setTimeout(() => toast('시작하려면 ⚙️에서 Anthropic API 키를 입력하세요.'), 600);
