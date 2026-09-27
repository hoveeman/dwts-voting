#!/usr/bin/env python3
"""
DWTS Live Show Watcher
Polls Wikipedia in real-time during Tuesday live show broadcasts (8:00 - 10:05 PM ET),
detects new judges' scores and eliminations, updates the cheat sheet and iOS voting files,
validates formatting, and pushes commits directly to GitHub main.
"""

import os
import sys
import time
import argparse
import subprocess
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from update_cheat_sheet import (
    fetch_wiki_html,
    parse_wikipedia_data,
    update_index_html,
    fetch_prediction_market_data,
    WORKSPACE_DIR
)
from validate_cheat_sheet import validate

ET_TZ = ZoneInfo("America/New_York")


def get_current_et():
    return datetime.now(ET_TZ)


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, cwd=WORKSPACE_DIR, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def git_has_changes():
    code, out, _ = run_cmd("git status --porcelain index.html dancers.json dancers.txt")
    return bool(out)


def push_updates(scored_count, total_count, leader_name, leader_score):
    print("Formatting validation check...")
    if validate() != 0:
        print("Validation failed! Aborting commit to protect site integrity.")
        return False

    run_cmd("git config user.name 'github-actions[bot]'")
    run_cmd("git config user.email 'github-actions[bot]@users.noreply.github.com'")
    run_cmd("git add index.html dancers.json dancers.txt")

    if not git_has_changes():
        print("No file changes detected after update.")
        return False

    summary = f"{scored_count}/{total_count} danced"
    if leader_name and leader_score:
        summary += f" · {leader_name} leads ({leader_score}/30)"

    commit_msg = f"chore(live): update show scores ({summary})"
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"Git commit failed: {err}")
        return False

    print(f"Committed: {commit_msg}")
    print("Pushing to origin main...")
    code, out, err = run_cmd("git push origin main")
    if code == 0:
        print("Successfully pushed live update to main!")
        return True
    else:
        print(f"Git push failed: {err}")
        return False


def poll_cycle(last_snapshot=None, market_odds=None, dry_run=False):
    wiki_html = fetch_wiki_html()
    data = parse_wikipedia_data(wiki_html)

    # Determine current week
    week_lineups = data.get('week_lineups', {})
    if not week_lineups:
        print("No week lineup data found.")
        return 0, 0, False, last_snapshot

    current_week = max(week_lineups.keys())
    couples = week_lineups[current_week].get('couples', [])
    scored = [c for c in couples if c.get('score') is not None]
    total = len(couples)

    scored_sorted = sorted(scored, key=lambda c: (-c['score'], c['name']))
    leader_name = scored_sorted[0]['name'] if scored_sorted else None
    leader_score = scored_sorted[0]['score'] if scored_sorted else None

    current_snapshot = (
        tuple(sorted([(c['name'], c.get('score'), c.get('dance'), c.get('song'), c.get('result', '')) for c in couples])),
        tuple(sorted(data.get('eliminated_info', {}).keys()))
    )

    has_results = any(bool(c.get('result')) for c in couples)
    all_scored = (len(scored) == total and total > 0)

    # Show is done if all routines have scores AND either:
    # 1. Elimination/results are recorded on Wikipedia, OR
    # 2. It is past 10:10 PM ET for a normal show (or past 11:10 PM ET for a 3-hour finale)
    now_et = get_current_et()
    all_done = False
    if all_scored:
        if has_results:
            all_done = True
        elif (now_et.hour == 22 and now_et.minute >= 10) or (now_et.hour >= 23 and now_et.minute >= 10):
            all_done = True

    if last_snapshot is not None and current_snapshot == last_snapshot:
        print(f"[{now_et.strftime('%I:%M:%S %p ET')}] No changes detected ({len(scored)}/{total} scored). Waiting for next poll...")
        return len(scored), total, all_done, current_snapshot

    print(f"[{now_et.strftime('%I:%M:%S %p ET')}] Update detected: {len(scored)} of {total} couples scored.")

    if dry_run:
        print("Dry run mode: Skipping file modifications and git push.")
        return len(scored), total, all_done, current_snapshot

    # Update index.html, dancers.json, dancers.txt
    update_index_html(data, market_odds)

    if git_has_changes():
        print("Detected changes to index.html/dancers.json/dancers.txt!")
        push_updates(len(scored), total, leader_name, leader_score)
    else:
        print("Files already up to date.")

    return len(scored), total, all_done, current_snapshot


def wait_until_tuesday_show():
    now = get_current_et()
    # Target Tuesday 20:00:00 (8:00 PM ET)
    days_ahead = (1 - now.weekday()) % 7  # 1 is Tuesday in Python (0=Mon, 1=Tue)
    if days_ahead == 0 and (now.hour > 22 or (now.hour == 22 and now.minute > 5)):
        days_ahead = 7  # show passed today, target next Tuesday

    target = now.replace(hour=20, minute=0, second=0, microsecond=0)
    if days_ahead > 0:
        from datetime import timedelta
        target += timedelta(days=days_ahead)

    diff_seconds = (target - now).total_seconds()
    if diff_seconds > 0:
        hours = diff_seconds / 3600
        print(f"Waiting for live show start at {target.strftime('%A, %b. %d at %I:%M %p ET')} (~{hours:.1f} hours away)...")
        time.sleep(diff_seconds)
        print("Live show window reached! Starting live polling loop...")


def main():
    parser = argparse.ArgumentParser(description="DWTS Live Show Real-Time Watcher")
    parser.add_argument("--interval", type=int, default=75, help="Seconds between Wikipedia checks (default: 75s)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and inspect without committing or pushing")
    parser.add_argument("--once", action="store_true", help="Run a single check now and exit")
    parser.add_argument("--wait-until-show", action="store_true", help="Sleep until Tuesday 8:00 PM ET before running")
    parser.add_argument("--max-hours", type=float, default=3.5, help="Max hours to run before exiting (default: 3.5h, accommodates 3h specials)")
    args = parser.parse_args()

    print("=== DWTS Season 35 Live Show Watcher ===")
    print(f"Current Time (ET): {get_current_et().strftime('%A, %b. %d, %Y %I:%M:%S %p ET')}")

    if args.wait_until_show:
        wait_until_tuesday_show()

    # Pre-fetch Kalshi odds once at startup
    print("Fetching prediction market baseline...")
    market_odds = fetch_prediction_market_data()
    print(f"Kalshi odds loaded for {len(market_odds)} couples.")

    last_snapshot = None

    if args.once:
        print("Running single live check...")
        poll_cycle(last_snapshot=None, market_odds=market_odds, dry_run=args.dry_run)
        print("Check completed.")
        return 0

    print(f"Starting live monitoring loop (polling every {args.interval}s, max runtime {args.max_hours}h)...")
    start_time = time.time()
    max_seconds = args.max_hours * 3600

    last_market_refresh = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            print(f"Reached maximum runtime ({args.max_hours} hours). Exiting watcher.")
            break

        # Refresh Kalshi odds every 15 minutes during the show
        if time.time() - last_market_refresh > 900:
            print("Refreshing Kalshi market odds...")
            market_odds = fetch_prediction_market_data()
            last_market_refresh = time.time()

        try:
            scored, total, all_done, last_snapshot = poll_cycle(
                last_snapshot=last_snapshot,
                market_odds=market_odds,
                dry_run=args.dry_run
            )
            if all_done:
                print(f"All {total} couples have completed their routines and scores are recorded!")
                print("Show complete. Exiting live watcher cleanly.")
                break
        except Exception as e:
            print(f"Error during poll cycle: {e}")

        time.sleep(args.interval)

    return 0


if __name__ == '__main__':
    sys.exit(main())
