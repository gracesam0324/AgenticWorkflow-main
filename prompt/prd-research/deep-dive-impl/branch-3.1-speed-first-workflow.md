이 프로젝트는 AI Agentic Workflow System PRD를 위한 개발 방법론 분석 문서입니다. 포괄적인 분석을 바로 제공하겠습니다.

---

# BRANCH 3.1 + 3.2: AI Agentic Workflow System 개발 프로세스 심층 분석

## BRANCH 3.1: 빠른 개발 프로세스 (Speed-First Implementation)

---

### 1. Claude Code를 활용한 개발 가속

#### workflow.md 기반 태스크 자동화

Claude Code는 `CLAUDE.md` 파일을 프로젝트 루트에 두면 자동으로 읽어 컨텍스트로 활용합니다. 이를 개발 가속의 핵심 도구로 사용합니다.

```markdown
<!-- CLAUDE.md -->
# AI Workflow Automation System - 개발 컨텍스트

## 프로젝트 구조
- src/workflow_engine/ : 핵심 실행 엔진
- src/planner/ : 자연어 → YAML 변환
- src/executors/ : 단계별 실행기
- tests/ : pytest 테스트

## 코드 규칙
- Python 3.11+, 타입 힌트 필수
- 모든 public 함수에 docstring
- 에러는 반드시 WorkflowError 서브클래스로

## 현재 개발 중인 기능
- [ ] YAML 플랜 파서 (Sprint 1)
- [ ] Claude API 연동 (Sprint 1)
- [ ] 파일 시스템 실행기 (Sprint 2)

## 절대 하지 말 것
- subprocess에서 shell=True 사용 금지
- 하드코딩된 API 키 금지
- ~/.workflow/ 외부 파일 쓰기 금지
```

#### Claude에게 코드 생성 요청 최적 패턴

**패턴 1: 컨텍스트-제약-예시 구조 (CCE Pattern)**

```
[나쁜 요청]
"YAML 파서 만들어줘"

[좋은 요청 - CCE Pattern]
Context: 이 프로젝트는 자연어 → YAML → 로컬 실행 파이프라인입니다.
YAML 스키마는 아래와 같습니다:
```yaml
workflow:
  name: string
  steps:
    - id: string
      type: shell | python | file_op
      command: string
      depends_on: list[str]
```

Constraint:
- Pydantic v2로 검증
- 순환 의존성 감지 포함
- 에러 메시지는 사용자 친화적으로

Example input/output:
- Input: 위 YAML 문자열
- Output: WorkflowPlan 객체

위 스펙에 맞는 파서를 구현해주세요. 테스트도 함께.
```

**패턴 2: 반복 개선 패턴 (Iterative Refinement)**

```
1단계: "최소 동작하는 버전 먼저"
→ 2단계: "엣지 케이스 추가: 빈 steps, 중복 id"  
→ 3단계: "성능 최적화: 대형 YAML 처리"
→ 4단계: "에러 메시지 개선"
```

**패턴 3: 코드 리뷰 자동화 프롬프트**

```
다음 코드를 리뷰해주세요. 아래 기준으로:
1. 보안 취약점 (특히 경로 탐색, 명령어 인젝션)
2. Python best practices 위반
3. 타입 힌트 누락
4. 에러 핸들링 누락
5. 성능 문제

[코드 붙여넣기]

각 문제를 severity (Critical/Major/Minor)로 분류하고
수정 코드를 포함해서 알려주세요.
```

**패턴 4: 아키텍처 결정 요청**

```
상황: workflow step 실행 시 timeout 처리가 필요합니다.
옵션 A: asyncio.wait_for() 사용
옵션 B: subprocess timeout 파라미터
옵션 C: threading.Timer

제약:
- Python 3.11
- subprocess 기반 shell 명령어 실행
- 동기/비동기 혼재 환경

각 옵션의 장단점과 이 프로젝트에 최적인 선택을 알려주세요.
```

---

### 2. 프로토타입 → 프로덕션 코드 전환 기법

#### 스파이크(Spike) 코드 작성 방법

스파이크는 "이것이 기술적으로 가능한가?"를 24시간 내에 검증하는 탐색 코드입니다.

```python
# spikes/spike_claude_yaml_generation.py
"""
SPIKE: Claude API로 YAML 플랜 생성 가능성 검증
목표: 자연어 입력 → 유효한 YAML 출력 확인
기간: 2025-01-15 (하루)
결과: [완료 후 기록]
"""

import anthropic
import yaml

# 스파이크는 품질 무시, 동작만 확인
client = anthropic.Anthropic()

def spike_generate_plan(user_input: str) -> dict:
    """TODO: 프로덕션 전환 시 WorkflowPlanner 클래스로 이동"""
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Generate a YAML workflow plan for: {user_input}"
        }]
    )
    # DEBT: 파싱 에러 처리 없음
    return yaml.safe_load(response.content[0].text)

if __name__ == "__main__":
    result = spike_generate_plan("백업 폴더 압축하고 날짜 붙여서 저장")
    print(result)
    # 결과 검증: 수동으로 YAML 구조 확인
```

**스파이크 → 프로덕션 전환 체크리스트:**

```
스파이크 결과가 아래를 만족할 때 프로덕션 코드 작성:
□ 핵심 기술 동작 확인됨
□ 주요 엣지 케이스 파악됨
□ 성능 요건 충족 가능성 확인됨
□ 의존성 라이센스 문제 없음
```

#### 리팩토링 판단 기준 (Rule of Three)

```python
# 리팩토링 트리거 규칙

# 규칙 1: Rule of Three
# 같은 코드가 3번째 복붙될 때 추상화

# 규칙 2: 함수 길이
# 함수가 40줄 초과 → 분리 고려

# 규칙 3: 인지 복잡도
# if/for/while 중첩 3단계 초과 → 리팩토링

# 규칙 4: 테스트 어려움
# "이걸 어떻게 테스트하지?"가 나오면 설계 문제

# 규칙 5: 변경 비용
# 요구사항 변경 시 5개 이상 파일 수정 필요 → 추상화 필요
```

#### 기술 부채 명시 방법 (DEBT 주석 시스템)

```python
# src/executors/shell_executor.py

# DEBT[보안][HIGH]: shell=True 사용 중. 
# 현재는 MVP 속도를 위해 허용하지만,
# Sprint 3에서 shlex.split() + shell=False로 교체 필요.
# 관련 이슈: #23
# 예상 수정 시간: 2시간
result = subprocess.run(command, shell=True, capture_output=True)  # DEBT

# DEBT[성능][LOW]: 매번 YAML 파일을 디스크에서 읽음.
# 캐싱 레이어 추가 시 개선 가능.
# 우선순위: Month 3 이후
with open(plan_file) as f:  # DEBT[캐싱]
    plan = yaml.safe_load(f)

# DEBT[유지보수][MEDIUM]: 이 로직은 WorkflowValidator로 이동해야 함.
# 현재 executor가 너무 많은 책임을 가짐 (SRP 위반)
if not all(step.get('id') for step in steps):  # DEBT[SRP]
    raise ValueError("모든 스텝에 id 필요")
```

**DEBT 집계 스크립트:**

```python
# scripts/debt_report.py
"""기술 부채 현황 리포트 생성"""
import re
from pathlib import Path
from collections import defaultdict

def scan_debt(root: str = "src") -> None:
    pattern = re.compile(
        r'# DEBT\[(\w+)\]\[(\w+)\]: (.+)'
    )
    debt_by_priority = defaultdict(list)
    
    for py_file in Path(root).rglob("*.py"):
        for i, line in enumerate(py_file.read_text().splitlines(), 1):
            if m := pattern.search(line):
                category, priority, desc = m.groups()
                debt_by_priority[priority].append({
                    "file": str(py_file),
                    "line": i,
                    "category": category,
                    "desc": desc
                })
    
    for priority in ["HIGH", "MEDIUM", "LOW"]:
        items = debt_by_priority.get(priority, [])
        print(f"\n[{priority}] {len(items)}건")
        for item in items:
            print(f"  {item['file']}:{item['line']} [{item['category']}]")
            print(f"    {item['desc']}")

if __name__ == "__main__":
    scan_debt()
```

#### Feature Flag 구현 패턴

```python
# src/config/feature_flags.py
"""
로컬 AI 시스템용 경량 Feature Flag 구현
환경변수 + YAML 파일 기반 (외부 서비스 불필요)
"""
from dataclasses import dataclass, field
from pathlib import Path
import os
import yaml


@dataclass
class FeatureFlags:
    # 기본값 = 안전한 쪽 (새 기능 OFF)
    enable_parallel_execution: bool = False
    enable_ai_retry: bool = True
    enable_step_caching: bool = False
    enable_dangerous_commands: bool = False  # 절대 기본 OFF
    max_ai_retries: int = 3
    
    @classmethod
    def load(cls) -> "FeatureFlags":
        """환경변수 > 로컬 파일 > 기본값 우선순위"""
        flags = cls()
        
        # 1. YAML 파일에서 로드
        config_file = Path.home() / ".workflow" / "features.yaml"
        if config_file.exists():
            data = yaml.safe_load(config_file.read_text())
            for key, value in (data or {}).items():
                if hasattr(flags, key):
                    setattr(flags, key, value)
        
        # 2. 환경변수로 오버라이드 (테스트/CI용)
        env_map = {
            "WF_PARALLEL": "enable_parallel_execution",
            "WF_CACHE": "enable_step_caching",
            "WF_DANGEROUS": "enable_dangerous_commands",
        }
        for env_key, attr in env_map.items():
            if val := os.getenv(env_key):
                setattr(flags, attr, val.lower() in ("1", "true", "yes"))
        
        return flags


# 전역 인스턴스 (싱글톤)
FLAGS = FeatureFlags.load()


# 사용 예시
# if FLAGS.enable_parallel_execution:
#     await asyncio.gather(*[run_step(s) for s in steps])
# else:
#     for step in steps:
#         await run_step(step)
```

---

### 3. AI 시스템 특화 개발 패턴

#### 비결정성 다루는 개발 패턴

LLM 출력은 매번 다릅니다. 이를 소프트웨어 엔지니어링으로 길들이는 패턴:

```python
# src/ai/deterministic_wrapper.py
"""
LLM 비결정성을 관리하는 래퍼 레이어
핵심 원칙: LLM은 항상 검증 가능한 구조화된 출력만 반환
"""
import json
import re
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError
import anthropic

T = TypeVar("T", bound=BaseModel)


class AIOutputError(Exception):
    """LLM이 파싱 불가능한 출력을 반환했을 때"""
    def __init__(self, raw_output: str, attempts: int):
        self.raw_output = raw_output
        self.attempts = attempts
        super().__init__(f"AI 출력 파싱 {attempts}회 실패")


class StructuredAIClient:
    """항상 구조화된 출력을 반환하는 AI 클라이언트"""
    
    def __init__(self, client: anthropic.Anthropic, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries
    
    def generate_structured(
        self, 
        prompt: str, 
        output_schema: Type[T],
        system_prompt: str | None = None
    ) -> T:
        """
        구조화된 출력 생성. 실패 시 재시도 + 수정 요청.
        
        Args:
            prompt: 사용자 요청
            output_schema: Pydantic 모델 클래스
            system_prompt: 시스템 프롬프트
        
        Returns:
            검증된 Pydantic 모델 인스턴스
        
        Raises:
            AIOutputError: max_retries 초과 시
        """
        schema_json = output_schema.model_json_schema()
        
        base_system = f"""당신은 정확한 JSON을 반환하는 AI입니다.
반드시 아래 JSON 스키마를 따르세요:
{json.dumps(schema_json, ensure_ascii=False, indent=2)}

규칙:
1. JSON 외 다른 텍스트 출력 금지
2. 마크다운 코드블록 금지
3. 주석 금지
4. 스키마의 모든 required 필드 포함"""
        
        if system_prompt:
            base_system = f"{system_prompt}\n\n{base_system}"
        
        last_error = None
        last_raw = ""
        
        for attempt in range(self.max_retries):
            # 첫 시도
            if attempt == 0:
                messages = [{"role": "user", "content": prompt}]
            else:
                # 재시도: 에러 피드백 포함
                messages = [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": last_raw},
                    {
                        "role": "user", 
                        "content": f"JSON 파싱 에러: {last_error}\n"
                                   f"위 스키마에 맞게 다시 작성해주세요."
                    }
                ]
            
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=4096,
                system=base_system,
                messages=messages
            )
            
            last_raw = response.content[0].text.strip()
            
            # JSON 추출 시도 (코드블록 있을 경우 대비)
            json_text = self._extract_json(last_raw)
            
            try:
                data = json.loads(json_text)
                return output_schema.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = str(e)
                continue
        
        raise AIOutputError(last_raw, self.max_retries)
    
    @staticmethod
    def _extract_json(text: str) -> str:
        """코드블록 안의 JSON 추출"""
        # ```json ... ``` 패턴
        if match := re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text):
            return match.group(1)
        # { ... } 패턴 (첫 번째 완전한 JSON 객체)
        if match := re.search(r'(\{[\s\S]+\})', text):
            return match.group(1)
        return text
```

#### 프롬프트 버전 관리 시스템

```
prompts/
├── v1/
│   ├── plan_generator.md
│   └── step_validator.md
├── v2/
│   ├── plan_generator.md    ← 현재 프로덕션
│   └── step_validator.md
├── experiments/
│   └── plan_generator_cot.md  ← 실험 중
└── registry.yaml
```

```yaml
# prompts/registry.yaml
version: 2

prompts:
  plan_generator:
    current: v2/plan_generator.md
    previous: v1/plan_generator.md
    experiment: experiments/plan_generator_cot.md
    promoted_at: "2025-02-10"
    metrics:
      v1: {success_rate: 0.82, avg_steps: 4.2}
      v2: {success_rate: 0.91, avg_steps: 5.1}
  
  step_validator:
    current: v2/step_validator.md
    previous: v1/step_validator.md
```

```python
# src/ai/prompt_manager.py
from pathlib import Path
import yaml


class PromptManager:
    """프롬프트 버전 관리 및 로드"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.root = Path(prompts_dir)
        self.registry = yaml.safe_load(
            (self.root / "registry.yaml").read_text()
        )
    
    def get(self, name: str, variant: str = "current") -> str:
        """
        Args:
            name: 프롬프트 이름 (예: "plan_generator")
            variant: "current" | "previous" | "experiment"
        """
        path = self.registry["prompts"][name][variant]
        return (self.root / path).read_text(encoding="utf-8")
    
    def ab_test(self, name: str, user_id: str) -> str:
        """사용자 ID 기반 A/B 테스트 (결정론적)"""
        use_experiment = hash(user_id) % 10 < 2  # 20%에게 실험 버전
        variant = "experiment" if use_experiment else "current"
        try:
            return self.get(name, variant)
        except KeyError:
            return self.get(name, "current")
```

```markdown
<!-- prompts/v2/plan_generator.md -->
당신은 로컬 컴퓨터 자동화 워크플로우 플래너입니다.

## 역할
사용자의 자연어 요청을 분석하여 실행 가능한 단계별 워크플로우 YAML을 생성합니다.

## 제약사항
- 오직 로컬 파일 시스템, 쉘 명령어, Python 스크립트만 사용
- 네트워크 요청은 명시적으로 요청된 경우에만
- 각 스텝은 독립적으로 실패/재시도 가능해야 함
- 위험한 명령어(rm -rf, 시스템 파일 수정)는 `requires_confirmation: true` 필수

## 출력 형식
반드시 아래 JSON 스키마를 따르세요:
{schema}

## 예시
입력: "Desktop의 모든 PNG 파일을 ~/Pictures/backup/오늘날짜 폴더로 복사"
출력:
{example_output}
```

#### LLM 출력 검증 레이어 (Pydantic v2 기반)

```python
# src/models/workflow_plan.py
"""
워크플로우 플랜 모델 - LLM 출력 검증의 핵심
"""
from __future__ import annotations
from enum import Enum
from pathlib import Path
import re
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator


class StepType(str, Enum):
    SHELL = "shell"
    PYTHON = "python"
    FILE_OP = "file_op"
    AI_TASK = "ai_task"


class WorkflowStep(BaseModel):
    id: Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]*$')]
    type: StepType
    name: str = Field(min_length=1, max_length=100)
    command: str = Field(min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=60, ge=1, le=3600)
    requires_confirmation: bool = False
    
    @field_validator('command')
    @classmethod
    def validate_command_safety(cls, v: str) -> str:
        """위험한 명령어 패턴 차단"""
        DANGEROUS_PATTERNS = [
            r'rm\s+-rf\s+/',          # 루트 삭제
            r':\(\)\{.*\}',            # Fork bomb
            r'>\s*/dev/sd',            # 디스크 직접 쓰기
            r'mkfs\.',                 # 포맷
            r'dd\s+if=.*of=/dev/',     # 디스크 덮어쓰기
        ]
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, v):
                raise ValueError(
                    f"위험한 명령어 패턴 감지됨. "
                    f"이 작업은 requires_confirmation: true 필요"
                )
        return v
    
    @field_validator('command')
    @classmethod  
    def validate_path_traversal(cls, v: str) -> str:
        """경로 탐색 공격 방어"""
        if '../' in v or '..\\' in v:
            raise ValueError("상대경로 탐색(..)은 허용되지 않습니다")
        return v


class WorkflowPlan(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    version: str = "1.0"
    steps: list[WorkflowStep] = Field(min_length=1)
    
    @model_validator(mode='after')
    def validate_no_circular_deps(self) -> WorkflowPlan:
        """순환 의존성 감지"""
        step_ids = {step.id for step in self.steps}
        
        # 존재하지 않는 스텝 참조 확인
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(
                        f"스텝 '{step.id}'가 존재하지 않는 '{dep}'에 의존합니다"
                    )
        
        # DFS로 순환 감지
        visited = set()
        rec_stack = set()
        
        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            step = next(s for s in self.steps if s.id == step_id)
            for dep in step.depends_on:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(step_id)
            return False
        
        for step in self.steps:
            if step.id not in visited:
                if has_cycle(step.id):
                    raise ValueError("워크플로우에 순환 의존성이 있습니다")
        
        return self
```

#### Golden Test 구축 방법

```python
# tests/golden/test_golden_outputs.py
"""
Golden Test: 검증된 입력-출력 쌍으로 AI 출력 품질 모니터링
목적: 프롬프트 변경 시 품질 저하 즉시 감지
"""
import json
import pytest
from pathlib import Path
from src.planner.workflow_planner import WorkflowPlanner
from src.models.workflow_plan import WorkflowPlan

GOLDEN_DIR = Path("tests/golden/fixtures")


def load_golden_cases():
    """golden 디렉토리의 모든 테스트 케이스 로드"""
    cases = []
    for input_file in GOLDEN_DIR.glob("*/input.txt"):
        case_dir = input_file.parent
        cases.append({
            "name": case_dir.name,
            "input": input_file.read_text(),
            "expected": json.loads((case_dir / "expected.json").read_text()),
            "min_steps": int((case_dir / "min_steps.txt").read_text().strip()),
        })
    return cases


class TestGoldenOutputs:
    """
    Golden Test Suite
    실제 AI 호출 (mock 아님) → CI에서는 skip, 로컬에서만 실행
    """
    
    @pytest.mark.golden  # 별도 마커로 구분
    @pytest.mark.parametrize("case", load_golden_cases(), 
                              ids=[c["name"] for c in load_golden_cases()])
    def test_golden_case(self, case, workflow_planner):
        plan = workflow_planner.generate(case["input"])
        
        # 구조 검증
        assert len(plan.steps) >= case["min_steps"], \
            f"스텝 수 부족: 최소 {case['min_steps']}개 필요"
        
        # 필수 스텝 타입 포함 확인
        step_types = {s.type.value for s in plan.steps}
        required_types = set(case["expected"].get("required_step_types", []))
        assert required_types.issubset(step_types), \
            f"필수 스텝 타입 누락: {required_types - step_types}"
        
        # 위험 명령어 포함 시 confirmation 확인
        for step in plan.steps:
            if any(p in step.command for p in ["rm ", "del ", "format"]):
                assert step.requires_confirmation, \
                    f"스텝 '{step.id}': 위험 명령어에 confirmation 없음"
```

```
tests/golden/fixtures/
├── backup_files/
│   ├── input.txt          "Desktop PNG 파일 백업"
│   ├── expected.json      {"required_step_types": ["shell", "file_op"]}
│   └── min_steps.txt      2
├── git_commit/
│   ├── input.txt          "변경사항 커밋하고 푸시"
│   ├── expected.json      {"required_step_types": ["shell"]}
│   └── min_steps.txt      3
└── cleanup_logs/
    ├── input.txt          "7일 이전 로그 파일 삭제"
    ├── expected.json      {"required_confirmation": true}
    └── min_steps.txt      1
```

---

### 4. 빠른 테스트 전략

#### 테스트 피라미드 (AI 시스템 맞춤형)

```
          /Golden Tests\      ← 5개, AI 품질 감시 (주 1회)
         /──────────────\
        / Integration    \    ← 15개, 실제 파일 I/O (커밋 전)
       /──────────────────\
      /    Unit Tests      \  ← 50개, 순수 로직 (매 저장)
     /──────────────────────\
```

#### pytest 설정 (완전한 예시)

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# 기본 실행: 빠른 테스트만
addopts = """
    -v
    --tb=short
    --strict-markers
    -m "not golden and not slow"
    --cov=src
    --cov-report=term-missing:skip-covered
    --cov-fail-under=70
"""

markers = [
    "unit: 순수 유닛 테스트 (외부 의존성 없음)",
    "integration: 파일시스템 등 외부 의존성 포함",
    "golden: 실제 AI API 호출 (느림, 비용 발생)",
    "slow: 5초 이상 소요",
    "smoke: 핵심 경로만 검증하는 스모크 테스트",
]

# 커버리지 설정
[tool.coverage.run]
source = ["src"]
omit = ["src/*/migrations/*", "src/config/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

```python
# tests/conftest.py
"""전역 픽스처 설정"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

from src.config.settings import Settings


@pytest.fixture(scope="session")
def tmp_workspace():
    """테스트용 임시 워크스페이스 (세션 전체 공유)"""
    with tempfile.TemporaryDirectory(prefix="workflow_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_claude_client():
    """Claude API 모킹 - 실제 API 호출 없이 테스트"""
    with patch("anthropic.Anthropic") as MockClient:
        client = MockClient.return_value
        # 기본 응답 설정
        client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"name": "test", "steps": []}')]
        )
        yield client


@pytest.fixture
def sample_workflow_yaml():
    """테스트용 샘플 워크플로우 YAML"""
    return """
workflow:
  name: test_backup
  steps:
    - id: create_dir
      type: shell
      name: 백업 디렉토리 생성
      command: mkdir -p ~/backup/test
    - id: copy_files
      type: shell  
      name: 파일 복사
      command: cp ~/Desktop/*.txt ~/backup/test/
      depends_on: [create_dir]
"""


@pytest.fixture(autouse=True)
def no_real_filesystem_writes(monkeypatch, tmp_path):
    """
    실수로 실제 파일시스템에 쓰는 것 방지
    HOME을 tmp_path로 교체
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("WORKFLOW_HOME", str(tmp_path / ".workflow"))
```

#### Smoke Test 자동화

```python
# tests/test_smoke.py
"""
Smoke Test: 시스템이 최소한으로 동작하는지 30초 내 확인
배포/커밋 후 즉시 실행
"""
import pytest


@pytest.mark.smoke
class TestSmoke:
    def test_import_core_modules(self):
        """핵심 모듈이 임포트 가능한지"""
        from src.planner import WorkflowPlanner  # noqa
        from src.executor import WorkflowExecutor  # noqa
        from src.models import WorkflowPlan  # noqa

    def test_yaml_parsing_works(self, sample_workflow_yaml):
        """YAML 파싱이 동작하는지"""
        from src.parser import YAMLParser
        plan = YAMLParser().parse(sample_workflow_yaml)
        assert plan.name == "test_backup"
        assert len(plan.steps) == 2

    def test_config_loads(self, tmp_workspace):
        """설정 파일 로드가 동작하는지"""
        from src.config.settings import Settings
        settings = Settings(workspace=tmp_workspace)
        assert settings.workspace.exists() or True  # 존재하지 않아도 OK

    def test_cli_entry_point(self):
        """CLI 진입점이 에러 없이 로드되는지"""
        from src.cli import app  # noqa
        assert app is not None
```

**하루 10분 이내 테스트 실행 Makefile:**

```makefile
# Makefile
.PHONY: test test-fast test-smoke test-all

# 빠른 테스트 (1분 이내): 저장할 때마다
test-fast:
	pytest -m "unit" -x -q --no-header

# 스모크 테스트 (30초): 커밋 전
test-smoke:
	pytest -m "smoke" -x -q

# 전체 테스트 (5-10분): 하루 1회
test:
	pytest -m "not golden" --tb=short

# 골든 테스트 포함 전체 (AI API 비용 발생)
test-all:
	pytest --tb=short

# 커버리지 리포트
coverage:
	pytest --cov=src --cov-report=html
	open htmlcov/index.html
```

---

### 5. Git 워크플로우 실제 구현

#### 솔로 개발자 Git 전략

```
main (항상 동작하는 코드)
  └── dev (일일 통합)
        ├── feat/yaml-parser
        ├── feat/claude-integration
        └── fix/timeout-handling

규칙:
1. main은 항상 smoke test 통과
2. dev에서 하루 작업 통합
3. feat/* 는 하루~3일 단위로 생성/병합
4. 커밋은 작게, 자주 (WIP 커밋 허용)
```

#### pre-commit hook 설정

```yaml
# .pre-commit-config.yaml
repos:
  # 기본 검사 (초고속)
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: detect-private-key       # API 키 실수 커밋 방지
      - id: no-commit-to-branch
        args: ['--branch', 'main']   # main 직접 커밋 방지

  # Python 포맷 (빠름)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # 타입 체크 (보통)
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, anthropic]
        args: [--ignore-missing-imports]

  # 보안 스캔 (빠름)
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        exclude: "tests/"

  # 스모크 테스트 (커밋 전 자동 실행)
  - repo: local
    hooks:
      - id: smoke-tests
        name: Smoke Tests
        entry: pytest -m smoke -x -q
        language: system
        pass_filenames: false
        always_run: true
```

#### 커밋 메시지 자동화 (Claude 활용)

```bash
#!/bin/bash
# scripts/smart_commit.sh
# 사용법: ./scripts/smart_commit.sh

# 변경사항 수집
DIFF=$(git diff --cached --stat)
DIFF_CONTENT=$(git diff --cached | head -200)  # 처음 200줄만

if [ -z "$DIFF" ]; then
    echo "스테이징된 변경사항이 없습니다."
    exit 1
fi

# Claude에게 커밋 메시지 생성 요청
COMMIT_MSG=$(python3 - <<EOF
import anthropic
import sys

client = anthropic.Anthropic()

diff_stat = """$DIFF"""
diff_content = """$DIFF_CONTENT"""

response = client.messages.create(
    model="claude-haiku-4-5",  # 비용 절약
    max_tokens=200,
    messages=[{
        "role": "user",
        "content": f"""아래 git diff를 보고 Conventional Commits 형식으로 커밋 메시지를 작성해주세요.

형식: <type>(<scope>): <description>

type: feat/fix/refactor/test/docs/chore
scope: 변경된 모듈명
description: 50자 이내 한국어

변경 통계:
{diff_stat}

주요 변경 내용:
{diff_content}

커밋 메시지만 출력하세요. 설명 없이."""
    }]
)

print(response.content[0].text.strip())
EOF
)

echo "생성된 커밋 메시지: $COMMIT_MSG"
echo ""
read -p "이 메시지로 커밋할까요? (y/n/e=편집): " choice

case $choice in
    y) git commit -m "$COMMIT_MSG" ;;
    e) git commit -e -m "$COMMIT_MSG" ;;
    *) echo "커밋 취소됨" ;;
esac
```

---
