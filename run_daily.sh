#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

/usr/bin/env python3 picker.py
/usr/bin/env python3 summarize.py
