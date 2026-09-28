#!/usr/bin/env python3
"""
Spotify Playlist Creator for DWTS Season 35.
Automatically creates public or private Spotify playlists for Week 1, Week 2, Week 3,
and Season 35 Master, then populates them with every song from the cheat sheet.

Prerequisites:
  1. A free Spotify account.
  2. A Spotify Developer App from https://developer.spotify.com/dashboard
     - Create an app (e.g. "DWTS Playlist Creator")
     - Set Redirect URI to: http://127.0.0.1:8888/callback
  3. Set environment variables or enter when prompted:
     export SPOTIPY_CLIENT_ID="your_client_id"
     export SPOTIPY_CLIENT_SECRET="your_client_secret"
     export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PLAYLISTS_DIR = os.path.join(WORKSPACE_DIR, 'playlists')

PLAYLIST_DEFS = [
    {
        "file": "week_1_birth_year_hits.csv",
        "name": "DWTS Season 35 — Week 1: Premiere (Birth-Year #1 Hits)",
        "description": "All 16 songs from Dancing with the Stars Season 35 Week 1 (Birth-Year Hits)."
    },
    {
        "file": "week_2_viral_hits.csv",
        "name": "DWTS Season 35 — Week 2: Viral Hits Night",
        "description": "All 14 songs from Dancing with the Stars Season 35 Week 2 (Viral Hits Night)."
    },
    {
        "file": "week_3_yacht_rock.csv",
        "name": "DWTS Season 35 — Week 3: Yacht Rock Night",
        "description": "All 13 songs from Dancing with the Stars Season 35 Week 3 (Yacht Rock Night)."
    },
    {
        "file": "season_35_all_songs.csv",
        "name": "DWTS Season 35 — Complete Soundtrack (All Weeks)",
        "description": "Every competitive song danced across all weeks of DWTS Season 35."
    }
]

auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful!</h1><p>You can close this tab and return to the terminal.</p>")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Authorization failed</h1>")
    
    def log_message(self, format, *args):
        pass


def get_credentials():
    client_id = os.environ.get('SPOTIPY_CLIENT_ID') or os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET') or os.environ.get('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI') or os.environ.get('SPOTIFY_REDIRECT_URI') or 'http://127.0.0.1:8888/callback'

    if not client_id:
        client_id = input("Enter your Spotify Client ID: ").strip()
    if not client_secret:
        client_secret = input("Enter your Spotify Client Secret: ").strip()

    return client_id, client_secret, redirect_uri


def authorize_user(client_id, redirect_uri):
    global auth_code
    scopes = "playlist-modify-public playlist-modify-private"
    auth_url = (
        f"https://accounts.spotify.com/authorize?"
        f"client_id={urllib.parse.quote(client_id)}&"
        f"response_type=code&"
        f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
        f"scope={urllib.parse.quote(scopes)}"
    )

    print("\n" + "="*60)
    print("STEP 1: Open this link in your browser to log in & authorize:")
    print(auth_url)
    print("="*60 + "\n")
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    import threading
    server_address = ('0.0.0.0', 8888)
    httpd = None
    try:
        httpd = HTTPServer(server_address, OAuthCallbackHandler)
        httpd.timeout = 1
        def run_server():
            while auth_code is None:
                httpd.handle_request()
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
    except Exception:
        pass

    print("After authorizing:")
    print("• If you are running locally, the browser will redirect automatically.")
    print("• Otherwise, copy the full redirected URL from your browser address bar and paste it below.")
    print("  (Even if the page says 'site can't be reached', the URL in your address bar has the code!)\n")
    
    user_input = input("Paste redirected URL (or press Enter if redirected automatically): ").strip()
    if user_input:
        if 'code=' in user_input:
            query = urllib.parse.urlparse(user_input).query or user_input
            params = urllib.parse.parse_qs(query)
            if 'code' in params:
                auth_code = params['code'][0]
        else:
            auth_code = user_input

    while auth_code is None:
        import time
        time.sleep(0.5)

    return auth_code


def exchange_code_for_token(client_id, client_secret, code, redirect_uri):
    import base64
    token_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }).encode()

    req = urllib.request.Request(
        token_url,
        data=data,
        headers={
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode())
        return tokens['access_token']


def spotify_api_request(endpoint, token, method='GET', payload=None):
    url = f"https://api.spotify.com/v1{endpoint}"
    data = json.dumps(payload).encode() if payload else None
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def search_track(token, track_title, artist):
    query = f"track:{track_title} artist:{artist}"
    endpoint = f"/search?q={urllib.parse.quote(query)}&type=track&limit=1"
    try:
        data = spotify_api_request(endpoint, token)
        tracks = data.get('tracks', {}).get('items', [])
        if tracks:
            return tracks[0]['uri'], tracks[0]['name'], tracks[0]['artists'][0]['name']
    except Exception:
        pass
    
    fallback_query = f"{track_title} {artist}"
    endpoint = f"/search?q={urllib.parse.quote(fallback_query)}&type=track&limit=1"
    try:
        data = spotify_api_request(endpoint, token)
        tracks = data.get('tracks', {}).get('items', [])
        if tracks:
            return tracks[0]['uri'], tracks[0]['name'], tracks[0]['artists'][0]['name']
    except Exception:
        pass

    return None, None, None


def main():
    print("==================================================")
    print(" DWTS Season 35 Spotify Playlist Creator")
    print("==================================================")
    
    client_id, client_secret, redirect_uri = get_credentials()
    if not client_id or not client_secret:
        print("Error: Spotify Client ID and Client Secret are required.")
        sys.exit(1)

    code = authorize_user(client_id, redirect_uri)
    print("Exchanging authorization code for Spotify access token...")
    token = exchange_code_for_token(client_id, client_secret, code, redirect_uri)

    me = spotify_api_request('/me', token)
    user_id = me['id']
    user_name = me.get('display_name', user_id)
    print(f"Authenticated as: {user_name} ({user_id})\n")

    created_playlists = []

    for p_def in PLAYLIST_DEFS:
        csv_file = os.path.join(PLAYLIST_DIR, p_def['file'])
        if not os.path.exists(csv_file):
            print(f"Skipping {p_def['file']} (file not found)")
            continue

        print(f"\nCreating playlist: \"{p_def['name']}\"...")
        pl_data = spotify_api_request(
            f"/users/{user_id}/playlists",
            token,
            method='POST',
            payload={
                "name": p_def['name'],
                "description": p_def['description'],
                "public": True
            }
        )
        playlist_id = pl_data['id']
        playlist_url = pl_data['external_urls']['spotify']

        track_uris = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:] # skip header
            for line in lines:
                parts = [p.strip('"\n\r') for p in line.split('","')]
                if len(parts) >= 2:
                    title, artist = parts[0], parts[1]
                    uri, found_title, found_artist = search_track(token, title, artist)
                    if uri:
                        track_uris.append(uri)
                        print(f"  ✓ Found: {title} · {artist} -> {found_title} ({found_artist})")
                    else:
                        print(f"  ✗ Not found on Spotify: {title} · {artist}")

        if track_uris:
            # Spotify allows adding up to 100 tracks per call
            spotify_api_request(
                f"/playlists/{playlist_id}/items",
                token,
                method='POST',
                payload={"uris": track_uris}
            )
            print(f"Added {len(track_uris)} songs to playlist!")

        created_playlists.append((p_def['name'], playlist_url))

    print("\n==================================================")
    print(" ALL PLAYLISTS CREATED SUCCESSFULLY!")
    print("==================================================")
    for name, url in created_playlists:
        print(f"• {name}:\n  {url}\n")


if __name__ == '__main__':
    main()
