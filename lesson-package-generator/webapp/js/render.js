/* render.js — render lesson plan + supplementary tabs; download + copy-prompt. */

const Render = (() => {
  const copyReg = [];
  function regCopy(text) { copyReg.push(text); return copyReg.length - 1; }
  function getCopy(i) { return copyReg[i]; }
  function reset() { copyReg.length = 0; }

  const esc = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const list = (arr) => `<ul>${(arr || []).map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`;
  const SECTION_KO = {
    learning_objectives: '학습목표', introduction: '도입', body_development: '본문전개',
    key_message: '핵심메시지', application: '적용', discussion_questions: '토의질문',
    closing: '마무리', time_allocation: '시간배분',
  };

  function copyBtn(text, label = '복사') {
    if (!text) return '';
    return `<button class="btn btn--ghost btn--sm" data-copy="${regCopy(text)}">📋 ${label}</button>`;
  }
  function dlBtn(kind, label) { return `<button class="btn btn--ghost btn--sm" data-dl="${kind}">⬇ ${label}</button>`; }

  /* ---- Lesson plan ---- */
  function plan(p) {
    const s = p.sections || {};
    const meta = p.meta || {};
    const ir = p.intake_ref || {};
    let html = `<div class="block"><div class="block__head"><div class="block__title">수업안</div>${dlBtn('plan-json', 'JSON')} ${dlBtn('plan-md', 'MD')}</div>`;
    html += `<div class="section">`;
    if (ir.audience) html += `<span class="kpill">대상 ${esc(ir.audience)}</span>`;
    if (meta.volume_minutes) html += `<span class="kpill">총 ${esc(meta.volume_minutes)}분</span>`;
    if (ir.emphasis) html += `<span class="kpill">강조 ${esc(ir.emphasis)}</span>`;
    html += `</div>`;

    for (const k of Object.keys(SECTION_KO)) {
      if (!(k in s)) continue;
      const v = s[k];
      html += `<div class="section"><h4>${SECTION_KO[k]}</h4>`;
      if (k === 'time_allocation' && Array.isArray(v)) {
        html += v.map((it) => `<div class="time-row"><span>${esc(it.segment)}</span><strong>${esc(it.minutes)}분</strong></div>`).join('');
      } else if (Array.isArray(v)) {
        html += list(v);
      } else {
        html += `<p>${esc(v)}</p>`;
      }
      html += `</div>`;
    }
    html += `</div>`;
    return html;
  }

  function planMarkdown(p) {
    const s = p.sections || {}, meta = p.meta || {}, ir = p.intake_ref || {};
    let md = `# 수업안 (Lesson Plan)\n\n`;
    if (ir.audience) md += `- **대상**: ${ir.audience}\n`;
    if (meta.volume_minutes) md += `- **분량**: 총 ${meta.volume_minutes}분\n`;
    if (ir.emphasis) md += `- **강조점**: ${ir.emphasis}\n`;
    md += `\n`;
    for (const k of Object.keys(SECTION_KO)) {
      if (!(k in s)) continue;
      md += `## ${SECTION_KO[k]}\n`;
      const v = s[k];
      if (k === 'time_allocation' && Array.isArray(v)) md += v.map((it) => `- ${it.segment}: ${it.minutes}분`).join('\n') + '\n\n';
      else if (Array.isArray(v)) md += v.map((x) => `- ${x}`).join('\n') + '\n\n';
      else md += `${v}\n\n`;
    }
    return md;
  }

  /* ---- Teaching ---- */
  function teaching(t) {
    if (!t) return empty('교보재를 생성하지 않았습니다.');
    const c = t.components || {};
    let html = `<div class="block"><div class="block__head"><div class="block__title">${esc((t.summary && t.summary.title) || '교보재')}</div>${dlBtn('teaching-json', 'JSON')}</div>`;
    if (t.summary && t.summary.key_message) html += `<div class="section"><h4>핵심메시지</h4><p>${esc(t.summary.key_message)}</p></div>`;

    html += comp('도입게임', c.intro_game, ['materials', 'steps', 'leader_notes']);
    html += comp('토의', c.discussion, ['format', 'questions', 'leader_notes']);
    html += comp('활동', c.activity, ['steps', 'debrief']);
    if (c.worksheet) {
      html += `<div class="section"><h4>워크시트 — ${esc(c.worksheet.title || '')}</h4>`;
      (c.worksheet.sections || []).forEach((ws) => { html += `<p><strong>${esc(ws.heading)}</strong><br>${esc(ws.body)}</p>`; });
      if (c.worksheet.leader_answer_key) html += `<p class="card__sub">교사 답안: ${esc(c.worksheet.leader_answer_key)}</p>`;
      html += `</div>`;
    }
    // image prompts collected from [IMG: ...]
    const imgs = collectImgPrompts(t);
    if (imgs.length) {
      html += `<div class="section"><h4>이미지 프롬프트 (${imgs.length})</h4>`;
      imgs.forEach((p) => { html += `<div class="copy-row"><div class="prompt-box">${esc(p)}</div>${copyBtn(p)}</div>`; });
      html += `</div>`;
    }
    if (Array.isArray(t.slides) && t.slides.length) {
      html += `<div class="section"><h4>슬라이드 (${t.slides.length})</h4>`;
      t.slides.forEach((sl) => { html += `<p><strong>${esc(sl.order)}. ${esc(sl.title)}</strong><br>${esc((sl.bullets || []).join(' · '))}</p>`; });
      html += `</div>`;
    }
    return html + `</div>`;
  }
  function comp(title, obj, fields) {
    if (!obj) return '';
    let h = `<div class="section"><h4>${title}${obj.title ? ' — ' + esc(obj.title) : ''}${obj.duration_minutes ? ` <span class="kpill">${esc(obj.duration_minutes)}분</span>` : ''}</h4>`;
    fields.forEach((f) => {
      const v = obj[f];
      if (!v || (Array.isArray(v) && !v.length)) return;
      const labels = { materials: '준비물', steps: '진행', leader_notes: '교사 노트', format: '형식', questions: '질문', debrief: '디브리핑' };
      h += `<p><strong>${labels[f] || f}</strong></p>`;
      h += Array.isArray(v) ? list(v) : `<p>${esc(v)}</p>`;
    });
    return h + `</div>`;
  }
  function collectImgPrompts(obj) {
    const out = []; const re = /\[IMG:\s*([^\]]+)\]/gi;
    JSON.stringify(obj).replace(re, (_, p) => { out.push(p.trim()); return _; });
    return out;
  }

  /* ---- Praise ---- */
  function praise(p) {
    if (!p) return empty('찬양을 생성하지 않았습니다.');
    const song = p.song || {};
    const mg = p.music_generation || {};
    let html = `<div class="block"><div class="block__head"><div class="block__title">${esc(song.title || '찬양')}</div>${dlBtn('praise-json', 'JSON')} ${dlBtn('praise-lyrics', '가사 MD')}</div>`;
    // lyrics
    html += `<div class="section"><h4>가사</h4><div class="lyrics">`;
    (song.structure || Object.keys(song.lyrics || {})).forEach((key) => {
      const part = (song.lyrics || {})[key];
      if (!part) return;
      html += `<span class="lbl">${esc(part.label || key)}</span>${esc((part.lines || []).join('\n'))}\n`;
    });
    html += `</div>`;
    if (song.copyright_notice) html += `<p class="card__sub">${esc(song.copyright_notice)}</p>`;
    html += `</div>`;
    // suno prompt
    if (mg.prompt_combined) {
      html += `<div class="section"><h4>Suno 음악 프롬프트</h4><div class="copy-row"><div class="prompt-box">${esc(mg.prompt_combined)}</div>${copyBtn(mg.prompt_combined)}</div>`;
      const st = mg.prompt_structured;
      if (st) html += `<p class="card__sub">${esc(st.genre || '')} · ${esc(st.mood || '')} · ${esc(st.bpm || '')}BPM</p>`;
      html += `<p class="card__sub">🎵 suno.com 커스텀 모드에 프롬프트를 붙여넣어 음원을 생성하세요.</p></div>`;
    }
    if (p.leader_notes) {
      const ln = p.leader_notes;
      html += `<div class="section"><h4>인도 노트</h4><p>${esc(ln.when_to_use || '')} ${ln.suggested_key ? '· 키 ' + esc(ln.suggested_key) : ''} ${ln.tempo ? '· ' + esc(ln.tempo) : ''}</p>${ln.teaching_tip ? `<p>${esc(ln.teaching_tip)}</p>` : ''}</div>`;
    }
    return html + `</div>`;
  }
  function praiseLyricsMarkdown(p) {
    const song = (p && p.song) || {};
    let md = `# ${song.title || '찬양'}\n\n`;
    if (song.copyright_notice) md += `*${song.copyright_notice}*\n\n`;
    (song.structure || Object.keys(song.lyrics || {})).forEach((key) => {
      const part = (song.lyrics || {})[key]; if (!part) return;
      md += `## ${part.label || key}\n${(part.lines || []).join('\n')}\n\n`;
    });
    if (p.music_generation && p.music_generation.prompt_combined) md += `## Suno 프롬프트\n${p.music_generation.prompt_combined}\n`;
    return md;
  }

  /* ---- Promo ---- */
  function promo(v) {
    if (!v) return empty('홍보영상을 생성하지 않았습니다.');
    const meta = v.meta || {};
    let html = `<div class="block"><div class="block__head"><div class="block__title">홍보영상 (${esc(meta.total_duration_seconds || '')}초)</div>${dlBtn('promo-json', 'JSON')} ${dlBtn('promo-srt', '자막 SRT')}</div>`;
    if (v.narration && v.narration.full_script) {
      html += `<div class="section"><h4>전체 내레이션</h4><div class="copy-row"><div class="prompt-box">${esc(v.narration.full_script)}</div>${copyBtn(v.narration.full_script)}</div></div>`;
    }
    const cuts = (v.storyboard && v.storyboard.cuts) || [];
    if (cuts.length) {
      html += `<div class="section"><h4>스토리보드 (${cuts.length}컷)</h4>`;
      cuts.forEach((c) => {
        html += `<div class="cut"><div><strong>Cut ${esc(c.id)}</strong> <span class="cut__meta">${esc(c.duration_seconds)}초 · ${esc(c.visual_type)}</span></div>`;
        html += `<p>${esc(c.scene_description)}</p>`;
        if (c.subtitle) html += `<p class="cut__meta">자막: ${esc(c.subtitle)}</p>`;
        const vp = c.video_prompt, ip = c.image_prompt;
        if (vp) html += `<div class="copy-row"><div class="prompt-box">🎬 ${esc(vp)}</div>${copyBtn(vp, '영상')}</div>`;
        if (ip) html += `<div class="copy-row"><div class="prompt-box">🖼 ${esc(ip)}</div>${copyBtn(ip, '이미지')}</div>`;
        html += `</div>`;
      });
      html += `</div>`;
    }
    if (v.cta) html += `<div class="section"><h4>CTA</h4><p>${esc(v.cta.text || '')} ${v.cta.on_screen ? '· ' + esc(v.cta.on_screen) : ''}</p></div>`;
    return html + `</div>`;
  }
  function promoSrt(v) {
    const subs = (v && v.subtitles) || [];
    const fmt = (s) => { const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = Math.floor(s % 60); return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')},000`; };
    return subs.map((s, i) => `${i + 1}\n${fmt(s.start_seconds || 0)} --> ${fmt(s.end_seconds || 0)}\n${s.text || ''}\n`).join('\n');
  }

  /* ---- Self-check ---- */
  function check(sc) {
    if (!sc) return empty('자기검수 결과가 없습니다.');
    const cls = sc.verdict === 'PASS' ? 'verdict--pass' : 'verdict--fail';
    let html = `<div class="block"><div class="block__head"><div class="block__title">자기검수</div></div>`;
    html += `<div class="section"><span class="verdict ${cls}">${sc.verdict === 'PASS' ? '✓ PASS' : '✗ FAIL'}</span>`;
    html += ` <span class="card__sub">통과 ${sc.summary.passed}/${sc.summary.total} · 치명 실패 ${sc.summary.critical} · 경고 ${sc.summary.warnings}</span></div>`;
    html += `<div class="section">`;
    sc.checks.forEach((c) => {
      const st = c.passed ? 'PASS' : (c.severity === 'info' ? 'NA' : 'FAIL');
      html += `<div class="check-row"><span class="check-row__id">${c.id}</span><span class="check-row__st st-${st}">${st}</span><span><strong>${esc(c.title)}</strong><br><span class="card__sub">${esc(c.detail)}</span></span></div>`;
    });
    return html + `</div></div>`;
  }

  function empty(msg) { return `<div class="empty">${esc(msg)}</div>`; }

  return { plan, planMarkdown, teaching, praise, praiseLyricsMarkdown, promo, promoSrt, check, getCopy, reset };
})();
