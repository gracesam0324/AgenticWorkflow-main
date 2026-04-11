# Anti-Homogenization Constraint Sheet (AHCS) — V2 Revision

> Each chapter must follow its assigned structural pattern. No two chapters may share the same opening+closing combination.

## Per-Chapter Constraints

| Ch | Title | 오프닝 유형 | 클로징 유형 | 질감 (texture) | 울음 상한 | 특수 제약 |
|----|-------|-----------|-----------|---------------|---------|---------|
| 01 | 나뭇결 위의 지도 | 감각/이미지 (나무 마루 천장) | 감각 에코 (감나무 마지막) | deep_scene | 0 | 울음 금지. 옆집 에피소드에서 "울었다" → 신체 묘사로 대체 |
| 02 | 별 아래의 목소리 | 대화 (김 선생님의 질문) | 미해결 질문 (소명의 의미) | dialogue_heavy | 1 | 사춘기 정체성 탐색 중심 |
| 03 | 부르심의 언어 | In medias res (수련회 캠프파이어) | 시간 점프 (군 입대) | deep_scene | 1 (수련회 정본) | 군 생활 확장 필요 |
| 04 | 307호 실험실 | 시간 표지 ("1989년 3월") | 전진 다리 (불안의 시작) | montage | 0 | 80년대 캠퍼스 역사 맥락 |
| 05 | 닫힌 문 | 장면 설정 (새벽 교회 마당) | 조용한 행동 (버스 탑승) | deep_scene | 1 | "7년"→"6년" 수정. 숙희 대화 확장 |
| 06 | 역풍 속의 신앙 | 성찰적 (IMF 위기 체감) | 대화 클로징 (숙희와의 대화) | transitional | 0 | IMF 체감 확장 필요 |
| 07 | 사람을 세우는 리더십 | 대화 (세 사람의 추천) | 이미지 정지 (차 안 라디오 찬송가) | dialogue_heavy | 0 | 숙희 거친 손 1회로. 시계 소리 제거 |
| 08 | 겨울 햇살 | In medias res (쓰러짐) | 감각 에코 (겨울 햇살→봄 햇살) | deep_scene | 1 (정본 — ICU) | "61년"→"45년" 수정. 심장마비 정본 대폭 확장 (목표 10K) |
| 09 | 하나님은 사람의 얼굴을 하고 오신다 | 질문/수사 ("왜 이 사람들은...") | 순환 귀환 (첫 질문으로 돌아옴) | contemplative | 0 | 목록형 회고 → 이장로님 다방 장면 + 박선배 첫날 장면 대화 중심 극화 |
| 10 | 새벽 문소리 | 장면 설정 (은행나무 길) | 침묵 (서랍 닫는 소리) | montage | 1 | 아들 고백 정본. 선호 멘토링 정본. 노트 정리 정본 |
| 11 | 열린 길 | 직접 호명 ("2020년 3월, 세상이 멈췄다" → 현재시제) | 조용한 행동 (마지막 출근일 상자) | contemplative | 0 | COVID 현재시제 일지. 회고 금지. 안경 청년/세 마디/챕터 목록 제거 |
| 12 | 나뭇결 안의 설계도 | 성찰적/경치적 (서재 새벽) | 감각 에코 (나뭇결 폐합) | deep_scene | 0 | 3악장 구조: (1)수련회 청년 정본 → (2)서재 새벽 → (3)나뭇결 폐합. 목록/에세이 전면 삭제 |

## Global Caps

| 제약 | 상한 | 검증 방법 |
|------|------|---------|
| "돌이켜보면" | 전체 3회 이하 | `grep -c "돌이켜" ch*_v2.md` |
| 시계 소리 (째깍/시계) | 3챕터 이하 | `grep -l "째깍\|시계.*소리\|초침" ch*_v2.md` |
| 숙희 거친 손 | 3챕터 이하 (Ch.05, Ch.08 + 최대 1곳) | `grep -l "거친.*손\|거칠어진.*손" ch*_v2.md` |
| 울음 클라이맥스 | 합계 5회 이하 | 위 표의 울음 상한 합계 |
| "그때는 몰랐지만" | 챕터당 최대 2회, 전체 8회 이하 | `grep -c "그때는 몰랐" ch*_v2.md` |
| 현관문 소리 언급 | 4챕터 이하 (Ch.01, Ch.10, Ch.12 + 최대 1곳) | `grep -l "현관문.*소리" ch*_v2.md` |

## Texture Distribution Rules

- No 2 consecutive chapters may share the same primary texture
- At least 3 of 5 texture types must appear across the full manuscript
- Current distribution: deep_scene(5), dialogue_heavy(2), montage(2), contemplative(2), transitional(1) ✓

## Opening/Closing Uniqueness

Every chapter's (opening type, closing type) pair must be unique. No two chapters share both.

## Circular Closure (원환 폐합)

- Ch.01 opening: 나무 마루 천장 나뭇결 → 상상의 지도
- Ch.12 closing: 나뭇결 안의 설계도 → 상상이 아니라 실재
- Mirror element: 나뭇결 이미지의 의미 전환 (상상 → 실재)
