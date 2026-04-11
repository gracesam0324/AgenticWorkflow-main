---
description: "Run quality verification manually (Phase 4 gates)"
---

# /app-verify — 수련회 앱 품질 검증

Manually run all P1 validation scripts and display PASS/FAIL results for each quality gate in Korean.

## Execute These Steps

### Step 1: Find Project

1. Read `%USERPROFILE%\.last-church-app-path` for project path
2. Verify `app-state.json` exists in project folder
3. Verify `scripts/` folder with validation scripts exists

If scripts not found:
- Korean: "검증 스크립트가 없어요. Phase 3 (코드 생성)을 먼저 완료해 주세요."

### Step 2: Read SOT for App Type

Read `app-state.json` → extract `intent.app_type` for app-specific gate selection.

### Step 3: Run P1 Validation Scripts

Execute all scripts via **Bash tool** (Claude Code's Python runtime):

```bash
# Technical gates Q1-Q11
python3 scripts/validate_gates.py --project-dir . --json

# Design gates D1-D9
python3 scripts/validate_design_gates.py --project-dir . --json

# App-type-specific gates
python3 scripts/validate_app_specific.py --project-dir . --type {app_type} --json

# Content insertion accuracy
python3 scripts/validate_content_insertion.py --project-dir . --json

# Integration check (HTML↔CSS↔JS)
python3 scripts/validate_integration.py --project-dir . --json

# Translation gates (if post-Phase 6)
python3 scripts/validate_translation_gates.py --project-dir . --json
```

### Step 4: Merge Results

Collect all JSON outputs and merge:
```python
all_results = {**q_results, **d_results, **app_results}
content_results = {...}
integration_results = {...}
fail_gates = [gate for gate in all_results if not gate["pass"]]
overall = "PASS" if len(fail_gates) == 0 else "FAIL"
```

### Step 5: Display Results in Korean

```
🔍 품질 검증 결과

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
기술 품질 게이트 (Q1-Q11)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Q1  서버 실행:        {✅ PASS / ❌ FAIL: reason}
Q2  HTML 유효성:      {✅ PASS / ❌ FAIL: reason}
Q3  외부 의존성:      {✅ PASS / ❌ FAIL: reason}
Q4  번들 크기:        {✅ PASS / ❌ FAIL: {size}KB / 500KB}
Q5  한국어 렌더링:    {✅ PASS / ❌ FAIL: reason}
Q6  터치 타겟:        {✅ PASS / ❌ FAIL: reason}
Q7  QR코드:          {✅ PASS / ❌ FAIL: reason}
Q8  관리자 보호:      {✅ PASS / ❌ FAIL: reason}
Q9  XSS 방지:        {✅ PASS / ❌ FAIL: reason}
Q10 시각 확인:        ⏭️ SKIP (사역자 직접 확인)
Q11 응답 속도:        {✅ PASS / ❌ FAIL: {latency}ms / 100ms}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
디자인 품질 게이트 (D1-D9)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
D1  카드 UI:          {✅ PASS / ❌ FAIL: reason}
D2  애니메이션:       {✅ PASS / ❌ FAIL: reason}
D3  다크 모드:        {✅ PASS / ❌ FAIL: reason}
D4  색상 일관성:      {✅ PASS / ❌ FAIL: {count} hardcoded}
D5  모바일 네이티브:  {✅ PASS / ❌ FAIL: reason}
D6  폰트 가독성:      {✅ PASS / ❌ FAIL: reason}
D7  마이크로 인터랙션: {✅ PASS / ❌ FAIL: reason}
D8  로딩 UX:          {✅ PASS / ❌ FAIL: reason}
D9  화면 이펙트:      {✅ PASS / ❌ FAIL: reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
콘텐츠 정확도
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
일치율: {match_rate}% ({found}/{total} 항목)
{if missing: list missing items}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
통합 검증
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HTML↔CSS 클래스:    {✅ PASS / ❌ FAIL: orphaned classes}
JS↔HTML ID:         {✅ PASS / ❌ FAIL: dangling refs}
매니페스트:          {✅ PASS / ❌ FAIL: reason}
서비스 워커:         {✅ PASS / ❌ FAIL: reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
종합 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{🎉 모든 게이트 통과! / ⚠️ {fail_count}개 게이트 실패}

{if FAIL exists:}
❌ 실패한 게이트를 자동으로 수정할까요? (네/아니요)
```

### Step 6: Offer Auto-Fix (if failures exist)

If 사역자 chooses auto-fix:
1. For each FAIL gate, apply the documented fix action (see quality-gates.md)
2. Re-run only the failed gate scripts to confirm PASS
3. Max 3 retries per gate
4. Display updated results

## Error Handling

| Error | Korean Message | Action |
|-------|---------------|--------|
| Scripts not found | "검증 스크립트가 없어요." | Guide to run Phase 3 first |
| Script error (exit 1) | "검증 스크립트 실행 중 오류가 발생했어요." | Show error detail |
| Server not running (Q1) | "서버가 실행 중이 아니에요. 서버를 시작할까요?" | Offer to start |
| No project found | "앱 프로젝트를 찾을 수 없어요." | Guide to /start-app |

## Constraints

- Read-only: validation scripts NEVER modify project files
- All output in Korean
- Q10 always shows SKIP (human-only gate)
- Translation gates only shown if post-Phase 6
