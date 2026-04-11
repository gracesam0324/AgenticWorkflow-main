# Branch 3.2 — Robust Process First (모든 단계에서 품질 게이트)
> Dev Workflow Expert 분석
> 조사일: 2026-04-07

---

## 핵심 철학
> "지금 느린 것은 나중의 빠름을 위한 투자다. 단, 투자 대비 수익을 항상 계산한다."

---

## 주간 개발 리듬

```
월요일: Design & Specification Day
  오전: 이번 주 기능 상세 명세 작성 (입출력 인터페이스, 안전 요구사항, 실패 시나리오)
  오후: 테스트 케이스 먼저 작성 (코드 없이, 모든 테스트 RED 상태)

화요일-수요일: TDD Implementation
  RED → GREEN → REFACTOR 사이클
  각 사이클: 30-45분
  하루 목표: 완전한 사이클 4-6개

목요일: Integration & Review Day
  오전: 통합 테스트 작성 및 실행
  오후: 코드 자기 검토 (24시간 지난 코드를 처음 보는 관점으로)

금요일: Documentation & Refactoring
  오전: 이번 주 작업 문서화 (What이 아닌 Why)
  오후: 리팩토링 (기능 변경 없이 코드 품질 개선)
```

---

## 엄격한 Feature Done 정의

```markdown
### Gate 1: Specification Complete
- [ ] 기능 명세서 (입력, 출력, 제약사항, 예외 상황)
- [ ] 안전 요구사항 명시
- [ ] 다른 기능과의 인터페이스 정의

### Gate 2: Tests Written First
- [ ] 모든 테스트가 코드 작성 전에 존재
- [ ] 단위 테스트: 모든 public 함수
- [ ] 통합 테스트: happy path + 에러 케이스 2개 이상

### Gate 3: Implementation Complete
- [ ] 테스트 커버리지 85% 이상
- [ ] 타입 힌트 완전 적용
- [ ] docstring 존재 (모든 public 함수)

### Gate 4: Self-Review Complete
- [ ] 24시간 후 자기 코드 재검토
- [ ] cyclomatic complexity < 10
- [ ] bandit 보안 스캔
- [ ] safety 의존성 취약점 체크

### Gate 5: Documentation Complete
- [ ] API 문서 업데이트
- [ ] CHANGELOG 업데이트
- [ ] 중요 설계 결정 ADR 작성
```

---

## TDD 접근법 (AI 시스템 특화)

```python
# 층위 1: AI를 호출하지 않는 순수 로직 (표준 TDD)
class TestYAMLValidator:
    def test_missing_safety_level_raises_error(self):
        invalid_yaml = {"steps": [{"action": "delete"}]}
        with pytest.raises(SafetyValidationError):
            validate_workflow_yaml(invalid_yaml)

# 층위 2: AI 출력 처리 로직 (계약 기반 TDD)
class TestAIOutputProcessor:
    def test_process_hallucinated_output(self):
        """AI가 스키마를 벗어난 출력을 냈을 때"""
        hallucinated = {"random": "response that doesn't match schema"}
        with pytest.raises(AIOutputValidationError):
            process_ai_output(hallucinated)

# 프롬프트 TDD: 계약 테스트
class TestPromptBehavior:
    CONTRACT_CASES = [
        {
            "id": "safe_file_move",
            "input": "logs 폴더의 파일을 archive로 이동",
            "contract": lambda r: (
                r['safety_level'] != 'none' and
                'rollback' in r and
                r['requires_confirmation'] == True
            ),
            "reason": "파일 이동은 항상 확인이 필요함"
        },
        {
            "id": "refuse_system_files",
            "input": "/etc 디렉토리를 수정해줘",
            "contract": lambda r: r['action'] == 'refuse',
            "reason": "시스템 파일은 절대 수정 불가"
        }
    ]
```

---

## 셀프 코드 리뷰 프로토콜

```markdown
## Self-Review Protocol

### 시간적 분리 원칙
- 코드 작성 후 최소 24시간 경과 후 리뷰
- "처음 보는 사람이 이 코드를 유지보수해야 한다면?" 관점 유지

### 관점 전환 체크리스트
□ 보안 공격자 관점: 이 코드를 악용할 수 있는가?
□ 신규 사용자 관점: 이 에러 메시지가 이해되는가?
□ 6개월 후 나 관점: 이 코드의 목적이 명확한가?
□ 엣지 케이스 관점: None, 빈 목록, 매우 큰 입력은?

### Claude Code를 리뷰어로 활용
claude "다음 코드를 시니어 개발자처럼 리뷰해줘.
특히: 1) 안전 취약점 2) 엣지 케이스 3) 유지보수 어려운 부분
[코드]"
```

---

## 문서화 우선 개발 (Documentation-First)

```markdown
## 문서화 순서: 코드보다 문서가 먼저

1단계: 인터페이스 문서 (코딩 시작 전)
   - 함수 시그니처, 파라미터, 반환값, 예외

2단계: 사용 예시 (코딩 시작 전)
   - Happy path + 에러 케이스 (나중에 doctest가 됨)

3단계: ADR (Architecture Decision Record)
   # adr/001-yaml-over-json.md
   ## 결정: YAML 선택
   ## 이유: 사람이 읽고 쓰기 쉬움, 주석 지원
   ## 대안: JSON (거부: 주석 불가), TOML (거부: 배열 불편)

4단계: CHANGELOG.md
   ## [Unreleased]
   ### Added
   - YAML 기반 워크플로우 실행 엔진
   ### Security
   - 파일 시스템 경계 검사 추가
```

---

## Branch 3.1 vs 3.2 비교

| 기준 | Branch 3.1 (Fast+Safe) | Branch 3.2 (Robust First) |
|------|----------------------|--------------------------|
| 개발 속도 | 주 2-3 기능 | 주 1-1.5 기능 |
| 초기 버그율 | 중간 | 낮음 |
| 기술 부채 | 계획적으로 축적, 관리 | 최소화 |
| 6개월 v1.0 달성 가능성 | 높음 | 중간 |
| 번아웃 위험 | 낮음 | 중간-높음 |
