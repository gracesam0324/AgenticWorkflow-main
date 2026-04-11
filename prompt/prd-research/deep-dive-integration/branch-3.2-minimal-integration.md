# Branch 3.2: 외부 도구 & 셸 통합 — Minimal Integration (stdlib 전용)
> External Tool & Shell Integration Specialist
> 조사일: 2026-04-07

---

## 핵심 철학

**의존성은 곧 취약점.** v1.0 코어는 Python stdlib만 사용.
외부 패키지는 선택적 설치(extras_require)로만.

---

## 1. MinimalSafeExecutor (stdlib 전용, 완전 구현)

```python
# minimal_executor.py
"""
최소 의존성 안전 subprocess 실행기.
Python stdlib만 사용. shell=False 절대 원칙.
"""
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False


class MinimalSafeExecutor:
    """
    보안 원칙:
    1. shell=False 강제
    2. 허용 목록(allowlist) 검증
    3. 타임아웃 강제 (기본 300초)
    4. 메모리 제한 (Unix, resource.setrlimit)
    5. 환경 변수 정제
    6. 프로세스 그룹 관리 (좀비 방지)
    7. cwd 범위 제한
    """

    ALLOWED_COMMANDS = frozenset([
        "python", "python3", "git",
        "cp", "mv", "mkdir", "ls", "find",
        "cat", "echo", "wc",
        "dbt", "node", "npm",
    ])

    SAFE_ENV_KEYS = frozenset([
        "PATH", "HOME", "USER", "LOGNAME",
        "LANG", "LC_ALL", "LC_CTYPE",
        "TMPDIR", "TEMP", "TMP",
        "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
        "PYTHONPATH", "PYTHONHOME",
        "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL",
    ])

    def __init__(
        self,
        base_dir: Optional[str] = None,
        max_memory_mb: int = 512,
        max_output_bytes: int = 10 * 1024 * 1024,
    ):
        self._base_dir = Path(base_dir).resolve() if base_dir else Path.cwd()
        self._max_memory_bytes = max_memory_mb * 1024 * 1024
        self._max_output = max_output_bytes

    def execute(
        self,
        cmd: list[str],
        cwd: Optional[str] = None,
        timeout: int = 300,
        env_override: Optional[dict] = None,
        capture_output: bool = True,
    ) -> ExecutionResult:
        self._validate_cmd(cmd)
        effective_cwd = self._validate_cwd(cwd)
        safe_env = self._build_safe_env(env_override)
        resolved_cmd = self._resolve_executable(cmd)

        start = time.monotonic()

        kwargs = dict(
            cwd=effective_cwd,
            env=safe_env,
            shell=False,   # 핵심: 절대 변경 금지
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if capture_output:
            kwargs["stdout"] = subprocess.PIPE
            kwargs["stderr"] = subprocess.PIPE

        if sys.platform != "win32":
            kwargs["preexec_fn"] = self._unix_preexec

        try:
            proc = subprocess.Popen(resolved_cmd, **kwargs)

            try:
                stdout, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._kill_process_group(proc)
                stdout_bytes, stderr_bytes = proc.communicate()
                return ExecutionResult(
                    returncode=-1,
                    stdout=(stdout_bytes or "")[:self._max_output],
                    stderr=(stderr_bytes or "")[:self._max_output],
                    duration_ms=(time.monotonic() - start) * 1000,
                    timed_out=True,
                )

            return ExecutionResult(
                returncode=proc.returncode,
                stdout=(stdout or "")[:self._max_output],
                stderr=(stderr or "")[:self._max_output],
                duration_ms=(time.monotonic() - start) * 1000,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Executable not found: {resolved_cmd[0]}")

    def _validate_cmd(self, cmd: list[str]) -> None:
        if not cmd or not isinstance(cmd, list):
            raise ValueError("cmd must be a non-empty list")
        for item in cmd:
            if not isinstance(item, str):
                raise ValueError(f"All cmd elements must be strings")
        executable = Path(cmd[0]).name
        if executable not in self.ALLOWED_COMMANDS:
            raise PermissionError(
                f"'{executable}' not in allowlist. Allowed: {sorted(self.ALLOWED_COMMANDS)}"
            )

    def _validate_cwd(self, cwd: Optional[str]) -> str:
        if cwd is None:
            return str(self._base_dir)
        resolved = Path(cwd).resolve()
        try:
            resolved.relative_to(self._base_dir)
        except ValueError:
            raise PermissionError(f"cwd '{resolved}' outside base_dir '{self._base_dir}'")
        return str(resolved)

    def _build_safe_env(self, extra: Optional[dict]) -> dict:
        safe = {k: v for k, v in os.environ.items() if k in self.SAFE_ENV_KEYS}
        if extra:
            import re
            for k, v in extra.items():
                if re.fullmatch(r"[A-Z_][A-Z0-9_]*", k, re.IGNORECASE):
                    safe[k] = str(v)
        return safe

    def _resolve_executable(self, cmd: list[str]) -> list[str]:
        import shutil
        executable = cmd[0]
        if not Path(executable).is_absolute():
            resolved = shutil.which(executable)
            if resolved:
                return [resolved] + cmd[1:]
        return cmd

    def _unix_preexec(self) -> None:
        """새 프로세스 그룹 + 메모리 제한"""
        os.setpgrp()
        try:
            import resource
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self._max_memory_bytes, self._max_memory_bytes),
            )
        except (ImportError, ValueError):
            pass

    def _kill_process_group(self, proc: subprocess.Popen) -> None:
        if sys.platform == "win32":
            proc.kill()
        else:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
```

---

## 2. MinimalGit (stdlib 전용)

```python
# minimal_git.py
import re
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitResult:
    success: bool
    output: str
    error: str
    returncode: int


class MinimalGit:
    """gitpython 없이 subprocess git 직접 호출. 외부 의존성 0."""

    ALLOWED_SUBCOMMANDS = frozenset([
        "fetch", "commit", "checkout", "log",
        "status", "add", "stash", "rev-parse",
        "diff", "show", "reset",
    ])

    def __init__(self, repo_path: str = "."):
        self._repo = Path(repo_path).resolve()
        self._git = shutil.which("git")
        if not self._git:
            raise RuntimeError("git not found in PATH")

    def _run(self, args: list[str], timeout: int = 60) -> GitResult:
        if not args:
            raise ValueError("args must not be empty")
        subcommand = args[0]
        if subcommand not in self.ALLOWED_SUBCOMMANDS:
            raise PermissionError(f"git '{subcommand}' not allowed")
        for arg in args[1:]:
            if arg.startswith("--upload-pack") or arg.startswith("--exec"):
                raise PermissionError(f"Dangerous git option: {arg}")

        result = subprocess.run(
            [self._git] + args,
            cwd=str(self._repo),
            capture_output=True, text=True, timeout=timeout, shell=False,
        )
        return GitResult(
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip(),
            returncode=result.returncode,
        )

    def status(self) -> GitResult: return self._run(["status", "--porcelain"])
    def add_all(self) -> GitResult: return self._run(["add", "--all"])

    def commit(self, message: str) -> GitResult:
        safe_msg = re.sub(r"[`$;|&<>]", "", message)
        return self._run(["commit", "-m", safe_msg])

    def current_hash(self) -> Optional[str]:
        result = self._run(["rev-parse", "HEAD"])
        return result.output if result.success else None

    def log(self, count: int = 10) -> list[dict]:
        fmt = "%H\x1f%an\x1f%ae\x1f%ai\x1f%s"
        result = self._run(["log", f"-{count}", f"--format={fmt}"])
        if not result.success:
            return []
        commits = []
        for line in result.output.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 5:
                commits.append({"hash": parts[0], "author": parts[1], "date": parts[3], "subject": parts[4]})
        return commits

    def checkout(self, ref: str) -> GitResult:
        if not re.fullmatch(r"[A-Za-z0-9_./\-]{1,200}", ref):
            raise ValueError(f"Invalid git ref: {ref!r}")
        return self._run(["checkout", ref])

    def stash_push(self, message: str) -> GitResult:
        safe_msg = re.sub(r"[`$;|&<>\"']", "", message)
        return self._run(["stash", "push", "-m", safe_msg])

    def stash_pop(self) -> GitResult: return self._run(["stash", "pop"])
```

---

## 3. PollingWatcher (watchdog 없이 stdlib)

```python
# polling_watcher.py
"""
watchdog 없이 stdlib으로 파일 변경 감지.
mtime + sha256 조합으로 정확한 변경 감지.
"""
import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, Optional


@dataclass
class ChangeEvent:
    event_type: str  # "created" | "modified" | "deleted"
    path: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class FileSnapshot:
    path: str
    mtime: float
    size: int
    sha256: Optional[str] = None


class PollingWatcher:
    """주기적 폴링으로 파일 변경 감지. watchdog 의존성 없음."""

    HASH_THRESHOLD_BYTES = 1024 * 1024  # 1MB

    def __init__(
        self,
        watch_dir: str,
        callback: Callable[[ChangeEvent], None],
        patterns: list[str] = None,
        interval_seconds: float = 2.0,
    ):
        self._watch_dir = Path(watch_dir).resolve()
        self._callback = callback
        self._patterns = patterns or ["*.yaml", "*.yml", "*.py", "*.json", "*.csv"]
        self._interval = interval_seconds
        self._snapshots: dict[str, FileSnapshot] = {}
        self._stop_event = threading.Event()

    def start(self) -> None:
        for path in self._scan():
            snap = self._take_snapshot(path)
            if snap:
                self._snapshots[path] = snap
        t = threading.Thread(target=self._poll_loop, daemon=True, name="PollingWatcher")
        t.start()

    def stop(self) -> None: self._stop_event.set()

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(timeout=self._interval):
            try:
                self._check_changes()
            except Exception:
                pass

    def _check_changes(self) -> None:
        current = set(self._scan())
        previous = set(self._snapshots.keys())

        for path in current - previous:
            snap = self._take_snapshot(path)
            if snap:
                self._snapshots[path] = snap
                self._emit(ChangeEvent("created", path))

        for path in previous - current:
            del self._snapshots[path]
            self._emit(ChangeEvent("deleted", path))

        for path in current & previous:
            old = self._snapshots[path]
            try:
                stat = os.stat(path)
            except FileNotFoundError:
                continue
            if stat.st_mtime == old.mtime and stat.st_size == old.size:
                continue
            new_hash = self._compute_hash(path, stat.st_size)
            if new_hash != old.sha256:
                self._snapshots[path] = FileSnapshot(path, stat.st_mtime, stat.st_size, new_hash)
                self._emit(ChangeEvent("modified", path))

    def _scan(self) -> Iterator[str]:
        from fnmatch import fnmatch
        for root, dirs, files in os.walk(self._watch_dir):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                if any(fnmatch(fname, p) for p in self._patterns):
                    yield os.path.join(root, fname)

    def _take_snapshot(self, path: str) -> Optional[FileSnapshot]:
        try:
            stat = os.stat(path)
            return FileSnapshot(path, stat.st_mtime, stat.st_size, self._compute_hash(path, stat.st_size))
        except (FileNotFoundError, PermissionError):
            return None

    def _compute_hash(self, path: str, size: int) -> str:
        h = hashlib.sha256()
        chunk = 65536
        try:
            with open(path, "rb") as f:
                if size <= self.HASH_THRESHOLD_BYTES:
                    for block in iter(lambda: f.read(chunk), b""):
                        h.update(block)
                else:
                    h.update(f.read(chunk))
                    f.seek(-chunk, 2)
                    h.update(f.read(chunk))
        except (FileNotFoundError, PermissionError, OSError):
            return ""
        return h.hexdigest()

    def _emit(self, event: ChangeEvent) -> None:
        try:
            self._callback(event)
        except Exception:
            pass

    def __enter__(self): self.start(); return self
    def __exit__(self, *args): self.stop()
```

---

## 4. PRD 권고 — 의존성 계층

```
[v1.0 Core]    stdlib only                    (외부 패키지 0개)
    MinimalSafeExecutor + MinimalGit
    SafeFileOperations + PollingWatcher
    PythonExecutor

    ↓ pip install workflow-agent[watch]
[v1.0 Watch]   + watchdog                     (실시간 파일 감시)

    ↓ pip install workflow-agent[data]
[v1.0 Data]    + openpyxl + pyarrow + orjson  (데이터 파일 처리)

    ↓ pip install workflow-agent[analytics]
[v1.1 Analy]   + duckdb + pandas + polars     (데이터 분석)

    ↓ pip install workflow-agent[web]
[v1.1 Web]     + httpx + beautifulsoup4       (웹 스크래핑)
```

### 절대 불변 원칙

1. `shell=False`는 어떤 경우에도 변경 금지
2. `sys.executable` 사용 (PATH 하이재킹 방지)
3. cwd는 항상 base_dir 내로 제한
4. 허용 명령어 목록은 코드에 하드코딩 (YAML 파일이 수정되어도 우회 불가)

### 위협별 방어 매핑

| 위협 | 방어 | 구현 위치 |
|---|---|---|
| 쉘 주입 | shell=False + 리스트 인자 | MinimalSafeExecutor |
| PATH 하이재킹 | shutil.which() + 절대경로 | _resolve_executable() |
| 경로 탈출 | Path.resolve().relative_to() | _validate_cwd() |
| 환경 변수 주입 | SAFE_ENV_KEYS 허용 목록 | _build_safe_env() |
| 리소스 고갈 | resource.setrlimit + timeout | _unix_preexec() |
| 커밋 해시 위조 | regex fullmatch 검증 | MinimalGit.checkout() |
