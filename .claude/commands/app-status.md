---
description: "Show current church retreat app workflow status and quality report"
---

# /app-status — 수련회 앱 상태 확인

Display the current workflow status, quality gate results, and pACS scores in Korean. This command is READ-ONLY.

## Execute These Steps

### Step 1: Find and Read SOT

1. Read `%USERPROFILE%\.last-church-app-path` for project path
2. If not found, search `~/Desktop/church-app*` folders
3. Read `app-state.json` from the project folder

Parse all sections:
- `status` — phase progress booleans
- `intent` — app type, team config
- `quality` — gate results, pACS scores
- `history` — modification records
- `deployment` — server, QR info

### Step 2: Check Server Status

Use **Bash tool** to check if the server is running:
```bash
netstat -ano | findstr :{PORT} 2>/dev/null || echo "NOT_RUNNING"
```

### Step 3: Display Status Dashboard in Korean

```
📱 수련회 앱 상태

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
기본 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
앱 유형:    {intent.app_type_korean}
교회 이름:  {intent.church_name}
팔레트:    {intent.design_palette}
프로젝트:   {meta.project_path}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
진행 단계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 0 환경 설정:     {✅/⬜}
Phase 1 콘텐츠 수집:   {✅/⬜}
Phase 2 프로젝트 초기화: {✅/⬜}
Phase 3 코드 생성:     {✅/⬜}
Phase 4 품질 검증:     {✅/⬜}
Phase 5 미리보기:      {✅/⬜}
Phase 6 배포:         {✅/⬜}

현재 단계: Phase {N} — {phase_description_korean}
진행률: [{filled}{empty}] {percentage}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
품질 점수 (pACS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
F (콘텐츠 정확성):  {F_score}/100  {GREEN/YELLOW/RED}
C (기능 완전성):   {C_score}/100  {GREEN/YELLOW/RED}
L (코드 정확성):   {L_score}/100  {GREEN/YELLOW/RED}
종합: pACS = min(F,C,L) = {pACS}  {status_emoji}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
품질 게이트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
기술 (Q1-Q11): {pass_count}/{total_count} 통과
디자인 (D1-D9): {pass_count}/{total_count} 통과
{if any FAIL: list failed gates with reason}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
수정 이력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
수정 횟수: {modification_count}회
{for each modification: timestamp + description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
서버 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
서버: {실행 중 ✅ / 중지됨 ⬜}
포트: {PORT}
URL: {url}
QR코드: {qr_path or "미생성"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
폴백 이력
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
현재 티어: Tier {N}
활성화 횟수: {count}회
{if any: list fallback activations}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
번역 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
번역 완료: {completed}/{total} 파일
T1 (파일 존재): {PASS/FAIL/미실행}
T2 (pACS ≥ 70): {PASS/FAIL/미실행}
T3 (용어 일관성): {PASS/FAIL/미실행}
```

### Step 4: Show Next Action

Based on current phase:
- Phase 0-1: "계속 대화를 이어가세요."
- Phase 2-4: "자동으로 진행 중이에요. 잠시만 기다려 주세요."
- Phase 5: "앱을 확인하고 수정할 부분을 말씀해 주세요."
- Phase 6: "배포가 완료되었어요! QR코드를 프린트하세요."
- All done: "모든 단계가 완료되었어요!"

## Error Handling

| Error | Korean Message | Action |
|-------|---------------|--------|
| No project found | "앱 프로젝트를 찾을 수 없어요. `/start-app`으로 시작하세요." | — |
| SOT parse error | "상태 파일을 읽을 수 없어요." | Show raw file path |
| Missing sections | Use "---" for unavailable data | Continue display |

## Constraints

- This command is **strictly read-only** — never modifies app-state.json
- All output in Korean (user-facing command)
- pACS color coding: GREEN ≥ 70, YELLOW 50-69, RED < 50
- Progress bar: 7 characters total (one per phase)
