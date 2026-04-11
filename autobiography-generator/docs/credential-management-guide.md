# Credential Management Guide

## Security Architecture for AI Autobiography Generator

This guide covers secure storage and access of API credentials for the multi-model
local workflow. All credentials live on the local macOS machine and never enter
version control.

---

## 1. Credential Inventory

| Credential | Provider | Storage Method | Access Pattern |
|-----------|----------|---------------|----------------|
| Claude API key | Anthropic | Native (Claude Code handles) | Automatic via `claude` CLI |
| OpenAI API key | OpenAI | macOS Keychain via `keyring` | `credential_manager.get("openai")` |
| Gemini API key | Google | macOS Keychain via `keyring` | `credential_manager.get("gemini")` |

---

## 2. Storage Tiers (Defense in Depth)

### Tier 1: macOS Keychain (RECOMMENDED for all API keys)

The macOS Keychain is an OS-level encrypted credential store protected by the
user's login password and the Secure Enclave on Apple Silicon. The Python
`keyring` library provides a clean interface.

**Why Keychain over .env files:**
- Encrypted at rest (AES-256-GCM on Apple Silicon)
- Per-application access control (apps must be authorized)
- No plaintext files on disk that could be accidentally committed
- Survives disk imaging without exposing secrets
- Auditable via Keychain Access.app

**Setup:**
```bash
pip install keyring
```

**Store credentials (one-time, from terminal):**
```python
import keyring

# Store OpenAI key
keyring.set_password("autobiography-generator", "openai-api-key", "sk-proj-...")

# Store Gemini key
keyring.set_password("autobiography-generator", "gemini-api-key", "AIza...")
```

**Retrieve credentials (in scripts):**
```python
import keyring

openai_key = keyring.get_password("autobiography-generator", "openai-api-key")
gemini_key = keyring.get_password("autobiography-generator", "gemini-api-key")
```

**Delete credentials:**
```python
keyring.delete_password("autobiography-generator", "openai-api-key")
```

### Tier 2: Environment Variables (Fallback)

For CI/CD or environments without Keychain access, fall back to environment
variables. These are less secure but widely supported.

```bash
# In ~/.zshrc or ~/.bash_profile (NOT in .env files in the repo)
export OPENAI_API_KEY="sk-proj-..."
export GEMINI_API_KEY="AIza..."
```

### Tier 3: .env Files (Development Only, STRONGLY DISCOURAGED)

If you must use .env files:
1. The file MUST be in `.gitignore` (already configured)
2. Set file permissions to owner-only: `chmod 600 .env`
3. Never store .env in project directories accessed by Claude Code
   (Claude Code auto-reads .env files, potentially sending contents to servers)

---

## 3. Credential Manager Module

The `credential_manager.py` module (in `scripts/`) provides a unified interface
with automatic tier fallback:

```
Keychain -> Environment Variable -> Fail with clear error
```

Key features:
- Automatic provider detection and fallback
- Credential validation (format checks before use)
- Rotation reminders (warns after 90 days)
- Never logs or prints credential values
- Thread-safe access

See `scripts/credential_manager.py` for implementation.

---

## 4. Claude Code Security Considerations

### Known Risks (CVE-2025-59536, CVE-2026-21852)

Claude Code has known vulnerabilities related to:
- Automatic .env file reading without explicit permission
- Hook-based credential exfiltration via malicious project configs
- Environment variable exposure through confused-deputy attacks

### Mitigations Applied in This Project

1. **No .env files in project directory** -- credentials in Keychain only
2. **`block_destructive_commands.py` hook** -- blocks network exfiltration
3. **`output_secret_filter.py` hook** -- detects credential patterns in output
4. **`security_sensitive_file_guard.py` hook** -- warns on security file edits
5. **Deny rules in `.claude/settings.json`** -- blocks access to sensitive paths

### Recommended `.claude/settings.json` Deny Rules

```json
{
  "permissions": {
    "deny": [
      "Read(.env*)",
      "Read(**/credentials*)",
      "Read(**/*secret*)",
      "Read(**/*token*)",
      "Bash(curl*)",
      "Bash(wget*)"
    ]
  }
}
```

---

## 5. Key Rotation Schedule

| Credential | Rotation Interval | Last Rotated | Next Due |
|-----------|-------------------|-------------|----------|
| OpenAI API key | 90 days | (set on first use) | (auto-calculated) |
| Gemini API key | 90 days | (set on first use) | (auto-calculated) |

The `credential_manager.py` module stores rotation metadata in Keychain alongside
the credential and warns when rotation is due.

---

## 6. Emergency Procedures

### If a Key Is Compromised

1. **Immediately revoke** the key at the provider's dashboard:
   - OpenAI: https://platform.openai.com/api-keys
   - Gemini: https://aistudio.google.com/apikey
2. **Delete from Keychain**: `keyring.delete_password("autobiography-generator", "<key-name>")`
3. **Generate new key** at the provider
4. **Store new key**: `keyring.set_password("autobiography-generator", "<key-name>", "<new-key>")`
5. **Audit git history**: `git log --all --full-history -- '*.env*' '*.key' '*.secret'`
6. **Run health check**: `python3 scripts/integration_health_check.py`

### If Keychain Is Unavailable

The credential manager falls back to environment variables automatically.
Set them in your shell profile (not in .env files).

---

## Sources

- [Python keyring library](https://pypi.org/project/keyring/)
- [Apple TN3137: On Mac keychain APIs](https://developer.apple.com/documentation/technotes/tn3137-on-mac-keychains)
- [OpenAI API Key Best Practices](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
- [Gemini API Key Usage](https://ai.google.dev/gemini-api/docs/api-key)
- [Claude Code Environment Variables](https://support.claude.com/en/articles/12304248-managing-api-key-environment-variables-in-claude-code)
- [Claude Code Hook Vulnerabilities (CVE-2025-59536)](https://research.checkpoint.com/2026/rce-and-api-token-exfiltration-through-claude-code-project-files-cve-2025-59536/)
- [Claude Code Auto-Loads .env Secrets](https://www.knostic.ai/blog/claude-loads-secrets-without-permission)
- [Gemini API Key Security Risk (Simon Willison)](https://simonwillison.net/2026/Feb/26/google-api-keys/)
