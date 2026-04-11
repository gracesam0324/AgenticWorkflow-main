# Branch D: CLI 구현 패턴 및 참조 사례
> CLI UX Designer
> 조사일: 2026-04-07

---

## 1. 최고 수준의 CLI UX 사례 분석

### gh에서 배우는 것: 컨텍스트 자동 감지

```python
import click
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def detect_context() -> dict:
    """현재 디렉토리 컨텍스트 자동 감지 (gh 스타일)"""
    import pathlib
    return {
        "cwd": str(pathlib.Path.cwd()),
        "has_git": pathlib.Path(".git").exists(),
        "log_files": list(pathlib.Path(".").glob("**/*.log")),
        "python_project": pathlib.Path("pyproject.toml").exists(),
    }

@click.command()
@click.argument("task", required=False)
@click.option("--mode", "-m", default="semi",
              type=click.Choice(["supervised", "semi", "autonomous"]))
def run(task: str, mode: str):
    ctx = detect_context()
    if not task:
        task = Prompt.ask("[bold]무엇을 할까요?[/bold]")
    console.print(f"[dim]컨텍스트: {ctx['cwd']} | 모드: {mode}[/dim]")
```

### poetry에서 배우는 것: 단계별 진행 표시

```python
from rich.progress import (
    Progress, SpinnerColumn, TextColumn,
    BarColumn, TimeElapsedColumn, TaskProgressColumn
)

def create_step_progress():
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=20),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        transient=False,  # poetry처럼 완료 후에도 표시 유지
    )
```

### Claude Code에서 배우는 것: AI 출력과 시스템 행동의 명확한 분리

```python
from rich.panel import Panel
from rich.syntax import Syntax

def display_llm_plan(plan_yaml: str, plan_summary: dict):
    """AI 생성 내용과 실행 명령을 시각적으로 분리"""
    console.print(Panel(
        plan_summary["description"],
        title="[bold cyan]AI 생성 플랜[/bold cyan]",
        subtitle="[dim]Claude claude-sonnet-4-6[/dim]",
        border_style="cyan",
    ))
    if Confirm.ask("[dim]YAML 원본 보기?[/dim]", default=False):
        console.print(Panel(
            Syntax(plan_yaml, "yaml", theme="monokai", line_numbers=True),
            title="[dim]plan.yaml[/dim]",
            border_style="dim",
        ))
```

### docker에서 배우는 것: 단계 번호 + 위험도 표시

```python
def print_step_header(step_num: int, total: int, name: str, risk: str):
    risk_colors = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}
    color = risk_colors.get(risk, "white")
    console.rule(
        f"[bold]STEP {step_num}/{total}[/bold]  "
        f"{name}  "
        f"[{color}]● {risk}[/{color}]"
    )
```

---

## 2. Rich 라이브러리 구현 패턴

### 플랜 미리보기 테이블

```python
from rich.table import Table
from rich.text import Text
from rich import box

def render_plan_table(steps: list[dict]) -> Table:
    table = Table(title="실행 플랜", box=box.ROUNDED, show_header=True)
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("작업", min_width=24)
    table.add_column("타입", width=8)
    table.add_column("위험", width=8)
    table.add_column("롤백", width=6)
    table.add_column("예상", width=6, justify="right")

    risk_style = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "bold red"}
    type_style = {
        "READ": "dim", "WRITE": "blue", "EXEC": "cyan",
        "DELETE": "bold red", "NETWORK": "magenta",
    }

    for i, step in enumerate(steps, 1):
        risk = step.get("risk", "LOW")
        op_type = step.get("type", "EXEC")
        table.add_row(
            str(i),
            step["name"],
            Text(op_type, style=type_style.get(op_type, "white")),
            Text(f"● {risk}", style=risk_style.get(risk, "white")),
            Text("가능" if step.get("rollback") else "—",
                 style="green" if step.get("rollback") else "dim"),
            step.get("estimated_time", "~?s"),
        )
    return table
```

### 실행 진행 상황 (Rich Live)

```python
from rich.live import Live
from rich.layout import Layout

class ExecutionDisplay:
    def __init__(self, steps: list[dict]):
        self.steps = steps
        self.statuses = ["waiting"] * len(steps)

    def render(self) -> Layout:
        icons = {
            "waiting": "[dim]○[/dim]",
            "running": "[bold yellow]⟳[/bold yellow]",
            "done":    "[bold green]✔[/bold green]",
            "failed":  "[bold red]✗[/bold red]",
            "skipped": "[dim]↷[/dim]",
        }
        steps_table = Table(box=box.SIMPLE, show_header=False, expand=True)
        steps_table.add_column("status", width=4)
        steps_table.add_column("step")
        for i, (step, status) in enumerate(zip(self.steps, self.statuses)):
            steps_table.add_row(icons[status], f"STEP {i+1}  {step['name']}")
        return Panel(steps_table, title="실행 현황")
```

### 단계별 확인 프롬프트

```python
from rich.prompt import Prompt

def step_confirm_prompt(step: dict, step_num: int, total: int) -> str:
    """반환값: 'yes' | 'no' | 'skip' | 'inspect' | 'abort'"""
    risk = step.get("risk", "LOW")
    risk_colors = {"LOW": "green", "MEDIUM": "yellow", "HIGH": "red"}
    color = risk_colors[risk]

    console.print()
    console.rule(
        f"[bold]STEP {step_num}/{total}[/bold]  "
        f"[{color}]● {risk}[/{color}]  {step['name']}"
    )

    if risk == "HIGH":
        console.print(Panel(
            "[bold red]⚠  이 작업은 되돌리기 어렵습니다.[/bold red]",
            border_style="red",
        ))

    console.print(
        "[bold green][y][/bold green] 실행  "
        "[bold red][n][/bold red] 중단  "
        "[yellow][s][/yellow] 건너뜀  "
        "[cyan][i][/cyan] 상세 보기"
    )

    choice = Prompt.ask(">", choices=["y", "n", "s", "i"], default="y",
                        show_choices=False)
    return {"y": "yes", "n": "abort", "s": "skip", "i": "inspect"}[choice]
```

### 성공/실패 최종 요약

```python
def render_summary(steps, results, total_duration, rollback_path=None):
    done = sum(1 for r in results if r["status"] == "done")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    color = "green" if failed == 0 else ("yellow" if done > 0 else "red")
    icon = "✔" if failed == 0 else ("⚠" if done > 0 else "✗")
    text = "모든 스텝 완료" if failed == 0 else f"{failed}개 스텝 실패"

    result_table = Table(box=box.SIMPLE, show_header=True)
    result_table.add_column("#", width=3)
    result_table.add_column("작업", min_width=20)
    result_table.add_column("결과", width=8)
    result_table.add_column("소요", width=8, justify="right")

    status_styles = {
        "done":    ("[green]✔ 완료[/green]", ""),
        "failed":  ("[red]✗ 실패[/red]", "on dark_red"),
        "skipped": ("[dim]↷ 건너뜀[/dim]", "dim"),
    }
    for i, (step, result) in enumerate(zip(steps, results), 1):
        status_text, row_style = status_styles[result["status"]]
        result_table.add_row(str(i), step["name"], status_text,
                             f"{result['duration']:.1f}s", style=row_style)

    rollback_note = ""
    if rollback_path:
        rollback_note = f"\n[dim]복구 명령: autoflow rollback {rollback_path.split('/')[-1]}[/dim]"

    console.print(Panel(
        result_table,
        title=f"[bold {color}]{icon}  {text}[/bold {color}]",
        subtitle=f"[green]완료: {done}[/green]  [red]실패: {failed}[/red]  "
                 f"[dim]건너뜀: {skipped}[/dim]  "
                 f"총 소요: {int(total_duration)}s" + rollback_note,
        border_style=color,
    ))
```

---

## 3. YAML 플랜 사용자 가독성 설계

### 두 레이어 분리 원칙

LLM이 생성하는 YAML에 `user_description` 필드를 별도 포함시킨다.

```yaml
steps:
  - id: step_1
    name: scan_log_files
    user_description: "30일 이상 된 로그 파일 목록을 확인합니다"  # 사용자에게 표시
    type: READ
    risk: LOW
    estimated_seconds: 2
    rollback: false
    affected_files:
      - "/var/logs/**/*.log"
    command: "find /var/logs -mtime +30 -name '*.log'"  # 기술적 세부사항 (i 키로만)

  - id: step_2
    name: compress_files
    user_description: "파일을 하나의 압축 파일로 묶습니다 (~580 MB 생성 예정)"
    type: WRITE
    risk: MEDIUM
    estimated_seconds: 30
    rollback: true
    rollback_action: "rm -f /var/archive/logs_archive.tar.gz"
    affected_files:
      - "/var/archive/logs_archive.tar.gz"
    command: "tar -czf /var/archive/logs_archive.tar.gz [files]"
```

---

## 4. PRD UX 섹션에 포함해야 할 내용

### 필수 UX 원칙 5가지

1. **행동 전 선언 (Declare Before Acting)**: 어떤 파일 시스템 변경도 사용자가 볼 수 없는 상태에서 발생하지 않는다.
2. **언제든 빠져나올 수 있음 (Always Escapable)**: Ctrl+C로 항상 안전하게 일시정지. 강제 종료는 두 번 연속만 가능.
3. **복구 가능성 명시 (Explicit Recoverability)**: 각 스텝 표시 시 롤백 가능/불가를 색상과 텍스트로 명확히 표시.
4. **자율성 레벨의 일관성 (Consistent Autonomy Contract)**: 선택한 자율성 레벨은 세션 내내 일관되게 동작.
5. **진단 가능한 실패 (Diagnosable Failure)**: 오류 발생 시 "무엇이", "왜", "어떻게 고칠 수 있는가"를 함께 표시.

### 금지 UX 안티패턴 3가지

1. **침묵 실행 (Silent Execution)**: 설명 없이 명령 실행 절대 금지. Autonomous Mode에서도 최소한의 진행 표시는 항상 출력.
2. **되돌릴 수 없는 작업의 기본값 허용 (Destructive Default)**: 삭제/덮어쓰기 포함 플랜에서 엔터 키 하나로 전체 실행 금지.
3. **오류 소비자화 (Error Minimization)**: 실패한 스텝을 조용히 건너뛰는 것 금지. 모든 실패는 명시적 표시.

### v1.0 필수 인터랙션 흐름

1. `autoflow init` — API 키 설정 + 자율성 레벨 선택 (3단계 wizard)
2. `autoflow run "<task>"` — 플랜 생성 → 미리보기 → Supervised 실행
3. 스텝별 y/n/s/i 확인 인터페이스
4. Ctrl+C 일시정지 → 재개/롤백/중단 선택
5. 스텝 실패 시 retry/skip/rollback/abort 선택
6. 실행 완료 요약 (성공/실패/건너뜀 카운트)
7. `autoflow rollback <id>` — 스냅샷 기반 복구
8. `autoflow history` — 이전 실행 목록 및 상태 확인
9. `autoflow config` — 설정 조회/수정

### v2.0으로 미룰 UX 개선

- 인터랙티브 플랜 편집기 (v1.0은 $EDITOR로 대체)
- 플랜 템플릿 라이브러리 (v1.0은 history 재실행만)
- 다중 에이전트 병렬 실행 UI (v1.0은 순차만)
- 웹 대시보드 (v1.0은 터미널 출력만)
- 플랜 diff 표시 (v1.0은 전체 재표시)
