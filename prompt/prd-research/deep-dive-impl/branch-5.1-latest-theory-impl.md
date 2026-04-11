# Theory Foundation Expert: AI Agentic Workflow Automation System

## 이론적 기반 심층 분석 보고서

---

# BRANCH 5.1: 최신 이론 기반 (2023-2024 Cutting Edge)

---

## 1. Claude SDK의 Tool Use 패턴 구현 이론

### Tool Use vs Function Calling 차이

**Function Calling** (OpenAI 방식)은 모델이 함수를 "호출"하고 결과를 기다리는 단방향 패턴입니다. **Tool Use** (Claude 방식)는 모델이 도구를 "사용 요청"하고, 호스트가 실행 후 결과를 돌려주는 양방향 대화 패턴입니다.

```
Function Calling: Model → Call → Result (단방향)
Tool Use:         Model → Request → Host executes → Result → Model continues (순환)
```

```python
# tool_use_pattern.py

import anthropic
import json
import subprocess
import os
from typing import Any

client = anthropic.Anthropic()

# 도구 스키마 정의 - JSON Schema 표준 준수
TOOLS = [
    {
        "name": "run_shell_command",
        "description": "로컬 쉘 명령어를 안전하게 실행합니다. 파일 생성/수정/삭제 시 확인이 필요합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "실행할 쉘 명령어"
                },
                "working_dir": {
                    "type": "string",
                    "description": "명령어를 실행할 디렉토리 경로",
                    "default": "."
                },
                "requires_confirmation": {
                    "type": "boolean",
                    "description": "사용자 확인이 필요한지 여부",
                    "default": False
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "로컬 파일을 읽어 내용을 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "읽을 파일의 절대 또는 상대 경로"
                },
                "encoding": {
                    "type": "string",
                    "description": "파일 인코딩",
                    "default": "utf-8"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "로컬 파일에 내용을 씁니다. 기존 파일 덮어쓰기 시 확인 필요.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {
                    "type": "string",
                    "enum": ["write", "append"],
                    "default": "write"
                }
            },
            "required": ["file_path", "content"]
        }
    }
]

# 안전한 Tool Use 구현 - 화이트리스트 기반
SAFE_COMMANDS = frozenset([
    "ls", "pwd", "echo", "cat", "mkdir", "cp",
    "git status", "git log", "git diff", "python"
])

DANGEROUS_PATTERNS = [
    "rm -rf", "sudo", "chmod 777", "> /dev/", 
    "dd if=", "mkfs", ":(){ :|:& };:"  # Fork bomb
]

def is_safe_command(command: str) -> tuple[bool, str]:
    """명령어 안전성 검증"""
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            return False, f"위험한 패턴 감지: {pattern}"
    
    base_cmd = command.split()[0] if command.split() else ""
    # 완전한 화이트리스트가 아닌 블랙리스트 방식으로 경고
    if base_cmd in {"rm", "mv", "chmod", "chown"}:
        return True, f"주의 필요 명령어: {base_cmd} (확인 권장)"
    
    return True, "안전"

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """도구 실행 핸들러"""
    if tool_name == "run_shell_command":
        command = tool_input["command"]
        working_dir = tool_input.get("working_dir", ".")
        requires_confirmation = tool_input.get("requires_confirmation", False)
        
        is_safe, reason = is_safe_command(command)
        if not is_safe:
            return json.dumps({"error": f"명령어 차단됨: {reason}"})
        
        if requires_confirmation:
            confirm = input(f"\n명령어 실행 확인: '{command}'\n실행하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                return json.dumps({"cancelled": True, "reason": "사용자가 취소"})
        
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True,
                text=True, cwd=working_dir, timeout=30
            )
            return json.dumps({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "명령어 실행 타임아웃 (30초 초과)"})
    
    elif tool_name == "read_file":
        try:
            with open(tool_input["file_path"], 
                     encoding=tool_input.get("encoding", "utf-8")) as f:
                return json.dumps({"content": f.read()})
        except FileNotFoundError:
            return json.dumps({"error": f"파일 없음: {tool_input['file_path']}"})
    
    elif tool_name == "write_file":
        mode = "a" if tool_input.get("mode") == "append" else "w"
        with open(tool_input["file_path"], mode, 
                 encoding="utf-8") as f:
            f.write(tool_input["content"])
        return json.dumps({"success": True, "path": tool_input["file_path"]})
    
    return json.dumps({"error": f"알 수 없는 도구: {tool_name}"})

def run_tool_use_agent(user_request: str) -> str:
    """Tool Use 에이전트 실행"""
    messages = [{"role": "user", "content": user_request}]
    
    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages
        )
        
        # 종료 조건 확인
        if response.stop_reason == "end_turn":
            # 최종 텍스트 응답 추출
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return "작업 완료"
        
        # Tool Use 요청 처리
        if response.stop_reason == "tool_use":
            # 어시스턴트 응답을 메시지 히스토리에 추가
            messages.append({
                "role": "assistant", 
                "content": response.content
            })
            
            # 모든 도구 결과 수집
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  [도구 실행] {block.name}: {block.input}")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            
            # 도구 결과를 메시지에 추가
            messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            break
    
    return "에이전트 루프 완료"
```

---

## 2. Agent Loop 구현 이론

### Claude의 Agentic Loop 작동 원리

```
┌─────────────────────────────────────────┐
│           AGENTIC LOOP                  │
│                                         │
│  User Input                             │
│      ↓                                  │
│  [Claude Thinks] → tool_use? → Execute  │
│      ↑                    ↓             │
│  [Tool Results] ←─────────┘             │
│      ↓                                  │
│  end_turn → Final Response              │
└─────────────────────────────────────────┘
```

```python
# agent_loop.py

import anthropic
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from enum import Enum

class LoopState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_CONFIRMATION = "waiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"

@dataclass
class LoopConfig:
    max_iterations: int = 20          # 무한 루프 방지 핵심
    max_tokens_per_turn: int = 4096
    timeout_seconds: float = 300.0    # 전체 루프 타임아웃
    confirmation_threshold: int = 3   # N번 이상 도구 실행 시 확인
    model: str = "claude-opus-4-5"

@dataclass  
class LoopMetrics:
    iterations: int = 0
    tool_calls: int = 0
    start_time: float = field(default_factory=time.time)
    tool_call_history: list = field(default_factory=list)

class AgentLoop:
    """
    안전한 Agentic Loop 구현
    
    핵심 안전 메커니즘:
    1. max_iterations: 무한 루프 방지
    2. timeout: 시간 기반 강제 종료
    3. interrupt_points: 사용자 확인 삽입
    4. tool_call_deduplication: 동일 도구 반복 호출 감지
    """
    
    def __init__(
        self, 
        config: LoopConfig,
        tools: list[dict],
        tool_executor: Callable,
        interrupt_handler: Optional[Callable] = None
    ):
        self.config = config
        self.tools = tools
        self.tool_executor = tool_executor
        self.interrupt_handler = interrupt_handler
        self.client = anthropic.Anthropic()
        self.state = LoopState.IDLE
        self.metrics = LoopMetrics()
    
    def _check_infinite_loop(self) -> bool:
        """
        반복 도구 호출 패턴 감지 (무한 루프 신호)
        최근 6번의 호출에서 같은 패턴이 2번 이상 반복되면 감지
        """
        if len(self.metrics.tool_call_history) < 6:
            return False
        
        recent = self.metrics.tool_call_history[-6:]
        # 최근 3개와 그 이전 3개 비교
        pattern_a = str(recent[:3])
        pattern_b = str(recent[3:])
        
        if pattern_a == pattern_b:
            return True
        return False
    
    def _should_interrupt(self) -> bool:
        """인터럽트 포인트: 사용자 확인이 필요한 시점"""
        # 1. 일정 횟수 이상 도구 실행 시
        if self.metrics.tool_calls >= self.config.confirmation_threshold:
            return True
        # 2. 커스텀 인터럽트 핸들러
        if self.interrupt_handler and self.interrupt_handler(self.metrics):
            return True
        return False
    
    def _check_timeout(self) -> bool:
        """전체 실행 시간 타임아웃 확인"""
        elapsed = time.time() - self.metrics.start_time
        return elapsed > self.config.timeout_seconds
    
    def run(self, user_input: str, system_prompt: str = "") -> dict:
        """
        메인 에이전트 루프 실행
        
        Returns:
            dict: {
                "result": str,
                "state": LoopState,
                "metrics": LoopMetrics,
                "messages": list
            }
        """
        self.state = LoopState.THINKING
        self.metrics = LoopMetrics()
        
        messages = [{"role": "user", "content": user_input}]
        kwargs = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens_per_turn,
            "tools": self.tools,
            "messages": messages
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        
        while self.metrics.iterations < self.config.max_iterations:
            # --- 안전 체크 ---
            if self._check_timeout():
                self.state = LoopState.FAILED
                return self._build_result("타임아웃 초과", messages)
            
            if self._check_infinite_loop():
                self.state = LoopState.FAILED
                return self._build_result("무한 루프 감지됨", messages)
            
            if self._should_interrupt():
                self.state = LoopState.WAITING_CONFIRMATION
                confirm = input(
                    f"\n[인터럽트] {self.metrics.tool_calls}번 도구 실행됨. "
                    f"계속 진행하시겠습니까? (y/N): "
                )
                if confirm.lower() != 'y':
                    self.state = LoopState.INTERRUPTED
                    return self._build_result("사용자 중단", messages)
                # 인터럽트 후 카운터 리셋
                self.metrics.tool_calls = 0
            
            # --- Claude 호출 ---
            self.metrics.iterations += 1
            kwargs["messages"] = messages
            response = self.client.messages.create(**kwargs)
            
            # --- 종료 조건 ---
            if response.stop_reason == "end_turn":
                self.state = LoopState.COMPLETED
                final_text = next(
                    (b.text for b in response.content if hasattr(b, 'text')), 
                    "완료"
                )
                return self._build_result(final_text, messages)
            
            # --- 도구 실행 ---
            if response.stop_reason == "tool_use":
                self.state = LoopState.EXECUTING
                messages.append({
                    "role": "assistant", 
                    "content": response.content
                })
                
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        self.metrics.tool_calls += 1
                        self.metrics.tool_call_history.append(
                            f"{block.name}:{str(block.input)[:50]}"
                        )
                        
                        result = self.tool_executor(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                
                messages.append({"role": "user", "content": tool_results})
                self.state = LoopState.THINKING
        
        # max_iterations 도달
        self.state = LoopState.FAILED
        return self._build_result(
            f"최대 반복 횟수 초과 ({self.config.max_iterations}회)", 
            messages
        )
    
    def _build_result(self, result: str, messages: list) -> dict:
        return {
            "result": result,
            "state": self.state,
            "metrics": self.metrics,
            "messages": messages
        }
```

---

## 3. Structured Output 이론과 구현

### JSON Schema → Pydantic 검증 → 재시도 전략

```python
# structured_output.py

import json
import re
from typing import TypeVar, Type, Optional
from pydantic import BaseModel, Field, field_validator, ValidationError
import anthropic

T = TypeVar('T', bound=BaseModel)

# YAML 플랜의 Pydantic 모델 정의
class WorkflowStep(BaseModel):
    step_id: str = Field(..., pattern=r'^step_\d+$')
    name: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., description="실행할 액션 유형")
    command: Optional[str] = None
    args: dict = Field(default_factory=dict)
    rollback_command: Optional[str] = None
    requires_confirmation: bool = False
    timeout_seconds: int = Field(default=30, ge=1, le=3600)
    
    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        allowed = {'shell', 'file_read', 'file_write', 'git', 'python'}
        if v not in allowed:
            raise ValueError(f"허용되지 않는 액션: {v}. 허용: {allowed}")
        return v

class WorkflowPlan(BaseModel):
    plan_id: str
    description: str
    steps: list[WorkflowStep] = Field(..., min_length=1, max_length=50)
    estimated_duration_seconds: int = Field(ge=1)
    requires_confirmation: bool = True
    
    @field_validator('steps')
    @classmethod
    def validate_step_ids_unique(cls, v):
        ids = [step.step_id for step in v]
        if len(ids) != len(set(ids)):
            raise ValueError("step_id는 고유해야 합니다")
        return v

class StructuredOutputParser:
    """
    LLM 출력의 신뢰성 확보를 위한 파서
    
    전략:
    1. JSON 추출 (마크다운 코드블록 처리)
    2. Pydantic 검증
    3. 실패 시 재시도 (오류 피드백 포함)
    """
    
    def __init__(self, client: anthropic.Anthropic, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries
    
    def _extract_json(self, text: str) -> str:
        """LLM 응답에서 JSON 추출 (코드블록, 순수 JSON 모두 처리)"""
        # ```json ... ``` 블록 추출
        json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', 
                               text, re.DOTALL)
        if json_block:
            return json_block.group(1)
        
        # 순수 JSON 객체 추출 (중첩 고려)
        stack = []
        start = -1
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        return text[start:i+1]
        
        return text  # 추출 실패 시 원본 반환
    
    def parse_with_retry(
        self, 
        model_class: Type[T],
        prompt: str,
        system_prompt: str = "",
        messages: list = None
    ) -> T:
        """
        재시도 전략이 포함된 구조화 출력 파싱
        
        실패 시: 오류 메시지를 컨텍스트로 추가하여 재시도
        """
        schema = model_class.model_json_schema()
        
        base_system = f"""당신은 JSON 형식으로만 응답합니다.
반드시 다음 JSON 스키마를 따르세요:
{json.dumps(schema, ensure_ascii=False, indent=2)}

응답은 반드시 유효한 JSON이어야 합니다. 다른 텍스트 없이 JSON만 반환하세요."""
        
        if system_prompt:
            base_system = system_prompt + "\n\n" + base_system
        
        current_messages = messages or [{"role": "user", "content": prompt}]
        last_error = None
        
        for attempt in range(self.max_retries):
            response = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2048,
                system=base_system,
                messages=current_messages
            )
            
            raw_text = response.content[0].text
            
            try:
                json_str = self._extract_json(raw_text)
                data = json.loads(json_str)
                validated = model_class.model_validate(data)
                return validated
                
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                error_context = (
                    f"이전 응답이 유효하지 않습니다.\n"
                    f"응답: {raw_text[:500]}\n"
                    f"오류: {str(e)}\n"
                    f"스키마를 다시 확인하고 올바른 JSON을 반환하세요."
                )
                # 오류를 컨텍스트로 추가하여 재시도
                current_messages = current_messages + [
                    {"role": "assistant", "content": raw_text},
                    {"role": "user", "content": error_context}
                ]
                print(f"  [재시도 {attempt+1}/{self.max_retries}] 검증 실패: {type(e).__name__}")
        
        raise ValueError(
            f"{self.max_retries}번 재시도 후 구조화 출력 파싱 실패. "
            f"마지막 오류: {last_error}"
        )

# 사용 예시
def generate_workflow_plan(user_request: str) -> WorkflowPlan:
    client = anthropic.Anthropic()
    parser = StructuredOutputParser(client, max_retries=3)
    
    plan = parser.parse_with_retry(
        model_class=WorkflowPlan,
        prompt=f"다음 요청에 대한 워크플로우 플랜을 생성하세요: {user_request}",
        system_prompt="당신은 로컬 자동화 워크플로우 플래너입니다."
    )
    return plan
```

---

## 4. 로컬 LLM 통합 이론 (Ollama)

### Claude API ↔ 로컬 LLM 전환 설계 (모델 라우팅 패턴)

```python
# llm_router.py

import anthropic
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class ModelTier(Enum):
    """모델 계층 정의"""
    CLOUD_POWERFUL = "cloud_powerful"    # Claude Opus - 복잡한 추론
    CLOUD_FAST = "cloud_fast"            # Claude Haiku - 빠른 응답
    LOCAL_CAPABLE = "local_capable"      # Ollama llama3.3 - 중간 작업
    LOCAL_FAST = "local_fast"            # Ollama phi3 - 단순 작업
    OFFLINE = "offline"                  # 완전 오프라인 폴백

@dataclass
class RoutingRule:
    """라우팅 규칙"""
    max_complexity: int      # 1-10 복잡도
    requires_tools: bool
    prefers_local: bool
    tier: ModelTier

class LLMBackend(ABC):
    """LLM 백엔드 추상 인터페이스 - 전략 패턴"""
    
    @abstractmethod
    def complete(self, messages: list, system: str = "", 
                 tools: list = None, max_tokens: int = 2048) -> dict:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

class ClaudeBackend(LLMBackend):
    """Anthropic Claude API 백엔드"""
    
    def __init__(self, model: str = "claude-opus-4-5"):
        self.model = model
        self.client = anthropic.Anthropic()
    
    def is_available(self) -> bool:
        try:
            # 최소한의 API 호출로 가용성 확인
            self.client.messages.create(
                model=self.model, max_tokens=10,
                messages=[{"role": "user", "content": "ping"}]
            )
            return True
        except Exception:
            return False
    
    def complete(self, messages: list, system: str = "", 
                 tools: list = None, max_tokens: int = 2048) -> dict:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools
        
        response = self.client.messages.create(**kwargs)
        
        # 통합 응답 포맷으로 정규화
        return {
            "content": response.content[0].text 
                       if response.content[0].type == "text" 
                       else None,
            "tool_uses": [
                {"name": b.name, "input": b.input, "id": b.id}
                for b in response.content 
                if b.type == "tool_use"
            ],
            "stop_reason": response.stop_reason,
            "model": self.model,
            "backend": "claude"
        }

class OllamaBackend(LLMBackend):
    """Ollama 로컬 LLM 백엔드"""
    
    def __init__(self, model: str = "llama3.2", 
                 base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        # Ollama는 OpenAI 호환 API 제공
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"  # 더미 키
            )
        except ImportError:
            self.client = None
    
    def is_available(self) -> bool:
        if not self.client:
            return False
        try:
            import urllib.request
            urllib.request.urlopen(
                f"{self.base_url}/api/tags", timeout=2
            )
            return True
        except Exception:
            return False
    
    def complete(self, messages: list, system: str = "", 
                 tools: list = None, max_tokens: int = 2048) -> dict:
        if system:
            messages = [{"role": "system", "content": system}] + messages
        
        # Ollama는 Tool Use를 일부 모델만 지원
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        if tools and self.model in {"llama3.1", "llama3.2", "mistral"}:
            # OpenAI 형식 도구 변환
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["input_schema"]
                    }
                } for t in tools
            ]
        
        response = self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # 통합 응답 포맷으로 정규화
        return {
            "content": message.content,
            "tool_uses": [],  # Ollama tool_calls 파싱 생략
            "stop_reason": "end_turn",
            "model": self.model,
            "backend": "ollama"
        }

class LLMRouter:
    """
    지능형 모델 라우터
    
    라우팅 전략:
    1. 복잡도 기반 (단순 작업 → 로컬, 복잡 추론 → Claude)
    2. 가용성 기반 (오프라인 시 로컬 폴백)
    3. 비용 기반 (반복 작업 → 로컬)
    """
    
    def __init__(self, prefer_local: bool = False):
        self.prefer_local = prefer_local
        self.backends = {
            ModelTier.CLOUD_POWERFUL: ClaudeBackend("claude-opus-4-5"),
            ModelTier.CLOUD_FAST: ClaudeBackend("claude-haiku-4-5"),
            ModelTier.LOCAL_CAPABLE: OllamaBackend("llama3.2"),
            ModelTier.LOCAL_FAST: OllamaBackend("phi3"),
        }
        self._availability_cache: dict[ModelTier, tuple[bool, float]] = {}
    
    def _get_availability(self, tier: ModelTier, 
                          cache_ttl: float = 60.0) -> bool:
        """가용성 캐싱 (60초)"""
        if tier in self._availability_cache:
            is_avail, checked_at = self._availability_cache[tier]
            if time.time() - checked_at < cache_ttl:
                return is_avail
        
        is_avail = self.backends[tier].is_available()
        self._availability_cache[tier] = (is_avail, time.time())
        return is_avail
    
    def route(self, complexity: int = 5, 
              requires_tools: bool = False,
              force_local: bool = False) -> LLMBackend:
        """
        복잡도와 가용성 기반 라우팅
        
        complexity: 1(매우 단순) ~ 10(매우 복잡)
        """
        if force_local or self.prefer_local:
            if self._get_availability(ModelTier.LOCAL_CAPABLE):
                return self.backends[ModelTier.LOCAL_CAPABLE]
        
        # Tool Use가 필요하고 복잡도 높음 → Claude Opus
        if requires_tools and complexity >= 7:
            if self._get_availability(ModelTier.CLOUD_POWERFUL):
                return self.backends[ModelTier.CLOUD_POWERFUL]
        
        # 단순하고 빠른 응답 필요 → Claude Haiku
        if complexity <= 3:
            if self._get_availability(ModelTier.CLOUD_FAST):
                return self.backends[ModelTier.CLOUD_FAST]
            if self._get_availability(ModelTier.LOCAL_FAST):
                return self.backends[ModelTier.LOCAL_FAST]
        
        # 중간 복잡도 → Claude Haiku 또는 로컬
        if self._get_availability(ModelTier.CLOUD_FAST):
            return self.backends[ModelTier.CLOUD_FAST]
        
        # 오프라인 폴백
        if self._get_availability(ModelTier.LOCAL_CAPABLE):
            print("[라우터] 오프라인 모드: 로컬 LLM으로 전환")
            return self.backends[ModelTier.LOCAL_CAPABLE]
        
        raise RuntimeError("사용 가능한 LLM 백엔드 없음 (오프라인 + 로컬 미설치)")
```

---

## 5. MCP (Model Context Protocol) 구현 이론

### 로컬 AI 시스템을 MCP 서버로 구현

```python
# mcp_server.py
# pip install mcp

import asyncio
import json
import subprocess
from pathlib import Path
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp import types

# MCP 서버 인스턴스 생성
app = Server("local-automation-agent")

# ─── 도구 정의 (MCP 도구 노출) ───────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """MCP 클라이언트에게 사용 가능한 도구 목록 노출"""
    return [
        types.Tool(
            name="execute_workflow",
            description="자연어로 워크플로우를 설명하면 자동으로 계획하고 실행합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "실행할 작업의 자연어 설명"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "True면 실제 실행 없이 계획만 반환",
                        "default": True
                    }
                },
                "required": ["description"]
            }
        ),
        types.Tool(
            name="run_local_command",
            description="로컬 쉘 명령어를 안전하게 실행합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "working_directory": {
                        "type": "string",
                        "default": "~"
                    }
                },
                "required": ["command"]
            }
        ),
        types.Tool(
            name="read_project_context",
            description="프로젝트 디렉토리의 컨텍스트 정보를 읽습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string"},
                    "include_git_history": {
                        "type": "boolean",
                        "default": False
                    }
                },
                "required": ["project_path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(
    name: str, 
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """MCP 도구 실행 핸들러"""
    
    if name == "execute_workflow":
        description = arguments["description"]
        dry_run = arguments.get("dry_run", True)
        
        # 실제 워크플로우 엔진 호출 (간략화)
        result = {
            "plan": f"'{description}'에 대한 워크플로우 플랜",
            "steps": ["1. 분석", "2. 실행", "3. 검증"],
            "dry_run": dry_run
        }
        
        return [types.TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    elif name == "run_local_command":
        command = arguments["command"]
        working_dir = Path(arguments.get("working_directory", "~")).expanduser()
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30
            )
            
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "stdout": stdout.decode(),
                    "stderr": stderr.decode(),
                    "returncode": proc.returncode
                }, ensure_ascii=False)
            )]
        except asyncio.TimeoutError:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": "명령어 타임아웃"})
            )]
    
    elif name == "read_project_context":
        project_path = Path(arguments["project_path"])
        include_git = arguments.get("include_git_history", False)
        
        context = {
            "path": str(project_path),
            "files": [str(f.name) for f in project_path.iterdir() 
                     if f.is_file()][:20],
        }
        
        if include_git:
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                capture_output=True, text=True, cwd=project_path
            )
            context["git_log"] = result.stdout
        
        return [types.TextContent(
            type="text",
            text=json.dumps(context, ensure_ascii=False, indent=2)
        )]
    
    raise ValueError(f"알 수 없는 도구: {name}")

# ─── 리소스 정의 (MCP 리소스 노출) ──────────────────────────────────

@app.list_resources()
async def list_resources() -> list[types.Resource]:
    """MCP 클라이언트에게 접근 가능한 리소스 노출"""
    return [
        types.Resource(
            uri="workflow://history",
            name="워크플로우 실행 이력",
            description="최근 실행된 워크플로우 목록",
            mimeType="application/json"
        )
    ]

async def main():
    """MCP 서버 실행 (stdio 트랜스포트)"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="local-automation-agent",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
```

---
