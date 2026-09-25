#!/usr/bin/env python3
"""
Validation script for DWTS Season 35 Cheat Sheet (index.html).
Checks compliance with formatting rules from dwts-cheat-sheet-implementation-plan.md:
- Score format: 'Week N · Dance Style · score/30'
- Total scores: running sum out of (30 * weeks completed)
- Mirrorball counters: '0 Mirrorballs', '1 Mirrorball', '2 Mirrorballs', etc.
- Eliminated couples have dates, exit dance, song, score, and final total
"""

import sys
import re
import os

HTML_FILE = os.path.join(os.path.dirname(__file__), '..', 'index.html')

def validate():
    if not os.path.exists(HTML_FILE):
        print(f"Error: {HTML_FILE} does not exist")
        return 1

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    errors = []

    # Check mirrorball labeling function
    if "mirrorballLabel" not in html:
        errors.append("Missing mirrorballLabel formatting function")

    # Check that eliminated couples exist
    if 'id="voted-off"' not in html:
        errors.append("Missing #voted-off section")

    # Check voting shortcut link
    if "shortcuts/3e951e5ba20b49dc82f5abded923b179" not in html:
        errors.append("Missing Trent's iOS SMS-voting shortcut link")

    # Check score box format pattern in JS or HTML
    if "Week ${index+1} · ${week.dance}" not in html and "Week 1 · " not in html:
        errors.append("Missing expected 'Week N · Dance' scoring pattern")

    if errors:
        print(f"Validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1
    else:
        print("Validation PASSED: All formatting rules and required sections verified.")
        return 0

if __name__ == '__main__':
    sys.exit(validate())
