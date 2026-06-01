# 수업안 패키지 생성기 — 웹앱 (webapp)

브라우저 단독으로 동작하는 단일 페이지 웹앱입니다. 서버가 없으며, **브라우저에서 Anthropic Claude API를 직접 호출**합니다. `lesson-package-generator`의 5단계 파이프라인(수업안 → 교보재 → 찬양 → 홍보영상 → 자기검수)을 그대로 옮겼습니다.

## 사용법

1. `webapp/index.html`을 브라우저로 엽니다 (로컬 더블클릭 또는 GitHub Pages 배포).
2. 우측 상단 **⚙️** → Anthropic API 키 입력 후 저장. 키는 **이 브라우저의 localStorage에만** 저장되며 어떤 서버로도 전송되지 않습니다. (키 발급: console.anthropic.com → Settings → API Keys)
3. 본문 · 테마 · 대상 · 분량을 입력하고 부가물(교보재·찬양·홍보영상)을 선택합니다.
4. **✨ 생성하기** → 단계별 진행이 표시되고, 완료되면 결과가 탭으로 나타납니다.
5. 각 탭에서 **다운로드**(JSON / MD / SRT)와 **프롬프트 복사**(Suno 음악, 이미지/영상 생성 AI)를 사용합니다.

## 결과물

| 탭 | 내용 | 내보내기 |
|----|------|----------|
| 수업안 | 학습목표·도입·본문전개·핵심메시지·적용·토의질문·마무리·시간배분 | JSON, Markdown |
| 교보재 | 도입게임·토의·활동·워크시트·슬라이드 + 이미지 프롬프트 | JSON, 프롬프트 복사 |
| 찬양 | 오리지널 가사 + Suno 음악 프롬프트 | JSON, 가사 MD, 프롬프트 복사 |
| 홍보영상 | 내레이션·스토리보드·컷별 영상/이미지 프롬프트·자막 | JSON, SRT, 프롬프트 복사 |
| 자기검수 | PK1–PK13 결정론적 무결성 검사 (브라우저에서 계산) | — |

## 구조

```
webapp/
├── index.html              단일 페이지
├── manifest.webmanifest    PWA 매니페스트
├── css/styles.css          디자인 시스템 (church-retreat-app 컨벤션)
└── js/
    ├── prompts.js          5단계 시스템 프롬프트 + payload (agents/prompts/* 포팅)
    ├── api.js              Claude 브라우저 직접 호출 + 키(localStorage)
    ├── selfcheck.js        PK1–PK13 (scripts/package_check.py 포팅)
    ├── pipeline.js         단계 체이닝 (scripts/orchestrator.py 포팅)
    ├── render.js           결과 렌더 + 다운로드/복사
    └── app.js              UI 연결 (설정·진행·탭)
```

## 동작 원리

- **API 키 비내장**: 코드에 키가 없습니다. 실행 중 ⚙️로 입력 → `localStorage`. 배포해도 키가 노출되지 않습니다.
- **브라우저 직접 호출**: `anthropic-dangerous-direct-browser-access: true` 헤더로 CORS 허용. 별도 백엔드가 필요 없습니다.
- **체이닝**: 수업안(`lesson-plan.v1`)을 먼저 생성하고, 교보재·찬양·홍보영상이 그 `key_message`를 입력으로 받습니다 (CLI 오케스트레이터와 동일).
- **자기검수**: LLM 없이 JS에서 PK1–PK13을 결정론적으로 계산합니다.

## 모델

⚙️에서 선택: Sonnet 4.6(기본·권장), Opus 4.8(최고 품질), Haiku 4.5(경량).

## 배포 (GitHub Pages)

`webapp/`를 정적 호스팅하면 됩니다. 예: 저장소 Settings → Pages → 소스 디렉터리 지정, 또는 `webapp/` 내용을 Pages 브랜치로 푸시.

## 주의

- 브라우저 직접 호출은 API 키가 사용자 브라우저에 노출됩니다(공용 PC 사용 주의). 다중 사용자/공개 서비스에는 별도 프록시 백엔드 권장.
- 콘텐츠 품질은 선택한 모델과 입력(본문·테마)의 구체성에 비례합니다.
