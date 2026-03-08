#!/usr/bin/env python3
"""Generate a structured podcast summary using local (no-API) retrieval."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSCRIPTS_DIR = ROOT / "Transcripts"
STATE_FILE = ROOT / "state.json"
SUMMARY_DIR = ROOT / "summaries"

STOPWORDS = {
    "the", "and", "that", "with", "this", "from", "have", "about", "your", "they", "what", "when",
    "which", "would", "there", "their", "them", "then", "just", "like", "into", "than", "because",
    "really", "also", "were", "been", "will", "where", "could", "should", "after", "before", "while",
    "some", "more", "most", "very", "much", "only", "over", "such", "many", "those", "these", "through",
    "being", "even", "make", "made", "does", "dont", "did", "doesnt", "cant", "youre", "its", "im",
}

SECTION_QUERIES = {
    "Top Insights": [
        "main point key lesson biggest takeaway",
        "what works what fails practical advice",
        "decision making framework team strategy",
    ],
    "Frameworks Mentioned": [
        "framework model system approach method process",
        "step by step playbook checklist principles",
    ],
    "Action Items": [
        "what should product leaders do next actions",
        "practical tactics implementation execution",
    ],
    "Notable Quotes": [
        "memorable line quote important statement",
        "strong opinion clear advice",
    ],
}


def get_today_selection() -> str:
    if not STATE_FILE.exists():
        raise RuntimeError("No state.json found. Run picker.py first.")

    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    today = datetime.now().strftime("%Y-%m-%d")
    for item in reversed(state.get("picked", [])):
        if item.get("date") == today:
            return item["file"]
    raise RuntimeError("No transcript selected for today.")


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    return [w for w in words if len(w) >= 3 and w not in STOPWORDS]


def split_chunks(text: str) -> list[str]:
    # Prefer paragraph chunks; fall back to sentence windows if needed.
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 80]
    paras = [p for p in paras if "episode is brought to you" not in p.lower()]
    if len(paras) >= 15:
        return paras

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 30]
    chunks = []
    for i in range(0, len(sentences), 3):
        block = " ".join(sentences[i:i + 3]).strip()
        if len(block) > 80:
            chunks.append(block)
    return chunks


def build_idf(chunks: list[str]) -> dict[str, float]:
    n_docs = max(len(chunks), 1)
    df = Counter()
    for c in chunks:
        df.update(set(tokenize(c)))
    return {t: math.log((n_docs + 1) / (f + 1)) + 1.0 for t, f in df.items()}


def score_chunk(query: str, chunk: str, idf: dict[str, float]) -> float:
    q_terms = tokenize(query)
    if not q_terms:
        return 0.0

    c_terms = tokenize(chunk)
    tf = Counter(c_terms)
    norm = math.sqrt(sum((tf[t] * idf.get(t, 0.0)) ** 2 for t in tf)) or 1.0

    score = 0.0
    for t in q_terms:
        if t in tf:
            score += (1 + math.log(tf[t])) * idf.get(t, 0.0)
    return score / norm


def retrieve(chunks: list[str], query: str, idf: dict[str, float], k: int = 4) -> list[str]:
    ranked = sorted(chunks, key=lambda c: score_chunk(query, c, idf), reverse=True)
    out = []
    seen = set()
    for c in ranked:
        key = c[:120]
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
        if len(out) >= k:
            break
    return out


def clean_utterance(text: str) -> str:
    t = text.replace("\n", " ").strip()
    # remove repeated speaker/timestamp prefixes
    t = re.sub(r"(?:^|\s)[A-Za-z .'-]+\s*\(\d{2}:\d{2}:\d{2}\):\s*", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def first_sentence(text: str, max_len: int = 220) -> str:
    cleaned = clean_utterance(text)
    sents = re.split(r"(?<=[.!?])\s+", cleaned)
    candidate = sents[0].strip() if sents else cleaned
    if len(candidate) > max_len:
        return candidate[: max_len - 1].rstrip() + "…"
    return candidate


def build_summary(transcript_name: str, transcript_text: str) -> str:
    chunks = split_chunks(transcript_text)
    idf = build_idf(chunks)

    # TL;DR from broad query
    tldr_chunks = retrieve(chunks, "main thesis central argument practical takeaway", idf, k=3)
    tldr = " ".join(first_sentence(c, 180) for c in tldr_chunks[:2])

    lines = [
        f"# Product Podcast Summary — {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"**Transcript:** {transcript_name}",
        "",
        "## TL;DR",
        f"{tldr}",
        "",
    ]

    for section, queries in SECTION_QUERIES.items():
        lines.append(f"## {section}")
        section_chunks: list[str] = []
        for q in queries:
            section_chunks.extend(retrieve(chunks, q, idf, k=3))

        # de-duplicate + keep top concise points
        clean = []
        seen = set()
        for c in section_chunks:
            sentence = first_sentence(c)
            s_lower = sentence.lower()
            if "episode is brought to you" in s_lower:
                continue
            if re.fullmatch(r"\(?\d{2}:\d{2}:\d{2}\)?[:\-\s]*", sentence):
                continue
            key = s_lower
            if key in seen:
                continue
            seen.add(key)
            clean.append(sentence)
            if len(clean) >= 5:
                break

        for item in clean:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## Sources")
    lines.append("- Generated via local retrieval (TF-IDF style) from the selected transcript only.")
    lines.append("")
    return "\n".join(lines)


def save_summary(content: str) -> Path:
    SUMMARY_DIR.mkdir(exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    out = SUMMARY_DIR / f"{date}.md"
    out.write_text(content, encoding="utf-8")
    return out


def main() -> None:
    file_name = get_today_selection()
    transcript = (TRANSCRIPTS_DIR / file_name).read_text(encoding="utf-8", errors="ignore")
    content = build_summary(file_name, transcript)
    summary_path = save_summary(content)

    print("📨 Morning summary generated (local RAG mode)")
    print(f"Transcript: {file_name}")
    print(f"Summary file: {summary_path}")


if __name__ == "__main__":
    main()
