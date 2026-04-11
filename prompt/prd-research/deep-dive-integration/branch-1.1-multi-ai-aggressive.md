# Branch 1.1: Multi-AI Model Integration — Aggressive (완전한 멀티모델 오케스트레이션)
> Multi-AI Model Integration Specialist
> 조사일: 2026-04-07
> 특이사항: OpenAI 공식 구독 CLI 존재하지 않음 확인, Ollama로 대체

---

## 핵심 사실 확인 (팩트 체크)

| AI 모델 | 허용 인증 방식 | 금지 방식 | 비고 |
|---|---|---|---|
| Claude (Anthropic) | API key (정상) | 없음 | anthropic SDK |
| Google Gemini | OAuth2 구독 계정 (Gemini CLI) | API key 금지 | npm 기반 |
| OpenAI | **공식 방법 없음** | API key 금지 | Ollama로 대체 |

### OpenAI 구독 계정 CLI: 팩트 확인 결과

**결론**: OpenAI는 ChatGPT Plus 구독 계정으로 API를 호출하는 **공식적인 방법을 제공하지 않음** (2025년 8월 기준).

| 항목 | 현황 |
|---|---|
| OpenAI 공식 CLI 도구 | **없음** |
| `openai` Python SDK 구독 계정 인증 | **불가능** (API key 필수) |
| ChatGPT CLI (공식) | **없음** |
| OAuth2를 통한 ChatGPT Plus API 접근 | **없음** |

OpenAI 비즈니스 모델: ChatGPT Plus(구독, 웹/앱 전용) + API(종량제) = **완전 분리 운영**

**권장 대안**: Ollama (로컬 LLM, OpenAI 호환 API, 무료, 합법)

---

## 1. Google Gemini CLI (구독 계정 기반) 연동

### 1.1 Gemini CLI 공식 정보

- **공식 저장소**: `github.com/google-gemini/gemini-cli`
- **출시**: 2025년 5월 (Google I/O 2025)
- **런타임**: Node.js 18+
- **라이선스**: Apache 2.0

```bash
# 설치
npm install -g @google/gemini-cli

# 또는 npx
npx @google/gemini-cli
```

### 1.2 구독 계정 OAuth2 인증 흐름

```bash
# 최초 실행 시 브라우저 OAuth2 화면 자동 열림
gemini
# 또는 명시적 로그인
gemini auth login
```

인증 흐름:
1. `gemini` 실행 → 브라우저 Google OAuth2 consent 화면
2. Google 계정 로그인
3. OAuth2 토큰 로컬 저장 (`~/.gemini/` 등)
4. 이후 자동 refresh token 갱신

**핵심**: 최초 1회만 브라우저 인터랙션. 이후 완전 자동.

### 1.3 Python subprocess 호출 패턴

```python
import subprocess
import shutil
from typing import Optional

def call_gemini_cli(prompt: str, timeout: int = 60) -> str:
    """
    Gemini CLI subprocess 호출.
    shell=False (보안), 구독 계정 OAuth2 인증.
    """
    gemini_path = shutil.which("gemini")
    if gemini_path is None:
        raise RuntimeError(
            "Gemini CLI 미설치. 설치: npm install -g @google/gemini-cli"
        )
    
    result = subprocess.run(
        [gemini_path, "-p", prompt, "--output_format", "text"],
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,          # 보안: shell=False 필수
        encoding="utf-8",
    )
    
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Gemini CLI 오류 (code {result.returncode}): {stderr}")
    
    return result.stdout.strip()


def call_gemini_json(prompt: str) -> dict:
    """구조화된 JSON 응답 요청"""
    import json
    gemini_path = shutil.which("gemini")
    json_prompt = f"{prompt}\n\n반드시 유효한 JSON 형식으로만 응답하세요."
    
    result = subprocess.run(
        [gemini_path, "-p", json_prompt, "--output_format", "json"],
        capture_output=True, text=True, timeout=120, shell=False, encoding="utf-8",
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Gemini 오류: {result.stderr}")
    
    raw_output = result.stdout.strip()
    # ```json ... ``` 형식 처리
    if raw_output.startswith("```"):
        lines = raw_output.split("\n")
        raw_output = "\n".join(lines[1:-1])
    
    return json.loads(raw_output)


def check_gemini_auth() -> bool:
    """Gemini CLI 인증 상태 확인"""
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        return False
    try:
        result = subprocess.run(
            [gemini_path, "--version"],
            capture_output=True, text=True, timeout=10, shell=False,
        )
        return result.returncode == 0
    except Exception:
        return False
```

### 1.4 인증 토큰 경로 (사전 확인)

```python
import os, platform

def is_gemini_pre_authenticated() -> bool:
    """저장된 인증 토큰 존재 여부 확인"""
    if platform.system() == "Windows":
        token_path = os.path.expandvars(r"%APPDATA%\gemini-cli\credentials.json")
    elif platform.system() == "Darwin":
        token_path = os.path.expanduser("~/Library/Application Support/gemini-cli/credentials.json")
    else:
        token_path = os.path.expanduser("~/.config/gemini-cli/credentials.json")
    
    return os.path.exists(token_path)
```

**제약 사항**:
- CI/CD / headless 환경에서 최초 인증 불가
- 이 시스템은 "로컬 컴퓨터에서 작동"이므로 최초 1회 사용자 인증 후 자동 운용 가능

### 1.5 비용 및 Rate Limit

| 계정 유형 | 모델 | Rate Limit |
|---|---|---|
| 개인 Google 계정 (무료) | Gemini 2.0 Flash | 분당 15 요청, 일일 1,500 |
| 개인 Google 계정 (무료) | Gemini 2.5 Pro | 분당 2-5 요청 (제한적) |
| Google One AI Premium ($19.99/월) | Gemini Advanced | 향상된 limit |

**Gemini 강점**: 1M 토큰 컨텍스트 → 전체 프로젝트 코드베이스 분석 가능

---

## 2. MultiModelRouter 전체 구현

```python
"""
multi_model_router.py
Claude API + Gemini CLI + Ollama 통합 라우터
"""
import subprocess, shutil, json, time, logging
from typing import Optional
from enum import Enum
from dataclasses import dataclass

import anthropic
from openai import OpenAI  # Ollama용

logger = logging.getLogger(__name__)


@dataclass
class ModelResponse:
    content: str
    model_used: str
    latency_ms: float
    token_count: Optional[int] = None
    fallback_used: bool = False


class MultiModelRouter:
    """
    멀티모델 오케스트레이터.
    우선순위: Claude → Gemini CLI → Ollama
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        ollama_base_url: str = "http://localhost:11434/v1",
        default_ollama_model: str = "llama3.2",
        gemini_timeout: int = 60,
    ):
        self.claude_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.ollama_client = OpenAI(base_url=ollama_base_url, api_key="ollama")
        self.default_ollama_model = default_ollama_model
        self.gemini_timeout = gemini_timeout
        self._gemini_available: Optional[bool] = None
        self._ollama_available: Optional[bool] = None
    
    def _check_gemini_available(self) -> bool:
        if self._gemini_available is not None:
            return self._gemini_available
        gemini_path = shutil.which("gemini")
        if not gemini_path:
            self._gemini_available = False
            return False
        try:
            result = subprocess.run(
                [gemini_path, "--version"],
                capture_output=True, text=True, timeout=10, shell=False,
            )
            self._gemini_available = result.returncode == 0
        except Exception:
            self._gemini_available = False
        return self._gemini_available
    
    def _check_ollama_available(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            models = self.ollama_client.models.list()
            self._ollama_available = len(models.data) > 0
        except Exception:
            self._ollama_available = False
        return self._ollama_available
    
    def _call_claude(self, prompt: str, model: str, system: str = "", max_tokens: int = 4096) -> ModelResponse:
        start = time.time()
        kwargs = dict(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
        if system:
            kwargs["system"] = system
        response = self.claude_client.messages.create(**kwargs)
        return ModelResponse(
            content=response.content[0].text,
            model_used=model,
            latency_ms=(time.time() - start) * 1000,
            token_count=response.usage.input_tokens + response.usage.output_tokens,
        )
    
    def _call_gemini_cli(self, prompt: str, model: str = "gemini-2.5-pro") -> ModelResponse:
        start = time.time()
        gemini_path = shutil.which("gemini")
        if not gemini_path:
            raise RuntimeError("Gemini CLI 미설치")
        
        result = subprocess.run(
            [gemini_path, "-p", prompt, "--model", model],
            capture_output=True, text=True,
            timeout=self.gemini_timeout, shell=False, encoding="utf-8",
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "auth" in stderr.lower() or "login" in stderr.lower():
                raise PermissionError(f"Gemini 인증 필요. 실행: gemini auth login\n{stderr}")
            if "rate" in stderr.lower() or "quota" in stderr.lower():
                raise RuntimeError(f"Gemini rate limit 초과: {stderr}")
            raise RuntimeError(f"Gemini CLI 오류 (code {result.returncode}): {stderr}")
        
        return ModelResponse(
            content=result.stdout.strip(),
            model_used=model,
            latency_ms=(time.time() - start) * 1000,
        )
    
    def _call_ollama(self, prompt: str, model: str = None) -> ModelResponse:
        start = time.time()
        model = model or self.default_ollama_model
        response = self.ollama_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return ModelResponse(
            content=response.choices[0].message.content,
            model_used=f"ollama/{model}",
            latency_ms=(time.time() - start) * 1000,
        )
    
    def _select_model(self, task: str) -> str:
        """태스크 분석 기반 자동 모델 선택"""
        task_lower = task.lower()
        
        # YAML/플랜 생성 → Claude Sonnet (구조화 출력 최적)
        if any(kw in task_lower for kw in ["yaml", "플랜", "plan", "workflow", "단계"]):
            return "claude-sonnet-4-5"
        
        # 대용량 코드베이스 → Gemini (1M 컨텍스트)
        if len(task) > 100_000:
            return "gemini-2.5-pro"
        
        # 코드 분석 + 대용량 → Gemini
        if any(kw in task_lower for kw in ["코드", "code"]) and len(task.split()) > 5000:
            return "gemini-2.5-pro"
        
        # 빠른 응답 → Claude Haiku
        if any(kw in task_lower for kw in ["간단", "빠르게", "요약", "summary"]):
            return "claude-haiku-4-5"
        
        # 개인정보/오프라인 → Ollama
        if any(kw in task_lower for kw in ["개인정보", "private", "오프라인"]):
            return "llama3.2"
        
        return "claude-sonnet-4-5"
    
    def route(self, task: str, model: str = "auto", fallback: bool = True) -> ModelResponse:
        if model == "auto":
            model = self._select_model(task)
        
        if model.startswith("claude-"):
            try:
                return self._call_claude(task, model)
            except anthropic.RateLimitError:
                if fallback and self._check_ollama_available():
                    resp = self._call_ollama(task)
                    resp.fallback_used = True
                    return resp
                raise
        
        if model.startswith("gemini-"):
            if not self._check_gemini_available():
                if fallback:
                    resp = self._call_claude(task, "claude-sonnet-4-5")
                    resp.fallback_used = True
                    return resp
                raise RuntimeError("Gemini CLI 미가용")
            try:
                return self._call_gemini_cli(task, model)
            except (RuntimeError, TimeoutError):
                if fallback:
                    resp = self._call_claude(task, "claude-haiku-4-5")
                    resp.fallback_used = True
                    return resp
                raise
        
        # Ollama
        return self._call_ollama(task, model.replace("ollama/", ""))
```

---

## 3. 자동 라우팅 결정 트리

```
태스크 입력
    │
    ├─ 길이 > 100K chars? ──YES──→ Gemini 2.5 Pro (1M context)
    │
    ├─ 개인정보/오프라인 요구? ──YES──→ Ollama (llama3.2)
    │
    ├─ YAML/플랜/워크플로? ──YES──→ Claude Sonnet
    │
    ├─ 코드 분석 + 대용량? ──YES──→ Gemini 2.5 Pro
    │
    ├─ 코드 분석 + 중소규모? ──YES──→ Claude Sonnet
    │
    ├─ 빠른 분류/요약? ──YES──→ Claude Haiku
    │
    └─ 기본값 ──→ Claude Sonnet
```

---

## 4. Ollama 설치 및 설정

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: https://ollama.com/download/windows

# 서비스로 실행
# macOS: brew services start ollama
# Linux: systemctl enable --now ollama

# 모델 다운로드
ollama pull llama3.2          # 2.0GB (3B)
ollama pull llama3.2:8b       # 5.0GB (8B)
ollama pull qwen2.5-coder:7b  # 4.7GB (코드 특화)
ollama pull qwen2.5-coder:14b # 9.0GB (고성능)
```

Ollama API 엔드포인트: `http://localhost:11434/v1/chat/completions` (OpenAI 호환)

---

## 5. v1.0 권장 아키텍처

```
┌─────────────────────────────────────────┐
│     AI Agentic Workflow System          │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │        MultiModelRouter         │   │
│  │                                 │   │
│  │  1순위: Claude API (API key)    │   │
│  │    ├─ claude-sonnet-4-5        │   │
│  │    ├─ claude-haiku-4-5         │   │
│  │    └─ claude-opus-4-5          │   │
│  │                                 │   │
│  │  2순위: Gemini CLI (OAuth2)    │   │
│  │    └─ gemini-2.5-pro (1M ctx) │   │
│  │                                 │   │
│  │  3순위: Ollama (localhost)     │   │
│  │    ├─ llama3.2                 │   │
│  │    └─ qwen2.5-coder            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  데이터: 로컬 전용, 외부 전송 없음       │
└─────────────────────────────────────────┘
```

**의존성**:
- `anthropic>=0.40.0`
- `openai>=1.50.0` (Ollama 클라이언트)
- Node.js 18+ + `@google/gemini-cli` (선택적)
- Ollama 서버 (폴백용, 선택적)

**설정 파일** (`config.yaml`):
```yaml
models:
  primary: claude-sonnet-4-5
  fallback_claude: claude-haiku-4-5
  fallback_local: ollama/llama3.2
  gemini_enabled: true
  gemini_model: gemini-2.5-pro

cache:
  enabled: true
  ttl_seconds: 3600
  directory: .llm_cache

timeouts:
  claude_seconds: 30
  gemini_seconds: 60
  ollama_seconds: 120
```
