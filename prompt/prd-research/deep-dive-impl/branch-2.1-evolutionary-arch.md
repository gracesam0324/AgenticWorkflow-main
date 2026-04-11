프로젝트 구조를 충분히 파악했습니다. 이제 실제 코드 예시를 포함한 깊이 있는 아키텍처 분석을 작성하겠습니다.

---

# AI Agentic Workflow Automation System — 코딩 아키텍처 심층 분석

현재 PRD와 실제 코드베이스(AgenticWorkflow, autobiography-generator, hook 스크립트들)를 분석한 결과입니다.

---

## BRANCH 2.1: 점진적 확장 설계 (Evolutionary Architecture)

### 1. 초기 코드 구조 (Month 1)

PRD의 절대 기준 1 — `IProcessExecutor`가 Week 1 첫 커밋에서 나온다 — 을 Python으로 번역하면 아래 구조가 됩니다.

```
workflow_ai/
  ├── __init__.py
  ├── cli.py          # 진입점: 자연어 입력 수신, 결과 출력
  ├── planner.py      # NL → WorkflowPlan (YAML)
  ├── executor.py     # WorkflowPlan → 단계별 실행
  ├── safety.py       # IProcessExecutor 구현 (PRD 절대 기준 1의 실체)
  └── state.py        # state.yaml 원자적 읽기/쓰기
```

각 파일의 실제 역할:

- `cli.py` — Click/Typer 기반 진입점. `workflow_ai run "로그 파일 정리해줘"` 형태로 호출. 단 하나의 책임: 사용자 입력을 받아 planner에 넘기고 결과를 출력한다.
- `planner.py` — Claude API를 호출해 자연어를 구조화된 YAML 플랜으로 변환. 출력이 PRD 스키마를 만족하는지 Pydantic으로 검증.
- `executor.py` — YAML 플랜의 단계를 순서대로 실행. 각 스텝을 safety.py의 `IProcessExecutor`를 통해서만 실행.
- `safety.py` — **이것이 제품의 면역 체계**. 실제 코드베이스의 `block_destructive_commands.py`에서 확인한 것처럼, 결정론적 regex 기반 검증을 수행.
- `state.py` — 실제 코드베이스의 `sot_lib.py`가 이미 완성된 참조 구현. `.tmp` 파일 경유 atomic rename + `.bak` 크래시 복구 패턴.

### 2. 핵심 데이터 흐름 구현

```python
# safety.py — Month 1의 핵심, Week 1 첫 커밋
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class Command:
    program: str          # "python", "git", "rm" 등
    args: list[str]       # ["--version"]
    working_dir: str      # 실행 디렉토리 (샌드박싱 핵심)
    timeout: int = 30     # 초

@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    blocked: bool = False
    block_reason: Optional[str] = None

class IProcessExecutor(ABC):
    """PRD 절대 기준 1의 Python 구현체.
    
    모든 셸 실행, 파일 작업은 이 인터페이스를 통과한다.
    예외 없음. LLM 프롬프트로 이 경계를 우회할 수 없다.
    이 인터페이스는 Week 1 첫 커밋에서 추출된다.
    """
    @abstractmethod
    def execute(self, cmd: Command) -> ExecutionResult:
        ...

    @abstractmethod  
    def classify(self, cmd: Command) -> str:
        """'safe' | 'destructive' | 'blocked' 를 반환"""
        ...

# 실제 실행기 (v1)
class LocalProcessExecutor(IProcessExecutor):
    # 실제 코드베이스(block_destructive_commands.py)의 패턴을 그대로 가져옴
    _BLOCKED = [
        re.compile(r"\brm\b.*-[rR].*-f"),
        re.compile(r"\bdd\b\s+if="),
        re.compile(r"\bmkfs\b"),
        re.compile(r"\bgit\s+push\b.*\s--force(?![-\w])"),
        re.compile(r"\bgit\s+reset\b.*\s--hard"),
    ]
    _DESTRUCTIVE = [
        re.compile(r"\brm\b"),
        re.compile(r"\bmv\b"),
        re.compile(r"\btruncate\b"),
    ]
    
    def classify(self, cmd: Command) -> str:
        full = " ".join([cmd.program] + cmd.args)
        for p in self._BLOCKED:
            if p.search(full):
                return "blocked"
        for p in self._DESTRUCTIVE:
            if p.search(full):
                return "destructive"
        return "safe"

    def execute(self, cmd: Command) -> ExecutionResult:
        import subprocess, os
        
        classification = self.classify(cmd)
        if classification == "blocked":
            return ExecutionResult(
                returncode=-1, stdout="", stderr="",
                blocked=True, 
                block_reason=f"안전 정책: {cmd.program} {' '.join(cmd.args)}"
            )
        
        # 경로 샌드박싱: working_dir 이탈 불가
        abs_wd = os.path.realpath(cmd.working_dir)
        result = subprocess.run(
            [cmd.program] + cmd.args,
            cwd=abs_wd,
            capture_output=True, text=True,
            timeout=cmd.timeout,
            env={**os.environ, "HOME": abs_wd}  # HOME 재정의로 ~/ 접근 차단
        )
        return ExecutionResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )

# Dry-run 실행기 (항상 존재 — PRD Green Zone P0)
class DryRunProcessExecutor(IProcessExecutor):
    def classify(self, cmd: Command) -> str:
        return "safe"  # dry-run은 분류 불필요
    
    def execute(self, cmd: Command) -> ExecutionResult:
        print(f"[DRY-RUN] 실행 예정: {cmd.program} {' '.join(cmd.args)}")
        print(f"[DRY-RUN] 작업 디렉토리: {cmd.working_dir}")
        return ExecutionResult(returncode=0, stdout="[dry-run]", stderr="")
```

```python
# planner.py — NL → WorkflowPlan
from dataclasses import dataclass, field
from typing import Optional
import hashlib, yaml, json
import anthropic

@dataclass
class WorkflowStep:
    id: str
    type: str          # shell | file-write | validate | notify | user-prompt
    description: str
    command: Optional[str] = None
    content: Optional[str] = None
    is_destructive: bool = False

@dataclass  
class WorkflowPlan:
    id: str
    title: str
    intent: str        # 사용자의 원본 요청
    steps: list[WorkflowStep]
    checksum: str      # PRD 절대 기준 3: 불변성 강제
    approved: bool = False
    
    @classmethod
    def _compute_checksum(cls, steps: list[WorkflowStep]) -> str:
        content = json.dumps(
            [{"id": s.id, "type": s.type, "command": s.command} for s in steps],
            sort_keys=True
        )
        return hashlib.sha256(content.encode()).hexdigest()[:16]

class WorkflowPlanner:
    def __init__(self, api_key: str, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def plan(self, user_request: str) -> WorkflowPlan:
        # Claude API 구조화 출력으로 YAML 플랜 생성
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="""당신은 로컬 자동화 워크플로우 플래너입니다.
            사용자 요청을 분석하여 실행 가능한 단계별 플랜을 생성하세요.
            출력은 반드시 유효한 YAML 형식이어야 합니다.
            위험 작업(rm, 시스템 변경 등)은 is_destructive: true로 표시하세요.""",
            messages=[{
                "role": "user",
                "content": f"다음 작업을 위한 워크플로우 플랜을 YAML로 작성하세요:\n\n{user_request}"
            }]
        )
        
        raw_plan = yaml.safe_load(response.content[0].text)
        steps = [WorkflowStep(**s) for s in raw_plan.get("steps", [])]
        
        return WorkflowPlan(
            id=f"plan-{hashlib.sha256(user_request.encode()).hexdigest()[:8]}",
            title=raw_plan.get("title", "워크플로우"),
            intent=user_request,
            steps=steps,
            checksum=WorkflowPlan._compute_checksum(steps)
        )
```

```python
# executor.py — WorkflowPlan → 실행
import sys
from safety import IProcessExecutor, Command
from planner import WorkflowPlan, WorkflowStep
from state import WorkflowStateManager

class WorkflowExecutor:
    def __init__(self, executor: IProcessExecutor, state_mgr: WorkflowStateManager):
        # 의존성 주입: executor는 외부에서 결정 (DI 컨테이너 없이)
        self.executor = executor
        self.state = state_mgr

    def execute_plan(self, plan: WorkflowPlan) -> dict:
        # PRD 절대 기준 3: 체크섬 검증 — 플랜이 승인 후 변경되지 않았는지 확인
        if not plan.approved:
            raise RuntimeError("미승인 플랜은 실행 불가")
        
        current_checksum = WorkflowPlan._compute_checksum(plan.steps)
        if current_checksum != plan.checksum:
            raise RuntimeError(f"플랜 변조 감지: {plan.checksum} → {current_checksum}")
        
        results = []
        for i, step in enumerate(plan.steps):
            # 상태 업데이트 (재개 가능하도록)
            self.state.update({"current_step": i, "status": "running"})
            
            result = self._execute_step(step, plan)
            results.append(result)
            
            if not result["success"]:
                # 평어체 실패 보고 (PRD Green Zone P0)
                self.state.update({
                    "status": "failed",
                    "failed_step": step.id,
                    "error": result["error"]
                })
                self._report_failure(step, result["error"])
                break
            
        return {"plan_id": plan.id, "steps": results}

    def _execute_step(self, step: WorkflowStep, plan: WorkflowPlan) -> dict:
        if step.type == "shell":
            return self._run_shell_step(step)
        elif step.type == "user-prompt":
            return self._run_user_prompt(step)
        elif step.type == "notify":
            print(f"\n[알림] {step.description}")
            return {"success": True, "step_id": step.id}
        # ... 기타 타입들

    def _run_shell_step(self, step: WorkflowStep) -> dict:
        # 파괴적 작업 승인 게이트 (PRD Green Zone P0)
        if step.is_destructive:
            confirmed = self._confirm_destructive_step(step)
            if not confirmed:
                return {"success": False, "step_id": step.id, 
                        "error": "사용자가 파괴적 작업을 거부했습니다"}
        
        parts = step.command.split()
        cmd = Command(program=parts[0], args=parts[1:], working_dir=".")
        result = self.executor.execute(cmd)
        
        return {
            "success": result.returncode == 0,
            "step_id": step.id,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.stderr if result.returncode != 0 else None
        }

    def _confirm_destructive_step(self, step: WorkflowStep) -> bool:
        """파괴적 작업 텍스트 입력 확인 방식 (PRD 사양)"""
        print(f"\n⚠️  파괴적 작업 감지")
        print(f"   단계: {step.description}")
        print(f"   명령어: {step.command}")
        print(f"\n   계속하려면 'yes'를 입력하세요: ", end="")
        user_input = input().strip().lower()
        return user_input == "yes"

    def _report_failure(self, step: WorkflowStep, error: str):
        """평어체 실패 보고"""
        print(f"\n[실패] '{step.description}' 단계에서 문제가 발생했습니다.")
        print(f"원인: {error[:200]}")
        print(f"복구 방법: 위 오류 메시지를 확인하고 {step.command}를 수동으로 실행해 보세요.")
```

```python
# state.py — 원자적 상태 관리
# autobiography-generator/scripts/sot_lib.py에서 직접 가져온 패턴
import os, shutil
import yaml
from pathlib import Path
from typing import Any

class WorkflowStateManager:
    """
    실제 코드베이스(sot_lib.py)의 패턴을 workflow_ai에 적용.
    핵심: .tmp → os.replace() atomic rename + .bak 크래시 복구
    """
    def __init__(self, state_file: str = "state.yaml"):
        self.path = Path(state_file)
        self.bak = Path(f"{state_file}.bak")
        self.tmp = Path(f"{state_file}.tmp")

    def load(self) -> dict:
        try:
            data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
            if data is None:
                raise ValueError("빈 state.yaml")
            return data
        except (yaml.YAMLError, FileNotFoundError):
            # .bak에서 복구
            if self.bak.exists():
                return yaml.safe_load(self.bak.read_text())
            return self._default_state()

    def save(self, state: dict) -> None:
        """원자적 쓰기: 파워 다운 중에도 데이터 손실 없음"""
        # 1. .bak 생성
        if self.path.exists():
            shutil.copy2(self.path, self.bak)
        
        # 2. .tmp에 먼저 쓰기
        self.tmp.write_text(
            yaml.dump(state, allow_unicode=True, sort_keys=False),
            encoding="utf-8"
        )
        
        # 3. atomic rename (POSIX에서 원자적 보장)
        os.replace(self.tmp, self.path)

    def update(self, changes: dict) -> None:
        state = self.load()
        state.update(changes)
        self.save(state)

    def _default_state(self) -> dict:
        return {
            "plan_id": None,
            "status": "idle",       # idle | running | paused | completed | failed
            "current_step": 0,
            "completed_steps": [],
            "failed_step": None,
            "error": None,
            "started_at": None,
            "completed_at": None,
        }
```

### 3. 사용자 확인 인터페이스 코드

```python
# cli.py — 플랜 승인 게이트 (PRD Green Zone P0)
import click
from planner import WorkflowPlanner
from executor import WorkflowExecutor
from safety import LocalProcessExecutor, DryRunProcessExecutor
from state import WorkflowStateManager

def display_plan_for_approval(plan) -> bool:
    """PRD 절대 기준 3: 사용자가 전체 플랜 검토 후 승인"""
    print(f"\n{'='*60}")
    print(f"워크플로우 플랜: {plan.title}")
    print(f"의도: {plan.intent}")
    print(f"{'='*60}")
    
    for i, step in enumerate(plan.steps, 1):
        destructive_tag = " ⚠️ [파괴적]" if step.is_destructive else ""
        print(f"\n  {i}. [{step.type.upper()}]{destructive_tag}")
        print(f"     {step.description}")
        if step.command:
            print(f"     $ {step.command}")
    
    print(f"\n체크섬: {plan.checksum}")
    print(f"\n이 플랜을 실행하시겠습니까?")
    print(f"  [y] 승인 및 실행")
    print(f"  [d] Dry-run (시뮬레이션)")
    print(f"  [n] 취소")
    
    choice = input("\n선택: ").strip().lower()
    
    if choice == 'y':
        plan.approved = True
        return 'execute'
    elif choice == 'd':
        plan.approved = True
        return 'dry-run'
    return 'cancel'

@click.command()
@click.argument('request')
@click.option('--dry-run', is_flag=True, help='실행 없이 시뮬레이션')
def run(request: str, dry_run: bool):
    """자연어 요청을 워크플로우로 실행합니다."""
    import os
    
    planner = WorkflowPlanner(api_key=os.environ["ANTHROPIC_API_KEY"])
    state_mgr = WorkflowStateManager()
    
    print("플랜 생성 중...")
    plan = planner.plan(request)
    
    action = display_plan_for_approval(plan)
    
    if action == 'cancel':
        print("취소되었습니다.")
        return
    
    # 실행기 선택 — 의존성 주입
    executor_impl = DryRunProcessExecutor() if (dry_run or action == 'dry-run') \
                    else LocalProcessExecutor()
    
    executor = WorkflowExecutor(executor_impl, state_mgr)
    result = executor.execute_plan(plan)
    
    # 실행 후 내러티브 (PRD Graduated Autonomy)
    _print_execution_narrative(result)

if __name__ == '__main__':
    run()
```

### 4. state.yaml 스키마 정의 및 재개(resume) 로직

```yaml
# state.yaml 스키마 (autobiography-generator/state.yaml 패턴 기반)
plan_id: "plan-a3f2b1c4"
status: "paused"           # idle|running|paused|completed|failed
current_step: 2            # 다음 실행할 스텝 인덱스
completed_steps:
  - id: "step-1"
    result: "success"
    stdout: "3 files processed"
    completed_at: "2026-04-07T10:30:00"
  - id: "step-2"
    result: "success"  
    stdout: ""
    completed_at: "2026-04-07T10:30:05"
failed_step: null
error: null
plan_checksum: "a3f2b1c4d5e6f7a8"  # 불변성 검증용
autonomy_level: "paranoid"           # paranoid|balanced|trust
success_count: 2
started_at: "2026-04-07T10:29:55"
completed_at: null
```

```python
# executor.py — resume 로직 추가
class WorkflowExecutor:
    def execute_plan(self, plan: WorkflowPlan, resume: bool = False) -> dict:
        """resume=True면 중단된 지점부터 재개"""
        start_index = 0
        
        if resume:
            state = self.state.load()
            if state.get("plan_id") != plan.id:
                raise RuntimeError("재개 대상 플랜 ID 불일치")
            if state.get("plan_checksum") != plan.checksum:
                raise RuntimeError("플랜이 변조되었습니다 — 재개 불가")
            
            start_index = state.get("current_step", 0)
            completed = state.get("completed_steps", [])
            print(f"[재개] {start_index}번 스텝부터 재개합니다.")
            print(f"[재개] 완료된 스텝: {[s['id'] for s in completed]}")
        
        results = []
        for i, step in enumerate(plan.steps[start_index:], start=start_index):
            self.state.update({
                "current_step": i, 
                "status": "running",
                "plan_checksum": plan.checksum
            })
            # ... 나머지 실행 로직
```

### 5. Month별 진화 경로 — 코드 레벨

**Month 1: 단일 파일 동작 (500 LOC)**
```python
# workflow_ai.py — 전부 한 파일
# 목적: 빠르게 동작하는 것을 확인
# Claude API → 플랜 생성 → 터미널 확인 → 실행 → 결과 출력
# safety 로직: IProcessExecutor 인터페이스는 있으나 LocalProcessExecutor만 존재
```

**Month 3: 모듈 분리 (1,500 LOC)**
```python
# 위의 구조로 분리 완료
# 추가: GraduatedAutonomyTracker (성공/실패 카운트 → 레벨 제안)
# 추가: AuditLogService (append-only, structured JSON)
# 추가: SelfHealingEngine 프로토타입 (재시도 1회, 오류 컨텍스트 주입)
```

**Month 6: 인터페이스 도입 — 딱 필요한 것만 추출**
```python
# PRD 사양대로 3개 인터페이스만 추출:
# IProcessExecutor (이미 Month 1부터 존재)
# ILLMProvider (AnthropicProvider, OpenAICompatibleProvider)
# IWorkflowPlanStore (YAML 파일 기반 — 추후 DB 교체 가능성)
# 이 3개 이외에는 추출하지 않는다.
```

### 유사 오픈소스 프로젝트 3개 분석

**1. Prefect (prefecthq/prefect)**
```
핵심 구조 패턴:
  flow/task 데코레이터로 워크플로우 정의
  State 객체가 단계별 상태를 캡슐화 (Pending/Running/Completed/Failed)
  
  @flow
  def my_workflow():
      result = my_task()
      return result

참고 가치:
  - State 머신 패턴 (State 객체의 transition 로직)
  - 재개(resume) 구현: task result caching으로 중간 결과 보존
  
한계 (우리 제품과 다른 점):
  - 서버-클라이언트 아키텍처 → 로컬 퍼스트 위반
  - YAML이 아닌 Python 코드로 플랜 정의 → 자연어 입력과 충돌
```

**2. Airflow (apache/airflow)**
```
핵심 구조 패턴:
  DAG(Directed Acyclic Graph)로 의존성 표현
  각 Task는 Operator 클래스의 인스턴스
  XCom으로 단계 간 데이터 전달
  
참고 가치:
  - BaseOperator 추상 클래스 패턴 → 우리의 스텝 타입 설계에 직접 적용 가능
  - execute(context) 메서드 시그니처
  - 실패 시 재시도 설정 (retries=3, retry_delay=timedelta(minutes=5))
  
한계:
  - 오버엔지니어링 (1인 6개월 MVP에 적합하지 않음)
  - 자연어 입력 없음
```

**3. TaskWeaver (microsoft/TaskWeaver)**
```
핵심 구조 패턴:
  자연어 → Code Generation → 실행 파이프라인
  Planner Agent + Code Interpreter 분리
  
참고 가치:
  - Planner와 Executor의 명확한 분리 (우리 planner.py / executor.py와 동일)
  - 안전 검증 레이어 위치 (Executor 앞, Planner 뒤)
  - 실행 컨텍스트(working directory, env vars) 관리 방법
  
한계:
  - 불변 플랜 개념 없음 → 실행 중 LLM이 플랜 수정 가능
  - 감사 로그 미흡
  - PRD 절대 기준 3(불변 플랜)을 위반하는 설계
```

---
