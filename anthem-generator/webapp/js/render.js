/* render.js — render praise-worship.v1 + downloads (JSON / lyrics MD) + Suno prompt copy. */

const Render = (() => {
  const copyReg = [];
  function reset() { copyReg.length = 0; }
  function getCopy(i) { return copyReg[i]; }
  function regCopy(t) { copyReg.push(t); return copyReg.length - 1; }
  const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const copyBtn = (t, label = '복사') => (t ? `<button class="btn btn--ghost btn--sm" data-copy="${regCopy(t)}">📋 ${label}</button>` : '');

  function render(pkg) {
    reset();
    const song = pkg.song || {};
    const mg = pkg.music_generation || {};
    let html = '';

    html += `<div class="section"><h4>가사 — ${esc(song.title || '찬양')}</h4><div class="lyrics">`;
    (song.structure || Object.keys(song.lyrics || {})).forEach((key) => {
      const part = (song.lyrics || {})[key];
      if (!part) return;
      html += `<span class="lbl">${esc(part.label || key)}</span>${esc((part.lines || []).join('\n'))}\n`;
    });
    html += `</div>`;
    if (song.copyright_notice) html += `<p class="card__sub">${esc(song.copyright_notice)}</p>`;
    html += `</div>`;

    if (mg.prompt_combined) {
      html += `<div class="section"><h4>Suno 음악 프롬프트</h4><div class="copy-row"><div class="prompt-box">${esc(mg.prompt_combined)}</div>${copyBtn(mg.prompt_combined)}</div>`;
      const st = mg.prompt_structured;
      if (st) html += `<p class="card__sub">${esc(st.genre || '')} · ${esc(st.mood || '')} · ${esc(st.bpm || '')}BPM</p>`;
      html += `<p class="card__sub">🎵 suno.com 커스텀 모드에 프롬프트와 가사를 붙여넣어 음원을 만드세요.</p></div>`;
    }

    if (pkg.leader_notes) {
      const ln = pkg.leader_notes;
      html += `<div class="section"><h4>인도 노트</h4><p>${esc(ln.when_to_use || '')} ${ln.suggested_key ? '· 키 ' + esc(ln.suggested_key) : ''} ${ln.tempo ? '· ' + esc(ln.tempo) : ''}</p>${ln.teaching_tip ? `<p>${esc(ln.teaching_tip)}</p>` : ''}</div>`;
    }
    return html;
  }

  function lyricsMarkdown(pkg) {
    const song = pkg.song || {};
    let md = `# ${song.title || '찬양'}\n\n`;
    if (song.copyright_notice) md += `*${song.copyright_notice}*\n\n`;
    (song.structure || Object.keys(song.lyrics || {})).forEach((key) => {
      const part = (song.lyrics || {})[key]; if (!part) return;
      md += `## ${part.label || key}\n${(part.lines || []).join('\n')}\n\n`;
    });
    if (pkg.music_generation && pkg.music_generation.prompt_combined) md += `## Suno 프롬프트\n${pkg.music_generation.prompt_combined}\n`;
    return md;
  }

  return { render, lyricsMarkdown, getCopy };
})();
