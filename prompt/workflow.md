# Church Youth Retreat App Auto-Generation Workflow

> **코딩 경험 제로인 사역자가 Claude Code와 한국어 대화만으로, 중학생이 "이거 진짜 앱이다!"라고 느끼는 수준의 수련회 앱을 처음부터 끝까지 자동으로 완성한다.**

## Overview

- **Input**: 사역자의 한국어 대화 (앱 유형, 콘텐츠, 디자인 선호)
- **Output**: 완성된 수련회 웹앱 (HTML/CSS/JS + LAN 서버 + QR코드 + "앱 실행.bat")
- **Frequency**: On-demand (수련회 준비 시)
- **Autopilot**: enabled — Phase 2~4, 6은 자동 실행. Phase 1, 5만 사역자 개입.
- **pACS**: enabled — 각 Phase 완료 시 자체 품질 평가
  - Dimensions: F (콘텐츠 정확성 — 사역자 의도 반영도), C (기능 완전성 — 요청 기능 구현 여부), L (코드 정확성 — 에러 없이 실행 여부)
  - Scoring: pACS = min(F, C, L) — GREEN ≥70 auto-proceed, YELLOW 50-69 proceed with flag, RED <50 rework
- **Context Injection**: Pattern A (Full Delegation) — 모든 데이터 <50KB, Claude Code 직접 접근
- **Checkpoint Pattern**: standard (≤10 턴/Step) — 전 단계 적용
- **Review**: none (전 단계) — 단일 세션 역할 전환 구조이므로 별도 @reviewer/@fact-checker 불필요. 품질은 Q1-Q10 + D1-D6 게이트가 보장

---

## Inherited DNA (Parent Genome)

> This workflow inherits the complete genome of AgenticWorkflow.
> Purpose varies by domain; the genome is identical. See `soul.md §0`.

**Constitutional Principles** (adapted to this workflow's domain):

1. **Quality Absolutism** — 완성된 앱이 중학생에게 "이거 진짜 앱이다!"라는 반응을 이끌어내는 것이 유일한 품질 기준. 속도, 토큰 비용, 단계 수는 완전히 무시한다. 디자인 품질(D1~D6)과 기술 품질(Q1~Q10)을 모두 통과해야만 완성으로 인정한다.
2. **Single-File SOT** — 프로젝트 폴더 내 `app-state.json`에 모든 상태 집중. 의도, 콘텐츠, 검증 결과, 배포 정보가 이 단일 파일에 기록된다. Claude Code가 유일한 실행 주체이자 쓰기 권한자.
3. **Code Change Protocol** — 코드 생성(Phase 3) 및 수정(Phase 5)에서 의도→영향→설계 3단계 수행. 코딩 기준점(CAP-1~4) 내면화. 특히 수정 요청 시 최소 범위 변경 원칙(CAP-4 외과적 변경) 필수.
   - **CAP-1 (Think Before Code)**: 코드 작성 전 의도와 구조를 먼저 설계
   - **CAP-2 (Simplicity First)**: 가장 단순한 구현을 우선 선택 (사역자 PC 환경 안정성)
   - **CAP-3 (Goal-Driven Execution)**: 사역자의 요청 목표에만 집중, 불필요한 확장 금지
   - **CAP-4 (Surgical Change)**: 수정 시 최소 범위만 변경 (색상 변경에 전체 재생성 금지)

**Inherited Patterns**:

| DNA Component | Inherited Form |
|--------------|---------------|
| 3-Phase Structure | Research (Phase 0-1) → Planning (Phase 2) → Implementation (Phase 3-6) |
| SOT Pattern | `app-state.json` — single writer (Claude Code, 단일 세션) |
| 4-Layer QA | L0 Anti-Skip (산출물 존재) → L1 Verification (Q1-Q10 + D1-D6) → L1.5 pACS → L2 사역자 확인 (Q10) |
| P1 Data Refinement | 대량 콘텐츠는 파일 입력 → 노이즈 제거 후 코드에 삽입 |
| P2 Expert Delegation | 단일 세션 내 4가지 역할 전환 (대화→코드→검증→배포) |
| Safety Hooks | XSS 방지, 외부 전송 금지, API 키 보호, 프로젝트 폴더 외부 접근 금지 |
| Decision Log | Git 커밋 메시지가 decision log 역할 (체크포인트 기반) |
| Context Preservation | 파일 기반 상태 저장 + Git 히스토리로 세션 중단/재개 지원 |

**Domain-Specific Gene Expression**:
- **P2(전문성 기반 위임) 강하게 발현**: 4가지 역할이 각각의 전문 영역에 집중. 역할 1은 한국어 대화와 UX에, 역할 2는 코드 품질에, 역할 3는 검증에, 역할 4는 배포 안정성에 집중.
- **P1(데이터 정제) 강하게 발현**: 사역자의 자연어 입력을 구조화된 데이터로 정제하여 코드 생성 정확도를 극대화.
- **Safety Hooks 강하게 발현**: 교회 환경 특성상 콘텐츠 안전성, 개인정보 최소 수집, 비용 제로 원칙이 필수.
- **CCP(코드 변경 프로토콜) 적응적 발현**: 새 앱 생성 시에는 전체 생성 흐름, 수정 요청 시에는 최소 범위 변경(CAP-4).

---

## The North Star (절대 목표)

> 이 워크플로우의 모든 단계, 모든 결정, 모든 출력은 아래 단 하나의 목표를 기준으로 판단한다.

```
코딩 경험 제로인 사역자가
   ↓
Claude Code와 한국어 대화만으로
   ↓
중학생이 "이거 진짜 앱이다!"라고 느끼는 수준의 앱을
   ↓
처음부터 끝까지 (기획 → 생성 → 테스트 → 배포 → QR 공유)
자기 PC에서 완성한다.
```

**검증 질문 (모든 설계 결정에 적용)**:
1. "코딩을 모르는 사역자가 이 단계에서 막히지 않는가?"
2. "완성된 결과물을 중학생이 보고 '이거 진짜 앱이다'라고 느끼는가?"

둘 중 하나라도 "No"라면, 그 결정은 재검토 대상이다.

---

## Absolute Constraints (절대 제약)

### AC1. 로컬 컴퓨터 실행 원칙

```
✅ 허용: 사역자 PC에서 파일 생성, 코드 작성, 서버 실행
✅ 허용: 같은 WiFi/핫스팟 내 LAN 접속
✅ 허용: Claude API 호출 (Claude Code 자체 동작에 필요)

❌ 금지: 외부 서버/서비스를 경유하는 데이터 전송
❌ 금지: 제3자 SaaS 서비스에 의존하는 기능
❌ 금지: 사역자 동의 없이 인터넷에 데이터 노출
❌ 금지: ngrok 등 터널링 서비스 사용

GitHub Pages는 사역자가 명시적으로 동의한 경우에만 사용 (선택 사항).
기본 동작은 항상 로컬 컴퓨터 + LAN이다.
```

### AC2. 사역자 대화 규칙

| 규칙 | 위반 사례 |
|------|-----------|
| **한국어 전용** | 에러 메시지에 영어, 기술 로그 노출 |
| **코딩 용어 금지** | "JSON", "포트", "npm", "빌드", "[Y/n]" |
| **기술적 결정 자동화** | "어떤 데이터베이스를 쓸까요?" |
| **결과 중심 소통** | 기술 스펙 선택지 제시 |
| **질문 최대 2개/턴** | 한 번에 5가지를 물어봄 |
| **예외: Phase 0** | 기술 도우미와 함께하므로 불가피한 용어 허용 (최소한으로) |

### AC3. 결과물 품질 기준

| 항목 | 기준 |
|------|------|
| 모바일 우선 | 375px 기준 완전 동작 |
| 터치 영역 | 모든 버튼 최소 44×44px |
| QR 진입 | QR코드 하나로 학생이 앱 접근 |
| 설치 불필요 | 학생은 브라우저만으로 사용 |
| 즉시 사용 | 회원가입/로그인 없이 (닉네임만) |
| 디자인 품질 | 카드 UI, 애니메이션, 다크모드 — "진짜 앱처럼" |
| 번들 크기 | 목표 300KB / 상한 500KB (gzip, 시스템 폰트 전용 — 성찰 G8 + M3 조화) |
| 동시 접속 | 35명 기본, 최대 50명 |

### AC4. 안전 & 보안

| 원칙 | 내용 |
|------|------|
| XSS 방지 | 학생 입력(닉네임, 기도제목 등) 무해화 |
| 외부 전송 금지 | 생성 앱이 프로젝트 폴더 외부로 데이터 전송 안 함 |
| API 키 보호 | 사역자 API 키가 생성 앱 코드에 포함 안 됨 |
| 개인정보 최소 수집 | 닉네임 외 수집 금지 (실명, 학교명, 전화번호 등) |
| 콘텐츠 적절성 | 교회 환경에 적합한 콘텐츠만 |
| Git 체크포인트 | 모든 변경 전 자동 커밋 — 즉시 롤백 가능 |
| 네이티브 컴파일 금지 | node-gyp 필요 패키지 사용 안 함 (SQLite 등) |

---

## workflow.md의 정체성

```
workflow.md는 Claude Code가 읽고 따르는 "내부 지시서"이다.

  - SaaS 제품의 설계도가 아니다.
  - 별도의 소프트웨어 시스템을 구축하는 것이 아니다.
  - Claude Code라는 기존 도구가 "이 문서를 읽고"
    사역자와 대화하면서 앱을 자동으로 만들어주는 것이다.

workflow.md의 역할:
  사역자가 Claude Code를 실행한다
  → Claude Code가 workflow.md를 읽는다
  → workflow.md에 적힌 대로 사역자와 대화한다
  → workflow.md에 적힌 대로 코드를 생성하고 서버를 실행한다
  → 사역자는 workflow.md의 존재를 모른다 (내부 지시서)
```

---

## Activation Mechanism (실행 활성화) — 성찰 N1

> workflow.md가 아무리 완벽해도 Claude Code에 연결되지 않으면 실행 불가.
> 이 섹션은 "악보를 연주자에게 건네는 방법"을 정의한다.

### 1. CLAUDE.md 수정 사항 (구현 시 반영)

```markdown
# CLAUDE.md의 "스킬 사용 판별" 테이블에 추가:

| 사용자 요청 패턴 | 스킬 | 진입점 |
|----------------|------|--------|
| "수련회 앱", "앱 만들어줘", "교회 앱" | church-retreat-app | prompt/workflow.md |
```

### 2. 슬래시 커맨드 파일 사양 (구현 시 생성)

```yaml
# .claude/commands/start-app.md
---
description: "수련회 앱 생성 워크플로우 시작"
---
prompt: |
  Read prompt/workflow.md completely.
  Then start from Step 2 (App Menu Presentation).
  Present the 수련회 앱 메뉴판 to the user in Korean.
  Follow all instructions in workflow.md exactly.

# .claude/commands/resume-app.md
---
description: "중단된 앱 생성 재개"
---
prompt: |
  Read prompt/workflow.md completely.
  Then read app-state.json from the project folder.
  Check %USERPROFILE%\.last-church-app-path for project path.
  Resume from the phase indicated by app-state.json status.
  Tell the user in Korean: "이전에 만들던 앱이 있어요. 이어서 할까요?"

# .claude/commands/deploy-app.md
---
description: "완성된 앱 배포 실행"
---
prompt: |
  Read prompt/workflow.md Step 10 (Deployment).
  Execute deployment for the current project.
```

### 3. 사역자의 첫 경험 흐름

```
[시나리오 A] 사역자가 "수련회 앱 만들어줘"라고 입력
  → CLAUDE.md의 스킬 판별 패턴 매칭
  → Claude Code가 workflow.md를 자동으로 읽음
  → Step 2 메뉴판부터 시작

[시나리오 B] 사역자가 "/start-app"을 입력 (기술 도우미가 알려줌)
  → 슬래시 커맨드가 workflow.md를 로드
  → Step 2 메뉴판부터 시작

[시나리오 C] 사역자가 아무것도 모르고 Claude Code를 실행
  → Claude Code 기본 대화 모드
  → 사역자가 수련회/앱 관련 키워드를 말하면 자동 트리거
  → "수련회 앱을 만들어드릴까요?" 확인 후 workflow.md 로드

사역자에게 터미널 안내 (Phase 0 설치 완료 시 전달):
  "Claude Code를 실행하면 검은 화면이 나와요.
   거기에 '수련회 앱 만들어줘'라고 입력하세요.
   그러면 제가 안내해 드릴게요."
```

### 4. SessionStart Hook 연동 (선택)

```python
# .claude/hooks/scripts/detect_church_app.py (구현 시 생성)
# SessionStart 시 %USERPROFILE%\.last-church-app-path 존재 확인
# 존재하면 stdout에 프로젝트 경로 출력 → Claude Code에 컨텍스트 제공
```

---

## Context Loading Strategy (컨텍스트 로딩 전략) — 성찰 N2

> workflow.md 전체(~28K 토큰)를 한번에 로드하면 앱 코드 생성 컨텍스트가 부족해진다.

### 분할 전략

```
[Phase 시작 시 로드하는 것] (항상 상주 — 핵심 규칙 ~300줄)
  → The North Star (절대 목표)
  → Absolute Constraints (AC1~AC4)
  → Role Definitions (4가지 역할)
  → 현재 Phase의 Step 정의
  → app-state.json 현재 상태

[필요 시 on-demand 로드] (해당 Phase에서만)
  → Phase 1: 대화 프로토콜, 콘텐츠 매트릭스, 메뉴판 템플릿
  → Phase 2: 기술 스택 선택표, 폴더 우선순위, 디자인 시스템
  → Phase 3: 코드 생성 순서, 서버 코드 패턴, 실시간 아키텍처
  → Phase 4: Q1~Q11 + D1~D9 품질 게이트 상세
  → Phase 5: 수정 루프 규칙, 롤백 메커니즘
  → Phase 6: .bat 사양, 네트워크 전략, 배포 메시지

[로드하지 않는 것] (참조용 — 구현 시에만 사용)
  → Activation Mechanism (이미 실행 후이므로)
  → Adversarial Review Tracking (문서 이력)
  → Distill Verification Checklist (문서 이력)
```

### 실행 원칙

```
Claude Code는 workflow.md 전체를 한번에 읽지 않는다.
슬래시 커맨드 또는 스킬 트리거 시:
  [1] 핵심 규칙 (~300줄)을 먼저 로드
  [2] 현재 Phase의 Step 정의를 로드
  [3] Phase 전환 시 이전 Phase 상세를 컨텍스트에서 해제하고
      다음 Phase 상세를 로드
  [4] 항상 app-state.json을 Phase 전환 시 다시 읽어 상태 확인
```

---

## Role Definitions (역할 단계 정의)

> Claude Code가 **단일 대화 세션**에서 4가지 역할을 순서대로 수행한다.
> "에이전트 팀"이 아니라 **"역할 전환"**이다. 실행 주체는 항상 Claude Code 하나.

### Role 1: Conversation Guide (대화 진행) — Phase 0, 1, 5

- 사역자 대화 관리 (의도 파악, 확인 신호 판단)
- 앱 유형 감지 + 필요 정보 재질문 + 콘텐츠 수집
- 에러 발생 시 사역자에게 보이는 메시지 관리 (한국어, 기술 용어 금지)
- 각 Phase 완료 시 명시적 단계 전환 출력
- 이전 앱 재사용 요청 감지
- **대화 규칙**: AC2 전체 준수

### Role 2: Code Generator (코드 생성) — Phase 2, 3, 5(수정)

- HTML 구조 + 한국어 콘텐츠 삽입
- CSS (모바일 우선 375px, 44px 터치 영역, 다크모드, 디자인 시스템)
- JavaScript 로직 (XSS 방어, 오프라인 캐시, 실시간 기능)
- 9개 앱 유형별 코드 직접 작성 (템플릿이 아닌 대화 기반 생성)
- 수정 요청 시 최소 범위 변경 (색상 변경에 전체 재생성 안 함 — CAP-4)
- 번들 목표 300KB / 상한 500KB (시스템 폰트 전용, 웹폰트 0KB — 성찰 G8 + M3)
- 모든 앱에 결과 저장 기능 기본 포함
- "앱 실행.bat" 파일 자동 생성
- **기술 스택**: Node.js + Express, 네이티브 WebSocket (Socket.io 대신), lowdb/JSON 파일 (SQLite 대신), 시스템 폰트 우선

### Role 3: Quality Checker (품질 검증) — Phase 4

- **기술 품질 게이트 (Q1~Q10)** + **디자인 품질 게이트 (D1~D6)** 자동 실행
- 실패 시 자동 수정 후 재검증 (최대 3회)
- 3회 실패 시 Git 롤백 후 사역자에게 보고
- Q10만 사역자 수동 확인 (유일한 human 검증)

### Role 4: Deployment Manager (배포 실행) — Phase 6

- LAN 서버 백그라운드 실행
- WiFi IP 자동 감지 (일반 WiFi / 모바일 핫스팟)
- QR 코드 PNG 생성 + 인쇄용 HTML (A4)
- 브라우저 자동 열기
- "앱 실행.bat" 바탕화면 자동 배치
- GitHub Pages 배포 (선택, 사역자 동의 시에만)
- 환경 감지: 포트(3000~3009 + 8080, 49152~49162), 디스크, 한글 경로, 방화벽

### Role Transition (역할 간 전환)

```
각 역할 단계 완료 시 산출물을 프로젝트 폴더에 파일로 저장한다.

  [대화 진행] 완료 → app-state.json에 의도/콘텐츠 기록
  [코드 생성] 완료 → 실제 코드 파일 + Git 커밋
  [품질 검증] 완료 → app-state.json에 검증 결과 기록
  [배포 실행] 완료 → app-state.json에 서버 URL, QR 경로 기록

Claude Code 세션이 끊어져도 파일은 남아 있으므로 재개 가능.
```

---

## Research Phase

> Phase 0 (환경 사전 준비) + Phase 1 (대화 & 콘텐츠 수집)
> 사역자의 의도와 콘텐츠를 수집하여 구조화하는 단계.

### Step 1. (human) Environment Setup — Phase 0

> **⏰ 권장 시기**: 수련회 **최소 1주일 전**에 완료할 것. Step 0만 미리 해두면 나머지(앱 생성~배포)는 1~2시간이면 충분하다. 수련회 3일 전에 처음 시작하면 시간 압박으로 좌절할 수 있다.

- **Action**: 기술 도우미(또는 사역자 본인)가 Claude Code 실행 환경을 준비한다.
- **Autopilot Default**: skip — 환경 사전 준비는 반드시 사람이 수행해야 하므로 Autopilot에서도 자동 승인하지 않음
- **Verification**:
  - [ ] Node.js installed (`node --version` responds)
  - [ ] Claude Code installed and API key authenticated
  - [ ] Disk space ≥ 2GB available
  - [ ] Antivirus allows Node.js execution
  - [ ] npm registry reachable (`npm ping` responds)
  - [ ] (Optional) Git installed + GitHub authenticated for GitHub Pages
- **Pre-requisites**:
  - Windows 10/11 PC
  - Internet connection
  - Administrator privileges for software installation
- **Task**: Install Node.js and Claude Code. Configure antivirus exceptions. Verify disk space and npm connectivity. Optionally set up Git/GitHub for Pages deployment.
- **Output**: Verified development environment ready for app generation
- **Review**: none
- **Translation**: none (technical setup, not user-facing content)

**Environment Checklist**:
```
[ ] Node.js 설치 완료 (node --version 응답)
[ ] Claude Code 설치 완료 + API 키 인증 성공
[ ] 디스크 공간 2GB 이상
[ ] 백신에서 Node.js 허용됨
[ ] npm 레지스트리 접속 가능 (npm ping 응답)
[ ] (선택) Git 설치 + GitHub 인증
```

**[C1 수정] Phase 0은 Claude Code 실행 전이므로 Claude Code가 안내할 수 없다**:
> Phase 0의 안내는 Claude Code에 의존하면 안 된다. 다음 3가지 독립 경로를 제공한다:

```
[경로 1] 그림 포함 설치 가이드 PDF (Claude Code 없이 독립 수행 가능)
  → Phase 6 완료 시 Claude Code가 자동으로 "설치 가이드.pdf"를 프로젝트 폴더에 생성
  → 이 PDF를 다른 사역자에게 공유하면 그 사역자도 독립적으로 설치 가능
  → 최초 1회는 이 워크플로우를 실행하는 사람(또는 기술 도우미)이 수동 설치

[경로 2] 기술 도우미가 있는 경우
  → 교회 청년부에서 컴퓨터 아는 분이 1회 도와줌
  → Claude Code 실행 후부터는 사역자 혼자 진행 가능

[경로 3] 기술 도우미 없이 혼자 하는 경우
  → Claude Code 공식 설치 페이지(https://claude.ai/download)의 안내를 따름
  → 설치 과정 중 막히면: 카카오톡 화면 공유로 지인에게 원격 도움 요청
  → Claude Code 실행만 성공하면, 이후 모든 과정은 한국어 대화로 진행
```

**[M4 수정] npm install 실패 시 교회 네트워크 대응**:
```
Phase 0 완료 후, 첫 번째 앱 생성 시 npm install이 실패하면:

[1] npm ping 사전 검증 (Phase 2 시작 시 자동 실행)
    → 실패 시: 프록시/방화벽 원인 진단

[2] 자동 대응 순서:
    → npm config set registry https://registry.npmmirror.com (미러 레지스트리)
    → NODE_TLS_REJECT_UNAUTHORIZED=0 임시 설정 (SSL 인스펙션 우회)
    → 최대 3회 재시도

[3] 최후 수단: 오프라인 설치 경로
    → Claude Code가 필요한 패키지를 node_modules.zip으로 번들링
    → 프로젝트 폴더에 압축 해제하여 npm install 없이 진행

[4] 사역자에게 안내:
    → "인터넷 연결에 문제가 있어서 다른 방법으로 준비하고 있어요."
```

**Claude Code Permission Setup**:
> workflow.md에서 안전한 작업(파일 생성, 서버 실행 등)은 자동 허용되도록 설정을 미리 구성한다.
> 사역자가 매번 "허용" 버튼을 누르지 않아도 되게 함.

---

### Step 2. App Menu Presentation & Intent Detection — Phase 1 (Part A)

- **Agent**: Claude Code (Role 1: Conversation Guide)
- **Verification**:
  - [ ] App type identified from 9 supported types (or combination)
  - [ ] Team count and team names confirmed by 사역자
  - [ ] Design palette selected (A/B/C or custom)
  - [ ] All required content types for the chosen app identified
  - [ ] 사역자 confirmation signal received ("네", "좋아요", "시작해주세요")
- **Task**: Present the "수련회 앱 메뉴판" to the 사역자. Detect app type through natural Korean conversation. Ask follow-up questions (max 2 per turn) with concrete examples. Identify all required content types. Get 사역자 confirmation on app structure.
- **Output**: Intent section in `app-state.json` (app type, team config, design palette, feature list)
- **Review**: none
- **Translation**: none (conversation is in Korean by nature)
- **Post-processing**: Validate intent data completeness in `app-state.json`

**Opening Message Template (수련회 앱 메뉴판)**:
```
"안녕하세요! 수련회 앱을 만들어드릴게요.
 이런 앱들을 만들 수 있어요:

 1) 성경 퀴즈 대회 — 팀끼리 버저 누르며 경쟁
 2) 팀 점수판 — 빔프로젝터에 실시간 순위 표시
 3) 수련회 일정표 — 학생 폰에서 일정 확인
 4) 찬양 가사 — 빔이랑 폰에 동시에 가사 표시
 5) 미션 스탬프 랠리 — QR코드로 미션 인증
 6) QT 가이드 — 매일 성경 묵상
 7) 사진 공유 — 수련회 사진 갤러리
 8) 기도제목 나눔 — 함께 기도해요
 9) 전부 합친 종합 앱

 🔥 많이 쓰이는 앱: 1번, 2번, 9번
 잘 모르겠으면 9번(종합 앱)을 추천해요!

 어떤 게 필요하세요? 여러 개 골라도 돼요!"
```

**Phase 1 대화 중 진행률 표시** (성찰 발견1):
```
각 턴마다 현재 위치를 사역자에게 알려준다:
  "[1/3] 어떤 앱인지 파악 중"   → 앱 유형 선택 전
  "[2/3] 필요한 내용 수집 중"   → 콘텐츠 수집 중
  "[3/3] 마지막 확인 중"        → 구조 미리보기 확인

예시: "좋아요! [2/3] 필요한 내용을 수집할게요. 팀이 몇 개인가요?"
```

**Conversation Flow Rules**:
```
사역자 발화 → Claude가 분류
  |-- 메뉴에서 선택 → 바로 필요한 콘텐츠 질문으로 이어감
  |-- 명확한 요청 → 바로 필요한 콘텐츠 질문으로 이어감
  |-- 모호한 요청 → 메뉴판 다시 제시 + 구체적 선택지 2~3개
  |-- 범위 밖 요청 → 이유 설명 + 대안 제시 (거절하지 않음)
  |-- "작년 앱 다시 쓰고 싶다" → archives/ 폴더에서 이전 앱 탐색
```

**Design Palette Selection**:
```
"어떤 분위기가 좋으세요?"
  [A] 차분한 느낌 (기본): 인디고 + 에메랄드
  [B] 활기찬 느낌: 보라 + 앰버
  [C] 따뜻한 느낌: 핑크 + 시안

사역자가 별도 요청 없으면 [A] 기본 적용.
```

**[m1 수정] 관리자 비밀번호 자동 처리**:
```
관리자 화면(/admin)이 필요한 앱:
  → 비밀번호를 자동 생성 (기본값: "1234")
  → 사역자에게: "진행자 화면에 들어가는 열쇠를 만들었어요. 열쇠는 '1234'예요."
  → 비밀번호를 인쇄물(QR 페이지)에 작게 포함
  → 사역자가 "비밀번호 바꿔줘"라고 하면 변경
  → 절대 "비밀번호를 설정하세요"라고 기술적 결정을 요구하지 않음
```

---

**⚠ Step 2 → Step 3 자연스러운 전환 규칙** (성찰 발견2 — E4 통합 원칙):
```
사역자에게는 별도 단계 전환을 알리지 않는다.
앱 유형 확정 후 자연스럽게 "좋아요! 몇 가지만 알려주세요."로 이어간다.
내부적으로만 app-state.json의 intent 섹션을 먼저 기록하고
대화를 끊지 않고 콘텐츠 수집으로 진입한다.

❌ 나쁜 예: "앱 유형이 확정되었습니다. 이제 콘텐츠 수집 단계입니다."
✅ 좋은 예: "성경 퀴즈 앱이요! 좋아요! [2/3] 팀이 몇 개인가요?"
```

### Step 3. Content Collection — Phase 1 (Part B)

- **Agent**: Claude Code (Role 1: Conversation Guide)
- **Verification**:
  - [ ] All required content for the chosen app type is collected (see content matrix below)
  - [ ] Content validated: no missing items, no obvious errors
  - [ ] Large content (11+ items) received via file, not conversation
  - [ ] 사역자 confirmed collected content accuracy ("맞아요", "네")
  - [ ] Content stored in `app-state.json` and/or separate content files
- **Task**: Collect all necessary content through natural conversation. For large content sets (11+ items), guide 사역자 to save in a text file on desktop. Read the file and confirm. Fix typos silently with one-line report.
- **Output**: Content section in `app-state.json` + content files in project folder
- **Review**: none
- **Translation**: none
- **Post-processing**: Validate content completeness against app type requirements

**Content Matrix by App Type**:

| App Type | Required Content | Collection Method |
|----------|-----------------|-------------------|
| 성경 퀴즈 | Quiz Q&A + team config | ≤10: 대화 / 11+: 텍스트 파일 / AI 생성: "요한복음에서 10문제 만들어줘" → Claude가 생성 → 사역자 확인 후 확정 (Bible Data Copyright Policy 참조) |
| 스탬프 랠리 | Mission locations + descriptions | Conversation |
| 일정표 | Schedule by date + location | Conversation (natural language) |
| 찬양 가사 | Song names + full lyrics | ≤3 songs: conversation / 4+: text file |
| QT 가이드 | Bible passages + reflection questions | Conversation |
| 팀 점수판 | Team names + team colors | Conversation |
| 사진 갤러리 | Gallery structure only (photos later) | Conversation |
| 기도제목 | Board settings only (students write) | Conversation |
| 종합 앱 | Selected features from above | Conversation |

**File Input Instructions (for 사역자)**:
```
"문제가 11개 이상이면, 메모장에 이렇게 적어서
 바탕화면에 저장해 주세요:

 1. 문제: 노아 방주에 탄 동물은 몇 쌍? / 정답: 한 쌍씩
 2. 문제: 모세가 건넌 바다 이름은? / 정답: 홍해
 ...

 파일 이름은 아무거나 괜찮아요.
 저장하셨으면 '저장했어요'라고 말씀해 주세요."
```

---

### Step 4. (human) Structure Preview & Confirmation

- **Action**: 사역자가 텍스트 기반 앱 구조 미리보기를 확인하고 승인한다.
- **Autopilot Default**: skip — 사역자 의도 확인은 워크플로우의 핵심이므로 Autopilot에서도 반드시 사역자 승인 필수. 이 단계를 건너뛰면 의도와 다른 앱이 생성되어 전체 재작업 위험.
- **Verification**:
  - [ ] App structure preview presented in Korean (no technical terms)
  - [ ] 사역자 explicitly confirmed ("네", "좋아요", "시작해주세요")
  - [ ] All modifications from 사역자 feedback incorporated before confirmation
- **Task**: Present the planned app structure as a simple Korean text preview. Wait for 사역자 confirmation signal.
- **Output**: Confirmed `app-state.json` with `research_complete: true`

**Structure Preview Template**:
```
"이렇게 만들게요!

 [학생 화면]
 - 팀 선택 → 버저 버튼 (크고 누르기 쉬운 버튼)
 - 점수 현황 실시간 표시

 [진행자 화면] (비밀번호 보호)
 - 문제 넘기기, 정답 공개, 점수 추가

 [빔프로젝터 화면]
 - 4팀 점수 대형 표시 + 애니메이션

 시작할까요?"
```

**Confirmation Signal Detection**:

| 사역자 발화 | 의미 | Claude 동작 |
|-------------|------|-------------|
| "네" / "좋아요" / "시작해주세요" | 승인 | 다음 Phase 진행 |
| "잠깐" / "잠시만" | 보류 | 대기, 30초 후 "천천히 생각하세요" |
| "이건 아닌데" / "바꿔주세요" | 수정 요청 | 수정 사항 파악 질문 |
| 무응답 (2분 이상) | 이탈 가능 | "혹시 다른 일 보고 계신가요?" |

---

## Planning Phase

> Phase 2 (프로젝트 초기화) — 앱 생성을 위한 기술 환경을 자동으로 준비하는 단계.

### Step 5. Project Initialization — Phase 2

- **Agent**: Claude Code (Role 2: Code Generator)
- **Verification**:
  - [ ] Project folder created at priority location (desktop > documents > C:\ > D:\)
  - [ ] Path contains no Korean characters (encoded path avoided)
  - [ ] Git repository initialized with initial commit
  - [ ] package.json created with required dependencies (no native compilation packages)
  - [ ] npm install completed successfully (all dependencies resolved)
  - [ ] `app-state.json` updated with `planning_complete: true`
- **Task**: Create project folder at optimal location. Initialize Git repository. Create package.json with dependencies based on app type (static vs realtime). Run npm install. Configure project structure.
- **Output**: Initialized project folder with Git, dependencies, and base structure
- **Review**: none
- **Translation**: none
- **Post-processing**: Verify folder structure matches app type requirements

**Folder Location Priority**:
```
1순위: 바탕화면\church-app\     (사역자가 찾기 쉬움)
2순위: 문서\church-app\         (바탕화면 권한 없을 시)
3순위: C:\church-app\           (위 둘 다 실패 시)
4순위: D:\church-app\           (C드라이브 권한 없을 시)
```

**Technology Stack Auto-Selection**:

| App Category | Technology | Reason |
|--------------|-----------|--------|
| Static (일정표, QT, 가사, 갤러리, 공지) | Pure HTML + CSS + JS | No server needed, GitHub Pages compatible |
| Realtime (퀴즈, 점수판, 가사 동기화) | Node.js + Express + native WebSocket | LAN server required |
| Hybrid (종합 앱) | Node.js + Express + WebSocket + static serving | Single entry point |

**Dependency Rules**:
- **금지**: SQLite, node-gyp, Python-dependent packages, native compilation packages
- **허용**: express, ws (WebSocket), lowdb, qrcode, open (browser open)
- **폰트**: Pretendard 서브셋(~50KB) + 시스템 폰트 폴백 (성찰 N5 — "윈도우 냄새" 제거, 50KB는 300KB 예산 안에 충분)
- **아이콘**: 인라인 SVG (외부 CDN 의존 제거)

**Progress Message to 사역자**:
```
"앱을 만들 준비를 하고 있어요. 잠시만 기다려 주세요."
```

---

### Step 6. Architecture Planning (Internal)

- **Agent**: Claude Code (Role 2: Code Generator)
- **Verification**:
  - [ ] URL structure defined (/, /admin, /screen as needed)
  - [ ] Data sync strategy selected (realtime vs static vs hybrid)
  - [ ] File structure planned matching app type
  - [ ] Design system variables configured (palette, typography, spacing, animation)
  - [ ] PWA service worker strategy planned (static cache, network-first for dynamic)
  - [ ] Admin authentication method planned (simple password)
- **Task**: Plan internal architecture based on app type and collected content. Define URL routes, file structure, data flow, and design system. This step is entirely internal — no 사역자 interaction.
- **Output**: Architecture plan appended to `app-state.json`
- **Review**: none
- **Translation**: none

**App Type → Architecture Mapping**:

| # | App Type | Data Sync | /admin | /screen | PWA | LAN | GitHub Pages |
|---|---------|-----------|--------|---------|-----|-----|-------------|
| 1 | 성경 퀴즈 | Realtime | O | O | O | O | X |
| 2 | 스탬프 랠리 | Individual→Server | O | X | O | O | X |
| 3 | 일정표 & 공지 | Static | X | X | O | O | O (optional) |
| 4 | 찬양 가사 | Realtime | O | O | O | O | X |
| 5 | QT 가이드 | Static | X | X | O | O | O (optional) |
| 6 | 팀 점수판 | Realtime | O | O | O | O | X |
| 7 | 사진 갤러리 | One-way | O | X | O | O | X |
| 8 | 기도제목 | Static+refresh | X | X | O | O | O (optional) |
| 9 | 종합 앱 | Hybrid | O | O | O | O | X |

**종합 앱(9번) 통합 아키텍처** (성찰 발견3):
```
종합 앱 = 단일 Express 서버가 모든 기능을 서빙하는 단일 진입점 구조.

URL 라우팅:
  /           → 메인 메뉴 (하단 탭 네비게이션)
  /quiz       → 성경 퀴즈 (WebSocket 실시간)
  /score      → 팀 점수판 (WebSocket 실시간)
  /schedule   → 수련회 일정표 (정적)
  /lyrics     → 찬양 가사 (WebSocket 실시간)
  /qt         → QT 가이드 (정적)
  /stamps     → 스탬프 랠리 (개별→서버)
  /gallery    → 사진 갤러리 (단방향)
  /prayer     → 기도제목 (정적+새로고침)
  /admin      → 통합 관리 콘솔 (비밀번호 보호)
  /screen     → 빔프로젝터 통합 뷰

통합 원칙:
  - 각 기능은 독립 JS 모듈이나 하나의 서버 프로세스에서 통합 실행
  - WebSocket 연결은 하나의 ws 서버에서 메시지 타입으로 라우팅
  - 정적 콘텐츠와 실시간 기능이 같은 포트에서 서빙
  - 학생에게는 QR코드 하나로 진입 → 탭으로 기능 전환
  - GitHub Pages 사용 안 함 (실시간 기능 포함이므로 LAN 전용)
  - 사역자가 선택한 기능만 포함 (9개 중 선택)
```

**Deployment Auto-Decision**:
```
실시간 기능이 하나라도 포함? → YES → LAN 서버 배포
                              → NO  → LAN 기본, GitHub Pages 선택 가능
```

**Design System Defaults** (성찰 N4+N5 반영 — 2026 중학생 트렌드):
```css
/* Color Palettes — 단색 + 그라데이션 프리셋 (성찰 N4) */
[A] 차분한 느낌 (default):
  --primary: #4F46E5;    --secondary: #10B981;
  --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
[B] 활기찬 느낌:
  --primary: #8B5CF6;    --secondary: #F59E0B;
  --gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
[C] 따뜻한 느낌:
  --primary: #EC4899;    --secondary: #06B6D4;
  --gradient: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);

/* Glassmorphism (글래스모피즘 — 카드/모달에 적용) */
--glass-bg: rgba(255, 255, 255, 0.15);
--glass-blur: blur(12px);
--glass-border: 1px solid rgba(255, 255, 255, 0.2);

/* Common Colors */
--background: #F9FAFB;   --surface: #FFFFFF;
--text: #111827;         --text-sub: #6B7280;
--danger: #EF4444;       --success: #22C55E;

/* Dark Mode: invert (background ↔ text) + glassmorphism with dark tint */

/* Typography (성찰 N5 — Pretendard 서브셋 복원, ~50KB) */
--font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
/* Pretendard 서브셋(자주 쓰는 한글 2350자 + 영문 + 숫자, ~50KB)을 프로젝트에 포함 */
--font-size-base: 16px;  --font-size-xl: 24px;  --font-size-3xl: 48px;

/* Spacing & Layout */
--radius: 16px;  --max-width: 480px;  /* radius 12→16 (더 둥글게, 2026 트렌드) */

/* Animation (REQUIRED — 성찰 N6 강화) */
--transition-fast: 150ms ease-out;    /* button tap */
--transition-normal: 250ms ease-out;  /* card transition */
--transition-slow: 400ms ease-out;    /* page transition */

/* Micro-interactions (성찰 N6 — D7 필수 패턴) */
/* 버튼 탭: scale(0.95) + 150ms — 누르는 느낌 */
/* 카드 터치: translateY(-2px) + box-shadow 강화 */
/* 페이지 전환: slide-in-right 또는 fade-up */
/* 리스트 아이템: stagger fade-in (순차 등장) */

/* Score/Quiz Effects (성찰 N6 — D9 빔 화면 이펙트) */
/* 점수 변경: 300ms 카운트업 + 팀 색상 펄스 */
/* 정답: 초록 플래시 + 체크 아이콘 + 효과음 */
/* 오답: 빨간 흔들림 + X 아이콘 */
/* 1등 역전: 화면 전체 컨페티(색종이) 폭발 + 환호 효과음 */
/* 최종 순위 발표: 3→2→1 순차 공개 + 드럼롤 효과음 */

/* Skeleton UI (성찰 N6 — D8 로딩 패턴) */
/* 데이터 로딩 시: 회색 박스 shimmer 애니메이션 (placeholder) */
/* 이미지 로딩 시: blur-up 기법 (저해상도 → 고해상도) */
```

**PWA 완전 구현 지침** (성찰 N3):
```
모든 앱에 PWA를 완전히 구현하여 "앱처럼" 느끼게 한다.

필수 파일:
  manifest.json:
    "display": "standalone"    ← URL 바 숨김 (핵심!)
    "theme_color": (선택 팔레트의 primary)
    "background_color": "#F9FAFB"
    "icons": [192x192, 512x512 PNG]
    "start_url": "/"
    "name": "{수련회 이름} 앱"
    "short_name": "{수련회 이름}"

  service-worker.js:
    정적 캐시: HTML, CSS, JS, 폰트, 아이콘
    네트워크 우선: API 요청, WebSocket fallback

"홈 화면 추가" 유도:
  첫 접속 시 3초간 상단 배너 표시:
    "홈 화면에 추가하면 앱처럼 쓸 수 있어요!"
    [추가하기] 버튼 → beforeinstallprompt 이벤트 활용
  → 홈 화면에 추가하면 URL 바 없이 전체 화면으로 실행
  → 앱 아이콘이 학생 폰 홈 화면에 표시
```

---

## Implementation Phase

> Phase 3 (코드 생성) + Phase 4 (품질 검증) + Phase 5 (미리보기 & 수정) + Phase 6 (배포)
> 실제 앱 코드를 생성하고, 검증하고, 사역자 피드백을 반영하고, 배포하는 단계.

### Step 7. Code Generation — Phase 3

- **Agent**: Claude Code (Role 2: Code Generator)
- **Verification**:
  - [ ] All HTML files render without errors
  - [ ] All CSS follows design system variables (no hardcoded colors)
  - [ ] All JavaScript passes basic syntax check
  - [ ] Korean text renders correctly (no broken characters)
  - [ ] All content from app-state.json is inserted into the app
  - [ ] Server code starts without errors (if realtime app)
  - [ ] Git checkpoint created for each major sub-step
  - [ ] Bundle size ≤ 300KB target / ≤ 500KB hard limit (gzip, 시스템 폰트 전용)
- **Task**: Generate complete app code following the architecture plan. Follow the generation order: structure → content → style → functionality → PWA. Create Git checkpoints at each major stage. Show progress to 사역자 in Korean.
- **Output**: Complete app code in project folder + Git checkpoints
- **Review**: none
- **Translation**: none (code generation)
- **Post-processing**: Verify all files exist and are non-empty (L0 Anti-Skip — minimum 100 bytes per file)

**Code Generation Order**:
```
[1] Project skeleton — folder structure + main HTML + base CSS + empty JS
    → Git checkpoint: "[초기화] 프로젝트 생성 완료"
    → 사역자 메시지: "지금 앱의 뼈대를 만들고 있어요 (1/5 단계)"

[2] Content insertion — quiz questions, schedule, bible verses, etc.
    → Git checkpoint: "[콘텐츠] {content type} 삽입"
    → 사역자 메시지: "내용을 넣고 있어요 (2/5 단계)"

[3] Styling & Design — colors, fonts, layout, animation, dark mode
    → Git checkpoint: "[디자인] 메인 색상 적용"
    → 사역자 메시지: "디자인을 입히고 있어요 (3/5 단계)"

[4] Functionality — realtime sync, admin console, PWA, offline cache
    → Git checkpoint: "[기능] {feature name} 구현"
    → 사역자 메시지: "기능을 추가하고 있어요 (4/5 단계)"

[5] Polish — data export, error handling, reconnection logic
    → Git checkpoint: "[마무리] 기능 완성"
    → 사역자 메시지: "마무리 점검 중이에요 (5/5 단계)"
```

**Realtime Data Architecture (for apps with WebSocket)**:
```
Broadcast direction: ONE-WAY ONLY

  진행자/관리자 → 서버 → 전체 학생  (1:N broadcast)
  학생 개인     → 서버              (1:1 individual, NO broadcast)

Example (quiz buzzer):
  Student presses buzzer → Server only (not broadcast to others)
  Host reveals answer    → Server → Broadcast to ALL students
```

**Server Code Requirements**:
```javascript
// Required patterns in generated server code:

// 1. WebSocket with HTTP polling fallback
// Primary: native WebSocket (ws library)
// Fallback: HTTP polling at 5-second intervals (auto-switch on WS failure)

// 2. Data persistence (성찰 M1: lowdb 동시 쓰기 race condition 방지)
// ALL state managed in-memory (JS object) — NOT lowdb direct file access
// JSON file is a periodic SNAPSHOT, not a realtime DB
// Write strategy: debounced write every 5 seconds (coalesce concurrent changes)
// On server restart: restore from JSON snapshot file
// NEVER use lowdb for concurrent write scenarios (quiz buzzer etc.)
// Pattern:
//   const state = { teams: {}, scores: {} };  // in-memory
//   setInterval(() => fs.writeFileSync('data.json', JSON.stringify(state)), 5000);

// 3. Admin authentication
// Simple password protection for /admin route
// Password set by 사역자 during conversation

// 4. Korean path safety
// Use path.join() for all file paths
// Project folder in English-only path
```

**Content Safety Rules**:
```
ALWAYS ALLOWED: Bible verses, worship content, educational game elements
ALWAYS BLOCKED: Violence, sexual content, religious discrimination, profanity, gambling

Quiz Generation Policy:
  - Questions must be based on Bible content
  - Answers verifiable from Scripture
  - Avoid theologically controversial topics
```

---

### Step 8. Quality Verification — Phase 4

- **Agent**: Claude Code (Role 3: Quality Checker)
- **Verification**:
  - [ ] All 11 technical quality gates (Q1~Q11) pass
  - [ ] All 9 design quality gates (D1~D9) pass
  - [ ] App-type-specific verification gates pass
  - [ ] Auto-fix attempted for any failures (max 3 retries)
  - [ ] If 3 retries fail: rolled back to last checkpoint + 사역자 notified
  - [ ] Git checkpoint: "[검증] 품질 검증 통과"
- **Task**: Run `verify-app.js` unified verification script (성찰 N8). All Q1~Q11 + D1~D9 + app-type-specific gates are executed in a single script call (1턴으로 완료, 컨텍스트 절감). For failures, attempt auto-fix and re-verify. Q10 is deferred to Step 9.
- **Output**: Quality report in `app-state.json` + verification log
- **Review**: none (이 단계 자체가 L1 Verification 역할)
- **Translation**: none

**통합 검증 스크립트** (성찰 N8):
```
Phase 3(코드 생성) 완료 시, Claude Code가 verify-app.js를 프로젝트 폴더에 생성한다.
이 스크립트가 Q1~Q11 + D1~D9를 한 번에 실행하고 JSON 결과를 반환한다.

실행: node verify-app.js
출력: { "Q1": "PASS", "Q2": "PASS", ..., "D9": "FAIL:reason", "overall": "FAIL" }

Claude Code는 이 결과를 1턴으로 받아서 FAIL 항목만 자동 수정한다.
→ 기존 방식(Q1~Q11을 개별 실행, 10+ 턴) 대비 컨텍스트 소모 90% 절감.
```

**Technical Quality Gates (Q1~Q11)**:

| # | Gate | Pass Criteria | Verification Method | On Failure |
|---|------|--------------|--------------------|-----------| 
| Q1 | Server running | HTTP 200 from localhost:PORT | `curl` or `fetch` | Port change + retry |
| Q2 | HTML validity | No render-blocking errors | HTML syntax check | Auto-fix + recheck |
| Q3 | External deps | 0 external scripts (except CDN font) | Search `<script src="http` | Inline or remove |
| Q4 | Bundle size | ≤ 300KB target / ≤ 500KB hard limit (gzip) | Measure build output | 이미지 압축 → 코드 분할 → 기능 축소 |
| Q5 | Korean rendering | No broken text in titles/buttons/menus | Check Korean text list | Add font fallback |
| Q6 | Touch targets | All buttons/links ≥ 44×44px | CSS property inspection | Auto-add min-height/width/padding |
| Q7 | QR code | QR decodes to correct URL | QR decode → URL compare | Regenerate QR |
| Q8 | Admin protection | /admin requires password | Attempt unauthenticated access | Add auth middleware |
| Q9 | XSS prevention | `<script>` in user input neutralized | Test input injection | Add escape function |
| Q10 | Visual check | 사역자 sees app in browser and approves | 사역자 feedback | Deferred to Step 9 |
| **Q11** | **Response latency** | **WebSocket 메시지 왕복 ≤ 100ms (localhost)** | **타임스탬프 기반 왕복 측정** | **이벤트 핸들러 최적화 + 불필요한 broadcast 제거** |

**Design Quality Gates (D1~D9)** (성찰 N6 — 3개 게이트 추가):

| # | Gate | Pass Criteria | Verification Method |
|---|------|--------------|--------------------| 
| D1 | Card UI | border-radius ≥ 12px + box-shadow + glassmorphism(선택) | CSS property search |
| D2 | Animation | ≥ 2 transition with duration ≥ 150ms + page transition 존재 | CSS pattern search |
| D3 | Dark mode | prefers-color-scheme media query exists | CSS pattern search |
| D4 | Color consistency | CSS variables + gradient 프리셋 사용, hardcoded 0개 | Code pattern search |
| D5 | Mobile native feel | fixed header (필수) + 하단 탭(종합/퀴즈만 필수) | HTML/CSS 앱 유형별 분기 |
| D6 | Font readability | font-size ≥ 16px (body), ≥ 24px (headings), Pretendard 로드 | CSS value check |
| **D7** | **Micro-interactions** | **버튼 탭 시 scale 변환 존재 + 리스트 stagger 애니메이션 존재** | **CSS/JS 패턴 검색** |
| **D8** | **Loading UX** | **Skeleton UI 또는 spinner가 데이터 로딩 시 표시됨** | **HTML 패턴 검색 (.skeleton, .loading)** |
| **D9** | **Screen impact** | **/screen 경로에 점수 변경 이펙트 + 컨페티 + 효과음 코드 존재** | **JS 패턴 검색 (confetti, AudioContext)** |

**앱 유형별 특수 검증** (성찰 N9):

| App Type | Additional Gate | Verification |
|----------|----------------|-------------|
| 성경 퀴즈 | 35명 동시 버저 시뮬레이션 | 35개 WS 연결 생성 → 동시 메시지 → 누락 0건 확인 |
| 종합 앱 | WebSocket 메시지 타입 라우팅 | quiz/score/lyrics 메시지가 각각 올바른 핸들러로 라우팅 |
| 스탬프 랠리 | QR 스캔 → 미션 인증 흐름 | 모든 미션 QR이 유효한 URL로 디코딩 |
| 찬양 가사 | 빔+폰 동시 표시 | /screen과 / 경로에서 동일 가사 동기화 확인 |
| 팀 점수판 | /admin → /screen 점수 반영 | admin에서 점수 변경 → screen 1초 이내 반영 |

**Quality Gate Flow**:
```
verify-app.js 실행 (1턴) → 전체 결과 JSON 반환
  → ALL PASS → Proceed to Step 9 (사역자 preview)
  → FAIL 존재 → FAIL 항목만 자동 수정 → verify-app.js 재실행 (max 3회)
                → Still failing? → Git rollback → Report to 사역자 in Korean
```

---

### Step 9. (human) Preview & Feedback Loop — Phase 5

- **Action**: 사역자가 완성된 앱을 브라우저에서 직접 확인하고, 수정을 요청하거나 승인한다.
- **Autopilot Default**: auto-approve after 3 modification cycles — Autopilot 모드에서는 3회 수정 사이클 후 자동으로 완성 처리. 수정 없이 첫 미리보기가 품질 게이트를 통과하면 즉시 승인.
- **Verification**:
  - [ ] Browser auto-opened with app preview
  - [ ] QR code displayed for mobile preview
  - [ ] 사역자 has seen the app on both PC and mobile (if possible)
  - [ ] All modification requests have been addressed
  - [ ] 사역자 explicitly signaled completion ("완성", "좋아요", "이대로 해주세요")
- **Task**: Auto-open browser with app. Display QR for mobile testing. Wait for 사역자 feedback. Process modification requests using the modification loop rules. Repeat until 사역자 is satisfied.

**Modification Loop Rules**:
```
사역자 수정 요청 → Claude Code가 수정 유형 판단:

  [A] Style/text change → Phase 3 (code fix) → Return to Phase 5 (QA skip)
      Example: "배경색 파란색으로 바꿔줘" → CSS variable 1줄 변경

  [B] Feature add/change → Phase 3 (code fix) → Phase 4 (QA required) → Return to Phase 5
      Example: "타이머 추가해줘" → JS module 추가 + HTML 수정

  [C] Rollback → Git checkpoint restore → **Post-Rollback SOT Sync** → Return to Phase 5 (QA skip)
      Example: "아까 것이 더 좋았어요" → git checkout [commit] -- .
      ⚠ [C4 수정] 롤백 직후 반드시 app-state.json을 현재 Phase에 맞게 즉시 갱신:
        → status.quality_passed = true (Phase 5에 있으므로 QA는 이미 통과 상태)
        → status.code_generated = true
        → quality 섹션은 마지막 통과 결과 유지
        → history.modifications에 롤백 기록 추가
```

**Visual Choice Presentation**:
```
색상 변경 시: 3가지 후보를 나란히 보여주고 선택 유도
"아까 것이 더 좋았어요" → Git 롤백 즉시 실행
3번 이상 같은 항목 수정 → "혹시 이런 느낌이세요?" + 구체적 예시
```

**Pre-test Mode (사전 테스트)**:
```
사역자: "학생 몇 명이랑 먼저 테스트해보고 싶어요"

Claude Code:
  1. 현재 LAN 서버 실행 상태 확인
  2. QR코드 제시: "이 QR코드를 테스트할 학생들에게 보여주세요"
  3. 접속 현황 실시간 표시: "지금 3명이 접속했어요"
  4. 테스트 후 피드백 수집
  5. 수정 → 재테스트 반복
```

---

### Step 10. Deployment — Phase 6

- **Agent**: Claude Code (Role 4: Deployment Manager)
- **Verification**:
  - [ ] LAN server running in background (or static files ready)
  - [ ] QR code PNG generated with correct URL
  - [ ] Print-ready HTML page generated (A4, church name + QR + instructions)
  - [ ] "앱 실행.bat" created on desktop with Korean messages
  - [ ] WiFi connection instructions page generated
  - [ ] Browser auto-opened with QR page
  - [ ] `app-state.json` updated with deployment info
  - [ ] Git checkpoint: "[배포] 최종 빌드 완료"
  - [ ] (If GitHub Pages) Repository created and Pages activated
- **Task**: Deploy the app based on type (LAN server or GitHub Pages). Generate QR code. Create print-ready page. Create "앱 실행.bat" on desktop. Generate WiFi instructions for students. Auto-open browser.
- **Output**: Running server + QR code + print page + .bat file + deployment info in `app-state.json`
- **Review**: none
- **Translation**: none

**Server Background Execution**:
```
Claude Code uses Bash tool's run_in_background option to start Node.js server.

After launch:
  - Claude Code continues conversation with 사역자
  - Server runs as separate process
  - Modification requests → server auto-restart by Claude Code
```

**Server Process Management**:
```
No PID files (stale risk).
On restart: netstat to find port-occupying process → taskkill → new server start.
On Claude Code session end: server process continues independently.
```

**"앱 실행.bat" Specification** (성찰 C2 + M2 반영):
```batch
@echo off
title 수련회 앱 서버
color 0A
cd /d "{project_folder_path}"
set count=0

REM [M2 수정] 재시작 카운터로 무한 루프 방지
REM [C2 수정] IP 변경 감지 + QR 자동 재생성

echo =========================================
echo   수련회 앱이 실행 중이에요!
echo   이 창을 닫지 마세요.
echo   창을 닫으면 앱이 꺼져요.
echo   앱을 끄려면 이 창을 닫으세요.
echo =========================================
echo.

REM 자가 진단: Node.js 존재 확인
where node >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo Node.js가 설치되어 있지 않아요.
    echo Claude Code를 열어서 "앱 고쳐줘"라고 말씀해 주세요.
    pause
    exit /b 1
)

REM 자가 진단: 프로젝트 폴더 확인
if not exist "server.js" (
    if not exist "index.html" (
        color 0C
        echo 앱 파일을 찾을 수 없어요.
        echo Claude Code를 열어서 "앱 고쳐줘"라고 말씀해 주세요.
        pause
        exit /b 1
    )
)

REM [N10 수정] node_modules 존재 확인 + 자동 복구
if not exist "node_modules" (
    echo 필요한 파일을 다시 준비하고 있어요. 잠시만 기다려 주세요...
    npm install --production 2>nul
    if %errorlevel% neq 0 (
        color 0C
        echo 인터넷 연결을 확인해 주세요.
        echo 또는 Claude Code를 열어서 "앱 고쳐줘"라고 말씀해 주세요.
        pause
        exit /b 1
    )
    echo 준비 완료!
    echo.
)

:start
set /a count+=1
if %count% gtr 3 (
    color 0C
    echo.
    echo =========================================
    echo   앱을 다시 시작하지 못했어요.
    echo   Claude Code를 열어서
    echo   "앱 고쳐줘"라고 말씀해 주세요.
    echo =========================================
    pause
    exit /b 1
)

REM [N10 수정] IP 감지 + QR 재생성 (별도 스크립트 호출)
if exist "regenerate-qr.js" (
    node regenerate-qr.js
    echo   새 QR코드가 준비되었어요.
) else (
    node -e "const os=require('os'),ni=os.networkInterfaces();let ip='';for(const k of Object.keys(ni)){for(const i of ni[k]){if(i.family==='IPv4'&&!i.internal){ip=i.address;break;}}if(ip)break;}const fs=require('fs');const port=fs.existsSync('port.txt')?fs.readFileSync('port.txt','utf8').trim():'3000';fs.writeFileSync('current-url.txt','http://'+ip+':'+port);console.log('  접속 주소: http://'+ip+':'+port);" 2>nul
)
REM regenerate-qr.js는 Phase 6에서 Claude Code가 자동 생성한다.
REM IP 감지 + QR PNG 재생성 + current-url.txt 갱신 + 브라우저 자동 열기를 수행한다.

echo.
echo   앱을 시작하고 있어요... (시도 %count%/3)
color 0A
node server.js
if %errorlevel% neq 0 (
    color 0E
    echo.
    echo   앱에 문제가 생겼어요. 자동으로 다시 시작하고 있어요...
    timeout /t 5 /nobreak > nul
    goto start
)
```

**[C2 수정] 수련회 당일 비상 대응 카드 (A4 자동 생성)**:
> Phase 6 완료 시, QR 인쇄물과 함께 "비상 대응 카드" HTML을 자동 생성한다.

```
비상 대응 카드 (인쇄용 A4)
━━━━━━━━━━━━━━━━━━━━━━━━━
앱이 안 될 때 이렇게 하세요:

1. 바탕화면의 "수련회 앱 실행"을 더블클릭하세요.
2. 검은 창이 나오면 기다리세요 (정상이에요).
3. 빨간 글씨가 나오면 → Claude Code를 열어서
   "앱 고쳐줘"라고 말하세요.

학생들이 접속이 안 될 때:
→ 학생 폰의 와이파이를 확인하세요.
→ 안 되면: 설정 > 모바일 핫스팟을 켜고,
   학생들에게 핫스팟에 연결하라고 하세요.
   새 QR코드가 자동으로 만들어져요.

진행자 비밀번호: {password}
━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Deployment Complete Message**:
```
"앱이 완성됐어요!
 학생들에게 이 QR코드를 보여주세요.
 [QR 이미지]

 바탕화면에 '수련회 앱 실행' 아이콘을 만들었어요.
 수련회 때 이 아이콘을 더블클릭하면 앱이 바로 켜져요.

 내용을 바꾸고 싶으시면 언제든 말씀해 주세요!"
```

**QR Code Delivery Methods (3가지)**:

| Method | When | Claude Code Message |
|--------|------|---------------------|
| Print | Printer available | "브라우저에서 인쇄 버튼(Ctrl+P)을 누르세요" |
| Projector | Beam available | "이 화면을 빔프로젝터에 띄워주세요" |
| KakaoTalk | Neither available | "QR코드 이미지를 저장해서 카카오톡 단체방에 보내주세요" |

---

### Step 11. (Optional) Data Export & App Archive — Post-Deployment

- **Verification**:
  - [ ] Export files created in results/ folder for requested data
  - [ ] Archive copy created in archives/ folder
  - [ ] Original archive is read-only (never modified)
- **Task**: When 사역자 requests ("결과 저장해줘", "수련회 끝났어요"), export app data to text files and create archive copy for future reuse.
- **Output**: `results/` folder with exported data + `archives/` folder with app copy
- **Translation**: none

**Export Data by App Type**:

| App Type | Export Data | Format |
|----------|-----------|--------|
| 성경 퀴즈 | Team scores, answer rates, final ranking | .txt |
| 스탬프 랠리 | Stamp status by team, completion list | .txt |
| QT 가이드 | Student reflection notes (by nickname) | .txt |
| 팀 점수판 | Cumulative scores, final ranking | .txt |
| 기도제목 | All prayer requests | .txt |
| 종합 앱 | Combined export | .txt |

**Archive for Reuse**:
```
archives/
  2026-여름수련회-성경퀴즈/
    (complete project copy)

Reuse pattern:
  사역자: "작년에 만든 퀴즈 앱을 올해도 쓰고 싶어요"
  Claude: archives/ 탐색 → 복사본 생성 → 수정할 부분만 확인
  원본 아카이브는 절대 수정하지 않음.
```

**[m2 수정] "다음 수련회 준비 가이드" 자동 생성**:
> Phase 6 완료 시 프로젝트 폴더에 `다음 수련회 준비.txt` 파일을 자동 생성한다.

```
다음 수련회 때 앱을 다시 만들고 싶으시면:

1. Claude Code를 실행하세요.
2. "작년 앱 다시 쓰고 싶어요"라고 말하세요.
3. 문제만 바꾸거나, 새로 만들 수 있어요.

앱을 수정하고 싶으시면:
1. Claude Code를 실행하세요.
2. "앱 수정하고 싶어요"라고 말하세요.

문제가 생기면:
1. Claude Code를 실행하세요.
2. "앱 고쳐줘"라고 말하세요.
```

---

## Network Strategy

> 모든 네트워크 접속은 로컬 범위 내에서만 이루어진다.

```
[1순위] 같은 WiFi LAN 접속 (기본)
  학생들이 수련회장 WiFi에 연결 → 192.168.x.x:PORT 접속
  → 가장 단순하고 안정적

[2순위] 모바일 핫스팟 (WiFi 문제 시)
  사역자 PC 모바일 핫스팟 ON → 학생들이 핫스팟에 연결
  → 최대 약 8대 동시 접속 (팀별 분할)
  → 핫스팟 IP(192.168.137.x) 자동 감지 → QR 재생성

[WiFi/핫스팟 둘 다 불가 시]
  → 실시간 기능은 사용 불가. 솔직히 안내.
  → 정적 앱은 GitHub Pages(사역자 동의 시)로 대체 가능
  → "학생들이 와이파이에 연결해야 앱을 쓸 수 있어요."
```

**WiFi Instructions Auto-Generation**:
> Claude Code automatically generates a printable A4 instruction page:
```
"앱을 쓰려면 와이파이에 연결해야 해요.
 설정 → 와이파이 → [수련회장 WiFi 이름] 선택
 (데이터로는 접속이 안 돼요!)"
```

**Environment Auto-Detection**:

| Item | Method |
|------|--------|
| WiFi IP | `os.networkInterfaces()` → 192.168.137.x (hotspot) priority, else first IPv4 |
| Port | 3000→3009→8080→49152~49162 sequential try |
| Disk | Warn if < 500MB |
| Korean path | `process.cwd()` detection → desktop or documents folder priority |
| Firewall | Port access test → full block → hotspot switch guide |

---

## Error Handling

### Error Recovery Tree

```
에러 발생
|-- [자동 복구 가능]
|     |-- 포트 충돌 → 3000~3009 → 8080 → 49152~49162 순차 탐색
|     |-- npm 설치 실패 → 캐시 삭제 후 재시도
|     |-- 번들 초과 → 이미지 압축 → 코드 분할 → 기능 축소
|     |-- QR 생성 실패 → 라이브러리 교체 후 재시도
|     |-- WebSocket 실패 → HTTP 폴링(5초)으로 자동 전환
|     |-- Git 커밋 실패 → 한글 경로 우회 후 재시도
|     |-- 빌드 에러 → Claude Code가 코드 자동 수정
|     |-- LAN 접속 불가 → 핫스팟 전환 안내
|     |-- C드라이브 권한 없음 → 바탕화면/문서 폴더로 이동
|     \-- (최대 3회 재시도, 모두 사역자 모르게 처리)
|
\-- [사역자 조치 필요] → 한국어 한 문장 + 행동 지침
      |-- 방화벽 차단 → "'허용' 버튼을 눌러주세요"
      |-- 디스크 부족 → "불필요한 파일을 삭제해 주세요"
      |-- WiFi 끊김 → "와이파이 연결을 확인해 주세요"
      |-- GitHub 인증 → "브라우저에서 로그인을 완료해 주세요"
      |-- 백신 차단 → "프로그램을 허용해 주세요" (기술 도우미 필요)
      \-- 복구 불가 → 마지막 체크포인트 롤백 + 대안 제시
```

### Error Message Translation

| Actual Error | 사역자에게 보이는 말 |
|-------------|---------------------|
| Build failed | "잠깐 손보는 중이에요. 1분만 기다려 주세요!" |
| Git conflict | "저장하다가 살짝 엉켰는데, 제가 정리했어요." |
| Deploy timeout | "인터넷이 잠깐 느렸어요. 다시 올리고 있어요." |
| Out of scope | "그건 어렵지만, 비슷하게 이렇게는 가능해요: ..." |
| LAN unreachable | "같은 와이파이에 연결되어 있는지 확인해 주세요." |
| Context overflow | "대화가 길어져서 앞부분이 잘 기억이 안 나요. 다시 한번 알려주시겠어요?" |
| API rate limit | "잠시 쉬었다가 할게요. 1~2분만 기다려 주세요." |

### Alternative Suggestion Patterns

| Failure | Bad Response | Good Response |
|---------|-------------|---------------|
| Realtime quiz fails | "기능을 줄여볼까요?" | "실시간 버저 대신, 학생들이 손을 들고 사역자님이 직접 점수를 입력하는 방식으로 바꿔드릴까요? 점수판은 그대로 작동해요." |
| WebSocket total failure | "연결이 안 돼요" | "실시간 연결이 안 되지만, 5초마다 자동으로 새로고침하는 방식으로 바꿨어요. 살짝 느리지만 똑같이 동작해요." |
| Stamp rally QR fails | "QR이 안 돼요" | "QR 대신 학생들이 미션 장소에서 비밀번호를 입력하는 방식으로 바꿔드릴까요? 비밀번호는 각 장소에 종이로 붙여두시면 돼요." |

### Completely Unrecoverable Scenarios

```
→ 백신이 Node.js 완전 차단: 기술 도우미 필요
→ npm 레지스트리 방화벽 차단: 기술 도우미 필요
→ 클라이언트 격리 + 전 포트 차단: 핫스팟 전환, 불가 시 정적 앱(GitHub Pages)
```

---

## Git Checkpoint & Rollback Strategy

**Commit Format**: `[단계] 설명`

**Auto-commit Points**:
```
[초기화] 프로젝트 생성 완료
[콘텐츠] 퀴즈 문제 50개 삽입
[디자인] 메인 색상 적용
[기능] 실시간 점수판 구현
[검증] 품질 검증 통과
[수정] 배경색 파란색 변경     ← 사역자 수정 요청
[롤백] 이전 디자인으로 복원   ← 롤백
[배포] 최종 빌드 완료
```

**Rollback Mechanism**:
```
"아까 것이 더 좋았어요"    → 직전 체크포인트 복원
"처음 것으로 돌아가주세요"  → 가장 이른 의미 있는 체크포인트 복원

Method: git checkout [commit] -- . → 새 커밋으로 기록 → 브라우저 새로고침
Git 히스토리는 사역자에게 절대 노출하지 않음.
```

---

## Session Interruption & Resume

```
Claude Code 재실행 시:

[0] 프로젝트 경로 탐색 (성찰 M5)
    → %USERPROFILE%\.last-church-app-path 파일 확인
    → 이 파일에 마지막 프로젝트 경로가 기록되어 있음
    → Phase 6 완료 시 자동 생성됨
    → 파일이 없으면: 바탕화면 > 문서 폴더 > C:\ 순서로 church-app 폴더 탐색

[1] 프로젝트 폴더 존재 확인
    → 존재: "이전에 만들던 앱이 있어요. 이어서 할까요?"
    → 없음: 새 프로젝트 시작

[2] app-state.json에서 마지막 상태 파악
    → research_complete: true → Phase 1 완료, Phase 2부터 재개
    → planning_complete: true → Phase 2 완료, Phase 3부터 재개
    → quality_passed: true → Phase 4 완료, Phase 5부터 재개
    → deployed: true → 배포 완료, 수정/내보내기 모드

[3] Git 히스토리에서 마지막 커밋 메시지 확인 (보조)
    → 중단된 단계 식별

[4] 해당 단계부터 재개
[5] 서버 재시작 + QR코드 재생성 (IP 변경 대비)
```

**Context Window Overflow Mitigation**:
```
[1] 핵심 결정만 app-state.json에 기록
    → 컨텍스트 압축 시에도 파일을 다시 읽으면 복원 가능

[2] 대량 콘텐츠는 대화가 아닌 파일로 입력
    → "메모장에 적어서 저장해주세요" 안내 → 파일로 읽기
    → 대화 컨텍스트에는 "퀴즈 50문제 파일에서 로드 완료"만 남김

[3] AgenticWorkflow의 Context Preservation System 활용
    → 세션 압축/중단 시 자동 스냅샷 저장 → 재개 시 복원
```

---

## SOT Schema (app-state.json)

```json
{
  "workflow": {
    "name": "church-retreat-app",
    "version": "1.0",
    "created_at": "",
    "parent_genome": {
      "source": "AgenticWorkflow",
      "version": "2026-04-09",
      "inherited_dna": [
        "absolute-criteria",
        "sot-pattern",
        "3-phase-structure",
        "4-layer-qa",
        "safety-hooks",
        "context-preservation"
      ]
    }
  },
  "intent": {
    "app_type": "",
    "app_types_combined": [],
    "team_count": 0,
    "team_names": [],
    "team_colors": [],
    "design_palette": "A",
    "features": [],
    "admin_password": ""
  },
  "content": {
    "quiz_questions": [],
    "schedule": [],
    "lyrics": [],
    "missions": [],
    "bible_passages": [],
    "custom_data": {}
  },
  "architecture": {
    "deployment_type": "",
    "tech_stack": "",
    "url_routes": [],
    "data_sync": "",
    "has_admin": false,
    "has_screen": false,
    "has_pwa": true
  },
  "status": {
    "current_phase": 0,
    "research_complete": false,
    "planning_complete": false,
    "code_generated": false,
    "quality_passed": false,
    "deployed": false,
    "project_folder": "",
    "modification_count": 0,
    "in_preview_loop": false,
    "pending_action": null,
    "server_port": null,
    "server_url": "",
    "qr_path": "",
    "bat_path": "",
    "github_pages_url": null
  },
  "quality": {
    "q_gates": {},
    "d_gates": {},
    "last_verified": "",
    "retry_count": 0
  },
  "history": {
    "modifications": [],
    "exports": [],
    "archive_path": null
  }
}
```

---

## Field Operations Guide (현장 운영)

### Pre-Event Checklist
```
0. 와이파이 수용 인원 확인
   → 공유기 최대 동시 접속 수 (일반: 20~30대)
   → 학생 35명 이상: 공유기 2대 또는 팀별 시간차 접속
   → 핫스팟 폴백: 최대 약 8대 동시 접속
1. 노트북을 전원에 연결 (배터리 모드 금지 — 절전 방지)
2. 수련회 장소 와이파이에 연결
3. "수련회 앱 실행.bat" 더블클릭 (또는 Claude Code에서 "앱 실행해줘")
4. QR코드를 인쇄하거나 빔프로젝터에 표시
5. 학생들이 QR 스캔 → 접속
```

### Server = 사역자 PC

| Situation | Impact | Response |
|-----------|--------|----------|
| Laptop sleep | Server stops | Windows power → "Never sleep" (Claude auto-guides) |
| Laptop lid closed | Sleep → stop | "노트북을 펼쳐둔 채로 유지해 주세요" |
| WiFi disconnect | Students can't connect | Hotspot switch guide |
| Power outage | Everything stops | Data saved in JSON; restart server after power |
| Server crash | Error on student screens | Auto-restart in .bat (30-sec recovery target) |

### Student Auto-Reconnect
```
Server stops → Student screen: "연결 대기 중..." 
Server restarts → Auto-reconnect (WebSocket reconnect or polling resume)
Target: Full reconnection within 30 seconds of server restart
```

---

## Windows-Specific Handling

| Situation | Problem | Auto-handling |
|-----------|---------|--------------|
| Firewall popup | "Allow network access?" | Korean guide: "'허용' 버튼을 눌러주세요" |
| Port conflict | EADDRINUSE | Auto-try next port (3000→3009→8080→49152+) |
| Local IP detection | Need WiFi IP for QR | `os.networkInterfaces()` auto-detect |
| Browser auto-open | Preview launch | `start http://localhost:PORT` |
| Sleep prevention | Server dies on sleep | Phase 6 배포 시 자동: `powercfg /change standby-timeout-ac 0` 실행. 앱 종료 시 원래 값 복원. 실패 시: "노트북 설정에서 '절전: 사용 안 함'으로 바꿔주세요" |
| Path separator | Windows \ vs / | `path.join()` in all generated code |
| Korean path | `C:\Users\김전도사\` | Create project in English-only path |
| Hotspot IP | Different subnet (192.168.137.x) | Auto-detect hotspot adapter → regenerate QR |

---

## GitHub Pages Automation (Optional)

> Only when 사역자 explicitly agrees. Not required for LAN deployment.

**First-time Setup (1회, Phase 0에서 수행)**:
```
[1] Git installed? → If not: "프로그램 하나를 설치해야 해요."
[2] GitHub CLI: winget install --id GitHub.cli (auto)
[3] gh auth login → "브라우저에서 로그인해 주세요"
[4] "GitHub 준비가 끝났어요!"
```

**Deployment (매번 자동)**:
```
[1] gh repo create church-camp-app --public --source=. --push
[2] gh api repos/{owner}/{repo}/pages -X POST ...
[3] Wait for deployment (30s~2min)
[4] Generate QR from https://{username}.github.io/{repo}/
[5] "앱이 완성됐어요! 이 주소로 접속하면 돼요: [URL]"
```

**GitHub Pages 에러 대응** (성찰 발견4):

| 에러 | 대응 |
|------|------|
| `gh auth` 실패 | "브라우저에서 로그인을 완료해 주세요" 재안내 |
| `gh repo create` 실패 (이름 중복) | 이름 뒤에 날짜 추가 (예: `camp-app-2026`) 후 재시도 |
| Pages 활성화 실패 | "GitHub 사이트에서 Settings → Pages를 열어주세요" 수동 안내 |
| 빌드 실패 | 정적 파일 재확인 + 이미지 최적화 후 재배포 |
| 배포 대기 2분 초과 | `gh api` 상태 재확인, 실패 시 LAN 전용 폴백 + "인터넷에 올리는 건 나중에 다시 할게요" |

---

## Scope Definition

### In Scope (v1.0)

```
✅ Claude Code 대화로 앱 직접 생성
✅ 9가지 수련회 앱 유형
✅ 실시간 기능 (native WebSocket + HTTP 폴링 폴백)
✅ QR 코드 + 인쇄용 HTML
✅ PWA (설치 불필요, 오프라인 캐싱)
✅ GitHub Pages 배포 (정적 앱, 선택)
✅ LAN 배포 (실시간 앱, 같은 와이파이)
✅ Git 체크포인트 + 롤백
✅ 중학생 개인정보 최소 수집
✅ 사역자 PC 로컬 실행
✅ 현장 운영 가이드 + 장애 대응
✅ 데이터 내보내기 + 앱 아카이브
✅ "앱 실행.bat" 바탕화면 자동 생성
```

### Out of Scope

```
❌ 별도 "앱 빌더" 시스템 사전 구축
❌ 네이티브 앱 / 다국어 / 결제 / 계정
❌ 학생 대상 AI 챗봇 / 영상 스트리밍
❌ SaaS 배포 / 클라우드 호스팅
❌ 별도 CLI 도구
❌ Ollama 로컬 LLM 폴백
❌ 학생→서버 사진 업로드
❌ 50명 자동 부하 테스트
❌ 터널링 (ngrok 등)
```

---

## Risk Assumptions

| # | Assumption | Risk | Mitigation |
|---|-----------|------|-----------|
| 1 | 사역자가 Claude Code 설치 완료 가능 | 기술 장벽으로 포기 | 기술 도우미 매칭, 상세 안내 |
| 2 | 한국어 대화로 요구사항 구체화 가능 | 의도 오해 | 시각적 예시 + 선택지 제시 |
| 3 | GitHub Pages 자동화 가능 | Git 설정 복잡 | LAN 전용 폴백 |
| 4 | 중학생이 "진짜 앱"으로 인식 | 디자인 부족 | D1~D6 품질 게이트 |
| 5 | 교회 와이파이에서 안정 동작 | 네트워크 불안정 | PWA + 핫스팟 폴백 |
| 6 | 사역자가 두 번째 앱도 독립 생성 | 반복 사용 실패 | 아카이브 + 재사용 패턴 |

**Verification Priority**: 1 → 2 → 3 (이 3개 통과 못하면 나머지 무의미)

---

## Bible Data Copyright Policy

| Item | Policy |
|------|--------|
| 개역개정 | 저작권 보호 텍스트 — 전체 DB 구축 시 라이선스 확인 필요 |
| 우선 전략 | 사역자가 직접 입력하는 성경 구절 사용 |
| 대안 1 | Claude Code가 성경 범위 기반으로 AI 생성 (사역자 확인 후 확정) |
| 대안 2 | 사역자가 성경 구절 직접 입력/붙여넣기 |
| 금지 | 저작권 미확인 상태에서 성경 전체 텍스트 자동 크롤링/DB화 |

---

## Cost Transparency

```
Claude Code 사용 시 API 비용이 발생합니다.
  - 앱 1개 생성: 대략 $1~5 (대화 길이와 수정 횟수에 따라 다름)
  - GitHub Pages 호스팅: 무료
  - LAN 배포: 비용 없음
  - 추가 유료 서비스 연결: 금지 (사역자 사전 동의 없이)
```

---

## Claude Code Configuration

> 이 워크플로우는 **단일 세션 역할 전환** 구조이므로, 별도의 서브에이전트 .md 파일이나 Agent Team을 사용하지 않는다.
> Claude Code 자체가 4가지 역할(대화→코드→검증→배포)을 순서대로 수행한다.

### Sub-agents

```yaml
# 이 워크플로우에서는 별도 서브에이전트를 사용하지 않는다.
# Claude Code 단일 세션이 4가지 역할을 전환하며 수행.
# 이유: 사역자와의 대화 맥락 유지가 최우선 (컨텍스트 분리 시 품질 저하)

agents: none

# 역할은 workflow.md 내부 지침으로 정의:
#   Role 1: Conversation Guide  — Phase 0, 1, 5
#   Role 2: Code Generator      — Phase 2, 3, 5(수정)
#   Role 3: Quality Checker     — Phase 4
#   Role 4: Deployment Manager  — Phase 6
```

### Agent Team

```yaml
# Agent Team 사용하지 않음.
# 이유: 단일 세션에서 역할 전환이 맥락 유지 + 품질 면에서 우월 (절대 기준 1).
# 사역자 대화 → 코드 생성 → 검증의 전체 흐름이 하나의 컨텍스트 안에서 이어져야
# 사역자 의도가 정확하게 코드에 반영된다.

teams: none
```

### SOT (상태 관리)

```yaml
sot:
  file: "app-state.json"           # 프로젝트 폴더 내 (state.yaml 대신 JSON — 생성 앱과 동일 포맷)
  writer: "Claude Code"            # 단일 쓰기 지점 (유일한 실행 주체)
  agent_access: "N/A"              # 서브에이전트 없음
  quality_override: "기본 패턴 적용"
```

### Hooks

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/scripts/block_destructive_commands.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

> **참고**: 이 워크플로우는 AgenticWorkflow 프로젝트의 기존 Hook 시스템을 상속한다.
> 추가 Hook은 불필요 — 품질 검증은 Step 8에서 Claude Code가 직접 수행.

### Slash Commands

```yaml
# 사역자가 직접 사용하는 명령은 없음 (한국어 대화 전용).
# 내부 유틸리티 명령:

commands:
  /start-app:
    description: "수련회 앱 워크플로우 시작 — Phase 1부터 실행"

  /resume-app:
    description: "중단된 앱 생성 재개 — app-state.json 기반 상태 복원"

  /deploy-app:
    description: "완성된 앱 배포 실행 — Phase 6 직접 실행"
```

### Required Skills

```yaml
# 이 워크플로우 자체가 workflow-generator 스킬에서 생성됨.
# 추가 스킬 의존성 없음.

skills: none
```

### MCP Servers

```yaml
# 외부 서비스 연동 없음 (로컬 실행 절대 원칙 AC1).

mcp_servers: none
```

### Runtime Directories

```yaml
runtime_directories:
  # 앱 프로젝트 폴더 내 생성
  results/:          # 데이터 내보내기 산출물
  archives/:         # 앱 아카이브 (재사용용)
```

### Error Handling

```yaml
error_handling:
  on_code_generation_failure:
    action: retry_with_feedback
    max_attempts: 3
    escalation: rollback_and_report  # Git 롤백 후 사역자에게 한국어 보고

  on_quality_gate_failure:
    action: auto_fix_and_recheck
    max_attempts: 3
    fallback: rollback_to_checkpoint

  on_deployment_failure:
    action: retry_with_port_change
    max_attempts: 10               # 포트 3000~3009 + 8080 + 49152~49162
    escalation: hotspot_guide      # 네트워크 문제 시 핫스팟 안내

  on_context_overflow:
    action: save_state_and_resume  # app-state.json에 저장 후 재개
```

### Autopilot Logs

```yaml
autopilot_logging:
  log_directory: "N/A"             # Git 커밋 메시지가 decision log 역할
  rationale: "단일 세션 워크플로우에서는 Git 체크포인트 메시지가 모든 결정을 추적"
```

### pACS Logs

```yaml
pacs_logging:
  log_directory: "N/A"             # app-state.json의 quality 섹션에 통합
  dimensions: [F, C, L]
  F: "콘텐츠 정확성 — 사역자가 요청한 내용이 정확히 반영되었는가"
  C: "기능 완전성 — 요청된 모든 기능이 구현되었는가"
  L: "코드 정확성 — 에러 없이 실행되고 품질 게이트를 통과하는가"
  scoring: "min-score"
  triggers:
    GREEN: "≥ 70 → 다음 Phase 자동 진행"
    YELLOW: "50-69 → 진행하되 플래그 기록"
    RED: "< 50 → 재작업 또는 사역자에게 대안 제시"
```

---

## Distill Verification Checklist

> workflow.md 생성 후 품질 극대화를 위한 자체 점검.

- [x] "이 단계가 최종 품질에 기여하는가?" — 모든 단계가 사역자 경험 또는 앱 품질에 직접 기여
- [x] "이 단계를 자동화하면 품질이 더 안정적인가?" — Phase 2~4, 6 완전 자동화
- [x] "품질을 높이기 위해 추가해야 할 단계가 있는가?" — D1~D6 디자인 검증이 추가됨
- [x] "각 Verification 기준이 파이프라인 연결을 포함하는가?" — Step 간 app-state.json으로 데이터 흐름 보장
- [x] Inherited DNA 3개 절대 기준 포함 (품질 > SOT > CCP)
- [x] CAP-1~4 코딩 기준점 맥락화 완료
- [x] 모든 Step에 Verification 필드 포함 (Task 앞에 배치)
- [x] 모든 Step에 Review 필드 포함 (none — 단일 세션 구조)
- [x] 모든 Step에 Translation 필드 포함 (none — 한국어 대화 기반)
- [x] (human) 단계에 Autopilot Default 지정
- [x] pACS 차원(F/C/L) 정의 완료
- [x] Context Injection Pattern A 지정 (전 단계)

---

## Adversarial Review Tracking (적대적 검증 추적표)

> 3명의 적대적 에이전트(사역자 관점, 기술 현실, 논리/구조)가 수행한 검증 결과.

### Critical — 4건 (모두 수정 완료)

| 코드 | 공격자 | 문제 | 수정 내용 | 상태 |
|------|--------|------|-----------|------|
| C1 | 사역자 | Phase 0에서 Claude Code가 안내 불가 (실행 전) | 3가지 독립 경로 추가: PDF 가이드 / 기술 도우미 / 독립 설치 | ✅ 완료 |
| C2 | 사역자 | 수련회 당일 서버 다운 + IP 변경 시 QR 무효화 | .bat에 IP 감지+QR 재생성 + 자가진단 로직 추가. 비상 대응 카드 A4 자동 생성 | ✅ 완료 |
| C3 | 논리 | Step 4 auto-approve → 잘못된 앱 구조 승인 | Autopilot Default를 skip으로 변경 (사역자 승인 필수) | ✅ 완료 |
| C4 | 논리 | Git 롤백 후 app-state.json 상태 불일치 | Post-Rollback SOT Sync 절차 명시적 추가 | ✅ 완료 |

### Major — 7건 (모두 수정 완료)

| 코드 | 공격자 | 문제 | 수정 내용 | 상태 |
|------|--------|------|-----------|------|
| M1 | 기술 | lowdb 35명 동시 쓰기 race condition | 메모리 관리 + 5초 debounce JSON 스냅샷 패턴으로 변경 | ✅ 완료 |
| M2 | 기술 | .bat 재시작 카운터 없음 → 무한 루프 | set /a count+=1, 3회 초과 시 종료 로직 추가 | ✅ 완료 |
| M3 | 기술 | 500KB + 웹폰트 비현실적 | 시스템 폰트 전용 확정 (웹폰트 0KB), 번들 300KB로 하향 | ✅ 완료 |
| M4 | 기술 | npm install 교회 프록시/방화벽 실패 | npm ping 사전 검증 + 미러 레지스트리 + 오프라인 설치 경로 추가 | ✅ 완료 |
| M5 | 기술 | 세션 재개 시 프로젝트 경로 탐색 불가 | .last-church-app-path 파일로 경로 기록 + 탐색 순서 명시 | ✅ 완료 |
| M6 | 논리 | SOT에 Phase 5 수정 횟수 필드 부재 | modification_count, in_preview_loop, pending_action 필드 추가 | ✅ 완료 |
| M7 | 논리 | D2, D5 검증 기준 측정 불가능 | D2: duration ≥ 150ms 조건 추가. D5: 앱 유형별 하단 탭 적용 매핑 | ✅ 완료 |

### Minor — 4건 (모두 수정 완료)

| 코드 | 공격자 | 문제 | 수정 내용 | 상태 |
|------|--------|------|-----------|------|
| m1 | 사역자 | 관리자 비밀번호 설정 부담 + 망각 | 자동 생성("1234") + 인쇄물 포함 + 변경은 대화로 | ✅ 완료 |
| m2 | 사역자 | 두 번째 앱 제작 시 가이드 부재 | "다음 수련회 준비.txt" 자동 생성 | ✅ 완료 |
| m3 | 논리 | PRD "수련회 1주일 전 시작" 권장 누락 | Step 1 상단에 시간 권장 추가 | ✅ 완료 |
| m4 | 논리 | 메뉴판 9개 → 선택 장애 | 인기 앱 3개 강조 + 종합 앱 추천 문구 추가 | ✅ 완료 |

### 2차 심층 성찰 — 6건 (모두 수정 완료)

| 코드 | 심각도 | 문제 | 수정 내용 | 상태 |
|------|--------|------|-----------|------|
| D1 | Major | Phase 1 대화 중 진행률 표시 누락 | "[1/3] 어떤 앱인지 파악 중" 등 3단계 진행률 표시 추가 | ✅ 완료 |
| D2 | Major | Step 2→3 전환 시 끊김 방지 지침 없음 (E4 위반) | 자연스러운 전환 규칙 + 좋은/나쁜 예시 추가 | ✅ 완료 |
| D3 | Major | 종합 앱 통합 아키텍처 구체성 부족 | URL 라우팅, 통합 원칙, 모듈 구조 상세 추가 | ✅ 완료 |
| D4 | Minor | GitHub Pages 에러 처리 구체 분기 없음 | 5가지 에러별 대응 테이블 추가 | ✅ 완료 |
| D5 | Minor | 절전 모드 방지가 안내만, 자동 처리 없음 | powercfg 자동 실행 + 복원 + 폴백 안내 | ✅ 완료 |
| D6 | Minor | AI 퀴즈 생성 → 사역자 확인 흐름 미연결 | Content Matrix에 AI 생성 경로 + 확인 절차 추가 | ✅ 완료 |

### 3차 적대적 성찰 (3명 공격자) — 10건 (모두 수정 완료)

| 코드 | 심각도 | 공격자 | 문제 | 수정 내용 | 상태 |
|------|--------|--------|------|-----------|------|
| N1 | Critical | 사역자+실행 | workflow.md → Claude Code 연결 배선 없음 | "Activation Mechanism" 섹션 신설 — CLAUDE.md 수정사항, 슬래시 커맨드 사양, 사역자 첫 경험 흐름, SessionStart hook 지침 | ✅ 완료 |
| N2 | Critical | 실행 | 28K 토큰 전체 로드 시 컨텍스트 압박 | "Context Loading Strategy" 섹션 신설 — 핵심 ~300줄 상주 + Phase별 on-demand 로드 분할 전략 | ✅ 완료 |
| N3 | Major | 중학생 | PWA URL 바 노출 → "앱 아니고 사이트" | PWA 완전 구현 지침 추가 — manifest.json standalone, 홈 화면 추가 배너 3초 | ✅ 완료 |
| N4 | Major | 중학생 | 단색 플랫 팔레트 촌스러움 | 그라데이션 프리셋 3종 + 글래스모피즘 토큰 추가 | ✅ 완료 |
| N5 | Major | 중학생 | 시스템 폰트 = "윈도우 냄새" | Pretendard 서브셋(~50KB) 복원 (300KB 예산 내) | ✅ 완료 |
| N6 | Major | 중학생 | D1~D6 기준 너무 낮음 + 빔 화면 밋밋 | D7(마이크로인터랙션) + D8(스켈레톤UI) + D9(빔 이펙트/컨페티/효과음) 추가 | ✅ 완료 |
| N7 | Major | 중학생 | 35명 동시 버저 응답 지연 검증 없음 | Q11 Response Latency 게이트 추가 (WebSocket ≤100ms) | ✅ 완료 |
| N8 | Major | 실행 | Q1~Q9 자기채점 + 10턴 컨텍스트 소모 | verify-app.js 통합 검증 스크립트 — 1턴으로 전체 실행 | ✅ 완료 |
| N9 | Major | 사역자 | 9개 앱 유형별 특수 검증 부재 | 앱 유형별 추가 검증 테이블 5종 추가 (퀴즈 동시접속, 종합 라우팅 등) | ✅ 완료 |
| N10 | Minor | 실행 | .bat에 node_modules 검증 + QR 재생성 미구현 | node_modules 자동 복구 + regenerate-qr.js 별도 호출 로직 추가 | ✅ 완료 |
