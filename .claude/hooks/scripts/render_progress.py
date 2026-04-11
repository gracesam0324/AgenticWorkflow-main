#!/usr/bin/env python3
"""
render_progress.py — 워크플로우 진행 상황 인라인 표시

Stop hook 또는 PostToolUse hook에서 호출되어,
SOT 파일의 상태 변화가 감지되면 진행 상황을 stderr로 출력한다.
Claude Code는 stderr 출력을 사용자에게 보여주므로,
이를 통해 워크플로우 진행률을 자연스럽게 표시한다.

Usage:
    python3 render_progress.py [--project-dir .]

트리거 조건: SOT의 current_step이 이전 호출 대비 변경된 경우에만 출력.
변경이 없으면 아무것도 출력하지 않는다 (노이즈 방지).
"""

import json
import os
import sys
import tempfile

# detect_projects.py의 함수를 재사용
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

try:
    from detect_projects import (
        detect_all,
        render_progress_bar,
        render_status_badge,
        _find_project_dir,
    )
except ImportError:
    # detect_projects를 import할 수 없으면 조용히 종료
    sys.exit(0)


def _get_cache_path(project_dir):
    """진행 상태 캐시 파일 경로."""
    cache_dir = os.path.join(project_dir, ".claude", "context-snapshots")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, ".progress-cache.json")


def _load_cache(cache_path):
    """이전 진행 상태 로드."""
    if not os.path.isfile(cache_path):
        return {}
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache_path, data):
    """현재 진행 상태 저장 (atomic write)."""
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(cache_path), suffix=".tmp"
        )
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        # Windows: 대상 파일이 존재하면 먼저 삭제
        if os.path.exists(cache_path):
            os.remove(cache_path)
        os.rename(tmp_path, cache_path)
    except Exception:
        pass


def _extract_current_state(state):
    """현재 활성 프로젝트의 step/phase 정보 추출."""
    result = {}

    ca = state.get("church_app", {})
    if ca.get("found"):
        result["church_app_step"] = ca.get("current_step", 0)
        result["church_app_phase"] = ca.get("current_phase", "")
        result["church_app_pct"] = ca.get("progress_pct", 0)

    ab = state.get("autobiography", {})
    if ab.get("found"):
        result["autobiography_step"] = ab.get("current_step", 0)
        result["autobiography_name"] = ab.get("step_name", "")
        result["autobiography_pct"] = ab.get("progress_pct", 0)

    wf = state.get("workflow", {})
    if wf.get("found"):
        result["workflow_step"] = wf.get("current_step", 0)
        result["workflow_name"] = wf.get("name", "")
        result["workflow_status"] = wf.get("status", "")

    return result


def _render_inline_progress(state, changes):
    """변경된 프로젝트의 인라인 진행률 렌더링."""
    lines = []

    ca = state.get("church_app", {})
    if ca.get("found") and "church_app_step" in changes:
        pct = ca.get("progress_pct", 0)
        phase = ca.get("current_phase", "?")
        bar = render_progress_bar(pct, width=15)
        lines.append(f"--- 수련회 앱  {bar}  Phase {phase} ---")

    ab = state.get("autobiography", {})
    if ab.get("found") and "autobiography_step" in changes:
        pct = ab.get("progress_pct", 0)
        step_name = ab.get("step_name", "?")
        step_num = ab.get("current_step", 0)
        bar = render_progress_bar(pct, width=15)
        lines.append(f"--- 자서전  {bar}  Step {step_num}: {step_name} ---")

    wf = state.get("workflow", {})
    if wf.get("found") and "workflow_step" in changes:
        step = wf.get("current_step", 0)
        name = wf.get("name", "workflow")
        status = wf.get("status", "")
        lines.append(f"--- {name}  Step {step}  {status} ---")

    return "\n".join(lines)


def main():
    try:
        project_dir = _find_project_dir()
        state = detect_all(project_dir)
        current = _extract_current_state(state)

        cache_path = _get_cache_path(project_dir)
        previous = _load_cache(cache_path)

        # 변경 감지
        changes = {}
        for key, val in current.items():
            if previous.get(key) != val:
                changes[key] = val

        # 변경이 있으면 인라인 진행률 출력 (stderr로)
        if changes:
            output = _render_inline_progress(state, changes)
            if output:
                print(output, file=sys.stderr)

        # 캐시 업데이트
        _save_cache(cache_path, current)

    except Exception:
        # 안전 원칙: 어떤 오류든 Claude를 차단하지 않는다
        pass


if __name__ == "__main__":
    main()
