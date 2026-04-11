# AI Studio

**"시작"이라고 말하면 시작됩니다.**

대화만으로 앱을 만들고, 자서전을 쓰고, 워크플로우를 설계하고, 논문을 다듬는 AI 워크플로우 시스템입니다.
코딩 경험이 없어도 됩니다. 한국어로 대화하면 AI가 나머지를 처리합니다.

> 이 시스템은 [AgenticWorkflow](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) 프레임워크에서 태어난 **자식 시스템**입니다.
> 부모의 전체 DNA(품질 기준, 안전장치, 기억 체계, 검증 구조)를 내장하고 있습니다.

---

## 실행 모드

| # | 모드 | 만들어지는 것 | 소요 시간 |
|---|------|-------------|----------|
| **1** | **수련회 앱 만들기** | 모바일 웹앱 + QR코드 | 수 시간 |
| **2** | **자서전 쓰기** | PDF/EPUB 책 | 수 일~주 |
| **3** | **워크플로우 설계** | workflow.md 설계도 | 수 시간 |
| **4** | **학술 글쓰기** | 박사급 논문 문체 문서 | 즉시 |

---

## 시작하기

### 1단계: 시작 명령

Claude Code에서 다음 중 아무거나 입력하세요:

```
시작
시작하자
start
```

### 2단계: 모드 선택

메뉴가 나타나면 **번호**를 입력하거나, 하고 싶은 것을 **자유롭게** 말하세요:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   AgenticWorkflow — 제품 실행 모드
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 수련회 앱 만들기
  2. 자서전 쓰기
  3. 워크플로우 설계
  4. 학술 글쓰기

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3단계: 대화로 진행

AI가 필요한 것을 물어봅니다. 한국어로 답하면 됩니다.

```
예시 (수련회 앱):
  AI: "어떤 앱을 만들까요? 성경 퀴즈, 스탬프 랠리, 일정표..."
  나: "성경 퀴즈 앱이요"
  AI: "어떤 성경 범위를 다루나요?"
  나: "마태복음, 4팀이 참가해요"
  AI: → 앱 생성 중... → 완성! QR코드가 여기 있습니다
```

---

## 진행 중인 프로젝트가 있다면

이전에 시작한 프로젝트가 있으면, **자동으로 감지**하여 `[진행 중]` 뱃지가 표시됩니다.
"이어서 진행할까요?"라고 물어보니, 이어서 하시면 됩니다.

현재 상태를 확인하려면:

```
/status
```

---

## 슬래시 명령어

| 명령어 | 설명 |
|--------|------|
| `/start` | 제품 실행 모드 진입 (시작 메뉴) |
| `/status` | 전체 프로젝트 상태 대시보드 |
| `/start-app` | 수련회 앱 새로 시작 |
| `/resume-app` | 수련회 앱 이어서 진행 |
| `/deploy-app` | 수련회 앱 배포 |
| `/app-status` | 수련회 앱 상태 확인 |
| `/app-verify` | 수련회 앱 품질 검증 |
| `/interview` | 자서전 인터뷰 시작 |
| `/review-chapter` | 자서전 챕터 검토 |
| `/build-verify` | 빌드 검증 |
| `/export` | PDF/EPUB 내보내기 |
| `/maintenance` | 시스템 건강 검진 |

---

## 프로젝트 구조

```
AgenticWorkflow/
│
├── [제품 시스템 문서]
│   ├── AI-STUDIO-README.md               ← 이 파일 (제품 소개)
│   ├── AI-STUDIO-USER-MANUAL.md          ← 사용자 매뉴얼
│   └── AI-STUDIO-ARCHITECTURE-AND-PHILOSOPHY.md  ← 제품 아키텍처
│
├── [부모 프레임워크 문서]
│   ├── AGENTICWORKFLOW-USER-MANUAL.md    ← 프레임워크 사용법
│   ├── AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md ← 프레임워크 설계 철학
│   ├── soul.md                           ← DNA 유전 정의
│   ├── AGENTS.md                         ← AI 에이전트 공통 규칙 (Hub)
│   ├── CLAUDE.md                         ← Claude Code 지시서
│   └── DECISION-LOG.md                   ← 설계 결정 로그
│
├── [실행 엔진]
│   ├── .claude/
│   │   ├── commands/ (14개)               ← 슬래시 명령어 (start, status 등)
│   │   ├── agents/ (22개)                ← 전문 AI 에이전트
│   │   ├── hooks/scripts/ (54개)         ← 자동 검증·안전·상태 관리
│   │   ├── skills/ (4개)                 ← 실행 모드별 스킬
│   │   │   ├── church-retreat-app/       ← 수련회 앱 생성
│   │   │   ├── autobiography/            ← 자서전 생성
│   │   │   ├── workflow-generator/       ← 워크플로우 설계
│   │   │   └── doctoral-writing/         ← 학술 글쓰기
│   │   └── schemas/                      ← SOT JSON 스키마
│   │
│   └── autobiography-generator/          ← 자서전 서브프로젝트
│       ├── state.yaml                    ← 자서전 SOT
│       ├── scripts/ (36+개)
│       └── webapp/                       ← Next.js 대시보드
│
├── [자서전 하위 시스템 문서]
│   ├── AUTOBIOGRAPHY-README.md
│   ├── AUTOBIOGRAPHY-USER-MANUAL.md
│   └── AUTOBIOGRAPHY-ARCHITECTURE-AND-PHILOSOPHY.md
│
└── [자원]
    ├── translations/glossary.yaml        ← 번역 용어 사전
    ├── prompt/                           ← 프롬프트 자료
    └── coding-resource/                  ← 이론적 기반
```

---

## 문서 읽기 순서

| 순서 | 문서 | 목적 |
|------|------|------|
| 1 | **이 파일** (`AI-STUDIO-README.md`) | 제품 개요 파악 |
| 2 | [`AI-STUDIO-USER-MANUAL.md`](AI-STUDIO-USER-MANUAL.md) | 실제 사용법 |
| 3 | [`AI-STUDIO-ARCHITECTURE-AND-PHILOSOPHY.md`](AI-STUDIO-ARCHITECTURE-AND-PHILOSOPHY.md) | 내부 구조 이해 (선택) |

> 부모 프레임워크(AgenticWorkflow)의 방법론이 궁금하다면:
> [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md)

---

## 부모-자식 관계

```
AgenticWorkflow (부모 = 만능줄기세포)
  │
  ├── AI Studio (자식 = 이 제품)
  │     ├── 수련회 앱 생성기
  │     ├── 자서전 생성기  ← 별도 문서: AUTOBIOGRAPHY-*.md
  │     ├── 워크플로우 설계기
  │     └── 학술 글쓰기 도구
  │
  └── (미래의 다른 자식 시스템들...)
```

이 제품은 부모의 DNA를 **내장**합니다:
- **품질 최우선**: 속도·비용보다 결과물의 품질이 유일한 기준
- **4계층 품질 보장**: 자동 검증 → 의미 검증 → 신뢰도 평가 → 적대적 리뷰
- **131개 자동화 테스트**: 안전장치가 코드 수준에서 동작
- **컨텍스트 보존**: 세션이 끊어져도 작업 내역이 자동 저장·복원
