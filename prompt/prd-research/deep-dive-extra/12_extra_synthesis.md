# Phase 4 추가 심층조사 종합 결과
> Competitive Intelligence + CLI UX + Security Threat Modeling
> 조사일: 2026-04-07

---

## 참여 에이전트

| 역할 | 브랜치 | 파일 | 상태 |
|------|--------|------|------|
| Competitive Intelligence Analyst | A: 경쟁 분석 / B: 포지셔닝 | branch-A/B | ✅ |
| CLI UX Designer | C: 인터랙션 플로우 / D: 구현 패턴 | branch-C/D | ✅ |
| Security Threat Modeler | E: 공격 벡터 / F: 방어 아키텍처 | branch-E/F | ✅ |

---

## 3개 에이전트 핵심 발견 요약

### Competitive Intelligence Analyst

**경쟁 공백 식별**: "로컬 + 전문가/개발자 특화" 사분면이 현재 시장에서 비어있다.
- Open Interpreter: 로컬이지만 범용, 안전 기본값 없음, 재현성 없음
- AutoGPT: 비용 폭주 + 무한루프로 실패. 교훈: "자율성 극대화"는 실용성 없음
- n8n/Zapier: 클라우드 의존 또는 설치 복잡성, GUI가 개발자에게 불편
- LangChain: 의존성 지옥, 버전 불안정성 → 직접 구현이 유리

**핵심 포지셔닝 문구**:
> "자연어로 계획하고, YAML로 검토하고, 로컬에서 실행한다. AutoGPT의 자율성이 아니라 Git의 재현성으로 AI 워크플로우를 관리하는 도구."

### CLI UX Designer

**3단계 자율성 레벨 설계 완성**:
- Level 1 (Supervised): 모든 스텝마다 y/n/s/i 확인
- Level 2 (Semi-Auto): 안전 스텝 자동, 위험 스텝만 확인
- Level 3 (Autonomous): 허용 목록 내 자동, 목록 외 BLOCK

**5대 필수 UX 원칙**:
1. 행동 전 선언 (Declare Before Acting)
2. 언제든 빠져나올 수 있음 (Always Escapable)
3. 복구 가능성 명시 (Explicit Recoverability)
4. 자율성 레벨의 일관성 (Consistent Autonomy Contract)
5. 진단 가능한 실패 (Diagnosable Failure)

**3대 금지 안티패턴**:
- 침묵 실행 (Silent Execution)
- 되돌릴 수 없는 작업의 기본값 허용 (Destructive Default)
- 오류 소비자화 (Error Minimization)

### Security Threat Modeler

**최고 위험도 벡터**: Indirect Prompt Injection (파일 내 숨겨진 지시문) — 기존 보안 도구로 감지 어려움.

**8대 절대 금지 행위**:
1. `shell=True` 사용
2. `yaml.load()` / `yaml.full_load()` 사용
3. API 키 하드코딩 (코드, YAML, 로그 모두)
4. `subprocess`에 전체 `os.environ` 전달
5. 사용자 입력의 `eval()`/`exec()` 실행
6. AI가 생성한 경로의 검증 없는 파일 접근
7. `sudo`/`su`/`bash`/`sh` 허용 목록 포함
8. 로그에 민감 데이터 평문 기록

**4계층 방어 모델**: 입력 계층 → 플랜 계층 → 실행 계층 → 감사 계층

---

## Phase 4 Green Zone (3개 에이전트 공통 동의)

1. ✅ **로컬 + 전문가 특화 포지셔닝 고수** — 경쟁 공백을 독점하는 유일한 전략
2. ✅ **확인 우선 기본값** — Supervised Mode가 기본, 자동화는 사용자가 명시적으로 설정
3. ✅ **ConstitutionalPolicy YAML** — AI 행동 헌법, 절대 금지 명령 + 허용 목록
4. ✅ **4계층 Defence in Depth** — 입력/플랜/실행/감사 각 계층 독립 방어
5. ✅ **Indirect Prompt Injection 방어** — 데이터 경계 격리 (DATA_BLOCK 패턴)
6. ✅ **v1.0 필수 인터랙션 9가지** — init/run/confirm/Ctrl+C/fail/summary/rollback/history/config
7. ✅ **v2.0으로 미룰 것 명확화** — GUI, 다중 에이전트 UI, 플랜 템플릿 라이브러리

---

## PRD에 반영해야 할 신규 발견 사항

### 경쟁 분석에서 도출

- **§1 제품 배경**: 경쟁 도구의 실패 원인(AutoGPT 무한루프, LangChain 의존성 지옥)을 설계 원칙 근거로 명시
- **§4 포지셔닝**: "로컬 + 재현 가능 + 전문가 특화"를 단 하나의 포지셔닝 선언문으로 정의
- **§7 로드맵**: 플랜 재사용/파라미터화 기능은 v1.1 우선순위로 격상 (경쟁 우위 확장)

### CLI UX에서 도출

- **§5 UX**: 3단계 자율성 레벨을 PRD에 명시 (Level 1/2/3 정의, 기본값, 전환 조건)
- **§5 UX**: YAML 플랜에 `user_description` 필드 추가 (기술적 세부사항과 분리)
- **§5 UX**: 5대 필수 UX 원칙과 3대 금지 안티패턴을 PRD 요구사항으로 포함
- **§6 기능 명세**: v1.0 필수 인터랙션 9가지를 기능 요구사항 목록에 추가

### 보안에서 도출

- **§3 안전 원칙**: 8대 절대 금지 행위를 "Non-Negotiable Security Requirements"로 PRD에 포함
- **§3 안전 원칙**: ConstitutionalPolicy YAML 스키마를 아키텍처 섹션에 포함
- **§6 기능 명세**: Append-Only JSONL 감사 로그를 v1.0 필수 기능으로 확정
- **§8 출시 기준**: v1.0 보안 체크리스트 (레드팀 시나리오 RT-001~RT-004 통과 포함)

---

## v1.0 기능 범위 최종 확정 (전체 Phase 1~4 통합)

### 반드시 포함 (Must-Have)

**핵심 플로우**
- 자연어 입력 → YAML 플랜 생성 (CoT 기반)
- 플랜 미리보기 + 위험도/롤백 가능성 표시
- 단계별 승인 UX (y/n/s/i)
- 3단계 자율성 레벨 설정

**안전 시스템**
- IProcessExecutor (허용 목록 + shell=False)
- SafePathResolver (resolve() + symlink 차단)
- ConstitutionalPolicy YAML 정책 엔진
- 4계층 Defence in Depth
- Indirect Prompt Injection 방어 (DATA_BLOCK 패턴)
- 8대 절대 금지 행위 시행

**복구 시스템**
- Command Pattern 기반 Undo/Rollback
- state.yaml 원자적 쓰기 (sot_lib.py 패턴)
- Append-Only JSONL 감사 로그

**CLI 경험**
- `autoflow init` wizard (3단계)
- Ctrl+C 일시정지 → 재개/롤백/중단 선택
- 실패 시 retry/skip/rollback/abort 옵션
- `autoflow history` + `autoflow rollback <id>`

### 확실히 제외 (Red Zone)

- GUI/웹 대시보드 → v2.0
- 플랜 템플릿 라이브러리 → v1.1
- 다중 에이전트 병렬 실행 UI → v2.0
- 플러그인 아키텍처 (RCE 벡터) → v2.0 (서명 체계 후)
- Ollama 로컬 모델 → v1.1 (ILLMProvider 추출 후)
- async DAG (사용자 피드백 기반) → v0.2
