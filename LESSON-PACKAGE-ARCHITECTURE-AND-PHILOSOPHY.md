# Lesson Package Generator: Architecture and Philosophy

> 수업안을 핵심 산출물로 삼는 로컬 우선 워크플로우의 설계 철학과 아키텍처.
> 부모 유기체 `AGENTICWORKFLOW-ARCHITECTURE-AND-PHILOSOPHY.md`의 게놈을 도메인에 맞게 발현한 자식 시스템이다.

---

## 목차

1. 설계 철학
2. 왜 자동 수업안인가
3. 파이프라인 아키텍처
4. 두 가지 실행 표면 (CLI · 웹앱)
5. 데이터 플로우와 출력 계약
6. 자기검수 아키텍처 (PK1–PK13)
7. 품질 보장 아키텍처
8. 외부 생성 AI 핸드오프
9. DNA 유전 상세
10. 주요 설계 결정 (ADR)

---

## 1. 설계 철학

### 1.1 핵심 신념: 수업안이 제품이다

이 시스템의 제1 가치는 **가르칠 수 있는 수업안**이다. 교보재·찬양·홍보영상은 매력적이지만, 그것들은 수업안에서 파생되는 부가물일 뿐이다. 성공 기준은 단 하나로 환원된다:

> 교사가 부가 파일을 단 하나도 열지 않고, **수업안만으로** 한 회차를 온전히 진행할 수 있는가?

이 신념은 코드 구조에 그대로 박혀 있다. Step 1은 필수(mandatory)이며, Step 2–4는 Step 1의 산출물(`lesson_plan.json`)이 검증을 통과하기 전에는 실행될 수 없다(하드 가드).

### 1.2 품질 절대주의의 수업 도메인 적용

부모의 절대 기준 1(품질 최우선)은 이 도메인에서 다음과 같이 발현된다:

- 단계를 줄여 빠르게 만들기보다, 자기검수 단계를 추가해서라도 패키지의 내부 정합을 보장한다.
- placeholder(오프라인) 모드조차 `"[자리표시자]"`가 아니라 **분량에 맞춰 시간배분이 정확히 합산되는 실제 수업안**을 산출한다(구조 데모 가능성 보장).
- 부가물은 수업안의 핵심메시지에서 파생되어야 하며, 이를 자기검수가 정합성으로 확인한다.

### 1.3 Core/Supplementary Tier 분리

자서전 시스템이 Generator-Critic 패턴을 이중 적용했다면, 이 시스템의 구조적 핵심은 **Tier 분리**다:

| Tier | 책임 | 독립성 |
|------|------|--------|
| Core (Step 1) | 본문 해석의 유일한 권위 | 본문을 해석하는 단 하나의 지점 |
| Supplementary (Step 2–4) | 수업안을 매체로 변환(게임·노래·영상) | 본문을 **재해석하지 않음** — 수업안 입력만 소비 |
| Integration (Step 5) | 전체 정합 검수 | 결정론적 |

> 부가물이 본문을 독립 해석하면 수업안과 부가물이 서로 다른 메시지를 말하게 된다. Tier 분리는 이 불일치를 구조적으로 차단한다.

---

## 2. 왜 자동 수업안인가

### 2.1 전통적 수업 준비의 병목

교회 교사의 수업 준비는 (1) 본문 묵상, (2) 학습목표 설정, (3) 도입·전개·적용 설계, (4) 시간배분, (5) 교보재·찬양·홍보물 제작으로 이어진다. 대부분의 교사는 비전문가이며 (5)에서 좌초한다. 결과적으로 수업안 없이 자료만 모으거나, 자료 없이 수업안만 머릿속에 둔다.

### 2.2 AI가 잘하는 것과 못하는 것의 경계

| AI가 잘하는 것 | 사람이 지켜야 하는 것 |
|---------------|---------------------|
| 본문→구조화된 수업안 초안 | 신학적 타당성 최종 판단 (휴먼 게이트) |
| 시간배분·토의질문 생성 | 대상의 실제 상황·민감성 |
| 부가물 일관 변환 | 음원/영상의 최종 제작 선택 |

이 경계가 휴먼 게이트(intake 확인, 수업안 승인)와 외부 AI 핸드오프(음원·영상은 스펙만 생성)로 구현된다.

---

## 3. 파이프라인 아키텍처

### 3.1 5단계 설계 원리

각 단계는 **독립 모듈**이다 — 하나의 `run()`과 하나의 프롬프트. 단계 N은 동결된 intake 스냅샷과(2–5의 경우) 정규 `lesson_plan.json`을 소비한다.

```
intake → [human: intake 확인]
       → ★ Step 1 lesson_plan (MAIN, 필수)
       → [human: 수업안 승인]
       → (선택) Step 2 교보재 / Step 3 찬양 / Step 4 홍보영상
       → Step 5 자기검수 (항상)
       → manifest
```

### 3.2 단계 간 의존성과 게이트

| 의존성 규칙 | 구현 |
|------------|------|
| Step 1 필수 | Step 2–4는 `lesson_plan` 없이 실행 불가 |
| intake 동결 | R3 이후 intake 스냅샷 고정 |
| 수업안 동결 | Step 1 승인 후 부가물이 동일 입력 공유 |
| 부가물 스킵 | `run_supplementary.{teaching,praise,promo}` 플래그로 제어, manifest에 `skipped` 기록 |
| 재실행 | Step 1 재실행 시 하위 부가물 버전 무효화 |

### 3.3 Human Gate의 전략적 배치

수업안 승인 게이트는 **부가물에 비용을 쓰기 전**에 위치한다. 잘못된 수업안 위에 만든 교보재·찬양·홍보영상은 전부 폐기되므로, 가장 비용이 큰 분기점 직전에 사람의 판단을 둔다. `--auto-approve`(CLI) 또는 웹앱의 무중단 실행으로 우회 가능하다.

---

## 4. 두 가지 실행 표면 (CLI · 웹앱)

이 시스템의 고유한 아키텍처 특징은 **동일한 단계 프롬프트·체이닝 로직을 공유하는 두 실행 표면**이다.

| | CLI (`scripts/orchestrator.py`) | 웹앱 (`webapp/`) |
|---|---|---|
| 런타임 | Python | 브라우저 단독 (서버 없음) |
| Claude 호출 | `anthropic` SDK (서버측) | `fetch` 직접 호출 (`anthropic-dangerous-direct-browser-access`) |
| API 키 | 환경변수 `ANTHROPIC_API_KEY` | ⚙️ → `localStorage` (코드 비내장) |
| 오프라인 | placeholder 모드 지원 | 미지원(항상 실제 호출) |
| 자기검수 | `package_check.py` | `js/selfcheck.js` (동일 PK1–PK13) |
| 대상 | 개발·CI·자동화 | 비개발자 교사 |
| 산출 | 디스크 파일(JSON/HTML/PDF/SRT) | 화면 탭 + 다운로드/복사 |

### 4.1 포팅 매핑

웹앱은 CLI의 자산을 1:1로 옮긴 것이다:

| CLI | 웹앱 |
|-----|------|
| `agents/prompts/step1…4.md` | `js/prompts.js` (PROMPTS + payload 빌더) |
| `scripts/orchestrator.py:run_pipeline` | `js/pipeline.js:runPipeline` |
| `scripts/package_check.py` | `js/selfcheck.js` |
| `*_generate.py`의 `build_downstream_payload` | `js/prompts.js:teachingDownstream/praiseDownstream` |
| `parse_minutes` | `js/prompts.js:parseMinutes` |

> 웹앱의 자기검수는 한국어 조사 교착(자유/자유는/자유를)에 강건하도록 **어간 부분매칭**을 추가했다. 이는 라이브 환경에서 헛경고를 줄이기 위한 의도적 강화다.

---

## 5. 데이터 플로우와 출력 계약

### 5.1 데이터 플로우

```
intake (body_text, theme, audience, volume)
  └─ Step 1 → lesson-plan.v1 { sections{8개}, meta.volume_minutes }
       ├─ Step 2 ← lesson_plan.key_message → teaching-materials.v1
       ├─ Step 3 ← lesson_plan.key_message (+ teaching_downstream) → praise-worship.v1
       └─ Step 4 ← lesson_plan.key_message (+ teaching/praise downstream) → promo-video.v1
  └─ Step 5 ← 위 전부 → manifest + self_check_report
```

### 5.2 출력 계약 (버전 고정)

| 계약 | 핵심 필드 | 하위 소비 |
|------|----------|----------|
| `lesson-plan.v1` | `sections.{learning_objectives, introduction, body_development, key_message, application, discussion_questions, closing, time_allocation}`, `meta.volume_minutes` | 모든 부가물의 1차 입력 |
| `teaching-materials.v1` | `summary.key_message`, `components.{intro_game,discussion,activity,worksheet}`, `slides[]` | 찬양·홍보 downstream |
| `praise-worship.v1` | `song.lyrics`, `music_generation.prompt_combined` | 홍보 downstream |
| `promo-video.v1` | `narration.full_script`, `storyboard.cuts[]`, `subtitles[]` | — |

### 5.3 SOT

CLI는 `state.yaml`을 단일 작성자(Orchestrator)로 관리하며 경로·버전·스킵 상태만 기록한다. 콘텐츠 자체는 `outputs/` 산출물 파일에 있다(구조적 SOT와 콘텐츠 분리).

---

## 6. 자기검수 아키텍처 (PK1–PK13)

### 6.1 설계 철학: 검수는 서술이 아니라 계산이다

Step 5는 LLM에게 "검토해줘"라고 묻지 않는다. 무결성은 **재현 가능**해야 하므로 결정론적 검사로 구현한다. verdict는 치명(critical) 검사 0 실패면 PASS다.

### 6.2 검사 항목

| ID | 검사 | 심각도 |
|----|------|--------|
| PK1 | 수업안(core) 존재 | critical |
| PK2 | 수업안 LP1–LP10 통과 | critical |
| PK3 | 강조점이 핵심메시지/적용에 반영 | warning |
| PK4 | 부가물은 유효한 수업안 위에서만 생성(가드) | critical |
| PK5 | 교보재가 수업안을 입력으로 소비 | warning |
| PK6 | 교보재 4종 구성요소 완비 | critical |
| PK7 | 찬양 가사/핵심메시지 존재 | critical |
| PK8 | 홍보영상 대본/핵심메시지 존재 | critical |
| PK9 | 실행/스킵 상태와 산출물 일치 | critical |
| PK10 | 부가물 핵심메시지가 수업안과 정합 | warning |
| PK11 | 대상(audience) 일관성 | warning |
| PK12 | 부가물 생성 오류 없음 | critical |
| PK13 | 부가물이 본문 구절을 참조 | warning |

> PK10/PK13은 자기검수가 "거짓 안심(false green)"을 주지 않도록 추가된 정합성 검사다 — 부가물이 수업안의 핵심메시지·본문 구절에서 실제로 파생되었는지 확인한다.

---

## 7. 품질 보장 아키텍처

### 7.1 4계층 (부모 게놈 발현)

```
L0 Anti-Skip Guard   파일 존재 + 의미 있는 크기
L1 Verification Gate  LP1–LP10 / PK1–PK13 (결정론적)
L1.5 pACS            (선택) 자기 신뢰도
L2 Review            휴먼 게이트(수업안 승인)
```

### 7.2 LP1–LP10 (수업안 검증)

8개 섹션 존재·비어있지 않음, 학습목표 ≥2, 토의질문 ≥3, 핵심메시지 비어있지 않음, 시간배분 합 = `volume_minutes`(±5), 본문전개 ≥80자, 도입·적용 ≥40자.

### 7.3 P1 할루시네이션 봉쇄

생성은 AI가, **검증은 코드가** 한다. `lesson_plan_generate.py`는 API 응답을 파싱·검증하고, 실패 시 결정론적 placeholder로 폴백한다(웹앱은 폴백 없이 오류 표면화).

---

## 8. 외부 생성 AI 핸드오프

이 시스템은 음원·영상을 직접 렌더링하지 않는다(비목표). 대신 외부 생성 AI에 넘길 **정확한 프롬프트**를 산출한다(P3 리소스 정확성):

| 부가물 | 핸드오프 산출물 | 외부 도구 |
|--------|----------------|----------|
| 찬양 | `music_generation.prompt_combined` (단일 통합 프롬프트) | Suno (custom 모드) |
| 홍보영상 | 컷별 `video_prompt` + 폴백 `image_prompt` + `subtitles`(SRT) | Runway/Pika/Kling + 이미지 AI |
| 교보재 | `[IMG: …]` 슬롯 | 이미지 생성 AI |

웹앱은 각 프롬프트에 **복사 버튼**을, CLI는 파일(`suno_prompt.txt`, `cut_NN_prompts.md`)을 제공한다. 홍보영상은 `assemble_promo_video.py`로 ffmpeg 조립(선택)도 지원한다.

---

## 9. DNA 유전 상세

| 부모 게놈 | 이 시스템의 발현 |
|----------|-----------------|
| 3단계 구조 | Research(intake) → Planning(부가물 선택·매핑) → Implementation(1–5) |
| SOT 패턴 | `state.yaml` 단일 작성자, 경로·버전만 기록 |
| 4계층 QA | L0–L2 + LP/PK 검증 |
| P1 데이터 정제 | 결정론적 검증·placeholder·자기검수 |
| P2 전문 위임 | 단계별 독립 모듈 (1 run + 1 prompt) |
| English-First (AC-4) | 내부 프롬프트·로직은 영어, 사용자 대면 산출물은 한국어 |
| Safety/Context | 부모 Hook 시스템 상속 |

---

## 10. 주요 설계 결정 (ADR)

### ADR-1: 수업안을 Core로, 부가물을 Supplementary로
수업안 단독으로 가치가 완결되어야 한다. 부가물은 선택이며 수업안 없이는 생성 불가. → 제품 위계와 하드 가드로 구현.

### ADR-2: 자기검수를 결정론적으로 (LLM 미사용)
무결성 verdict는 재현 가능해야 한다. LLM "PASS" 스텁은 거짓 안심을 준다. → `package_check.py` / `selfcheck.js`로 PK1–PK13 계산.

### ADR-3: 부가물은 본문이 아니라 수업안을 입력으로
부가물이 본문을 재해석하면 수업안과 메시지가 갈라진다. → 부가물은 `lesson_plan.key_message`를 1차 입력으로 받고, PK10/PK13이 정합을 확인.

### ADR-4: 두 실행 표면, 단일 프롬프트·로직 소스
교사용 웹앱과 개발용 CLI가 단계 프롬프트·체이닝·자기검수를 공유한다. → 웹앱은 CLI 자산의 1:1 포팅(§4.1).

### ADR-5: 브라우저 직접 호출 + 키 비내장
서버 없이 배포 가능해야 하고, 배포물에 키가 노출되면 안 된다. → `anthropic-dangerous-direct-browser-access` + 런타임 `localStorage` 키. 다중 사용자 공개 서비스에는 프록시 백엔드 권장(주의 문서화).

### ADR-6: 음원·영상은 렌더링하지 않고 프롬프트만 산출
v1 비목표로 렌더링 제외. → 외부 생성 AI(Suno/영상AI)로의 정확한 핸드오프 프롬프트 + (선택) ffmpeg 조립.

---

*문서 버전: 1.0 — 웹앱 추가 반영. 마스터 플랜: `lesson-package-generator/PLAN.md` (v0.2)*
