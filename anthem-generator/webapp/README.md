# 찬양 생성기 — 웹앱 (anthem-generator/webapp)

브라우저 단독 단일 페이지 웹앱. 서버 없이 **브라우저에서 Claude API를 직접 호출**해 오리지널 찬양(`praise-worship.v1`)과 Suno 음악 프롬프트를 생성합니다.

## 사용법
1. `anthem-generator/webapp/index.html`을 브라우저로 엽니다(또는 GitHub Pages URL).
2. ⚙️ → Anthropic API 키 입력·저장(이 브라우저 localStorage에만 저장).
3. 본문·테마·대상 입력 → **✨ 생성하기**.
4. 가사 확인 → **⬇ JSON / ⬇ 가사 MD**, **Suno 프롬프트 📋 복사** → suno.com 커스텀 모드에 붙여넣어 음원 생성.

## 구조
```
webapp/
├── index.html · manifest.webmanifest
├── css/styles.css
└── js/  prompt.js(찬양 프롬프트) · api.js(키 localStorage) · render.js(가사/Suno) · app.js
```

## 메모
- API 키는 코드에 없습니다(런타임 ⚙️). 같은 origin의 다른 앱과 키 공유(`lpg.apiKey`).
- 음원은 만들지 않습니다(Suno 핸드오프). 가사는 오리지널 — CCLI 등 권리 확인 후 배포.
