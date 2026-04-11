## BRANCH 2.2: 초기 완성도 설계 (Complete Architecture from Start)

### 1. 헥사고날 아키텍처 Python 구현

```
workflow_ai/
  ├── domain/
  │   ├── models.py       # 순수 데이터 클래스 (외부 의존성 없음)
  │   ├── services.py     # 비즈니스 로직 (인터페이스에만 의존)
  │   └── ports.py        # ABC / Protocol 추상 인터페이스
  ├── adapters/
  │   ├── claude_adapter.py   # anthropic SDK 격리
  │   ├── shell_adapter.py    # subprocess 격리
  │   └── yaml_store.py       # YAML 파일 I/O 격리
  └── application/
      └── orchestrator.py     # 유스케이스 조율
```

```python
# domain/ports.py — 순수 추상 인터페이스
from abc import ABC, abstractmethod
from typing import Protocol

class LLMProviderPort(Protocol):
    """ILLMProvider의 Python Protocol 구현 (typing.Protocol은 ABC보다 유연)"""
    def complete(self, prompt: str, system: str) -> str: ...

class ProcessExecutorPort(ABC):
    """IProcessExecutor의 ABC 구현 (강제적 구현 필요성이 있을 때 ABC 선택)"""
    @abstractmethod
    def execute(self, cmd: "Command") -> "ExecutionResult": ...
    
    @abstractmethod
    def classify(self, cmd: "Command") -> str: ...

class PlanStorePort(Protocol):
    """IWorkflowPlanStore — 한 번 쓰기, 체크섬 검증 포함"""
    def save(self, plan: "WorkflowPlan") -> None: ...
    def load(self, plan_id: str) -> "WorkflowPlan": ...
```

```python
# domain/services.py — 비즈니스 로직 (외부 의존성 제로)
class PlanningService:
    def __init__(self, llm: LLMProviderPort):
        self._llm = llm  # ABC/Protocol에만 의존 → 테스트 가능

    def create_plan(self, request: str) -> WorkflowPlan:
        raw = self._llm.complete(prompt=request, system=SYSTEM_PROMPT)
        # ... 파싱, 검증, 체크섬 계산

class ExecutionService:
    def __init__(
        self,
        executor: ProcessExecutorPort,
        plan_store: PlanStorePort,
        event_bus: "EventBus",  # 이벤트 시스템 주입
    ):
        self._executor = executor
        self._store = plan_store
        self._bus = event_bus

    def execute(self, plan_id: str) -> ExecutionResult:
        plan = self._store.load(plan_id)  # 체크섬 검증 포함
        # ... 실행 로직
        self._bus.emit("step_completed", {"plan_id": plan_id, "step_id": step.id})
```

```python
# adapters/claude_adapter.py — anthropic SDK를 domain과 격리
import anthropic
from domain.ports import LLMProviderPort

class ClaudeAdapter:
    """anthropic SDK 변경에 domain이 영향받지 않도록 격리"""
    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, prompt: str, system: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
```

### 2. 의존성 주입 패턴 — DI 컨테이너 없이

```python
# application/orchestrator.py — DI의 조립 지점
class WorkflowOrchestrator:
    """컨테이너 없는 수동 DI — 1인 MVP에 충분하다"""
    
    @classmethod
    def create_production(cls, config: Config) -> "WorkflowOrchestrator":
        """프로덕션용 인스턴스 조립"""
        llm = ClaudeAdapter(api_key=config.api_key)
        executor = LocalProcessExecutor()
        store = YamlPlanStore(path=config.state_dir / "plans.yaml")
        bus = SimpleEventBus()
        
        planning_svc = PlanningService(llm=llm)
        execution_svc = ExecutionService(
            executor=executor, plan_store=store, event_bus=bus
        )
        return cls(planning=planning_svc, execution=execution_svc, bus=bus)
    
    @classmethod
    def create_dry_run(cls, config: Config) -> "WorkflowOrchestrator":
        """Dry-run용 인스턴스 — executor만 교체"""
        llm = ClaudeAdapter(api_key=config.api_key)
        executor = DryRunProcessExecutor()  # 여기만 다름
        store = YamlPlanStore(path=config.state_dir / "plans.yaml")
        bus = SimpleEventBus()
        # ...

# 테스트용
def create_test_orchestrator():
    """테스트에서 모든 외부 의존성 대체 가능"""
    class FakeLLM:
        def complete(self, prompt, system):
            return "steps:\n  - id: test-1\n    type: shell\n    command: echo hello"
    
    return WorkflowOrchestrator.create_production(
        llm=FakeLLM(),
        executor=DryRunProcessExecutor(),
        store=InMemoryPlanStore()
    )
```

### 3. 이벤트 시스템 구현

```python
# domain/events.py — Python EventBus 패턴
from collections import defaultdict
from typing import Callable, Any

class SimpleEventBus:
    """MVP용 동기 EventBus — asyncio 없이 구현"""
    
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[dict], None]) -> None:
        self._handlers[event_type].append(handler)

    def emit(self, event_type: str, payload: dict) -> None:
        for handler in self._handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception as e:
                # 핸들러 오류가 메인 실행을 막지 않도록
                print(f"[EventBus 경고] {event_type} 핸들러 오류: {e}")

# 사용 예시 — 감사 로그와 Graduated Autonomy를 이벤트로 연결
bus = SimpleEventBus()

# 감사 로그 자동 기록
bus.subscribe("step_completed", audit_log.record_step)
bus.subscribe("step_failed", audit_log.record_failure)

# Graduated Autonomy 카운터 업데이트
bus.subscribe("step_completed", autonomy_tracker.on_success)
bus.subscribe("step_failed", autonomy_tracker.on_failure)
```

### 4. 플러그인 아키텍처 (Entry Points)

```python
# 새 스텝 타입 추가 방법 — setuptools entry_points 활용

# pyproject.toml
[project.entry-points."workflow_ai.step_types"]
shell = "workflow_ai.steps.shell:ShellStep"
file-write = "workflow_ai.steps.file_write:FileWriteStep"
validate = "workflow_ai.steps.validate:ValidateStep"
notify = "workflow_ai.steps.notify:NotifyStep"
user-prompt = "workflow_ai.steps.user_prompt:UserPromptStep"
# 새 플러그인은 별도 패키지에서 이 entry_point를 등록하면 됨
```

```python
# executor.py — 런타임 플러그인 로딩
import importlib.metadata

class PluginStepLoader:
    def __init__(self):
        # 설치된 모든 workflow_ai.step_types entry point를 로드
        self._step_types: dict[str, type] = {}
        for ep in importlib.metadata.entry_points(group="workflow_ai.step_types"):
            self._step_types[ep.name] = ep.load()
    
    def get(self, step_type: str) -> type:
        if step_type not in self._step_types:
            raise ValueError(f"알 수 없는 스텝 타입: {step_type}")
        return self._step_types[step_type]

# 사용: 새 스텝 타입 추가 시 executor.py 코드 변경 없음
loader = PluginStepLoader()
StepClass = loader.get(step.type)
step_instance = StepClass(executor=self.executor)
result = step_instance.run(step)
```

### 5. Branch 2.1과의 실제 코드 복잡도 비교

| 항목 | Branch 2.1 (점진적) | Branch 2.2 (완전) |
|---|---|---|
| Month 1 코드 라인 수 | ~500 LOC | ~1,800 LOC |
| Month 3 코드 라인 수 | ~1,500 LOC | ~3,000 LOC |
| Month 6 코드 라인 수 | ~2,500 LOC | ~4,500 LOC |
| 첫 동작하는 버전까지 | **3일** | **2주** |
| 테스트 작성 용이성 | Month 3 이후 (인터페이스 추출 후) | **Day 1부터 가능** |
| 신규 기여자 이해 시간 | **30분** | 3-4시간 |
| 오버엔지니어링 위험 | 낮음 | **높음** |

Branch 2.2의 현실적 문제점:
```python
# 헥사고날이 만드는 실제 부담

# 단순한 작업 하나를 추가할 때:
# 1. domain/models.py에 모델 추가
# 2. domain/ports.py에 인터페이스 추가
# 3. domain/services.py에 서비스 메서드 추가
# 4. adapters/에 어댑터 추가
# 5. application/orchestrator.py에서 DI 배선
# 6. 각 계층별 테스트 작성

# Branch 2.1에서 동일한 작업:
# 1. executor.py에 _run_new_step() 메서드 추가
# 2. 동작 확인
# → 인터페이스 필요성이 생기면 그때 추출
```

---

## 결론: 두 Branch 비교 및 권장사항

### 핵심 트레이드오프

**Branch 2.1 (점진적)의 실제 장점:**

```python
# Month 1 — 이것이 먼저 동작한다
def run_workflow(request: str):
    plan = planner.plan(request)      # Claude API 호출
    if confirm_plan(plan):             # 터미널 확인
        return executor.run(plan)      # 단순 실행

# 이 50줄이 동작하는 순간, 나머지는 리팩터링이다.
# 리팩터링은 동작하는 코드 위에서 안전하게 할 수 있다.
```

**Branch 2.2 (완전)의 실제 단점:**

```python
# domain/ports.py를 정의하는 데 시간을 쓰는 동안
# "실제로 자연어 → YAML 변환이 잘 되는가"를 모른다.
# Claude API가 어떤 형식으로 응답하는지, 
# 파싱 예외가 어디서 발생하는지를 
# 500줄의 추상화 레이어 뒤에서 발견하게 된다.
```

**Branch 2.2 (완전)의 실제 장점:**

```python
# 테스트 작성이 Day 1부터 가능하다.
def test_planning_service_with_fake_llm():
    class FakeLLM:
        def complete(self, prompt, system):
            return FIXTURE_YAML  # 실제 API 호출 없음
    
    svc = PlanningService(llm=FakeLLM())
    plan = svc.create_plan("로그 정리해줘")
    assert len(plan.steps) > 0
    # 이 테스트는 Claude API 없이도 CI에서 돌아간다
```

### 1인 6개월 MVP에 권장하는 아키텍처: **Branch 2.1 + 선택적 2.2 요소**

핵심 원칙: **PRD 절대 기준 1 (`IProcessExecutor`)은 Week 1에 추출하되, 나머지는 필요할 때 추출한다.**

```
Week 1-2:  safety.py의 IProcessExecutor + DryRunExecutor 구현 (Branch 2.2 방식)
           → 이것만은 처음부터 인터페이스가 필요하다 (안전이 목적)
           → 나머지는 단일 파일로 시작

Month 1:   단일 파일 → 5개 모듈 분리 (Branch 2.1)
           cli.py / planner.py / executor.py / safety.py / state.py
           → 이미 실제 autobiography-generator에서 검증된 구조

Month 3:   ILLMProvider 추출 (Branch 2.2 방식, 선택적)
           → Ollama Yellow Zone 조건 충족 시 자연스럽게 필요해짐
           → 필요 전에 추출하지 않는다

Month 4-6: IWorkflowPlanStore 추출 (Branch 2.2 방식, 조건부)
           → 플랜 저장 방식을 바꾸어야 할 실제 이유가 생기면 추출
           → EventBus는 AuditLog + GraduatedAutonomyTracker가 
             동시에 필요해지는 Month 3에 자연스럽게 등장
```

### PRD에 반영해야 할 아키텍처 결정 사항

**결정 1: 인터페이스 추출 시점을 명시하라**

현재 PRD §6은 "딱 3개" 인터페이스를 나열하지만 언제 추출하는지가 없습니다. 추가 권장 문구:

> `IProcessExecutor`는 Week 1 첫 커밋에서 추출한다. `ILLMProvider`는 두 번째 구현체(Ollama)가 필요해지는 시점에 추출한다. `IWorkflowPlanStore`는 저장 방식을 바꾸어야 할 이유가 생길 때 추출한다. "미래에 필요할 것 같아서" 추출하지 않는다.

**결정 2: state.yaml 원자적 쓰기 패턴을 아키텍처 결정으로 명시하라**

autobiography-generator의 `sot_lib.py`가 이미 완성된 구현입니다. 이 패턴 (`fcntl.flock` + `.tmp` 파일 경유 `os.replace()` + `.bak` 복구)을 PRD에 ADR 형식으로 기록하고, workflow_ai가 이 라이브러리를 재사용하도록 명시하는 것이 좋습니다.

**결정 3: 이벤트 버스 도입 조건을 명시하라**

현재 PRD에 EventBus 언급이 없습니다. AuditLogService와 GraduatedAutonomyTracker가 동시에 구현되는 Month 3 시점에 `SimpleEventBus`를 도입하되, 그 전까지는 직접 함수 호출로 유지한다는 결정을 ADR에 추가하면 Month 1 오버엔지니어링을 방지합니다.

**결정 4: 플러그인 아키텍처는 Red Zone으로 이동하라**

Entry points 기반 플러그인은 커뮤니티 템플릿 공유와 동일한 위험(RCE 벡터)을 갖습니다. PRD Red Zone의 "커뮤니티 템플릿 공유 — 품질 제어 없는 공유는 RCE 벡터" 논리가 플러그인에도 동일하게 적용됩니다. v1에서는 6가지 내장 스텝 타입으로 충분하며, 플러그인은 서명 체계 구축 후 v2에서 도입하는 것이 PRD 절대 기준 1(안전 우선)과 일관됩니다.

---

**최종 요약**: Branch 2.1의 점진적 접근이 1인 6개월 MVP에 현실적이며, `IProcessExecutor` 하나만은 Branch 2.2 방식(처음부터 인터페이스)으로 구현한다. 이것이 PRD의 절대 기준 1 "안전 경계는 코드 레벨"을 실현하는 유일한 방법이고, 나머지는 동작하는 코드가 생긴 후 리팩터링으로 충분합니다. autobiography-generator의 `sot_lib.py`와 `block_destructive_commands.py`는 이 하이브리드 접근의 실제 구현 참조 코드로 직접 활용 가능합니다.