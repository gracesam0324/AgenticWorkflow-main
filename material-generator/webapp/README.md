# 교보재 생성기 — 웹앱 (material-generator/webapp)

브라우저 단독으로 동작하는 단일 페이지 웹앱. 서버 없이 **브라우저에서 Claude API를 직접 호출**해 교보재(`teaching-materials.v1`)를 생성합니다. lesson-package 웹앱과 동일한 방식.

## 사용법
1. `material-generator/webapp/index.html`을 브라우저로 엽니다(또는 GitHub Pages 배포 URL).
2. ⚙️ → Anthropic API 키 입력·저장. 키는 **이 브라우저(localStorage)에만** 저장되며 서버로 전송되지 않습니다.
3. 본문·테마·대상(·분량) 입력 → **✨ 생성하기**.
4. 결과 확인 → **⬇ JSON / ⬇ MD** 다운로드, 이미지 프롬프트 **📋 복사**.

## 구조
```
webapp/
├── index.html · manifest.webmanifest
├── css/styles.css         (lesson-package 웹앱과 동일 디자인 토큰)
└── js/
    ├── prompt.js          교보재 시스템 프롬프트 + payload (agents/prompts/material.md 포팅)
    ├── api.js             Claude 브라우저 직접 호출 + 키(localStorage, lpg.* 공유)
    ├── render.js          teaching-materials.v1 렌더 + 다운로드 + 이미지 프롬프트 복사
    └── app.js             UI 연결
```

## 메모
- API 키는 코드에 없습니다(런타임 ⚙️ 입력). 같은 origin의 다른 모듈/lesson-package 웹앱과 키를 공유합니다(`lpg.apiKey`).
- 모델: ⚙️에서 Sonnet 4.6(기본)/Opus 4.8/Haiku 4.5 선택.
- 이미지 프롬프트(`[IMG: …]`)는 이미지 생성 AI로 핸드오프(이 앱은 이미지를 만들지 않음).
- 브라우저 직접 호출은 키가 사용자 브라우저에 노출되므로 공용 PC 주의.
