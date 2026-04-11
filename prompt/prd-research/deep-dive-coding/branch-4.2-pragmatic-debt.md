# Branch 4.2: 실용적 부채 관리 (Move Fast, Refactor Later)
> Technical Debt Manager — 기술 부채 분석
> 조사일: 2026-04-07

## 핵심 철학
> "동작하는 코드가 완벽한 코드보다 낫다. 단, 부채는 명시적으로 기록한다."

이 전략의 핵심은 **부채를 "모르는 상태"가 아닌 "알면서 감수하는 상태"** 로 유지하는 것이다.

---

## 부채 레지스터 (Debt Register) 시스템

```yaml
# TECHNICAL_DEBT_REGISTER.yaml

debts:
  - id: TD-001
    category: architecture
    title: "WorkflowRunner 단일 클래스에 모든 로직 집중"
    severity: medium
    created: 2024-01-10
    context: "MVP 속도를 위해 계층 분리 생략"
    impact: |
      - 새 실행기 타입 추가 시 전체 클래스 수정 필요
      - 단위 테스트 격리 어려움
    trigger: "실행기 타입이 2가지 이상 필요해질 때"
    estimated_effort: "3일"
    
  - id: TD-002
    category: testing
    title: "통합 테스트 부재 - 수동 테스트로 대체"
    severity: high
    deadline: "2024-03-01"  # 하드 데드라인 설정
    
  - id: TD-003
    category: security
    title: "YAML 인젝션 검증 미흡 - 기본 패턴만 차단"
    severity: critical  # ← 즉시 처리 예약 필요
    deadline: "2024-02-03"  # CRITICAL은 반드시 데드라인
```

**부채 심각도 분류:**
- `CRITICAL` → 즉시 처리 (2주 내)
- `HIGH` → 다음 마일스톤 내 해결
- `MEDIUM` → 분기별 리팩터링 스프린트
- `LOW` → v2.0 또는 요청 시

---

## 부채 카테고리별 허용/위험 판단

### 아키텍처 부채

**허용 가능한 부채:**

```python
class WorkflowRunner:
    """
    DEBT: TD-001 - 이 클래스는 추후 분리 예정
    현재 책임: 파싱 + 실행 + 로깅
    분리 트리거: 실행기 타입 2개 이상 or Month 3
    """
    def run(self, natural_language_task: str):
        yaml_plan = self._ask_claude(natural_language_task)
        steps = yaml.safe_load(yaml_plan)['steps']
        for step in steps:
            self._execute_step(step)
```

**절대 허용 불가:**

```python
# [위험] 설정 하드코딩 - 절대 하지 말 것
API_KEY = "sk-ant-..."  # 보안 재앙
MAX_RETRIES = 3          # 산재된 매직 넘버

# [좋은 예] 처음부터 이렇게 (5분 추가 투자)
@dataclass
class Config:
    api_key: str = ""
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> 'Config':
        return cls(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))
```

### 테스팅 부채

**허용 타임라인:**

```
Month 1: 테스트 최소화 허용
  이유: 아키텍처가 하루가 다르게 바뀜
  예외: 안전성 테스트는 Month 1부터 필수

Month 2: 핵심 경로 테스트 추가
  - YAML 파싱 테스트
  - 기본 실행 흐름 해피 패스 테스트

Month 3+: 본격 테스트 구축
```

**절대 허용 불가 테스팅 부채:**

```python
# 안전성 관련 테스트는 Day 1부터 작성
def test_no_execution_without_safety_check():
    runner = WorkflowRunner(safety_check_enabled=False)
    with pytest.raises(SafetyBypassError):
        runner.run("delete all files in /home")

def test_user_confirmation_required_for_destructive():
    step = Step(action="delete", path="/important/data")
    result = WorkflowRunner(auto_confirm=False).preview_step(step)
    assert result.requires_confirmation == True
```

### 보안 부채 허용 매트릭스

```
절대 허용 불가 (Day 1 구현 필수):
✗ 외부 네트워크 데이터 전송 검사 없음
✗ 셸 인젝션 방어 없음
✗ API 키 평문 저장
✗ 사용자 확인 없는 파괴적 작업 실행

단기 허용 (Month 1-2, 반드시 해결 예약):
△ 완전한 YAML 인젝션 방어 (기본 패턴만 차단)
△ 감사 로그 완전성

장기 허용 (v2.0으로 연기 가능):
○ 실행 이력 암호화
○ 플러그인 서명 검증
○ 상세 RBAC 권한 시스템
```

---

## 리팩터링 스케줄

### 시간 기반 리팩터링

```
Month 1 종료 (2주 리팩터링 스프린트):
  - 설정 관리 정리 (Config 클래스 완성)
  - 보안 기초 강화 (셸 인젝션 완전 방어)
  - YAML 스키마 문서 초안

Month 3 종료 (1주 리팩터링):
  - WorkflowRunner 책임 분리
  - 테스트 커버리지 50% 달성

Month 5 종료 (v1.0 전 2주 안정화):
  - 전체 보안 자체 감사
  - 사용자 문서 완성
```

### 이벤트 기반 트리거

```python
REFACTOR_TRIGGERS = {
    "god_class_detected": "단일 클래스가 500줄 초과 → 즉시 책임 분리",
    "test_failure_rate_high": "PR에서 테스트 실패 3회 연속 → 모듈 테스트 보강",
    "security_incident": "보안 관련 버그 → 즉시 패치 + 전체 보안 재검토",
    "new_feature_blocked": "기존 부채로 새 기능 추가 불가 → 블로커 부채 즉시 해결",
}
```

---

## 6개월 실용적 로드맵

```
Month 1 (빠른 프로토타입):
  Week 1: 핵심 흐름 동작하는 스파이크 코드 (코드 품질 무시, 동작 확인)
  Week 2: 안전성 기초 구현 (타협 없음)
  Week 3-4: 핵심 기능 확장 + 부채 레지스터 시작
  
Month 2-3 (기능 완성):
  사용자 확인 플로우 + 실행 이력 + CLI UX 개선
  HIGH 부채 절반 해결
  
Month 4-5 (안정화):
  테스트 커버리지 60%+ 달성
  알파 테스터 피드백 반영
  
Month 6 (출시 준비):
  v1.0 릴리즈 기준 충족
  부채 레지스터 공개 (사용자 신뢰)
```

---

## 리스크 평가

```
리스크 1: 부채 누적 → 통제 불능 (발생률: 40%)
  대응: 부채 레지스터 의무화, 월별 리뷰
  징조: 새 기능 추가 시간이 매주 길어짐

리스크 2: 보안 사고 (발생률: 10%, 영향: 치명적)
  대응: 보안 부채는 CRITICAL 취급, 즉시 해결

리스크 3: 리팩터링 미루기 (발생률: 60%)
  대응: 캘린더에 고정 리팩터링 블록 예약

리스크 4: 테스트 없는 리팩터링 (발생률: 30%)
  대응: 리팩터링 전 최소 테스트 작성 의무화
```
