# Phase 5 외부 연동 기술 심층조사 종합
> External Integration: Multi-AI Models + MCP + Tools + Data + SDK
> 조사일: 2026-04-07

---

## 참여 에이전트

| 역할 | 브랜치 | 파일 | 상태 |
|------|--------|------|------|
| Multi-AI 모델 연동 전문가 | 1.1 Aggressive / 1.2 Conservative | branch-1.x | ✅ |
| MCP 프로토콜 통합 전문가 | 2.1 서버 / 2.2 클라이언트 | branch-2.x | ✅ |
| 외부 도구 & 셸 통합 전문가 | 3.1 Rich / 3.2 Minimal | branch-3.x | ✅ |
| 데이터 파이프라인 & 포맷 전문가 | 4.1 Rich / 4.2 Minimal | branch-4.x | ✅ |
| 공식 SDK 문서 & 구현 참조 전문가 | 5.1 최신 SDK / 5.2 구현 참조 | branch-5.x | ✅ |

---

## 팩트 체크: 핵심 발견 사항

### OpenAI 구독 계정 CLI — 중요 사실 확인

| 방법 | 가능 여부 | 비고 |
|---|---|---|
| Codex CLI (`codex login`) | ✅ 가능 | ChatGPT Plus/Pro, 코딩 에이전트 전용 |
| openai Python SDK (구독 인증) | ❌ 불가 | API Key 필수 |
| ChatGPT 웹 비공개 API | ❌ 불가 | ToS 위반, 불안정 |
| "구독으로 API 무제한 호출" | ❌ 존재 안 함 | OpenAI 비즈니스 구조상 불가 |

**결론**: OpenAI 구독 계정으로 범용 API를 호출하는 공식 방법은 없음. **Ollama 로컬 모델이 유일한 현실적, 합법적 대안.**

### Gemini CLI 구독 연동 — 실용성 평가

- **공식 도구**: `@google/gemini-cli` (Apache 2.0, GitHub 오픈소스)
- **OAuth 방식**: 대화형 터미널에서 안정적. Python subprocess에서는 TTY 감지 버그
- **자동화 권장**: `GEMINI_API_KEY` 환경변수 방식
- **정책 주의**: Google 공식 입장에서 제3자 앱의 OAuth 사용은 정책 위반 가능

---

## 5개 에이전트 핵심 발견 요약

### 1. Multi-AI Model Integration (Branch 1.x)

**v1.0 권장 아키텍처**: Claude API → Gemini CLI (선택적) → Ollama (폴백)

```
Claude Sonnet 4.6 (주)
  ↓ rate limit/장애 시
Claude Haiku 4.5 (폴백)
  ↓ 전체 장애 시
Ollama llama3.2 (로컬 폴백)

별도 라우팅: 대용량 컨텍스트(>100K) → Gemini 2.5 Pro (1M context)
```

**의존성**:
- `anthropic>=0.40.0` (필수)
- `openai>=1.50.0` (Ollama 클라이언트용)
- Node.js 18+ + `@google/gemini-cli` (선택적)

### 2. MCP Protocol Integration (Branch 2.x)

**FastMCP 기반 4개 도구**: `execute_workflow`, `validate_workflow`, `list_plan_history`, `rollback_workflow`

**핵심**: stdio 방식 = 데이터 로컬 보장, Claude Desktop 네이티브 통합.
1-2일 내 구현 가능. pyproject.toml 진입점으로 `workflow-mcp-server` 명령어 배포.

**활용 가능한 공개 MCP 서버**: filesystem, git, memory, sequentialthinking

### 3. External Tool & Shell Integration (Branch 3.x)

**절대 불변 원칙**: `shell=False` + ALLOWED_COMMANDS allowlist

- `MinimalSafeExecutor`: stdlib 전용, 프로세스 그룹 관리, 메모리 제한
- `MinimalGit`: gitpython 없이 subprocess 직접 (CVE 위험 없음)
- `SafeFileOperations`: 경로 탈출 방지 + atomic write + trash 백업
- `PollingWatcher`: watchdog 없이 stdlib으로 파일 변경 감지

**gitpython 판정**: CVE-2024-22190 위험 → v1.0은 MinimalGit 사용 권장

### 4. Data Pipeline & Format Integration (Branch 4.x)

**v1.0 Standard 범위**:
```
CSV/JSON/JSONL/TXT (stdlib 기본)
  + Excel (openpyxl, extras)
  + Parquet (pyarrow, extras)
  + PDF 텍스트 추출 (pdfplumber, extras)
```

**v1.1으로 연기**: DuckDB, pandas, polars (analytics extras)

- EUC-KR 인코딩 지원 필수 (한국 데이터 처리)
- 실행 로그에 파일 해시 자동 기록 (재현성)
- `FileStateManager`: SQLite 없이 JSONL만으로 상태 관리 가능

### 5. Official SDK Docs & Implementation Reference (Branch 5.x)

**Anthropic SDK 핵심 패턴**:
- Prompt Caching: 5분/1시간 캐시, 90% 비용 절감
- Tool Use: 에이전트 루프 핵심 (`max_iterations=20`)
- Extended Thinking: 복잡한 플랜 생성에만 사용
- Retry: tenacity 기반 지수 백오프, 429/529 처리

**인증 관리**: `SecretManager` (환경변수 → .env → keyring → 사용자 입력)

---

## Phase 5 Green Zone (5개 에이전트 공통 동의)

1. ✅ **Claude API 우선** — anthropic SDK + API Key (필수)
2. ✅ **shell=False 절대 원칙** — subprocess 모든 호출에 적용
3. ✅ **Ollama = OpenAI의 현실적 대안** — 공식 OpenAI 구독 CLI 없음
4. ✅ **Gemini CLI v1.0 선택적 포함** — 자동화 환경에서 API Key 방식 사용
5. ✅ **MCP 서버로 패키징 (v1.0 필수)** — FastMCP 1-2일 구현, Claude Desktop 네이티브
6. ✅ **의존성 계층 분리** — Core(stdlib) → [data] → [analytics] extras
7. ✅ **gitpython 대신 MinimalGit** — CVE 위험 없음, 의존성 0
8. ✅ **Prompt Caching 적용** — 반복 호출 비용 90% 절감
9. ✅ **SecretManager (keyring)** — OS 네이티브 자격증명 관리
10. ✅ **EUC-KR 인코딩 지원** — 한국 레거시 데이터 처리 필수

---

## PRD에 반영해야 할 신규 발견 사항

### §1 제품 배경
- OpenAI 구독 계정 CLI 연동 불가 사실 명시 → Ollama 대체로 설계

### §3 안전 원칙
- `shell=False` + ALLOWED_COMMANDS를 코드 레벨에 하드코딩
- 제3자 도구(Gemini CLI OAuth)의 정책 위험 명시

### §5 외부 AI 연동
- Multi-AI 폴백 체인 명시: Claude Sonnet → Haiku → Ollama
- Gemini CLI: 대화형은 OAuth, 자동화는 API Key
- `SecretManager` 우선순위 명시

### §6 기능 명세
- MCP 서버 4개 도구 (`execute_workflow` 등) v1.0 필수
- `extras_require` 구조로 선택적 데이터 라이브러리

### §7 기술 아키텍처
- 의존성 계층: Core(stdlib) → [data] → [analytics] → [web]
- `MinimalSafeExecutor` + `MinimalGit` + `SafeFileOperations` Day 1

---

## v1.0 외부 연동 기능 범위 확정

### 필수 포함 (Must-Have)

**AI 모델**:
- Claude Sonnet/Haiku (API Key) — 플랜 생성 핵심
- Ollama (localhost, 선택적 설치) — 오프라인/폴백
- Prompt Caching 적용

**외부 도구**:
- MinimalSafeExecutor (subprocess, shell=False, allowlist)
- MinimalGit (subprocess git, 체크포인트)
- SafeFileOperations (경로 탈출 방지, atomic write)
- PollingWatcher 또는 watchdog (파일 변경 감지)

**데이터**:
- CSV/JSON/JSONL (stdlib 기본)
- EUC-KR 인코딩 지원

**인증/보안**:
- SecretManager (keyring + .env)
- ConstitutionalPolicy YAML 정책 엔진

**MCP**:
- FastMCP 서버 (4개 도구)
- Claude Desktop `claude_desktop_config.json` 연동

### 선택적 포함 (extras_require)

- `[data]`: openpyxl, pyarrow, pdfplumber, orjson
- `[analytics]`: duckdb, pandas, polars (v1.1)
- `[watch]`: watchdog
- `[mcp]`: mcp[cli]>=1.2.0

### 확실히 제외 (v1.1 이후)

- Gemini CLI MCP 서버 외부 클라이언트 연동 → v1.1
- DuckDB `duckdb_query` 스텝 → v1.1
- OpenAI Codex CLI 연동 → v2.0 (범용 API 없음)
- 멀티모델 자동 라우팅 UI → v1.1

---

## 전체 연동 아키텍처 다이어그램

```
자연어 입력
    │
    ▼
┌──────────────────────────────────────┐
│         플랜 생성 레이어             │
│  Claude Sonnet 4.6 + Prompt Cache    │
│  → (rate limit) Claude Haiku 4.5    │
│  → (장애) Ollama llama3.2           │
└──────────────────┬───────────────────┘
                   │ YAML 플랜
                   ▼
┌──────────────────────────────────────┐
│          안전 실행 레이어             │
│  MinimalSafeExecutor (shell=False)   │
│  ConstitutionalPolicy YAML 검증      │
│  SafePathResolver (경로 탈출 방지)   │
│  SafeFileOperations (atomic write)   │
└──────────────────┬───────────────────┘
                   │
          ┌────────┴────────┐
          ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│  Git 체크포인트  │  │ 데이터 처리       │
│  MinimalGit      │  │ CSV/JSON/JSONL   │
│  (rollback 내장) │  │ + [data] extras  │
└─────────────────┘  └──────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│        MCP 서버 (Claude Desktop)     │
│  execute_workflow / validate         │
│  list_plan_history / rollback        │
│  → stdio, 데이터 완전 로컬           │
└──────────────────────────────────────┘
```
