# Anthem Generator 사용자 매뉴얼 (찬양)

> 찬양을 **단독으로** 생성하는 모듈 사용법. (수업안과 함께 쓰려면 `LESSON-PACKAGE-USER-MANUAL.md`의 웹앱을 사용하세요.)

---

## 1. 가장 쉬운 사용법

```bash
python anthem-generator/run.py \
  --body "요한복음 3:16" \
  --theme "하나님의 사랑" \
  --audience "중등부"
```
끝나면 `anthem-generator/outputs/praise/` 에 가사와 Suno 프롬프트가 생깁니다.

| 옵션 | 필수 | 설명 | 기본 |
|------|------|------|------|
| `--body` | 예 | 본문(성경 구절/요약) | — |
| `--theme` | 예 | 테마/강조점 | — |
| `--audience` | 아니오 | 대상 | 중등부 |
| `--teaching-downstream` | 아니오 | 교보재 downstream JSON 경로(정합 강화) | 없음 |
| `--output-dir` | 아니오 | 출력 폴더 | `anthem-generator/outputs` |

---

## 2. API 키 (실제 가사 생성)

기본은 **placeholder 모드**(구조 데모용 결정론적 가사). 실제 본문/테마 맞춤 가사는 Claude API가 필요합니다.

```powershell
$env:CONTENT_PLACEHOLDER="0"; $env:ANTHROPIC_API_KEY="sk-ant-..."
python anthem-generator/run.py --body "..." --theme "..." --audience "중등부"
```

---

## 3. 출력물

`outputs/praise/` 아래:

| 파일 | 내용 |
|------|------|
| `praise_worship.v1.json` | 정규 계약(JSON) — 가사·음악 프롬프트·인도자 노트 |
| `lyrics/full_lyrics.md` | 전체 가사 (Suno 가사 칸에 붙여넣기) |
| `music/suno_prompt.txt` | Suno 스타일 프롬프트 (한 줄 통합) |
| `music/music_prompt.json` | 구조화 프롬프트(genre·mood·bpm·instruments) |
| `leader_notes.md` | 인도 시점·조성·템포·팁 |
| `audio/README.txt` | 생성한 음원을 `song.mp3`로 둘 위치 안내 |
| `praise_worship.downstream.json` | 홍보영상이 소비할 요약(suno_prompt·song_title·key_message) |

---

## 4. Suno 음원 핸드오프 (필수 단계)

이 모듈은 음원을 **만들지 않습니다**. 아래로 완성하세요.
1. `music/suno_prompt.txt` 내용을 복사
2. https://suno.com → **Custom 모드**
3. 가사 칸: `lyrics/full_lyrics.md` 붙여넣기 / 스타일 칸: 복사한 프롬프트 붙여넣기
4. 생성 → 마음에 드는 음원 다운로드
5. (선택) `outputs/praise/audio/song.mp3`로 저장 — 홍보영상 조립 시 배경음으로 사용 가능

> 가사는 오리지널 창작물입니다. 공연·녹음 공개 전 CCLI 등 권리 확인이 필요합니다.

---

## 5. 교보재/수업안과 함께 쓰기 (선택)

- 교보재 downstream을 주면(`--teaching-downstream` 또는 라이브러리 `prior`) 핵심메시지·토의 흐름과 정합됩니다.
- 수업안(`lesson_plan`)을 주면 수업안 핵심메시지가 가사 메시지에 반영됩니다.
- lesson-package-generator 오케스트레이터(웹앱 포함)는 교보재 downstream을 자동으로 넘깁니다.

---

## 6. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `ModuleNotFoundError: content_common` | 저장소 루트 `content-common/` 확인. `run.py`가 경로 자동 설정 |
| 가사가 본문과 동떨어짐 | placeholder 모드입니다. API 키 설정(§2) 후 재실행 |
| Suno 결과가 밋밋함 | `music_prompt.json`의 mood/bpm/style_tags를 Suno에서 보정 |

---

## 부록: 관련 문서
- [`ANTHEM-README.md`](ANTHEM-README.md) · [`ANTHEM-ARCHITECTURE-AND-PHILOSOPHY.md`](ANTHEM-ARCHITECTURE-AND-PHILOSOPHY.md)
- [`anthem-generator/workflow.md`](anthem-generator/workflow.md) · [`anthem-generator/PLAN.md`](anthem-generator/PLAN.md)
