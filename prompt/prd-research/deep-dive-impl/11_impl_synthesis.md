# Phase 3 구현 기술 심층조사 종합 결과
> Coding & Implementation Deep-Dive PRD Teammate
> 조사일: 2026-04-07
> 대상: AI Agentic Workflow Automation System (로컬 실행)

---

## 참여 Teammate

| 역할 | 브랜치 | 파일 | 상태 |
|------|--------|------|------|
| Core Tech Researcher | 1.1 Cutting Edge / 1.2 Proven | branch-1.1/1.2 | ✅ |
| Architecture Specialist | 2.1 Evolutionary / 2.2 Complete | branch-2.1/2.2 | ✅ |
| Dev Workflow Expert | 3.1 Speed-First / 3.2 Quality-First | branch-3.1/3.2 | ✅ |
| Technical Debt Manager | 4.1 Minimize / 4.2 Pragmatic | branch-4.1/4.2 | ✅ |
| Theory Foundation Expert | 5.1 Latest Theory / 5.2 Classic Theory | branch-5.1/5.2 | ✅ |

---

## 5개 Teammate 핵심 권고 요약

### Core Tech Researcher
- **Branch 1.1 (Cutting Edge)**: Claude SDK Tool Use + async DAG + MCP 서버 + SQLAlchemy
- **Branch 1.2 (Proven)**: Click CLI + PyYAML + subprocess 안전 래퍼 + 파일 기반 상태
- **권고**: Pragmatic Hybrid — 보수적 기반 위에 선택적으로 공격적 기능 추가
  - Phase 1(M1-2): 보수적 기반 (Click + PyYAML + 순차 실행)
  - Phase 2(M3-4): Pydantic 업그레이드 + 단계별 승인 + Git 롤백
  - Phase 3(M5-6): async DAG(선택) + MCP 서버(선택)
  - **MVP 완성 예상**: 3-4개월 (Branch 1.2 기반)

### Architecture Specialist
- **Branch 2.1 (Evolutionary)**: 동작 코드 우선, 리팩터링 트리거 조건 정의
- **Branch 2.2 (Complete)**: IProcessExecutor + ILLMProvider + IWorkflowPlanStore 처음부터
- **권고**: 하이브리드 — `IProcessExecutor`만 Branch 2.2(Day 1), 나머지는 Branch 2.1
  - `state.yaml` 원자적 쓰기: `sot_lib.py` 패턴 직접 재사용 (`.tmp` → `os.replace()` + `.bak`)
  - `EventBus`는 AuditLog + GraduatedAutonomyTracker 동시 필요 시점(Month 3)에 도입
  - 플러그인 아키텍처는 Red Zone 유지 (서명 체계 없이 RCE 벡터)

### Dev Workflow Expert
- **Branch 3.1 (Speed-First)**: Spike → Production 전환 방법론, DEBT 태그 시스템
- **Branch 3.2 (Quality-First)**: TDD + Golden Tests + 계층별 테스트 피라미드
- **권고**: "보안은 처음부터, 품질은 점진적으로"
  - Pydantic v2 입력 검증: Day 1
  - pre-commit hooks + ruff: Week 1
  - mypy: Month 2
  - GitHub Actions CI/CD: Month 3
  - DEBT 태그 + 주간 골든 테스트: 지속적으로

### Technical Debt Manager
- **Branch 4.1 (Minimize)**: 완전한 pyproject.toml + ruff + mypy + bandit + pre-commit
- **Branch 4.2 (Pragmatic)**: AI 특화 부채 분류 + TECHNICAL_DEBT_REGISTER.yaml
- **권고**: 5대 절대 허용 불가 부채를 식별
  1. 경로 순회 검증 없음 → LLM이 `../../../etc/passwd` 생성 가능
  2. `shell=True` subprocess → 프롬프트 인젝션 → 셸 인젝션 연계
  3. LLM 출력 무검증 실행 → 환각으로 파일 삭제/덮어쓰기
  4. 실행 타임아웃 없음 → 무한 루프 → 리소스 고갈
  5. API 키 소스코드 하드코딩 → git push 시 유출

### Theory Foundation Expert
- **Branch 5.1 (Latest)**: Claude Tool Use 패턴 + Safety-First Agent Loop + Structured Output
- **Branch 5.2 (Classic)**: WorkflowStateMachine + Command Pattern(Undo) + EventBus
- **권고**: 7가지 이론 원칙 + 5가지 구현 패턴 도출
  - 최우선: Safety-First Agent Loop + Atomic Rollback
  - Phase 1(M1-2): FSM + Agent Loop + StructuredOutputParser
  - Phase 2(M3-4): CommandHistory Rollback + SafeExecutor + EventBus
  - Phase 3(M5-6): LLMRouter(Ollama 폴백) + MCP + Pipeline 스트리밍

---

## Phase 3 Green Zone (5개 모두 동의)

1. ✅ **IProcessExecutor Day 1 인터페이스** — 안전 경계 코드 레벨 강제, 첫 커밋부터
2. ✅ **Pydantic v2 LLM 출력 검증** — 환각 방어, 재시도 최대 3회
3. ✅ **5대 절대 부채 금지** — 경로순회/shell=True/무검증실행/타임아웃없음/API키하드코딩
4. ✅ **보수적 기반 시작** — Click + PyYAML + 순차 실행 (3-4개월 MVP 달성 가능)
5. ✅ **Safety-First Agent Loop** — max_iterations=20 + 안전 체크 + 사용자 승인
6. ✅ **`state.yaml` 원자적 쓰기** — `.tmp` → `os.replace()` + `.bak` 패턴 (sot_lib.py 재사용)
7. ✅ **DEBT 태그 시스템** — `# DEBT[분류][우선순위]` 형식으로 기술 부채 추적

---

## Phase 3 Yellow Zone (조건부 포함)

- async DAG 병렬 실행: 사용자 피드백 기반으로 Phase 3(M5-6)에서 도입
- SQLite 상태 관리: 파일 기반으로 충분하면 스킵, 필요 시 마이그레이션
- EventBus: AuditLog + GraduatedAutonomyTracker 동시 필요 시점(Month 3)에 도입
- mypy 전체 적용: Month 2부터 점진적 도입

---

## Phase 3 Red Zone (현재 제외)

- 플러그인 아키텍처 — 서명 체계 없이 RCE 벡터, v2에서
- LangChain/LlamaIndex — 과도한 추상화, 의존성 관리 복잡
- 완전한 TDD (처음부터) — 6개월 MVP 제약으로 보안만 TDD 적용
- Celery/Ray — 분산 처리, 로컬 단일 실행에 불필요
- OpenTelemetry — 관측가능성 오버킬, Phase 3+

---

## 핵심 기술 스택 (Phase 3 권고)

```
AI 호출:    anthropic>=0.40.0 (공식 SDK)
CLI:        click>=8.1 + rich>=13
파싱/검증:  pyyaml>=6 + pydantic>=2
상태관리:   YAML 파일 (Plan/State 원자적 쓰기)
안전실행:   subprocess(shell=False) + 허용 목록
롤백:       gitpython>=3.1 + Command Pattern
이벤트:     append-only JSONL EventBus (Month 3)
테스트:     pytest + hypothesis + Golden Tests
보안:       bandit + ruff[security] + pre-commit
배포:       pipx (의존성 5개 이하 목표)
```

---

## PRD에 반영해야 할 아키텍처 결정 (ADR)

### ADR-1: IProcessExecutor 추출 시점
> `IProcessExecutor`는 Week 1 첫 커밋에서 추출한다.  
> `ILLMProvider`는 두 번째 구현체(Ollama)가 필요해질 때 추출한다.  
> `IWorkflowPlanStore`는 저장 방식을 바꿔야 할 이유가 생길 때 추출한다.  
> "미래에 필요할 것 같아서" 추출하지 않는다.

### ADR-2: state.yaml 원자적 쓰기
> `sot_lib.py`의 `fcntl.flock` + `.tmp` 경유 `os.replace()` + `.bak` 복구 패턴을  
> 이 프로젝트도 직접 재사용한다. (autobiography-generator에서 검증된 구현)

### ADR-3: EventBus 도입 조건
> AuditLogService와 GraduatedAutonomyTracker가 동시 구현되는 Month 3에  
> `SimpleEventBus`를 도입한다. 그 전까지는 직접 함수 호출로 유지한다.

### ADR-4: 5대 절대 부채 금지
> 경로 순회 검증 없음 / shell=True / LLM 출력 무검증 / 타임아웃 없음 / API 키 하드코딩  
> 이 5가지는 pre-commit hooks + bandit으로 자동 감지하고, 코드 리뷰 체크리스트에 명시한다.

### ADR-5: 보안 코드는 TDD, 나머지는 실용적
> SafetyValidator, IProcessExecutor 구현은 Branch 3.2 방식(TDD + 85% 커버리지).  
> 나머지 기능은 Branch 3.1 방식(동작 우선 + Critical Path 테스트만).

---

## 6개월 구현 로드맵 (Phase 3 반영)

```
Month 1: 보수적 기반 + 안전 우선
  - IProcessExecutor (허용 목록 + shell=False) — TDD 적용
  - Claude API 기본 호출 + Pydantic 출력 검증
  - YAML 파싱 + state.yaml 원자적 쓰기 (sot_lib.py 재사용)
  - Click CLI 기반 + Rich 출력
  - pre-commit + ruff Day 1 설정

Month 2-3: 핵심 기능 + 안전 시스템
  - Safety-First Agent Loop (max_iterations=20)
  - 단계별 승인 UX (3단계 자율성 레벨)
  - Command Pattern 기반 Undo/Rollback
  - EventBus 도입 (AuditLog + GraduatedAutonomyTracker)
  - mypy 점진적 적용 시작
  - Golden Tests 도입 (AI 품질 주간 모니터링)

Month 4: 검증 강화 + 부채 해소
  - 5대 절대 부채 pre-commit 자동 감지 설정
  - TECHNICAL_DEBT_REGISTER.yaml 정리 + TOP 3 해소
  - GitHub Actions CI/CD 구축
  - bandit 보안 스캔 파이프라인

Month 5-6: 안정화 + 선택적 확장
  - MCP 서버 구현 (얼리어답터 대응)
  - async DAG (사용자 피드백 기반, 선택)
  - 베타 테스트 (50-100명)
  - pipx 배포 패키징
```
