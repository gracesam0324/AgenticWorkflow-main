# Branch 5.1: 공식 SDK 문서 & 구현 참조 — 최신 SDK 패턴
> Official SDK & Documentation Reference Specialist
> 조사일: 2026-04-07
> 참조: anthropic SDK 0.40+, Gemini CLI 공식 문서, llm CLI 0.30+

---

## 1. Anthropic Python SDK — 완전 분석

### 설치

```bash
pip install anthropic           # 기본 SDK
pip install claude-agent-sdk    # Agent SDK
```

### 패턴 1: 기본 Messages API

```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")

response = client.messages.create(
    model="claude-sonnet-4-6",    # 2026년 기준 권장
    max_tokens=4096,
    system="당신은 YAML 플랜을 생성하는 전문가입니다.",
    messages=[{"role": "user", "content": "데이터 파이프라인 구축해줘"}]
)

text = response.content[0].text
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens
```

**2026년 기준 모델 가격**:
| 모델 | 입력 (/1M tok) | 출력 (/1M tok) | 용도 |
|---|---|---|---|
| claude-haiku-4-5 | $1.00 | $5.00 | 분류, 요약 |
| claude-sonnet-4-6 | $3.00 | $15.00 | 플랜 생성 (기본) |
| claude-opus-4-6 | $5.00 | $25.00 | 복잡한 추론 |

### 패턴 2: Tool Use (에이전트 핵심)

```python
import anthropic, json

client = anthropic.Anthropic()

tools = [
    {
        "name": "execute_shell_command",
        "description": "로컬 셸 명령어를 안전하게 실행합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "실행할 명령어"},
                "working_dir": {"type": "string"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    }
]

def agent_loop(user_prompt: str, max_iterations: int = 20) -> str:
    """Safety-First Agent Loop (max_iterations=20)"""
    messages = [{"role": "user", "content": user_prompt}]

    for iteration in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            return response.content[0].text

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = tool_dispatch(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    return "최대 반복 횟수 초과 (20회)"
```

### 패턴 3: Streaming (실시간 출력)

```python
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()

def stream_plan_generation(user_input: str) -> str:
    full_response = ""
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system="YAML 형식의 실행 플랜을 생성하세요.",
        messages=[{"role": "user", "content": user_input}]
    ) as stream:
        with Live(console=console, refresh_per_second=10) as live:
            for text in stream.text_stream:
                full_response += text
                live.update(Text(full_response))
        final = stream.get_final_message()
        console.print(f"[dim]입력: {final.usage.input_tokens}tok | 출력: {final.usage.output_tokens}tok[/dim]")
    return full_response
```

### 패턴 4: Prompt Caching (90% 비용 절감)

```python
SYSTEM_PROMPT = """당신은 AI Agentic Workflow Automation System의 핵심 플래너입니다.
[수천 토큰의 YAML 스키마 정의...]
"""

def create_plan_with_cache(user_request: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}  # 5분 캐시 기본
                # TTL 1시간: {"type": "ephemeral", "ttl": 3600}
            }
        ],
        messages=[{"role": "user", "content": user_request}]
    )
    # 캐시 사용 여부 확인
    if response.usage.cache_read_input_tokens > 0:
        print(f"캐시 히트: {response.usage.cache_read_input_tokens}tok 절약")
    return response.content[0].text
```

**캐시 가격**:
- 5분 캐시 쓰기: 입력가격 × 1.25
- 1시간 캐시 쓰기: 입력가격 × 2
- 캐시 읽기: 입력가격 × 0.1 (90% 할인)

### 패턴 5: Extended Thinking

```python
def generate_complex_plan(complex_task: str) -> dict:
    """복잡한 다단계 워크플로우 플랜 생성 (thinking 활성화)"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        thinking={"type": "enabled", "budget_tokens": 10000},
        messages=[{"role": "user", "content": complex_task}]
    )
    thinking_text = ""
    final_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text = block.thinking
        elif block.type == "text":
            final_text = block.text
    return {"thinking": thinking_text, "plan": final_text}
```

**사용 기준**: 10개+ 스텝의 복잡한 파이프라인, 의존성 분석 필요 시. 단순 플랜엔 불필요.

### 패턴 6: Retry 전략 (에러 코드)

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import random, time

@retry(
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
def resilient_api_call(messages: list):
    try:
        return client.messages.create(model="claude-sonnet-4-6", max_tokens=4096, messages=messages)
    except anthropic.RateLimitError as e:
        retry_after = e.response.headers.get("retry-after", "60")
        time.sleep(int(retry_after) + random.uniform(0, 2))
        raise
    except anthropic.APIStatusError as e:
        if e.status_code == 529:  # 과부하
            raise
        elif e.status_code == 400:  # 잘못된 요청 (재시도 무의미)
            raise anthropic.BadRequestError(e.message)
        raise
```

**에러 코드**:
| HTTP | 타입 | 재시도 |
|---|---|---|
| 400 | BadRequestError | ❌ |
| 401 | AuthenticationError | ❌ |
| 429 | RateLimitError | ✅ (retry-after 헤더) |
| 529 | APIStatusError | ✅ (지수 백오프) |

---

## 2. Claude Agent SDK

```python
import anyio
from claude_agent_sdk import query, ClaudeSDKClient
from claude_agent_sdk.types import AssistantMessage, TextBlock

# 방법 1: 간단한 query()
async def simple_query():
    async for message in query(
        prompt="현재 디렉토리 Python 파일 목록",
        options={"max_turns": 5}
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

# 방법 2: 고급 ClaudeSDKClient
async def advanced_client():
    client = ClaudeSDKClient(options={
        "model": "claude-sonnet-4-6",
        "max_turns": 10,
        "cwd": "/path/to/project"
    })
    async for message in client.query("데이터 분석 스크립트 작성 후 실행"):
        print(message)
```

**Messages API vs Agent SDK**:
| 기준 | Messages API | Agent SDK |
|---|---|---|
| 파일/셸 기능 | 직접 구현 | 내장 |
| 비용 제어 | 완전 제어 | 제한적 |
| 추천 용도 | 플랜 생성, 맞춤 에이전트 | 빠른 프로토타이핑 |

---

## 3. Google Gemini CLI — 구독 계정 연동

### 설치 및 인증

```bash
npm install -g @google/gemini-cli  # Node.js 18+ 필요

# 방법 A: Google 계정 OAuth (구독 계정)
gemini auth login  # 브라우저 OAuth2

# 방법 B: API Key (자동화 환경 권장)
export GEMINI_API_KEY="AIza..."
```

**구독 티어**:
| 티어 | RPM | 일일 | 모델 |
|---|---|---|---|
| 무료 | 60 | 1,000 | Gemini Flash (기본) |
| Google AI Pro | 높음 | 1,500 | Gemini 2.5 Pro |
| Google AI Ultra | 매우 높음 | 별도 | 전체 |

### Python subprocess 연동

```python
import subprocess, json, os
from pathlib import Path

class GeminiCLIClient:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self._validate_auth()

    def _validate_auth(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.auth_method = "api_key"
        elif Path("~/.gemini/credentials.json").expanduser().exists():
            self.auth_method = "oauth"
        else:
            raise RuntimeError("Gemini 인증 필요: gemini auth login 또는 GEMINI_API_KEY")

    def query(self, prompt: str, timeout: int = 120) -> dict:
        cmd = ["gemini", "--model", self.model, "-p", prompt, "--output-format", "json"]
        env = os.environ.copy()
        env["NO_COLOR"] = "1"   # 비대화형 모드
        env["TERM"] = "dumb"    # TTY 감지 우회

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        if result.returncode != 0:
            raise RuntimeError(f"Gemini CLI 오류: {result.stderr}")

        try:
            data = json.loads(result.stdout)
            return {"response": data.get("response", ""), "stats": data.get("stats", {})}
        except json.JSONDecodeError:
            return {"response": result.stdout}
```

**JSON 출력 구조** (`--output-format json`):
```json
{
  "response": "AI 응답 텍스트",
  "stats": {
    "model": "gemini-2.0-flash",
    "tokenUsage": {"inputTokens": 42, "outputTokens": 387}
  }
}
```

**실용적 주의사항**:
1. Python subprocess에서 OAuth 캐시가 무시되는 TTY 감지 버그 존재
2. 자동화 환경에서는 `GEMINI_API_KEY` 방식이 더 안정적
3. Google 정책: 제3자 앱에서 OAuth 사용은 정책 위반 가능 (계정 제재 위험)

---

## 4. OpenAI — 구독 계정 CLI 현실

**결론**: OpenAI는 Codex CLI (공식) 제공하나 코딩 에이전트 목적에 특화.

```bash
# OpenAI Codex CLI (공식, ChatGPT Plus/Pro 구독 필요)
npm install -g @openai/codex
codex login  # 브라우저 OAuth
codex "버그 찾아줘"
```

**구독 계정 CLI 연동 평가**:
| 방법 | 가능 여부 | 비고 |
|---|---|---|
| Codex CLI | ✅ 가능 | 코딩 에이전트 전용 |
| openai Python SDK | ❌ 불가 | API Key 필수 |
| ChatGPT 웹 API | ❌ 불가 | 비공개, ToS 위반 |
| "구독으로 API 무제한" | ❌ 존재 안 함 | — |

**권장 대안**: `llm` CLI + `llm-ollama` (로컬 모델, API Key 불필요)

---

## 5. `llm` CLI (Simon Willison) — 가장 실용적 통합 CLI

```bash
pip install llm
llm install llm-claude-3      # Anthropic
llm install llm-gemini         # Google Gemini
llm install llm-ollama         # 로컬 (API Key 불필요)

llm keys set anthropic         # API Key 설정
llm "안녕" -m claude-sonnet-4-6
llm "코드 리뷰" -m gemini-2.0-flash
llm "안녕" -m llama3.2:latest  # API Key 없이
```

```python
import subprocess

class LLMCLIClient:
    MODEL_MAP = {
        "claude": "claude-sonnet-4-6",
        "gemini": "gemini-2.0-flash",
        "local": "llama3.2:latest"  # API Key 불필요
    }

    def query(self, prompt: str, model_alias: str = "claude", timeout: int = 120) -> str:
        model = self.MODEL_MAP.get(model_alias, model_alias)
        result = subprocess.run(
            ["llm", "-m", model, prompt],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise RuntimeError(f"llm 오류: {result.stderr}")
        return result.stdout.strip()
```

---

## 6. 시크릿 관리 (keyring 기반)

```python
import os, getpass
from pathlib import Path
import keyring
from dotenv import load_dotenv

class SecretManager:
    """우선순위: 환경 변수 → .env → keyring → 사용자 프롬프트"""

    SERVICE_NAME = "autoflow-ai-agent"

    def __init__(self):
        load_dotenv(Path.home() / ".autoflow" / ".env", override=False)
        load_dotenv()

    def get_secret(self, key_name: str, prompt: str = None) -> str:
        if val := os.environ.get(key_name):
            return val
        if val := keyring.get_password(self.SERVICE_NAME, key_name):
            return val
        val = getpass.getpass(f"{prompt or key_name} 입력: ")
        if not val:
            raise ValueError(f"{key_name} 필요")
        keyring.set_password(self.SERVICE_NAME, key_name, val)
        return val

    def get_anthropic_key(self) -> str:
        return self.get_secret("ANTHROPIC_API_KEY", "Anthropic API Key")

    def get_gemini_key(self) -> str | None:
        try:
            return self.get_secret("GEMINI_API_KEY", "Gemini API Key (선택)")
        except ValueError:
            return None  # OAuth 방식 폴백
```

---

## 7. 최종 폴백 전략

```python
import anthropic

class FallbackLLMClient:
    """자동 폴백 체인: Claude Sonnet → Haiku → Gemini Flash → Ollama"""

    def query(self, prompt: str, require_quality: bool = True) -> str:
        tiers = ["claude-sonnet-4-6", "claude-haiku-4-5"]
        if not require_quality:
            tiers.extend(["gemini-flash", "ollama-local"])

        for model in tiers:
            try:
                return self._query_model(prompt, model)
            except (anthropic.RateLimitError, RuntimeError) as e:
                print(f"[폴백] {model} 실패: {e}")
                continue

        raise RuntimeError("모든 LLM 서비스 실패")
```

**오프라인 동작 가능 범위**:
- ✅ YAML 플랜 파싱/검증
- ✅ 로컬 파일 읽기/쓰기
- ✅ Git 체크포인트 (로컬 repo)
- ✅ Ollama 로컬 모델 (사전 설치 시)
- ✅ SQLite/DuckDB 쿼리
- ❌ Claude API (플랜 생성)
- ❌ Gemini CLI (OAuth 갱신)
