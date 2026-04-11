---
description: "프로젝트 상태 대시보드 — 모든 활성 프로젝트의 진행 상황을 표시"
---

# /status — 프로젝트 상태 대시보드

모든 활성 프로젝트의 진행 상황, 품질 점수, 다음 할 일을 표시한다.
이 커맨드는 **READ-ONLY** — SOT 파일을 절대 수정하지 않는다.

---

## Step 1: 상태 감지 스크립트 실행

**Bash로 실행**:

```bash
python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/scripts/detect_projects.py" \
  --project-dir="$CLAUDE_PROJECT_DIR" --render=dashboard
```

> Windows에서 `python3`가 실패하면 `py` 또는 `python`으로 재시도.

스크립트 출력을 **그대로** 사용자에게 보여준다.

스크립트가 실패하면 Step 1F(Fallback)로 이동.

---

## Step 1F: Fallback (스크립트 실행 실패 시)

직접 SOT 파일을 읽어서 상태를 파악한다:

1. `autobiography-generator/state.yaml` — 자서전 SOT
2. `app-state.json` — 수련회 앱 SOT
3. `state.yaml` (프로젝트 루트) — 일반 워크플로우 SOT

각 파일에서 `current_step`, `status`, `outputs` 필드를 읽어 아래 형식으로 출력:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   AgenticWorkflow — 프로젝트 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

활성 프로젝트별로:
- 프로젝트 이름 + 상태 뱃지
- 현재 단계/Phase
- 진행률 바
- SOT 경로

활성 프로젝트가 없으면:
> *활성 프로젝트가 없습니다. `/start`로 새 프로젝트를 시작하세요.*

---

## Step 2: 심화 정보 (활성 프로젝트가 있는 경우)

### 수련회 앱이 활성인 경우

`app-state.json`을 Read tool로 읽어 추가 정보 표시:

| 항목 | 출처 |
|------|------|
| 앱 유형 | `intent.app_type` |
| 앱 이름 | `intent.app_name` |
| 현재 Phase | `workflow.current_phase` |
| 품질 점수 | `quality.pacs` (있으면) |
| 마지막 검증 | `quality.last_gate` (있으면) |
| 다음 할 일 | Phase 기반 자동 판단 |

### 자서전이 활성인 경우

`autobiography-generator/state.yaml`을 Read tool로 읽어 추가 정보 표시:

| 항목 | 출처 |
|------|------|
| 현재 단계 | `workflow.current_step` |
| 인터뷰 상태 | `interviews` 섹션 (있으면) |
| 챕터 상태 | `chapters` 섹션 (있으면) |
| 품질 점수 | `pacs` 섹션 (있으면) |
| 번역 상태 | `translation` 섹션 (있으면) |
| 다음 할 일 | Step 기반 자동 판단 |

### 일반 워크플로우가 활성인 경우

`state.yaml`을 Read tool로 읽어:

| 항목 | 출처 |
|------|------|
| 워크플로우 이름 | `workflow.name` |
| 현재 Step | `workflow.current_step` |
| 완료된 산출물 | `outputs` 섹션 |
| 다음 할 일 | Step 기반 자동 판단 |

---

## Step 3: 다음 행동 추천

대시보드 하단에 **구체적인 다음 행동**을 1~2개 제안한다:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   다음 할 일
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

예시:
- 수련회 앱 Phase 1 → "앱 콘텐츠(퀴즈 문제, 일정 등)를 입력해 주세요"
- 자서전 Step 2 → "인터뷰를 계속하려면 `/interview`를 입력하세요"
- 자서전 Step 7 → "챕터를 검토하려면 `/review-chapter`를 입력하세요"
- 프로젝트 없음 → "`/start`로 새 프로젝트를 시작하세요"

---

## 제약

- **READ-ONLY**: 이 커맨드는 SOT를 절대 수정하지 않는다.
- **English-First (AC-4)**: 내부 분석은 영어. 사용자 출력만 한국어.
- **NEVER SHOW Infrastructure Build**: 이 대시보드에서 빌드/설치 관련 정보는 표시하지 않는다.
