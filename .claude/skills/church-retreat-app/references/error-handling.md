# Error Handling — Church Retreat App

> Error recovery tree by phase, Korean error messages for 사역자, fallback escalation,
> and WebSocket reconnection strategy.

---

## Error Recovery Tree by Phase

### Phase 0 — Environment Setup Errors

```
Node.js not found
  → Korean: "Node.js가 설치되어 있지 않아요."
  → Action: Guide 사역자 to install Node.js (provide download link)
  → Fallback: Offer GitHub Pages static-only mode (no WebSocket apps)

npm not found
  → Korean: "npm이 설치되어 있지 않아요. Node.js를 다시 설치해 주세요."
  → Action: Node.js reinstall includes npm

git not found
  → Korean: "Git이 설치되어 있지 않아요."
  → Action: Guide installation OR continue without git (no checkpoints)
  → Fallback: Manual backup copies instead of git checkpoints

Folder creation failed
  → Korean: "폴더를 만들 수 없어요. 다른 위치에 만들까요?"
  → Action: Try alternative path (Documents → D:\ → C:\temp)
```

### Phase 1 — Content Collection Errors

```
Content too large (>50KB total)
  → Korean: "내용이 너무 많아요. 핵심만 추려볼까요?"
  → Action: Summarize/truncate content with 사역자 approval

Missing required fields
  → Korean: "{field_name}이(가) 아직 없어요. 알려주실 수 있나요?"
  → Action: Re-prompt for specific missing content
  → Gate: validate_content_collection.py blocks Phase 2 until complete

File read error (content file)
  → Korean: "파일을 읽을 수 없어요. 다시 보내주시겠어요?"
  → Action: Retry file read, suggest alternative format (copy-paste)

Invalid app type selection
  → Korean: "잘 이해하지 못했어요. 1~9 중에 골라주세요."
  → Action: Re-present menu
```

### Phase 2 — Project Initialization Errors

```
npm install failure
  → Korean: "패키지 설치 중 문제가 생겼어요. 다시 시도할게요."
  → Action: Retry with --force → retry with reduced dependencies
  → Fallback: Static-only mode (no express/ws)

Port already in use
  → Korean: "포트 {PORT}이 이미 사용 중이에요. 다른 포트로 바꿀게요."
  → Action: Scan ports 3000-3010 for available

Disk space insufficient
  → Korean: "디스크 공간이 부족해요. 100MB 이상 확보해 주세요."
  → Action: Report required space, wait for user to free space
```

### Phase 3 — Code Generation Errors

```
TDD test write failure
  → Korean: (internal — not shown to 사역자)
  → Action: Retry test generation → skip to manual testing

Code generation produces syntax errors
  → Korean: (internal — auto-fixed)
  → Action: Run linter → auto-fix → re-verify
  → Gate: Q2 catches HTML errors in Phase 4

Integration verification failure (T-3.11)
  → Korean: (internal — auto-fixed)
  → Action: Fix orphaned classes/dangling refs → re-run validate_integration.py

P1 script copy failure
  → Korean: (internal)
  → Action: Verify template path → retry copy → generate scripts inline as last resort
```

### Phase 4 — Quality Verification Errors

```
Script execution error (exit code 1)
  → Korean: (internal)
  → Action: Check script syntax → verify project-dir exists → retry

Gate failure (FAIL result)
  → Korean: (internal for Pass 2 fixes)
  → Action: @quality-checker applies fix → re-run specific gate
  → Max 3 retries per gate
  → If still failing after 3 retries:
    → Git rollback to last checkpoint
    → Korean: "품질 검증에서 문제가 생겼어요. 다시 만들어 볼게요."

All gates fail simultaneously
  → Korean: "앱 생성 중 큰 문제가 생겼어요. 처음부터 다시 시도할까요?"
  → Action: Git rollback to Phase 2 checkpoint → regenerate
```

### Phase 5 — Preview & Feedback Errors

```
Browser open failure
  → Korean: "브라우저가 자동으로 열리지 않았어요. 이 주소를 직접 열어주세요: {URL}"
  → Action: Display URL as fallback

Server crash during preview
  → Korean: "서버가 멈췄어요. 다시 시작할게요."
  → Action: Restart server → regenerate QR (IP may have changed)

QR code invalid after IP change
  → Korean: "WiFi가 바뀐 것 같아요. QR코드를 새로 만들게요."
  → Action: Detect new IP → regenerate QR

Modification loop exceeds 5 cycles
  → Korean: "많이 수정했네요! 이 부분은 직접 만나서 이야기해 볼까요?"
  → Action: Suggest saving current state + scheduling follow-up
```

### Phase 6 — Deployment Errors

```
.bat file creation failure
  → Korean: "바탕화면에 실행 파일을 만들 수 없었어요."
  → Action: Try alternative location → provide manual start command

QR generation failure
  → Korean: "QR코드 생성에 문제가 있어요. 주소를 직접 공유하세요: {URL}"
  → Action: Display URL as text fallback

Server won't start in background
  → Korean: "서버 실행에 문제가 있어요. .bat 파일로 직접 실행해 주세요."
  → Action: Provide manual instructions

GitHub Pages deployment failure
  → Korean: "GitHub 배포에 문제가 있어요. 로컬 서버로 진행할까요?"
  → Action: Fallback to LAN-only deployment
```

---

## Fallback Escalation Tiers

```
Tier 0: Normal operation
  → All systems nominal

Tier 1: Auto-retry (internal, invisible to 사역자)
  → Script errors, transient network issues
  → Max 3 retries with exponential backoff

Tier 2: Auto-fix (brief Korean notification)
  → Quality gate failures, missing dependencies
  → @quality-checker or orchestrator applies fix
  → Korean: "조금 수정하고 있어요. 잠시만요."

Tier 3: User notification (Korean explanation + options)
  → Persistent failures, environment issues
  → Korean: "문제가 생겼어요. {description}. {option_A} 할까요, {option_B} 할까요?"
  → 사역자 chooses path

Tier 4: Graceful degradation (reduced feature set)
  → Cannot fix within constraints
  → Korean: "이 기능은 지금 환경에서 어려워요. {feature}은 빼고 나머지만 만들까요?"
  → Remove problematic feature, continue with rest

Tier 5: Manual intervention (emergency)
  → System-level issue (disk, permissions, Node.js broken)
  → Korean: "기술적인 도움이 필요해요. 이 화면을 기술 담당자에게 보여주세요."
  → Display diagnostic info for tech support
```

---

## WebSocket Reconnection Strategy

```javascript
// Client-side WebSocket reconnection (included in all realtime apps)
class ReconnectingWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.maxRetries = options.maxRetries || 10;
    this.baseDelay = options.baseDelay || 1000;  // 1 second
    this.maxDelay = options.maxDelay || 30000;    // 30 seconds
    this.retryCount = 0;
    this.handlers = { open: [], close: [], message: [], error: [] };
    this.connect();
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = (e) => {
      this.retryCount = 0;  // Reset on successful connection
      this.handlers.open.forEach(h => h(e));
      console.log('[WS] 연결됨');
    };

    this.ws.onclose = (e) => {
      this.handlers.close.forEach(h => h(e));
      if (this.retryCount < this.maxRetries) {
        const delay = Math.min(
          this.baseDelay * Math.pow(2, this.retryCount),
          this.maxDelay
        );
        console.log(`[WS] ${delay}ms 후 재연결 시도 (${this.retryCount + 1}/${this.maxRetries})`);
        setTimeout(() => {
          this.retryCount++;
          this.connect();
        }, delay);
      } else {
        console.error('[WS] 최대 재시도 횟수 초과');
        this.showReconnectUI();
      }
    };

    this.ws.onmessage = (e) => this.handlers.message.forEach(h => h(e));
    this.ws.onerror = (e) => this.handlers.error.forEach(h => h(e));
  }

  on(event, handler) {
    this.handlers[event].push(handler);
  }

  send(data) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  showReconnectUI() {
    // Show Korean reconnection prompt
    const overlay = document.createElement('div');
    overlay.innerHTML = `
      <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);
                  display:flex;align-items:center;justify-content:center;z-index:9999">
        <div style="background:white;padding:24px;border-radius:16px;text-align:center;max-width:300px">
          <p style="font-size:18px;margin-bottom:16px">연결이 끊어졌어요</p>
          <button onclick="location.reload()" 
                  style="padding:12px 24px;background:var(--primary,#4F46E5);
                         color:white;border:none;border-radius:12px;font-size:16px;
                         min-height:44px;cursor:pointer">
            다시 연결하기
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  }
}
```

---

## Korean Error Message Templates

| Code | Korean Message | Context |
|------|---------------|---------|
| E001 | "Node.js가 설치되어 있지 않아요." | Phase 0 environment |
| E002 | "npm 패키지 설치에 실패했어요. 다시 시도할게요." | Phase 2 init |
| E003 | "포트 {PORT}이 사용 중이에요. {NEW_PORT}로 바꿀게요." | Server start |
| E004 | "파일을 읽을 수 없어요. 다시 보내주시겠어요?" | Content file |
| E005 | "서버가 멈췄어요. 다시 시작할게요." | Runtime crash |
| E006 | "WiFi가 바뀐 것 같아요. QR코드를 새로 만들게요." | IP change |
| E007 | "품질 검증에서 문제가 생겼어요. 자동으로 수정하고 있어요." | Gate failure |
| E008 | "디스크 공간이 부족해요. 100MB 이상 확보해 주세요." | Disk full |
| E009 | "브라우저가 자동으로 열리지 않았어요. 이 주소를 열어주세요: {URL}" | Browser fail |
| E010 | "연결이 끊어졌어요. 다시 연결할게요." | WebSocket |
| E011 | "기술적인 도움이 필요해요. 이 화면을 기술 담당자에게 보여주세요." | Tier 5 |
| E012 | "잘 이해하지 못했어요. 다시 한번 말씀해 주세요." | Input parse fail |
