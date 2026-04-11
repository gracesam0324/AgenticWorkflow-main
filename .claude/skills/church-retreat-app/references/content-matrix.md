# Content Matrix — Church Retreat App

> App type → required content fields table, collection strategy, and validation rules.
> Used by `@conversation-guide` in Phase 1 and `validate_content_collection.py` at Phase 1→2 gate.

---

## Content Matrix (App Type → Required Fields)

| # | App Type | Required Fields | Optional Fields |
|---|----------|----------------|-----------------|
| 1 | 성경 퀴즈 | `team_count`, `team_names`, `quiz_questions[]`, `design_palette` | `team_colors`, `time_limit`, `difficulty_labels` |
| 2 | 스탬프 랠리 | `missions[]` (name + location + QR data), `design_palette` | `reward_description`, `completion_threshold` |
| 3 | 일정표 & 공지 | `schedule[]` (time + title + description), `design_palette` | `notices[]`, `location_map`, `emergency_contact` |
| 4 | 찬양 가사 | `lyrics[]` (song_title + lyrics_text), `design_palette` | `song_order`, `chord_info`, `youtube_key` |
| 5 | QT 가이드 | `bible_passages[]` (reference + text + questions), `design_palette` | `daily_theme`, `prayer_topics` |
| 6 | 팀 점수판 | `team_count`, `team_names`, `team_colors`, `design_palette` | `score_categories`, `initial_scores` |
| 7 | 사진 갤러리 | `gallery_title`, `design_palette` | `upload_password`, `categories` |
| 8 | 기도제목 | `prayer_categories[]`, `design_palette` | `anonymous_option`, `sharing_rules` |
| 9 | 종합 앱 | `features[]` (selected from 1-8), `design_palette` | Per-feature fields from selected types |

---

## Field Definitions

### Common Fields (All App Types)

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `design_palette` | enum: A\|B\|C\|custom | Must be one of A/B/C or custom hex values | Show 3 visual previews, ask to choose |
| `church_name` | string | Non-empty, ≤ 50 chars | "교회 이름을 알려주세요" |
| `retreat_name` | string | Non-empty, ≤ 100 chars | "수련회 이름이 있나요?" (optional) |
| `admin_password` | string | Non-empty, ≥ 4 chars | Auto-generate, show to 사역자 |

### Team Configuration

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `team_count` | integer | 2 ≤ n ≤ 10 | "팀이 몇 개인가요?" |
| `team_names` | string[] | length == team_count, each non-empty | "팀 이름을 알려주세요 (예: 사랑, 믿음, 소망)" |
| `team_colors` | string[] | length == team_count, valid hex | Auto-assign from palette, allow override |

### Quiz Content

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `quiz_questions` | object[] | length ≥ 5, each has question + answer + options | "퀴즈 문제를 알려주세요. 문제, 정답, 보기를 포함해 주세요." |
| `quiz_questions[].question` | string | Non-empty | Within quiz_questions |
| `quiz_questions[].answer` | string | Non-empty, must match one option | Within quiz_questions |
| `quiz_questions[].options` | string[] | length ≥ 2 | Within quiz_questions |
| `time_limit` | integer | 5 ≤ n ≤ 60 (seconds) | Default: 15, "시간 제한을 바꿀까요?" |

### Schedule Content

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `schedule` | object[] | length ≥ 1 | "수련회 일정을 알려주세요" |
| `schedule[].time` | string | Non-empty (e.g., "09:00") | Within schedule |
| `schedule[].title` | string | Non-empty | Within schedule |
| `schedule[].description` | string | Optional | Within schedule |
| `schedule[].day` | integer | Optional (multi-day support) | "몇 박 며칠인가요?" |

### Lyrics Content

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `lyrics` | object[] | length ≥ 1 | "찬양 가사를 알려주세요. 파일로 보내셔도 돼요" |
| `lyrics[].song_title` | string | Non-empty | Within lyrics |
| `lyrics[].lyrics_text` | string | Non-empty, contains Korean | Within lyrics |
| `lyrics[].sections` | object[] | Optional (verse/chorus structure) | Auto-detect from text |

### Mission Content (Stamp Rally)

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `missions` | object[] | length ≥ 3 | "스탬프 미션을 알려주세요" |
| `missions[].name` | string | Non-empty | Within missions |
| `missions[].location` | string | Optional | "장소 정보도 있나요?" |
| `missions[].description` | string | Optional | Within missions |

### Bible Passage Content (QT)

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `bible_passages` | object[] | length ≥ 1 | "QT 말씀을 알려주세요" |
| `bible_passages[].reference` | string | Non-empty (e.g., "요한복음 3:16") | Within passages |
| `bible_passages[].text` | string | Non-empty | Within passages |
| `bible_passages[].questions` | string[] | length ≥ 1 | "묵상 질문도 있나요?" |

### Combined App Features

| Field | Type | Validation | Collection Strategy |
|-------|------|-----------|-------------------|
| `features` | string[] | length ≥ 2, each in [quiz, score, schedule, lyrics, qt, stamps, gallery, prayer] | "어떤 기능들을 넣을까요?" |

---

## Collection Strategy by Input Method

### Direct Conversation (Default)
```
사역자: "퀴즈 10문제 만들어줘"
Guide: "퀴즈 문제를 알려주세요! 이런 형식이면 좋아요:
       1. 문제: 노아의 방주에 몇 쌍의 동물이 탔나요?
          정답: 한 쌍씩
          보기: 한 쌍씩 / 두 쌍씩 / 세 쌍씩"
```

### File Upload
```
사역자: (파일 첨부 — .txt, .xlsx, .docx)
Guide: "파일을 잘 받았어요! 내용을 확인하고 정리할게요."
→ Parse file → extract structured data → confirm with 사역자
```

### Minimal Input (P4 — 최대 4개 질문)
```
Guide: "퀴즈 앱이군요! 몇 가지만 여쭤볼게요.
       1. 팀은 몇 개인가요? (2~10개)
       2. 팀 이름은요? (예: 사랑, 믿음, 소망)
       3. 퀴즈 문제는 파일로 주시겠어요, 직접 알려주시겠어요?
       4. 색상은 어떤 느낌이 좋으세요? (차분한 / 활기찬 / 따뜻한)"
```

---

## Validation Rules

### Pre-Phase 2 Gate (`validate_content_collection.py`)

```python
CONTENT_MATRIX = {
    "quiz": {
        "required": ["team_count", "team_names", "quiz_questions", "design_palette"],
        "validators": {
            "team_count": lambda v: isinstance(v, int) and 2 <= v <= 10,
            "team_names": lambda v: isinstance(v, list) and len(v) > 0 and all(v),
            "quiz_questions": lambda v: isinstance(v, list) and len(v) >= 5,
            "design_palette": lambda v: v in ("A", "B", "C") or (isinstance(v, dict)),
        }
    },
    "score": {
        "required": ["team_count", "team_names", "team_colors", "design_palette"],
        "validators": {
            "team_count": lambda v: isinstance(v, int) and 2 <= v <= 10,
            "team_names": lambda v: isinstance(v, list) and len(v) > 0,
            "team_colors": lambda v: isinstance(v, list) and len(v) > 0,
            "design_palette": lambda v: v in ("A", "B", "C") or isinstance(v, dict),
        }
    },
    "schedule": {
        "required": ["schedule", "design_palette"],
        "validators": {
            "schedule": lambda v: isinstance(v, list) and len(v) > 0,
            "design_palette": lambda v: v in ("A", "B", "C") or isinstance(v, dict),
        }
    },
    "lyrics": {
        "required": ["lyrics", "design_palette"],
        "validators": {
            "lyrics": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "stamps": {
        "required": ["missions", "design_palette"],
        "validators": {
            "missions": lambda v: isinstance(v, list) and len(v) >= 3,
        }
    },
    "qt": {
        "required": ["bible_passages", "design_palette"],
        "validators": {
            "bible_passages": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "combined": {
        "required": ["features", "design_palette"],
        "validators": {
            "features": lambda v: isinstance(v, list) and len(v) >= 2,
        }
        # Plus each selected feature's own requirements
    }
}
```

### Content Accuracy Check (`validate_content_insertion.py`)

After code generation, verify that SOT content appears verbatim in HTML:
- Quiz: Each question text in HTML DOM elements
- Schedule: Each schedule item in HTML
- Lyrics: Each song title in HTML
- Match rate must be ≥ 95% for PASS

### Data Sanitization Rules

| Rule | Check | Action |
|------|-------|--------|
| No personal info | Scan for phone/email patterns | Warn 사역자, suggest removal |
| No profanity | (Korean profanity word list) | Auto-remove, notify |
| Max content size | Total < 50KB | Suggest condensing |
| Korean text valid | No `\uFFFD` (replacement chars) | Re-encode or re-collect |
| HTML entities escaped | No raw `<script>`, `<iframe>` | Auto-escape |
