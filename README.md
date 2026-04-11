# AI Studio

**"시작하자"라고 말하면 시작됩니다.**

대화만으로 앱을 만들고, 자서전을 쓰고, 워크플로우를 설계하고, 논문을 다듬는 AI 시스템입니다.

```
시작하자
```

이것만 입력하면 됩니다.

---

## 무엇을 할 수 있나요?

| # | 모드 | 만들어지는 것 |
|---|------|-------------|
| **1** | **수련회 앱 만들기** | 모바일 웹앱 + QR코드 (GitHub Pages 배포) |
| **2** | **자서전 쓰기** | PDF/EPUB 출판 가능한 책 |
| **3** | **워크플로우 설계** | 자동화 워크플로우 설계도 (workflow.md) |
| **4** | **학술 글쓰기** | 박사급 논문 문체 문서 (한국어·영어) |

---

## 시작하기

```
사용자: "시작하자"
   ↓
┌─────────────────────────────────┐
│   실행 모드를 선택하세요          │
├─────────────────────────────────┤
│ 1. 수련회 앱 만들기              │
│ 2. 자서전 쓰기                  │
│ 3. 워크플로우 설계               │
│ 4. 학술 글쓰기                  │
└─────────────────────────────────┘
   ↓ (번호 입력 또는 자유롭게 말하기)
   ↓
대화로 진행 → 결과물 완성
```

진행 중인 프로젝트가 있으면 `[진행 중]` 표시가 되어, 이어서 작업할 수 있습니다.

---

## 문서 안내

### 이 제품 (AI Studio)

| 문서 | 내용 |
|------|------|
| **[AI-STUDIO-USER-MANUAL.md](AI-STUDIO-USER-MANUAL.md)** | **사용자 매뉴얼** — 시작부터 결과물까지 |
| [AI-STUDIO-README.md](AI-STUDIO-README.md) | 제품 상세 소개 + 프로젝트 구조 |
| [AI-STUDIO-ARCHITECTURE-AND-PHILOSOPHY.md](AI-STUDIO-ARCHITECTURE-AND-PHILOSOPHY.md) | 제품 아키텍처와 설계 철학 |

### 자서전 하위 시스템

| 문서 | 내용 |
|------|------|
| [AUTOBIOGRAPHY-README.md](AUTOBIOGRAPHY-README.md) | 자서전 시스템 소개 |
| [AUTOBIOGRAPHY-USER-MANUAL.md](AUTOBIOGRAPHY-USER-MANUAL.md) | 자서전 사용법 |
| [AUTOBIOGRAPHY-ARCHITECTURE-AND-PHILOSOPHY.md](AUTOBIOGRAPHY-ARCHITECTURE-AND-PHILOSOPHY.md) | 자서전 아키텍처 |

### 부모 프레임워크 (AgenticWorkflow)

> 이 제품을 **만든 도구**에 대한 문서입니다. 사용에는 필요하지 않습니다.

| 문서 | 내용 |
|------|------|
| [AGENTICWORKFLOW-USER-MANUAL.md](AGENTICWORKFLOW-USER-MANUAL.md) | 프레임워크 사용법 |
| [AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) | 프레임워크 설계 철학 |
| [soul.md](soul.md) | DNA 유전 정의 — 부모-자식 관계의 핵심 |
| [AGENTS.md](AGENTS.md) | AI 에이전트 공통 규칙 (Hub) |
| [CLAUDE.md](CLAUDE.md) | Claude Code 지시서 |
| [DECISION-LOG.md](DECISION-LOG.md) | 설계 결정 로그 (ADR 56건) |

---

## 부모-자식 관계

이 프로젝트는 **만능줄기세포**(AgenticWorkflow)와 그로부터 태어난 **자식 시스템**(AI Studio)을 구분합니다.

```
AgenticWorkflow (부모 = 만능줄기세포 프레임워크)
  │
  ├── AI Studio (자식 = 이 제품)
  │     ├── 수련회 앱 생성기
  │     ├── 자서전 생성기       ← 별도 문서: AUTOBIOGRAPHY-*.md
  │     ├── 워크플로우 설계기
  │     └── 학술 글쓰기 도구
  │
  └── (미래의 다른 자식 시스템들...)
```

- **부모 문서** (`AGENTICWORKFLOW-*.md`): 방법론과 프레임워크를 기술
- **자식 문서** (`AI-STUDIO-*.md`): 도메인 고유 아키텍처를 기술
- 이 분리는 자식 시스템이 **독립적으로 이해·운영**될 수 있게 합니다

---

## 유용한 명령어

| 입력 | 동작 |
|------|------|
| **시작하자** | 제품 실행 모드 메뉴 |
| **/status** | 프로젝트 상태 대시보드 |
| **/start-app** | 수련회 앱 새로 시작 |
| **/interview** | 자서전 인터뷰 시작 |
| **/maintenance** | 시스템 건강 검진 |

---

## 내장된 보호 장치

- **4계층 품질 보장**: 자동 검증 → 의미 검증 → 신뢰도 평가 → 적대적 리뷰
- **131개 안전 테스트**: 위험 명령 차단, 시크릿 탐지, 민감 파일 보호
- **자동 저장**: 세션이 끊어져도 작업 내역 자동 복원
- **54 Hook 스크립트**: 코드 수준의 결정론적 검증 (AI 판단 0%)

---

## 프로젝트 구조

```
AgenticWorkflow/
├── [제품 문서]
│   ├── README.md                         ← 이 파일
│   ├── AI-STUDIO-README.md               ← 제품 상세 소개
│   ├── AI-STUDIO-USER-MANUAL.md          ← 사용자 매뉴얼
│   └── AI-STUDIO-ARCHITECTURE-AND-PHILOSOPHY.md
│
├── [실행 엔진]
│   ├── .claude/
│   │   ├── commands/start.md             ← 제품 실행 모드 진입점
│   │   ├── agents/ (22개)                ← 전문 AI 에이전트
│   │   ├── hooks/scripts/ (54개)         ← 자동 검증·안전·상태
│   │   └── skills/ (4개)                 ← 실행 모드별 스킬
│   └── autobiography-generator/          ← 자서전 서브프로젝트
│
├── [부모 프레임워크 문서]
│   ├── AGENTICWORKFLOW-*.md, soul.md, AGENTS.md, CLAUDE.md
│   └── docs/protocols/                   ← 상세 프로토콜
│
├── [자서전 하위 시스템 문서]
│   └── AUTOBIOGRAPHY-*.md (3개)
│
└── [자원]
    ├── translations/                     ← 번역 용어 사전
    ├── prompt/                           ← 프롬프트 자료
    └── coding-resource/                  ← 이론적 기반
```

---

*이 시스템은 [AgenticWorkflow](soul.md) 프레임워크에서 태어났습니다. 부모의 전체 DNA를 내장하고 있습니다.*
