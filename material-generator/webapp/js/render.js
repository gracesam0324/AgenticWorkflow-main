/* render.js — render teaching-materials.v1 + downloads (JSON/MD) + image-prompt copy. */

const Render = (() => {
  const copyReg = [];
  function reset() { copyReg.length = 0; }
  function getCopy(i) { return copyReg[i]; }
  function regCopy(t) { copyReg.push(t); return copyReg.length - 1; }

  const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const list = (arr) => `<ul>${(arr || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`;
  const copyBtn = (t, label = '복사') => (t ? `<button class="btn btn--ghost btn--sm" data-copy="${regCopy(t)}">📋 ${label}</button>` : '');

  function collectImgPrompts(obj) {
    const out = []; const re = /\[IMG:\s*([^\]]+)\]/gi;
    JSON.stringify(obj || {}).replace(re, (_, p) => { out.push(p.trim()); return _; });
    return out;
  }

  function comp(title, obj, fields) {
    if (!obj) return '';
    const labels = { materials: '준비물', steps: '진행', leader_notes: '교사 노트', format: '형식', questions: '질문', debrief: '디브리핑' };
    let h = `<div class="section"><h4>${title}${obj.title ? ' — ' + esc(obj.title) : ''}${obj.duration_minutes ? ` <span class="kpill">${esc(obj.duration_minutes)}분</span>` : ''}</h4>`;
    fields.forEach((f) => {
      const v = obj[f];
      if (!v || (Array.isArray(v) && !v.length)) return;
      h += `<p><strong>${labels[f] || f}</strong></p>` + (Array.isArray(v) ? list(v) : `<p>${esc(v)}</p>`);
    });
    return h + `</div>`;
  }

  function render(pkg) {
    reset();
    const c = pkg.components || {};
    const s = pkg.summary || {};
    let html = '';
    if (s.key_message) html += `<div class="section"><h4>핵심메시지</h4><p>${esc(s.key_message)}</p></div>`;

    html += comp('도입게임', c.intro_game, ['materials', 'steps', 'leader_notes']);
    html += comp('토의', c.discussion, ['format', 'questions', 'leader_notes']);
    html += comp('활동', c.activity, ['steps', 'debrief']);
    if (c.worksheet) {
      html += `<div class="section"><h4>워크시트 — ${esc(c.worksheet.title || '')}</h4>`;
      (c.worksheet.sections || []).forEach((w) => { html += `<p><strong>${esc(w.heading)}</strong><br>${esc(w.body)}</p>`; });
      if (c.worksheet.leader_answer_key) html += `<p class="card__sub">교사 답안: ${esc(c.worksheet.leader_answer_key)}</p>`;
      html += `</div>`;
    }

    const imgs = collectImgPrompts(pkg);
    if (imgs.length) {
      html += `<div class="section"><h4>이미지 프롬프트 (${imgs.length}) — 이미지 생성 AI에 붙여넣기</h4>`;
      imgs.forEach((p) => { html += `<div class="copy-row"><div class="prompt-box">${esc(p)}</div>${copyBtn(p)}</div>`; });
      html += `</div>`;
    }

    if (Array.isArray(pkg.slides) && pkg.slides.length) {
      html += `<div class="section"><h4>슬라이드 (${pkg.slides.length})</h4>`;
      pkg.slides.forEach((sl) => { html += `<p><strong>${esc(sl.order)}. ${esc(sl.title)}</strong><br>${esc((sl.bullets || []).join(' · '))}</p>`; });
      html += `</div>`;
    }
    return html;
  }

  function markdown(pkg) {
    const c = pkg.components || {}, s = pkg.summary || {};
    let md = `# ${s.title || '교보재'}\n\n`;
    if (s.key_message) md += `**핵심메시지**: ${s.key_message}\n\n`;
    const sec = (t, body) => { md += `## ${t}\n${body}\n\n`; };
    if (c.intro_game) sec('도입게임 — ' + (c.intro_game.title || ''), (c.intro_game.steps || []).map((x) => `- ${x}`).join('\n'));
    if (c.discussion) sec('토의', (c.discussion.questions || []).map((x) => `- ${x}`).join('\n'));
    if (c.activity) sec('활동 — ' + (c.activity.title || ''), (c.activity.steps || []).map((x) => `- ${x}`).join('\n'));
    if (c.worksheet) sec('워크시트 — ' + (c.worksheet.title || ''), (c.worksheet.sections || []).map((w) => `### ${w.heading}\n${w.body}`).join('\n\n'));
    return md;
  }

  return { render, markdown, getCopy };
})();
