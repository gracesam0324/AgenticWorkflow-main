#!/usr/bin/env python3
"""init_project.py — Deterministic project initialization for autobiography workflow.

Creates an isolated project directory, manages symlinks, and archives previous projects.
All operations are deterministic — zero AI calls, zero network calls.

This script follows the P1 (Hallucination Prevention) pattern:
  - Every file system operation is explicit and verified
  - Symlink replacement is atomic (os.symlink + os.rename)
  - Migration verifies file counts before deleting originals
  - All results reported via structured JSON to stdout

Usage:
  # New project (no existing data)
  python3 scripts/init_project.py --subject-name "홍길동" --project-dir .

  # First-time setup: migrate existing outputs/ real directory
  python3 scripts/init_project.py --subject-name "최윤식" --project-dir . --migrate-existing

  # Custom date (for testing)
  python3 scripts/init_project.py --subject-name "홍길동" --project-dir . --date 20260401

Exit codes:
  0 — success (JSON result to stdout)
  1 — failure (error details to stderr)

Output (JSON to stdout):
  {
    "project_id": "20260318-홍길동",
    "project_dir": "projects/20260318-홍길동",
    "abs_project_dir": "/full/path/to/projects/20260318-홍길동",
    "created_dirs": [...],
    "symlinks": {"outputs": "projects/.../outputs", "review-logs": "projects/.../review-logs"},
    "archived_previous": {...} | null,
    "migrated": false,
    "migration_file_count": 0
  }

100% deterministic. Zero AI calls. Zero network calls.
"""

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime


# ─── Constants ───────────────────────────────────────────────────────────────

PROJECTS_SUBDIR = "projects"

# Required subdirectories inside each project's outputs/
REQUIRED_OUTPUT_SUBDIRS = [
    "interviews",
    "story-blueprint",
    "story-bible",
    "style-selection",
    "chapters",
    "chapters-ko",
    "builds",
    "eval-reports",
    "comparisons",
]

# Symlinks to create (relative to project-dir root)
# key = symlink name, value = target subpath inside project directory
SYMLINK_MAP = {
    "outputs": "outputs",
    "review-logs": "review-logs",
}

# Root-level directories to archive from previous project
ROOT_ARCHIVE_DIRS = [
    "autopilot-logs",
    "verification-logs",
    "pacs-logs",
]

# SOT path (relative to project-dir's parent, i.e., repo root)
SOT_RELATIVE = os.path.join(".claude", "state.yaml")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _sanitize_name(name: str) -> str:
    """Sanitize subject name for use in directory names.

    Preserves Korean characters, alphanumeric, and hyphens.
    Collapses whitespace to hyphens. Strips leading/trailing hyphens.
    """
    # Replace whitespace with hyphens
    sanitized = re.sub(r"\s+", "-", name.strip())
    # Keep only word chars (includes Korean via Unicode), hyphens
    sanitized = re.sub(r"[^\w가-힣-]", "", sanitized)
    # Collapse multiple hyphens
    sanitized = re.sub(r"-{2,}", "-", sanitized)
    # Strip leading/trailing hyphens
    sanitized = sanitized.strip("-")
    return sanitized


def _generate_project_id(subject_name: str, date_str: str | None = None) -> str:
    """Generate project ID: YYYYMMDD-sanitized_name."""
    date_part = date_str or datetime.now().strftime("%Y%m%d")
    name_part = _sanitize_name(subject_name)
    if not name_part:
        name_part = "unnamed"
    return f"{date_part}-{name_part}"


def _resolve_duplicate(projects_dir: str, project_id: str) -> str:
    """If project_id already exists, append -2, -3, etc."""
    candidate = project_id
    suffix = 2
    while os.path.exists(os.path.join(projects_dir, candidate)):
        candidate = f"{project_id}-{suffix}"
        suffix += 1
    return candidate


def _count_files(directory: str) -> int:
    """Count all files (not dirs) recursively in a directory."""
    count = 0
    for _, _, files in os.walk(directory):
        count += len(files)
    return count


def _is_symlink(path: str) -> bool:
    """Check if path is a symlink (not a real directory)."""
    return os.path.islink(path)


def _read_symlink_target(path: str) -> str | None:
    """Read symlink target. Returns None if not a symlink."""
    if not os.path.islink(path):
        return None
    return os.readlink(path)


def _detect_previous_project(project_dir: str) -> dict | None:
    """Detect if there's a previous project (via symlink targets).

    Returns:
        dict with previous project info, or None if no previous project.
    """
    outputs_path = os.path.join(project_dir, "outputs")

    if _is_symlink(outputs_path):
        target = _read_symlink_target(outputs_path)
        # Extract project ID from target path: "projects/{id}/outputs" → "{id}"
        if target and target.startswith(PROJECTS_SUBDIR + os.sep):
            parts = target.split(os.sep)
            if len(parts) >= 2:
                return {
                    "project_id": parts[1],
                    "project_dir": os.path.join(PROJECTS_SUBDIR, parts[1]),
                    "source": "symlink",
                }
    elif os.path.isdir(outputs_path):
        return {
            "project_id": None,  # Unknown — legacy flat structure
            "project_dir": None,
            "source": "real_directory",
        }

    return None


# ─── Core Operations ─────────────────────────────────────────────────────────

def archive_previous_project(
    project_dir: str,
    repo_root: str,
    previous_info: dict,
    new_project_id: str,
) -> dict:
    """Archive previous project's state and root-level logs.

    Returns archive report dict.
    """
    report = {
        "archived": False,
        "state_snapshot": None,
        "root_logs_copied": {},
    }

    # Determine archive target directory
    if previous_info["source"] == "symlink" and previous_info["project_id"]:
        archive_dir = os.path.join(
            project_dir, PROJECTS_SUBDIR, previous_info["project_id"]
        )
    else:
        # Legacy flat structure — archive under a generated ID
        archive_id = f"legacy-pre-{new_project_id}"
        archive_dir = os.path.join(project_dir, PROJECTS_SUBDIR, archive_id)
        report["legacy_archive_id"] = archive_id

    os.makedirs(archive_dir, exist_ok=True)

    # 1. Archive state.yaml snapshot
    sot_path = os.path.join(repo_root, SOT_RELATIVE)
    if os.path.isfile(sot_path):
        snapshot_dest = os.path.join(archive_dir, "state-snapshot.yaml")
        if not os.path.exists(snapshot_dest):  # Don't overwrite existing snapshot
            shutil.copy2(sot_path, snapshot_dest)
            report["state_snapshot"] = snapshot_dest
            report["archived"] = True

    # 2. Archive root-level log directories
    for log_dir_name in ROOT_ARCHIVE_DIRS:
        src = os.path.join(repo_root, log_dir_name)
        if os.path.isdir(src) and os.listdir(src):  # Non-empty
            dest = os.path.join(archive_dir, log_dir_name)
            if not os.path.exists(dest):
                shutil.copytree(src, dest)
                src_count = _count_files(src)
                dest_count = _count_files(dest)
                if src_count == dest_count:
                    report["root_logs_copied"][log_dir_name] = src_count
                    report["archived"] = True
                else:
                    print(
                        f"WARNING: File count mismatch for {log_dir_name}: "
                        f"src={src_count}, dest={dest_count}",
                        file=sys.stderr,
                    )

    return report


def migrate_existing_directory(
    project_dir: str,
    project_id: str,
) -> dict:
    """Migrate existing real outputs/ directory to projects/{id}/outputs/.

    Returns migration report.
    """
    report = {
        "migrated": False,
        "outputs_file_count": 0,
        "review_logs_file_count": 0,
    }

    project_path = os.path.join(project_dir, PROJECTS_SUBDIR, project_id)
    os.makedirs(project_path, exist_ok=True)

    for dir_name in SYMLINK_MAP:
        src = os.path.join(project_dir, dir_name)

        if not os.path.isdir(src) or _is_symlink(src):
            continue  # Skip if doesn't exist or is already a symlink

        dest = os.path.join(project_path, dir_name)

        if os.path.exists(dest):
            print(
                f"WARNING: Migration target already exists: {dest}. Skipping.",
                file=sys.stderr,
            )
            continue

        # Step 1: Copy (preserve original until verified)
        shutil.copytree(src, dest)

        # Step 2: Verify file counts match
        src_count = _count_files(src)
        dest_count = _count_files(dest)

        if src_count != dest_count:
            # Rollback: remove incomplete copy
            shutil.rmtree(dest)
            print(
                f"ERROR: Migration file count mismatch for {dir_name}: "
                f"src={src_count}, dest={dest_count}. Rolled back.",
                file=sys.stderr,
            )
            return {"migrated": False, "error": f"File count mismatch for {dir_name}"}

        # Step 3: Rename original as backup (NOT delete — safety first)
        backup_path = src + ".pre-migration"
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)  # Remove old backup if re-migrating
        os.rename(src, backup_path)

        report[f"{dir_name.replace('-', '_')}_file_count"] = dest_count
        report["migrated"] = True
        report["backup_path"] = backup_path

    return report


def create_project_structure(project_dir: str, project_id: str) -> list[str]:
    """Create all required directories for a new project.

    Returns list of created directories (relative paths).
    """
    project_path = os.path.join(project_dir, PROJECTS_SUBDIR, project_id)
    created = []

    # outputs/ subdirectories
    for subdir in REQUIRED_OUTPUT_SUBDIRS:
        dir_path = os.path.join(project_path, "outputs", subdir)
        os.makedirs(dir_path, exist_ok=True)
        created.append(os.path.join(PROJECTS_SUBDIR, project_id, "outputs", subdir))

    # review-logs/
    review_logs_path = os.path.join(project_path, "review-logs")
    os.makedirs(review_logs_path, exist_ok=True)
    created.append(os.path.join(PROJECTS_SUBDIR, project_id, "review-logs"))

    return created


def create_symlinks_atomic(project_dir: str, project_id: str) -> dict:
    """Create or atomically replace symlinks for outputs/ and review-logs/.

    Uses os.symlink() + os.rename() for atomic replacement.

    Returns dict of symlink_name → target_path.
    """
    result = {}
    project_rel = os.path.join(PROJECTS_SUBDIR, project_id)

    for symlink_name, target_subdir in SYMLINK_MAP.items():
        symlink_path = os.path.join(project_dir, symlink_name)
        target_rel = os.path.join(project_rel, target_subdir)
        tmp_symlink = symlink_path + "-tmp-init"

        # Clean up any leftover temp symlink from a previous crash
        if os.path.islink(tmp_symlink):
            os.unlink(tmp_symlink)

        # Create temporary symlink pointing to new target
        os.symlink(target_rel, tmp_symlink)

        # Atomic replace: os.rename() is atomic on same filesystem (POSIX)
        os.rename(tmp_symlink, symlink_path)

        result[symlink_name] = target_rel

    return result


# ─── Main ────────────────────────────────────────────────────────────────────

def init_project(
    project_dir: str,
    subject_name: str,
    date_str: str | None = None,
    migrate_existing: bool = False,
) -> dict:
    """Main entry point: initialize a new project with full isolation.

    Args:
        project_dir: Path to autobiography-generator/ directory.
        subject_name: Subject's name (will be sanitized).
        date_str: Optional date override (YYYYMMDD format).
        migrate_existing: If True, migrate real outputs/ to project directory.

    Returns:
        Result dict with all metadata.
    """
    project_dir = os.path.abspath(project_dir)

    # Determine repo root (parent of autobiography-generator/)
    repo_root = os.path.dirname(project_dir)

    # Generate project ID
    raw_id = _generate_project_id(subject_name, date_str)
    projects_dir = os.path.join(project_dir, PROJECTS_SUBDIR)
    os.makedirs(projects_dir, exist_ok=True)

    # Detect previous project
    previous_info = _detect_previous_project(project_dir)

    # Archive previous project if exists
    archive_report = None
    if previous_info:
        project_id = _resolve_duplicate(projects_dir, raw_id)
        archive_report = archive_previous_project(
            project_dir, repo_root, previous_info, project_id
        )
    else:
        project_id = _resolve_duplicate(projects_dir, raw_id)

    # Migrate existing real directory if requested
    migration_report = {"migrated": False, "outputs_file_count": 0, "review_logs_file_count": 0}
    if migrate_existing and previous_info and previous_info["source"] == "real_directory":
        # For migration, we use a migration-specific project ID
        # based on SOT data if available
        migrate_id = _determine_migration_id(project_dir, repo_root, raw_id)
        if migrate_id != project_id:
            # Migration goes to a different project (the old one)
            migration_report = migrate_existing_directory(project_dir, migrate_id)
        else:
            migration_report = migrate_existing_directory(project_dir, project_id)

    # Create project directory structure
    created_dirs = create_project_structure(project_dir, project_id)

    # Create/replace symlinks atomically
    symlinks = create_symlinks_atomic(project_dir, project_id)

    # Verify symlinks point correctly
    for symlink_name, expected_target in symlinks.items():
        actual_target = _read_symlink_target(os.path.join(project_dir, symlink_name))
        if actual_target != expected_target:
            print(
                f"ERROR: Symlink verification failed for {symlink_name}: "
                f"expected={expected_target}, actual={actual_target}",
                file=sys.stderr,
            )
            return {"error": f"Symlink verification failed for {symlink_name}"}

    return {
        "project_id": project_id,
        "project_dir": os.path.join(PROJECTS_SUBDIR, project_id),
        "abs_project_dir": os.path.join(project_dir, PROJECTS_SUBDIR, project_id),
        "created_dirs": created_dirs,
        "symlinks": symlinks,
        "archived_previous": archive_report,
        "migrated": migration_report.get("migrated", False),
        "migration_file_count": (
            migration_report.get("outputs_file_count", 0)
            + migration_report.get("review_logs_file_count", 0)
        ),
    }


def _determine_migration_id(
    project_dir: str, repo_root: str, fallback_id: str
) -> str:
    """Determine project ID for migrating existing data.

    Reads SOT to extract subject_name and project_start_date if available.
    Falls back to the provided ID if SOT is unavailable.
    """
    sot_path = os.path.join(repo_root, SOT_RELATIVE)
    if not os.path.isfile(sot_path):
        return fallback_id

    try:
        import yaml
        with open(sot_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}

        meta = state.get("meta", {})
        subject = meta.get("subject_name", "")
        start_date = meta.get("project_start_date", "")

        if subject and start_date:
            date_str = start_date.replace("-", "")
            return _generate_project_id(subject, date_str)
    except Exception:
        pass

    return fallback_id


def main():
    parser = argparse.ArgumentParser(
        description="Deterministic project initialization — P1 compliant"
    )
    parser.add_argument(
        "--subject-name",
        required=True,
        help="Subject's name for the autobiography",
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Path to autobiography-generator/ directory",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Date override in YYYYMMDD format (default: today)",
    )
    parser.add_argument(
        "--migrate-existing",
        action="store_true",
        help="Migrate existing real outputs/ directory to project directory",
    )

    args = parser.parse_args()

    # Validate project-dir exists
    if not os.path.isdir(args.project_dir):
        print(f"ERROR: Project directory not found: {args.project_dir}", file=sys.stderr)
        sys.exit(1)

    # Validate date format if provided
    if args.date:
        if not re.match(r"^\d{8}$", args.date):
            print(f"ERROR: Invalid date format: {args.date}. Use YYYYMMDD.", file=sys.stderr)
            sys.exit(1)

    try:
        result = init_project(
            project_dir=args.project_dir,
            subject_name=args.subject_name,
            date_str=args.date,
            migrate_existing=args.migrate_existing,
        )

        if "error" in result:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(f"ERROR: Unexpected failure: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
