/* app.js — 교보재 생성기 UI: 설정·생성·렌더·다운로드. */

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

/* settings */
function openSettings() { $('#apiKeyInput').value = Config.getKey(); $('#modelSelect').value = Config.getModel(); $('#settingsModal').hidden = false; }
function closeSettings() { $('#settingsModal').hidden = true; }
$('#settingsBtn').addEventListener('click', openSettings);
$('#settingsModal').addEventListener('click', (e) => { if (e.target.hasAttribute('data-close')) closeSettings(); });
$('#settingsSave').addEventListener('click', () => { Config.setKey($('#apiKeyInput').value); Config.setModel($('#modelSelect').value); closeSettings(); toast('설정을 저장했습니다.'); });

/* generate */
$('#genForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!Config.hasKey()) { toast('먼저 ⚙️에서 API 키를 입력하세요.'); openSettings(); return; }

  const intake = buildIntake({
    body: $('#bodyText').value.trim(),
    theme: $('#theme').value.trim(),
    audience: $('#audience').value.trim(),
    volume: $('#volume').value.trim(),
  });

  $('#inputSection').hidden = true;
  $('#resultSection').hidden = true;
  $('#progressSection').hidden = false;
  $('#cancelBtn').hidden = true;
  $('#progDetail').textContent = 'Claude 호출 중…';

  abortCtrl = new AbortController();
  try {
    const raw = await callClaude({ system: MATERIAL_PROMPT, user: buildPayload(intake), signal: abortCtrl.signal });
    const pkg = parseJsonResponse(raw);
    if (pkg.format !== 'teaching-materials.v1') pkg.format = 'teaching-materials.v1';
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
  $('#resultTitle').textContent = (pkg.summary && pkg.summary.title) || '교보재';
  $('#resultMeta').textContent = `${intake.audience} · 테마: ${intake.theme}`;
  $('#result').innerHTML = Render.render(pkg);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* download + copy */
function slug() { return ((LAST && LAST.intake.theme) || 'material').replace(/[^\w가-힣]+/g, '_').slice(0, 20); }
function download(name, text, type = 'application/json') {
  const blob = new Blob([text], { type: type + ';charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
}
$('#dlJson').addEventListener('click', () => { if (LAST) { download(`${slug()}_교보재.json`, JSON.stringify(LAST.pkg, null, 2)); toast('다운로드를 시작합니다.'); } });
$('#dlMd').addEventListener('click', () => { if (LAST) { download(`${slug()}_교보재.md`, Render.markdown(LAST.pkg), 'text/markdown'); toast('다운로드를 시작합니다.'); } });

document.addEventListener('click', (e) => {
  const cp = e.target.closest('[data-copy]');
  if (cp) navigator.clipboard.writeText(Render.getCopy(Number(cp.dataset.copy))).then(() => toast('프롬프트를 복사했습니다.')).catch(() => toast('복사 실패'));
});

if (!Config.hasKey()) setTimeout(() => toast('시작하려면 ⚙️에서 Anthropic API 키를 입력하세요.'), 600);
