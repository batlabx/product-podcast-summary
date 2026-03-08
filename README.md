# 🎙️ Product Podcast Summary

A daily automation project that:

1. Stores all podcast transcripts in `Transcripts/`
2. Picks **one random transcript per day**
3. Prevents repeats until all transcripts are exhausted
4. Updates `progress.md` automatically
5. Generates a morning summary file in `summaries/`

---

## ✨ Project Structure

```text
product-podcast-summary/
├── Transcripts/            # Source transcript archive (.txt)
├── summaries/              # Daily generated summaries
├── picker.py               # Daily transcript picker (no repeats)
├── summarize.py            # Summary generator
├── run_daily.sh            # One-shot runner (pick + summarize)
├── state.json              # Internal pick history/state
├── progress.md             # Human-readable tracking log
└── README.md
```

---

## 🚀 Quick Start

```bash
cd product-podcast-summary
python3 picker.py
python3 summarize.py
```

Or run both together:

```bash
bash run_daily.sh
```

---

## 🔁 Daily Schedule (7:30 AM)

Install a cron job:

```bash
(crontab -l 2>/dev/null; echo "30 7 * * * cd /Users/batlab/.openclaw/workspace/product-podcast-summary && /bin/bash run_daily.sh >> daily.log 2>&1") | crontab -
```

This runs every day at **7:30 AM** and logs output to `daily.log`.

---

## ✅ No-Repeat Guarantee

`picker.py` stores all prior picks in `state.json` and only chooses from remaining transcripts.

If a pick already happened today, it reuses that pick (idempotent behavior) unless run with:

```bash
python3 picker.py --force
```

---

## 🧠 Progress Tracking

Every new pick appends this format to `progress.md`:

```markdown
| YYYY-MM-DD | Transcript Name.txt | Selected |
```

You can later upgrade statuses manually (e.g., `Selected` → `Summarized` → `Shared`).

---

## 🔐 Notes

- Built to be deterministic and safe for daily automation.
- Handles large transcript sets without duplicates.
- Easy to extend for WhatsApp/email sending hooks later.
