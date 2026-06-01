"""Step 5 self-check — deterministic package integrity checks (PK1–PK13).

The integrated package succeeds when the core lesson plan is valid and every
supplementary artifact that ran is aligned to that plan. Checks are
deterministic (no LLM): integrity must be reproducible, not narrated.

A check has a ``severity``:
  - ``critical`` — a failure makes the package verdict FAIL.
  - ``warning``  — recorded, surfaced, but does not fail the package.
  - ``info``     — not applicable this run (e.g. a skipped supplementary step).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts.lesson_plan_contract import STEP_ID as LESSON_STEP_ID
from scripts.lesson_plan_contract import validate_lesson_plan

_STOPWORDS = {
    "강조", "지양", "그리고", "말씀", "오늘", "우리", "통해", "대한", "위해",
    "이번", "한", "수", "것", "때", "더",
}

SUPP_NAMES = ("teaching", "praise", "promo")


def _tokens(text: Any) -> set[str]:
    if not isinstance(text, str):
        return set()
    parts = re.split(r"[\s,.··…\"'`()\[\]{}!?~\-:;/]+", text)
    return {p for p in parts if len(p) >= 2 and p not in _STOPWORDS}


def _supp_key_message(pkg: dict[str, Any]) -> str:
    if not isinstance(pkg, dict):
        return ""
    # teaching → summary.key_message; praise/promo → inputs.key_message
    return (
        pkg.get("summary", {}).get("key_message")
        or pkg.get("inputs", {}).get("key_message")
        or ""
    )


def _passage_tokens(body_text: Any) -> set[str]:
    """Scripture-locating tokens from body_text: book name + chapter:verse markers."""
    tokens: set[str] = set()
    if not isinstance(body_text, str):
        return tokens
    book = re.match(r"\s*([가-힣]{2,})", body_text)
    if book:
        tokens.add(book.group(1))           # e.g. 누가복음
    tokens.update(re.findall(r"\d+:\d+", body_text))  # e.g. 8:26
    return tokens


def _supp_passage_text(pkg: dict[str, Any]) -> str:
    """Concatenate a supplementary package's passage-bearing fields."""
    if not isinstance(pkg, dict):
        return ""
    parts = [
        pkg.get("intake", {}).get("body_text", ""),
        pkg.get("inputs", {}).get("body_text", ""),
    ]
    worksheet = pkg.get("components", {}).get("worksheet", {})
    if isinstance(worksheet, dict):
        parts.append(str(worksheet.get("passage_reference", "")))
    song = pkg.get("song", {})
    if isinstance(song, dict):
        parts.append(str(song.get("scripture_anchor", "")))
    return " ".join(p for p in parts if p)


def _check(cid: str, title: str, severity: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"id": cid, "title": title, "severity": severity, "passed": passed, "detail": detail}


def run_self_check(
    intake: dict[str, Any],
    lesson_plan: dict[str, Any],
    ran: dict[str, bool],
    modules: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    """Return {verdict, checks, summary}.

    ``ran``     — {"teaching": bool, "praise": bool, "promo": bool}
    ``modules`` — {"teaching": <package dict|None>, ...} (the *package*, not the result envelope)
    """
    checks: list[dict[str, Any]] = []
    sections = lesson_plan.get("sections", {}) if isinstance(lesson_plan, dict) else {}

    # PK1 — core present
    core_present = isinstance(lesson_plan, dict) and lesson_plan.get("step_id") == LESSON_STEP_ID
    checks.append(_check(
        "PK1", "수업안(core) 존재", "critical", core_present,
        "lesson_plan present with correct step_id" if core_present
        else "lesson_plan missing or wrong step_id",
    ))

    # PK2 — core valid (LP1–LP10)
    lp_errors = validate_lesson_plan(lesson_plan) if isinstance(lesson_plan, dict) else ["no plan"]
    checks.append(_check(
        "PK2", "수업안 LP1–LP10 통과", "critical", not lp_errors,
        "lesson plan valid" if not lp_errors else f"{len(lp_errors)} LP violation(s): {lp_errors}",
    ))

    # PK3 — emphasis reflected in key_message or application
    emphasis_tokens = _tokens(intake.get("emphasis") or intake.get("theme"))
    reflected_text = f"{sections.get('key_message', '')} {sections.get('application', '')}"
    reflected = (not emphasis_tokens) or bool(emphasis_tokens & _tokens(reflected_text))
    checks.append(_check(
        "PK3", "강조점이 핵심메시지/적용에 반영", "warning", reflected,
        "emphasis reflected" if reflected
        else f"emphasis tokens {sorted(emphasis_tokens)} absent from key_message/application",
    ))

    any_supp = any(isinstance(modules.get(n), dict) for n in SUPP_NAMES)

    # PK4 — supplementary guard: no supplementary without a valid core
    guard_ok = (not any_supp) or (core_present and not lp_errors)
    checks.append(_check(
        "PK4", "부가물은 유효한 수업안 위에서만 생성", "critical", guard_ok,
        "ok" if guard_ok else "supplementary artifacts exist but core lesson plan is invalid",
    ))

    plan_km_tokens = _tokens(sections.get("key_message"))

    # PK5 — teaching consumed the real plan (mode step1, not intake_only)
    teaching = modules.get("teaching")
    if ran.get("teaching") and isinstance(teaching, dict):
        mode = teaching.get("lesson_plan_ref", {}).get("mode")
        passed = mode == "step1"
        checks.append(_check(
            "PK5", "교보재가 수업안을 입력으로 소비", "warning", passed,
            f"lesson_plan_ref.mode={mode!r}" if mode
            else "teaching did not record lesson_plan_ref (intake-only fallback?)",
        ))
    else:
        checks.append(_check("PK5", "교보재가 수업안을 입력으로 소비", "info", True, "teaching not run"))

    # PK6 — teaching components complete
    if ran.get("teaching") and isinstance(teaching, dict):
        comps = teaching.get("components", {})
        missing = [k for k in ("intro_game", "discussion", "activity", "worksheet") if k not in comps]
        checks.append(_check(
            "PK6", "교보재 4종 구성요소 완비", "critical", not missing,
            "all present" if not missing else f"missing: {missing}",
        ))
    else:
        checks.append(_check("PK6", "교보재 4종 구성요소 완비", "info", True, "teaching not run"))

    # PK7 — praise has key_message + lyrics
    praise = modules.get("praise")
    if ran.get("praise") and isinstance(praise, dict):
        has_km = bool(_supp_key_message(praise))
        has_lyrics = bool(praise.get("song", {}).get("lyrics"))
        passed = has_km and has_lyrics
        checks.append(_check(
            "PK7", "찬양 가사/핵심메시지 존재", "critical", passed,
            "ok" if passed else f"key_message={has_km}, lyrics={has_lyrics}",
        ))
    else:
        checks.append(_check("PK7", "찬양 가사/핵심메시지 존재", "info", True, "praise not run"))

    # PK8 — promo has key_message + narration script
    promo = modules.get("promo")
    if ran.get("promo") and isinstance(promo, dict):
        has_km = bool(_supp_key_message(promo))
        has_script = bool(promo.get("narration", {}).get("full_script"))
        passed = has_km and has_script
        checks.append(_check(
            "PK8", "홍보영상 대본/핵심메시지 존재", "critical", passed,
            "ok" if passed else f"key_message={has_km}, narration={has_script}",
        ))
    else:
        checks.append(_check("PK8", "홍보영상 대본/핵심메시지 존재", "info", True, "promo not run"))

    # PK9 — run/skip consistency: flag True ⇔ package present
    mismatches = [
        n for n in SUPP_NAMES
        if bool(ran.get(n)) != isinstance(modules.get(n), dict)
    ]
    checks.append(_check(
        "PK9", "실행/스킵 상태와 산출물 일치", "critical", not mismatches,
        "consistent" if not mismatches else f"mismatch on: {mismatches}",
    ))

    # PK10 — supplementary key_message overlaps plan key_message
    if plan_km_tokens:
        drifted = []
        for n in SUPP_NAMES:
            pkg = modules.get(n)
            if ran.get(n) and isinstance(pkg, dict):
                if not (_tokens(_supp_key_message(pkg)) & plan_km_tokens):
                    drifted.append(n)
        checks.append(_check(
            "PK10", "부가물 핵심메시지가 수업안과 정합", "warning", not drifted,
            "aligned" if not drifted else f"no shared key terms with plan: {drifted}",
        ))
    else:
        checks.append(_check("PK10", "부가물 핵심메시지가 수업안과 정합", "info", True, "no plan key_message"))

    # PK11 — audience consistency
    base_aud = (intake.get("audience") or "").strip()
    aud_mismatch = []
    for n in SUPP_NAMES:
        pkg = modules.get(n)
        if ran.get(n) and isinstance(pkg, dict):
            aud = (pkg.get("intake", {}).get("audience") or pkg.get("inputs", {}).get("audience") or "").strip()
            if base_aud and aud and aud != base_aud:
                aud_mismatch.append(f"{n}:{aud}")
    checks.append(_check(
        "PK11", "대상(audience) 일관성", "warning", not aud_mismatch,
        f"audience={base_aud!r}" if not aud_mismatch else f"differs → {aud_mismatch}",
    ))

    # PK12 — no module reported an error/fallback status
    errored = []
    for n in SUPP_NAMES:
        pkg = modules.get(n)
        if ran.get(n) and isinstance(pkg, dict):
            gen = pkg.get("meta", {}).get("generated_by", "")
            if "error" in gen:
                errored.append(f"{n}:{gen}")
    checks.append(_check(
        "PK12", "부가물 생성 오류 없음", "critical", not errored,
        "ok" if not errored else f"errors: {errored}",
    ))

    # PK13 — supplementary references the lesson's actual body passage
    body_tokens = _passage_tokens(intake.get("body_text"))
    if body_tokens:
        off_passage = []
        for n in SUPP_NAMES:
            pkg = modules.get(n)
            if ran.get(n) and isinstance(pkg, dict):
                txt = _supp_passage_text(pkg)
                if not any(tok in txt for tok in body_tokens):
                    off_passage.append(n)
        checks.append(_check(
            "PK13", "부가물이 본문 구절을 참조", "warning", not off_passage,
            f"passage tokens {sorted(body_tokens)} referenced" if not off_passage
            else f"no reference to body passage in: {off_passage}",
        ))
    else:
        checks.append(_check(
            "PK13", "부가물이 본문 구절을 참조", "info", True,
            "body_text has no locatable passage reference",
        ))

    critical_fail = [c for c in checks if c["severity"] == "critical" and not c["passed"]]
    warnings = [c for c in checks if c["severity"] == "warning" and not c["passed"]]
    verdict = "PASS" if not critical_fail else "FAIL"

    return {
        "verdict": verdict,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "critical_failures": len(critical_fail),
            "warnings": len(warnings),
            "passed": sum(1 for c in checks if c["passed"]),
        },
    }


def render_report(result: dict[str, Any], intake: dict[str, Any]) -> str:
    s = result["summary"]
    icon = {"critical": "🔴", "warning": "🟡", "info": "⚪"}
    lines = [
        "# 자기검수 보고서 (Self-Check Report)",
        "",
        f"- **판정(Verdict)**: **{result['verdict']}**",
        f"- 대상: {intake.get('audience', '')} · 분량: {intake.get('volume', '')}분 · 강조점: {intake.get('emphasis', '')}",
        f"- 검사 {s['total']}건 · 통과 {s['passed']} · 치명 실패 {s['critical_failures']} · 경고 {s['warnings']}",
        "",
        "| ID | 검사 | 심각도 | 결과 | 비고 |",
        "|----|------|--------|------|------|",
    ]
    for c in result["checks"]:
        status = "PASS" if c["passed"] else ("N/A" if c["severity"] == "info" else "FAIL")
        lines.append(
            f"| {c['id']} | {c['title']} | {icon.get(c['severity'], '')}{c['severity']} | {status} | {c['detail']} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


# --- Disk loaders (used by the standalone P1 CLI) --------------------------

def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def load_from_disk(outputs_dir: Path) -> dict[str, Any]:
    """Reconstruct (intake, lesson_plan, ran, modules) from an outputs/ tree."""
    intake = _load_json(outputs_dir / "intake" / "lesson_intake.json") or {}
    lesson_plan = _load_json(outputs_dir / "lesson_plan" / "lesson_plan.json") or {}
    modules = {
        "teaching": _load_json(outputs_dir / "teaching" / "teaching_materials.v1.json"),
        "praise": _load_json(outputs_dir / "praise" / "praise_worship.v1.json"),
        "promo": _load_json(outputs_dir / "promo" / "promo_video.v1.json"),
    }
    ran = {n: isinstance(modules.get(n), dict) for n in SUPP_NAMES}
    return {"intake": intake, "lesson_plan": lesson_plan, "ran": ran, "modules": modules}
