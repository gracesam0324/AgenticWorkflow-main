---
description: "Deploy completed church retreat app (Phase 6)"
---

# /deploy-app — 수련회 앱 배포

Deploy the completed church retreat app. Executes Phase 6 of the workflow.

## Execute These Steps

### Step 1: Load Deployment Spec

Use the **Read tool** to load:
1. `prompt/workflow.md` Step 10 (Deployment)
2. `prompt/workflow-coding.md` §4.6 (deployment-manager spec)
3. `app-state.json` from the current project

### Step 2: Verify Readiness

Check SOT fields:
- `status.quality_passed == true` — Phase 4 complete
- `status.user_approved == true` — Phase 5 complete (사역자 confirmed)

If not ready:
- Korean: "아직 앱이 완성되지 않았어요. 먼저 품질 검증과 미리보기를 완료해 주세요."
- Suggest appropriate phase to run first

### Step 3: Spawn Deployment Manager

Activate `@deployment-manager` agent with:
- Project path from SOT
- App type from SOT
- Deployment target: LAN server (default) or GitHub Pages (if user chose)

### Step 4: Execute Deployment

The deployment-manager performs:

1. **Start LAN server** (background)
   ```bash
   # Using Bash tool's run_in_background option
   node server.js
   ```

2. **Detect IP address**
   ```bash
   # Windows
   ipconfig | findstr /i "IPv4"
   ```

3. **Generate QR code**
   - URL: `http://{IP}:{PORT}/`
   - Save as `qr-code.png` in project folder

4. **Create print-ready HTML page** (A4)
   - Church name + retreat name
   - QR code image
   - WiFi connection instructions
   - URL as text fallback

5. **Create "앱 실행.bat"** on Desktop
   - Korean console messages
   - Node.js self-check
   - Auto-restart on crash (max 5 retries)
   - IP change detection + QR regeneration

6. **Generate emergency response card** (Korean)
   - "서버가 안 돼요" → .bat 파일 다시 실행
   - "QR이 안 돼요" → WiFi 확인 + URL 직접 입력
   - "앱이 느려요" → 접속자 수 확인
   - Claude Code 재실행 안내

7. **Generate WiFi instructions page**
   - SSID + password (if provided)
   - Step-by-step Korean instructions for students
   - QR scan instructions

8. **Auto-open browser** with QR page
   ```bash
   start http://localhost:{PORT}/
   ```

### Step 5: Update SOT

Write to `app-state.json`:
```json
{
  "deployment": {
    "method": "lan",
    "port": 3000,
    "ip": "{detected_ip}",
    "url": "http://{ip}:{port}/",
    "qr_path": "qr-code.png",
    "bat_path": "~/Desktop/앱 실행.bat",
    "deployed_at": "{timestamp}"
  },
  "status": {
    "deployed": true
  }
}
```

### Step 6: Git Checkpoint

```bash
git add -A && git commit -m "[배포] 최종 빌드 완료"
```

### Step 7: Display Completion in Korean

```
🎉 앱 배포가 완료되었어요!

📱 앱 주소: http://{IP}:{PORT}/
📷 QR코드: qr-code.png (프린트해서 사용하세요)
🖥️ 바탕화면에 "앱 실행.bat" 파일을 만들었어요

사용 방법:
1. 수련회장에서 "앱 실행.bat"을 더블클릭하세요
2. QR코드를 프린트하거나 빔프로젝터로 보여주세요
3. 학생들이 QR코드를 스캔하면 바로 접속!

⚠️ 주의: 이 창(서버)을 닫지 마세요. 닫으면 앱이 꺼져요.
💡 만약 문제가 생기면 긴급 대응 카드를 확인하세요.
```

## Error Handling

| Error | Korean Message | Action |
|-------|---------------|--------|
| Port in use | "포트가 사용 중이에요. 다른 포트로 바꿀게요." | Scan 3000-3010 |
| No network | "네트워크가 연결되어 있지 않아요. WiFi를 켜주세요." | Wait + retry |
| QR generation fail | "QR코드 생성에 실패했어요. URL을 직접 공유하세요." | Display URL text |
| Browser open fail | "브라우저가 안 열렸어요. 이 주소를 직접 열어주세요." | Show URL |
