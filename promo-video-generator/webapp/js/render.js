/* render.js — render promo-video.v1 + downloads (JSON / SRT) + per-cut prompt copy. */

const Render = (() => {
  const copyReg = [];
  function reset() { copyReg.length = 0; }
  function getCopy(i) { return copyReg[i]; }
  function regCopy(t) { copyReg.push(t); return copyReg.length - 1; }
  const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const copyBtn = (t, label = '복사') => (t ? `<button class="btn btn--ghost btn--sm" data-copy="${regCopy(t)}">📋 ${label}</button>` : '');

  function render(pkg) {
    reset();
    const meta = pkg.meta || {};
    let html = '';

    if (pkg.narration && pkg.narration.full_script) {
      html += `<div class="section"><h4>전체 내레이션 (${esc(meta.total_duration_seconds || '')}초)</h4><div class="copy-row"><div class="prompt-box">${esc(pkg.narration.full_script)}</div>${copyBtn(pkg.narration.full_script)}</div></div>`;
    }

    const cuts = (pkg.storyboard && pkg.storyboard.cuts) || [];
    if (cuts.length) {
      html += `<div class="section"><h4>스토리보드 (${cuts.length}컷)</h4>`;
      cuts.forEach((c) => {
        html += `<div class="cut"><div><strong>Cut ${esc(c.id)}</strong> <span class="cut__meta">${esc(c.duration_seconds)}초 · ${esc(c.visual_type)}</span></div>`;
        html += `<p>${esc(c.scene_description)}</p>`;
        if (c.subtitle) html += `<p class="cut__meta">자막: ${esc(c.subtitle)}</p>`;
        if (c.video_prompt) html += `<div class="copy-row"><div class="prompt-box">🎬 ${esc(c.video_prompt)}</div>${copyBtn(c.video_prompt, '영상')}</div>`;
        if (c.image_prompt) html += `<div class="copy-row"><div class="prompt-box">🖼 ${esc(c.image_prompt)}</div>${copyBtn(c.image_prompt, '이미지')}</div>`;
        html += `</div>`;
      });
      html += `</div>`;
    }

    if (pkg.cta) html += `<div class="section"><h4>CTA</h4><p>${esc(pkg.cta.text || '')} ${pkg.cta.on_screen ? '· ' + esc(pkg.cta.on_screen) : ''}</p></div>`;
    return html;
  }

  function srt(pkg) {
    const subs = (pkg && pkg.subtitles) || [];
    const fmt = (s) => {
      const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = Math.floor(s % 60);
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')},000`;
    };
    return subs.map((s, i) => `${i + 1}\n${fmt(s.start_seconds || 0)} --> ${fmt(s.end_seconds || 0)}\n${s.text || ''}\n`).join('\n');
  }

  return { render, srt, getCopy };
})();
