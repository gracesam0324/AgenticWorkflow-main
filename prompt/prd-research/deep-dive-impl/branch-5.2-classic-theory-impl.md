# BRANCH 5.2: 고전 이론 기반 (Proven CS Foundations)

---

## 1. 상태 머신 이론 → 워크플로우 엔진

### FSM으로 워크플로우 상태 완전 모델링

```python
# workflow_state_machine.py

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Callable, Optional
import time

class WorkflowState(Enum):
    """워크플로우 유한 상태 정의"""
    IDLE = auto()
    PLANNING = auto()
    PLAN_REVIEW = auto()      # 사용자 검토 대기
    EXECUTING = auto()
    STEP_EXECUTING = auto()   # 개별 스텝 실행
    PAUSED = auto()           # 일시 중지
    COMPLETED = auto()
    FAILED = auto()
    ROLLING_BACK = auto()
    ROLLED_BACK = auto()

class WorkflowEvent(Enum):
    """상태 전이를 트리거하는 이벤트"""
    START_PLANNING = auto()
    PLAN_GENERATED = auto()
    PLAN_APPROVED = auto()
    PLAN_REJECTED = auto()
    START_EXECUTION = auto()
    STEP_COMPLETE = auto()
    STEP_FAILED = auto()
    ALL_STEPS_DONE = auto()
    PAUSE = auto()
    RESUME = auto()
    FAILURE = auto()
    START_ROLLBACK = auto()
    ROLLBACK_COMPLETE = auto()
    RESET = auto()

@dataclass
class StateTransition:
    """상태 전이 정의"""
    from_state: WorkflowState
    event: WorkflowEvent
    to_state: WorkflowState
    guard: Optional[Callable] = None      # 전이 조건 (Guard)
    action: Optional[Callable] = None     # 전이 시 실행 액션

class WorkflowStateMachine:
    """
    워크플로우 유한 상태 머신
    
    설계 원칙:
    - 모든 가능한 상태와 전이를 명시적으로 정의
    - 정의되지 않은 전이는 예외 발생 (방어적 설계)
    - 각 전이에 액션과 가드 조건 부착 가능
    """
    
    # 전이 테이블 (핵심 FSM 구성요소)
    TRANSITIONS = [
        StateTransition(WorkflowState.IDLE, WorkflowEvent.START_PLANNING, WorkflowState.PLANNING),
        StateTransition(WorkflowState.PLANNING, WorkflowEvent.PLAN_GENERATED, WorkflowState.PLAN_REVIEW),
        StateTransition(WorkflowState.PLAN_REVIEW, WorkflowEvent.PLAN_APPROVED, WorkflowState.EXECUTING),
        StateTransition(WorkflowState.PLAN_REVIEW, WorkflowEvent.PLAN_REJECTED, WorkflowState.IDLE),
        StateTransition(WorkflowState.EXECUTING, WorkflowEvent.START_EXECUTION, WorkflowState.STEP_EXECUTING),
        StateTransition(WorkflowState.STEP_EXECUTING, WorkflowEvent.STEP_COMPLETE, WorkflowState.EXECUTING),
        StateTransition(WorkflowState.STEP_EXECUTING, WorkflowEvent.STEP_FAILED, WorkflowState.FAILED),
        StateTransition(WorkflowState.EXECUTING, WorkflowEvent.ALL_STEPS_DONE, WorkflowState.COMPLETED),
        StateTransition(WorkflowState.STEP_EXECUTING, WorkflowEvent.PAUSE, WorkflowState.PAUSED),
        StateTransition(WorkflowState.PAUSED, WorkflowEvent.RESUME, WorkflowState.STEP_EXECUTING),
        StateTransition(WorkflowState.FAILED, WorkflowEvent.START_ROLLBACK, WorkflowState.ROLLING_BACK),
        StateTransition(WorkflowState.ROLLING_BACK, WorkflowEvent.ROLLBACK_COMPLETE, WorkflowState.ROLLED_BACK),
        StateTransition(WorkflowState.COMPLETED, WorkflowEvent.RESET, WorkflowState.IDLE),
        StateTransition(WorkflowState.ROLLED_BACK, WorkflowEvent.RESET, WorkflowState.IDLE),
        StateTransition(WorkflowState.FAILED, WorkflowEvent.RESET, WorkflowState.IDLE),
    ]
    
    def __init__(self):
        self.state = WorkflowState.IDLE
        self._transition_map = self._build_transition_map()
        self._history: list[tuple[WorkflowState, WorkflowEvent, float]] = []
    
    def _build_transition_map(self) -> dict:
        """빠른 조회를 위한 전이 맵 구축"""
        return {
            (t.from_state, t.event): t 
            for t in self.TRANSITIONS
        }
    
    def trigger(self, event: WorkflowEvent, context: dict = None) -> WorkflowState:
        """
        이벤트 트리거 → 상태 전이
        
        Raises:
            InvalidTransitionError: 현재 상태에서 해당 이벤트 불가
        """
        key = (self.state, event)
        
        if key not in self._transition_map:
            raise ValueError(
                f"유효하지 않은 전이: {self.state.name} + {event.name}\n"
                f"현재 상태에서 가능한 이벤트: "
                f"{[e.name for (s,e) in self._transition_map if s == self.state]}"
            )
        
        transition = self._transition_map[key]
        
        # Guard 조건 확인
        if transition.guard and not transition.guard(context):
            raise ValueError(
                f"전이 가드 조건 실패: {self.state.name} → {transition.to_state.name}"
            )
        
        # 상태 전이 기록
        self._history.append((self.state, event, time.time()))
        prev_state = self.state
        self.state = transition.to_state
        
        # 전이 액션 실행
        if transition.action:
            transition.action(prev_state, self.state, context)
        
        return self.state
    
    def can_trigger(self, event: WorkflowEvent) -> bool:
        """특정 이벤트 트리거 가능 여부 확인"""
        return (self.state, event) in self._transition_map
    
    def get_available_events(self) -> list[WorkflowEvent]:
        """현재 상태에서 가능한 이벤트 목록"""
        return [e for (s, e) in self._transition_map if s == self.state]
```

---

## 2. 파이프라인 패턴 → 실행 엔진

### 제너레이터 기반 스트리밍 실행 (Unix 파이프 철학)

```python
# pipeline_executor.py

from typing import Generator, Iterator, Any, Callable
from dataclasses import dataclass
import time

@dataclass
class PipelineItem:
    """파이프라인을 흐르는 데이터 단위"""
    step_id: str
    data: Any
    metadata: dict
    timestamp: float = 0.0
    
    def __post_init__(self):
        self.timestamp = time.time()

@dataclass
class ExecutionResult:
    """스텝 실행 결과"""
    step_id: str
    success: bool
    output: Any
    error: str = None
    duration_ms: float = 0.0

def pipeline_stage(func: Callable) -> Callable:
    """파이프라인 스테이지 데코레이터"""
    def wrapper(items: Iterator[PipelineItem]) -> Generator[PipelineItem, None, None]:
        for item in items:
            yield func(item)
    return wrapper

class WorkflowPipeline:
    """
    제너레이터 기반 워크플로우 실행 파이프라인
    
    Unix 파이프 철학:
    - 각 스테이지는 독립적으로 동작
    - 데이터는 스트림으로 흐름 (메모리 효율적)
    - 백프레셔: 소비자 속도에 맞춰 생산
    - 각 스테이지는 제너레이터로 구현
    """
    
    def __init__(self):
        self.stages: list[Callable] = []
        self._results: list[ExecutionResult] = []
    
    def add_stage(self, stage: Callable) -> 'WorkflowPipeline':
        """스테이지 추가 (메서드 체이닝)"""
        self.stages.append(stage)
        return self
    
    def _validate_stage(
        self, items: Iterator[PipelineItem]
    ) -> Generator[PipelineItem, None, None]:
        """검증 스테이지: 각 아이템의 필수 필드 확인"""
        for item in items:
            if not item.step_id:
                raise ValueError(f"step_id 없는 파이프라인 아이템")
            yield item
    
    def _log_stage(
        self, items: Iterator[PipelineItem]
    ) -> Generator[PipelineItem, None, None]:
        """로깅 스테이지: 각 아이템 통과 기록"""
        for item in items:
            print(f"  [Pipeline] 처리 중: {item.step_id}")
            yield item
    
    def _execute_stage(
        self, items: Iterator[PipelineItem],
        executor: Callable
    ) -> Generator[ExecutionResult, None, None]:
        """실행 스테이지: 실제 스텝 실행"""
        for item in items:
            start = time.time()
            try:
                output = executor(item.data)
                duration = (time.time() - start) * 1000
                result = ExecutionResult(
                    step_id=item.step_id,
                    success=True,
                    output=output,
                    duration_ms=duration
                )
            except Exception as e:
                duration = (time.time() - start) * 1000
                result = ExecutionResult(
                    step_id=item.step_id,
                    success=False,
                    output=None,
                    error=str(e),
                    duration_ms=duration
                )
            
            self._results.append(result)
            yield result
    
    def execute(
        self, 
        steps: list[dict],
        step_executor: Callable,
        progress_callback: Callable = None
    ) -> Generator[ExecutionResult, None, None]:
        """
        파이프라인 실행 (제너레이터 반환 - 스트리밍)
        
        백프레셔 처리: 소비자가 next()를 호출할 때만 다음 스텝 실행
        """
        # 소스: 스텝 목록 → PipelineItem 스트림
        def source() -> Generator[PipelineItem, None, None]:
            for step in steps:
                yield PipelineItem(
                    step_id=step["step_id"],
                    data=step,
                    metadata={"total_steps": len(steps)}
                )
        
        # 파이프라인 구성 (제너레이터 체이닝)
        stream = source()
        stream = self._validate_stage(stream)
        stream = self._log_stage(stream)
        stream = self._execute_stage(stream, step_executor)
        
        # 스트리밍 소비 (백프레셔 자동 처리)
        for result in stream:
            if progress_callback:
                progress_callback(result)
            yield result  # 소비자에게 즉시 전달

# 사용 예시
def demo_pipeline():
    pipeline = WorkflowPipeline()
    
    steps = [
        {"step_id": "step_1", "command": "echo 'Hello'"},
        {"step_id": "step_2", "command": "ls -la"},
        {"step_id": "step_3", "command": "pwd"},
    ]
    
    def simple_executor(step_data: dict) -> str:
        import subprocess
        result = subprocess.run(
            step_data["command"], shell=True, 
            capture_output=True, text=True
        )
        return result.stdout
    
    # 스트리밍 실행 - 각 결과가 완료되는 즉시 처리
    for result in pipeline.execute(steps, simple_executor):
        status = "✓" if result.success else "✗"
        print(f"{status} {result.step_id}: {result.duration_ms:.1f}ms")
```

---

## 3. 관찰자 패턴 → 이벤트 시스템

```python
# event_bus.py

from dataclasses import dataclass, field
from typing import Callable, Any
from enum import Enum
import time
import json
from pathlib import Path

class SystemEvent(Enum):
    """시스템 이벤트 정의"""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"
    LLM_CALLED = "llm.called"
    LLM_RESPONDED = "llm.responded"
    USER_CONFIRMED = "user.confirmed"
    USER_CANCELLED = "user.cancelled"
    ROLLBACK_STARTED = "rollback.started"
    ROLLBACK_COMPLETED = "rollback.completed"

@dataclass
class Event:
    """이벤트 데이터 클래스"""
    type: SystemEvent
    payload: dict
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: 
                          f"evt_{int(time.time()*1000)}")

class EventBus:
    """
    Observer 패턴 기반 이벤트 버스
    
    특징:
    - 비동기 가능한 동기 구현 (MVP 단계)
    - 감사 로그 자동 기록
    - 실시간 진행상황 스트리밍
    - 와일드카드 구독 지원 ("workflow.*")
    """
    
    def __init__(self, log_file: str = "audit.jsonl"):
        self._subscribers: dict[str, list[Callable]] = {}
        self._log_file = Path(log_file)
        self._event_history: list[Event] = []
        
        # 감사 로그는 항상 기록 (자동 구독)
        self.subscribe("*", self._audit_log_handler)
    
    def subscribe(self, event_pattern: str, handler: Callable) -> None:
        """
        이벤트 구독
        
        event_pattern: 
          - "workflow.started" (정확한 이벤트)
          - "workflow.*" (와일드카드)
          - "*" (모든 이벤트)
        """
        if event_pattern not in self._subscribers:
            self._subscribers[event_pattern] = []
        self._subscribers[event_pattern].append(handler)
    
    def unsubscribe(self, event_pattern: str, handler: Callable) -> None:
        if event_pattern in self._subscribers:
            self._subscribers[event_pattern].remove(handler)
    
    def publish(self, event_type: SystemEvent, payload: dict = None) -> Event:
        """이벤트 발행 → 모든 구독자에게 즉시 전달"""
        event = Event(type=event_type, payload=payload or {})
        self._event_history.append(event)
        
        event_value = event_type.value  # e.g., "workflow.started"
        notified = set()
        
        for pattern, handlers in self._subscribers.items():
            if self._matches(pattern, event_value):
                for handler in handlers:
                    if id(handler) not in notified:
                        try:
                            handler(event)
                        except Exception as e:
                            print(f"[EventBus] 핸들러 오류 ({pattern}): {e}")
                        notified.add(id(handler))
        
        return event
    
    def _matches(self, pattern: str, event_value: str) -> bool:
        """와일드카드 패턴 매칭"""
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_value.startswith(prefix)
        return pattern == event_value
    
    def _audit_log_handler(self, event: Event) -> None:
        """감사 로그 자동 기록 (JSONL 형식)"""
        log_entry = {
            "event_id": event.event_id,
            "type": event.type.value,
            "payload": event.payload,
            "timestamp": event.timestamp,
            "datetime": time.strftime(
                "%Y-%m-%dT%H:%M:%S", 
                time.localtime(event.timestamp)
            )
        }
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# 전역 이벤트 버스 (싱글턴)
event_bus = EventBus()

# 사용 예시
def setup_progress_display():
    """실시간 진행상황 표시 구독자 등록"""
    
    def on_step_started(event: Event):
        step_name = event.payload.get("step_name", "")
        print(f"\n→ 실행 중: {step_name}")
    
    def on_step_completed(event: Event):
        step_name = event.payload.get("step_name", "")
        duration = event.payload.get("duration_ms", 0)
        print(f"  ✓ 완료: {step_name} ({duration:.0f}ms)")
    
    def on_workflow_completed(event: Event):
        total = event.payload.get("total_steps", 0)
        print(f"\n워크플로우 완료: {total}개 스텝 성공")
    
    event_bus.subscribe("step.started", on_step_started)
    event_bus.subscribe("step.completed", on_step_completed)
    event_bus.subscribe("workflow.completed", on_workflow_completed)
```

---

## 4. 방어적 프로그래밍 → 안전 시스템

### Design by Contract + 불변량 검증

```python
# defensive_programming.py

import functools
import os
import re
from pathlib import Path
from typing import Callable, Any

# ─── Design by Contract 구현 ─────────────────────────────────────────

class ContractViolation(Exception):
    """계약 위반 예외"""
    pass

def precondition(condition: Callable, message: str):
    """전제조건 데코레이터 (사전 조건)"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not condition(*args, **kwargs):
                raise ContractViolation(
                    f"[전제조건 위반] {func.__name__}: {message}\n"
                    f"입력값: args={args[:3]}, kwargs={kwargs}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def postcondition(condition: Callable, message: str):
    """사후조건 데코레이터 (결과 검증)"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            if not condition(result):
                raise ContractViolation(
                    f"[사후조건 위반] {func.__name__}: {message}\n"
                    f"결과값: {str(result)[:200]}"
                )
            return result
        return wrapper
    return decorator

def invariant(condition: Callable, message: str):
    """불변량 데코레이터 (클래스 상태 일관성)"""
    def decorator(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            result = method(self, *args, **kwargs)
            if not condition(self):
                raise ContractViolation(
                    f"[불변량 위반] {self.__class__.__name__}.{method.__name__}: "
                    f"{message}"
                )
            return result
        return wrapper
    return decorator

# ─── 로컬 실행 안전 시스템 ────────────────────────────────────────────

class SafeExecutor:
    """
    방어적 프로그래밍으로 구현된 안전 실행기
    
    계약:
    - 전제조건: 명령어는 문자열, 경로는 존재, 위험 패턴 없음
    - 사후조건: 결과는 dict, returncode 포함
    - 불변량: 실행 후 working_dir 변경 없음
    """
    
    FORBIDDEN_PATTERNS = [
        r'rm\s+-rf\s+/', r'sudo\s+rm', r'>\s*/dev/sd',
        r'mkfs', r'fdisk', r'dd\s+if=.*of=/dev/',
        r'chmod\s+777\s+/', r':\(\)\s*\{',  # fork bomb
    ]
    
    def __init__(self, allowed_base_dirs: list[str] = None):
        self._allowed_dirs = [
            Path(d).resolve() for d in (allowed_base_dirs or [str(Path.home())])
        ]
        self._execution_count = 0
        self._original_cwd = Path.cwd()
    
    def _check_forbidden_patterns(self, command: str) -> None:
        """위험 패턴 검사 (전제조건 헬퍼)"""
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                raise ContractViolation(
                    f"위험한 명령어 패턴 감지: {pattern}\n명령어: {command}"
                )
    
    def _check_path_safety(self, path_str: str) -> None:
        """경로 안전성 검사 (디렉토리 탈출 방지)"""
        path = Path(path_str).resolve()
        is_allowed = any(
            str(path).startswith(str(allowed)) 
            for allowed in self._allowed_dirs
        )
        if not is_allowed:
            raise ContractViolation(
                f"허용되지 않은 경로: {path}\n"
                f"허용 디렉토리: {self._allowed_dirs}"
            )
    
    @precondition(
        lambda self, command, working_dir=".": (
            isinstance(command, str) and len(command.strip()) > 0
        ),
        "명령어는 비어있지 않은 문자열이어야 함"
    )
    @postcondition(
        lambda result: (
            isinstance(result, dict) and 
            "returncode" in result and
            isinstance(result["returncode"], int)
        ),
        "실행 결과는 returncode를 포함한 dict이어야 함"
    )
    def execute(self, command: str, working_dir: str = ".") -> dict:
        """
        안전한 명령어 실행
        
        계약:
        - PRE:  command는 비어있지 않음, 위험 패턴 없음, 경로 허용됨
        - POST: 결과는 {stdout, stderr, returncode} dict
        - INV:  실행 후 현재 디렉토리 불변
        """
        import subprocess
        
        # 추가 전제조건 검사
        self._check_forbidden_patterns(command)
        self._check_path_safety(working_dir)
        
        saved_cwd = Path.cwd()
        
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, cwd=working_dir, timeout=60
            )
            self._execution_count += 1
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "execution_count": self._execution_count
            }
        finally:
            # 불변량: cwd는 변경되지 않아야 함
            if Path.cwd() != saved_cwd:
                os.chdir(saved_cwd)  # 강제 복구
```

---

## 5. Command 패턴 → 롤백 시스템

```python
# rollback_system.py

import subprocess
import shutil
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import time

class Command(ABC):
    """
    Command 패턴 기반 인터페이스
    
    모든 실행 가능한 작업은 이 인터페이스를 구현
    - execute(): 작업 수행
    - undo(): 작업 취소 (롤백)
    - can_undo(): 롤백 가능 여부
    """
    
    @abstractmethod
    def execute(self) -> dict:
        pass
    
    @abstractmethod
    def undo(self) -> dict:
        pass
    
    @abstractmethod
    def can_undo(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass

class FileCreateCommand(Command):
    """파일 생성 명령 (롤백: 파일 삭제)"""
    
    def __init__(self, file_path: str, content: str):
        self.file_path = Path(file_path)
        self.content = content
        self._existed_before = False
        self._original_content: Optional[str] = None
    
    @property
    def description(self) -> str:
        return f"파일 생성: {self.file_path}"
    
    def execute(self) -> dict:
        # 기존 상태 저장 (롤백용)
        if self.file_path.exists():
            self._existed_before = True
            self._original_content = self.file_path.read_text(encoding="utf-8")
        
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.write_text(self.content, encoding="utf-8")
        return {"success": True, "path": str(self.file_path)}
    
    def undo(self) -> dict:
        if self._existed_before and self._original_content is not None:
            # 원본 내용 복원
            self.file_path.write_text(self._original_content, encoding="utf-8")
            return {"success": True, "action": "restored_original"}
        else:
            # 새로 만든 파일 삭제
            if self.file_path.exists():
                self.file_path.unlink()
            return {"success": True, "action": "deleted_new_file"}
    
    def can_undo(self) -> bool:
        return True

class GitCommitCommand(Command):
    """Git 커밋 명령 (롤백: git revert)"""
    
    def __init__(self, repo_path: str, message: str, files: list[str] = None):
        self.repo_path = Path(repo_path)
        self.message = message
        self.files = files or ["."]
        self._commit_hash: Optional[str] = None
    
    @property
    def description(self) -> str:
        return f"Git 커밋: '{self.message}'"
    
    def execute(self) -> dict:
        # 파일 스테이징
        files_str = " ".join(self.files)
        subprocess.run(
            f"git add {files_str}", shell=True, 
            cwd=self.repo_path, check=True
        )
        
        # 커밋
        result = subprocess.run(
            f'git commit -m "{self.message}"',
            shell=True, capture_output=True, 
            text=True, cwd=self.repo_path
        )
        
        # 커밋 해시 저장
        hash_result = subprocess.run(
            "git rev-parse HEAD", shell=True,
            capture_output=True, text=True, cwd=self.repo_path
        )
        self._commit_hash = hash_result.stdout.strip()
        
        return {
            "success": result.returncode == 0,
            "commit_hash": self._commit_hash,
            "output": result.stdout
        }
    
    def undo(self) -> dict:
        if not self._commit_hash:
            return {"success": False, "error": "커밋 해시 없음"}
        
        # git revert로 안전하게 취소 (히스토리 보존)
        result = subprocess.run(
            f"git revert {self._commit_hash} --no-edit",
            shell=True, capture_output=True,
            text=True, cwd=self.repo_path
        )
        return {
            "success": result.returncode == 0,
            "reverted_hash": self._commit_hash,
            "output": result.stdout
        }
    
    def can_undo(self) -> bool:
        return self._commit_hash is not None

@dataclass
class CommandHistory:
    """
    실행된 명령 히스토리 관리 (Undo Stack)
    """
    commands: list[Command] = field(default_factory=list)
    execution_log: list[dict] = field(default_factory=list)
    
    def execute(self, command: Command) -> dict:
        """명령 실행 및 히스토리 기록"""
        start = time.time()
        result = command.execute()
        duration = (time.time() - start) * 1000
        
        self.commands.append(command)
        self.execution_log.append({
            "description": command.description,
            "result": result,
            "duration_ms": duration,
            "timestamp": time.time(),
            "can_undo": command.can_undo()
        })
        
        return result
    
    def rollback_last(self) -> dict:
        """마지막 명령 롤백"""
        if not self.commands:
            return {"success": False, "error": "롤백할 명령 없음"}
        
        command = self.commands[-1]
        if not command.can_undo():
            return {"success": False, "error": f"롤백 불가: {command.description}"}
        
        result = command.undo()
        if result.get("success"):
            self.commands.pop()
        return result
    
    def rollback_all(self) -> list[dict]:
        """모든 명령을 역순으로 롤백"""
        results = []
        while self.commands:
            result = self.rollback_last()
            results.append(result)
            if not result.get("success"):
                break
        return results
    
    def rollback_to_checkpoint(self, checkpoint_index: int) -> list[dict]:
        """특정 체크포인트까지 롤백"""
        results = []
        while len(self.commands) > checkpoint_index:
            result = self.rollback_last()
            results.append(result)
        return results
    
    def create_checkpoint(self) -> int:
        """현재 상태를 체크포인트로 저장"""
        return len(self.commands)

# Git 기반 전체 롤백 구현
class GitRollbackManager:
    """
    Git을 활용한 스냅샷 기반 롤백 시스템
    
    워크플로우 실행 전 스냅샷 → 실패 시 즉시 복원
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self._snapshot_branch: Optional[str] = None
    
    def create_snapshot(self, tag: str = None) -> str:
        """실행 전 스냅샷 생성"""
        snapshot_name = tag or f"snapshot_{int(time.time())}"
        
        # 현재 상태 스태시 (미커밋 변경사항 포함)
        subprocess.run(
            f"git stash push -m '{snapshot_name}'",
            shell=True, cwd=self.repo_path
        )
        
        # 스냅샷 태그 생성
        subprocess.run(
            f"git tag {snapshot_name}",
            shell=True, cwd=self.repo_path
        )
        
        self._snapshot_branch = snapshot_name
        return snapshot_name
    
    def restore_snapshot(self, snapshot_name: str = None) -> dict:
        """스냅샷으로 복원"""
        target = snapshot_name or self._snapshot_branch
        if not target:
            return {"success": False, "error": "복원할 스냅샷 없음"}
        
        # 태그로 하드 리셋
        result = subprocess.run(
            f"git reset --hard {target}",
            shell=True, capture_output=True,
            text=True, cwd=self.repo_path
        )
        
        # 스태시 복원
        subprocess.run(
            "git stash pop",
            shell=True, cwd=self.repo_path
        )
        
        return {
            "success": result.returncode == 0,
            "restored_to": target,
            "output": result.stdout
        }
```

---

# 결론: 즉시 적용 가능한 TOP 5 이론/패턴

---

## 비교 분석표

| 이론/패턴 | Branch | 적용 영역 | 난이도 | MVP 필수도 |
|-----------|--------|-----------|--------|-----------|
| **Agent Loop + 안전 메커니즘** | 5.1 | 핵심 실행 엔진 | 보통 | ★★★★★ |
| **상태 머신 (FSM)** | 5.2 | 워크플로우 상태 관리 | 보통 | ★★★★★ |
| **Command 패턴 + 롤백** | 5.2 | 안전 실행/복원 | 보통 | ★★★★☆ |
| **Structured Output + 재시도** | 5.1 | LLM 출력 신뢰성 | 쉬움 | ★★★★☆ |
| **관찰자 패턴 (EventBus)** | 5.2 | 감사 로그/모니터링 | 쉬움 | ★★★☆☆ |

---

## TOP 5: 즉시 적용 가능한 패턴

### 1위. Agent Loop + 무한 루프 방지 [난이도: 보통]

**왜 1위인가**: 이 제품의 심장부. 없으면 제품이 없는 것과 같습니다.

핵심 구현 포인트:
```python
# 이 세 줄이 MVP의 생사를 가름
MAX_ITERATIONS = 20          # 하드 리밋
TIMEOUT_SECONDS = 300        # 5분 강제 종료
CONFIRMATION_THRESHOLD = 5   # 5번 도구 실행 시 사용자 확인
```

### 2위. 워크플로우 상태 머신 (FSM) [난이도: 보통]

**왜 2위인가**: "지금 시스템이 뭘 하고 있는지" 항상 알 수 있어야 합니다. 디버깅, 재시작, 롤백의 기반.

```python
# 핵심 상태 전이
idle → planning → plan_review → executing → completed
                              ↘ failed → rolling_back → rolled_back
```

### 3위. Command 패턴 기반 롤백 [난이도: 보통]

**왜 3위인가**: 로컬 실행의 가장 큰 리스크는 "되돌릴 수 없는 실수". Git + Command 패턴으로 완벽 대응.

```python
history = CommandHistory()
checkpoint = history.create_checkpoint()

try:
    history.execute(FileCreateCommand("config.yaml", content))
    history.execute(GitCommitCommand(".", "auto commit"))
except Exception:
    history.rollback_to_checkpoint(checkpoint)  # 원자적 롤백
```

### 4위. Structured Output + Pydantic 재시도 [난이도: 쉬움]

**왜 4위인가**: LLM은 항상 잘못된 JSON을 반환할 수 있습니다. 재시도 전략 없는 파서는 프로덕션에서 반드시 실패.

```python
# 3번 재시도, 매번 오류 피드백 포함
plan = parser.parse_with_retry(WorkflowPlan, prompt, max_retries=3)
```

### 5위. EventBus (관찰자 패턴) [난이도: 쉬움]

**왜 5위인가**: 감사 로그와 실시간 피드백은 1인 개발자 도구의 신뢰성 핵심. 구현이 쉽고 효과가 큽니다.

---

## PRD.md에 반영할 기술 기반 원칙

```markdown
## 기술 아키텍처 원칙 (PRD 반영)

### 원칙 1: Safety-First Agent Loop
- 모든 에이전트 실행은 max_iterations=20, timeout=300s 하드 리밋 적용
- 5회 이상 자동 도구 실행 시 사용자 확인 인터럽트 의무화
- 무한 루프 패턴 감지 시 즉시 중단 (최근 6회 패턴 비교)

### 원칙 2: Explicit State Machine
- 워크플로우 상태는 FSM으로 명시적 관리
- 허용되지 않은 상태 전이는 예외 발생 (암묵적 전이 금지)
- 상태 전이 이력 100% 로깅

### 원칙 3: Atomic Rollback
- 모든 실행 단계는 Command 패턴으로 구현 (undo 의무)
- 실행 전 Git 스냅샷 자동 생성
- 실패 시 마지막 안전 체크포인트로 자동 롤백 옵션 제공

### 원칙 4: Validated Structured I/O
- LLM 출력은 Pydantic 모델로 100% 검증
- 검증 실패 시 최대 3회 재시도 (오류 컨텍스트 포함)
- YAML 플랜은 실행 전 스키마 검증 필수

### 원칙 5: Observable System
- EventBus로 모든 시스템 이벤트 발행
- audit.jsonl 감사 로그 자동 기록 (삭제 불가)
- 실시간 진행상황은 이벤트 구독으로 표시 (UI 분리)

### 원칙 6: Layered LLM Strategy
- 복잡 추론/Tool Use → Claude Opus (API)
- 단순 작업/빠른 응답 → Claude Haiku (비용 최적화)
- 오프라인/반복 작업 → Ollama 로컬 LLM (폴백)

### 원칙 7: Defensive by Default
- 모든 쉘 명령어는 위험 패턴 블랙리스트 검사
- 파일 시스템 접근은 허용 디렉토리 화이트리스트
- 계약 프로그래밍(전제/사후조건)으로 API 경계 보호
```

---

## 6개월 MVP 구현 로드맵 (이론 → 코드)

```
Phase 1 (M1-2): 핵심 기반
  ├── WorkflowStateMachine (FSM)       ← 2위 패턴
  ├── AgentLoop + 안전 메커니즘         ← 1위 패턴
  └── StructuredOutputParser           ← 4위 패턴

Phase 2 (M3-4): 안전 시스템
  ├── CommandHistory + Rollback        ← 3위 패턴
  ├── SafeExecutor (방어적 프로그래밍)
  └── EventBus + 감사 로그             ← 5위 패턴

Phase 3 (M5-6): 확장 및 통합
  ├── LLMRouter (Ollama 폴백)
  ├── MCP 서버 노출
  └── Pipeline 스트리밍 실행
```

이 7가지 원칙과 5가지 패턴이 PRD.md의 "기술 아키텍처" 섹션 뼈대가 되어야 합니다. 특히 **Safety-First Agent Loop**와 **Atomic Rollback**은 1인 개발자가 로컬 자동화 도구를 신뢰할 수 있게 만드는 최우선 요소입니다.