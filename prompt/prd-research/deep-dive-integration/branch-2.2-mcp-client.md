# Branch 2.2: MCP 프로토콜 통합 — MCP 클라이언트 구현
> MCP Protocol Integration Specialist
> 조사일: 2026-04-07

---

## 전략: 우리 시스템이 외부 MCP 서버를 클라이언트로 호출

```python
# workflow_automation/mcp_client_integration.py
"""
워크플로우 실행 중 외부 MCP 서버를 호출하는 클라이언트
Python MCP SDK 1.2.0+
"""

import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class WorkflowMCPClient:
    """워크플로우 실행 중 외부 MCP 서버 호출 클라이언트"""

    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}

    async def connect_filesystem_server(self, allowed_paths: list[str]) -> ClientSession:
        """Filesystem MCP 서버 연결"""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"] + allowed_paths,
            env=None
        )
        transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        self._sessions["filesystem"] = session
        return session

    async def connect_git_server(self, repo_path: str) -> ClientSession:
        """Git MCP 서버 연결"""
        server_params = StdioServerParameters(
            command="uvx",
            args=["mcp-server-git", "--repository", repo_path],
            env=None
        )
        transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = transport
        session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        self._sessions["git"] = session
        return session

    async def read_file(self, path: str) -> str:
        """Filesystem MCP를 통해 파일 읽기"""
        session = self._sessions.get("filesystem")
        if not session:
            raise RuntimeError("Filesystem MCP 서버에 연결되지 않았습니다.")

        result = await asyncio.wait_for(
            session.call_tool("read_file", {"path": path}),
            timeout=30.0
        )
        contents = result.content
        return contents[0].text if contents and hasattr(contents[0], "text") else ""

    async def get_git_status(self) -> str:
        """Git MCP를 통해 저장소 상태 조회"""
        session = self._sessions.get("git")
        if not session:
            raise RuntimeError("Git MCP 서버에 연결되지 않았습니다.")

        result = await session.call_tool("git_status", {})
        return result.content[0].text if result.content else ""

    async def connect_multiple_servers(
        self,
        filesystem_paths: list[str] | None = None,
        git_repo: str | None = None
    ):
        """여러 MCP 서버를 병렬 연결"""
        tasks = []
        if filesystem_paths:
            tasks.append(self.connect_filesystem_server(filesystem_paths))
        if git_repo:
            tasks.append(self.connect_git_server(git_repo))
        await asyncio.gather(*tasks)

    async def cleanup(self):
        await self.exit_stack.aclose()
        self._sessions.clear()


# 사용 예시
async def workflow_with_mcp():
    client = WorkflowMCPClient()
    try:
        await client.connect_multiple_servers(
            filesystem_paths=["C:\\Users\\김성준\\projects"],
            git_repo="C:\\Users\\김성준\\projects\\my-project"
        )
        content = await client.read_file("C:\\Users\\김성준\\projects\\README.md")
        git_status = await client.get_git_status()
    finally:
        await client.cleanup()
```

---

## Claude API + MCP 베타 기능 (제약 확인)

```python
import anthropic

client = anthropic.Anthropic()

# 원격 MCP 서버를 Claude API에 등록 (베타)
# 단: URL 방식의 원격 서버만 지원, 로컬 stdio 서버 불가
response = client.beta.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "파일 시스템 분석"}],
    betas=["mcp-client-2025-04-04"],
    mcp_servers=[
        {
            "type": "url",
            "url": "https://my-remote-server.example.com/mcp",
            "name": "remote-filesystem",
        }
    ]
)
```

**우리 시스템 한계**: 이 방식은 원격 HTTP 엔드포인트 요구 → "절대 SaaS 아님, 데이터 로컬" 원칙과 충돌. **Claude Desktop + stdio MCP 서버** 조합이 올바른 접근.

---

## MCP vs 직접 subprocess 비교

| 항목 | MCP 방식 (stdio) | 직접 subprocess |
|---|---|---|
| 표준화 | JSON-RPC 2.0 기반 | 시스템 전용 |
| 생태계 활용 | filesystem/git/fetch 즉시 사용 | 직접 구현 필요 |
| Claude Desktop 통합 | 네이티브 지원 | 불가능 |
| v1.0 구현 현실성 | 1-2일 추가 | 즉시 가능 |
| 장기 유지보수 | 쉬움 | 어려움 |

---

## PRD 권고 (하이브리드 전략)

- **MCP 서버로 노출** (v1.0 필수): 4개 도구
- **외부 MCP 클라이언트** (v1.1): filesystem + git MCP를 워크플로우 엔진 내부에서 클라이언트로 연결
- **직접 subprocess 유지**: 핵심 실행 엔진은 subprocess 유지 (이미 검증됨)

**비즈니스 가치**:
- "Claude Desktop에서 바로 사용 가능한 워크플로우 자동화" 포지셔닝
- Anthropic 승인 UI로 사용자 동의 자동화
- filesystem/git/memory 등 기존 MCP 서버 동시 활용
