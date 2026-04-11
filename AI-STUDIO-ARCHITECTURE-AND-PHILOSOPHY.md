# AI Studio — 아키텍처와 설계 철학

> 이 문서는 AI Studio의 **내부 구조와 설계 결정**을 기술한다.
> 사용법은 [`AI-STUDIO-USER-MANUAL.md`](AI-STUDIO-USER-MANUAL.md)를 참조한다.
> 부모 프레임워크의 방법론은 [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md)를 참조한다.

---

## 1. 정체성 — 부모에서 태어난 자식

AI Studio는 **AgenticWorkflow 프레임워크**(만능줄기세포)에서 분화된 **자식 시스템**이다.

```
AgenticWorkflow (부모 유기체 — 만능줄기세포)
  │
  │  DNA 유전: 절대 기준 3개, SOT 패턴, 3단계 구조,
  │            4계층 검증, P1 봉쇄, Safety Hook,
  │            Adversarial Review, Context Preservation
  │
  └── AI Studio (자식 — 이 시스템)
        │
        ├── 수련회 앱 생성기 (church-retreat-app)
        ├── 자서전 생성기 (autobiography)
        ├── 워크플로우 설계기 (workflow-generator)
        └── 학술 글쓰기 도구 (doctoral-writing)
```

줄기세포가 분화할 때 모든 세포가 부모의 전체 DNA를 갖듯이, AI Studio는 부모의 전체 게놈을 **내장**한다. "참고"하는 것이 아니라 구조적으로 포함한다.

### 부모에서 유전된 DNA

| 게놈 구성요소 | AI Studio에서의 형태 |
|-------------|-------------------|
| 절대 기준 1 (품질 최우선) | 4계층 품질 보장 시스템으로 구현 |
| 절대 기준 2 (단일 파일 SOT) | `app-state.json`, `state.yaml` — 스킬별 단일 SOT |
| 절대 기준 3 (코드 변경 프로토콜) | Hook 스크립트가 결정론적으로 강제 |
| 3단계 구조 | Research → Planning → Implementation |
| P1 할루시네이션 봉쇄 | 50+ Python 검증 스크립트, AI 판단 0% |
| Safety Hook | 131개 자동화 테스트, 위험 명령 차단 |
| Context Preservation | 세션 간 자동 저장·복원 (RLM 패턴) |

### AI Studio가 스스로 추가한 유전자

| 고유 특성 | 설명 |
|----------|------|
| **제품 실행 모드** | 자연어 시작 명령 → 스마트 라우터 → 4개 스킬 분기 |
| **프로젝트 자동 감지** | SOT 파일 기반 진행 중 프로젝트 감지 + `[진행 중]` 뱃지 |
| **인라인 진행률** | Stop hook에서 SOT 변경 감지 시 자동 표시 |
| **Infrastructure Build 격리** | 사용자에게 빌드/설치 옵션을 절대 노출하지 않음 |
| **대화형 진입** | "시작하자" 한 마디로 전체 시스템 진입 |

---

## 2. 아키텍처 개요

### 전체 흐름

```
사용자: "시작하자"
       │
       ▼
┌──────────────────────┐
│   자연어 라우팅       │  CLAUDE.md의 트리거 패턴 매칭
│   (시작/start/go)     │  → /start 커맨드 실행
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   프로젝트 감지       │  detect_projects.py (P1 결정론적)
│   + 메뉴 렌더링       │  SOT 파일 스캔 → 마크다운 메뉴 생성
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│   실행 모드 선택       │  사용자 입력 (번호 또는 자연어)
│   1/2/3/4            │  → 키워드 매칭 → 스킬 라우팅
└──────┬───────────────┘
       │
       ├─ 1 → church-retreat-app → /start-app 또는 /resume-app
       ├─ 2 → autobiography     → /interview 또는 현재 단계
       ├─ 3 → workflow-generator → SKILL.md 진입
       └─ 4 → doctoral-writing  → SKILL.md 진입
              │
              ▼
       ┌──────────────────────┐
       │   스킬 실행 엔진      │
       │   (대화 → 작업 → 검증) │
       └──────┬───────────────┘
              │
              ▼ (매 응답마다)
       ┌──────────────────────┐
       │   Stop Hook 파이프라인 │
       │   1. context_guard    │  컨텍스트 스냅샷
       │   2. sot_snapshot     │  SOT 백업
       │   3. render_progress  │  진행률 표시 (변경 시만)
       └──────────────────────┘
```

### 핵심 컴포넌트

| 컴포넌트 | 파일 | 역할 |
|---------|------|------|
| **스마트 라우터** | `.claude/commands/start.md` | 자연어 → 스킬 매핑 |
| **프로젝트 감지기** | `detect_projects.py` | SOT 파일 스캔 → 상태 감지 → UI 렌더링 |
| **진행률 표시기** | `render_progress.py` | Stop hook — 변경 감지 시 인라인 표시 |
| **상태 대시보드** | `.claude/commands/status.md` | `/status` — 전체 프로젝트 상태 |
| **스킬 엔진** | `.claude/skills/*/SKILL.md` | 스킬별 실행 프로토콜 |
| **에이전트 팀** | `.claude/agents/*.md` | 22개 전문 에이전트 |
| **슬래시 명령** | `.claude/commands/*.md` | 14개 명령어 (`/start`, `/status` 등) |
| **품질 게이트** | `hooks/scripts/validate_*.py` | 16 P1 검증 스크립트 |
| **안전 가드** | `hooks/scripts/block_*.py` | 위험 명령 차단 + 시크릿 탐지 (131 자동 테스트) |

---

## 3. 스킬 아키텍처

### 3.1 수련회 앱 (church-retreat-app)

```
Phase 0: 환경 설정 (자동)
Phase 1: 대화로 요구사항 수집 → @conversation-guide
Phase 2: 앱 설계 → @church-app-orchestrator
Phase 3: 코드 생성 → @code-generator + @design-system-agent
Phase 4: 품질 검증 → @quality-checker + @tdd-guard
Phase 5: 미리보기 + 사용자 피드백 (최대 3회 수정)
Phase 6: 배포 → @deployment-manager
```

- **SOT**: `app-state.json` (JSON Schema draft-07로 검증)
- **전용 에이전트**: 8개
- **전용 라이브러리**: `_church_app_lib.py`
- **용어 사전**: `translations/church-app-glossary.yaml`
- **결과물**: HTML/JS 웹앱 + QR코드 + .bat 실행파일

### 3.2 자서전 (autobiography)

```
Step 0-1:  환경 설정 (자동)
Step 2:    AI 인터뷰 → @interviewer (McAdams 프레임워크)
Step 3:    자료 평가 (자동) → 사용자 승인
Step 4-6:  내러티브 설계 → @story-architect + @voice-calibrator
Step 7:    챕터 집필 루프 → @chapter-writer + @autobiography-reviewer
Step 8:    일관성 검토 → @consistency-checker
Step 9:    PDF/EPUB 빌드
Step 10-11: 최종 검토 → 출판
```

- **SOT**: `autobiography-generator/state.yaml`
- **전용 에이전트**: 6개
- **서브프로젝트**: `autobiography-generator/` (36+ 스크립트, Next.js 대시보드)
- **별도 문서**: `AUTOBIOGRAPHY-*.md` 3개
- **결과물**: PDF/EPUB 자서전

### 3.3 워크플로우 설계 (workflow-generator)

- **SOT**: 없음 (일회성 생성)
- **전용 에이전트**: 없음 (메인 세션이 수행)
- **결과물**: `workflow.md` 설계도
- **특수 기능**: Distill 검증, DNA 유전 프로토콜 (자식 워크플로우에 부모 게놈 내장)

### 3.4 학술 글쓰기 (doctoral-writing)

- **SOT**: 없음 (즉시 적용)
- **전용 에이전트**: 없음
- **결과물**: 학술적 문체로 수정된 문서
- **특수 기능**: 분야별 가이드 (인문·사회·자연과학), 한국어·영어 모두 지원

---

## 4. 품질 보장 아키텍처

### 4계층 스택

```
L0   Anti-Skip Guard (결정론적)
       파일 존재 + 최소 100 bytes
         ↓ PASS
L1   Verification Gate (의미론적)
       기능적 목표 100% 달성 검증
         ↓ PASS
L1.5 pACS Self-Rating (신뢰도)
       Pre-mortem → F/C/L 채점 → min(F,C,L)
       GREEN(≥70) → 진행 / RED(<50) → 재작업
         ↓ PASS
L2   Adversarial Review (적대적)
       @reviewer + @fact-checker 독립 검토
       P1 검증으로 리뷰 품질 보장
```

### P1 할루시네이션 봉쇄

"100% 정확해야 하는 작업은 Python 코드가 수행한다. AI 판단 0%."

| 검증 범주 | 스크립트 | 항목 수 |
|----------|---------|--------|
| pACS 구조 | `validate_pacs.py` | PA1-PA7 |
| 리뷰 구조 | `validate_review.py` | R1-R5 |
| 번역 품질 | `validate_translation.py` | T1-T9 |
| 검증 로그 | `validate_verification.py` | V1a-V1c |
| 진단 로그 | `validate_diagnosis.py` | AD1-AD10 |
| 추적성 | `validate_traceability.py` | CT1-CT5 |
| DNA 유전 | `validate_workflow.py` | W1-W8 |
| 재시도 예산 | `validate_retry_budget.py` | RB1-RB3 |
| 앱 SOT 스키마 | `validate_app_state_schema.py` | JSON Schema |
| Phase 전환 | `validate_phase_transition.py` | H-CRITICAL |
| 번역 준비 | `validate_translation_readiness.py` | BLOCKING |
| pACS 점수 | `compute_pacs_score.py` | H-CRITICAL |

---

## 5. 안전 아키텍처

### 4계층 방어

```
Layer 0: settings.json deny (18개 정적 차단 패턴)
   curl|sh, sudo, chmod 777, mkfs, dd, npm publish, ~/.ssh 등

Layer 1: PreToolUse 차단 (exit 2)
   block_destructive_commands.py (위험 명령)
   sot_write_guard.py (SOT 보호)
   block_test_file_edit.py (TDD 보호)
   file_ownership_guard.py (파일 소유권)

Layer 2a: PostToolUse 탐지 (경고)
   output_secret_filter.py (25+ 시크릿 패턴, 2-패스)
   security_sensitive_file_guard.py (12 민감 파일 패턴)

Layer 2b: PostToolUse 검증 (경고)
   enforce_design_system.py (디자인 일관성)
   bundle_size_guard.py (크기 제한)
```

### 테스트 커버리지

| Hook | 테스트 수 |
|------|----------|
| `block_destructive_commands.py` | 43 |
| `output_secret_filter.py` | 44 |
| `security_sensitive_file_guard.py` | 44 |
| **합계** | **131** |

---

## 6. 컨텍스트 보존

세션이 끊어져도(토큰 초과, `/clear`, 브라우저 닫기) 작업 내역이 자동으로 저장·복원된다.

```
작업 중 ──→ [PostToolUse] update_work_log.py ──→ 작업 로그 누적
        ├→ [PostToolUse] output_secret_filter.py ──→ 시크릿 탐지
        └→ [PostToolUse] security_sensitive_file_guard.py ──→ 민감 파일 경고

응답 완료 ──→ [Stop] generate_context_summary.py ──→ 스냅샷 저장
          ├→ [Stop] sot_snapshot.py ──→ SOT 백업
          └→ [Stop] render_progress.py ──→ 진행률 표시

세션 종료 ──→ [SessionEnd] save_context.py ──→ 전체 스냅샷

새 세션 ───→ [SessionStart] restore_context.py ──→ RLM 포인터 복원
```

### Knowledge Archive

세션별 메타데이터가 자동으로 축적된다:
- `phase`: 작업 단계
- `error_patterns`: 에러 12패턴 분류 + 해결책 매칭
- `tool_sequence`: 도구 사용 시퀀스 (RLE 압축)
- `final_status`: 세션 종료 상태

---

## 7. Infrastructure Build 격리 원칙

AI Studio는 **사용자에게 인프라를 보여주지 않는다**. 이것은 설계 철학이다.

| 계층 | 사용자에게 보이는가? | 이유 |
|------|-------------------|------|
| Hook 스크립트 | 보이지 않음 | 자동으로 동작 |
| settings.json | 보이지 않음 | 프레임워크 설정 |
| Agent 정의 | 보이지 않음 | 내부 실행 구조 |
| `/start` 메뉴 | **보임** | 사용자 진입점 |
| 대화 흐름 | **보임** | 핵심 상호작용 |
| 결과물 | **보임** | 앱, PDF, 문서 |
| `/status` | **보임** | 진행 상황 확인 |

**절대 금지**: `/start` 메뉴에서 Infrastructure Build, 인프라 빌드, 프레임워크 설치 옵션은 어떤 형태로든 표시하지 않는다.

---

## 8. 설계 결정 참조

주요 설계 결정은 [`DECISION-LOG.md`](DECISION-LOG.md)에 ADR(Architecture Decision Record) 형식으로 기록되어 있다.

| ADR | 결정 |
|-----|------|
| ADR-052 | 자서전 스킬 — 12단계 파이프라인, 6 전용 에이전트 |
| ADR-053 | 수련회 앱 스킬 — 8 전용 에이전트, JSON Schema SOT |
| ADR-054 | Hook 아키텍처 확장 — 50+ 스크립트, 10 기능 범주 |
| ADR-055 | 제품 실행 모드 — 자연어 라우팅 + Infrastructure Build 격리 |

---

## 부모-자식 문서 분리 패턴

이 프로젝트는 **만능줄기세포**(AgenticWorkflow)와 그로부터 태어난 **자식 시스템**(AI Studio)을 구분한다.

| 문서 | 접두어 | 기술 대상 |
|------|--------|---------|
| 부모 | `AGENTICWORKFLOW-` | 방법론, 프레임워크, DNA 정의 |
| 자식 (이 시스템) | `AI-STUDIO-` | 제품 아키텍처, 사용자 경험 |
| 손자 (자서전) | `AUTOBIOGRAPHY-` | 자서전 도메인 고유 구조 |

부모 문서는 **"어떻게 만드는가"**를, 자식 문서는 **"무엇이 만들어졌는가"**를 기술한다.
이 분리는 자식 시스템이 독립적으로 이해·운영될 수 있게 한다.
