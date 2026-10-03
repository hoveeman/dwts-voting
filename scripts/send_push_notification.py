#!/usr/bin/env python3
"""
DWTS Push Notification Broadcaster via Firebase Cloud Messaging (FCM HTTP v1)
Sends topic notifications for pre-show countdowns and official eliminations.

Prerequisites:
- Set environment variable FIREBASE_SERVICE_ACCOUNT_KEY with the contents or path of the Firebase service account JSON.
- Or place service_account.json in the project root (ignored by git).
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import time
from datetime import datetime
from zoneinfo import ZoneInfo

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ET_TZ = ZoneInfo("America/New_York")


def get_access_token(service_account_info):
    """Generate an OAuth2 access token for FCM using standard library / crypto or pyjwt/requests."""
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
    except ImportError:
        # Fallback if google-auth is not installed: guide user or use simple token
        raise RuntimeError(
            "google-auth package is required to sign service account JWTs. Run: pip install google-auth requests"
        )


def load_service_account():
    """Load service account info from environment variable or local file."""
    env_val = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')
    if env_val:
        if os.path.exists(env_val):
            with open(env_val, 'r', encoding='utf-8') as f:
                return json.load(f)
        try:
            return json.loads(env_val)
        except Exception:
            pass

    # Look for local service account JSON files
    for fname in os.listdir(WORKSPACE_DIR):
        if fname.endswith('.json') and ('firebase' in fname.lower() or 'service_account' in fname.lower() or 'adminsdk' in fname.lower()):
            candidate = os.path.join(WORKSPACE_DIR, fname)
            try:
                with open(candidate, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'project_id' in data and 'private_key' in data:
                        return data
            except Exception:
                continue

    return None


def send_fcm_message(project_id, access_token, topic, title, body, data=None):
    """Send an FCM message to a topic via the HTTP v1 API."""
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    
    payload = {
        "message": {
            "topic": topic,
            "notification": {
                "title": title,
                "body": body
            },
            "data": data or {},
            "apns": {
                "payload": {
                    "aps": {
                        "sound": "default",
                        "badge": 1
                    }
                }
            },
            "android": {
                "notification": {
                    "sound": "default",
                    "channel_id": "dwts_broadcasts"
                }
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; UTF-8"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            print(f"[Push SUCCESS] Topic: {topic} | Response: {resp_body}")
            return True, resp_body
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"[Push ERROR {e.code}] {err_msg}", file=sys.stderr)
        return False, err_msg
    except Exception as e:
        print(f"[Push ERROR] {e}", file=sys.stderr)
        return False, str(e)


def broadcast_show_reminder(week_theme="Week 4 Live Show"):
    """Broadcast pre-show reminder 15 minutes before 8:00 PM ET."""
    service_acc = load_service_account()
    if not service_acc:
        print("[Push] No Firebase Service Account credentials found. Skipping push.")
        return False

    project_id = service_acc.get('project_id')
    token = get_access_token(service_acc)

    title = "🪩 DWTS Starts in 15 Minutes!"
    body = f"Tonight is {week_theme}! Check tonight's dance lineup, live scores, and prepare your 10 SMS votes."
    data = {"type": "show_start", "url": "https://dwts.hoverhobbies.com/#schedule"}

    # Broadcast to pre-show topic
    success, _ = send_fcm_message(project_id, token, "dwts-show-reminder", title, body, data)
    return success


def broadcast_elimination(eliminated_couple, week_num=4):
    """Broadcast elimination results after Tuesday live broadcast."""
    service_acc = load_service_account()
    if not service_acc:
        print("[Push] No Firebase Service Account credentials found. Skipping push.")
        return False

    project_id = service_acc.get('project_id')
    token = get_access_token(service_acc)

    # 1. Alert for users who want full elimination spoilers
    title_spoiler = "🪩 DWTS Elimination Result"
    body_spoiler = f"{eliminated_couple} has been eliminated from Season 35 tonight."
    send_fcm_message(
        project_id, token, "dwts-eliminations",
        title_spoiler, body_spoiler,
        {"type": "elimination", "couple": eliminated_couple, "url": "https://dwts.hoverhobbies.com/#voted-off"}
    )

    # 2. Alert for users who requested spoiler-free alerts
    title_clean = "🪩 DWTS Elimination Results"
    body_clean = f"The Week {week_num} results are in! Tap to reveal who was eliminated tonight."
    send_fcm_message(
        project_id, token, "dwts-eliminations-spoilerfree",
        title_clean, body_clean,
        {"type": "elimination", "url": "https://dwts.hoverhobbies.com/#voted-off"}
    )
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Send DWTS Push Notifications via Firebase Cloud Messaging")
    parser.add_argument("--type", choices=["reminder", "elimination"], required=True, help="Notification type")
    parser.add_argument("--couple", type=str, default="", help="Eliminated couple name")
    parser.add_argument("--theme", type=str, default="Week 4 Live Show", help="Weekly theme name")
    parser.add_argument("--week", type=int, default=4, help="Week number")

    args = parser.parse_args()

    if args.type == "reminder":
        broadcast_show_reminder(week_theme=args.theme)
    elif args.type == "elimination":
        if not args.couple:
            print("Error: --couple required for elimination notification.", file=sys.stderr)
            sys.exit(1)
        broadcast_elimination(args.couple, week_num=args.week)
