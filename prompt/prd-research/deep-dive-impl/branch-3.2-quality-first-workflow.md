## BRANCH 3.2: 견고한 개발 프로세스 (Quality-First Implementation)

---

### 1. TDD로 AI 시스템 구현하기

#### AI 출력을 포함한 TDD 패턴

AI 시스템 TDD의 핵심은 **AI를 의존성으로 주입**하고 **인터페이스로 추상화**하는 것입니다.

```python
# tests/test_workflow_planner_tdd.py
"""
TDD 예시: WorkflowPlanner 개발 과정
Red → Green → Refactor 사이클
"""
import pytest
from unittest.mock import MagicMock
from src.models.workflow_plan import WorkflowPlan, WorkflowStep, StepType


# === RED: 먼저 테스트 작성 (구현 없음) ===

class TestWorkflowPlannerContract:
    """
    WorkflowPlanner의 계약(Contract) 테스트
    구현 방법이 아닌 '무엇을 해야 하는가'를 정의
    """
    
    def test_generates_plan_from_simple_input(self, mock_planner):
        """단순 입력에서 유효한 플랜 생성"""
        plan = mock_planner.generate("폴더 백업")
        
        assert isinstance(plan, WorkflowPlan)
        assert len(plan.steps) >= 1
        assert plan.name  # 이름이 있어야 함
    
    def test_plan_steps_have_required_fields(self, mock_planner):
        """각 스텝에 필수 필드가 있어야 함"""
        plan = mock_planner.generate("파일 정리")
        
        for step in plan.steps:
            assert step.id, "id 필수"
            assert step.type in StepType, "유효한 타입 필수"
            assert step.command, "command 필수"
    
    def test_dangerous_operation_requires_confirmation(self, mock_planner_with_dangerous_response):
        """위험한 작업은 confirmation 필요"""
        plan = mock_planner_with_dangerous_response.generate("오래된 파일 삭제")
        
        dangerous_steps = [s for s in plan.steps if "rm" in s.command or "del" in s.command]
        for step in dangerous_steps:
            assert step.requires_confirmation, \
                f"스텝 '{step.id}'의 위험 명령어에 confirmation 없음"
    
    def test_ai_failure_raises_meaningful_error(self, failing_mock_planner):
        """AI 실패 시 명확한 에러 메시지"""
        with pytest.raises(Exception) as exc_info:
            failing_mock_planner.generate("테스트")
        
        # 기술적 에러가 아닌 사용자 친화적 메시지
        assert "API" in str(exc_info.value) or "생성 실패" in str(exc_info.value)


# === 픽스처: AI 응답 모킹 ===

@pytest.fixture
def mock_ai_client():
    """WorkflowPlanner에 주입할 AI 클라이언트 모킹"""
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='''
{
  "name": "파일_백업",
  "steps": [
    {
      "id": "create_backup_dir",
      "type": "shell",
      "name": "백업 디렉토리 생성",
      "command": "mkdir -p ~/backup",
      "depends_on": [],
      "timeout_seconds": 30,
      "requires_confirmation": false
    }
  ]
}
''')]
    )
    return client


@pytest.fixture
def mock_planner(mock_ai_client):
    from src.planner.workflow_planner import WorkflowPlanner
    return WorkflowPlanner(ai_client=mock_ai_client)


@pytest.fixture
def failing_mock_planner():
    """항상 실패하는 AI 클라이언트"""
    import anthropic
    client = MagicMock()
    client.messages.create.side_effect = anthropic.APIError(
        "rate limit exceeded", response=MagicMock(), body={}
    )
    from src.planner.workflow_planner import WorkflowPlanner
    return WorkflowPlanner(ai_client=client)
```

#### Property-based Testing (hypothesis)

```python
# tests/test_properties.py
"""
Property-based Testing: 
'어떤 유효한 입력에도 시스템이 망가지지 않는다'는 속성 검증
"""
from hypothesis import given, settings, strategies as st
import pytest
from src.models.workflow_plan import WorkflowPlan, WorkflowStep, StepType
from src.parser import YAMLParser


# YAML 파서 속성 테스트
class TestYAMLParserProperties:
    
    @given(st.text(min_size=0, max_size=10000))
    @settings(max_examples=200, deadline=500)
    def test_parser_never_crashes(self, random_input: str):
        """어떤 입력에도 파서가 크래시하지 않음 (에러는 허용)"""
        parser = YAMLParser()
        try:
            parser.parse(random_input)
        except Exception as e:
            # 에러는 OK, 하지만 TypeError/AttributeError는 버그
            assert not isinstance(e, (TypeError, AttributeError)), \
                f"파서 내부 버그: {type(e).__name__}: {e}"
    
    @given(st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd')),
                min_size=1, max_size=20),
        min_size=1, max_size=10,
        unique=True
    ))
    def test_step_ids_must_be_unique(self, step_ids: list[str]):
        """중복 스텝 ID는 항상 검증 실패"""
        # 첫 번째 ID를 복제하여 중복 생성
        duplicate_ids = step_ids + [step_ids[0]]
        
        with pytest.raises(Exception):
            WorkflowPlan(
                name="test",
                steps=[
                    WorkflowStep(
                        id=id_, type=StepType.SHELL,
                        name=f"step {id_}", command="echo test"
                    )
                    for id_ in duplicate_ids
                ]
            )


# 커맨드 검증 속성 테스트
class TestCommandValidationProperties:
    
    SAFE_CHARS = st.text(
        alphabet=st.characters(
            whitelist_categories=('Ll', 'Lu', 'Nd'),
            whitelist_characters=' -_/.'
        ),
        min_size=3, max_size=100
    )
    
    @given(SAFE_CHARS)
    def test_safe_commands_always_pass(self, command: str):
        """안전한 문자만 포함된 명령어는 통과"""
        # 위험 패턴이 없는 명령어는 검증 통과
        step = WorkflowStep(
            id="test_step", type=StepType.SHELL,
            name="test", command=f"echo {command}"
        )
        assert step.command is not None
```

---

### 2. 안전 관련 코드 구현 기법

#### 입력 검증 레이어 (Pydantic v2 완전 구현)

```python
# src/security/input_validator.py
"""
Security-by-Design: 모든 외부 입력의 단일 검증 진입점
원칙: 허용 목록(allowlist) 기반, 기본값은 거부
"""
from __future__ import annotations
import re
import os
from pathlib import Path, PurePosixPath
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.functional_validators import AfterValidator


# ===== 타입 레벨 검증 =====

def _validate_safe_string(v: str) -> str:
    """SQL 인젝션, 쉘 인젝션 공통 방어"""
    INJECTION_PATTERNS = [
        r'[;&|`$]',           # 쉘 메타문자
        r'\$\(',              # 명령어 치환
        r'\bSELECT\b',        # SQL (대소문자 무관)
        r'\bDROP\b',
        r'<script',           # XSS
    ]
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, v, re.IGNORECASE):
            raise ValueError(f"허용되지 않는 문자 패턴 포함: {pattern}")
    return v


SafeString = Annotated[str, AfterValidator(_validate_safe_string)]


def _validate_safe_path(v: str) -> str:
    """경로 탐색 공격 방어 + 허용 경로 확인"""
    # 정규화
    try:
        path = Path(v).resolve()
    except (ValueError, OSError) as e:
        raise ValueError(f"유효하지 않은 경로: {e}")
    
    # 경로 탐색 감지
    if ".." in str(v):
        raise ValueError("경로에 '..' 포함 불가")
    
    # 허용된 기본 경로 확인
    home = Path.home()
    allowed_bases = [
        home / ".workflow",
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        Path("/tmp"),
    ]
    
    # 커스텀 허용 경로 (환경변수)
    if extra := os.getenv("WORKFLOW_ALLOWED_PATHS"):
        allowed_bases.extend(Path(p) for p in extra.split(":"))
    
    is_allowed = any(
        str(path).startswith(str(base)) 
        for base in allowed_bases
    )
    
    if not is_allowed:
        raise ValueError(
            f"허용되지 않은 경로: {path}\n"
            f"허용 경로: {[str(b) for b in allowed_bases]}"
        )
    
    return str(path)


SafePath = Annotated[str, AfterValidator(_validate_safe_path)]


# ===== 요청 모델 =====

class UserWorkflowRequest(BaseModel):
    """사용자 자연어 요청 - 외부 입력 진입점"""
    
    user_input: str = Field(
        min_length=5,
        max_length=2000,
        description="사용자의 자연어 워크플로우 요청"
    )
    working_directory: SafePath | None = None
    dry_run: bool = False
    
    @field_validator('user_input')
    @classmethod
    def sanitize_user_input(cls, v: str) -> str:
        # 앞뒤 공백 제거
        v = v.strip()
        # 연속 공백 정규화
        v = re.sub(r'\s+', ' ', v)
        # NULL 바이트 제거
        v = v.replace('\x00', '')
        return v
    
    @field_validator('user_input')
    @classmethod
    def check_not_prompt_injection(cls, v: str) -> str:
        """프롬프트 인젝션 패턴 감지"""
        INJECTION_INDICATORS = [
            "ignore previous instructions",
            "disregard your instructions", 
            "you are now",
            "act as if",
            "forget everything",
            "new system prompt",
            "이전 지시를 무시",
            "시스템 프롬프트를 변경",
        ]
        v_lower = v.lower()
        for indicator in INJECTION_INDICATORS:
            if indicator.lower() in v_lower:
                raise ValueError(
                    "프롬프트 인젝션 시도가 감지되었습니다. "
                    "워크플로우 자동화 요청만 입력해주세요."
                )
        return v
```

#### 명령어 인젝션 방어 코드

```python
# src/security/command_sanitizer.py
"""
명령어 실행 보안 레이어
핵심: shell=False + 인수 분리로 인젝션 원천 차단
"""
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SafeCommandResult:
    stdout: str
    stderr: str
    returncode: int
    command: list[str]  # 실제 실행된 명령어 (감사 로그용)


class SafeCommandExecutor:
    """
    보안 명령어 실행기
    모든 명령어는 이 클래스를 통해서만 실행
    """
    
    # 절대 실행 불가 명령어
    FORBIDDEN_COMMANDS = frozenset([
        "rm", "del", "format", "mkfs", "dd",
        "chmod", "chown", "sudo", "su",
        "passwd", "visudo", "crontab",
        "iptables", "ufw",
    ])
    
    # 허용된 명령어 목록 (allowlist 방식)
    ALLOWED_COMMANDS = frozenset([
        "cp", "mv", "mkdir", "ls", "dir",
        "echo", "cat", "head", "tail", "grep",
        "find", "wc", "sort", "uniq", "diff",
        "zip", "unzip", "tar", "gzip",
        "python", "python3", "pip",
        "git",
        "ffmpeg", "convert",  # 미디어 처리
    ])
    
    def __init__(
        self,
        working_dir: Path | None = None,
        timeout: int = 60,
        use_allowlist: bool = True,
    ):
        self.working_dir = working_dir or Path.home() / ".workflow" / "workspace"
        self.timeout = timeout
        self.use_allowlist = use_allowlist
    
    def execute(self, command: str) -> SafeCommandResult:
        """
        보안 명령어 실행
        
        Args:
            command: 실행할 명령어 문자열
        
        Raises:
            SecurityError: 금지된 명령어 또는 패턴
            subprocess.TimeoutExpired: 타임아웃
        """
        # 1. 파싱 (쉘 메타문자 무력화)
        try:
            args = shlex.split(command)  # POSIX 방식 분리
        except ValueError as e:
            raise SecurityError(f"명령어 파싱 실패: {e}")
        
        if not args:
            raise SecurityError("빈 명령어")
        
        base_cmd = Path(args[0]).name.lower()  # 경로 제거, 소문자화
        
        # 2. 금지 목록 확인
        if base_cmd in self.FORBIDDEN_COMMANDS:
            raise SecurityError(
                f"'{base_cmd}'는 보안 정책으로 실행이 금지됩니다.\n"
                f"이 작업이 필요하다면 수동으로 실행해주세요."
            )
        
        # 3. 허용 목록 확인 (allowlist 모드)
        if self.use_allowlist and base_cmd not in self.ALLOWED_COMMANDS:
            raise SecurityError(
                f"'{base_cmd}'는 허용 목록에 없습니다.\n"
                f"허용된 명령어: {sorted(self.ALLOWED_COMMANDS)}"
            )
        
        # 4. 인수 안전성 확인 (경로 탐색 방어)
        for arg in args[1:]:
            if ".." in arg:
                raise SecurityError(f"인수에 경로 탐색('..')이 포함됨: {arg}")
        
        # 5. 실행 (shell=False 필수!)
        result = subprocess.run(
            args,                          # 리스트 형태
            shell=False,                   # 핵심: 쉘 인터프리터 우회 방지
            capture_output=True,
            text=True,
            timeout=self.timeout,
            cwd=str(self.working_dir),
        )
        
        return SafeCommandResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            command=args,
        )


class SecurityError(Exception):
    """보안 정책 위반"""
    pass
```

---

### 3. 코드 품질 자동화 (완전한 설정)

#### ruff 린팅 + 포맷 설정

```toml
# pyproject.toml (품질 도구 통합 설정)

[tool.ruff]
target-version = "py311"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # bugbear
    "S",    # bandit (보안)
    "ANN",  # annotations
    "RUF",  # ruff-specific
    "PT",   # pytest style
]
ignore = [
    "S101",   # assert 사용 허용 (테스트에서 필요)
    "ANN101", # self 타입 힌트 불필요
    "ANN102", # cls 타입 힌트 불필요
    "E501",   # 긴 줄 허용 (ruff format이 처리)
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "ANN"]  # 테스트에서 보안/타입 체크 완화
"spikes/**" = ["ALL"]       # 스파이크는 검사 제외

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

#### mypy 타입 체크 설정

```toml
# pyproject.toml 계속

[tool.mypy]
python_version = "3.11"
strict = true                     # 최대 엄격도
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true

# 외부 라이브러리 타입 스텁 없을 때
[[tool.mypy.overrides]]
module = ["yaml.*", "anthropic.*"]
ignore_missing_imports = true

# 테스트는 완화
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

#### bandit 보안 스캔 설정

```toml
# pyproject.toml 계속

[tool.bandit]
targets = ["src"]
skips = [
    "B101",  # assert_used: 테스트에서 허용
    "B404",  # subprocess import: 의도적 사용
]
severity = "medium"  # MEDIUM 이상만 리포트

[tool.bandit.assert_used]
skips = ["*_test.py", "test_*.py"]
```

---

### 4. 문서화 코드 연동

#### ADR (Architecture Decision Record) 구조

```
docs/adr/
├── 0001-use-yaml-for-workflow-plans.md
├── 0002-claude-api-for-planning.md
├── 0003-pydantic-v2-for-validation.md
└── template.md
```

```markdown
<!-- docs/adr/0002-claude-api-for-planning.md -->
# ADR-0002: Claude API를 워크플로우 플랜 생성에 사용

## 상태
채택됨 (2025-01-20)

## 컨텍스트
자연어 입력을 구조화된 YAML 워크플로우로 변환하는 방법이 필요합니다.
옵션:
- A) 규칙 기반 파서 (NLP 없음)
- B) 로컬 LLM (ollama)
- C) Claude API

## 결정
**C) Claude API 사용**

## 근거
- 규칙 기반: 자연어 다양성 처리 불가
- 로컬 LLM: 8GB RAM에서 품질 불충분, 설치 복잡
- Claude API: 품질 최상, 개발 속도 빠름, 비용 월 $10 예상

## 결과
- 오프라인 사용 불가 → 오프라인 모드는 캐시된 플랜 사용으로 완화
- API 키 관리 필요 → Keyring 라이브러리로 OS 키체인에 저장
- 비용 발생 → 요청당 캐싱으로 반복 요청 최소화

## 재검토 시점
Month 4: 로컬 LLM 품질 재평가 (llama3.1 출시 이후)
```

#### docstring → 자동 문서화

```python
# src/planner/workflow_planner.py
"""
워크플로우 플래너 모듈

이 모듈은 사용자의 자연어 요청을 분석하여
실행 가능한 워크플로우 플랜을 생성합니다.

Example:
    >>> from src.planner import WorkflowPlanner
    >>> import anthropic
    >>> planner = WorkflowPlanner(ai_client=anthropic.Anthropic())
    >>> plan = planner.generate("Desktop PNG 파일 백업")
    >>> print(plan.name)
    'PNG_파일_백업'
"""
from __future__ import annotations
from typing import Protocol
import anthropic
from src.models.workflow_plan import WorkflowPlan
from src.ai.prompt_manager import PromptManager
from src.ai.deterministic_wrapper import StructuredAIClient, AIOutputError


class AIClientProtocol(Protocol):
    """AI 클라이언트 인터페이스 - 테스트 용이성을 위한 추상화"""
    
    @property
    def messages(self) -> object: ...


class WorkflowPlanner:
    """
    자연어 → 워크플로우 플랜 변환기
    
    Attributes:
        ai_client: Anthropic API 클라이언트
        prompt_manager: 프롬프트 버전 관리자
        max_retries: AI 출력 파싱 최대 재시도 횟수
    
    Raises:
        AIOutputError: AI가 유효한 플랜을 생성하지 못한 경우
        anthropic.APIError: API 호출 실패
    """
    
    def __init__(
        self,
        ai_client: anthropic.Anthropic | None = None,
        prompt_manager: PromptManager | None = None,
        max_retries: int = 3,
    ) -> None:
        self._client = StructuredAIClient(
            client=ai_client or anthropic.Anthropic(),
            max_retries=max_retries,
        )
        self._prompts = prompt_manager or PromptManager()
    
    def generate(self, user_request: str) -> WorkflowPlan:
        """
        자연어 요청으로부터 워크플로우 플랜을 생성합니다.
        
        Args:
            user_request: 사용자의 자연어 요청
                예: "Desktop의 모든 PNG 파일을 백업 폴더로 복사"
        
        Returns:
            검증된 WorkflowPlan 인스턴스
        
        Raises:
            AIOutputError: AI가 유효한 JSON을 반환하지 못한 경우
            ValueError: 생성된 플랜이 보안 검증을 통과하지 못한 경우
        
        Example:
            >>> plan = planner.generate("로그 파일 압축")
            >>> assert len(plan.steps) >= 1
            >>> assert all(s.type for s in plan.steps)
        """
        system_prompt = self._prompts.get("plan_generator")
        
        return self._client.generate_structured(
            prompt=user_request,
            output_schema=WorkflowPlan,
            system_prompt=system_prompt,
        )
```

---

### 5. CI/CD 파이프라인 구현

#### GitHub Actions 전체 파이프라인

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"
  # 로컬 AI 시스템 CI 특수 설정
  # 실제 AI API는 호출하지 않음 (모킹 사용)
  WF_TEST_MODE: "true"
  # API 키 없이 테스트 실행
  ANTHROPIC_API_KEY: "test-key-not-real"

jobs:
  # Job 1: 빠른 품질 검사 (병렬)
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Ruff lint check
        run: ruff check src tests
      
      - name: Ruff format check
        run: ruff format --check src tests
      
      - name: mypy type check
        run: mypy src --ignore-missing-imports
      
      - name: bandit security scan
        run: bandit -r src -c pyproject.toml

  # Job 2: 테스트 (품질 검사 통과 후)
  test:
    name: Tests
    needs: quality
    runs-on: ubuntu-latest
    strategy:
      matrix:
        # 로컬 AI 시스템: OS별 경로 처리 차이 테스트
        os: [ubuntu-latest, macos-latest, windows-latest]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: pip
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run unit + integration tests (no AI calls)
        run: |
          pytest -m "not golden and not slow" \
            --cov=src \
            --cov-report=xml \
            --cov-fail-under=70 \
            -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        if: matrix.os == 'ubuntu-latest'
        with:
          file: coverage.xml

  # Job 3: 보안 검사 (main 브랜치만)
  security:
    name: Security Audit
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: pip install -e ".[dev]" pip-audit
      
      - name: Dependency vulnerability scan
        run: pip-audit --strict
      
      - name: Check for secrets in code
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: HEAD~1

  # Job 4: 릴리즈 (태그 푸시 시)
  release:
    name: Build Release
    needs: [quality, test, security]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Build distribution
        run: |
          pip install build
          python -m build
      
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

**로컬 AI 시스템 CI 특수 고려사항:**

```yaml
# .github/workflows/golden-tests.yml
# 골든 테스트: 실제 AI API 호출 (주 1회, 수동 트리거)
name: Golden Tests (Weekly)

on:
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 오전 9시
  workflow_dispatch:       # 수동 트리거

jobs:
  golden:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run golden tests (real AI)
        env:
          # GitHub Secrets에 저장된 실제 API 키
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          pytest -m "golden" \
            --tb=long \
            -v \
            --junit-xml=golden-results.xml
      
      - name: Upload golden test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: golden-test-results
          path: golden-results.xml
      
      - name: Alert on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '⚠️ Golden Tests 실패 - AI 품질 저하 가능성',
              body: '주간 골든 테스트가 실패했습니다. AI 출력 품질을 확인하세요.',
              labels: ['ai-quality', 'urgent']
            })
```

---

## 결론: 두 Branch 비교 및 권장 방향

---

### 개발 일정 예측 비교

#### Branch 3.1 (Speed-First) - 월별 달성 가능 기능

```
Month 1: 핵심 동작 프로토타입
  ✓ Claude API 연동 + YAML 플랜 생성
  ✓ 기본 쉘 명령어 실행
  ✓ CLI 인터페이스 (typer)
  ✓ 스모크 테스트
  → 데모 가능한 버전

Month 2: 실용적 기능 확장
  ✓ 파일 작업 실행기 (복사/이동/삭제)
  ✓ Python 스크립트 실행
  ✓ 실행 히스토리 저장
  ✓ 에러 핸들링 기본
  ✓ Feature Flag 시스템
  → 개인 사용 가능 버전

Month 3: 안정화 + 품질
  ✓ 프롬프트 버전 관리
  ✓ 비결정성 처리 (재시도 로직)
  ✓ 기술 부채 상위 5개 해소
  ✓ 통합 테스트 15개
  → 일상 업무 자동화 사용

Month 4: 고급 기능
  ✓ 병렬 스텝 실행
  ✓ 컨텍스트 인식 (이전 실행 결과 참조)
  ✓ 워크플로우 템플릿 시스템
  → 복잡한 자동화 가능

Month 5: 마감 준비
  ✓ 보안 강화 (DEBT 해소)
  ✓ 성능 최적화
  ✓ 문서화

Month 6: MVP 완성
  ✓ 설치 패키지 (pip install)
  ✓ 사용자 가이드
  ✓ 오픈소스 공개 준비
```

#### Branch 3.2 (Quality-First) - 월별 달성 가능 기능

```
Month 1: 아키텍처 + 기반
  ✓ 완전한 타입 시스템 설계
  ✓ TDD 환경 구축 (픽스처, 모킹)
  ✓ CI/CD 파이프라인
  ✓ 보안 레이어 구현
  → YAML 파서만 완성 (데모 불가)

Month 2: 핵심 기능 구현
  ✓ Claude API 연동 (TDD)
  ✓ 입력 검증 완전 구현
  ✓ 명령어 실행기 (보안)
  → 기본 CLI 동작

Month 3: 기능 완성
  ✓ 파일 작업 실행기
  ✓ 통합 테스트 완성
  ✓ 문서 자동화
  → Month 3.1의 Month 1 수준

Month 4: 고급 기능 시작
  ✓ 프롬프트 버전 관리
  ✓ 골든 테스트 구축
  → Month 3.1의 Month 2 수준

Month 5-6: 기능 개발 집중
  → Month 3.1의 Month 3-4 수준에서 MVP
```

**핵심 차이**: Branch 3.2는 Month 6에 3.1의 Month 3-4 수준 기능 완성. 3.2가 약 2-3개월 느립니다.

---

### 1인 개발자에게 권장하는 개발 프로세스

**결론: "실용적 하이브리드" - Speed로 시작하고 Quality로 이행**

이것을 **"Safety Core + Speed Shell"** 전략이라고 부릅니다.

```
전략: 안전에 관한 것은 처음부터 Quality-First
      기능 개발은 Speed-First
      
[처음부터 Quality: 절대 나중에 추가 못함]
- 입력 검증 레이어 (Pydantic v2)
- 명령어 실행 보안 (shell=False)
- API 키 관리 (OS Keyring)
- 기본 타입 힌트

[Speed-First 후 점진 개선]
- 테스트 (스모크 먼저, 유닛 나중)
- 문서화 (docstring → 나중에 ADR)
- 리팩토링 (DEBT 주석으로 추적)
- CI/CD (로컬 pre-commit → 나중에 GitHub Actions)
```

**월별 실행 계획:**

```
Month 1 (기반): Safety Core 구축 + 프로토타입
  - Week 1: 보안 레이어 + 기본 모델 (Pydantic)
  - Week 2: Claude API 연동 스파이크 → 프로덕션
  - Week 3-4: YAML 파서 + 기본 실행기
  
  품질 투자: 20% (보안만)
  속도 투자: 80% (기능 구현)

Month 2 (핵심): 동작하는 MVP
  - 스모크 테스트 + pre-commit 설정
  - Feature Flag 구현
  - 기본 CLI 완성
  
  품질 투자: 30%
  속도 투자: 70%

Month 3 (안정): 첫 번째 Quality Sprint
  - DEBT 주석 상위 5개 해소
  - 통합 테스트 15개 추가
  - 프롬프트 버전 관리
  
  품질 투자: 50%
  속도 투자: 50%

Month 4-5 (성숙): 기능 확장
  - 고급 기능 개발 (병렬 실행, 템플릿)
  - 골든 테스트 구축
  - ADR 작성 (중요 결정 소급 기록)
  
  품질 투자: 40%
  속도 투자: 60%

Month 6 (완성): MVP 마감
  - 문서화 완성
  - CI/CD 완성
  - 패키징
  
  품질 투자: 60%
  속도 투자: 40%
```

---

### PRD.md에 반영할 개발 방법론 방향

PRD에 아래 섹션들을 포함하기를 권장합니다:

```markdown
## 개발 방법론

### 전략: Safety Core + Speed Shell Hybrid

**원칙 1: 보안은 설계 단계에서 (Security-by-Design)**
- 모든 외부 입력은 Pydantic v2로 검증
- 명령어 실행은 shell=False + allowlist 방식
- API 키는 OS Keyring 저장 (하드코딩 절대 금지)
- 이 규칙은 협상 불가, Day 1부터 적용

**원칙 2: 기능은 스파이크로 검증 후 구현**
- 새 기능마다 24시간 스파이크 선행
- 스파이크 결과를 기반으로 구현 방향 결정
- 스파이크 코드는 src/에 절대 들어가지 않음

**원칙 3: 기술 부채는 코드에 명시**
- # DEBT[카테고리][우선순위]: 설명 형식 사용
- 월 1회 부채 리포트 생성 및 상위 3개 해소
- "나중에 고치지"는 DEBT 주석 없이 금지

**원칙 4: AI 출력은 항상 검증**
- LLM 출력은 Pydantic 모델로 항상 검증
- 검증 실패 시 구조화된 재시도 (최대 3회)
- 골든 테스트로 AI 품질 주 1회 모니터링

**원칙 5: 테스트 피라미드**
- Unit(50) + Integration(15) + Golden(5) 구성 목표
- 스모크 테스트는 커밋마다 자동 실행
- AI API 실제 호출 테스트는 별도 마커로 분리

### 핵심 도구 스택
| 도구 | 용도 | 도입 시점 |
|------|------|----------|
| Pydantic v2 | 입력 검증 | Day 1 |
| pytest + hypothesis | 테스트 | Day 1 |
| ruff | 린팅/포맷 | Day 1 |
| pre-commit | 자동 품질 검사 | Week 1 |
| mypy | 타입 체크 | Month 2 |
| GitHub Actions | CI/CD | Month 3 |
| bandit | 보안 스캔 | Month 3 |

### 개발 리듬
- 일일: 저장 시 자동 ruff + fast unit tests
- 커밋: pre-commit hooks (smoke test 포함)
- 주간: 골든 테스트 + DEBT 리뷰
- 월간: 기술 부채 TOP 3 해소 스프린트
```

---

**최종 권장사항**: 6개월 MVP라는 제약 하에서, 완벽한 TDD나 완전한 CI/CD를 처음부터 구축하는 것은 시간을 과다 소비합니다. 반면 보안 취약점을 나중에 고치는 것은 아키텍처 재설계 수준의 비용이 발생합니다. "**보안은 처음부터, 품질은 점진적으로**"가 1인 개발자 6개월 MVP의 최적 전략입니다. Claude Code + CLAUDE.md를 적극 활용하면 실제 코딩 시간의 40-60%를 절약할 수 있으며, 이 여유 시간을 설계와 보안 검토에 투자하는 것이 장기적으로 더 빠른 개발 속도를 만들어냅니다.