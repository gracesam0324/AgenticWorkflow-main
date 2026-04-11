# AI Autobiography Generator

**인터뷰에서 책까지 — AI 에이전트 파이프라인으로 인생 이야기를 출판 품질의 자서전으로 변환합니다.**

---

## 이 시스템이 하는 일

AI Autobiography Generator는 인물의 인생 이야기를 **전문적으로 조판된 자서전 책**으로 변환하는 다중 에이전트 워크플로우 시스템입니다.

```
인터뷰(대화) ──→ 스토리 바이블(구조) ──→ 챕터 산문(글) ──→ 완성 도서(PDF/EPUB)
```

| 입력 | 출력 |
|------|------|
| 인물의 인생 경험 (AI 인터뷰 세션) | PDF (memoir 클래스) + EPUB |
| | + Story Bible (서사 구조 SOT) |
| | + 영한 병렬 출판물 |

---

## 핵심 특징

### 1. 12단계 파이프라인
Research(1-4) → Planning(5-8) → Implementation(9-12) 3단계 구조로, 인터뷰 수집부터 PDF 빌드까지 전 과정을 자동화합니다.

### 2. 8종 전문 에이전트
인터뷰어, 스토리 아키텍트, 챕터 라이터, 보이스 캘리브레이터, 적대적 리뷰어, 심층 리뷰어, 번역가 — 각 단계에 최적화된 전문 에이전트가 작동합니다.

### 3. 보이스 피델리티 시스템
인터뷰에서 추출한 **수치 기반 보이스 지문**(문장 길이, 대화 비율, 어휘 수준 등)을 Python으로 계산하고, 10종 작가 스타일(헤밍웨이~무라카미)과 수학적으로 블렌딩합니다. AI 추정치가 아닌 **결정론적 메트릭**이 글쓰기를 지배합니다.

### 4. 4계층 품질 보장
```
L0 Anti-Skip Guard ──→ L1 Verification Gate (Python) ──→ L1.5 pACS Self-Rating ──→ L2 Adversarial Review (@reviewer)
```
30개 이상의 검증 항목(SB1-SB10, CH1-CH10, CC1-CC8, BP1-BP7, VM1-VM6 등)이 결정론적으로 실행됩니다.

### 5. 프로젝트 격리
각 자서전 프로젝트(`projects/{YYYYMMDD-이름}/`)는 symlink 기반으로 완전히 격리됩니다. 여러 자서전을 동시에 작업해도 산출물이 뒤섞이지 않습니다.

### 6. 영한 병렬 출판
모든 단계에서 `@translator` 에이전트가 영어 원본을 한국어로 번역합니다. 최종 도서는 영어판과 한국어판이 동시에 생산됩니다.

### 7. 한국 문학 품질 시스템 (Appendix A)
11개의 문학 지시문(A-1~A-11)이 한국어 자서전의 문학적 품격을 보장합니다:

| 지시문 | 핵심 |
|--------|------|
| A-2: 개인사=시대사 | 역사가 일상에 침투하는 체험으로 서술 (배경 설명 금지) |
| A-3: 여운 | 교훈·도덕·요약 없는 엔딩 (4가지 허용 기법) |
| A-4: 침묵 | 침묵을 서사 콘텐츠로 사용 (챕터당 최소 1회) |
| A-5: 기승전결 | 4막 리듬 — 전(轉)은 관점 전환이지 클라이맥스가 아님 |
| A-6: 한/흥/정 | 체화된 감정 — 단어 자체는 산문에 라벨로 절대 사용 금지 |
| A-7: 이중 의식 | 체험하는 자아 vs 서술하는 자아의 비율 (인생 시기별) |
| A-8: 존댓말 변화 | 인생 시기별 경어 전환을 보여주되 설명하지 않음 |
| A-9: 장면 구성 6단계 | 핫스팟→장소→감각→대화→신체화→의미 (챕터당 ≥2장면) |
| A-10: 번역체 9패턴 금지 | 피동 되다, 것이다, ~적(的) 남발 등 원천 차단 |
| A-11: 허용 윤색 프로토콜 | 대화 재구성, 감각 디테일 허용 / 사건 날조 금지 (`[INFERRED]` 태깅) |

### 8. 학술 기반 인터뷰 방법론
단순 질의응답이 아닌 4가지 학술 프레임워크의 융합:
- **McAdams Life Story Interview** — 8개 인생 시기 × 44개 질문 구조
- **Kvale 9-Type Follow-Up** — 적응적 후속 질문 상태 머신
- **Tulving Redirect** — 빈약한 응답(3연속 <30단어) 시 의미 기억→에피소드 기억 전환
- **Rubin Sensory Cues** — 비자발적 자전적 기억 활성화 (세션당 ≥1 감각 단서)

### 9. 웹 대시보드
Next.js 기반 웹앱이 `autobiography-generator/webapp/`에 포함되어, 챕터 진행 상황과 품질 메트릭을 시각적으로 모니터링할 수 있습니다.

---

## 시스템 아키텍처 (조감도)

```
                         ┌─────────────────────────────────┐
                         │        Orchestrator             │
                         │   (워크플로우 조율 + SOT 관리)    │
                         └─────────┬───────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            │                      │                      │
    ┌───────▼───────┐    ┌────────▼────────┐    ┌────────▼────────┐
    │   Research     │    │   Planning       │    │ Implementation  │
    │  Steps 1-4     │    │  Steps 5-8       │    │  Steps 9-12     │
    └───────┬───────┘    └────────┬────────┘    └────────┬────────┘
            │                      │                      │
   @interviewer           @story-architect        @chapter-writer
   (인터뷰 수행)          (스토리 바이블 구축)      (챕터 산문 작성)
                                                          │
                                               @voice-calibrator
                                               (보이스 메트릭 검증)
                                                          │
                                                  @reviewer
                                               (적대적 품질 평가)
                                                          │
                                                 @translator
                                               (영→한 번역)
                                                          │
                                                ┌─────────▼─────────┐
                                                │   Book Build       │
                                                │ PDF + EPUB (EN/KO) │
                                                └───────────────────┘
```

---

## 12단계 파이프라인 개요

### Research (조사)

| Step | 이름 | 에이전트 | 산출물 |
|------|------|---------|--------|
| 1 | Interview Planning | Orchestrator | `interview_plan.md` |
| 2 | Conduct Interviews | `@interviewer` | `INT-{NNN}.json` (세션별) |
| 3 | (human) Interview Review | 사용자 | 승인 / 추가 세션 요청 |
| 4 | (human) Story Blueprint Co-Creation | `@story-architect` + 사용자 | `story_blueprint.json` |

### Planning (기획)

| Step | 이름 | 에이전트 | 산출물 |
|------|------|---------|--------|
| 5 | Story Bible Construction | `@story-architect` | `story_bible.json` |
| 6 | Story Bible Review | `@reviewer` | `RV-story-bible.json` |
| 7 | (human) Story Bible Approval | 사용자 | 승인 / 수정 요청 |
| 8 | (human) Writing Style Selection | `@chapter-writer` + 사용자 | `style_selection.json` |

### Implementation (구현)

| Step | 이름 | 에이전트 | 산출물 |
|------|------|---------|--------|
| 9 | Chapter Writing Loop | `@chapter-writer` + `@voice-calibrator` + `@reviewer` | `ch{NN}_draft_v{V}.md` |
| 10 | Cross-Chapter Consistency | `@reviewer` + `@reviewer-deep` | `consistency-report.json` |
| 11 | (human) Manuscript Review | 사용자 | 최종 승인 |
| 12 | Book Build | Orchestrator | `book_latest.pdf` + `.epub` (EN/KO) |

---

## 사전 준비

| 항목 | 필수 여부 | 설명 |
|------|----------|------|
| [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) | 필수 | `npm install -g @anthropic-ai/claude-code` |
| Python 3.10+ | 필수 | 검증 스크립트, 보이스 분석, 빌드 파이프라인 |
| PyYAML | 필수 | SOT 파일 파싱 |
| jsonschema | 필수 | JSON Schema 검증 |
| Pandoc + XeLaTeX | 선택 | PDF/EPUB 빌드 (Step 12) |

---

## 빠른 시작

```bash
# 1. 프로젝트 디렉터리에서 Claude Code 실행
cd Writingbook-AgenticWorkflow
claude

# 2. 워크플로우 시작
> 시작하자

# 3. /start 커맨드가 자동 실행됨
#    - 실행 모드 선택 (Autopilot / Manual / ULW)
#    - 프로젝트 초기화 (이름, 날짜, 디렉터리)
#    - Step 1부터 자동 진행
```

---

## 에이전트 생태계

| 에이전트 | 모델 | 역할 | SOT 접근 |
|---------|------|------|----------|
| Orchestrator | opus | 워크플로우 조율, 상태 관리 | Read/Write `state.yaml` |
| `@interviewer` | opus | AI 인터뷰 진행, 감각적 디테일 추출 | Read only |
| `@story-architect` | opus | 스토리 바이블 구축 (타임라인, 인물, 테마) | Write `story_bible.json` |
| `@chapter-writer` | opus | 산문 작성 (스타일 블렌딩 적용) | Read only |
| `@voice-calibrator` | sonnet | 보이스 메트릭 분석 (정량적 편차 리포트) | Read only |
| `@reviewer` | opus | 적대적 품질 평가 (7차원 + CoVe) | Read only |
| `@reviewer-deep` | opus | 동질화 방지 심층 스캔 (Step 10) | Read only |
| `@translator` | opus | 영→한 번역 (용어 사전 기반, 7단계 프로토콜) | Read only |

---

## 검증 스크립트 (P1 할루시네이션 봉쇄)

| 스크립트 | 검증 항목 | 트리거 시점 |
|---------|----------|-----------|
| `validate_story_bible.py` | SB1-SB10 (엔티티, 타임라인, 캐릭터, 테마) | Step 5 완료 후 |
| `validate_chapter.py` | CH1-CH10 (산문 품질, 출처, 분량) | Step 9b 완료 후 |
| `validate_consistency.py` | CC1-CC8 (교차 챕터 일관성) | Step 10 |
| `validate_blueprint.py` | BP1-BP7 (블루프린트 구조) | Step 4 완료 후 |
| `validate_voice_match.py` | VM1-VM6 (보이스 가이드 편차) | Step 9b, 9c |
| `validate_source_tracing.py` | ST1-ST6 (출처 추적성) | Step 5, 9b |
| `validate_pacs_floor.py` | pACS 자기평가 인플레이션 검증 | Step 6, 9d |
| `compute_voice_fingerprint.py` | 결정론적 보이스 메트릭 추출 | Step 4 전처리 |
| `style_blender.py` | 스타일 파라미터 블렌딩 (순수 산술) | Step 8 후처리 |
| `schema_validator.py` | JSON Schema 적합성 | 모든 JSON 쓰기 후 |

---

## 글쓰기 스타일 라이브러리

10종의 작가 스타일 스킬이 `.claude/skills/writing-styles/`에 내장되어 있습니다:

| 스타일 | 특징 |
|--------|------|
| Hemingway | 짧은 문장, 감정 절제, "빙산 이론" |
| Márquez | 마법적 사실주의, 긴 문장, 감각적 묘사 |
| Dostoevsky | 내면 독백, 철학적 탐구, 심리 갈등 |
| Orwell | 명료한 산문, 정치적 의식, 간결한 진실 |
| Austen | 사회적 관찰, 아이러니, 세밀한 대화 |
| Kant | 체계적 논증, 개념적 정밀성, 추상적 깊이 |
| Hesse | 영적 탐구, 자기 발견, 상징적 여정 |
| Shakespeare | 극적 구조, 언어유희, 보편적 인간성 |
| Murakami | 일상 속 초현실, 음악적 리듬, 고독한 화자 |
| Woolf | 의식의 흐름, 시간의 주관성, 감각적 인상 |

사용자의 인터뷰 보이스 지문과 선택한 스타일을 **수학적으로 블렌딩**하여 (기본 30% 스타일 / 70% 화자 보이스), 화자의 고유한 목소리를 보존하면서 문학적 품격을 더합니다.

---

## 산출물 구조

```
autobiography-generator/
├── projects/
│   └── {YYYYMMDD-이름}/          ← 프로젝트별 격리 디렉터리
│       ├── outputs/
│       │   ├── interviews/
│       │   │   ├── interview_plan.md
│       │   │   ├── INT-001.json
│       │   │   └── INT-{NNN}.json
│       │   ├── story-blueprint/
│       │   │   └── story_blueprint.json
│       │   ├── voice_fingerprint.json
│       │   ├── story-bible/
│       │   │   └── story_bible.json
│       │   ├── style-selection/
│       │   │   └── style_selection.json
│       │   ├── chapters/
│       │   │   ├── ch01_draft_v1.md
│       │   │   ├── ch01_draft_v1.meta.json
│       │   │   └── ...
│       │   └── builds/
│       │       ├── book_latest.pdf        (영문)
│       │       ├── book_latest.epub       (영문)
│       │       ├── book_latest.ko.pdf     (한국어)
│       │       └── book_latest.ko.epub    (한국어)
│       └── review-logs/
│           ├── RV-story-bible.json
│           ├── RV-ch01-round1.json
│           └── consistency-report.json
├── schemas/                              ← JSON Schema 정의
├── scripts/                              ← 검증·빌드 스크립트 30종+
├── agents/prompts/                       ← 에이전트 프롬프트 템플릿
├── config/                               ← 감정 키워드, 한자 사전
├── templates/                            ← EPUB 메타데이터, 문서 표준
└── workflow.md                           ← 파이프라인 정의서
```

---

## DNA 유전 (부모 게놈)

이 시스템은 **AgenticWorkflow** 만능줄기세포로부터 분화된 자식 유기체입니다.

| DNA 구성 요소 | 유전된 형태 |
|-------------|-----------|
| 3단계 구조 | Research(1-4) → Planning(5-8) → Implementation(9-12) |
| SOT 패턴 | `.claude/state.yaml` — 단일 작성자(Orchestrator) |
| 4계층 QA | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 Review |
| P1 할루시네이션 봉쇄 | 30종+ 검증 스크립트 |
| P2 전문 위임 | 8종 전문 에이전트 |
| Safety Hooks | 위험 명령 차단, 시크릿 탐지, TDD Guard |
| Context Preservation | 세션 자동 저장·복원 |
| 번역 파이프라인 | English-First → `@translator` → 한국어 쌍 |

상세: [`soul.md`](soul.md) — 부모 게놈의 전체 사양

---

## 문서 안내

| 문서 | 대상 독자 | 내용 |
|------|---------|------|
| **이 문서 (`AUTOBIOGRAPHY-README.md`)** | 모든 사람 | 시스템 개요, 핵심 특징, 빠른 시작 |
| **[`AUTOBIOGRAPHY-ARCHITECTURE-AND-PHILOSOPHY.md`](AUTOBIOGRAPHY-ARCHITECTURE-AND-PHILOSOPHY.md)** | 아키텍트, 개발자 | 설계 철학, 아키텍처 심층 분석, 데이터 플로우, 설계 결정 근거 |
| **[`AUTOBIOGRAPHY-USER-MANUAL.md`](AUTOBIOGRAPHY-USER-MANUAL.md)** | 사용자, 운영자 | 단계별 사용 가이드, 커맨드 레퍼런스, 트러블슈팅 |
| [`workflow.md`](autobiography-generator/workflow.md) | 아키텍트, 개발자 | 12단계 파이프라인 상세 명세 (검증 체크리스트, 에이전트 레지스트리, 훅 설정) |
| [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) | 프레임워크 이해 | 부모 유기체(만능줄기세포)의 설계 철학과 아키텍처 |
| [`AGENTICWORKFLOW-USER-MANUAL.md`](AGENTICWORKFLOW-USER-MANUAL.md) | 프레임워크 사용 | 부모 유기체의 워크플로우 설계·구현 방법 |

---

## 저작권

이 시스템과 그 산출물은 [`COPYRIGHT.md`](COPYRIGHT.md)의 조건을 따릅니다.
