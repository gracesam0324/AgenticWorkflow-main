#!/usr/bin/env python3
"""PreToolUse(Bash) hook: Block dangerous network commands.

Blocks: ngrok, localtunnel, curl/wget to non-localhost URLs.
Allows: npm, git, node, python, localhost/127.0.0.1 requests.
Exit 0 = allow, Exit 2 = block.
"""
import json
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _church_app_lib import parse_tool_input

BLOCKED_COMMANDS = ["ngrok", "localtunnel", "lt "]
NETWORK_COMMANDS = ["curl", "wget"]
LOCALHOST_PATTERNS = [
    r"localhost", r"127\.0\.0\.1", r"\[::1\]", r"0\.0\.0\.0",
]
SAFE_COMMANDS = ["npm", "npx", "git", "node", "python", "python3", "pip", "pip3", "ls", "cat", "mkdir"]


def is_localhost_url(cmd):
    """Check if network command targets localhost."""
    for pat in LOCALHOST_PATTERNS:
        if re.search(pat, cmd):
            return True
    return False


def main():
    tool_input = parse_tool_input()
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    cmd_lower = command.lower().strip()

    # Check for blocked tunnel/proxy commands
    for blocked in BLOCKED_COMMANDS:
        if blocked in cmd_lower:
            result = {
                "decision": "block",
                "reason": f"Command '{blocked.strip()}' is not allowed. "
                          "External tunneling/proxy services are blocked for security.",
            }
            print(json.dumps(result))
            sys.exit(2)

    # Check curl/wget to non-localhost
    for net_cmd in NETWORK_COMMANDS:
        if re.search(rf"\b{net_cmd}\b", cmd_lower):
            if not is_localhost_url(cmd_lower):
                result = {
                    "decision": "block",
                    "reason": f"'{net_cmd}' to external URLs is not allowed. "
                              "Only localhost requests are permitted.",
                }
                print(json.dumps(result))
                sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
