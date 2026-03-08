#!/usr/bin/env python3
"""Pick one transcript per day, avoid repeats, and update progress.md."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = ROOT / "Transcripts"
STATE_FILE = ROOT / "state.json"
PROGRESS_FILE = ROOT / "progress.md"


@dataclass
class PickResult:
    file_name: str
    date: str


def list_transcripts() -> list[str]:
    if not TRANSCRIPTS_DIR.exists():
        raise FileNotFoundError(f"Transcripts folder not found: {TRANSCRIPTS_DIR}")
    return sorted([p.name for p in TRANSCRIPTS_DIR.glob("*.txt")])


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"picked": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def pick_transcript(force: bool = False) -> PickResult:
    today = datetime.now().strftime("%Y-%m-%d")
    state = load_state()

    # Reuse today's pick unless --force was set
    if not force:
        for item in state.get("picked", []):
            if item.get("date") == today:
                return PickResult(file_name=item["file"], date=today)

    all_files = list_transcripts()
    picked_files = {item["file"] for item in state.get("picked", [])}
    remaining = [f for f in all_files if f not in picked_files]

    if not remaining:
        raise RuntimeError("All transcripts have already been picked.")

    chosen = random.choice(remaining)
    state.setdefault("picked", []).append({"date": today, "file": chosen})
    save_state(state)
    append_progress(today, chosen)

    return PickResult(file_name=chosen, date=today)


def append_progress(date: str, file_name: str) -> None:
    if not PROGRESS_FILE.exists():
        PROGRESS_FILE.write_text(
            "# Progress\n\n"
            "Track of transcripts selected/summarized by date.\n\n"
            "| Date | Transcript | Status |\n"
            "|---|---|---|\n",
            encoding="utf-8",
        )

    line = f"| {date} | {file_name} | Selected |\n"
    existing = PROGRESS_FILE.read_text(encoding="utf-8")
    if line not in existing:
        with PROGRESS_FILE.open("a", encoding="utf-8") as f:
            f.write(line)


def print_selection(result: PickResult) -> None:
    print("✅ Daily transcript selected")
    print(f"Date: {result.date}")
    print(f"Transcript: {result.file_name}")
    print(f"Path: {TRANSCRIPTS_DIR / result.file_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily transcript picker")
    parser.add_argument("--force", action="store_true", help="Force a new pick for today")
    args = parser.parse_args()

    result = pick_transcript(force=args.force)
    print_selection(result)


if __name__ == "__main__":
    main()
