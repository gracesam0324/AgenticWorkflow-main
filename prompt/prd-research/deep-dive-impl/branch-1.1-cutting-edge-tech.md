# Core Tech Research: AI Agentic Workflow Automation System

## BRANCH 1.1: 공격적 기술 선택 (Cutting Edge Implementation)

---

### 1. Claude SDK 최신 활용법

#### 1.1 최신 API 패턴 (tool_use, streaming, extended thinking)

```python
# anthropic >= 0.40.0 기준
import anthropic
from anthropic.types import ToolUseBlock, TextBlock

client = anthropic.Anthropic()

# Tool Use 패턴 - 구조화된 액션 정의
tools = [
    {
        "name": "execute_shell",
        "description": "로컬 셸 명령어 실행",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "실행할 명령어"},
                "working_dir": {"type": "string", "description": "작업 디렉토리"},
                "timeout": {"type": "integer", "description": "타임아웃(초)", "default": 30}
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "파일 읽기",
        "input_schema": {
            "type": "object", 
            "properties": {
                "path": {"type": "string"},
                "encoding": {"type": "string", "default": "utf-8"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "파일 쓰기",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "enum": ["write", "append"], "default": "write"}
            },
            "required": ["path", "content"]
        }
    }
]

# Streaming 응답 처리
def stream_with_tools(messages: list, system: str) -> str:
    full_response = ""
    tool_uses = []
    
    with client.messages.stream(
        model="claude-opus-4-5",
        max_tokens=8096,
        system=system,
        tools=tools,
        messages=messages
    ) as stream:
        for event in stream:
            if hasattr(event, 'type'):
                if event.type == 'content_block_delta':
                    if hasattr(event.delta, 'text'):
                        full_response += event.delta.text
                        print(event.delta.text, end='', flush=True)
                elif event.type == 'content_block_start':
                    if hasattr(event.content_block, 'type'):
                        if event.content_block.type == 'tool_use':
                            tool_uses.append({
                                'id': event.content_block.id,
                                'name': event.content_block.name,
                                'input': {}
                            })
    
    return full_response, tool_uses
```

#### 1.2 Agent Loop 구현

핵심 개념: Claude가 스스로 tool_use → 결과 수신 → 다음 판단을 반복하는 루프

```python
import asyncio
from dataclasses import dataclass, field
from typing import Any
import anthropic

@dataclass
class AgentState:
    messages: list = field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 20
    tool_results: list = field(default_factory=list)

class ClaudeAgentLoop:
    def __init__(self, tools: list, tool_executor):
        self.client = anthropic.Anthropic()
        self.tools = tools
        self.tool_executor = tool_executor  # 실제 도구 실행 함수
    
    async def run(self, initial_prompt: str, system: str) -> AgentState:
        state = AgentState()
        state.messages = [{"role": "user", "content": initial_prompt}]
        
        while state.iteration < state.max_iterations:
            state.iteration += 1
            
            # Claude 호출
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=8096,
                system=system,
                tools=self.tools,
                messages=state.messages
            )
            
            # 응답을 messages에 추가
            state.messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            # 종료 조건: tool 사용 없이 텍스트만 반환
            if response.stop_reason == "end_turn":
                break
            
            # tool_use 처리
            if response.stop_reason == "tool_use":
                tool_results = []
                
                for block in response.content:
                    if isinstance(block, anthropic.types.ToolUseBlock):
                        # 도구 실행 (승인 UX 포함)
                        result = await self.execute_with_approval(
                            block.name, 
                            block.input,
                            block.id
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                
                # tool 결과를 messages에 추가
                state.messages.append({
                    "role": "user",
                    "content": tool_results
                })
        
        return state
    
    async def execute_with_approval(
        self, 
        tool_name: str, 
        tool_input: dict,
        tool_id: str
    ) -> Any:
        """단계별 승인 UX - 핵심 기능"""
        from rich.console import Console
        from rich.panel import Panel
        from rich.syntax import Syntax
        import json
        
        console = Console()
        
        # 실행 예정 액션 표시
        console.print(Panel(
            Syntax(json.dumps(tool_input, indent=2, ensure_ascii=False), "json"),
            title=f"[yellow]승인 필요: {tool_name}[/yellow]",
            border_style="yellow"
        ))
        
        # 대화형 승인
        choice = input("실행하시겠습니까? [y/n/s(kip)/q(uit)]: ").strip().lower()
        
        if choice == 'q':
            raise SystemExit("사용자가 워크플로우를 중단했습니다.")
        elif choice in ('n', 's'):
            return {"status": "skipped", "reason": "user_rejected"}
        
        # 실제 실행
        return await self.tool_executor(tool_name, tool_input)
```

#### 1.3 Multi-turn Conversation 관리 (Context Window 최적화)

```python
from collections import deque
import tiktoken  # Claude용 토큰 카운팅

class ConversationManager:
    """슬라이딩 윈도우 방식의 대화 기록 관리"""
    
    def __init__(self, max_tokens: int = 150_000):
        self.messages = []
        self.max_tokens = max_tokens
        self.system_summary = ""  # 압축된 이전 컨텍스트
    
    def add_message(self, role: str, content: str | list):
        self.messages.append({"role": role, "content": content})
        self._trim_if_needed()
    
    def _estimate_tokens(self) -> int:
        """간략한 토큰 추정 (문자수 기반)"""
        total = 0
        for msg in self.messages:
            if isinstance(msg['content'], str):
                total += len(msg['content']) // 4
            elif isinstance(msg['content'], list):
                for block in msg['content']:
                    if isinstance(block, dict) and 'text' in block:
                        total += len(block['text']) // 4
        return total
    
    def _trim_if_needed(self):
        """오래된 메시지 요약 후 압축"""
        while self._estimate_tokens() > self.max_tokens and len(self.messages) > 4:
            # 처음 2개 메시지(user+assistant 쌍) 요약
            old_messages = self.messages[:2]
            summary = self._summarize_messages(old_messages)
            
            # 시스템 요약에 누적
            self.system_summary += f"\n[이전 대화 요약]: {summary}"
            
            # 원본 제거
            self.messages = self.messages[2:]
    
    def _summarize_messages(self, messages: list) -> str:
        """Claude를 사용해 대화 압축 (비용 최적화: Haiku 사용)"""
        client = anthropic.Anthropic()
        content = "\n".join([
            f"{m['role']}: {m['content'] if isinstance(m['content'], str) else str(m['content'])}"
            for m in messages
        ])
        
        response = client.messages.create(
            model="claude-haiku-4-5",  # 비용 최적화
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"다음 대화를 3줄 이내로 요약하세요:\n{content}"
            }]
        )
        return response.content[0].text
    
    def get_messages_for_api(self) -> list:
        return self.messages.copy()
```

---

### 2. YAML 워크플로우 엔진 구현

#### 2.1 YAML → Pydantic 모델 자동 파싱

```python
# workflow_models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, Any
from enum import Enum
import yaml

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class RetryConfig(BaseModel):
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    on_errors: list[str] = Field(default_factory=lambda: ["TimeoutError", "ConnectionError"])

class StepDefinition(BaseModel):
    id: str
    name: str
    type: Literal["shell", "python", "file", "ai", "http"]
    action: str
    args: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    timeout: int = 60  # seconds
    on_failure: Literal["stop", "continue", "rollback"] = "stop"
    rollback_action: Optional[str] = None
    requires_approval: bool = False
    condition: Optional[str] = None  # Python 표현식 (예: "{{ prev_step.exit_code }} == 0")
    
    @validator('id')
    def id_must_be_slug(cls, v):
        import re
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError('Step ID는 소문자, 숫자, -, _만 허용됩니다')
        return v

class WorkflowDefinition(BaseModel):
    version: str = "1.0"
    name: str
    description: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    
    # 전역 설정
    default_timeout: int = 300
    max_parallelism: int = 4
    working_directory: str = "."
    environment: dict[str, str] = Field(default_factory=dict)
    
    steps: list[StepDefinition]
    
    @validator('steps')
    def validate_no_circular_deps(cls, steps):
        """순환 의존성 검사"""
        step_ids = {s.id for s in steps}
        
        # 모든 depends_on이 유효한 step_id 참조인지 확인
        for step in steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(f"Step '{step.id}'이 존재하지 않는 '{dep}'에 의존합니다")
        
        # 순환 참조 DFS 탐지
        def has_cycle(step_id: str, visited: set, rec_stack: set) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next(s for s in steps if s.id == step_id)
            for dep in step.depends_on:
                if dep not in visited:
                    if has_cycle(dep, visited, rec_stack):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.discard(step_id)
            return False
        
        visited, rec_stack = set(), set()
        for step in steps:
            if step.id not in visited:
                if has_cycle(step.id, visited, rec_stack):
                    raise ValueError("워크플로우에 순환 의존성이 있습니다")
        
        return steps

def load_workflow(yaml_path: str) -> WorkflowDefinition:
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return WorkflowDefinition(**data)
```

실제 YAML 예시:
```yaml
# workflow.yaml
version: "1.0"
name: "데이터 파이프라인 자동화"
description: "CSV 파일을 정제하고 분석 보고서 생성"
default_timeout: 300
max_parallelism: 2

steps:
  - id: validate_input
    name: "입력 파일 검증"
    type: shell
    action: "python validate.py --file {{ input_file }}"
    timeout: 30
    requires_approval: false
    on_failure: stop

  - id: clean_data
    name: "데이터 정제"
    type: python
    action: "data_cleaner.clean"
    args:
      input: "{{ input_file }}"
      output: "cleaned_data.csv"
      rules: ["remove_nulls", "normalize_dates"]
    depends_on: [validate_input]
    retry:
      max_attempts: 2
      delay_seconds: 5.0

  - id: analyze_parallel_a
    name: "통계 분석"
    type: python
    action: "analyzer.statistical_analysis"
    depends_on: [clean_data]

  - id: analyze_parallel_b
    name: "시각화 생성"
    type: shell
    action: "python visualize.py cleaned_data.csv"
    depends_on: [clean_data]

  - id: generate_report
    name: "보고서 생성 (AI)"
    type: ai
    action: "generate_summary_report"
    args:
      template: "report_template.md"
    depends_on: [analyze_parallel_a, analyze_parallel_b]
    requires_approval: true
```

#### 2.2 DAG 실행 엔진 (async/await)

```python
# dag_engine.py
import asyncio
from collections import defaultdict
from typing import Callable, Coroutine
import time

class DAGExecutor:
    def __init__(
        self, 
        workflow: WorkflowDefinition,
        step_runner: Callable,
        on_step_start: Callable = None,
        on_step_complete: Callable = None,
        on_step_fail: Callable = None
    ):
        self.workflow = workflow
        self.step_runner = step_runner
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete
        self.on_step_fail = on_step_fail
        
        # 실행 상태 추적
        self.step_status: dict[str, StepStatus] = {
            s.id: StepStatus.PENDING for s in workflow.steps
        }
        self.step_results: dict[str, Any] = {}
        self.step_start_times: dict[str, float] = {}
        
    def _build_dependency_graph(self) -> dict[str, set]:
        """역방향 의존성 그래프 구성 (누가 나를 기다리는가)"""
        graph = defaultdict(set)
        for step in self.workflow.steps:
            for dep in step.depends_on:
                graph[dep].add(step.id)
        return graph
    
    def _get_ready_steps(self) -> list[StepDefinition]:
        """실행 준비된 스텝 반환 (모든 의존성 완료)"""
        ready = []
        for step in self.workflow.steps:
            if self.step_status[step.id] != StepStatus.PENDING:
                continue
            
            # 모든 의존성이 완료됐는지 확인
            all_deps_done = all(
                self.step_status.get(dep) == StepStatus.COMPLETED
                for dep in step.depends_on
            )
            
            if all_deps_done:
                # 조건 평가
                if step.condition and not self._evaluate_condition(step.condition):
                    self.step_status[step.id] = StepStatus.SKIPPED
                    continue
                ready.append(step)
        
        return ready
    
    def _evaluate_condition(self, condition: str) -> bool:
        """조건 표현식 평가 (제한된 안전 환경)"""
        # Jinja2 스타일 변수를 Python 변수로 치환
        import re
        condition = re.sub(
            r'\{\{\s*(\w+)\.(\w+)\s*\}\}',
            lambda m: f'step_results.get("{m.group(1)}", {{}}).get("{m.group(2)}")',
            condition
        )
        
        # 제한된 eval 환경
        safe_globals = {"step_results": self.step_results, "__builtins__": {}}
        try:
            return bool(eval(condition, safe_globals))
        except Exception:
            return True  # 평가 실패시 실행
    
    async def execute_step_with_retry(self, step: StepDefinition) -> Any:
        """재시도 로직이 포함된 스텝 실행"""
        retry_cfg = step.retry
        last_error = None
        
        for attempt in range(retry_cfg.max_attempts):
            try:
                self.step_status[step.id] = StepStatus.RUNNING
                self.step_start_times[step.id] = time.time()
                
                if self.on_step_start:
                    await self.on_step_start(step, attempt)
                
                # 타임아웃 적용
                result = await asyncio.wait_for(
                    self.step_runner(step, self.step_results),
                    timeout=step.timeout
                )
                
                self.step_status[step.id] = StepStatus.COMPLETED
                self.step_results[step.id] = result
                
                if self.on_step_complete:
                    await self.on_step_complete(step, result)
                
                return result
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Step '{step.id}' 타임아웃 ({step.timeout}초)")
            except Exception as e:
                last_error = e
            
            # 재시도 전 대기 (지수 백오프)
            if attempt < retry_cfg.max_attempts - 1:
                delay = retry_cfg.delay_seconds * (retry_cfg.backoff_multiplier ** attempt)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.step_status[step.id] = StepStatus.FAILED
        if self.on_step_fail:
            await self.on_step_fail(step, last_error)
        
        if step.on_failure == "rollback":
            await self._execute_rollback(step)
        elif step.on_failure == "stop":
            raise last_error
        
        return None
    
    async def _execute_rollback(self, failed_step: StepDefinition):
        """롤백 실행 - 완료된 스텝을 역순으로"""
        completed_steps = [
            s for s in self.workflow.steps
            if self.step_status[s.id] == StepStatus.COMPLETED and s.rollback_action
        ]
        
        for step in reversed(completed_steps):
            try:
                rollback_step = StepDefinition(
                    id=f"{step.id}_rollback",
                    name=f"롤백: {step.name}",
                    type=step.type,
                    action=step.rollback_action,
                    timeout=step.timeout
                )
                await self.step_runner(rollback_step, self.step_results)
            except Exception as e:
                print(f"롤백 실패 ({step.id}): {e}")
    
    async def run(self) -> dict:
        """DAG 전체 실행"""
        semaphore = asyncio.Semaphore(self.workflow.max_parallelism)
        
        async def run_with_semaphore(step):
            async with semaphore:
                return await self.execute_step_with_retry(step)
        
        while True:
            ready_steps = self._get_ready_steps()
            
            if not ready_steps:
                # 완료 여부 확인
                pending = [
                    s for s in self.workflow.steps 
                    if self.step_status[s.id] == StepStatus.PENDING
                ]
                if not pending:
                    break
                
                # 실패로 인해 실행 불가능한 상태
                failed = [
                    s.id for s in self.workflow.steps 
                    if self.step_status[s.id] == StepStatus.FAILED
                ]
                if failed:
                    raise RuntimeError(f"워크플로우 중단 (실패한 스텝: {failed})")
                
                await asyncio.sleep(0.1)  # 실행 중인 스텝 대기
                continue
            
            # 준비된 스텝들 병렬 실행
            tasks = [run_with_semaphore(step) for step in ready_steps]
            # 먼저 상태를 RUNNING으로 마크해 중복 실행 방지
            for step in ready_steps:
                self.step_status[step.id] = StepStatus.RUNNING
            
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return self.step_results
```

---

### 3. 로컬 프로세스 안전 실행

#### 3.1 subprocess 샌드박싱

```python
# safe_executor.py
import asyncio
import os
import sys
import resource  # Unix 전용 (Linux/macOS)
import signal
from pathlib import Path
from dataclasses import dataclass

@dataclass
class ExecutionLimits:
    max_cpu_seconds: int = 60
    max_memory_mb: int = 512
    max_file_size_mb: int = 100
    max_open_files: int = 50
    allowed_paths: list[str] = None  # None이면 cwd만 허용
    network_allowed: bool = False
    timeout_seconds: int = 60

@dataclass 
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    elapsed_seconds: float
    killed: bool = False
    kill_reason: str = ""

class SafeSubprocessExecutor:
    def __init__(self, limits: ExecutionLimits = None):
        self.limits = limits or ExecutionLimits()
    
    def _preexec_fn(self):
        """자식 프로세스 제한 설정 (Unix 전용)"""
        if sys.platform != 'win32':
            # CPU 시간 제한
            resource.setrlimit(
                resource.RLIMIT_CPU, 
                (self.limits.max_cpu_seconds, self.limits.max_cpu_seconds + 5)
            )
            # 메모리 제한
            memory_bytes = self.limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_AS,
                (memory_bytes, memory_bytes)
            )
            # 파일 크기 제한
            file_bytes = self.limits.max_file_size_mb * 1024 * 1024
            resource.setrlimit(
                resource.RLIMIT_FSIZE,
                (file_bytes, file_bytes)
            )
            # 파일 디스크립터 제한
            resource.setrlimit(
                resource.RLIMIT_NOFILE,
                (self.limits.max_open_files, self.limits.max_open_files + 10)
            )
            # 새 프로세스 그룹 생성 (킬 시 자식도 함께)
            os.setsid()
    
    async def run(
        self, 
        command: str | list,
        working_dir: str = ".",
        env_override: dict = None,
        input_data: str = None
    ) -> ExecutionResult:
        import time
        
        # 안전한 환경 변수 구성
        safe_env = self._build_safe_env(env_override)
        
        # 명령어 정규화
        if isinstance(command, str):
            # shell=True는 보안상 위험 - 리스트로 파싱
            import shlex
            cmd_list = shlex.split(command)
        else:
            cmd_list = command
        
        # 허용된 명령어 검증
        self._validate_command(cmd_list)
        
        start_time = time.monotonic()
        
        process = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if input_data else None,
            cwd=working_dir,
            env=safe_env,
            preexec_fn=self._preexec_fn if sys.platform != 'win32' else None
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=self.limits.timeout_seconds
            )
            elapsed = time.monotonic() - start_time
            
            return ExecutionResult(
                exit_code=process.returncode,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                elapsed_seconds=elapsed
            )
            
        except asyncio.TimeoutError:
            # 프로세스 그룹 전체 종료
            try:
                if sys.platform != 'win32':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            
            await process.wait()
            elapsed = time.monotonic() - start_time
            
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"타임아웃: {self.limits.timeout_seconds}초 초과",
                elapsed_seconds=elapsed,
                killed=True,
                kill_reason="timeout"
            )
    
    def _validate_command(self, cmd_list: list):
        """위험한 명령어 차단"""
        BLOCKED_COMMANDS = {
            'rm', 'rmdir', 'dd', 'mkfs', 'fdisk', 'format',
            'shutdown', 'reboot', 'halt', 'poweroff',
            'chmod', 'chown', 'sudo', 'su',
            'curl', 'wget', 'nc', 'netcat',  # 네트워크 (옵션)
        }
        
        if cmd_list and cmd_list[0] in BLOCKED_COMMANDS:
            if not self.limits.network_allowed and cmd_list[0] in {'curl', 'wget'}:
                raise PermissionError(f"명령어 '{cmd_list[0]}' 실행 차단됨")
        
        # 경로 탈출 방지
        for arg in cmd_list:
            if '../' in arg or arg.startswith('/etc') or arg.startswith('/sys'):
                raise PermissionError(f"위험한 경로 접근 차단: {arg}")
    
    def _build_safe_env(self, override: dict = None) -> dict:
        """최소한의 안전한 환경 변수"""
        safe_env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin',
            'HOME': os.path.expanduser('~'),
            'LANG': 'en_US.UTF-8',
            'PYTHONPATH': os.environ.get('PYTHONPATH', ''),
        }
        if override:
            # 위험한 변수 필터링
            BLOCKED_ENV = {'LD_PRELOAD', 'LD_LIBRARY_PATH', 'DYLD_INSERT_LIBRARIES'}
            safe_override = {k: v for k, v in override.items() if k not in BLOCKED_ENV}
            safe_env.update(safe_override)
        return safe_env
```

---

### 4. 상태 관리 구현

#### 4.1 SQLite + SQLAlchemy (Event Sourcing 패턴)

```python
# state_manager.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, JSON, DateTime, Enum as SAEnum
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="running")  
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict)  # 초기 변수들
    yaml_snapshot: Mapped[str] = mapped_column(String)  # 실행 당시 YAML 내용

class StepEvent(Base):
    """Event Sourcing: 모든 스텝 이벤트를 이벤트 로그로 저장"""
    __tablename__ = "step_events"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(String)
    step_id: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String)  # started/completed/failed/retried/skipped
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # 결과, 에러 등

class StateManager:
    def __init__(self, db_path: str = "~/.local/share/autoflow/state.db"):
        db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    
    async def initialize(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def create_run(self, workflow: WorkflowDefinition, context: dict) -> str:
        async with AsyncSession(self.engine) as session:
            run = WorkflowRun(
                workflow_name=workflow.name,
                context=context,
                yaml_snapshot=workflow.model_dump_json()
            )
            session.add(run)
            await session.commit()
            return run.id
    
    async def record_event(
        self, 
        run_id: str, 
        step_id: str, 
        event_type: str,
        payload: dict = None
    ):
        async with AsyncSession(self.engine) as session:
            event = StepEvent(
                run_id=run_id,
                step_id=step_id,
                event_type=event_type,
                payload=payload or {}
            )
            session.add(event)
            await session.commit()
    
    async def get_resume_state(self, run_id: str) -> dict:
        """중단된 워크플로우 재개를 위한 상태 복원"""
        async with AsyncSession(self.engine) as session:
            from sqlalchemy import select
            
            # 가장 최근 이벤트 기준으로 각 스텝 상태 재구성
            events = await session.execute(
                select(StepEvent)
                .where(StepEvent.run_id == run_id)
                .order_by(StepEvent.timestamp)
            )
            
            step_states = {}
            step_results = {}
            
            for event in events.scalars():
                step_states[event.step_id] = event.event_type
                if event.event_type == "completed":
                    step_results[event.step_id] = event.payload.get("result")
            
            return {
                "step_states": step_states,
                "step_results": step_results
            }
```

---

### 5. MCP 서버 구현

```python
# mcp_server.py
# pip install mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
import asyncio
import json

app = Server("autoflow-mcp")

# 사용 가능한 도구 등록
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="run_workflow",
            description="YAML 워크플로우 파일 실행",
            inputSchema={
                "type": "object",
                "properties": {
                    "yaml_path": {"type": "string", "description": "워크플로우 YAML 경로"},
                    "variables": {"type": "object", "description": "변수 오버라이드"},
                    "dry_run": {"type": "boolean", "description": "실제 실행 없이 플랜만 확인"}
                },
                "required": ["yaml_path"]
            }
        ),
        Tool(
            name="list_workflows",
            description="저장된 워크플로우 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "default": "~/.autoflow/workflows"}
                }
            }
        ),
        Tool(
            name="get_workflow_status",
            description="워크플로우 실행 상태 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"}
                },
                "required": ["run_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "run_workflow":
        yaml_path = arguments["yaml_path"]
        variables = arguments.get("variables", {})
        dry_run = arguments.get("dry_run", False)
        
        try:
            workflow = load_workflow(yaml_path)
            
            if dry_run:
                plan = generate_execution_plan(workflow)
                return [TextContent(type="text", text=json.dumps(plan, ensure_ascii=False, indent=2))]
            
            # 실제 실행
            executor = DAGExecutor(workflow, step_runner=create_step_runner())
            results = await executor.run()
            
            return [TextContent(
                type="text", 
                text=json.dumps({"status": "completed", "results": results}, ensure_ascii=False, indent=2)
            )]
        except Exception as e:
            return [TextContent(type="text", text=f"오류: {str(e)}")]
    
    elif name == "list_workflows":
        directory = os.path.expanduser(arguments.get("directory", "~/.autoflow/workflows"))
        workflows = []
        
        for yaml_file in Path(directory).glob("*.yaml"):
            try:
                wf = load_workflow(str(yaml_file))
                workflows.append({
                    "name": wf.name,
                    "file": str(yaml_file),
                    "steps": len(wf.steps)
                })
            except Exception:
                pass
        
        return [TextContent(type="text", text=json.dumps(workflows, ensure_ascii=False, indent=2))]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Branch 1.1 실제 유사 도구 분석

| 도구 | 기술 스택 | 특징 | 참고점 |
|------|-----------|------|--------|
| **OpenDevin** | Python + React, Docker 샌드박스, Claude/GPT 지원 | 완전 자율 에이전트, 브라우저 조작 | 너무 복잡 - 팀 프로젝트 규모 |
| **Aider** | Python, Claude/GPT, Git 통합 | 코드 편집 특화, TDD 방식 | Git 통합 패턴 참고 가능 |
| **AutoGen** | Python, 멀티에이전트 대화 | 에이전트 간 협업 | 대화 관리 패턴 참고 |

---
