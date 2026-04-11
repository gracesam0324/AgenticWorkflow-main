# Branch 2.1: MCP 프로토콜 통합 — MCP 서버로 패키징
> MCP Protocol Integration Specialist
> 조사일: 2026-04-07
> SDK: Python MCP SDK 1.2.0+, Protocol 2025-03-26

---

## 핵심 개념

MCP(Model Context Protocol): AI 앱과 외부 시스템을 연결하는 오픈 표준 (JSON-RPC 2.0 기반).

| 계층 | 역할 |
|---|---|
| MCP Host | AI 앱 (Claude Desktop, VS Code) |
| MCP Client | 호스트 내 서버당 1개 전용 연결 |
| MCP Server | 우리가 만들 것 |

**3개 프리미티브**:
- **Tools**: LLM이 호출하는 실행 함수
- **Resources**: 읽기 전용 컨텍스트 데이터
- **Prompts**: 재사용 가능한 템플릿

---

## 1. FastMCP 서버 전체 구현

```bash
# 설치
uv add "mcp[cli]"
# 또는
pip install "mcp[cli]"
```

```python
# mcp_server.py
"""
AI Agentic Workflow Automation System - MCP Server
FastMCP 기반 stdio 방식 구현
Python MCP SDK 1.2.0+, Protocol 2025-03-26
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# STDIO 서버에서는 print()를 stdout으로 쓰면 안 됨
# JSON-RPC 메시지를 오염시킴 - 반드시 stderr 사용
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "workflow-automation",
    version="1.0.0",
    description="로컬 AI Agentic Workflow Automation System MCP Server"
)


# TOOL 1: execute_workflow
@mcp.tool()
async def execute_workflow(
    task: str,
    dry_run: bool = True,
    autonomy_level: int = 1
) -> str:
    """자연어 태스크를 YAML 플랜으로 변환 후 단계별 실행합니다.

    Args:
        task: 실행할 태스크의 자연어 설명
        dry_run: True이면 실행 계획만 표시 (기본값: True)
        autonomy_level: 자율 실행 수준 (1=각 단계 승인, 2=그룹, 3=완전 자동)
    """
    logger.info(f"execute_workflow: task={task!r}, dry_run={dry_run}, autonomy={autonomy_level}")

    if autonomy_level not in [1, 2, 3]:
        return "오류: autonomy_level은 1, 2, 3 중 하나여야 합니다."

    cmd = ["python", "-m", "workflow_automation", "run", task]
    if dry_run:
        cmd.append("--dry-run")
    cmd.extend(["--autonomy", str(autonomy_level)])

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.home()
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300.0)

        if proc.returncode == 0:
            return stdout.decode("utf-8", errors="replace")
        else:
            return f"실행 실패 (exit {proc.returncode}):\n{stderr.decode('utf-8', errors='replace')}"

    except asyncio.TimeoutError:
        return "오류: 시간 초과 (300초)"
    except FileNotFoundError:
        return "오류: workflow_automation 모듈을 찾을 수 없습니다."
    except Exception as e:
        return f"예상치 못한 오류: {e!s}"


# TOOL 2: validate_workflow
@mcp.tool()
async def validate_workflow(yaml_content: str) -> str:
    """YAML 워크플로우 플랜의 안전성과 유효성을 검증합니다."""
    logger.info("validate_workflow 호출")

    try:
        import yaml
        plan = yaml.safe_load(yaml_content)
    except Exception as e:
        return f"YAML 파싱 오류: {e!s}"

    if not isinstance(plan, dict):
        return "오류: 최상위 요소가 dict여야 합니다."

    issues = []
    if "steps" not in plan:
        issues.append("'steps' 필드가 없습니다.")
    elif not isinstance(plan["steps"], list):
        issues.append("'steps'는 리스트여야 합니다.")
    else:
        for i, step in enumerate(plan["steps"]):
            if "name" not in step:
                issues.append(f"step[{i}]: 'name' 필드 없음")
            if "action" not in step:
                issues.append(f"step[{i}]: 'action' 필드 없음")

    dangerous_patterns = ["rm -rf", "format", "del /f", "DROP TABLE", "shutdown"]
    yaml_lower = yaml_content.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in yaml_lower:
            issues.append(f"경고: 위험 패턴 감지 - '{pattern}'")

    if issues:
        return "검증 문제 발견:\n" + "\n".join(f"- {i}" for i in issues)
    return f"검증 통과: {len(plan.get('steps', []))}개 단계 유효"


# TOOL 3: list_plan_history
@mcp.tool()
async def list_plan_history(limit: int = 10) -> str:
    """과거에 실행된 워크플로우 플랜 이력을 조회합니다."""
    history_dir = Path.home() / ".workflow_automation" / "history"

    if not history_dir.exists():
        return "실행 이력이 없습니다."

    history_files = sorted(
        history_dir.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )[:limit]

    if not history_files:
        return "이력 파일이 없습니다."

    results = []
    for f in history_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append(
                f"[{data.get('timestamp', '?')}] "
                f"ID: {data.get('session_id', f.stem)} | "
                f"태스크: {data.get('task', '?')[:60]} | "
                f"상태: {data.get('status', '?')}"
            )
        except Exception as e:
            results.append(f"[읽기 오류: {f.name}] {e!s}")

    return f"최근 {len(results)}개 이력:\n" + "\n".join(results)


# TOOL 4: rollback_workflow
@mcp.tool()
async def rollback_workflow(session_id: str) -> str:
    """특정 세션 ID의 워크플로우를 이전 상태로 롤백합니다."""
    if not session_id or len(session_id) > 64:
        return "오류: 유효하지 않은 session_id"

    cmd = ["python", "-m", "workflow_automation", "rollback", session_id]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60.0)

        if proc.returncode == 0:
            return f"롤백 성공:\n{stdout.decode('utf-8', errors='replace')}"
        return f"롤백 실패:\n{stderr.decode('utf-8', errors='replace')}"
    except asyncio.TimeoutError:
        return "오류: 롤백 시간 초과 (60초)"
    except Exception as e:
        return f"롤백 오류: {e!s}"


# RESOURCE: YAML 플랜 파일
@mcp.resource("workflow://plans/{plan_name}")
async def get_plan_resource(plan_name: str) -> str:
    """저장된 YAML 워크플로우 플랜을 리소스로 읽어옵니다."""
    plans_dir = Path.home() / ".workflow_automation" / "plans"
    plan_file = plans_dir / f"{plan_name}.yaml"

    if not plan_file.exists():
        return f"플랜 '{plan_name}'을 찾을 수 없습니다."

    try:
        plan_file.resolve().relative_to(plans_dir.resolve())
    except ValueError:
        return "오류: 허용되지 않은 경로"

    return plan_file.read_text(encoding="utf-8")


# PROMPT: 워크플로우 설계 가이드
@mcp.prompt()
def workflow_design_prompt(goal: str, constraints: str = "") -> str:
    """새 워크플로우 플랜 작성 안내 프롬프트."""
    return f"""당신은 AI Agentic Workflow Automation System 전문가입니다.
목표: {goal}
제약사항: {constraints or "없음"}

YAML 형식:
```yaml
name: "플랜 이름"
steps:
  - name: "단계 이름"
    action: "액션"
    rollback: "롤백 명령어"
```

원칙: dry_run=true로 먼저 테스트, 각 단계 rollback 포함.
"""


def main():
    logger.info("Workflow Automation MCP Server 시작 (stdio)")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

---

## 2. Claude Desktop 연동 설정

**Windows**: `%AppData%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "workflow-automation": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\김성준\\workflow-automation",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

pipx 설치 후:
```json
{
  "mcpServers": {
    "workflow-automation": {
      "command": "workflow-mcp-server"
    }
  }
}
```

설정 변경 후 **Claude Desktop 완전 재시작** 필요.

---

## 3. pyproject.toml 패키징

```toml
[project]
name = "workflow-automation-mcp"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.2.0",
    "pyyaml>=6.0",
    "anthropic>=0.40.0",
    "click>=8.1.0",
]

[project.scripts]
workflow-mcp-server = "workflow_automation.mcp_server:main"
```

---

## 4. 공개 MCP 서버 생태계 활용

```json
{
  "mcpServers": {
    "workflow-automation": {"command": "workflow-mcp-server"},
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem",
               "C:\\Users\\김성준\\projects"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "sequentialthinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequentialthinking"]
    }
  }
}
```

**주요 공개 서버**:
- `@modelcontextprotocol/server-filesystem` — 파일 읽기/쓰기 (허용 경로 명시 필수)
- `mcp-server-git` — git status/diff/log/commit
- `@modelcontextprotocol/server-memory` — 영구 지식 그래프
- `@modelcontextprotocol/server-sequentialthinking` — 복잡한 문제 단계 분해
- `@modelcontextprotocol/server-fetch` — 웹 콘텐츠 수집

---

## 5. stdio vs HTTP 비교

| 항목 | stdio (로컬) | Streamable HTTP |
|---|---|---|
| 데이터 로컬 보장 | **완전** | 노출 가능 |
| 네트워크 필요 | 불필요 | 필요 |
| 설정 복잡도 | 낮음 | 높음 |
| 우리 시스템 적합도 | **최적** | 비적합 |

---

## 6. PRD 권고

**v1.0 필수**: 4개 도구 (`execute_workflow`, `validate_workflow`, `list_plan_history`, `rollback_workflow`)를 FastMCP로 1-2일 내 구현 가능.

**구현 로드맵**:
- Day 1: FastMCP 4 도구 + Claude Desktop 설정 테스트
- Day 2: Resource/Prompt + pyproject.toml 패키징
- Day 3: 에러 처리 강화 + MCP Inspector 디버깅

**보안 원칙**:
1. stdout 출력 절대 금지 (stderr만 사용)
2. 파일 경로 순회 방지 (`relative_to()` 검증)
3. 모든 외부 호출 타임아웃 적용
4. session_id 길이 제한 (64자)
