#!/usr/bin/env python3
"""
Post-execution hook that validates analysis output.

This script checks if Analyzed_Output files were modified and ensures
all new rows went through the enforced analysis workflow (have process token).

If invalid rows are found, the file is reverted via git.

Usage (as hook):
    Called automatically after Bash tool executions

Manual:
    python scripts/check_process_token.py
"""

import os
import json
import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = Path(os.path.expanduser("~/Desktop/Files/Analyzed_Output"))
LOG_FILE = PROJECT_ROOT / "logs" / "validation_hook.log"
STATE_FILE = PROJECT_ROOT / "logs" / "validation_hook_state.json"

# Output files to monitor
MONITORED_FILES = [
    "Final 2024 Denodo Review - Analyzed.xlsx",
    "Phase_3_2023_Use Tax - Analyzed.xlsx",
    "Phase_3_2024_Use Tax - Analyzed.xlsx",
]


def log(message: str):
    """Write to log file."""
    LOG_FILE.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[HOOK] {message}")


def has_process_token(reasoning: str) -> bool:
    """Check if AI_Reasoning contains a valid process token."""
    if pd.isna(reasoning):
        return True  # Empty rows are OK (not analyzed yet)
    return "ENFORCED_PROCESS|" in str(reasoning)


def _is_in_repo(filepath: Path) -> bool:
    """Return True if filepath is inside this git repository."""
    try:
        filepath.resolve().relative_to(PROJECT_ROOT.resolve())
        return True
    except ValueError:
        return False


def file_sha256(filepath: Path) -> str:
    """Compute file hash to detect content changes outside git."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_state() -> dict:
    """Load last-seen file hashes for monitored outputs."""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception as e:
        log(f"Could not load state file: {e}")
    return {}


def save_state(state: dict):
    """Persist last-seen file hashes."""
    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def is_modified(filepath: Path, state: dict) -> tuple[bool, str]:
    """
    Determine if file content changed since last successful hook run.

    On first sight of a file (no prior state), bootstrap hash and return False
    to avoid validating historical rows that predate this hook state.
    """
    key = str(filepath)
    current_hash = file_sha256(filepath)
    previous_hash = state.get(key)

    if previous_hash is None:
        state[key] = current_hash
        return False, current_hash

    return current_hash != previous_hash, current_hash


def revert_file(filepath: Path) -> bool:
    """Revert file to last committed state via git checkout."""
    if not _is_in_repo(filepath):
        log(f"Cannot auto-revert non-repo file: {filepath}")
        return False

    try:
        repo_relpath = str(filepath.resolve().relative_to(PROJECT_ROOT.resolve()))
        result = subprocess.run(
            ["git", "checkout", "--", repo_relpath],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        return result.returncode == 0
    except Exception as e:
        log(f"Failed to revert {filepath}: {e}")
        return False


def validate_file(filepath: Path) -> tuple[bool, list]:
    """
    Validate an analysis output file.
    Returns (is_valid, list_of_invalid_row_indices)
    """
    if not filepath.exists():
        return True, []

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        log(f"Could not read {filepath}: {e}")
        return True, []  # Can't validate, assume OK

    # Find AI_Reasoning column
    reasoning_col = None
    for col in ["AI_Reasoning", "Recon Analysis", "KOM Analysis & Notes"]:
        if col in df.columns:
            reasoning_col = col
            break

    if not reasoning_col:
        return True, []  # No reasoning column, can't validate

    # Check each row with content
    invalid_rows = []
    for idx, row in df.iterrows():
        reasoning = row.get(reasoning_col, "")

        # Skip empty rows (not analyzed yet)
        if pd.isna(reasoning) or not str(reasoning).strip():
            continue

        # Check for process token
        if not has_process_token(reasoning):
            invalid_rows.append(idx)

    return len(invalid_rows) == 0, invalid_rows


def main():
    """Main hook execution."""
    log("Validation hook triggered")

    any_issues = False
    state = load_state()

    for filename in MONITORED_FILES:
        filepath = OUTPUT_DIR / filename

        if not filepath.exists():
            continue

        # Check if file content changed since last run
        modified, current_hash = is_modified(filepath, state)
        if not modified:
            continue  # Not modified

        log(f"Checking modified file: {filename}")

        # Validate the file
        is_valid, invalid_rows = validate_file(filepath)

        if not is_valid:
            any_issues = True
            log(f"INVALID: {filename} has {len(invalid_rows)} rows without process token")
            log(f"Invalid row indices: {invalid_rows[:10]}...")  # Show first 10

            # Attempt to revert
            if revert_file(filepath):
                log(f"REVERTED: {filename} restored to last committed state")
                if filepath.exists():
                    state[str(filepath)] = file_sha256(filepath)
                print(f"\n{'='*60}")
                print(f"⚠️  BLOCKED: Analysis output rejected")
                print(f"{'='*60}")
                print(f"File: {filename}")
                print(f"Reason: {len(invalid_rows)} row(s) missing process token")
                print(f"Action: File reverted to last committed state")
                print(f"\nRows must go through enforced analysis workflow.")
                print(f"Run: python scripts/analyze_row.py --file <dataset>")
                print(f"{'='*60}\n")
            else:
                log(f"WARNING: Could not revert {filename}")
                print(f"\n{'='*60}")
                print(f"⚠️  BLOCKED: Analysis output rejected")
                print(f"{'='*60}")
                print(f"File: {filename}")
                print(f"Reason: {len(invalid_rows)} row(s) missing process token")
                print("Action: Manual revert required (file is outside repo)")
                print(f"\nRows must go through enforced analysis workflow.")
                print(f"Run: python scripts/analyze_row.py --file <dataset>")
                print(f"{'='*60}\n")
        else:
            log(f"VALID: {filename} passed validation")
            state[str(filepath)] = current_hash

    save_state(state)

    if any_issues:
        sys.exit(1)  # Signal failure to hook system

    log("Validation hook completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
