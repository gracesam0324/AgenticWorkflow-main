# Promo Video Generator 사용자 매뉴얼 (홍보영상)

> 홍보영상 기획을 **단독으로** 생성하는 모듈 사용법. (수업안과 함께 쓰려면 `LESSON-PACKAGE-USER-MANUAL.md`의 웹앱을 사용하세요.)

---

## 1. 가장 쉬운 사용법

```bash
python promo-video-generator/run.py --theme "중등 수련회" --audience "중등부"
```
끝나면 `promo-video-generator/outputs/promo/` 에 스토리보드·자막·컷별 프롬프트가 생깁니다.

| 옵션 | 필수 | 설명 | 기본 |
|------|------|------|------|
| `--theme` | 예 | 테마/강조점 | — |
| `--audience` | 아니오 | 대상 | 중등부 |
| `--body` | 아니오 | 본문(선택) | "" |
| `--teaching-downstream` | 아니오 | 교보재 downstream JSON 경로 | 없음 |
| `--praise-downstream` | 아니오 | 찬양 downstream JSON 경로 | 없음 |
| `--assemble` | 아니오 | ffmpeg로 클립 조립(설치+assets 필요) | off |
| `--output-dir` | 아니오 | 출력 폴더 | `promo-video-generator/outputs` |

---

## 2. API 키 (실제 기획 생성)

기본은 **placeholder 모드**. 실제 테마 맞춤 내레이션·스토리보드는 Claude API가 필요합니다.

```powershell
$env:CONTENT_PLACEHOLDER="0"; $env:ANTHROPIC_API_KEY="sk-ant-..."
python promo-video-generator/run.py --theme "..." --audience "중등부"
```

---

## 3. 출력물

`outputs/promo/` 아래:

| 파일 | 내용 |
|------|------|
| `promo_video.v1.json` | 정규 계약(JSON) — 내레이션·스토리보드·자막 |
| `storyboard.json`, `storyboard.md` | 컷별 장면·길이·프롬프트 |
| `subtitles.srt` | 자막(편집 도구에 로드) |
| `narration_script.md` | 전체 내레이션 + 컷별 |
| `prompts/cut_XX_prompts.md` | 컷별 영상/이미지 프롬프트 |

---

## 4. 영상 핸드오프 (필수 단계)

이 모듈은 영상을 **만들지 않습니다**. 아래로 완성하세요.
1. 각 `prompts/cut_XX_prompts.md`(또는 storyboard의 `video_prompt`)를 복사
2. 영상 생성 AI(Runway/Pika/Kling 등)에 컷별로 붙여넣어 클립 생성
   - 영상 AI가 어려우면 `image_prompt`로 정지컷 → 슬라이드쇼 대체
3. 클립을 순서대로 편집, `subtitles.srt`로 자막 입히기
4. (선택) **ffmpeg 자동 조립**: `assets/cut_XX.mp4`(또는 .png) 배치 후
   ```bash
   python promo-video-generator/run.py --theme "..." --assemble
   # 또는 라이브러리: from promo_video_generator import assemble; assemble(promo_dir, music_path=...)
   ```
   배경음으로 찬양 모듈의 `song.mp3`를 `music_path`로 넣을 수 있습니다.
5. 내레이션은 전체 스크립트를 TTS 또는 직접 녹음

---

## 5. 교보재/찬양/수업안과 함께 쓰기 (선택)

- 교보재·찬양 downstream을 주면(`--teaching-downstream`/`--praise-downstream` 또는 라이브러리 `prior`) 메시지·톤이 정합됩니다.
- 수업안(`lesson_plan`)을 주면 핵심메시지·학습목표가 CTA/훅에 반영됩니다.
- lesson-package-generator 오케스트레이터(웹앱 포함)는 교보재·찬양 downstream을 자동으로 넘깁니다.

---

## 6. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `ModuleNotFoundError: content_common` | 저장소 루트 `content-common/` 확인. `run.py`가 경로 자동 설정 |
| `--assemble` 시 실패 | ffmpeg 미설치 또는 `assets/cut_XX.*` 미배치. ffmpeg 설치 후 에셋 준비 |
| 기획이 테마와 동떨어짐 | placeholder 모드입니다. API 키 설정(§2) 후 재실행 |
| 길이가 30–45초 밖 | 검증(P1)에서 경고 — API 모드에서 재생성 |

---

## 부록: 관련 문서
- [`PROMO-VIDEO-README.md`](PROMO-VIDEO-README.md) · [`PROMO-VIDEO-ARCHITECTURE-AND-PHILOSOPHY.md`](PROMO-VIDEO-ARCHITECTURE-AND-PHILOSOPHY.md)
- [`promo-video-generator/workflow.md`](promo-video-generator/workflow.md) · [`promo-video-generator/PLAN.md`](promo-video-generator/PLAN.md)
