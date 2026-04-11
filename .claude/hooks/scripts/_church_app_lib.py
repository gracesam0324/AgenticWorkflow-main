#!/usr/bin/env python3
"""
Shared utility library for church-retreat-app workflow hooks.
Lives at: .claude/hooks/scripts/_church_app_lib.py

WHY a separate library (not extending _context_lib.py):
  _context_lib.py is the PARENT genome's shared library — used by
  autobiography-generator and all other workflows. Modifying it
  would create a ripple effect across the entire AgenticWorkflow project.
  _church_app_lib.py is church-app-specific, imports FROM _context_lib
  where needed, and adds church-app-specific utilities.

Dependencies: _context_lib.py (read-only import for atomic_write)
"""

import json
import os
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Re-export from parent library (verified to exist at _context_lib.py:2257)
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)
try:
    from _context_lib import atomic_write
except ImportError:
    def atomic_write(filepath, content, mode='w'):
        """Fallback if _context_lib not available (e.g., in testing)."""
        parent = os.path.dirname(filepath)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(filepath, mode, encoding='utf-8') as f:
            f.write(content)


# =============================================================================
# Hook Input Parsing (C-1 FIX: returns tool_input dict, not full stdin)
# =============================================================================

def parse_tool_input():
    """Parse Claude Code hook stdin JSON. Returns tool_input dict.

    Claude Code hooks receive JSON on stdin:
      {"tool_name": "Write", "tool_input": {"file_path": "...", ...}}

    This function returns ONLY the tool_input dict.
    Callers can then do: tool_input.get("file_path", "")
    """
    try:
        data = json.load(sys.stdin)
        return data.get("tool_input", {})
    except (json.JSONDecodeError, IOError, ValueError):
        return {}


def parse_tool_input_from_string(input_string):
    """Parse hook input from a string (for testing). Returns tool_input dict."""
    try:
        data = json.loads(input_string)
        return data.get("tool_input", {})
    except (json.JSONDecodeError, ValueError):
        return {}


# =============================================================================
# Environment Helpers
# =============================================================================

def get_agent_name():
    """Read current agent name from CLAUDE_AGENT_NAME env var."""
    return os.environ.get("CLAUDE_AGENT_NAME", "unknown")


def get_project_dir():
    """Read project directory from CLAUDE_PROJECT_DIR env var.
    Fallback: current working directory (per blueprint §7.3)."""
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


# =============================================================================
# SOT (app-state.json) Operations
# =============================================================================

# C-2 FIX: Only app-state.json is SOT. Only church-app-orchestrator writes.
SOT_FILES = ["app-state.json"]
ALLOWED_SOT_WRITERS = ["church-app-orchestrator"]


def read_sot(project_dir=None):
    """Read app-state.json from project folder. Returns dict or empty dict."""
    pdir = project_dir or get_project_dir()
    sot_path = os.path.join(pdir, "app-state.json")
    if not os.path.exists(sot_path):
        return {}
    try:
        with open(sot_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def get_sot_field(field_path, project_dir=None):
    """Get a nested field from SOT using dot notation. E.g., 'status.current_phase'.
    Returns None if field not found."""
    sot = read_sot(project_dir)
    keys = field_path.split(".")
    current = sot
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def is_agent_team_active(project_dir=None):
    """Check if Agent Team mode is active (from SOT)."""
    val = get_sot_field("status.agent_team_active", project_dir)
    return val is True


# =============================================================================
# File Pattern Matching
# =============================================================================

def match_file_pattern(filepath, patterns):
    """Check if filepath matches any glob-like pattern in the list.
    Handles both Unix and Windows path separators."""
    import fnmatch
    basename = os.path.basename(filepath)
    filepath_normalized = filepath.replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(filepath_normalized, pattern):
            return True
    return False


# =============================================================================
# Agent Team File Ownership (C-3 FIX: agent_name → [file_patterns])
# =============================================================================

OWNERSHIP_MAP = {
    "code-generator": [
        "server.js", "*.html", "app.js", "routes/*.js",
        "data.json", "package.json", "regenerate-qr.js",
    ],
    "design-system": [
        "styles.css", "animations.css", "manifest.json",
        "service-worker.js", "icons/*",
    ],
    "tdd-guard": [
        "tests/*", "verify-app.js", "scripts/*",
    ],
    "app-translator": [
        "reports/*.ko.md", "pacs-logs/*", "translations/*.yaml",
    ],
}


def get_file_owner(filepath):
    """Determine which agent owns a given file based on OWNERSHIP_MAP.
    Returns agent name or None if unowned (shared/free).

    Structure: {agent_name: [file_patterns]} — matches blueprint §5.2."""
    for agent_name, patterns in OWNERSHIP_MAP.items():
        if match_file_pattern(filepath, patterns):
            return agent_name
    return None


def check_file_ownership(filepath, agent_name):
    """Check if an agent is allowed to write to a file.
    Returns (allowed: bool, owner: str or None).

    C-2/H-5 FIX: "unknown" is NEVER allowed. Only the file owner
    or the orchestrator can write to owned files."""
    basename = os.path.basename(filepath)

    # SOT check first — only orchestrator
    if basename in SOT_FILES:
        allowed = agent_name in ALLOWED_SOT_WRITERS
        return allowed, "church-app-orchestrator"

    owner = get_file_owner(filepath)
    if owner is None:
        # Unowned file — anyone can write
        return True, None
    if owner == agent_name:
        return True, owner
    if agent_name in ALLOWED_SOT_WRITERS:
        # Orchestrator can write anywhere (it's the coordinator)
        return True, owner
    return False, owner


# =============================================================================
# H2-3: Deterministic Modification Classifier (Phase 5)
# Korean patterns for classifying user feedback during preview loop.
# =============================================================================

STYLE_PATTERNS = [
    r'색상|색깔|컬러|color|배경|background|글씨|폰트|font|크기|size|굵기|bold',
    r'간격|margin|padding|둥글|radius|그림자|shadow|투명|opacity',
    r'다크\s?모드|dark\s?mode|밝[게기]|어둡[게기]|테마|theme',
]

FEATURE_PATTERNS = [
    r'추가|넣어|만들어|기능|타이머|timer|버튼|button|페이지|page',
    r'실시간|websocket|알림|notification|소리|sound|효과음|effect',
    r'점수|score|랭킹|ranking|순위|팀|team|새로운|new',
]

ROLLBACK_PATTERNS = [
    r'아까|이전|전[에으]|돌려|되돌|롤백|rollback|원래|처음|복구|restore',
]


def classify_modification(user_text):
    """Deterministic Phase 5 modification classifier (H2-3).

    Returns: ("A", "style") | ("B", "feature") | ("C", "rollback") | ("?", "uncertain")
    AI should ONLY be consulted when result is ("?", "uncertain").
    This prevents: style change misclassified as feature (unnecessary QA re-run)
                   feature change misclassified as style (QA skip = quality risk)
    """
    text = user_text.lower()
    rollback_score = sum(1 for p in ROLLBACK_PATTERNS if re.search(p, text))
    feature_score = sum(1 for p in FEATURE_PATTERNS if re.search(p, text))
    style_score = sum(1 for p in STYLE_PATTERNS if re.search(p, text))

    if rollback_score > 0 and rollback_score >= feature_score:
        return ("C", "rollback")
    if feature_score > style_score:
        return ("B", "feature")
    if style_score > 0:
        return ("A", "style")
    return ("?", "uncertain")


# =============================================================================
# H2-4: Deterministic Completion Signal Detector (Phase 5)
# Korean patterns for detecting when user is satisfied with the app.
# =============================================================================

COMPLETION_SIGNALS = [
    r'완성', r'좋아요', r'이대로', r'시작해', r'끝', r'괜찮', r'오케이', r'ok',
    r'배포', r'deploy', r'이걸로', r'충분', r'만족', r'진행',
]

NEGATION_TRAILING = [
    r'인데', r'지만', r'근데', r'그런데', r'대신', r'말고',
    r'하지만', r'그래도', r'다만', r'대신에',
    r'바꿔', r'바꿔줘', r'수정', r'고쳐', r'변경',
]


def detect_completion_signal(user_text):
    """Deterministic Phase 5 completion signal detector (H2-4, A1-5 fix).

    Returns True ONLY if completion pattern found AND no negation trailing.
    CRITICAL: Even when True, orchestrator MUST ask explicit confirmation:
    "이대로 배포할까요? (네/아니요)" — prevents false-positive premature deployment.
    """
    text = user_text.lower().strip()
    has_signal = any(re.search(p, text) for p in COMPLETION_SIGNALS)
    if not has_signal:
        return False
    has_negation = any(re.search(p, text) for p in NEGATION_TRAILING)
    return not has_negation


# =============================================================================
# Bundle Size Calculation
# =============================================================================

EXCLUDE_DIRS = {'node_modules', '.git', 'tests', 'archives', 'results',
                'reports', 'pacs-logs', 'scripts', '__pycache__', '.claude'}
TARGET_KB = 300
HARD_LIMIT_KB = 500


def calculate_bundle_size(project_dir=None):
    """Calculate total project size excluding non-bundle directories.
    Returns (total_kb, file_count, over_target, over_hard_limit)."""
    root = project_dir or get_project_dir()
    total_bytes = 0
    file_count = 0

    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            try:
                total_bytes += os.path.getsize(os.path.join(dirpath, f))
                file_count += 1
            except OSError:
                pass

    total_kb = total_bytes / 1024
    return total_kb, file_count, total_kb > TARGET_KB, total_kb > HARD_LIMIT_KB


# =============================================================================
# CSS Hardcoded Color Detection (M-5 FIX: per-match, not per-line skip)
# =============================================================================

_HEX_COLOR_RE = re.compile(r'#[0-9A-Fa-f]{3,8}\b')
_VAR_DECL_RE = re.compile(r'--[\w-]+\s*:\s*#[0-9A-Fa-f]{3,8}')
_ROOT_BLOCK_RE = re.compile(r':root\s*\{[^}]*\}', re.DOTALL)


def detect_hardcoded_colors(css_content):
    """Detect hardcoded CSS colors not inside :root or CSS variable declarations.
    Returns list of (line_number, color_value, line_content) tuples.

    M-5 FIX: Checks per-match instead of skipping entire line when var(--) present."""
    violations = []
    root_blocks = _ROOT_BLOCK_RE.findall(css_content)

    for i, line in enumerate(css_content.split("\n"), 1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        # Skip CSS variable declarations (--name: #color)
        if _VAR_DECL_RE.search(line):
            continue
        # Skip lines inside :root blocks
        if any(stripped in block for block in root_blocks):
            continue

        # Find hex colors NOT preceded by var(
        for m in _HEX_COLOR_RE.finditer(line):
            start = m.start()
            preceding = line[:start]
            # Skip if this color is part of a var() expression
            if 'var(' in preceding and ')' not in preceding[preceding.rfind('var('):]:
                continue
            violations.append((i, m.group(), stripped))

    return violations


# =============================================================================
# SOT Snapshot Management
# =============================================================================

MAX_SNAPSHOTS = 10


def create_sot_snapshot(project_dir=None, max_keep=None):
    """Create timestamped snapshot of app-state.json.
    Keeps last max_keep snapshots, deletes older ones."""
    pdir = project_dir or get_project_dir()
    sot_path = os.path.join(pdir, "app-state.json")
    if not os.path.exists(sot_path):
        return None

    snapshot_dir = os.path.join(pdir, ".claude", "context-snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_path = os.path.join(snapshot_dir, f"app-state-{timestamp}.json")
    shutil.copy2(sot_path, snapshot_path)

    # Cleanup old snapshots
    keep = max_keep or MAX_SNAPSHOTS
    snapshots = sorted(
        [f for f in os.listdir(snapshot_dir)
         if f.startswith("app-state-") and f.endswith(".json")],
        reverse=True
    )
    for old in snapshots[keep:]:
        try:
            os.remove(os.path.join(snapshot_dir, old))
        except OSError:
            pass

    return snapshot_path


# =============================================================================
# Content Matrix Validation (C-4 FIX: matches workflow-coding.md 9 app types)
# =============================================================================

CONTENT_MATRIX = {
    "quiz": {
        "required_fields": {
            "intent.team_count": lambda v: isinstance(v, int) and v > 0,
            "intent.team_names": lambda v: isinstance(v, list) and len(v) > 0,
            "content.quiz_questions": lambda v: isinstance(v, list) and len(v) > 0,
            "intent.design_palette": lambda v: v in ("A", "B", "C"),
        }
    },
    "score": {
        "required_fields": {
            "intent.team_count": lambda v: isinstance(v, int) and v > 0,
            "intent.team_names": lambda v: isinstance(v, list) and len(v) > 0,
            "intent.team_colors": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "schedule": {
        "required_fields": {
            "content.schedule": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "lyrics": {
        "required_fields": {
            "content.lyrics": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "stamps": {
        "required_fields": {
            "content.missions": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "qt": {
        "required_fields": {
            "content.bible_passages": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
    "prayer": {
        "required_fields": {}  # minimal — just needs app_type set
    },
    "photo": {
        "required_fields": {}  # minimal — just needs app_type set
    },
    "combined": {
        "required_fields": {
            "intent.features": lambda v: isinstance(v, list) and len(v) > 0,
        }
    },
}


def validate_content_collection(sot_data, project_dir=None):
    """Validate that all required fields for the chosen app type are present in SOT.
    Returns (complete: bool, missing: list, app_type: str).

    Called by orchestrator at Phase 1→2 transition.
    C-4 FIX: uses 9 app types matching workflow-coding.md §9.5."""
    if not sot_data or not isinstance(sot_data, dict):
        return False, ["SOT not found or empty"], "unknown"

    app_type = sot_data.get("intent", {}).get("app_type", "")
    if not app_type:
        return False, ["intent.app_type not set"], "unknown"

    matrix = CONTENT_MATRIX.get(app_type)
    if matrix is None:
        return False, [f"Unknown app_type: {app_type}"], app_type

    missing = []
    for field_path, validator in matrix["required_fields"].items():
        # Traverse nested dict using dot notation
        keys = field_path.split(".")
        current = sot_data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                current = None
                break

        if current is None or not validator(current):
            missing.append(field_path)

    return len(missing) == 0, missing, app_type


# =============================================================================
# Translation Pair Validation (H-4 FIX: loads actual glossary files)
# =============================================================================

def _load_glossary_terms(project_dir=None):
    """Load glossary terms from glossary.yaml and church-app-glossary.yaml.
    Returns dict of {english_term: korean_term} or empty dict."""
    pdir = project_dir or get_project_dir()
    terms = {}

    for glossary_file in ["translations/glossary.yaml", "translations/church-app-glossary.yaml"]:
        glossary_path = os.path.join(pdir, glossary_file)
        if not os.path.exists(glossary_path):
            continue
        try:
            # Use yaml if available, otherwise simple key:value parsing
            try:
                import yaml
                with open(glossary_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    file_terms = data.get("terms", data)
                    if isinstance(file_terms, dict):
                        terms.update(file_terms)
            except ImportError:
                # Fallback: simple line-by-line parsing for key: value format
                with open(glossary_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('#') or ':' not in line:
                            continue
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            k, v = parts[0].strip(), parts[1].strip()
                            if k and v:
                                terms[k] = v
        except (IOError, OSError):
            pass

    return terms


def validate_translation_pair(en_path, ko_path, glossary_terms=None):
    """Validate Korean translation file against English original.
    Returns (valid: bool, errors: list).

    Checks per workflow-coding.md §7.3 validate_translation_pair.py:
    1. Section count match
    2. Code blocks NOT translated
    3. Glossary terms consistent
    4. No empty sections"""
    errors = []

    if not os.path.exists(en_path):
        return False, [f"English original not found: {en_path}"]
    if not os.path.exists(ko_path):
        return False, [f"Korean translation not found: {ko_path}"]

    with open(en_path, 'r', encoding='utf-8') as f:
        en_content = f.read()
    with open(ko_path, 'r', encoding='utf-8') as f:
        ko_content = f.read()

    # Check 1: Section count match
    en_sections = len(re.findall(r'^#+\s', en_content, re.MULTILINE))
    ko_sections = len(re.findall(r'^#+\s', ko_content, re.MULTILINE))
    if en_sections != ko_sections:
        errors.append(f"Section count mismatch: English={en_sections}, Korean={ko_sections}")

    # Check 2: Code blocks NOT translated (fenced code blocks must match)
    en_code_blocks = re.findall(r'```[\s\S]*?```', en_content)
    ko_code_blocks = re.findall(r'```[\s\S]*?```', ko_content)
    if len(en_code_blocks) != len(ko_code_blocks):
        errors.append(f"Code block count mismatch: English={len(en_code_blocks)}, Korean={len(ko_code_blocks)}")
    else:
        for idx, (en_block, ko_block) in enumerate(zip(en_code_blocks, ko_code_blocks)):
            if en_block != ko_block:
                errors.append(f"Code block {idx+1} was modified in translation")

    # Check 3: Glossary terms (H-4 FIX: load from actual files)
    if glossary_terms is None:
        glossary_terms = _load_glossary_terms()
    if glossary_terms:
        for en_term, ko_term in glossary_terms.items():
            if en_term.lower() in en_content.lower() and ko_term not in ko_content:
                errors.append(f"Glossary term '{en_term}' → '{ko_term}' not found in translation")

    # Check 4: No empty sections
    ko_lines = ko_content.split("\n")
    for idx, line in enumerate(ko_lines):
        if re.match(r'^#+\s', line):
            next_content = False
            for j in range(idx + 1, min(idx + 5, len(ko_lines))):
                if ko_lines[j].strip() and not re.match(r'^#+\s', ko_lines[j]):
                    next_content = True
                    break
            if not next_content:
                errors.append(f"Empty section at line {idx+1}: {line.strip()}")

    return len(errors) == 0, errors


# =============================================================================
# Agent Team Availability Detection (G1 FIX)
# =============================================================================

def agent_teams_available():
    """Check if Claude Code Agent Teams feature is available.

    Decision logic (per orchestrator.md §Phase 3):
      1. Check CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS env var
      2. If not set, Agent Team mode is unavailable → use sequential mode

    Returns True if Agent Teams can be used, False otherwise.
    Called by orchestrator in choose_execution_mode() to decide
    between sequential (default) and agent-team (combined 3+ features).
    """
    flag = os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "")
    return flag.lower() in ("1", "true", "yes", "enabled")


# =============================================================================
# Deterministic Error Pattern Extraction (H1 FIX — Hallucination Prevention)
# =============================================================================

def extract_phase_errors(sot_data, phase_num=None):
    """Extract failed quality gates and error patterns from SOT — DETERMINISTIC.

    Replaces AI-based error pattern "collection" with deterministic extraction.
    Same SOT input → same output, EVERY TIME. Zero AI judgment.

    Reads from:
      - quality.q_gates   → Q1-Q11 technical gate results
      - quality.d_gates   → D1-D9 design gate results
      - quality.app_specific_gates → app-type-specific gates
      - quality.verify_log → chronological verification history
      - quality.retry_count → total retry attempts
      - status.fallback_tier → current fallback level

    Returns dict:
      {
        "failed_gates": [{"id": "Q2", "detail": "..."}, ...],
        "passed_gates": ["Q1", "Q3", ...],
        "retry_count": int,
        "fallback_tier": int,
        "has_errors": bool,
        "summary": str   # one-line deterministic summary for sub-agent injection
      }
    """
    if not sot_data or not isinstance(sot_data, dict):
        return {
            "failed_gates": [], "passed_gates": [],
            "retry_count": 0, "fallback_tier": 1,
            "has_errors": False, "summary": "No SOT data available."
        }

    quality = sot_data.get("quality", {})
    status = sot_data.get("status", {})

    # Collect all gate results from SOT
    failed = []
    passed = []

    for gate_source_name in ("q_gates", "d_gates", "app_specific_gates"):
        gates = quality.get(gate_source_name, {})
        if isinstance(gates, dict):
            for gate_id, gate_result in gates.items():
                if isinstance(gate_result, dict):
                    gate_status = gate_result.get("status", "").upper()
                    if gate_status == "FAIL":
                        failed.append({
                            "id": gate_id,
                            "detail": gate_result.get("detail", ""),
                            "source": gate_source_name,
                        })
                    elif gate_status == "PASS":
                        passed.append(gate_id)
                elif isinstance(gate_result, str):
                    if gate_result.upper() == "FAIL":
                        failed.append({
                            "id": gate_id, "detail": "", "source": gate_source_name
                        })
                    elif gate_result.upper() == "PASS":
                        passed.append(gate_id)

    # Extract from verify_log (chronological entries)
    verify_log = quality.get("verify_log", [])
    if isinstance(verify_log, list):
        for entry in verify_log:
            if isinstance(entry, dict) and entry.get("status", "").upper() == "FAIL":
                gate_id = entry.get("gate_id", entry.get("id", "unknown"))
                # Avoid duplicates
                if not any(f["id"] == gate_id for f in failed):
                    failed.append({
                        "id": gate_id,
                        "detail": entry.get("detail", entry.get("message", "")),
                        "source": "verify_log",
                    })

    retry_count = quality.get("retry_count", 0)
    fallback_tier = status.get("fallback_tier", 1)
    has_errors = len(failed) > 0 or retry_count > 0

    # Build deterministic summary string
    if not has_errors:
        summary = "No errors detected. All gates passed."
    else:
        failed_ids = ", ".join(f["id"] for f in failed)
        details = "; ".join(
            f'{f["id"]}: {f["detail"]}' for f in failed if f["detail"]
        )
        summary = (
            f"Failed gates: [{failed_ids}]. "
            f"Retry count: {retry_count}. "
            f"Fallback tier: {fallback_tier}."
        )
        if details:
            summary += f" Details: {details}"

    return {
        "failed_gates": failed,
        "passed_gates": sorted(passed),
        "retry_count": retry_count,
        "fallback_tier": fallback_tier,
        "has_errors": has_errors,
        "summary": summary,
    }


# =============================================================================
# Deterministic Git Hash Extraction (H2 FIX — Hallucination Prevention)
# =============================================================================

def get_latest_git_hash(project_dir=None):
    """Get the latest git commit short hash — DETERMINISTIC.

    Replaces manual SOT last_git_checkpoint editing with deterministic extraction.
    Calls: git rev-parse --short HEAD

    Returns: short hash string (e.g., "5b2d984") or "" if git unavailable.
    """
    import subprocess
    pdir = project_dir or get_project_dir()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=pdir, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""
