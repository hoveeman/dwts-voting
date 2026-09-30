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

# Force line-buffering on stdout/stderr so Unraid and background cron logs stream in real time
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

LOG_FILE_PATH = os.path.join(WORKSPACE_DIR, "live_watcher.log")


def set_log_file(path):
    global LOG_FILE_PATH
    LOG_FILE_PATH = path


def log(msg, level="INFO"):
    now_et = get_current_et()
    time_str = now_et.strftime("%I:%M:%S %p ET")
    formatted = f"[{time_str}] [{level}] {msg}"
    print(formatted, flush=True)

    if LOG_FILE_PATH:
        try:
            date_time_str = now_et.strftime("%Y-%m-%d %H:%M:%S ET")
            with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
                f.write(f"[{date_time_str}] [{level}] {msg}\n")
        except Exception:
            pass


def get_current_et():
    return datetime.now(ET_TZ)


def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, cwd=WORKSPACE_DIR, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def git_has_changes():
    code, out, _ = run_cmd("git status --porcelain index.html dancers.json dancers.txt")
    return bool(out)


def push_updates(scored_count, total_count, leader_name, leader_score):
    log("Running validation check on index.html formatting...")
    if validate() != 0:
        log("Validation FAILED! Aborting commit to protect site integrity.", level="ERROR")
        return False
    log("Validation PASSED: All formatting rules and required sections verified.")

    run_cmd("git config user.name 'github-actions[bot]'")
    run_cmd("git config user.email 'github-actions[bot]@users.noreply.github.com'")
    run_cmd("git add index.html dancers.json dancers.txt")

    if not git_has_changes():
        log("No file changes detected after update.")
        return False

    summary = f"{scored_count}/{total_count} danced"
    if leader_name and leader_score:
        summary += f" · {leader_name} leads ({leader_score}/30)"

    commit_msg = f"chore(live): update show scores ({summary})"
    code, out, err = run_cmd(f'git commit -m "{commit_msg}"')
    if code != 0:
        log(f"Git commit failed: {err}", level="ERROR")
        return False

    log(f"Committed: {commit_msg}")
    log("Pushing updates to origin main...")
    code, out, err = run_cmd("git push origin main")
    if code != 0:
        log(f"Initial push rejected ({err}). Pulling remote changes with rebase and retrying...", level="WARN")
        run_cmd("git pull --rebase origin main")
        code, out, err = run_cmd("git push origin main")

    if code == 0:
        log("Successfully pushed live update to main! (GitHub Pages deploying)", level="SUCCESS")
        return True
    else:
        log(f"Git push failed: {err}", level="ERROR")
        return False


def poll_cycle(last_snapshot=None, market_odds=None, dry_run=False, interval_secs=75, poll_index=1):
    wiki_html = fetch_wiki_html()
    data = parse_wikipedia_data(wiki_html)

    # Determine current week
    week_lineups = data.get('week_lineups', {})
    if not week_lineups:
        log("No week lineup data found on Wikipedia.", level="WARN")
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

    has_elimination = any('eliminated' in str(c.get('result', '')).lower() for c in couples) or any(v.get('week') == current_week for v in data.get('eliminated_info', {}).values())
    all_have_results = (len(couples) > 0 and all(bool(c.get('result')) for c in couples))
    all_scored = (len(scored) == total and total > 0)

    # Show is done if all routines have scores AND either:
    # 1. An official elimination is recorded on Wikipedia, OR
    # 2. All couples have results marked AND it is past 10:05 PM ET (e.g. non-elimination episode), OR
    # 3. Safety time cutoff: past 10:20 PM ET for a normal show (or past 11:20 PM ET for a finale)
    now_et = get_current_et()
    all_done = False
    if all_scored:
        if has_elimination:
            all_done = True
        elif all_have_results and ((now_et.hour == 22 and now_et.minute >= 5) or now_et.hour >= 23):
            all_done = True
        elif (now_et.hour == 22 and now_et.minute >= 20) or (now_et.hour >= 23 and now_et.minute >= 20):
            all_done = True

    if last_snapshot is not None and current_snapshot == last_snapshot:
        recent_str = f" · Leader: {leader_name} ({leader_score}/30)" if leader_name else ""
        log(f"Check #{poll_index}: No changes detected ({len(scored)}/{total} scored{recent_str}). Next check in {interval_secs}s.")
        return len(scored), total, all_done, current_snapshot

    scored_summary = ", ".join([f"{c['name']} ({c['score']}/30)" for c in scored]) if scored else "None yet"
    log(f"Check #{poll_index}: SCORE UPDATE DETECTED! {len(scored)} of {total} couples scored [{scored_summary}].", level="UPDATE")

    if dry_run:
        log("Dry run mode: Skipping file modifications and git push.")
        return len(scored), total, all_done, current_snapshot

    # Update index.html, dancers.json, dancers.txt
    update_index_html(data, market_odds)

    if git_has_changes():
        log("Detected changes to index.html/dancers.json/dancers.txt!")
        push_updates(len(scored), total, leader_name, leader_score)
    else:
        log("Files already up to date.")

    return len(scored), total, all_done, current_snapshot


def wait_until_tuesday_show():
    now = get_current_et()
    from datetime import datetime, timedelta
    # Check special Monday Nov 2 show (Disney Night due to Election Day)
    special_date = datetime(2026, 11, 2, 20, 0, 0, tzinfo=ET_TZ)
    if now < special_date and (special_date - now).total_seconds() <= 86400 * 3:
        target = special_date
    else:
        # Target Tuesday 20:00:00 (8:00 PM ET)
        days_ahead = (1 - now.weekday()) % 7  # 1 is Tuesday in Python (0=Mon, 1=Tue)
        if days_ahead == 0 and (now.hour > 22 or (now.hour == 22 and now.minute > 5)):
            days_ahead = 7  # show passed today, target next Tuesday

        target = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if days_ahead > 0:
            target += timedelta(days=days_ahead)

    diff_seconds = (target - now).total_seconds()
    if diff_seconds > 0:
        hours = diff_seconds / 3600
        log(f"Waiting for live show start at {target.strftime('%A, %b. %d at %I:%M %p ET')} (~{hours:.1f} hours away)...")
        time.sleep(diff_seconds)
        log("Live show window reached! Starting live polling loop...")


def main():
    parser = argparse.ArgumentParser(description="DWTS Live Show Real-Time Watcher")
    parser.add_argument("--interval", type=int, default=75, help="Seconds between Wikipedia checks (default: 75s)")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and inspect without committing or pushing")
    parser.add_argument("--once", action="store_true", help="Run a single check now and exit")
    parser.add_argument("--wait-until-show", action="store_true", help="Sleep until Tuesday 8:00 PM ET before running")
    parser.add_argument("--max-hours", type=float, default=3.5, help="Max hours to run before exiting (default: 3.5h, accommodates 3h specials)")
    parser.add_argument("--log-file", type=str, default=os.path.join(WORKSPACE_DIR, "live_watcher.log"), help="Path to write log output (default: live_watcher.log)")
    parser.add_argument("--no-log-file", action="store_true", help="Disable writing to log file (stdout only)")
    args = parser.parse_args()

    if args.no_log_file:
        set_log_file(None)
    else:
        set_log_file(args.log_file)

    log("=== DWTS Season 35 Live Show Watcher Started ===")
    log(f"Current Time (ET): {get_current_et().strftime('%A, %b. %d, %Y %I:%M:%S %p ET')}")
    if LOG_FILE_PATH:
        log(f"Persistent log file: {LOG_FILE_PATH}")

    if args.wait_until_show:
        wait_until_tuesday_show()

    # Pre-fetch Kalshi odds once at startup
    log("Fetching prediction market baseline from Kalshi...")
    market_odds = fetch_prediction_market_data()
    log(f"Kalshi odds loaded for {len(market_odds)} couples.")

    last_snapshot = None

    if args.once:
        log("Running single check mode (--once)...")
        poll_cycle(last_snapshot=None, market_odds=market_odds, dry_run=args.dry_run, interval_secs=args.interval, poll_index=1)
        log("Check completed successfully.")
        return 0

    log(f"Starting live monitoring loop (polling every {args.interval}s, max runtime {args.max_hours}h)...")
    start_time = time.time()
    max_seconds = args.max_hours * 3600
    poll_count = 0

    last_market_refresh = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            log(f"Reached maximum runtime ({args.max_hours} hours). Exiting watcher.")
            break

        # Refresh Kalshi odds every 15 minutes during the show
        if time.time() - last_market_refresh > 900:
            log("Refreshing Kalshi market odds...")
            market_odds = fetch_prediction_market_data()
            last_market_refresh = time.time()

        poll_count += 1
        try:
            scored, total, all_done, last_snapshot = poll_cycle(
                last_snapshot=last_snapshot,
                market_odds=market_odds,
                dry_run=args.dry_run,
                interval_secs=args.interval,
                poll_index=poll_count
            )
            if all_done:
                log(f"All {total} couples have completed their routines and scores/results are recorded!", level="SUCCESS")
                log("Show complete. Exiting live watcher cleanly.")
                break
        except Exception as e:
            log(f"Error during poll cycle #{poll_count}: {e}", level="ERROR")

        time.sleep(args.interval)

    return 0


if __name__ == '__main__':
    sys.exit(main())
