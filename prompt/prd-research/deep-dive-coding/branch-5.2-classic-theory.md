# Branch 5.2 — 검증된 고전 이론
> Theory Foundation Expert 분석
> 조사일: 2026-04-07

---

## 1. UNIX 철학 — AI 에이전트 적용

**UNIX 원칙 → AI 에이전트 원칙 매핑:**
```
Do One Thing Well       → 각 워크플로우 스텝은 단일 책임만
Text Stream Communication → 에이전트 간 통신: JSON/YAML 스트림
Composability           → 작은 워크플로우들을 파이프라인으로 조합
```

```yaml
# UNIX 파이프라인 개념: 조합 가능한 워크플로우
pipeline:
  - include: fetch_data.yaml      # 단일 책임: 데이터 가져오기
  - include: analyze_data.yaml    # 단일 책임: 분석
  - include: generate_report.yaml # 단일 책임: 보고서 생성
```

**핵심 통찰**: UNIX 파이프라인은 이미 1970년대에 현재 AI 에이전트 파이프라인의 본질을 포착했다.

**v1.0 우선순위: MUST-HAVE (설계 철학으로)**

---

## 2. Event Sourcing + CQRS

**Event Sourcing**: 시스템 상태를 마지막 스냅샷이 아닌 이벤트 시퀀스로 저장.
```
전통적 저장:  현재_상태 = {status: completed}
Event Sourcing: [STEP_STARTED, STEP_COMPLETED, WORKFLOW_DONE, ...]
현재_상태 = 이벤트 순서대로 재생하여 계산
```

**로컬 AI 적용 — 롤백의 핵심:**
```python
class WorkflowEventStore:
    def record(self, event: WorkflowEvent):
        """append-only. 과거 이벤트 수정 불가."""
        self._append_to_log(event)
    
    def rollback_to(self, session_id: str, timestamp: str) -> WorkflowState:
        """특정 시점의 상태로 롤백 (타임머신 기능)"""
        events = self._get_events_before(session_id, timestamp)
        return self._replay(events)
    
    def get_audit_trail(self, session_id: str) -> List[WorkflowEvent]:
        """완전한 실행 이력 (감사용)"""
        return self._get_events(session_id)
```

**v1.0 우선순위: MUST-HAVE (Event Sourcing), Nice-to-have (전체 CQRS)**

---

## 3. ECA (Event-Condition-Action) 규칙

```
ON [Event] IF [Condition] THEN [Action]
```

```yaml
eca_rules:
  - name: "자동_재시도"
    on: step_failed
    condition: "error.type == 'transient' AND retry_count < 3"
    action: retry_with_backoff
  
  - name: "메모리_초과_방지"
    on: memory_usage_check
    condition: "system.memory_percent > 85"
    action: pause_workflow
  
  - name: "데이터_파이프라인_트리거"
    on: file_created
    condition: "file.path matches '~/data/input/*.csv'"
    action: start_workflow
    workflow: "data_processing_pipeline.yaml"
```

**ECA + ReAct 조합**: ReAct가 능동적 계획 실행이라면, ECA는 수동적 반응 처리. 두 패턴의 조합이 최적.

**v1.0 우선순위: MUST-HAVE**

---

## 4. Principle of Least Privilege (최소 권한 원칙, 1974)

```python
class LeastPrivilegeEnforcer:
    def calculate_required_permissions(self, workflow: YAMLWorkflow) -> PermissionSet:
        """워크플로우 정적 분석으로 실제 필요한 권한만 계산"""
        required = PermissionSet()
        for step in workflow.steps:
            if step.action == "read_file":
                required.add(Permission.READ, scope=step.params['path'])
            elif step.action == "write_file":
                required.add(Permission.WRITE, scope=step.params['path'])
            # 네트워크는 명시적으로 요청된 경우만
            if step.params.get('network_access'):
                required.add(Permission.NETWORK)
        return required
```

```yaml
# YAML에서 권한 명시적 선언 (사용자가 검토 가능)
required_permissions:
  - type: read_file
    paths: ["~/data/*.csv"]
  - type: write_file
    paths: ["~/reports/"]
  - type: execute_python
    network_access: false  # 명시적으로 네트워크 차단
```

**v1.0 우선순위: MUST-HAVE**

---

## 5. Defense in Depth — 5계층 안전 모델

```
Layer 5: 사용자 감사 & 투명성 (모든 행동 로그, 언제든 중단)
Layer 4: 프로세스 격리 (샌드박스, 리소스 제한, 네트워크 격리)
Layer 3: 런타임 정책 엔진 (Constitutional AI, ECA 규칙)
Layer 2: YAML 계획 검증 (정적 분석, 권한 체크)
Layer 1: 자연어 입력 해석 (의도 명확화, 범위 확인)
```

**계층 간 독립성**: 각 계층은 다른 계층의 실패를 가정하고 설계.

**v1.0 우선순위: Layer 1,2,3 MUST-HAVE / Layer 4,5 Nice-to-have**

---

## 6. SOLID 원칙 — AI 에이전트 적용

```python
# S: Single Responsibility
class InputParser:      # 자연어 → 구조화 태스크
class WorkflowPlanner:  # 태스크 → YAML
class StepExecutor:     # YAML 스텝 실행
class SafetyValidator:  # 안전성 검증

# O: Open/Closed — 새 액션 타입 추가 시 기존 코드 수정 없이 확장
@StepExecutorRegistry.register(StepType.SHELL)
class ShellStepExecutor(IStepExecutor): ...

# D: Dependency Inversion — 추상화에 의존
class WorkflowEngine:
    def __init__(self, storage: StorageInterface, executor: ExecutorInterface): ...
    # 테스트 시 Mock 주입 가능
```

**v1.0 우선순위: SRP/OCP/DIP MUST-HAVE, LSP/ISP Nice-to-have**

---

## 7. Petri Net — 데드락 없는 워크플로우 검증

```python
class WorkflowPetriNetAnalyzer:
    def analyze(self, workflow: YAMLWorkflow) -> SafetyAnalysis:
        petri_net = self._convert_to_petri_net(workflow)
        
        deadlocks = petri_net.find_deadlocks()
        unreachable = petri_net.find_unreachable_places()
        conflicts = petri_net.find_resource_conflicts()
        
        return SafetyAnalysis(
            safe=len(deadlocks) == 0,
            deadlocks=deadlocks,
            unreachable_steps=unreachable,
            resource_conflicts=conflicts
        )
```

**실용적 단순화**: 완전한 Petri Net 대신 DAG(방향 비순환 그래프) 검증으로 시작.

**v1.0 우선순위: 간소화된 DAG 검증 MUST-HAVE, 완전한 Petri Net Nice-to-have**

---

## 8. Conway's Law — 에이전트 팀 설계

```
에이전트 팀 구조가 도메인 경계를 반영해야 한다.

자연어 처리 도메인 | 워크플로우 계획 | 실행 도메인 | 안전 도메인
InputParser       | WorkflowPlanner | StepExecutor| SafetyValidator
```

v1.0은 단일 에이전트이지만, 내부 모듈 경계를 도메인 경계와 일치시켜 나중에 멀티에이전트로 자연스럽게 전환 가능하게 설계.

**v1.0 우선순위: Nice-to-have (단, 설계 시 고려는 필수)**
