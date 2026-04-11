# Branch 3.1: 외부 도구 & 셸 통합 — Rich Tool Ecosystem
> External Tool & Shell Integration Specialist
> 조사일: 2026-04-07

---

## 1. Git 통합 (subprocess 직접 호출 권장)

### gitpython vs subprocess 판정

**gitpython 사용 금지 권고**:
- `CVE-2024-22190`: Windows에서 `GIT_PYTHON_GIT_EXECUTABLE` 환경 변수 통한 임의 명령 실행 (3.1.41 이전)
- 내부적으로 결국 subprocess 호출 → 추상화 비용만 있음
- shell=False 원칙을 고수하는 이 시스템에는 subprocess 직접 호출이 더 안전

### GitCheckpointManager (subprocess 직접)

```python
# git_checkpoint.py
import re
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CheckpointResult:
    success: bool
    commit_hash: Optional[str]
    message: str
    error: Optional[str] = None


class GitCheckpointManager:
    """
    subprocess(shell=False)만 사용하는 Git 체크포인트 매니저.
    외부 의존성 없음. Python stdlib만 사용.
    """

    ALLOWED_SUBCOMMANDS = frozenset([
        "add", "commit", "stash", "checkout",
        "reset", "log", "status", "diff", "rev-parse",
        "show", "tag",
    ])

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self._git_bin = self._find_git_binary()

    def _find_git_binary(self) -> str:
        git_path = shutil.which("git")
        if not git_path:
            raise RuntimeError("git binary not found in PATH")
        return git_path

    def _run_git(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        if not args:
            raise ValueError("git args must not be empty")
        subcommand = args[0]
        if subcommand not in self.ALLOWED_SUBCOMMANDS:
            raise PermissionError(f"git '{subcommand}' not allowed. Allowed: {sorted(self.ALLOWED_SUBCOMMANDS)}")

        return subprocess.run(
            [self._git_bin] + args,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,   # 핵심: 절대 True 금지
            check=check,
        )

    def create_checkpoint(self, message: str) -> CheckpointResult:
        safe_message = message.replace("`", "").replace("$", "").replace(";", "")
        full_message = f"[autoflow-checkpoint] {safe_message}"

        try:
            status = self._run_git(["status", "--porcelain"], check=False)
            if not status.stdout.strip():
                head = self._run_git(["rev-parse", "HEAD"])
                return CheckpointResult(True, head.stdout.strip(), "No changes, returning current HEAD")

            self._run_git(["add", "--all"])
            self._run_git(["commit", "-m", full_message])
            result = self._run_git(["rev-parse", "HEAD"])
            commit_hash = result.stdout.strip()
            return CheckpointResult(True, commit_hash, f"Checkpoint: {commit_hash[:8]}")

        except subprocess.CalledProcessError as e:
            return CheckpointResult(False, None, "Checkpoint failed", e.stderr)
        except subprocess.TimeoutExpired:
            return CheckpointResult(False, None, "Git timed out", "timeout 60s")

    def rollback_to(self, commit_hash: str) -> CheckpointResult:
        if not re.fullmatch(r"[0-9a-f]{7,40}", commit_hash, re.IGNORECASE):
            raise ValueError(f"Invalid commit hash: {commit_hash!r}")

        try:
            self._run_git(["stash", "push", "-m", "autoflow-pre-rollback"], check=False)
            self._run_git(["checkout", commit_hash])
            return CheckpointResult(True, commit_hash, f"Rolled back to {commit_hash[:8]}")
        except subprocess.CalledProcessError as e:
            return CheckpointResult(False, None, "Rollback failed", e.stderr)
```

---

## 2. SafeFileOperations

```python
# safe_file_ops.py
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional


class PathTraversalError(Exception):
    pass


class SafeFileOperations:
    """경로 검증, 백업, 원자적 연산을 갖춘 안전한 파일 작업"""

    def __init__(self, base_dir: str, trash_dir: Optional[str] = None):
        self.base_dir = Path(base_dir).resolve()
        self.trash_dir = Path(trash_dir).resolve() if trash_dir else self.base_dir / ".autoflow_trash"
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path(self, path: str) -> Path:
        resolved = Path(path).resolve()
        try:
            resolved.relative_to(self.base_dir)
        except ValueError:
            raise PathTraversalError(f"Path '{resolved}' outside base '{self.base_dir}'")
        return resolved

    def safe_copy(self, src: str, dst: str) -> None:
        src_path = self._validate_path(src)
        dst_path = self._validate_path(dst)
        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src_path}")
        if dst_path.exists():
            self._backup_to_trash(dst_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)

    def safe_move(self, src: str, dst: str) -> None:
        src_path = self._validate_path(src)
        dst_path = self._validate_path(dst)
        if not src_path.exists():
            raise FileNotFoundError(f"Source not found: {src_path}")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.replace(src_path, dst_path)
        except OSError:
            with tempfile.NamedTemporaryFile(dir=dst_path.parent, delete=False, suffix=".tmp") as tmp:
                tmp_path = Path(tmp.name)
            try:
                shutil.copy2(src_path, tmp_path)
                os.replace(tmp_path, dst_path)
                src_path.unlink()
            except Exception:
                tmp_path.unlink(missing_ok=True)
                raise

    def safe_delete(self, path: str) -> Path:
        target = self._validate_path(path)
        if not target.exists():
            raise FileNotFoundError(f"Target not found: {target}")
        return self._backup_to_trash(target)

    def _backup_to_trash(self, path: Path) -> Path:
        import time
        timestamp = int(time.time() * 1000)
        backup_path = self.trash_dir / f"{path.name}.{timestamp}"
        shutil.move(str(path), str(backup_path))
        return backup_path

    def read_file(self, path: str, encoding: str = "utf-8") -> str:
        target = self._validate_path(path)
        if not target.is_file():
            raise IsADirectoryError(f"Not a file: {target}")
        return target.read_text(encoding=encoding)

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> None:
        target = self._validate_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding=encoding, dir=target.parent, delete=False, suffix=".tmp"
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        os.replace(tmp_path, target)

    @staticmethod
    def file_hash(path: str, algorithm: str = "sha256") -> str:
        h = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
```

---

## 3. PythonExecutor (sys.executable 사용)

```python
# python_executor.py
import json, os, subprocess, sys, tempfile, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False
    output_data: Optional[dict] = field(default=None)


class PythonExecutor:
    """
    subprocess로 Python 스크립트 격리 실행.
    sys.executable 사용 (PATH 오염 방지 핵심).
    """

    SAFE_ENV_KEYS = frozenset([
        "PATH", "HOME", "USER", "LANG", "LC_ALL",
        "TMPDIR", "TEMP", "TMP", "VIRTUAL_ENV", "PYTHONPATH",
    ])

    def __init__(self, default_timeout: int = 300, max_output_bytes: int = 10 * 1024 * 1024):
        self._timeout = default_timeout
        self._max_output = max_output_bytes
        self._python_bin = sys.executable  # PATH 오염 방지

    def _build_safe_env(self, extra_env: Optional[dict] = None) -> dict:
        safe = {k: v for k, v in os.environ.items() if k in self.SAFE_ENV_KEYS}
        if extra_env:
            import re
            for k, v in extra_env.items():
                if re.fullmatch(r"[A-Z_][A-Z0-9_]*", k, re.IGNORECASE):
                    safe[k] = str(v)
        return safe

    def execute_script(
        self,
        script_path: str,
        args: list[str] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env_override: Optional[dict] = None,
        venv_path: Optional[str] = None,
    ) -> ExecutionResult:
        script = Path(script_path).resolve()
        if not script.is_file():
            raise FileNotFoundError(f"Script not found: {script}")

        python_bin = self._get_venv_python(venv_path) if venv_path else self._python_bin
        cmd = [python_bin, str(script)] + (args or [])
        env = self._build_safe_env(env_override)

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True,
                timeout=timeout or self._timeout,
                cwd=cwd or str(script.parent),
                env=env,
                shell=False,
            )
            duration_ms = (time.monotonic() - start) * 1000

            output_data = None
            stdout = result.stdout
            if stdout.strip().startswith(("{", "[")):
                try:
                    output_data = json.loads(stdout)
                except json.JSONDecodeError:
                    pass

            return ExecutionResult(
                returncode=result.returncode,
                stdout=stdout[:self._max_output],
                stderr=result.stderr[:self._max_output],
                duration_ms=duration_ms,
                output_data=output_data,
            )
        except subprocess.TimeoutExpired as e:
            return ExecutionResult(-1, "", "", (time.monotonic() - start) * 1000, timed_out=True)

    def _get_venv_python(self, venv_path: str) -> str:
        venv = Path(venv_path).resolve()
        python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        if not python.exists():
            raise FileNotFoundError(f"venv Python not found: {python}")
        return str(python)
```

---

## 4. watchdog 파일 감시 (Rich 방식)

```python
# file_watcher.py
import threading, time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer


class WorkflowTriggerHandler(FileSystemEventHandler):
    """파일 변경 → 워크플로우 트리거 (debounce 포함)"""

    def __init__(self, callback: Callable, patterns: list[str] = None, debounce: float = 0.5):
        super().__init__()
        self._callback = callback
        self._patterns = patterns or ["*.yaml", "*.csv", "*.json"]
        self._debounce = debounce
        self._pending: dict[str, float] = {}
        self._lock = threading.Lock()

    def _matches(self, path: str) -> bool:
        from fnmatch import fnmatch
        return any(fnmatch(Path(path).name, p) for p in self._patterns)

    def _debounced_trigger(self, path: str, event_type: str) -> None:
        with self._lock:
            self._pending[path] = time.monotonic() + self._debounce

        def _fire():
            time.sleep(self._debounce)
            with self._lock:
                if time.monotonic() >= self._pending.get(path, 0):
                    self._pending.pop(path, None)
                    self._callback(path, event_type)

        threading.Thread(target=_fire, daemon=True).start()

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._matches(event.src_path):
            self._debounced_trigger(event.src_path, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._matches(event.src_path):
            self._debounced_trigger(event.src_path, "modified")


class FileWatcher:
    def __init__(self, watch_dir: str, callback: Callable):
        self._observer = Observer()
        self._observer.schedule(
            WorkflowTriggerHandler(callback),
            str(Path(watch_dir).resolve()),
            recursive=True
        )

    def start(self): self._observer.start()
    def stop(self): self._observer.stop(); self._observer.join()
    def __enter__(self): self.start(); return self
    def __exit__(self, *args): self.stop()
```

---

## 5. 안전한 HTTP 클라이언트 (웹 스크래핑)

```python
# web_client.py
import re, time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx

class RateLimiter:
    def __init__(self, rps: float = 1.0):
        self._rps = rps
        self._last: dict[str, float] = {}

    def wait(self, domain: str):
        now = time.monotonic()
        wait = (1.0 / self._rps) - (now - self._last.get(domain, 0))
        if wait > 0:
            time.sleep(wait)
        self._last[domain] = time.monotonic()


class SafeWebClient:
    """robots.txt 준수 + rate limiting + SSRF 방지 HTTP 클라이언트"""

    BLOCKED_HOSTS = re.compile(
        r"^(localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|::1|0\.0\.0\.0)"
    )

    def __init__(self, user_agent: str = "AutoflowBot/1.0", rate_limit_rps: float = 1.0):
        self._headers = {"User-Agent": user_agent}
        self._rate_limiter = RateLimiter(rate_limit_rps)
        self._robots_cache: dict = {}

    def _validate_url(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Only http/https allowed: {parsed.scheme}")
        if self.BLOCKED_HOSTS.match(parsed.hostname or ""):
            raise PermissionError(f"SSRF 방지: {parsed.hostname}")
        return url

    def get(self, url: str) -> httpx.Response:
        url = self._validate_url(url)
        self._rate_limiter.wait(urlparse(url).netloc)
        with httpx.Client(headers=self._headers, timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            if len(response.content) > 50 * 1024 * 1024:
                raise ValueError("Response too large (>50MB)")
            return response
```

---

## 패키지 버전 참조

| 패키지 | 버전 | 비고 |
|---|---|---|
| gitpython | 3.1.43+ | CVE-2024-22190 패치 필수 (사용 지양) |
| watchdog | 4.0.2+ | inotify/FSEvents/ReadDirectoryChanges |
| httpx | 0.27.0+ | async/sync, HTTP/2 |
| polars | 0.20.31+ | Rust 기반 고속 |
| pandas | 2.2.2+ | 생태계 호환 |
| pyarrow | 16.1.0+ | Parquet I/O |
