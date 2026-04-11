# Branch 5.2: 공식 SDK 문서 & 구현 참조 — 구현 참조 패턴
> Official SDK & Documentation Reference Specialist
> 조사일: 2026-04-07

---

## 1. 프로세스 그룹 관리 (Ctrl+C 안전 처리)

```python
import os, signal, subprocess, sys
from contextlib import contextmanager
from typing import Generator

def run_with_process_group(
    cmd: list[str],
    timeout: int = 300,
    cwd: str = None
) -> tuple[str, str, int]:
    """
    프로세스 그룹으로 실행 → 자식 프로세스까지 안전 종료.
    Unix: os.setsid(), Windows: CREATE_NEW_PROCESS_GROUP
    """
    if sys.platform == "win32":
        process = subprocess.Popen(
            cmd, shell=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            cwd=cwd
        )
    else:
        process = subprocess.Popen(
            cmd, shell=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
            cwd=cwd
        )

    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return (
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
            process.returncode
        )
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            if sys.platform != "win32":
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        raise TimeoutError(f"명령어 {timeout}초 초과: {' '.join(cmd)}")
    except KeyboardInterrupt:
        if sys.platform != "win32":
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        raise


@contextmanager
def managed_subprocess(cmd: list[str], **kwargs) -> Generator[subprocess.Popen, None, None]:
    """Context manager로 subprocess 리소스 안전 관리"""
    process = subprocess.Popen(cmd, **kwargs)
    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def stream_subprocess_output(cmd: list[str], cwd: str = None) -> Generator[str, None, None]:
    """subprocess 출력 실시간 스트리밍 (Rich 콘솔 연동)"""
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        bufsize=1, universal_newlines=True, cwd=cwd
    ) as proc:
        for line in proc.stdout:
            yield line.rstrip("\n")
        proc.wait()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd)
```

---

## 2. Open Interpreter에서 채용할 패턴

```python
class SafeCodeExecutor:
    """Open Interpreter의 semi-safe 실행 패턴에서 파생"""

    BLOCKED_COMMANDS = [
        "rm -rf /", "mkfs", "dd if=/dev/zero",
        ":(){ :|:& };:", "chmod 777 /",
    ]
    MAX_OUTPUT_SIZE = 100_000  # 100KB

    def is_safe(self, command: str) -> tuple[bool, str]:
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command:
                return False, f"위험 명령어: {blocked}"
        return True, ""

    def execute(self, command: str, cwd: str = None, timeout: int = 30,
                require_approval: bool = True) -> dict:
        is_safe, reason = self.is_safe(command)
        if not is_safe:
            return {"success": False, "error": reason}

        if require_approval:
            print(f"\n실행할 명령어: {command}")
            confirm = input("실행? [y/N]: ")
            if confirm.lower() != "y":
                return {"success": False, "error": "사용자 거부"}

        try:
            result = subprocess.run(
                command, shell=True,  # Open Interpreter는 편의상 shell=True
                capture_output=True, text=True, timeout=timeout, cwd=cwd
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:self.MAX_OUTPUT_SIZE],
                "stderr": result.stderr[:self.MAX_OUTPUT_SIZE],
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"타임아웃 ({timeout}초)"}
```

**우리 시스템과의 차이**: Open Interpreter는 사용자 편의를 위해 shell=True 사용. 우리는 shell=False 절대 원칙으로 더 안전.

---

## 3. GitPython 체크포인트 (레퍼런스 구현)

```python
import git
from pathlib import Path
from datetime import datetime

class WorkflowCheckpoint:
    """
    YAML 플랜 각 스텝 완료 시 Git 체크포인트 생성.
    실패 시 이전 체크포인트로 롤백.
    
    주의: gitpython CVE-2024-22190 → 3.1.41+ 필요
    """

    def __init__(self, repo_path: str = "."):
        self.repo = git.Repo(repo_path, search_parent_directories=True)
        self.prefix = "autoflow-checkpoint"

    def create_checkpoint(self, step_name: str, step_index: int) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_name = f"{self.prefix}/{step_index:03d}_{step_name}"

        if self.repo.is_dirty(untracked_files=True):
            self.repo.git.add(A=True)
            self.repo.index.commit(
                f"[autoflow] Step {step_index}: {step_name} 완료\n\n타임스탬프: {timestamp}"
            )
        self.repo.create_tag(tag_name)
        return tag_name

    def list_checkpoints(self) -> list[dict]:
        return sorted([
            {
                "tag": tag.name,
                "commit": tag.commit.hexsha[:8],
                "message": tag.commit.message.strip(),
                "date": tag.commit.committed_datetime.isoformat()
            }
            for tag in self.repo.tags
            if tag.name.startswith(self.prefix)
        ], key=lambda x: x["date"])

    def rollback_to_checkpoint(self, tag_name: str, hard: bool = False):
        tag = self.repo.tags[tag_name]
        if hard:
            self.repo.git.reset("--hard", tag.commit.hexsha)
        else:
            self.repo.git.reset("--soft", tag.commit.hexsha)
```

**gitpython vs MinimalGit 선택**:
- v1.0 기본: `MinimalGit` (subprocess 직접, 의존성 0, CVE 위험 없음)
- 복잡한 Git 객체 모델 필요 시: `gitpython` 3.1.43+ (CVE-2024-22190 패치)

---

## 4. 의존성 완전 목록 (pyproject.toml)

```toml
[project]
name = "workflow-automation"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    # ── 핵심 AI SDK ──
    "anthropic>=0.40.0",           # Messages API, Tool Use, Streaming
    # "claude-agent-sdk>=0.2.0",   # Agent Loop SDK (선택적)

    # ── 시크릿 관리 ──
    "keyring>=25.0.0",             # OS 네이티브 자격증명
    "python-dotenv>=1.0.0",        # .env 파일

    # ── 워크플로우 ──
    "pyyaml>=6.0.1",               # YAML 플랜 파싱
    "tenacity>=9.0.0",             # Retry 전략

    # ── 터미널 UI ──
    "rich>=13.7.0",                # 콘솔 출력
    "click>=8.1.0",                # CLI 인터페이스
]

[project.optional-dependencies]
data = [
    "orjson>=3.10.0",              # 고속 JSON
    "openpyxl>=3.1.5",             # Excel 읽기
    "pyarrow>=19.0.0",             # Parquet
    "pdfplumber>=0.11.0",          # PDF 텍스트
]
analytics = [
    "duckdb>=1.2.0",               # 로컬 분석 DB
    "pandas>=2.2.0",               # 데이터 조작
    "polars>=0.20.0",              # 고속 데이터 처리
]
watch = [
    "watchdog>=4.0.0",             # 실시간 파일 감시
]
git = [
    "gitpython>=3.1.43",           # Git 객체 모델 (CVE 패치)
]
web = [
    "httpx>=0.27.0",               # HTTP 클라이언트
    "beautifulsoup4>=4.12.0",      # HTML 파싱
    "lxml>=5.0.0",                 # BS4 파서
]
llm = [
    "llm>=0.30.0",                 # 통합 LLM CLI
]
mcp = [
    "mcp[cli]>=1.2.0",             # MCP 서버/클라이언트
]
all = [
    "workflow-automation[data,analytics,watch,git,web,llm,mcp]",
]
```

**외부 CLI 도구 (별도 설치)**:
```bash
# Gemini CLI (선택적, Node.js 18+ 필요)
npm install -g @google/gemini-cli
gemini auth login  # 구독 계정

# OpenAI Codex (선택적, ChatGPT 구독 필요)
npm install -g @openai/codex
codex login

# Ollama (로컬 모델, 완전 무료)
# https://ollama.ai 에서 설치
ollama pull llama3.2
```

---

## 5. 전체 외부 연동 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              AI Agentic Workflow System                     │
│                  (로컬 실행, 데이터 로컬 유지)               │
└─────────────────────┬───────────────────────────────────────┘
                      │ 자연어 입력
                      ▼
     ┌─────────────────────────────────────────┐
     │            플랜 생성 레이어              │
     │  Claude Sonnet 4.6 (API Key)            │
     │    + Prompt Caching (5분/1시간)         │
     │    + Extended Thinking (선택적)         │
     │    + Tool Use (에이전트 루프)           │
     │  폴백: Claude Haiku 4.5                 │
     └─────────────────────┬───────────────────┘
                           │ YAML 플랜
                           ▼
     ┌─────────────────────────────────────────┐
     │            플랜 실행 레이어              │
     │  MinimalSafeExecutor (subprocess)       │
     │  MinimalGit / gitpython (체크포인트)    │
     │  SafeFileOperations (파일 I/O)          │
     │  SQLite / DuckDB (로컬 데이터)          │
     │  Rich UI (실시간 출력)                  │
     │  SecretManager (keyring)                │
     └─────────────────────┬───────────────────┘
                           │ 보조 모델 필요 시
                           ▼
     ┌─────────────────────────────────────────┐
     │         보조 모델 레이어 (선택적)        │
     │  Gemini CLI (구독 OAuth / API Key)     │
     │    → subprocess -p prompt --json       │
     │  llm CLI (llm-gemini / llm-ollama)     │
     │  Ollama (완전 오프라인, 무료)           │
     │  MCP Server (Claude Desktop 연동)      │
     └─────────────────────────────────────────┘
```

---

## 6. 인증 결정 트리

```
[Claude] ANTHROPIC_API_KEY 환경변수
       → .env 파일
       → keyring (OS 자격증명)
       → 사용자 입력 → keyring 저장

[Gemini] 대화형: gemini auth login (Google AI Pro 구독)
         자동화: GEMINI_API_KEY 환경변수 (TTY 버그 우회)
         없으면: 해당 기능 비활성화

[OpenAI] Codex CLI: chatgpt 구독 계정 (코딩 전용)
         일반 API: API Key 필요 (구독과 무관)
         → 권장 대안: Ollama 로컬 모델
```

---

## 7. Rate Limit 및 비용 종합표

| 서비스 | Rate Limit | 비용 | 폴백 |
|---|---|---|---|
| Claude Sonnet 4.6 | 5 RPM (기본) | $3/$15 /1M tok | Haiku 4.5 |
| Claude Haiku 4.5 | 5 RPM (기본) | $1/$5 /1M tok | Ollama |
| Gemini 2.0 Flash (무료) | 60 RPM | 무료 | API Key 방식 |
| Gemini 2.5 Pro (AI Pro) | 제한적 | 구독 포함 | Flash |
| Ollama (로컬) | 하드웨어 제한 | 무료 | — |
| llm + llm-ollama | 하드웨어 제한 | 무료 | — |
