# Lesson Package Generator

**본문에서 수업까지 — 본문·테마·대상·분량을 입력하면 가르칠 수 있는 수업안과 교보재·찬양·홍보영상을 한 번에 생성합니다.**

---

## 이 시스템이 하는 일

Lesson Package Generator는 교회 중고등부 교사를 위해, **자동 설계된 수업안(수업 계획)**을 핵심 산출물로 만드는 워크플로우 시스템입니다. 교보재·찬양·홍보영상은 그 수업안에서 파생되는 **부가 산출물**입니다.

```
[입력: 본문 · 테마 · 대상 · 분량]
   → ★ 수업안 설계 (MAIN)
   → 교보재 · 찬양 · 홍보영상 (부가, 선택)
   → 자기검수
   → [출력: 수업안 + 선택적 부가물 + 통합 패키지]
```

| 입력 | 출력 |
|------|------|
| 본문(성경 본문/원고/요약) | 수업안 (`lesson-plan.v1`: 학습목표·도입·본문전개·핵심메시지·적용·토의질문·마무리·시간배분) |
| 테마 / 강조점 | + 교보재 (도입게임·토의·활동·워크시트·슬라이드) |
| 대상 (연령·인원·맥락) | + 찬양 (오리지널 가사 + Suno 음악 프롬프트) |
| 분량 (분) | + 홍보영상 (내레이션·스토리보드·컷별 AI 프롬프트·자막) |
| | + 자기검수 보고서 (PK1–PK13) |

---

## 제품 위계 — Core vs Supplementary

| Tier | 단계 | 사용자 대면 이름 | MVP 필수 |
|------|------|------------------|----------|
| **Core** | 1 | 수업안 자동 설계 | **예** — 이것만으로도 가르칠 수 있어야 함 |
| **Supplementary** | 2 | 교보재 | 실행 단위 선택 |
| **Supplementary** | 3 | 찬양 | 실행 단위 선택 |
| **Supplementary** | 4 | 홍보영상 | 실행 단위 선택 |
| **Integration** | 5 | 자기검수 | 부가물 실행 시 항상 |

> **설계 불변식**: 부가물(2–4)은 본문을 독립적으로 재해석하지 않는다. 모두 승인된 **수업안의 핵심메시지**를 1차 입력으로 받는다.

---

## 핵심 특징

### 1. 수업안 우선(Lesson-Plan-First) 파이프라인
모든 가치의 중심은 수업안입니다. 교사는 부가 파일을 열지 않고 **수업안만으로** 한 회차를 진행할 수 있어야 합니다.

### 2. 두 가지 실행 표면 — 웹앱 + CLI
- **웹앱** (`webapp/`): 서버 없이 브라우저 단독으로 동작하는 단일 페이지 앱. 브라우저에서 Claude API를 직접 호출합니다. 비개발자 교사를 위한 기본 사용 경로입니다.
- **CLI** (`scripts/orchestrator.py`): Python 오케스트레이터. CI/오프라인 테스트용 placeholder 모드와 API 모드를 지원합니다.

두 표면은 **동일한 단계 프롬프트와 체이닝 로직**을 공유합니다.

### 3. 고정 출력 계약 (Output Contracts)
각 단계는 버전이 명시된 JSON 계약을 산출합니다: `lesson-plan.v1`(core), `teaching-materials.v1`, `praise-worship.v1`, `promo-video.v1`. 부가물은 이 계약을 통해 안정적으로 체이닝됩니다.

### 4. 결정론적 자기검수 (PK1–PK13)
Step 5는 LLM이 아니라 **결정론적 검사**로 패키지 무결성을 평가합니다 — 수업안 유효성(LP1–LP10), 부가물의 수업안 정합(핵심메시지·본문 구절 참조), 실행/스킵 일치 등. verdict는 재현 가능합니다.

### 5. 외부 생성 AI 핸드오프
- **찬양**: Suno용 단일 음악 프롬프트 → suno.com에서 음원 생성
- **홍보영상**: 컷별 영상 프롬프트(Runway/Pika/Kling 등) + 이미지 폴백 프롬프트 + SRT 자막
- **교보재**: `[IMG: …]` 슬롯 → 이미지 생성 AI

### 6. P1 검증 게이트
`validate_lesson_plan.py`(LP1–LP10)와 `validate_package_integrity.py`(PK1–PK13)가 산출물 품질을 결정론적으로 봉쇄합니다.

### 7. 휴먼 게이트
intake 확인 후, 그리고 **수업안 승인 후(부가물 생성 전)** 사람이 개입할 수 있습니다. `--auto-approve`로 비대화형(CI) 실행이 가능합니다.

---

## 시스템 아키텍처 (조감도)

```
                   ┌─────────────────────────────┐
                   │        Orchestrator          │
                   │  (단계 조율 + SOT 관리)       │
                   └───────────────┬─────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
  ┌─────▼─────┐            ┌───────▼───────┐          ┌───────▼───────┐
  │  Research  │            │   Planning     │          │ Implementation │
  │  intake    │            │ 부가물 선택·매핑 │          │  Steps 1–5     │
  └─────┬─────┘            └───────┬───────┘          └───────┬───────┘
        │                          │                          │
   lesson_intake.json        run_supplementary           ★ Step 1 수업안 (MAIN)
                                                                │  lesson-plan.v1
                                                    ┌───────────┼───────────┐
                                              Step 2 교보재  Step 3 찬양  Step 4 홍보영상
                                                    └───────────┼───────────┘
                                                          Step 5 자기검수
                                                                │
                                                    통합 패키지 + manifest
```

---

## 5단계 파이프라인 개요

### Implementation (생성)

| Step | 이름 | Tier | 입력 | 산출물(계약) |
|------|------|------|------|------|
| 1 | 수업안 설계 (MAIN) | Core | intake | `lesson-plan.v1` |
| 2 | 교보재 | Supplementary | 수업안 + intake | `teaching-materials.v1` |
| 3 | 찬양 | Supplementary | 수업안 + intake | `praise-worship.v1` |
| 4 | 홍보영상 | Supplementary | 수업안 + intake | `promo-video.v1` |
| 5 | 자기검수 | Integration | 수업안 + 부가물 | manifest + 보고서 (PK1–PK13) |

> Research(intake 정규화)와 Planning(부가물 선택·매핑 규칙)은 개념적 선행 단계입니다. 상세는 `lesson-package-generator/PLAN.md` §2 참조.

---

## 사전 준비

### 웹앱 (권장 — 교사용)

| 항목 | 필수 | 설명 |
|------|------|------|
| 최신 웹 브라우저 | 필수 | Chrome/Edge/Safari 등 |
| Anthropic API 키 | 필수 | console.anthropic.com에서 발급, 실행 중 ⚙️로 입력 |
| 정적 호스팅 | 선택 | GitHub Pages 등 (배포 시) |

### CLI (개발/CI)

| 항목 | 필수 | 설명 |
|------|------|------|
| Python 3.10+ | 필수 | 오케스트레이터·검증 스크립트 |
| PyYAML | 필수 | SOT(`state.yaml`) 파싱 |
| `anthropic` SDK + `ANTHROPIC_API_KEY` | 선택 | API 모드 (없으면 placeholder 모드) |
| ffmpeg | 선택 | 홍보영상 조립(`assemble_promo_video.py`) |

---

## 빠른 시작

### 웹앱

```text
1. lesson-package-generator/webapp/index.html 을 브라우저로 연다
2. 우측 상단 ⚙️ → Anthropic API 키 입력 후 저장 (브라우저 localStorage에만 저장)
3. 본문·테마·대상·분량 입력 + 부가물 선택
4. ✨ 생성하기 → 진행 표시 → 탭(수업안/교보재/찬양/홍보영상/자기검수)에서 확인
5. 다운로드(JSON/MD/SRT) + 프롬프트 복사(Suno·이미지·영상)
```

### CLI

```bash
cd lesson-package-generator

# 수업안만 (Step 1)
python scripts/orchestrator.py --body "누가복음 8:26-39" --audience "중등부" --volume 80 --emphasis "자유"

# 부가물 포함 + 비대화형
python scripts/orchestrator.py --body "..." --audience "..." --volume 80 --emphasis "자유" \
  --with-teaching --with-praise --with-promo --auto-approve

# P1 검증
python scripts/validate_lesson_plan.py
python scripts/validate_package_integrity.py
```

---

## 출력 계약과 검증

| 계약 | 산출 단계 | 검증 스크립트 | 검증 항목 |
|------|----------|--------------|----------|
| `lesson-plan.v1` (core) | Step 1 | `validate_lesson_plan.py` | LP1–LP10 (섹션·시간배분 합·토의질문 수 등) |
| `teaching-materials.v1` | Step 2 | 모듈 내부 `validate_teaching_package` | 4종 컴포넌트·슬라이드·본문 |
| `praise-worship.v1` | Step 3 | 모듈 내부 `validate_praise_package` | 가사 구조·Suno 프롬프트 |
| `promo-video.v1` | Step 4 | 모듈 내부 `validate_promo_package` | 컷 길이 합(30–45초)·자막 |
| 패키지 manifest | Step 5 | `validate_package_integrity.py` | PK1–PK13 (무결성·정합·본문 참조) |

> 웹앱은 PK1–PK13을 `js/selfcheck.js`에서 동일하게 계산합니다(LLM 미사용).

---

## 산출물 구조

```
lesson-package-generator/
├── PLAN.md                       ← 설계 v0.2 (수업안 = MAIN)
├── workflow.md, state.yaml       ← 파이프라인 정의 + SOT
├── scripts/
│   ├── orchestrator.py           ← 단계 조율 + 휴먼 게이트 + run_supplementary
│   ├── lesson_plan_contract.py / lesson_plan_generate.py   (core)
│   ├── teaching_*.py / praise_*.py / promo_*.py             (부가)
│   ├── package_check.py          ← PK1–PK13 엔진
│   ├── validate_lesson_plan.py / validate_package_integrity.py
│   └── modules/step1_lesson_plan.py … step5_self_check.py
├── schemas/                      ← JSON Schema (lesson_plan 등)
├── agents/prompts/               ← step1…step5 단계 프롬프트
├── webapp/                       ← 브라우저 단독 웹앱 (서버 없음)
│   ├── index.html, manifest.webmanifest
│   ├── css/styles.css
│   └── js/ (prompts·api·selfcheck·pipeline·render·app)
├── outputs/                      ← 생성물 (lesson_plan·teaching·praise·promo·package)
└── tests/                        ← pytest
```

---

## DNA 유전 (부모 게놈)

이 시스템은 **AgenticWorkflow** 만능줄기세포로부터 분화된 자식 유기체입니다.

| DNA 구성 요소 | 유전된 형태 |
|-------------|-----------|
| 3단계 구조 | Research(intake) → Planning(부가물 선택) → Implementation(1–5) |
| SOT 패턴 | `state.yaml` — 단일 작성자(Orchestrator) |
| 4계층 QA | L0 Anti-Skip → L1 Verification → L1.5 pACS → L2 Review |
| P1 할루시네이션 봉쇄 | LP1–LP10, PK1–PK13 결정론적 검증 |
| P2 전문 위임 | 단계별 독립 모듈(1 run() + 1 prompt) |
| 휴먼 게이트 | intake 확인 · 수업안 승인 |

상세: [`soul.md`](soul.md)

---

## 문서 안내

| 문서 | 대상 독자 | 내용 |
|------|---------|------|
| **이 문서 (`LESSON-PACKAGE-README.md`)** | 모든 사람 | 개요, 핵심 특징, 빠른 시작 |
| **[`LESSON-PACKAGE-ARCHITECTURE-AND-PHILOSOPHY.md`](LESSON-PACKAGE-ARCHITECTURE-AND-PHILOSOPHY.md)** | 아키텍트, 개발자 | 설계 철학, 파이프라인 구조, 두 실행 표면, 데이터 플로우, 설계 결정 |
| **[`LESSON-PACKAGE-USER-MANUAL.md`](LESSON-PACKAGE-USER-MANUAL.md)** | 교사, 사용자 | 웹앱 단계별 사용법, API 키 설정, 외부 AI 핸드오프 |
| [`PLAN.md`](lesson-package-generator/PLAN.md) | 아키텍트 | 마스터 플랜 v0.2 (단계·계약·검증 명세) |
| [`AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`](AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md) | 프레임워크 이해 | 부모 유기체의 설계 철학 |

---

## 저작권

이 시스템과 그 산출물은 [`COPYRIGHT.md`](COPYRIGHT.md)의 조건을 따릅니다. 찬양 가사는 오리지널 창작물이며, 외부 배포 전 CCLI 등 권리 확인이 필요합니다.
