#!/usr/bin/env python3
"""
detect_projects.py — 활성 프로젝트 감지 및 상태 요약 출력

/start, /status 커맨드에서 호출하여 현재 프로젝트 상태를 파악한다.
출력: JSON 형식의 프로젝트 상태 (stdout)

Usage:
    python3 detect_projects.py [--project-dir .]
"""

import json
import os
import sys
import glob

def _find_project_dir():
    """프로젝트 루트 디렉터리 탐색."""
    for arg in sys.argv[1:]:
        if arg.startswith("--project-dir="):
            return arg.split("=", 1)[1]
    # CLAUDE_PROJECT_DIR 환경변수 → 현재 디렉터리 순으로 탐색
    return os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def _read_yaml_safe(path):
    """PyYAML 없이도 동작하는 최소 YAML 파서 (key: value 수준)."""
    result = {}
    if not os.path.isfile(path):
        return result
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        pass
    # fallback: 단순 파싱
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if v:
                        result[k] = v
    except Exception:
        pass
    return result


def _read_json_safe(path):
    """JSON 파일 안전 읽기."""
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _detect_church_app(project_dir):
    """수련회 앱 프로젝트 감지."""
    # app-state.json 탐색 (프로젝트 루트 및 하위)
    candidates = [
        os.path.join(project_dir, "app-state.json"),
    ]
    # 하위 디렉터리에서도 탐색
    for g in glob.glob(os.path.join(project_dir, "*", "app-state.json")):
        candidates.append(g)

    for path in candidates:
        data = _read_json_safe(path)
        if data:
            status_info = data.get("status", {})
            workflow = data.get("workflow", {})
            intent = data.get("intent", {})
            current_phase = workflow.get("current_phase", "unknown")
            current_step = workflow.get("current_step", 0)
            app_type = intent.get("app_type", "unknown")
            app_name = intent.get("app_name", "")
            total_phases = 7  # P0-P6

            return {
                "found": True,
                "sot_path": path,
                "app_type": app_type,
                "app_name": app_name,
                "current_phase": current_phase,
                "current_step": current_step,
                "total_phases": total_phases,
                "progress_pct": min(100, int((current_step / max(total_phases, 1)) * 100)),
                "status": status_info.get("overall", "unknown"),
            }

    return {"found": False}


def _detect_autobiography(project_dir):
    """자서전 프로젝트 감지."""
    path = os.path.join(project_dir, "autobiography-generator", "state.yaml")
    data = _read_yaml_safe(path)
    if not data:
        return {"found": False}

    workflow = data.get("workflow", data)
    current_step = 0
    total_steps = 12  # Steps 0-11
    status = "unknown"

    # current_step 추출 (중첩 또는 플랫 구조 모두 대응)
    if isinstance(workflow, dict):
        cs = workflow.get("current_step", data.get("current_step", 0))
        try:
            current_step = int(cs)
        except (ValueError, TypeError):
            current_step = 0
        status = workflow.get("status", data.get("status", "unknown"))

    step_names = {
        0: "환경 설정", 1: "인터뷰 준비", 2: "인터뷰 진행",
        3: "자료 평가", 4: "내러티브 아키텍처", 5: "보이스 캘리브레이션",
        6: "아웃라인 생성", 7: "챕터 집필", 8: "일관성 검토",
        9: "PDF/EPUB 빌드", 10: "최종 검토", 11: "출판",
    }

    return {
        "found": True,
        "sot_path": path,
        "current_step": current_step,
        "total_steps": total_steps,
        "step_name": step_names.get(current_step, f"Step {current_step}"),
        "progress_pct": min(100, int((current_step / max(total_steps, 1)) * 100)),
        "status": str(status),
    }


def _detect_workflow(project_dir):
    """일반 워크플로우 프로젝트 감지."""
    # state.yaml (프로젝트 루트)
    path = os.path.join(project_dir, "state.yaml")
    data = _read_yaml_safe(path)
    if not data:
        return {"found": False}

    workflow = data.get("workflow", data)
    if isinstance(workflow, dict):
        name = workflow.get("name", "unknown")
        current_step = workflow.get("current_step", 0)
        status = workflow.get("status", "unknown")
        try:
            current_step = int(current_step)
        except (ValueError, TypeError):
            current_step = 0
        return {
            "found": True,
            "sot_path": path,
            "name": name,
            "current_step": current_step,
            "status": str(status),
        }

    return {"found": False}


def _detect_skills(project_dir):
    """사용 가능한 스킬 목록."""
    skills_dir = os.path.join(project_dir, ".claude", "skills")
    available = []
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            skill_md = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.isfile(skill_md):
                available.append(entry)
    return available


def detect_all(project_dir):
    """모든 프로젝트 상태를 감지하여 통합 결과 반환."""
    return {
        "project_dir": project_dir,
        "church_app": _detect_church_app(project_dir),
        "autobiography": _detect_autobiography(project_dir),
        "workflow": _detect_workflow(project_dir),
        "available_skills": _detect_skills(project_dir),
    }


def render_progress_bar(pct, width=20):
    """ASCII 진행률 바 생성."""
    filled = int(width * pct / 100)
    empty = width - filled
    bar = "\u2588" * filled + "\u2591" * empty
    return f"{bar} {pct}%"


def render_status_badge(status):
    """상태 뱃지 텍스트."""
    mapping = {
        "running": "[진행 중]",
        "in_progress": "[진행 중]",
        "paused": "[일시정지]",
        "completed": "[완료]",
        "error": "[오류]",
    }
    return mapping.get(str(status).lower(), "")


def render_start_menu(state):
    """제품 실행 모드 메뉴를 마크다운 형식으로 렌더링."""
    lines = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("```")
    lines.append("\u2501" * 50)
    lines.append("   AgenticWorkflow \u2014 \uc81c\ud488 \uc2e4\ud589 \ubaa8\ub4dc")
    lines.append("\u2501" * 50)
    lines.append("")
    lines.append("   \ub300\ud654\ub9cc\uc73c\ub85c \uc644\uc131\ud558\ub294 AI \uc6cc\ud06c\ud50c\ub85c\uc6b0 \uc2dc\uc2a4\ud15c\uc785\ub2c8\ub2e4.")
    lines.append("   \uc544\ub798\uc5d0\uc11c \uc2e4\ud589\ud560 \ubaa8\ub4dc\ub97c \uc120\ud0dd\ud558\uc138\uc694.")
    lines.append("")
    lines.append("\u2501" * 50)
    lines.append("```")
    lines.append("")

    # 1. 수련회 앱
    ca = state["church_app"]
    badge_ca = ""
    detail_ca = ""
    if ca["found"]:
        badge_ca = " " + render_status_badge(ca.get("status", ""))
        detail_ca = f"\n     {render_progress_bar(ca['progress_pct'])}  Phase {ca.get('current_phase', '?')}"

    # 2. 자서전
    ab = state["autobiography"]
    badge_ab = ""
    detail_ab = ""
    if ab["found"] and ab.get("current_step", 0) > 0:
        badge_ab = " " + render_status_badge(ab.get("status", ""))
        detail_ab = f"\n     {render_progress_bar(ab['progress_pct'])}  {ab.get('step_name', '?')}"

    menu = f"""
**1.  수련회 앱 만들기{badge_ca}**
     교회 수련회용 모바일 웹앱을 대화로 제작
     HTML/JS \u2192 GitHub Pages 배포{detail_ca}

**2.  자서전 쓰기{badge_ab}**
     AI 인터뷰 → 내러티브 설계 → 자동 집필
     PDF/EPUB 출판{detail_ab}

**3.  워크플로우 설계**
     복잡한 작업을 자동화 워크플로우로 설계
     workflow.md 생성

**4.  학술 글쓰기**
     박사급 논문 문체의 학술적 글쓰기 지원
     한국어 \u00b7 영어 모두 지원
"""
    lines.append(menu)

    lines.append("---")
    lines.append("")
    lines.append("> 번호를 입력하거나, 하고 싶은 것을 자유롭게 말씀하세요.")
    lines.append('> 예: "1", "수련회 앱", "자서전을 쓰고 싶어요"')
    lines.append("")

    return "\n".join(lines)


def render_status_dashboard(state):
    """범용 상태 대시보드를 마크다운 형식으로 렌더링."""
    lines = []
    lines.append("")
    lines.append("```")
    lines.append("\u2501" * 50)
    lines.append("   AgenticWorkflow \u2014 \ud504\ub85c\uc81d\ud2b8 \uc0c1\ud0dc")
    lines.append("\u2501" * 50)
    lines.append("```")
    lines.append("")

    has_any = False

    # 수련회 앱
    ca = state["church_app"]
    if ca["found"]:
        has_any = True
        lines.append(f"### \uc218\ub828\ud68c \uc571  {render_status_badge(ca.get('status', ''))}")
        lines.append("")
        lines.append(f"| \ud56d\ubaa9 | \uac12 |")
        lines.append(f"|------|-----|")
        lines.append(f"| \uc571 \uc720\ud615 | {ca.get('app_type', '-')} |")
        if ca.get("app_name"):
            lines.append(f"| \uc571 \uc774\ub984 | {ca['app_name']} |")
        lines.append(f"| \ud604\uc7ac Phase | {ca.get('current_phase', '-')} |")
        lines.append(f"| \uc9c4\ud589\ub960 | {render_progress_bar(ca['progress_pct'])} |")
        lines.append(f"| SOT | `{ca['sot_path']}` |")
        lines.append("")

    # 자서전
    ab = state["autobiography"]
    if ab["found"]:
        has_any = True
        lines.append(f"### \uc790\uc11c\uc804  {render_status_badge(ab.get('status', ''))}")
        lines.append("")
        lines.append(f"| \ud56d\ubaa9 | \uac12 |")
        lines.append(f"|------|-----|")
        lines.append(f"| \ud604\uc7ac \ub2e8\uacc4 | Step {ab.get('current_step', 0)}: {ab.get('step_name', '-')} |")
        lines.append(f"| \uc9c4\ud589\ub960 | {render_progress_bar(ab['progress_pct'])} |")
        lines.append(f"| SOT | `{ab['sot_path']}` |")
        lines.append("")

    # 일반 워크플로우
    wf = state["workflow"]
    if wf["found"]:
        has_any = True
        lines.append(f"### \uc6cc\ud06c\ud50c\ub85c\uc6b0: {wf.get('name', 'unknown')}  {render_status_badge(wf.get('status', ''))}")
        lines.append("")
        lines.append(f"| \ud56d\ubaa9 | \uac12 |")
        lines.append(f"|------|-----|")
        lines.append(f"| \ud604\uc7ac Step | {wf.get('current_step', 0)} |")
        lines.append(f"| \uc0c1\ud0dc | {wf.get('status', '-')} |")
        lines.append(f"| SOT | `{wf['sot_path']}` |")
        lines.append("")

    if not has_any:
        lines.append("*\ud65c\uc131 \ud504\ub85c\uc81d\ud2b8\uac00 \uc5c6\uc2b5\ub2c8\ub2e4. `/start`\ub85c \uc0c8 \ud504\ub85c\uc81d\ud2b8\ub97c \uc2dc\uc791\ud558\uc138\uc694.*")
        lines.append("")

    # 사용 가능한 스킬
    skills = state.get("available_skills", [])
    if skills:
        lines.append("### \uc0ac\uc6a9 \uac00\ub2a5\ud55c \uc2a4\ud0ac")
        lines.append("")
        skill_names = {
            "workflow-generator": "\uc6cc\ud06c\ud50c\ub85c\uc6b0 \uc124\uacc4",
            "doctoral-writing": "\ud559\uc220 \uae00\uc4f0\uae30",
            "autobiography": "\uc790\uc11c\uc804 \uc4f0\uae30",
            "church-retreat-app": "\uc218\ub828\ud68c \uc571 \ub9cc\ub4e4\uae30",
        }
        for s in skills:
            name = skill_names.get(s, s)
            lines.append(f"- **{name}** (`{s}`)")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    project_dir = _find_project_dir()
    state = detect_all(project_dir)

    # --render 옵션으로 포맷 선택
    if "--render=menu" in sys.argv:
        print(render_start_menu(state))
    elif "--render=dashboard" in sys.argv:
        print(render_status_dashboard(state))
    else:
        print(json.dumps(state, indent=2, ensure_ascii=False))
