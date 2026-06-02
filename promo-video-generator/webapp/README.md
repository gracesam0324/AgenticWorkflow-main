# 홍보영상 생성기 — 웹앱 (promo-video-generator/webapp)

브라우저 단독 단일 페이지 웹앱. 서버 없이 **브라우저에서 Claude API를 직접 호출**해 30–45초 수련회 홍보영상 기획(`promo-video.v1`)을 생성합니다.

## 사용법
1. `promo-video-generator/webapp/index.html`을 브라우저로 엽니다(또는 GitHub Pages URL).
2. ⚙️ → Anthropic API 키 입력·저장(이 브라우저 localStorage에만 저장).
3. 테마·대상(·본문 선택) 입력 → **✨ 생성하기**.
4. 내레이션·스토리보드 확인 → **⬇ JSON / ⬇ 자막 SRT**, 컷별 **영상/이미지 프롬프트 📋 복사** → Runway/Pika/Kling·이미지 AI로 핸드오프.

## 구조
```
webapp/
├── index.html · manifest.webmanifest
├── css/styles.css
└── js/  prompt.js(홍보 프롬프트) · api.js(키 localStorage) · render.js(스토리보드/자막) · app.js
```

## 메모
- API 키는 코드에 없습니다(런타임 ⚙️). 같은 origin의 다른 앱과 키 공유(`lpg.apiKey`).
- 영상·음원은 만들지 않습니다(프롬프트·SRT 핸드오프). ffmpeg 조립은 모듈 CLI(`run.py --assemble`) 참고.
