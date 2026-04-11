# Branch 4.1: 최소 부채 전략 (Clean Architecture First)
> Technical Debt Manager — 기술 부채 분석
> 조사일: 2026-04-07

## 핵심 철학
> "처음부터 올바르게 구축하면, 나중에 다시 짓지 않아도 된다."

1인 개발자가 6개월 동안 클린 아키텍처를 유지하면 **후반 속도가 빨라지지만, 초반 2-3개월이 느리다**는 구조적 트레이드오프를 갖는다.

---

## 부채 카테고리별 상세 분석

### 아키텍처 부채 (Architecture Debt)

**피해야 할 구체적 패턴:**

```
[위험 패턴 - 모놀리식 실행기]
class WorkflowRunner:
    def run(self, yaml_path):
        # YAML 파싱 + 유효성 검사 + 실행 + 로깅 + 에러처리
        # 모두 한 클래스에 뒤섞임
```

**권장 패턴 - 계층 분리:**

```
core/
├── domain/
│   ├── entities/          # 순수 도메인 객체
│   ├── use_cases/         # 유스케이스
│   └── ports/             # 추상 인터페이스
adapters/
├── claude_adapter.py      # Claude SDK 구현체
├── yaml_parser_adapter.py
└── local_executor_adapter.py
```

**핵심 인터페이스 설계:**

```python
# core/domain/ports/executor_port.py
from abc import ABC, abstractmethod

class ExecutorPort(ABC):
    """로컬 실행기의 추상 인터페이스.
    - 테스트 시 MockExecutor 교체 가능
    - 향후 Docker/샌드박스 실행기로 교체 가능
    - Claude API 변경에 독립적
    """
    
    @abstractmethod
    async def execute_step(self, step: Step, context: dict) -> ExecutionResult: ...
    
    @abstractmethod
    async def validate_step(self, step: Step) -> list[str]: ...
    
    @abstractmethod
    def is_safe_operation(self, step: Step) -> bool: ...
```

**초반 투자 비용:** 1-2주 추가 설계 시간  
**장기 이익:** 컴포넌트 교체 시 30분 vs 3일의 차이

---

### 테스팅 부채 (Testing Debt)

**테스트 피라미드 목표:**

```
테스트 피라미드 (로컬 AI 시스템 특화):
- E2E Tests:   5% (실제 Claude API 호출)
- Integration: 20% (컴포넌트 통합)
- Unit Tests:  75% (순수 도메인 로직)

목표:
- Unit: 최소 80개 이상
- Integration: 최소 20개
- E2E: 5개 (비용 때문에 최소화)
```

**핵심 테스트 - 안전성 검증 (가장 중요):**

```python
class TestSafetyGuards:
    """이 테스트들은 절대 삭제하면 안 됨"""
    
    def test_rm_rf_command_is_blocked(self):
        dangerous_step = Step(action="shell", command="rm -rf /home/user/important")
        result = SafetyValidator().validate(dangerous_step)
        assert result.is_blocked
    
    def test_credential_files_are_protected(self):
        step = Step(action="read_file", path="~/.ssh/id_rsa")
        assert not SafetyValidator().is_allowed(step)
    
    def test_network_exfiltration_is_blocked(self):
        step = Step(action="http_request", url="https://external-server.com", body="${sensitive_data}")
        assert SafetyValidator().classify_risk(step) == RiskLevel.CRITICAL
```

**테스트 커버리지 목표 (현실적):**
- Month 1: 도메인 엔티티 100%, 유스케이스 80%
- Month 3: 전체 커버리지 70%+
- Month 6 (v1.0): 전체 75%+, 안전성 관련 100%

---

### 문서화 부채 (Documentation Debt)

**ADR (Architecture Decision Record) 방식으로 주요 결정 기록:**

```markdown
# ADR-002: 안전성 검증 접근 방식

## 상태: 승인됨

## 결정
Allowlist 기반 검증 (Denylist 아님):
- 허용된 액션 목록만 실행 가능
- 새 액션 추가 시 명시적 승인 필요

## 대안 고려
- Denylist: 위험 명령어 목록으로 차단
  → 거부: 새 위험 패턴 지속 추가 필요, 우회 가능성 높음
```

---

### 보안 부채 (Security Debt)

**이 제품에서 보안 부채는 존재 자체가 위험:**

```python
# 안전한 명령어 실행 - 절대 shell=True 사용 금지
class SafeCommandExecutor:
    ALLOWED_COMMANDS = {'python', 'pip', 'git', 'ls', 'cat', 'mkdir'}
    
    def execute(self, command_string: str) -> ExecutionResult:
        tokens = shlex.split(command_string)
        
        if tokens[0] not in self.ALLOWED_COMMANDS:
            raise SecurityViolation(f"'{tokens[0]}'는 허용되지 않은 명령어")
        
        for token in tokens:
            if '..' in token or token.startswith('/etc'):
                raise SecurityViolation("경로 탐색 시도 감지")
        
        result = subprocess.run(
            tokens,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False  # 절대 True 사용 금지
        )
        return ExecutionResult(stdout=self._sanitize_output(result.stdout), ...)
```

---

## 6개월 타임라인 (Clean Architecture)

```
Month 1-2: 기반 구축
  Week 1-2: 도메인 엔티티 설계 + 포트 인터페이스 정의 + 보안 기초
  Week 3-4: 단위 테스트 인프라 (Mock, Fixture) + YAML 파서
  Week 5-8: 핵심 실행 엔진 + 안전성 검증 완성 + 기본 CLI

Month 3-4: 기능 완성
  에러 처리 + 복구 메커니즘
  실행 이력 / 로깅 시스템
  사용자 승인 플로우

Month 5-6: 안정화 및 출시
  E2E 테스트 (실제 Claude API)
  성능 프로파일링
  보안 자체 감사
  v1.0 릴리즈
```

---

## 리스크 평가

```
핵심 위험: "YAGNI 위반"
- 6개월 MVP에서 불필요한 추상화 과잉 구축
- 대응: 인터페이스는 교환 가능성이 필요한 곳에만 적용

발생 가능 문제:
- 일정 초과 (Month 2 초반): 높은 발생률
- 과도한 추상화: 높은 발생률
- 초기 기능 부족: 중간 발생률
- 사용자 피드백 지연: 중간 발생률
```
