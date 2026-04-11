# Branch 3.1 — Fast with Safety Rails (빠르게, 통제된 방식으로)
> Dev Workflow Expert 분석
> 조사일: 2026-04-07

---

## 핵심 철학
> "완벽한 코드보다 동작하는 코드가 먼저다. 단, 안전 장치는 절대 타협하지 않는다."

---

## 주간 개발 리듬

```
[매일]
09:00-09:30  Day Kickoff (어제 Git 상태 + Critical path smoke test)
09:30-12:30  Deep Work (핵심 기능 개발, Feature Flag로 격리)
13:30-15:30  Integration (통합 + 안전 테스트)
15:30-17:00  Hardening (엣지 케이스 처리 - 새 기능 금지)
17:00-17:30  Day Wrap (커밋 + 내일 계획)

[주간]
월요일: Sprint Planning + 위험 요소 식별
화-목:  Core Development (하루 1 Feature 목표)
금요일: Hardening Day (새 기능 절대 금지, 통합 테스트 + 부채 정리)
```

---

## Feature "완료(Done)" 정의

```yaml
level_1_non_negotiable:  # 이것 없으면 절대 배포 불가
  - Safety boundary test 통과 (파일 시스템 접근 범위 검증)
  - 입력값 검증 (악의적/실수 입력 방어)
  - 에러 발생 시 롤백 메커니즘 존재
  - Critical path unit test 최소 1개
  - 로컬 실행 확인

level_2_strongly_recommended:  # 빠진 경우 기술 부채로 등록
  - Happy path integration test
  - 에러 메시지 명확성
  - YAML 스키마 검증
  - 로그 출력 적절성

level_3_nice_to_have:  # v1.0 이후 가능
  - 성능 최적화
  - 100% 커버리지
  - 상세 API 문서
```

---

## Git 워크플로우: Session-Based Branching

```
main
  └── develop (항상 동작 보장)
        ├── feat/yaml-parser-v2
        ├── feat/safety-sandbox
        ├── fix/file-permission-edge-case
        └── session/2026-04-07-file-ops  (Claude 에이전트 세션 브랜치)
```

### 커밋 컨벤션

```bash
# 타입 접두사
feat:     새 기능
fix:      버그 수정
safe:     안전 관련 코드 변경 [SAFETY-CRITICAL]
prompt:   프롬프트 변경 [PROMPT-CHANGE]
test:     테스트 추가/수정
refactor: 기능 변경 없는 코드 개선

# 일일 루틴
git add -p           # 절대 git add . 금지, 변경사항 하나씩 확인
git commit -m "wip: [현재 작업 상태]"   # 30-60분마다 micro-commit
git push origin develop                  # 하루 마감 시 백업
```

---

## 테스트 전략: "Critical Path Only"

```python
# 테스트 우선순위 매트릭스
"""
              위험도 높음          위험도 낮음
복잡도 높음  [MUST TEST NOW]    [테스트 후 배포]
복잡도 낮음  [MUST TEST NOW]    [나중에 테스트]
"""

# MUST TEST NOW:
# 1. 파일 시스템 작업 (삭제, 덮어쓰기)
# 2. YAML 파싱 → 명령 실행 변환
# 3. 안전 경계 검사 로직
# 4. 롤백 메커니즘
# 5. 외부 프로세스 실행 (subprocess)

# 테스트 구조
tests/
  critical/           # 항상 통과해야 하는 테스트 (CI 항상 실행)
    test_safety.py
    test_yaml_parse.py
    test_rollback.py
  smoke/              # 매일 아침 30초 이내
    test_startup.py
  integration/        # 주 1회
    test_full_workflow.py
```

### AI 비결정성 대응 테스트 패턴

```python
class TestYAMLGeneration:
    def test_yaml_has_required_fields(self):
        """내용이 아닌 구조를 테스트 (비결정성 대응)"""
        result = generate_yaml_plan("파일을 복사해줘")
        
        # 내용 검증 (X) - flaky test 양산
        # 구조 검증 (O) - 항상 동일해야 하는 것만
        assert 'steps' in result
        assert 'safety_level' in result
        for step in result['steps']:
            assert 'rollback' in step  # 모든 스텝에 롤백 필수

class TestPromptRegression:
    GOLDEN_CASES = [
        {
            "input": ".log 파일들을 archive 폴더로 이동",
            "expected_action_type": "file_move",
            "expected_safety_check": True,
            "must_not_contain": ["delete", "rm -rf"]
        }
    ]
    
    def test_prompt_golden_cases(self):
        for case in self.GOLDEN_CASES:
            result = process_natural_language(case['input'])
            assert result['action_type'] == case['expected_action_type']
            for forbidden in case['must_not_contain']:
                assert forbidden not in str(result).lower()
```

---

## Claude Code를 개발 가속에 활용

```bash
# 반복적 테스트 작성 자동화
claude "이 함수에 대한 pytest 테스트 작성해줘. 
파일 시스템 경계 검사와 롤백 메커니즘에 집중해줘: [코드]"

# 코드 리뷰 자동화
claude "이 변경사항 검토해줘. 안전 취약점, 엣지 케이스 찾아줘:
$(git diff develop..HEAD)"

# 에러 디버깅
claude "이 스택트레이스 분석해줘. 원인과 수정 방법 알려줘: [에러]"
```

---

## CI/CD 파이프라인

```yaml
# .github/workflows/safety_first.yml
jobs:
  critical_safety_tests:
    name: "🔴 Critical Safety (MUST PASS)"
    timeout-minutes: 5
    steps:
      - run: pytest tests/critical/ -v

  smoke_tests:
    needs: critical_safety_tests
    timeout-minutes: 2
    steps:
      - run: pytest tests/smoke/ -v

  integration_tests:
    needs: smoke_tests
    if: github.ref == 'refs/heads/main'  # main에서만
    timeout-minutes: 15
    steps:
      - run: pytest tests/integration/ -v

  prompt_regression:
    needs: critical_safety_tests
    if: contains(github.event.commits[0].modified, 'prompts/')
    steps:
      - run: python scripts/run_prompt_regression.py
```

---

## 추적 메트릭

```python
weekly_metrics = {
    "velocity": {
        "features_completed": 0,  # 목표: 주 2-3개
        "commit_count": 0,        # 목표: 하루 5-10개
    },
    "quality": {
        "critical_test_coverage": 0,  # 목표: 90%+
        "total_test_coverage": 0,     # 목표: 60%+ (현실적)
        "safety_bugs": 0,             # 반드시 0
    },
    "ai_specific": {
        "prompt_changes": 0,
        "schema_violations_caught": 0,
        "non_determinism_incidents": 0,
    }
}
```
