# Branch 1.2: Multi-AI Model Integration — Conservative (Claude 우선 + 선택적 폴백)
> Multi-AI Model Integration Specialist
> 조사일: 2026-04-07

---

## 전략 요약

Claude API를 기본으로, Ollama를 폴백으로 사용하는 최소 복잡도 전략.
Gemini CLI는 선택적으로만 포함 (대용량 컨텍스트 필요 시).

---

## 1. Claude SDK 최적화 활용

### 1.1 모델 선택 기준 (비용 최적화)

| 모델 | 컨텍스트 | 입력 비용 | 출력 비용 | 최적 태스크 |
|---|---|---|---|---|
| claude-opus-4-5 | 200K | $15/1M | $75/1M | 복잡한 추론, 장문 코드 분석 |
| claude-sonnet-4-5 | 200K | $3/1M | $15/1M | YAML 플랜 생성, 일반 분석 |
| claude-haiku-4-5 | 200K | $0.25/1M | $1.25/1M | 빠른 분류, 간단 요약 |

```python
def select_claude_model(prompt: str, task_type: str = "general") -> str:
    """복잡도 기반 Claude 모델 자동 선택"""
    prompt_tokens = len(prompt.split()) * 1.3
    
    if task_type in ("classify", "summarize", "extract") or prompt_tokens < 500:
        return "claude-haiku-4-5"
    
    if task_type in ("complex_reasoning", "architecture", "security_review"):
        return "claude-opus-4-5"
    
    return "claude-sonnet-4-5"  # 기본값
```

### 1.2 Streaming vs 동기 호출

```python
import anthropic
from typing import Generator

client = anthropic.Anthropic(api_key="...")

def call_claude_streaming(prompt: str, model: str = "claude-sonnet-4-5") -> Generator[str, None, None]:
    """
    스트리밍: 긴 응답 (YAML 플랜 생성, 코드 생성)
    사용자에게 진행상황 실시간 표시 가능
    """
    with client.messages.stream(
        model=model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text

def call_claude_sync(prompt: str, model: str = "claude-haiku-4-5") -> str:
    """
    동기: 분류, 짧은 응답, 결과 전체가 필요한 파싱 로직
    """
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
```

**선택 기준**:
- **Streaming**: YAML 플랜 생성, 코드 생성, 사용자 진행상황 표시 필요 시
- **동기**: 분류, 라우팅 결정, 짧은 판단, Pydantic 파싱이 이어질 때

### 1.3 Prompt Caching (비용 90% 절감)

```python
def call_claude_with_cache(
    system_prompt: str,
    user_prompt: str,
    model: str = "claude-sonnet-4-5",
) -> str:
    """
    시스템 프롬프트 캐싱.
    동일 시스템 프롬프트 반복 호출 시 최대 90% 비용 절감.
    캐시 TTL: 5분 (ephemeral)
    """
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text

# YAML 스키마 정의를 시스템 프롬프트에 넣고 캐싱
YAML_SYSTEM_PROMPT = """당신은 AI Workflow Planner입니다. 다음 스키마를 준수하세요: ..."""

result1 = call_claude_with_cache(YAML_SYSTEM_PROMPT, "Python 파일 정리 워크플로")  # 캐시 미스
result2 = call_claude_with_cache(YAML_SYSTEM_PROMPT, "Git 커밋 자동화 워크플로")   # 캐시 히트 (90% 절감)
```

### 1.4 대화 이력 효율 관리

```python
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ConversationManager:
    max_messages: int = 20
    max_context_tokens: int = 150_000  # 200K의 75%
    _history: deque = field(default_factory=lambda: deque(maxlen=20))
    
    def add_message(self, role: str, content: str):
        self._history.append({"role": role, "content": content})
    
    def get_messages(self) -> List[Dict]:
        return list(self._history)
    
    def estimate_tokens(self) -> int:
        return int(sum(len(m["content"]) for m in self._history) / 4)
    
    def truncate_if_needed(self):
        while self.estimate_tokens() > self.max_context_tokens and len(self._history) > 2:
            self._history.popleft()
            if self._history:
                self._history.popleft()
```

---

## 2. Conservative LLMRouter (Claude 우선 + Ollama 폴백)

```python
"""
llm_router.py — Conservative 전략
폴백 순서: Claude Sonnet → Claude Haiku → Ollama
"""
import anthropic
from openai import OpenAI, APIConnectionError
from anthropic import RateLimitError, APIStatusError
import logging, time
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
            raise RuntimeError("최대 재시도 횟수 초과")
        return wrapper
    return decorator


class LLMRouter:
    """
    Claude 우선 + Ollama 폴백.
    폴백 순서:
    1. Claude Sonnet (기본)
    2. Claude Haiku (Sonnet rate limit 시)
    3. Ollama llama3.2 (Claude 전체 장애 시)
    """
    
    def __init__(
        self,
        anthropic_api_key: str,
        primary_model: str = "claude-sonnet-4-5",
        haiku_model: str = "claude-haiku-4-5",
        ollama_model: str = "llama3.2",
        ollama_base_url: str = "http://localhost:11434/v1",
    ):
        self.claude = anthropic.Anthropic(api_key=anthropic_api_key)
        self.ollama = OpenAI(base_url=ollama_base_url, api_key="ollama")
        self.primary_model = primary_model
        self.haiku_model = haiku_model
        self.ollama_model = ollama_model
        self._call_count = {"claude": 0, "haiku": 0, "ollama": 0}
    
    def call(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        # 1차: Claude Sonnet
        try:
            result = self._call_claude(prompt, self.primary_model, system, max_tokens)
            self._call_count["claude"] += 1
            return result
        except RateLimitError as e:
            logger.warning(f"Claude Sonnet rate limit: {e}")
        except APIStatusError as e:
            if e.status_code == 529:
                logger.warning("Claude Sonnet 과부하")
            else:
                raise
        
        # 2차 폴백: Claude Haiku
        try:
            result = self._call_claude(prompt, self.haiku_model, system, max_tokens)
            self._call_count["haiku"] += 1
            return result
        except (RateLimitError, Exception) as e:
            logger.warning(f"Claude Haiku도 실패: {e}")
        
        # 3차 폴백: Ollama
        logger.info("Ollama 로컬 모델로 최종 폴백")
        result = self._call_ollama(prompt, system)
        self._call_count["ollama"] += 1
        return result
    
    @retry_with_backoff(max_retries=2)
    def _call_claude(self, prompt: str, model: str, system: str = "", max_tokens: int = 4096) -> str:
        kwargs = dict(
            model=model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        if system:
            kwargs["system"] = system
        response = self.claude.messages.create(**kwargs)
        return response.content[0].text
    
    def _call_ollama(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.ollama.chat.completions.create(
                model=self.ollama_model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except APIConnectionError:
            raise RuntimeError("Ollama 서버 미가동. 'ollama serve' 실행 필요")
    
    def get_stats(self) -> dict:
        total = sum(self._call_count.values())
        return {
            "total_calls": total,
            "by_model": self._call_count,
            "fallback_rate": (
                (self._call_count["haiku"] + self._call_count["ollama"]) / total
                if total > 0 else 0
            ),
        }
```

---

## 3. API 호출 캐싱 (비용 절감)

```python
import hashlib, json, time
from pathlib import Path
from typing import Optional

class LLMCache:
    """파일 기반 LLM 응답 캐시"""
    
    def __init__(self, cache_dir: str = ".llm_cache", ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl_seconds
    
    def _make_key(self, prompt: str, model: str, system: str = "") -> str:
        content = json.dumps({"prompt": prompt, "model": model, "system": system})
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get(self, prompt: str, model: str, system: str = "") -> Optional[str]:
        key = self._make_key(prompt, model, system)
        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        if time.time() - data["timestamp"] > self.ttl:
            cache_file.unlink()
            return None
        return data["response"]
    
    def set(self, prompt: str, model: str, response: str, system: str = ""):
        key = self._make_key(prompt, model, system)
        cache_file = self.cache_dir / f"{key}.json"
        data = {
            "timestamp": time.time(),
            "model": model,
            "prompt_preview": prompt[:100],
            "response": response,
        }
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class CachedLLMRouter(LLMRouter):
    """LLMRouter + 캐싱"""
    
    def __init__(self, *args, cache_ttl: int = 3600, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = LLMCache(ttl_seconds=cache_ttl)
    
    def call(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        cached = self.cache.get(prompt, self.primary_model, system)
        if cached:
            logger.debug("캐시 히트 - API 호출 절약")
            return cached
        result = super().call(prompt, system, max_tokens)
        self.cache.set(prompt, self.primary_model, result, system)
        return result
```

---

## 4. 기술 실현 가능성 평가

| 연동 대상 | 가능성 | 근거 |
|---|---|---|
| Claude API (API key) | ★★★★★ | 공식 SDK, 안정적 |
| Gemini CLI (OAuth2) | ★★★★☆ | 공식 오픈소스, subprocess 호환 |
| Ollama (localhost) | ★★★★★ | 완전 로컬, OpenAI 호환 |
| OpenAI 구독 계정 CLI | ★☆☆☆☆ | **공식 방법 없음** — Ollama로 대체 |

---

## 5. PRD 권고 (Conservative)

**v1.0 필수 구성**:
- Claude Sonnet/Haiku (API key) — 핵심
- Ollama 폴백 — 선택적 but 권장
- `LLMCache` — API 비용 절감

**v1.1으로 연기**:
- Gemini CLI 통합 (대용량 컨텍스트용)
- MultiModelRouter 자동 라우팅

**영구 제외**:
- OpenAI 구독 계정 연동 (공식 API 없음)
- 비공식 reverse-engineered 방법 (이용약관 위반)
