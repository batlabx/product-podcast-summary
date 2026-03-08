#!/usr/bin/env python3
"""Generate a simple extractive summary for the latest selected transcript."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = ROOT / "Transcripts"
STATE_FILE = ROOT / "state.json"
SUMMARY_DIR = ROOT / "summaries"

STOPWORDS = {
    "the", "and", "that", "with", "this", "from", "have", "about", "your", "they", "what", "when", "which",
    "would", "there", "their", "them", "then", "just", "like", "into", "than", "because", "really", "also",
    "were", "been", "will", "where", "could", "should", "after", "before", "while", "some", "more", "most",
    "very", "much", "only", "over", "such", "many", "those", "these", "through", "being", "even", "make",
}


def get_latest_selection_for_today() -> str:
    if not STATE_FILE.exists():
        raise RuntimeError("No state.json found. Run picker.py first.")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    today = datetime.now().strftime("%Y-%m-%d")
    for item in reversed(state.get("picked", [])):
        if item.get("date") == today:
            return item["file"]

    raise RuntimeError("No transcript selected for today.")


def clean_sentence(sentence: str) -> str:
    s = sentence.replace("\n", " ").strip()
    # Remove speaker/timestamp patterns like: "Lenny (00:12:34):"
    s = re.sub(r"\b[\w .'-]+\s*\(\d{2}:\d{2}:\d{2}\):\s*", "", s)
    # Remove naked timestamp prefix like "(00:19:14):"
    s = re.sub(r"^\(?\d{2}:\d{2}:\d{2}\)?\s*:\s*", "", s)
    # Remove timestamp markers that survive in middle of sentences
    s = re.sub(r"\(?\d{2}:\d{2}:\d{2}\)?\s*:\s*", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_noise(sentence: str) -> bool:
    s = sentence.lower()
    if "episode is brought to you" in s:
        return True
    if "reader-supported publication" in s:
        return True
    if len(s) < 60:
        return True
    return False


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        cleaned = clean_sentence(p)
        if is_noise(cleaned):
            continue
        out.append(cleaned)
    return out


def sentence_score(sentence: str, top_words: set[str]) -> int:
    words = re.findall(r"[a-zA-Z']+", sentence.lower())
    return sum(1 for w in words if w in top_words)


def summarize_text(text: str, n: int = 8) -> list[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if len(w) < 4 or w in STOPWORDS:
            continue
        freq[w] = freq.get(w, 0) + 1

    top_words = {w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:60]}
    sentences = split_sentences(text)
    ranked = sorted(sentences, key=lambda s: sentence_score(s, top_words), reverse=True)

    selected: list[str] = []
    seen_prefix = set()
    for s in ranked:
        key = s[:120].lower()
        if key in seen_prefix:
            continue
        seen_prefix.add(key)
        selected.append(s)
        if len(selected) >= n:
            break

    # Fallback: ensure we always return something
    if not selected and sentences:
        selected = sentences[: min(n, len(sentences))]

    return selected


def save_summary(file_name: str, bullets: list[str]) -> Path:
    SUMMARY_DIR.mkdir(exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    out = SUMMARY_DIR / f"{date}.md"

    content = [
        f"# Product Podcast Summary — {date}",
        "",
        f"**Transcript:** {file_name}",
        "",
        "## Key Points",
    ]
    content.extend([f"- {b}" for b in bullets])
    content.append("")

    out.write_text("\n".join(content), encoding="utf-8")
    return out


def main() -> None:
    file_name = get_latest_selection_for_today()
    transcript = (TRANSCRIPTS_DIR / file_name).read_text(encoding="utf-8", errors="ignore")
    bullets = summarize_text(transcript)
    summary_path = save_summary(file_name, bullets)

    print("📨 Morning summary generated")
    print(f"Transcript: {file_name}")
    print(f"Summary file: {summary_path}")


if __name__ == "__main__":
    main()
