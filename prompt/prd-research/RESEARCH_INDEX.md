# PRD 사전조사 인덱스
> AI Agentic Workflow Automation System (로컬 실행)
> 최종 업데이트: 2026-04-07

---

## Phase 1: 시장·사용자·기술·비즈니스 조사

| 파일 | 내용 | 상태 |
|------|------|------|
| `00_synthesis.md` | Phase 1 전체 종합 | ✅ |
| `01_market_researcher.md` | 시장 분석 (낙관/보수 2관점) | ✅ |
| `02_user_researcher.md` | 사용자 분석 (Edge Case / Mainstream) | ✅ |
| `03_tech_architect.md` | 기술 아키텍처 (Monolithic / Modular) | ✅ |
| `04_business_strategist.md` | 비즈니스 전략 (공격적/안정적) | ✅ |

---

## Phase 2: 기술 심층조사 (deep-dive-coding/)

| 파일 | 내용 | 상태 |
|------|------|------|
| `10_tech_synthesis.md` | Phase 2 전체 종합 | ✅ |
| `branch-1.1-aggressive-core-tech.md` | 공격적 기술 스택 (LangGraph 등) | ✅ |
| `branch-1.2-conservative-core-tech.md` | 보수적 기술 스택 (Click+Python) | ✅ |
| `branch-2.1-evolutionary-architecture.md` | 진화적 아키텍처 | ✅ |
| `branch-2.2-complete-architecture.md` | 완전한 아키텍처 (BDUF+헥사고날) | ✅ |
| `branch-3.1-fast-dev-workflow.md` | 빠른 개발 워크플로우 | ✅ |
| `branch-3.2-robust-dev-workflow.md` | 견고한 개발 워크플로우 (TDD) | ✅ |
| `branch-4.1-minimize-debt.md` | 기술 부채 최소화 전략 | ✅ |
| `branch-4.2-pragmatic-debt.md` | 실용적 부채 관리 전략 | ✅ |
| `branch-5.1-latest-theory.md` | 최신 AI 이론 (ReAct, MCP 등) | ✅ |
| `branch-5.2-classic-theory.md` | 고전 CS 이론 (UNIX, Event Sourcing 등) | ✅ |
| `09_technical_debt_manager.md` | 기술 부채 관리 종합 | ✅ |

---

## 핵심 결정 사항 요약

### Phase 1 Green Zone (4관점 모두 동의)
- Edge Case 사용자 먼저 (데이터 엔지니어, 보안 연구자, 학술 연구자)
- 단계별 승인 UX 필수 (3단계 자율성 레벨)
- 로컬 실행 원칙 불변
- Git 기반 롤백 내장
- 안전 경계는 코드 레벨
- v1.0 범위 엄격 제한

### Phase 2 Green Zone (5개 기술 팀메이트 동의)
- YAML SOT 패턴 (Plan 불변 / State 가변)
- Event Sourcing 기반 롤백
- ReAct + CoT 실행 엔진
- MCP 호환 설계
- 단일 에이전트 v1.0
- 안전 코드는 Day 1부터 클린하게

---

---

## Phase 3: 코딩·구현 기술 심층조사 (deep-dive-impl/)

| 파일 | 내용 | 상태 |
|------|------|------|
| `11_impl_synthesis.md` | Phase 3 전체 종합 + ADR | ✅ |
| `branch-1.1-cutting-edge-tech.md` | Claude SDK 최신 패턴 (Tool Use, async DAG, MCP) | ✅ |
| `branch-1.2-proven-tech.md` | 검증된 기술 (Click + PyYAML + 순차 실행) | ✅ |
| `branch-2.1-evolutionary-arch.md` | 점진적 확장 아키텍처 (Spike → Production) | ✅ |
| `branch-2.2-complete-arch.md` | 완전 설계 아키텍처 (IProcessExecutor 등 인터페이스) | ✅ |
| `branch-3.1-speed-first-workflow.md` | 빠른 개발 워크플로우 (DEBT 태그, Spike 방법론) | ✅ |
| `branch-3.2-quality-first-workflow.md` | 품질 우선 워크플로우 (TDD, Golden Tests, CI/CD) | ✅ |
| `branch-4.1-debt-minimize.md` | 부채 최소화 (pyproject.toml + 전체 품질 게이트) | ✅ |
| `branch-4.2-debt-pragmatic.md` | 실용적 부채 관리 (5대 절대 부채 + DEBT_REGISTER) | ✅ |
| `branch-5.1-latest-theory-impl.md` | 최신 이론 구현 (Tool Use, Agent Loop, Pydantic) | ✅ |
| `branch-5.2-classic-theory-impl.md` | 고전 이론 구현 (FSM, Command Pattern, EventBus) | ✅ |

---

### Phase 3 Green Zone (5개 Teammate 동의)
- IProcessExecutor Day 1 인터페이스 (안전 경계 코드 레벨)
- Pydantic v2 LLM 출력 검증 (환각 방어)
- 5대 절대 부채 금지 (경로순회/shell=True/무검증/타임아웃없음/API키하드코딩)
- 보수적 기반 시작 (Click + PyYAML + 순차 실행)
- Safety-First Agent Loop (max_iterations=20 + 사용자 승인)
- state.yaml 원자적 쓰기 (sot_lib.py 패턴 재사용)
- DEBT 태그 시스템 (기술 부채 추적)

---

---

## Phase 4: 추가 심층조사 (deep-dive-extra/)

| 파일 | 내용 | 상태 |
|------|------|------|
| `12_extra_synthesis.md` | Phase 4 전체 종합 + v1.0 기능 범위 최종 확정 | ✅ |
| `branch-A-competitive-analysis.md` | 경쟁 도구 분석 (Open Interpreter, AutoGPT, n8n 등) | ✅ |
| `branch-B-positioning-strategy.md` | 포지셔닝 매트릭스 + 차별화 전략 + 경쟁 학습 | ✅ |
| `branch-C-cli-ux-flows.md` | 3단계 자율성 UX + 오류 상황별 흐름 + 상태 머신 | ✅ |
| `branch-D-cli-ux-implementation.md` | Rich 구현 패턴 + 참조 사례 (gh, poetry, Claude Code) | ✅ |
| `branch-E-security-attack-vectors.md` | 공격 벡터 (Prompt Injection, Path Traversal, Command Injection) | ✅ |
| `branch-F-security-defense-arch.md` | 4계층 방어 아키텍처 + 감사 로그 + 보안 테스트 전략 | ✅ |

---

### Phase 4 Green Zone (3개 에이전트 공통 동의)
- 로컬 + 전문가 특화 포지셔닝 고수 (경쟁 공백 독점)
- 확인 우선 기본값 (Supervised Mode 기본값)
- ConstitutionalPolicy YAML (AI 행동 헌법)
- 4계층 Defence in Depth
- Indirect Prompt Injection 방어 (DATA_BLOCK 패턴)
- 8대 절대 금지 보안 행위 시행
- v1.0 필수 인터랙션 9가지 확정

---

---

## Phase 5: 외부 연동 기술 심층조사 (deep-dive-integration/)

| 파일 | 내용 | 상태 |
|------|------|------|
| `13_integration_synthesis.md` | Phase 5 전체 종합 + 연동 아키텍처 다이어그램 | ✅ |
| `branch-1.1-multi-ai-aggressive.md` | 멀티 AI 적극적 연동 (MultiModelRouter: Claude+Gemini CLI+Ollama) | ✅ |
| `branch-1.2-multi-ai-conservative.md` | 멀티 AI 보수적 연동 (Claude 우선 폴백 체인 + 응답 캐싱) | ✅ |
| `branch-2.1-mcp-server.md` | MCP 서버 구현 (FastMCP 4개 도구 + Claude Desktop 연동) | ✅ |
| `branch-2.2-mcp-client.md` | MCP 클라이언트 패턴 (외부 MCP 서버 연동) | ✅ |
| `branch-3.1-rich-tool-ecosystem.md` | 도구 통합 풍부한 에코시스템 (GitCheckpointManager, SafeWebClient) | ✅ |
| `branch-3.2-minimal-integration.md` | 최소 stdlib 통합 (MinimalSafeExecutor, MinimalGit, PollingWatcher) | ✅ |
| `branch-4.1-rich-data-integration.md` | 데이터 파이프라인 풍부한 통합 (SQLite, DuckDB, orjson, Parquet) | ✅ |
| `branch-4.2-minimal-data.md` | 데이터 파이프라인 최소 통합 (DataPipelineExecutor stdlib 전용) | ✅ |
| `branch-5.1-latest-sdk-docs.md` | 최신 SDK 공식 패턴 (Tool Use, Prompt Caching, SecretManager) | ✅ |
| `branch-5.2-implementation-reference.md` | 구현 참조 패턴 (프로세스 그룹 관리, pyproject.toml 전체 의존성) | ✅ |

---

### Phase 5 Green Zone (5개 에이전트 공통 동의)
- Claude API 우선 — anthropic SDK + API Key (필수)
- shell=False 절대 원칙 — subprocess 모든 호출에 적용
- Ollama = OpenAI의 현실적 대안 — 공식 OpenAI 구독 CLI 없음
- Gemini CLI v1.0 선택적 포함 — 자동화 환경에서 API Key 방식 사용
- MCP 서버로 패키징 (v1.0 필수) — FastMCP 1-2일 구현, Claude Desktop 네이티브
- 의존성 계층 분리 — Core(stdlib) → [data] → [analytics] extras
- gitpython 대신 MinimalGit — CVE-2024-22190 위험 없음, 의존성 0
- Prompt Caching 적용 — 반복 호출 비용 90% 절감
- SecretManager (keyring) — OS 네이티브 자격증명 관리
- EUC-KR 인코딩 지원 — 한국 레거시 데이터 처리 필수

---

## 전체 조사 현황

| Phase | 폴더 | 파일 수 | 핵심 주제 |
|-------|------|--------|----------|
| Phase 1 | (루트) | 6개 | 시장/사용자/기술/비즈니스 |
| Phase 2 | deep-dive-coding/ | 12개 | 기술 이론 심층 (5팀×2브랜치) |
| Phase 3 | deep-dive-impl/ | 11개 | 코딩 구현 기술 (5팀×2브랜치) |
| Phase 4 | deep-dive-extra/ | 7개 | 경쟁/UX/보안 (3팀×2브랜치) |
| Phase 5 | deep-dive-integration/ | 11개 | 외부 연동 기술 (5팀×2브랜치) |
| **합계** | | **47개** | |

---

## 다음 단계

- [x] Phase 5 외부 연동 기술 심층조사 완료
- [ ] 모든 조사 결과 최종 종합 (Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5)
- [ ] PRD.md 초안 작성 (사용자 승인 후)
