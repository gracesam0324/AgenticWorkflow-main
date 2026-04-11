# Branch 2.2 — 완전한 아키텍처 설계 (Big Design Up Front)
> Architecture Specialist 분석
> 조사일: 2026-04-07

---

## 핵심 철학

BDUF는 구현 시작 전에 시스템의 모든 레이어, 컴포넌트, 인터페이스를 명확히 정의하는 접근법이다.

핵심 가정:
- 안전성은 설계 단계에서 결정된다
- 도메인 로직은 안정적이다 (NL→YAML→실행 파이프라인)
- 인터페이스 계약이 진화를 허용한다

---

## 헥사고날 아키텍처 전체 구조

```
DRIVING ADAPTERS (CLI, SDK, REST)
    ↓
INPUT PORTS (IWorkflowOrchestrator, IPlanningService, IExecutionService)
    ↓
CORE DOMAIN (WorkflowOrchestrator, PlanGenerator, StepExecutor, SafetyValidator, StateManager)
    ↓
OUTPUT PORTS (IAIProvider, IFileSystemPort, IShellPort, IStateRepository, IGitPort)
    ↓
DRIVEN ADAPTERS (Claude API, Local FS/OS, Git)
```

---

## 핵심 포트(Port) 정의

```python
# Input Port
class IWorkflowOrchestrator(ABC):
    @abstractmethod
    async def execute(self, request: WorkflowRequest) -> AsyncIterator[WorkflowState]: ...
    @abstractmethod
    async def resume(self, workflow_id: str) -> AsyncIterator[WorkflowState]: ...
    @abstractmethod
    async def abort(self, workflow_id: str) -> WorkflowResult: ...

# Output Ports
class IAIProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_message: str, response_format: ResponseFormat) -> AIResponse: ...

class IShellPort(ABC):
    ALLOWED_COMMANDS = frozenset(['python', 'pip', 'git', 'ls', 'cp', 'mv', 'mkdir', ...])
    
    @abstractmethod
    async def execute(self, command: str, args: list[str], cwd: Path, env: dict, timeout: int) -> ShellResult: ...
    
    @abstractmethod
    def is_dangerous_pattern(self, command: str) -> bool: ...

class IStateRepository(ABC):
    @abstractmethod
    async def save(self, state: WorkflowState) -> None: ...
    @abstractmethod
    async def load(self, workflow_id: str) -> WorkflowState: ...
    @abstractmethod
    async def list_active(self) -> list[WorkflowState]: ...
```

---

## 핵심 도메인 모델

```python
@dataclass(frozen=True)
class SafetyPolicy:
    allowed_paths: tuple[Path, ...]
    blocked_paths: tuple[Path, ...]
    allowed_commands: frozenset[str]
    max_execution_time_seconds: int = 3600
    require_approval_for_destructive: bool = True
    allow_network_access: bool = False

@dataclass
class WorkflowPlan:
    """SSOT — YAML로 표현된 전체 워크플로우 플랜. 생성 후 불변."""
    id: str
    version: str
    name: str
    steps: list[StepDefinition]
    safety_policy: SafetyPolicy

@dataclass
class WorkflowState:
    """실행 중 상태 — WorkflowPlan과 분리하여 관리."""
    workflow_id: str
    plan: WorkflowPlan
    status: WorkflowStatus
    current_step_id: Optional[str]
    step_results: dict[str, StepResult]
    context: dict[str, Any]
    checkpoints: list[str]
```

---

## YAML SOT 패턴 (상태 관리)

```
~/.local/share/workflow-ai/
├── plans/{workflow_id}.plan.yaml     # 불변: 무엇을 할 것인지
├── states/{workflow_id}.state.yaml   # 가변: 어디까지 왔는지
├── checkpoints/{workflow_id}/        # Git 스냅샷
└── archive/{date}/                   # 완료된 워크플로우
```

Plan 파일 (불변):
```yaml
workflow:
  id: wf_abc123
  version: "1"
  name: "Python 타입 힌트 분석"
  created_at: "2024-01-15T09:30:00Z"
  source_request: "src 폴더의 모든 Python 파일 분석..."
steps:
  - id: scan_files
    name: "Python 파일 목록 수집"
    type: shell
    config:
      command: find
      args: ["./src", "-name", "*.py"]
```

State 파일 (가변, 원자적 업데이트):
```yaml
workflow_id: wf_abc123
status: running
current_step: analyze_types
step_results:
  scan_files:
    status: completed
    completed_at: "2024-01-15T09:31:03Z"
checkpoints:
  - id: cp_001
    after_step: scan_files
    git_ref: "abc1234"
```

---

## v1.1/v2.0 확장 포인트

```
EXTENSION POINT 1: New Step Types
  현재: shell, file_*, ai_*, git, human_approval
  추가: database_query, http_request, docker_run
  구현: IStepExecutor 구현 + 등록 (기존 코드 수정 없음)

EXTENSION POINT 2: New AI Providers
  현재: Claude API
  추가: GPT-4, Ollama (로컬 모델)
  구현: IAIProvider 인터페이스 구현

EXTENSION POINT 3: New Storage Backends
  현재: YAML 파일
  추가: SQLite, PostgreSQL
  구현: IStateRepository 구현

EXTENSION POINT 4: New Presentation Adapters
  현재: CLI
  추가: Web UI, VS Code Extension
  구현: IWorkflowOrchestrator Input Port 구현
```

---

## Evolutionary Architecture(Branch 2.1)와의 비교

| 차원 | BDUF (Branch 2.2) | Evolutionary (Branch 2.1) |
|------|-------------------|--------------------------|
| 초기 설계 비용 | 높음 (2-4주) | 낮음 (1-2일) |
| 첫 동작 코드까지 | 느림 (5-6주) | 빠름 (1-2주) |
| 아키텍처 일관성 | 높음 | 중간 |
| 요구사항 변경 대응 | 낮음 | 높음 |
| 1인 개발 적합성 | 낮음 | 높음 |
| AI 파이프라인 불확실성 | 위험 | 안전 |

---

## 최종 권고: BDUF는 이 프로젝트에 부적합

**근거:**
1. 1인 × 6개월 = 전체 헥사고날 아키텍처 구현에만 4-6주 소요
2. AI 파이프라인은 실험적 — NL→YAML 동작은 구현해봐야 알 수 있음
3. 타겟 사용자 검증 전에 상세 설계는 위험
4. 동작하는 결과 없이 설계만 하면 동기 부여 저하

**권장 하이브리드: "Architecture-Informed Evolution"**
```
Phase 0 (1주): 아키텍처 스케치 (3개 핵심 포트만 정의)
  - IAIProvider (Claude 교체 가능성)
  - IShellPort (안전성 핵심)
  - IStateRepository (재개 기능 필수)
  - 도메인 모델 초안 (WorkflowPlan, WorkflowState)

Phase 1-4 (Month 1-4): Evolutionary 개발
  스케치를 가이드로 삼아 진화적 구현

Phase 5 (Month 5): Architecture Consolidation
  실제 코드 기반으로 전체 아키텍처 문서화

Phase 6 (Month 6): v1.0 Release Readiness
```

**BDUF에서 반드시 가져가야 할 요소:**
1. SafetyPolicy 도메인 모델 (Day 1부터)
2. WorkflowPlan/WorkflowState 분리 (YAML SOT 패턴)
3. IShellPort 화이트리스트 계약
4. YAML 플랜 스키마 계약
5. 이벤트 기반 상태 알림
