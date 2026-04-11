# Phase 2 기술 심층조사 종합 결과
> Technology Development Deep-Dive PRD Teammate
> 조사일: 2026-04-07
> 대상: AI Agentic Workflow Automation System (로컬 실행)

---

## 참여 Teammate

| 역할 | 브랜치 | 파일 | 상태 |
|------|--------|------|------|
| Core Tech Researcher | 1.1 Aggressive / 1.2 Conservative | branch-1.1/1.2 | ✅ |
| Architecture Specialist | 2.1 Evolutionary / 2.2 BDUF | branch-2.1/2.2 | ✅ |
| Dev Workflow Expert | 3.1 Fast+Safe / 3.2 Robust | branch-3.1/3.2 | ✅ |
| Technical Debt Manager | 4.1 Minimize / 4.2 Pragmatic | branch-4.1/4.2 | ✅ |
| Theory Foundation Expert | 5.1 Latest / 5.2 Classic | branch-5.1/5.2 | ✅ |

---

## 5개 Teammate 핵심 권고 요약

### Core Tech Researcher
- **Branch 1.1 (Aggressive)**: LangGraph + Claude API + FastAPI + React
- **Branch 1.2 (Conservative)**: Click + Python + Ollama + YAML 파일
- **권고**: 1인 6개월 MVP에는 Branch 1.2 (Conservative). Claude API는 허용.

### Architecture Specialist
- **Branch 2.1 (Evolutionary)**: 동작하는 코드 먼저, 점진적 추상화
- **Branch 2.2 (BDUF)**: 헥사고날 아키텍처 전체 설계 후 구현
- **권고**: Branch 2.1 기반 + Branch 2.2에서 3개 핵심 포트만 추출
  - IAIProvider, IShellPort, IStateRepository

### Dev Workflow Expert
- **Branch 3.1 (Fast+Safe)**: 주 2-3 기능, Critical Path 테스트만
- **Branch 3.2 (Robust)**: 주 1-1.5 기능, TDD + 전체 품질 게이트
- **권고**: 하이브리드 — 일반 코드는 3.1, 안전 관련 코드는 3.2

### Technical Debt Manager
- **Branch 4.1 (Minimize)**: 클린 아키텍처 처음부터
- **Branch 4.2 (Pragmatic)**: 부채 레지스터로 관리하며 빠르게
- **권고**: "안전 우선 실용주의" — 보안 코드는 클린하게, 나머지는 실용적으로

### Theory Foundation Expert
- **Branch 5.1 (Latest)**: ReAct, Constitutional AI, MCP, Agent Safety
- **Branch 5.2 (Classic)**: UNIX 철학, Event Sourcing, ECA, Least Privilege
- **권고**: Top 10 원칙 도출 (최신 + 고전 균형 조합)

---

## Phase 2 Green Zone (5개 모두 동의)

1. ✅ **로컬 전용 원칙 불변** — Claude API 처리용 호출만 허용, 저장은 로컬
2. ✅ **안전 코드는 Day 1부터 클린하게** — 이후 기능에 타협 없음
3. ✅ **YAML SOT 패턴** — Plan(불변) + State(가변) 분리
4. ✅ **Event Sourcing 기반 롤백** — 모든 실행 이력 append-only 로그
5. ✅ **ReAct + CoT 실행 엔진** — 추론 → 안전 검증 → 실행
6. ✅ **MCP 호환 설계** — 에코시스템 통합 (Claude Desktop 등)
7. ✅ **단일 에이전트 v1.0** — 멀티에이전트는 v2.0 이후

---

## Phase 2 Yellow Zone (조건부 포함)

- ToT(Tree-of-Thoughts): 복잡한 태스크에만 적용 (API 비용 고려)
- 완전한 CQRS: Event Sourcing만 먼저, CQRS는 v1.1 이후
- LangGraph 직접 사용: 패턴만 채용, 프레임워크 의존성은 나중에 판단

---

## Phase 2 Red Zone (현재 제외)

- 마이크로서비스 아키텍처 — 1인 개발에 과도
- 완전한 Petri Net 검증 — DAG 검증으로 대체
- GUI/웹 대시보드 — v2.0 이후
- Ollama 로컬 모델 우선 — 성능 격차로 v1.1 이후

---

## TOP 10 이론적 원칙 (PRD 반영 필요)

| 순위 | 원칙 | 출처 | v1.0 필수 |
|------|------|------|-----------|
| 1 | Reason Before Acting | ReAct + CoT | ✅ |
| 2 | Safety is Foundation | Defense in Depth + Constitutional AI | ✅ |
| 3 | Local-First Privacy-by-Design | MCP + Least Privilege | ✅ |
| 4 | Reversibility First | Event Sourcing + Agent Safety | ✅ |
| 5 | Observable by Default | ECA + Audit Trail | ✅ |
| 6 | Composability Over Completeness | UNIX Philosophy + SOLID OCP | ✅ |
| 7 | Explicit Over Implicit | Constitutional AI + YAML 투명성 | ✅ |
| 8 | Fail Safely, Recover Gracefully | Petri Net + Defense in Depth | ✅ |
| 9 | Domain Boundaries Drive Architecture | Conway's Law + DDD | ⚠️ |
| 10 | Ecosystem Citizen, Not Island | MCP + UNIX Philosophy | ✅ |

---

## 기술 스택 최종 권고 (v1.0)

```
언어: Python 3.11+
AI: Claude API (claude-opus-4-6 / claude-sonnet-4-6)
CLI: Click (typer도 가능)
설정: Pydantic + YAML
상태관리: YAML 파일 (Plan/State 분리)
버전관리: Git (자동 체크포인트)
이벤트로그: append-only JSONL 파일
테스트: pytest + hypothesis
보안: bandit + subprocess(shell=False 필수)
배포: MCP 서버로 패키징

명시적 제외:
- 데이터베이스 (파일로 충분)
- API 서버 (로컬만)
- GUI (CLI + 문서)
- LangChain/LlamaIndex (의존성 과다)
- Docker (v1.1 이후)
```

---

## 6개월 구현 로드맵

```
Month 1: 안전한 기반 + 첫 동작
  - SafetyValidator + ShellExecutor (Branch 3.2 방식)
  - Claude API 연동 + YAML 파서
  - ReAct 실행 엔진 기초
  - Event Sourcing 로그 기초

Month 2-3: 핵심 기능 완성
  - 사용자 확인 플로우 (단계별 승인)
  - 롤백 메커니즘 완성
  - 5개 큐레이션 템플릿
  - MCP 서버 기초

Month 4: 검증 강화
  - 4계층 검증 (L0-L2) 완성
  - 자율성 레벨 3단계 구현
  - TECHNICAL_DEBT_REGISTER 정리

Month 5-6: 안정화 + 출시
  - 베타 테스트 (50-100명)
  - 보안 자체 감사
  - 문서화 완성
  - v1.0 릴리즈
```
