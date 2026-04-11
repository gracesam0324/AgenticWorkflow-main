# 기술 부채 심층 분석: AI Agentic Workflow Automation System

---

## BRANCH 4.1: 기술 부채 최소화 전략

### 1. 코딩 표준 설정

#### pyproject.toml 전체 구성

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-workflow-automation"
version = "0.1.0"
description = "Local AI Agentic Workflow Automation System"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.20.0",
    "pydantic>=2.5.0",
    "pyyaml>=6.0.1",
    "gitpython>=3.1.40",
    "rich>=13.7.0",
    "typer>=0.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "bandit>=1.7.6",
    "pre-commit>=3.6.0",
    "hypothesis>=6.98.0",   # 프로퍼티 기반 테스트
]

# ─── Ruff: Linter + Formatter 통합 ───────────────────────────────
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
    "B",    # flake8-bugbear (실제 버그 패턴)
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "S",    # bandit (보안)
    "N",    # pep8-naming
    "ANN",  # flake8-annotations (타입 힌트 강제)
    "PTH",  # pathlib 사용 강제 (os.path 금지)
    "RUF",  # ruff 전용 규칙
    "SIM",  # 코드 단순화
    "TCH",  # TYPE_CHECKING 블록 최적화
]
ignore = [
    "ANN101",  # self 타입 힌트 불필요
    "ANN102",  # cls 타입 힌트 불필요
    "S101",    # assert 허용 (테스트에서 사용)
    "B008",    # Typer 의존성 주입 허용
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S",       # 테스트에서 보안 경고 완화
    "ANN",     # 테스트에서 타입 힌트 완화
]
"src/prompts/**/*.py" = [
    "E501",    # 프롬프트 파일 줄 길이 완화
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true

# ─── Mypy: 정적 타입 검사 ────────────────────────────────────────
[tool.mypy]
python_version = "3.11"
strict = true                    # 모든 strict 옵션 활성화
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true
plugins = ["pydantic.mypy"]      # Pydantic v2 통합

[[tool.mypy.overrides]]
module = [
    "yaml.*",
    "git.*",
]
ignore_missing_imports = true    # 스텁 없는 라이브러리 예외처리

# ─── Bandit: 보안 정적 분석 ──────────────────────────────────────
[tool.bandit]
targets = ["src"]
severity = "medium"              # medium 이상만 차단
confidence = "medium"
skips = [
    "B101",    # assert 허용
    "B603",    # subprocess 제한적 허용 (로컬 실행 필요)
]
exclude_dirs = ["tests", ".venv"]

# ─── Pytest ───────────────────────────────────────────────────────
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=70",       # MVP: 70% 커버리지 최저선
    "-v",
    "--tb=short",
]
markers = [
    "unit: 단위 테스트 (빠름, 모킹 사용)",
    "integration: 통합 테스트 (실제 파일시스템)",
    "llm: LLM 실제 호출 필요 (느림, CI 제외)",
    "slow: 5초 이상 소요",
]

# ─── Coverage ────────────────────────────────────────────────────
[tool.coverage.run]
source = ["src"]
omit = [
    "src/prompts/*",     # 프롬프트 파일 커버리지 제외
    "src/*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@overload",
]
```

#### pre-commit hooks 전체 구성 (.pre-commit-config.yaml)

```yaml
# .pre-commit-config.yaml
# 설치: pre-commit install
# 수동 실행: pre-commit run --all-files

repos:
  # ── 기본 파일 검사 ─────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--allow-multiple-documents]
      - id: check-toml
      - id: check-json
      - id: check-merge-conflict
      - id: check-added-large-files
        args: [--maxkb=500]          # 500KB 이상 파일 차단
      - id: detect-private-key        # API 키 실수 커밋 방지
      - id: check-case-conflict
      - id: mixed-line-ending
        args: [--fix=lf]

  # ── Ruff: Lint + Format ────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.1
    hooks:
      - id: ruff
        args: [--fix]                # 자동 수정 가능한 것은 수정
      - id: ruff-format

  # ── Mypy: 타입 검사 ───────────────────────────────────────────
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.5.0
          - types-pyyaml
          - types-requests

  # ── Bandit: 보안 검사 ─────────────────────────────────────────
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        exclude: tests/

  # ── 비밀/민감정보 탐지 ────────────────────────────────────────
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]
        exclude: (\.lock$|\.yaml$)    # YAML 플랜 파일 제외

  # ── YAML 플랜 스키마 검증 (커스텀) ───────────────────────────
  - repo: local
    hooks:
      - id: validate-plan-schema
        name: Validate YAML Plan Schema
        entry: python scripts/validate_plan_schema.py
        language: python
        files: plans/.*\.yaml$
        pass_filenames: true

      - id: check-debt-register
        name: Check Debt Register
        entry: python scripts/check_debt_register.py
        language: python
        pass_filenames: false
        always_run: true
```

---

### 2. AI 시스템 특화 부채 항목

#### 2-1. 프롬프트 하드코딩 부채

**나쁜 구현 (부채 발생):**
```python
# BAD: 프롬프트가 비즈니스 로직에 박혀있음
class PlanGenerator:
    def generate(self, user_input: str) -> str:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{
                "role": "user",
                # 프롬프트 변경 시 코드 수정 + 재배포 필요
                # A/B 테스트 불가능
                # 버전 추적 불가능
                "content": f"Convert this to YAML plan: {user_input}"
            }]
        )
        return response.content[0].text
```

**올바른 구현 (부채 없음):**
```python
# src/prompts/plan_generation.py
"""프롬프트를 코드와 분리하여 독립적으로 관리"""
from pathlib import Path
from string import Template
from typing import Final

import yaml
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """프롬프트 메타데이터 + 내용 분리"""
    version: str
    description: str
    model_recommendation: str
    template: str
    variables: list[str]
    
    def render(self, **kwargs: str) -> str:
        """변수 치환 + 누락 변수 검증"""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing prompt variables: {missing}")
        return Template(self.template).safe_substitute(**kwargs)


class PromptRegistry:
    """
    프롬프트 레지스트리: YAML 파일에서 로드
    
    디렉토리 구조:
    prompts/
      plan_generation/
        v1.yaml      ← 현재 버전
        v2.yaml      ← 실험 버전
        current.txt  ← "v1" (심볼릭 버전 포인터)
    """
    
    _cache: dict[str, PromptTemplate] = {}
    
    @classmethod
    def load(
        cls, 
        name: str, 
        version: str = "current"
    ) -> PromptTemplate:
        cache_key = f"{name}:{version}"
        
        if cache_key not in cls._cache:
            prompts_dir = Path("prompts") / name
            
            if version == "current":
                version = (prompts_dir / "current.txt").read_text().strip()
            
            prompt_file = prompts_dir / f"{version}.yaml"
            data = yaml.safe_load(prompt_file.read_text(encoding="utf-8"))
            cls._cache[cache_key] = PromptTemplate(**data)
        
        return cls._cache[cache_key]
```

```yaml
# prompts/plan_generation/v1.yaml
version: "v1"
description: "자연어 입력을 YAML 실행 플랜으로 변환"
model_recommendation: "claude-3-5-sonnet-20241022"
variables:
  - user_input
  - available_tools
  - working_directory
template: |
  You are a workflow automation planner. Convert the user's natural language 
  request into a structured YAML execution plan.
  
  Available tools: $available_tools
  Working directory: $working_directory
  
  User request: $user_input
  
  Requirements:
  - Each step must have: name, tool, parameters, on_failure
  - Steps must be atomic and reversible where possible
  - Include explicit validation steps
  
  Output ONLY valid YAML, no markdown fences.
```

```python
# 사용 예시
class PlanGenerator:
    def __init__(self, prompt_registry: PromptRegistry) -> None:
        self._prompts = prompt_registry
    
    def generate(self, user_input: str, context: ExecutionContext) -> str:
        prompt = self._prompts.load("plan_generation")
        rendered = prompt.render(
            user_input=user_input,
            available_tools=", ".join(context.available_tools),
            working_directory=str(context.working_dir),
        )
        # 프롬프트 버전이 응답에 태깅됨 → 재현성 확보
        return self._call_claude(rendered, model=prompt.model_recommendation)
```

#### 2-2. LLM 출력 무검증 부채

**나쁜 구현:**
```python
# BAD: LLM 출력을 그냥 믿음 → 런타임 폭발
def parse_plan(llm_response: str) -> dict:
    return yaml.safe_load(llm_response)  # KeyError, TypeError 폭탄
```

**올바른 구현:**
```python
# src/validation/plan_validator.py
from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class StepFailurePolicy(str, Enum):
    ABORT = "abort"
    CONTINUE = "continue"
    RETRY = "retry"
    ROLLBACK = "rollback"


class StepParameter(BaseModel):
    """각 파라미터의 타입과 값 검증"""
    model_config = {"extra": "forbid"}  # 미정의 필드 차단
    
    name: str
    value: str | int | float | bool | list[str]
    sensitive: bool = False  # 로그에서 마스킹


class WorkflowStep(BaseModel):
    model_config = {"extra": "forbid"}
    
    name: Annotated[str, Field(min_length=1, max_length=100)]
    tool: str
    parameters: list[StepParameter] = Field(default_factory=list)
    on_failure: StepFailurePolicy = StepFailurePolicy.ABORT
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    requires_confirmation: bool = False
    
    @field_validator("tool")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """도구 이름 인젝션 방지"""
        if not re.match(r"^[a-z_][a-z0-9_]*$", v):
            raise ValueError(f"Invalid tool name: {v!r}. Only lowercase, digits, underscores.")
        return v
    
    @field_validator("name")
    @classmethod
    def validate_step_name(cls, v: str) -> str:
        """경로 순회 공격 방지"""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError(f"Step name cannot contain path separators: {v!r}")
        return v


class WorkflowPlan(BaseModel):
    model_config = {"extra": "forbid"}
    
    version: str = "1.0"
    name: Annotated[str, Field(min_length=1, max_length=200)]
    description: str = ""
    steps: Annotated[list[WorkflowStep], Field(min_length=1, max_length=50)]
    
    # 위험 작업이 있으면 전체 플랜 확인 요구
    requires_confirmation: bool = False
    
    @model_validator(mode="after")
    def check_confirmation_escalation(self) -> WorkflowPlan:
        """위험 단계가 하나라도 있으면 플랜 전체 확인 필요"""
        if any(step.requires_confirmation for step in self.steps):
            self.requires_confirmation = True
        return self


class LLMOutputParser:
    """LLM 출력의 방어적 파싱"""
    
    # LLM이 markdown 코드블록으로 감쌀 때 처리
    _YAML_FENCE_PATTERN = re.compile(
        r"```(?:yaml)?\s*\n(.*?)\n```", 
        re.DOTALL
    )
    
    def parse_plan(self, raw_output: str) -> WorkflowPlan:
        """
        LLM 출력 → 검증된 WorkflowPlan
        
        실패 시 ValidationError 발생 (절대 조용히 넘어가지 않음)
        """
        yaml_content = self._extract_yaml(raw_output)
        
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise ValueError(f"LLM produced invalid YAML: {e}") from e
        
        if not isinstance(data, dict):
            raise ValueError(
                f"Expected YAML dict, got {type(data).__name__}. "
                f"Raw output: {raw_output[:200]!r}"
            )
        
        # Pydantic이 모든 타입/값 검증 수행
        return WorkflowPlan.model_validate(data)
    
    def _extract_yaml(self, raw: str) -> str:
        """마크다운 코드블록 자동 제거"""
        match = self._YAML_FENCE_PATTERN.search(raw)
        if match:
            return match.group(1)
        return raw.strip()
```

#### 2-3. 비결정성 미처리 부채

```python
# src/execution/determinism.py
"""LLM 비결정성을 시스템 수준에서 처리"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0
    # 재시도해야 할 에러 타입 (비결정성 관련)
    retryable_errors: tuple[type[Exception], ...] = field(
        default_factory=lambda: (ValueError, yaml.YAMLError)
    )


class DeterministicExecutor:
    """
    비결정성 처리 3가지 전략:
    1. 재시도 (Retry): 파싱 실패 시 재시도
    2. 캐싱 (Cache): 동일 입력 → 동일 출력 보장
    3. 검증 루프 (Validation Loop): 검증 실패 시 자동 수정 요청
    """
    
    def __init__(
        self,
        cache_dir: Path,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._retry = retry_config or RetryConfig()
    
    def execute_with_retry(
        self,
        func: Callable[[], T],
        validator: Callable[[T], None] | None = None,
    ) -> T:
        """
        비결정적 LLM 호출을 결정적으로 만드는 래퍼
        
        검증 실패 시 에러 메시지를 다음 프롬프트에 포함 → 자가 수정
        """
        last_error: Exception | None = None
        
        for attempt in range(self._retry.max_attempts):
            try:
                result = func()
                if validator:
                    validator(result)
                return result
                
            except tuple(self._retry.retryable_errors) as e:
                last_error = e
                delay = min(
                    self._retry.base_delay * (2 ** attempt),
                    self._retry.max_delay,
                )
                # 로그는 남기되 사용자에게 노출 최소화
                logger.warning(
                    "LLM output validation failed (attempt %d/%d): %s",
                    attempt + 1,
                    self._retry.max_attempts,
                    str(e),
                )
                time.sleep(delay)
        
        raise RuntimeError(
            f"LLM failed to produce valid output after "
            f"{self._retry.max_attempts} attempts"
        ) from last_error
    
    def get_cached_or_execute(
        self,
        cache_key_data: dict[str, str],
        executor: Callable[[], str],
    ) -> tuple[str, bool]:
        """
        캐시 히트 시 LLM 호출 없이 이전 결과 반환
        → 재현성 + 비용 절감
        
        Returns: (result, was_cached)
        """
        cache_key = hashlib.sha256(
            json.dumps(cache_key_data, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        cache_file = self._cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            cached = json.loads(cache_file.read_text())
            return cached["result"], True
        
        result = executor()
        cache_file.write_text(
            json.dumps({
                "result": result,
                "key_data": cache_key_data,
                "timestamp": time.time(),
            }, indent=2),
            encoding="utf-8",
        )
        return result, False
```

---

### 3. 아키텍처 부채 방지

#### God Object 방지 패턴

```python
# BAD: 모든 것이 하나의 클래스에 (God Object)
class WorkflowSystem:
    def parse_input(self): ...
    def call_claude(self): ...
    def validate_yaml(self): ...
    def execute_step(self): ...
    def rollback(self): ...
    def send_notification(self): ...
    def save_to_git(self): ...
    def show_ui(self): ...
    # → 1000줄짜리 괴물 클래스
```

```python
# GOOD: 단일 책임 원칙 적용 구조
# src/
# ├── core/           ← 순수 도메인 (외부 의존성 없음)
# │   ├── models.py   ← Pydantic 모델만
# │   └── errors.py   ← 커스텀 예외만
# ├── planning/       ← 플랜 생성 (Claude 호출)
# │   ├── generator.py
# │   └── validator.py
# ├── execution/      ← 플랜 실행 (파일시스템, 프로세스)
# │   ├── runner.py
# │   └── rollback.py
# ├── storage/        ← 영속성 (Git, 파일)
# │   └── repository.py
# └── cli/            ← 사용자 인터페이스만
#     └── commands.py


# src/core/errors.py
"""전체 시스템의 예외 계층 - 한 곳에서 관리"""

class WorkflowError(Exception):
    """모든 워크플로우 예외의 기반"""
    def __init__(self, message: str, recoverable: bool = False) -> None:
        super().__init__(message)
        self.recoverable = recoverable


class PlanGenerationError(WorkflowError):
    """Claude가 유효한 플랜을 생성하지 못함"""


class PlanValidationError(WorkflowError):
    """생성된 플랜이 스키마/보안 검증 실패"""
    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message, recoverable=True)
        self.raw_output = raw_output


class StepExecutionError(WorkflowError):
    """단계 실행 실패"""
    def __init__(
        self, 
        message: str, 
        step_name: str,
        recoverable: bool = False,
    ) -> None:
        super().__init__(message, recoverable)
        self.step_name = step_name


# src/core/interfaces.py  ← 의존성 역전의 핵심
"""
DI 컨테이너 없이 의존성 역전 구현
Protocol을 사용해 인터페이스 정의
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    """LLM 클라이언트 인터페이스 - Claude SDK에 직접 의존하지 않음"""
    def complete(
        self, 
        prompt: str, 
        model: str,
        max_tokens: int = 4096,
    ) -> str: ...


@runtime_checkable  
class PlanStorage(Protocol):
    """플랜 저장소 인터페이스"""
    def save(self, plan: WorkflowPlan, name: str) -> Path: ...
    def load(self, name: str) -> WorkflowPlan: ...
    def list_plans(self) -> list[str]: ...


@runtime_checkable
class StepExecutor(Protocol):
    """단계 실행기 인터페이스"""
    def can_execute(self, tool_name: str) -> bool: ...
    def execute(self, step: WorkflowStep) -> StepResult: ...


# src/planning/generator.py
class PlanGenerator:
    """
    오직 플랜 생성만 담당
    
    외부 의존성은 모두 Protocol로 주입
    → 테스트 시 Mock으로 교체 가능
    → Claude SDK 변경 시 이 클래스 수정 불필요
    """
    
    def __init__(
        self,
        llm_client: LLMClient,           # Protocol (인터페이스)
        prompt_registry: PromptRegistry,  # 구체 클래스 (변경 적음)
        output_parser: LLMOutputParser,   # 구체 클래스
    ) -> None:
        self._llm = llm_client
        self._prompts = prompt_registry
        self._parser = output_parser
    
    def generate(
        self, 
        user_input: str, 
        context: ExecutionContext,
    ) -> WorkflowPlan:
        """단일 공개 메서드 - 복잡도 외부 노출 없음"""
        prompt = self._build_prompt(user_input, context)
        raw_output = self._llm.complete(prompt, model="claude-3-5-sonnet-20241022")
        return self._parser.parse_plan(raw_output)
    
    def _build_prompt(
        self, 
        user_input: str, 
        context: ExecutionContext,
    ) -> str:
        template = self._prompts.load("plan_generation")
        return template.render(
            user_input=user_input,
            available_tools=", ".join(context.available_tools),
            working_directory=str(context.working_dir),
        )
```

#### 순환 의존성 방지

```python
# scripts/check_circular_imports.py
"""CI에서 순환 의존성 자동 탐지"""
import ast
import sys
from pathlib import Path


def get_imports(file_path: Path) -> set[str]:
    """파일에서 내부 임포트만 추출"""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("src."):
                # src.planning.generator → planning
                module_parts = node.module.split(".")
                if len(module_parts) > 1:
                    imports.add(module_parts[1])
    
    return imports


def check_circular_deps(src_dir: Path) -> list[str]:
    """
    허용 의존성 방향:
    cli → planning → core
    cli → execution → core  
    execution → storage → core
    
    금지:
    core → 어떤 것도 (순수 도메인)
    planning → execution (계획이 실행을 알면 안 됨)
    """
    allowed_deps: dict[str, set[str]] = {
        "core": set(),           # 아무것도 의존 안 함
        "planning": {"core"},    # core만 의존
        "execution": {"core", "storage"},
        "storage": {"core"},
        "cli": {"core", "planning", "execution", "storage"},
    }
    
    violations = []
    
    for module_dir in src_dir.iterdir():
        if not module_dir.is_dir():
            continue
        module_name = module_dir.name
        if module_name not in allowed_deps:
            continue
        
        for py_file in module_dir.rglob("*.py"):
            actual_imports = get_imports(py_file)
            forbidden = actual_imports - allowed_deps[module_name]
            
            for dep in forbidden:
                violations.append(
                    f"VIOLATION: {module_name} → {dep} "
                    f"(in {py_file.relative_to(src_dir)})"
                )
    
    return violations


if __name__ == "__main__":
    violations = check_circular_deps(Path("src"))
    if violations:
        print("Circular dependency violations found:")
        for v in violations:
            print(f"  {v}")
        sys.exit(1)
    print("No circular dependencies found.")
```

---

### 4. 테스트 부채 방지

#### AI 출력 모킹 전략

```python
# tests/conftest.py
"""전역 픽스처 시스템 - 테스트 인프라 중앙화"""
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 골든 파일 픽스처 시스템 ──────────────────────────────────────
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_plan(request: pytest.FixtureRequest) -> dict[str, Any]:
    """
    tests/fixtures/plans/{name}.yaml에서 테스트 플랜 로드
    
    사용: def test_something(fixture_plan):
          plan = fixture_plan("simple_file_copy")
    """
    def _load(name: str) -> dict[str, Any]:
        fixture_file = FIXTURES_DIR / "plans" / f"{name}.yaml"
        if not fixture_file.exists():
            pytest.fail(f"Fixture not found: {fixture_file}")
        return yaml.safe_load(fixture_file.read_text())
    return _load


@pytest.fixture
def mock_llm_client():
    """
    LLM 클라이언트 Mock - 결정적 응답 반환
    
    실제 API 호출 없이 테스트 가능
    """
    mock = MagicMock(spec=LLMClient)
    
    # 기본 응답: 유효한 YAML 플랜
    default_plan = (FIXTURES_DIR / "llm_responses" / "valid_plan.yaml").read_text()
    mock.complete.return_value = default_plan
    
    return mock


@pytest.fixture
def mock_llm_client_invalid():
    """LLM이 잘못된 출력을 반환하는 케이스 테스트용"""
    mock = MagicMock(spec=LLMClient)
    mock.complete.return_value = "This is not YAML at all!!!"
    return mock


@pytest.fixture
def mock_llm_client_sequence():
    """
    순서대로 다른 응답 반환 (재시도 로직 테스트용)
    
    사용: client = mock_llm_client_sequence(["invalid", "invalid", "valid_yaml"])
    """
    def _create(responses: list[str]):
        mock = MagicMock(spec=LLMClient)
        mock.complete.side_effect = responses
        return mock
    return _create


# ── 임시 작업 디렉토리 ────────────────────────────────────────────
@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """
    격리된 임시 작업공간
    테스트 종료 시 자동 정리 (pytest tmp_path 기반)
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "data").mkdir()
    (workspace / "output").mkdir()
    return workspace


# ── 골든 테스트 헬퍼 ─────────────────────────────────────────────
@pytest.fixture
def assert_matches_golden():
    """
    실제 출력을 골든 파일과 비교
    UPDATE_GOLDEN=1 환경변수로 골든 파일 갱신
    """
    import os
    
    def _assert(actual: str, golden_name: str) -> None:
        golden_file = FIXTURES_DIR / "golden" / f"{golden_name}.txt"
        
        if os.environ.get("UPDATE_GOLDEN") == "1":
            golden_file.parent.mkdir(parents=True, exist_ok=True)
            golden_file.write_text(actual, encoding="utf-8")
            pytest.skip(f"Updated golden file: {golden_file}")
        
        if not golden_file.exists():
            pytest.fail(
                f"Golden file missing: {golden_file}\n"
                f"Run with UPDATE_GOLDEN=1 to create it."
            )
        
        expected = golden_file.read_text(encoding="utf-8")
        assert actual == expected, (
            f"Output doesn't match golden file {golden_name}.\n"
            f"Run with UPDATE_GOLDEN=1 to update."
        )
    
    return _assert
```

```python
# tests/unit/test_plan_generator.py
"""최소한의 테스트로 최대 안전성 확보"""
import pytest
from unittest.mock import MagicMock

from src.planning.generator import PlanGenerator
from src.core.errors import PlanValidationError


class TestPlanGenerator:
    """
    전략: 행복 경로 1개 + 실패 경로 3개
    = 가장 중요한 4가지 케이스만 테스트
    """
    
    def test_generates_valid_plan_from_natural_language(
        self,
        mock_llm_client,
        fixture_plan,
    ) -> None:
        """핵심 행복 경로: 정상 입력 → 유효한 플랜"""
        generator = PlanGenerator(
            llm_client=mock_llm_client,
            prompt_registry=PromptRegistry(),
            output_parser=LLMOutputParser(),
        )
        
        plan = generator.generate(
            user_input="파이썬 파일들을 백업하고 압축해줘",
            context=ExecutionContext(
                working_dir=Path("/tmp/test"),
                available_tools=["file_copy", "compress"],
            ),
        )
        
        assert plan.name  # 이름이 있어야 함
        assert len(plan.steps) >= 1  # 최소 1단계
        assert all(step.tool for step in plan.steps)  # 모든 단계에 도구
    
    def test_raises_on_invalid_llm_output(
        self,
        mock_llm_client_invalid,
    ) -> None:
        """LLM이 쓰레기를 반환하면 조용히 넘어가지 않음"""
        generator = PlanGenerator(llm_client=mock_llm_client_invalid, ...)
        
        with pytest.raises(PlanValidationError) as exc_info:
            generator.generate("아무 입력", ExecutionContext(...))
        
        assert exc_info.value.recoverable  # 재시도 가능함을 표시
    
    def test_retries_on_validation_failure(
        self,
        mock_llm_client_sequence,
        fixture_plan,
    ) -> None:
        """2번 실패 후 3번째에 성공 → 정상 반환"""
        valid_yaml = yaml.dump(fixture_plan("simple_copy"))
        client = mock_llm_client_sequence(["bad", "bad", valid_yaml])
        
        generator = PlanGenerator(llm_client=client, ...)
        plan = generator.generate("입력", ExecutionContext(...))
        
        assert plan is not None
        assert client.complete.call_count == 3  # 정확히 3번 호출
    
    def test_never_executes_plan_with_path_traversal(
        self,
        mock_llm_client,
    ) -> None:
        """보안: 경로 순회 공격이 포함된 플랜 거부"""
        # LLM이 악의적 플랜을 반환하는 시나리오 (프롬프트 인젝션 대응)
        malicious_plan = """
        name: test
        steps:
          - name: "../../etc/passwd"  # 경로 순회
            tool: file_read
        """
        mock_llm_client.complete.return_value = malicious_plan
        
        generator = PlanGenerator(llm_client=mock_llm_client, ...)
        
        with pytest.raises(PlanValidationError, match="path separator"):
            generator.generate("입력", ExecutionContext(...))
```

---

### 5. 6개월 부채 관리 일정

```
Month 1 (기초 공사):   허용 부채 많음, 금지 부채 엄격
Month 2 (핵심 기능):   아키텍처 부채 최소화
Month 3 (통합):        Month 1 부채 상환 스프린트
Month 4 (안정화):      성능 부채 탐지
Month 5 (보안 강화):   보안 부채 전수 감사
Month 6 (출시 준비):   부채 0 목표
```

```python
# scripts/debt_tracker.py
"""
코드베이스에서 DEBT 주석을 파싱하여 보고서 생성

사용 규약:
  # DEBT[P1]: 설명 (priority 1=즉시, 2=이번달, 3=다음달)
  # DEBT[P2]: 설명 @owner:sj @due:2024-03
  # DEBT[P3]: 설명 #category:testing
"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DebtItem:
    file: str
    line: int
    priority: int
    description: str
    owner: str | None
    due: str | None
    category: str | None


DEBT_PATTERN = re.compile(
    r"#\s*DEBT\[P(\d)\]:\s*(.+?)(?:\s*@owner:(\S+))?(?:\s*@due:(\S+))?(?:\s*#category:(\S+))?$"
)


def scan_debt(src_dir: Path) -> list[DebtItem]:
    items = []
    
    for py_file in src_dir.rglob("*.py"):
        for line_num, line in enumerate(
            py_file.read_text(encoding="utf-8").splitlines(), 1
        ):
            match = DEBT_PATTERN.search(line)
            if match:
                items.append(DebtItem(
                    file=str(py_file.relative_to(src_dir)),
                    line=line_num,
                    priority=int(match.group(1)),
                    description=match.group(2).strip(),
                    owner=match.group(3),
                    due=match.group(4),
                    category=match.group(5),
                ))
    
    return sorted(items, key=lambda x: x.priority)


def generate_report(items: list[DebtItem]) -> None:
    p1 = [i for i in items if i.priority == 1]
    p2 = [i for i in items if i.priority == 2]
    p3 = [i for i in items if i.priority == 3]
    
    print(f"\n=== TECHNICAL DEBT REPORT ===")
    print(f"Total: {len(items)} items  |  P1: {len(p1)}  P2: {len(p2)}  P3: {len(p3)}")
    
    if p1:
        print("\n🚨 P1 (즉시 해소 필요):")
        for item in p1:
            print(f"  {item.file}:{item.line} → {item.description}")
    
    # CI에서 P1 부채가 있으면 빌드 실패
    if p1:
        print("\n❌ P1 debt found! Fix before committing.")
        sys.exit(1)


if __name__ == "__main__":
    items = scan_debt(Path("src"))
    generate_report(items)
```

---
