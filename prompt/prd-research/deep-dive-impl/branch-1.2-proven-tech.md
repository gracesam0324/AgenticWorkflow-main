## BRANCH 1.2: 보수적 기술 선택 (Proven Implementation)

---

### 1. Claude API 최소화 활용

#### 1.1 기본 패턴 + Jinja2 프롬프트 관리

```python
# prompt_manager.py
import anthropic
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import hashlib
import json
import time

class PromptManager:
    def __init__(self, template_dir: str = "templates/prompts"):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.client = anthropic.Anthropic()
        self._cache = {}  # 간단한 인메모리 캐시
    
    def render(self, template_name: str, **kwargs) -> str:
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
    
    def _cache_key(self, model: str, prompt: str) -> str:
        return hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()
    
    def call(
        self, 
        template_name: str,
        model: str = "claude-haiku-4-5",  # 비용 최적화 기본값
        max_tokens: int = 2048,
        use_cache: bool = True,
        **template_vars
    ) -> str:
        prompt = self.render(template_name, **template_vars)
        cache_key = self._cache_key(model, prompt)
        
        # 캐시 확인 (동일 입력 재호출 방지)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result = response.content[0].text
        
        if use_cache:
            self._cache[cache_key] = result
        
        return result
```

프롬프트 템플릿 예시:
```jinja2
{# templates/prompts/generate_plan.j2 #}
당신은 워크플로우 자동화 전문가입니다.

## 사용자 요청
{{ user_request }}

## 사용 가능한 액션 타입
- shell: 셸 명령어 실행
- python: Python 함수 실행  
- file: 파일 읽기/쓰기
- http: HTTP 요청

## 현재 작업 디렉토리 구조
{{ directory_tree }}

YAML 형식으로 워크플로우 플랜을 생성하세요.
각 스텝은 명확한 id, name, type, action을 가져야 합니다.
의존성이 있는 경우 depends_on을 명시하세요.

```yaml
version: "1.0"
name: "..."
steps:
  ...
```
```

#### 1.2 비용 최적화 전략

```python
# cost_optimizer.py
MODEL_COSTS = {
    # input/output per 1M tokens (USD)
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-opus-4-5": {"input": 15.00, "output": 75.00},
}

def select_model(task_complexity: str) -> str:
    """작업 복잡도에 따른 모델 자동 선택"""
    mapping = {
        "simple": "claude-haiku-4-5",      # 플랜 파싱, 요약
        "moderate": "claude-sonnet-4-5",   # 워크플로우 생성
        "complex": "claude-opus-4-5",      # 복잡한 코드 분석
    }
    return mapping.get(task_complexity, "claude-haiku-4-5")

class CostTracker:
    def __init__(self, budget_usd: float = 5.0):
        self.budget = budget_usd
        self.spent = 0.0
        self.calls = []
    
    def record(self, model: str, input_tokens: int, output_tokens: int):
        costs = MODEL_COSTS[model]
        cost = (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000
        self.spent += cost
        self.calls.append({"model": model, "cost": cost, "time": time.time()})
        
        if self.spent > self.budget * 0.8:
            print(f"경고: 예산의 80% 사용 (${self.spent:.4f}/${self.budget})")
    
    @property
    def remaining(self) -> float:
        return self.budget - self.spent
```

---

### 2. 단순 YAML 실행 엔진 (보수적)

```python
# simple_engine.py
import yaml
import subprocess
import json
from dataclasses import dataclass, field
from typing import Optional, Any
from pathlib import Path

@dataclass
class SimpleStep:
    """dataclass 기반 - Pydantic 없이"""
    id: str
    name: str
    type: str  # 'shell', 'python', 'file'
    action: str
    args: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    timeout: int = 60
    retry: int = 1
    on_failure: str = "stop"

@dataclass
class SimpleWorkflow:
    name: str
    steps: list[SimpleStep]
    version: str = "1.0"

def parse_workflow(yaml_path: str) -> SimpleWorkflow:
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    steps = [SimpleStep(**step) for step in data['steps']]
    return SimpleWorkflow(
        name=data['name'],
        steps=steps,
        version=data.get('version', '1.0')
    )

class SimpleExecutor:
    """순차 실행 - 복잡성 최소화"""
    
    def __init__(self, working_dir: str = "."):
        self.working_dir = working_dir
        self.results = {}
        self.status_file = Path(".autoflow_state.json")
    
    def run(self, workflow: SimpleWorkflow) -> dict:
        """순차 실행 (의존성 순서대로)"""
        ordered_steps = self._topological_sort(workflow.steps)
        
        for step in ordered_steps:
            print(f"\n[{step.id}] {step.name} 실행 중...")
            
            success = False
            for attempt in range(step.retry):
                try:
                    result = self._run_step(step)
                    self.results[step.id] = result
                    self._save_state()
                    success = True
                    break
                except Exception as e:
                    print(f"  시도 {attempt+1}/{step.retry} 실패: {e}")
            
            if not success and step.on_failure == "stop":
                raise RuntimeError(f"스텝 '{step.id}' 실패로 중단")
        
        return self.results
    
    def _run_step(self, step: SimpleStep) -> Any:
        if step.type == "shell":
            return self._run_shell(step)
        elif step.type == "python":
            return self._run_python(step)
        elif step.type == "file":
            return self._run_file_op(step)
        else:
            raise ValueError(f"알 수 없는 스텝 타입: {step.type}")
    
    def _run_shell(self, step: SimpleStep) -> dict:
        """subprocess.run 안전 래퍼"""
        import shlex
        cmd = step.action
        
        # 변수 치환
        cmd = self._substitute_vars(cmd)
        
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=step.timeout,
            cwd=self.working_dir
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"명령어 실패 (exit {result.returncode}): {result.stderr}")
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def _substitute_vars(self, text: str) -> str:
        """{{ step_id.field }} 형식 변수 치환"""
        import re
        def replace(match):
            step_id, field = match.group(1), match.group(2)
            return str(self.results.get(step_id, {}).get(field, ''))
        
        return re.sub(r'\{\{\s*(\w+)\.(\w+)\s*\}\}', replace, text)
    
    def _topological_sort(self, steps: list[SimpleStep]) -> list[SimpleStep]:
        """Kahn's 알고리즘으로 위상 정렬"""
        in_degree = {s.id: len(s.depends_on) for s in steps}
        step_map = {s.id: s for s in steps}
        queue = [s for s in steps if in_degree[s.id] == 0]
        sorted_steps = []
        
        while queue:
            step = queue.pop(0)
            sorted_steps.append(step)
            
            for other in steps:
                if step.id in other.depends_on:
                    in_degree[other.id] -= 1
                    if in_degree[other.id] == 0:
                        queue.append(other)
        
        return sorted_steps
    
    def _save_state(self):
        """파일 기반 상태 저장 (재개용)"""
        state = {
            step_id: {"status": "completed", "result": result}
            for step_id, result in self.results.items()
        }
        with open(self.status_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
```

---

### 3. CLI 구현 (Click + Rich)

```python
# cli.py
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm, Prompt
import yaml

console = Console()

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """AutoFlow - 로컬 AI 워크플로우 자동화 도구"""
    pass

@cli.command()
@click.argument('request', nargs=-1)
@click.option('--output', '-o', default='workflow.yaml', help='출력 YAML 파일 경로')
@click.option('--model', '-m', default='claude-sonnet-4-5', help='Claude 모델')
@click.option('--dry-run', is_flag=True, help='실제 저장 없이 미리보기')
def plan(request, output, model, dry_run):
    """자연어로 워크플로우 플랜 생성
    
    예시: autoflow plan "CSV 파일을 정제하고 보고서 생성"
    """
    request_text = ' '.join(request)
    
    if not request_text:
        request_text = Prompt.ask("[bold cyan]무엇을 자동화할까요?[/bold cyan]")
    
    console.print(Panel(f"[bold]요청 분석 중...[/bold]\n{request_text}", border_style="blue"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Claude가 플랜 생성 중...", total=None)
        
        # Claude API 호출
        pm = PromptManager()
        yaml_content = pm.call(
            "generate_plan.j2",
            model=model,
            user_request=request_text,
            directory_tree=get_directory_tree()
        )
        
        progress.update(task, completed=True, description="플랜 생성 완료!")
    
    # YAML 미리보기
    console.print("\n[bold green]생성된 워크플로우:[/bold green]")
    console.print(Syntax(yaml_content, "yaml", theme="monokai"))
    
    if dry_run:
        return
    
    # 저장 확인
    if Confirm.ask(f"\n[yellow]{output}[/yellow]에 저장할까요?"):
        with open(output, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        console.print(f"[green]저장됨:[/green] {output}")

@cli.command()
@click.argument('yaml_file')
@click.option('--var', '-v', multiple=True, help='변수 오버라이드 (key=value)')
@click.option('--auto-approve', '-y', is_flag=True, help='모든 승인 자동 처리')
@click.option('--resume', '-r', is_flag=True, help='중단된 워크플로우 재개')
@click.option('--step', '-s', help='특정 스텝부터 실행')
def run(yaml_file, var, auto_approve, resume, step):
    """YAML 워크플로우 실행
    
    예시: autoflow run workflow.yaml -v input_file=data.csv
    """
    # 변수 파싱
    variables = {}
    for v in var:
        key, _, value = v.partition('=')
        variables[key] = value
    
    try:
        workflow = parse_workflow(yaml_file)
    except Exception as e:
        console.print(f"[red]YAML 파싱 오류:[/red] {e}")
        raise SystemExit(1)
    
    # 워크플로우 요약 표시
    _display_workflow_summary(workflow)
    
    if not auto_approve:
        if not Confirm.ask("\n[bold]이 워크플로우를 실행할까요?[/bold]"):
            console.print("[yellow]취소됨[/yellow]")
            return
    
    executor = SimpleExecutor()
    
    # 진행상황 표시
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        main_task = progress.add_task(
            f"[cyan]{workflow.name}[/cyan] 실행 중...", 
            total=len(workflow.steps)
        )
        
        def on_step_complete(step_id: str, result: dict):
            progress.advance(main_task)
            progress.print(f"  [green]✓[/green] {step_id}")
        
        try:
            results = executor.run(workflow)
            console.print("\n[bold green]워크플로우 완료![/bold green]")
            _display_results(results)
        except Exception as e:
            console.print(f"\n[bold red]실패:[/bold red] {e}")
            raise SystemExit(1)

@cli.command()
@click.option('--limit', '-n', default=10, help='표시할 실행 수')
def history(limit):
    """실행 히스토리 조회"""
    table = Table(title="워크플로우 실행 히스토리")
    table.add_column("실행 ID", style="cyan")
    table.add_column("워크플로우", style="white")
    table.add_column("상태", style="green")
    table.add_column("시작 시간")
    table.add_column("소요 시간")
    
    # DB에서 히스토리 로드
    runs = get_recent_runs(limit)
    for run in runs:
        status_style = "green" if run.status == "completed" else "red"
        table.add_row(
            run.id[:8],
            run.workflow_name,
            f"[{status_style}]{run.status}[/{status_style}]",
            run.created_at.strftime("%Y-%m-%d %H:%M"),
            f"{run.elapsed:.1f}s"
        )
    
    console.print(table)

def _display_workflow_summary(workflow: SimpleWorkflow):
    """워크플로우 요약 테이블"""
    table = Table(title=f"워크플로우: {workflow.name}")
    table.add_column("#", style="dim")
    table.add_column("스텝 ID", style="cyan")
    table.add_column("이름")
    table.add_column("타입", style="yellow")
    table.add_column("의존성", style="dim")
    
    for i, step in enumerate(workflow.steps, 1):
        deps = ", ".join(step.depends_on) if step.depends_on else "-"
        table.add_row(str(i), step.id, step.name, step.type, deps)
    
    console.print(table)

if __name__ == '__main__':
    cli()
```

---

### 4. 테스트 전략

```python
# tests/test_executor.py
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import yaml

@pytest.fixture
def sample_workflow_yaml(tmp_path):
    """테스트용 임시 YAML 파일"""
    workflow_data = {
        "name": "테스트 워크플로우",
        "version": "1.0",
        "steps": [
            {
                "id": "step_a",
                "name": "첫 번째 스텝",
                "type": "shell",
                "action": "echo hello",
                "timeout": 10
            },
            {
                "id": "step_b", 
                "name": "두 번째 스텝",
                "type": "shell",
                "action": "echo {{ step_a.stdout }}",
                "depends_on": ["step_a"],
                "timeout": 10
            }
        ]
    }
    
    yaml_file = tmp_path / "test_workflow.yaml"
    yaml_file.write_text(yaml.dump(workflow_data, allow_unicode=True))
    return str(yaml_file)

class TestSimpleExecutor:
    def test_sequential_execution(self, sample_workflow_yaml, tmp_path):
        """순차 실행 테스트"""
        workflow = parse_workflow(sample_workflow_yaml)
        executor = SimpleExecutor(working_dir=str(tmp_path))
        results = executor.run(workflow)
        
        assert "step_a" in results
        assert "step_b" in results
        assert results["step_a"]["exit_code"] == 0
    
    def test_dependency_order(self, tmp_path):
        """의존성 순서 검증"""
        workflow_data = {
            "name": "test",
            "steps": [
                {"id": "c", "name": "C", "type": "shell", "action": "echo c", "depends_on": ["b"]},
                {"id": "a", "name": "A", "type": "shell", "action": "echo a"},
                {"id": "b", "name": "B", "type": "shell", "action": "echo b", "depends_on": ["a"]},
            ]
        }
        
        yaml_file = tmp_path / "deps.yaml"
        yaml_file.write_text(yaml.dump(workflow_data))
        workflow = parse_workflow(str(yaml_file))
        
        executor = SimpleExecutor()
        sorted_steps = executor._topological_sort(workflow.steps)
        
        ids = [s.id for s in sorted_steps]
        assert ids.index('a') < ids.index('b')
        assert ids.index('b') < ids.index('c')
    
    def test_failure_stops_execution(self, tmp_path):
        """실패 시 중단 확인"""
        workflow_data = {
            "name": "test",
            "steps": [
                {"id": "fail_step", "name": "실패", "type": "shell", 
                 "action": "nonexistent_command_xyz", "on_failure": "stop"}
            ]
        }
        
        yaml_file = tmp_path / "fail.yaml"
        yaml_file.write_text(yaml.dump(workflow_data))
        workflow = parse_workflow(str(yaml_file))
        
        executor = SimpleExecutor(working_dir=str(tmp_path))
        with pytest.raises(RuntimeError):
            executor.run(workflow)

class TestClaudeIntegration:
    """AI 출력 모킹 테스트"""
    
    @pytest.fixture
    def mock_anthropic(self):
        with patch('anthropic.Anthropic') as mock:
            client = MagicMock()
            mock.return_value = client
            
            # API 응답 모킹
            response = MagicMock()
            response.content = [MagicMock(text="""
version: "1.0"
name: "모킹된 워크플로우"
steps:
  - id: test_step
    name: "테스트"
    type: shell
    action: "echo test"
""")]
            client.messages.create.return_value = response
            yield client
    
    def test_plan_generation(self, mock_anthropic):
        """플랜 생성 테스트 (API 모킹)"""
        pm = PromptManager()
        result = pm.call("generate_plan.j2", user_request="테스트 자동화")
        
        assert "steps" in result
        mock_anthropic.messages.create.assert_called_once()
    
    def test_cost_tracking(self, mock_anthropic):
        """비용 추적 테스트"""
        tracker = CostTracker(budget_usd=1.0)
        tracker.record("claude-haiku-4-5", input_tokens=1000, output_tokens=500)
        
        expected_cost = (1000 * 0.80 + 500 * 4.00) / 1_000_000
        assert abs(tracker.spent - expected_cost) < 0.0001

# GitHub Actions CI
# .github/workflows/test.yml
"""
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov=autoflow --cov-report=xml
      - uses: codecov/codecov-action@v4
"""
```

---

### 5. 패키징과 배포

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "autoflow"
version = "0.1.0"
description = "로컬 AI 워크플로우 자동화 도구"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
keywords = ["ai", "automation", "workflow", "claude"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Topic :: Software Development :: Build Tools",
]

dependencies = [
    "anthropic>=0.40.0",
    "click>=8.1.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "jinja2>=3.1.0",
    "pydantic>=2.0.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "aiosqlite>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]
mcp = [
    "mcp>=1.0.0",
]

[project.scripts]
autoflow = "autoflow.cli:cli"

[project.urls]
Repository = "https://github.com/username/autoflow"
Issues = "https://github.com/username/autoflow"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.mypy]
python_version = "3.11"
strict = true
```

pipx 설치 및 업데이트:
```bash
# 설치
pipx install autoflow

# 개발 버전 설치 (editable)
pipx install --editable .

# 업데이트 메커니즘
autoflow self-update  # 내부적으로 실행하는 코드:
```

```python
# self_update.py
@cli.command()
def self_update():
    """최신 버전으로 업데이트"""
    import subprocess
    import pkg_resources
    
    current = pkg_resources.get_distribution("autoflow").version
    
    # PyPI에서 최신 버전 확인
    import urllib.request, json
    with urllib.request.urlopen("https://pypi.org/pypi/autoflow/json") as r:
        latest = json.loads(r.read())["info"]["version"]
    
    if current == latest:
        console.print(f"[green]최신 버전 사용 중:[/green] {current}")
        return
    
    console.print(f"업데이트 가능: {current} → {latest}")
    if Confirm.ask("업데이트할까요?"):
        subprocess.run(["pipx", "upgrade", "autoflow"], check=True)
        console.print("[green]업데이트 완료![/green]")
```

---

### Branch 1.2 검증된 유사 도구 분석

| 도구 | 기술 스택 | 배운 점 |
|------|-----------|---------|
| **Fabric** | Python, Click, paramiko | 간단한 CLI 패턴, 태스크 정의 방식 |
| **Invoke** | Python, Click 유사 CLI | 태스크 의존성 관리 패턴이 명확 |
| **Prefect** | Python, Pydantic, async | Flow/Task 분리 개념, 상태 관리 |
| **Dagster** | Python, 타입 기반 파이프라인 | Asset 기반 설계, 재실행 패턴 |
| **doit** | Python, YAML 태스크 러너 | 파일 기반 상태 관리 단순성 |

---

## 최종 결론: 두 Branch 비교 및 권장 전략

### 코드 복잡도 비교

| 영역 | Branch 1.1 (공격적) | Branch 1.2 (보수적) |
|------|---------------------|---------------------|
| **전체 코드 라인** | ~3,000-5,000 LOC | ~800-1,200 LOC |
| **외부 의존성** | 15-20개 | 5-8개 |
| **테스트 난이도** | 높음 (async, 스트리밍) | 낮음 (동기 위주) |
| **디버깅 난이도** | 높음 | 낮음 |
| **MVP 완성 예상** | 8-12개월 (1인) | 3-4개월 (1인) |

### 1인 6개월 MVP 현실적 평가

**Branch 1.1의 함정:**
- `asyncio` + `SQLAlchemy async` + `MCP` 동시 구현은 디버깅 지옥
- DAG 엔진 edge case(순환 의존성 + 동시 실패) 처리에 2-3개월 소모
- Claude streaming + tool_use 동시 처리 복잡도 과소평가됨

**Branch 1.2의 안전성:**
- 순차 실행으로 시작해도 타겟 유저(데이터 엔지니어)가 원하는 95% 커버
- Click + Rich는 커뮤니티에서 가장 검증된 Python CLI 스택
- 파일 기반 상태에서 SQLite로의 마이그레이션은 6개월 이후에도 가능

---

### 권장 구현 전략: **Pragmatic Hybrid (실용적 혼합)**

핵심 원칙: **보수적 기반 위에 공격적 기능을 선택적으로 얹는다**

#### Phase 1 (Month 1-2): 보수적 기반 구축
```
- SimpleExecutor (순차 실행)
- PyYAML + dataclasses 파싱
- Click CLI + Rich 출력
- subprocess.run 안전 래퍼
- 파일 기반 상태 (.json)
- Claude 기본 호출 + Jinja2 템플릿
```

#### Phase 2 (Month 3-4): 핵심 기능 강화
```
- Pydantic 모델로 업그레이드 (하위 호환)
- 단계별 승인 UX 완성
- Git 기반 롤백 구현
- pytest 기반 테스트 스위트
- pyproject.toml + pipx 배포
```

#### Phase 3 (Month 5-6): 선택적 고급 기능
```
- async DAG (병렬 실행) - 사용자 피드백 기반
- SQLite 상태 관리 - 필요한 경우만
- MCP 서버 - 얼리어답터 대응용
```

#### 최적 기술 조합 (최종 권장)

```python
# 권장 의존성 (최소화된 핵심)
CORE_STACK = {
    "ai": "anthropic>=0.40.0",           # 공식 SDK
    "cli": "click>=8.1 + rich>=13",      # 검증된 CLI
    "config": "pyyaml>=6 + pydantic>=2", # 타입 안전 파싱
    "templates": "jinja2>=3.1",          # 프롬프트 관리
    "db": "sqlalchemy>=2 + aiosqlite",   # Phase 2부터
}

# 피해야 할 것 (MVP 범위 초과)
AVOID_FOR_MVP = [
    "langchain",      # 과도한 추상화, 자주 변경
    "celery",         # 분산 큐 - 로컬 불필요
    "docker-sdk",     # 샌드박싱 오버킬
    "ray",            # 분산 컴퓨팅 - 범위 초과
    "opentelemetry",  # 관측가능성 - Phase 3+
]
```

#### PRD 작성을 위한 핵심 기술 방향

PRD에 명시해야 할 기술 결정 사항:

1. **실행 모델**: 순차 우선, async는 v0.2에서 도입
2. **상태 저장**: JSON 파일 → SQLite 마이그레이션 경로 명시
3. **AI 호출**: 단방향 call/response 기반, agent loop는 v0.3
4. **보안 경계**: subprocess 실행 시 사용자 승인이 유일한 게이트
5. **확장점**: MCP 서버는 인터페이스로 정의, 구현은 후순위
6. **배포**: pipx 단일 설치, 의존성 5개 이하 유지가 목표

이 전략으로 4개월 안에 실제 데이터 엔지니어가 매일 사용할 수 있는 도구를 만들고, 나머지 2개월은 실 사용자 피드백 기반의 개선에 투자하는 것이 1인 개발자에게 가장 현실적인 경로입니다.