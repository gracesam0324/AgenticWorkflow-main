# Tech Architect 분석
> AI Agentic Workflow Automation System (로컬 실행)
> 조사일: 2026-04-07

---

## 4가지 핵심 기술 과제

### 과제 1: 안전한 로컬 코드 실행 (Safety)

```
IProcessExecutor 인터페이스
├── SafetyClassifier — 명령어 분류 (Whitelist / Dangerous / Forbidden)
├── DryRunExecutor — 실행 전 시뮬레이션 (사이드 이펙트 없음)
├── ApprovalGate — 위험 작업 시 사용자 명시 승인
└── AuditLogger — append-only 실행 로그

절대 원칙: 안전 경계는 프롬프트가 아닌 코드 레벨로만
```

**절대 차단 목록:**
- rm -rf, del /f (파괴적 삭제)
- curl/wget (네트워크 유출)
- git push --force (Git 파괴)
- shutdown, reboot (시스템 파괴)
- .env, SSH key 접근 (명시 허용 전)

### 과제 2: 컨텍스트 관리 (Context Management)

```yaml
# state.yaml (Single Source of Truth)
metadata:
  workflow_id: uuid
  current_step: int
  last_modified: timestamp

workflow_inputs:
  user_intent: "자연어 입력"

generated_plan:
  steps: []
  checksum: sha256  # 실행 중 수정 불가

step_results:
  step_01: { status, output, timestamp }
  ...

approval_history:
  - timestamp, decision, rationale
```

**계층적 메모리:**
- L0: 진행 중 (state.yaml)
- L1: 검증 로그 (validation scripts)
- L2: 세션 스냅샷 (.claude/context-snapshots/)

### 과제 3: 실패 복구 (Fault Tolerance)

```
실패 감지 → Diagnostic Agent
├── 1차: 에러 로그 파싱
├── 2차: 직전 5단계 재검토
└── 3차: 자가 수복 제안

재시도 예산:
├── 자동 재시도: 1회 (에러 컨텍스트 주입)
├── 사용자 승인 재시도: 3회
└── Hard fail → Rollback 제안

Rollback:
├── Git 기반: 모든 변경 commit → git revert
├── 상태 스냅샷: 각 단계 완료 후 저장
└── 원자성: 각 단계 all-or-nothing
```

### 과제 4: 확인/검증 (Verification) — 4계층

```
L0: Anti-Skip Guard (human-approval 강제)
L1: Technical Gates (파일 존재, 스키마, 체크섬)
L1.5: pACS Self-Assessment (점수 인플레이션 감지)
L2: Calibration Review (독립 에이전트 재검증)
```

---

## BRANCH A: Monolithic / Fast-Launch

### 기술 스택

```
Core:
├── Claude Opus 4.6 (200K context)
├── Claude Sonnet 4.6 (비용 최적화)
├── Claude Code CLI (네이티브)
└── Python 3.10+

Storage: YAML + Markdown + JSON + Git

명시적 제외:
├── 데이터베이스 (파일로 충분)
├── API 서버 (로컬만 실행)
├── GUI (CLI + 문서)
├── 마이크로서비스
└── LangChain/LlamaIndex (의존성 증가)
```

### 아키텍처

```
workflow.md (Master Orchestrator)
├── Step 1: NL → YAML 플랜 변환
├── Step 2: 사용자 플랜 승인
├── Step 3: 플랜 체크섬 잠금
├── Step 4: Dry-run 검증
└── Step 5-N: 순차 실행 → 검증 → 로그

.claude/agents/
├── orchestrator.md
├── planner.md
├── executor.md
├── validator.md
└── reporter.md

scripts/ (결정론적)
├── validate_plan.py
├── classify_safety.py
├── run_dry_run.py
└── verify_outputs.py
```

### 6개월 구현 범위

| 월 | 기능 |
|----|------|
| 1-2 | NL→YAML, 승인 게이트, dry-run, 안전 분류, 기본 실행 |
| 2-3 | 멀티스텝 워크플로우, 에러 복구, 상태 관리, 5개 템플릿 |
| 3-4 | 4계층 검증, 자율성 레벨, 자가치유 프로토타입 |
| 5-6 | 베타(50-100명), 피드백 반영, 문서화, 공개 출시 |

### 주요 기술 부채

| 항목 | 해결 시점 |
|------|---------|
| 단일 에이전트 (컨텍스트 rot) | Month 8-9 |
| 파일 기반 상태 (병렬 X) | Month 12 (v1.1) |
| 수동 테스트 | Month 7 후 자동화 |

**팀 규모**: 2.4 FTE / **예상 비용**: $200K-300K (6개월)

---

## BRANCH B: Modular / Long-term

### 아키텍처 레이어

```
L4: User Interface (CLI commands, logging)
L3: Workflow Engine (DAG executor, state machine, hook system)
L2: Agent Orchestration (registry, message queue, conflict resolution)
L1: Core Interfaces (IProcessExecutor, ILLMProvider, IWorkflowStorage)
L0: External Services (Claude API, Local LLM, 파일 시스템)
```

### 컴포넌트 구조

```
core/interfaces/          — 추상화 레이어
core/implementations/     — 플랫폼별 구현체
core/safety/              — 안전 경계

orchestration/            — DAG 실행, 상태 관리
agents/                   — planner, executor, validator, healer
validation/               — 4계층 검증 프레임워크
templates/                — 템플릿 레지스트리
```

### 확장 로드맵

- v1.0: Sequential only, 단일 에이전트, 파일 기반 상태
- v1.1: Agent teams (병렬), Multi-LLM, 스냅샷
- v1.2: Conditional branching, Loop, 커스텀 validator
- v2+: Sub-workflows, 커뮤니티 템플릿, 웹 대시보드

---

## Branch A vs B 비교

| 차원 | Branch A (Fast) | Branch B (Modular) |
|------|-----------------|------------------|
| 6개월 출시 가능성 | 95% | 85% |
| Month 3 동작 제품 | 70% | 40% |
| Month 12 기능 완성도 | 70% | 90% |
| 장기 유지보수 비용 | 높음 | 낮음 |
| 누적 개발 시간 (Month 12) | 28주 | 22주 |

---

## 권장: Branch A → Month 8에 Branch B 구조로 진화

**이유**: 빠른 출시로 초기 검증(6개월) → 사용 데이터 기반 리팩토링(Month 7-8) → 확장 기능은 Branch B 구조에서(Month 9+)

---

## 절대 기준 3가지

### 절대 기준 1: 안전 우선
```
안전 > 로컬 퍼스트 > 불변 플랜 > 기능 완성도
- IProcessExecutor: 코드 레벨 경계
- 프롬프트 엔지니어링은 보안 경계 아님
- 승인 게이트는 로직이 아닌 사용자
```

### 절대 기준 2: 로컬 퍼스트
```
허용: Claude API (처리만), 로컬 파일, Git push (선택)
금지: 클라우드 저장, 텔레메트리(동의 없이), 원격 실행, 계정 필요
```

### 절대 기준 3: 품질 우선
```
토큰 비용 < 개발 속도 < 기능 수 < 결과물 품질
- 4계층 검증 (L0-L2)
- 빠른 것보다 신뢰할 수 있는 것
- 많은 기능보다 잘 작동하는 기능
```

---

## Top 5 기술 리스크

| 순위 | 리스크 | 확률 | 완화 전략 |
|-----|-------|------|---------|
| 1 | 토큰 초과 (긴 워크플로우) | 60% | Context manager + compression |
| 2 | 안전 경계 우회 | 30% | 코드 레벨만 신뢰 |
| 3 | 다중 에이전트 경합 | 40% | SOT 패턴, Orchestrator만 쓰기 |
| 4 | CLI 진입장벽 (사용자) | 70% | 문서화, 템플릿 |
| 5 | 기술 부채 누적 | 50% | Phase-based 출시 |
