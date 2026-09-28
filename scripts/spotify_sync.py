#!/usr/bin/env python3
"""
Spotify Playlist Sync Module for DWTS Season 35.
Handles OAuth token lifecycle, playlist creation, cover art upload,
and real-time song reordering to match show broadcast order.
"""

import os
import sys
import json
import time
import base64
import urllib.request
import urllib.parse
from datetime import datetime, timezone

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENV_FILE = os.path.join(WORKSPACE_DIR, '.env')
TOKENS_FILE = os.path.join(WORKSPACE_DIR, '.spotify_tokens.json')
PLAYLISTS_FILE = os.path.join(WORKSPACE_DIR, 'spotify_playlists.json')
CACHE_FILE = os.path.join(WORKSPACE_DIR, '.spotify_track_cache.json')
TRACKS_FILE = os.path.join(WORKSPACE_DIR, 'spotify_tracks.json')
COVERS_DIR = os.path.join(WORKSPACE_DIR, 'assets', 'playlist_covers')

SCOPES = "playlist-modify-public playlist-modify-private ugc-image-upload"


def load_env():
    """Loads environment variables from .env if present."""
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v


def get_credentials():
    load_env()
    client_id = os.environ.get('SPOTIPY_CLIENT_ID') or os.environ.get('SPOTIFY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET') or os.environ.get('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI') or os.environ.get('SPOTIFY_REDIRECT_URI') or 'http://127.0.0.1:8888/callback'
    return client_id, client_secret, redirect_uri


def load_tokens():
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_tokens(tokens):
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2)


def refresh_access_token(client_id, client_secret, refresh_token):
    token_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    data = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
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
        res = json.loads(resp.read().decode())
        tokens = load_tokens() or {}
        tokens['access_token'] = res['access_token']
        tokens['expires_at'] = int(time.time()) + res.get('expires_in', 3600)
        if 'refresh_token' in res:
            tokens['refresh_token'] = res['refresh_token']
        save_tokens(tokens)
        return tokens['access_token']


def exchange_code_for_tokens(client_id, client_secret, code, redirect_uri):
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
        res = json.loads(resp.read().decode())
        tokens = {
            'access_token': res['access_token'],
            'refresh_token': res['refresh_token'],
            'expires_at': int(time.time()) + res.get('expires_in', 3600)
        }
        save_tokens(tokens)
        return tokens


def get_valid_access_token():
    client_id, client_secret, _ = get_credentials()
    if not client_id or not client_secret:
        return None

    tokens = load_tokens()
    refresh_token = (tokens.get('refresh_token') if tokens else None) or os.environ.get('SPOTIPY_REFRESH_TOKEN') or os.environ.get('SPOTIFY_REFRESH_TOKEN')
    if not refresh_token:
        return None

    if tokens and tokens.get('access_token') and int(time.time()) < tokens.get('expires_at', 0) - 60:
        return tokens['access_token']

    try:
        return refresh_access_token(client_id, client_secret, refresh_token)
    except Exception as e:
        print(f"[Spotify] Error refreshing token: {e}")
        return None


def spotify_api(endpoint, token, method='GET', payload=None, is_image=False, raw_body=None):
    url = f"https://api.spotify.com/v1{endpoint}"
    headers = {'Authorization': f'Bearer {token}'}

    if is_image:
        headers['Content-Type'] = 'image/jpeg'
        data = raw_body
    elif payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode('utf-8')
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            if not body:
                return {}
            return json.loads(body.decode('utf-8'))
    except urllib.error.HTTPError as err:
        err_msg = err.read().decode('utf-8', errors='ignore')
        raise Exception(f"Spotify API Error {err.code} on {endpoint}: {err_msg}")


def load_track_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_track_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)
    tracks = {}
    for k, uri in cache.items():
        track_id = uri.split(':')[-1]
        track_url = f"https://open.spotify.com/track/{track_id}"
        tracks[k] = track_url
        parts = k.split(' --- ')
        if len(parts) == 2:
            title, artist = parts[0], parts[1]
            simple_key = f"{title} {artist}".replace('&', 'and').replace('feat.', '').replace('  ', ' ').strip()
            tracks[simple_key] = track_url
    with open(TRACKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2)


def search_track_cached(token, title, artist):
    cache = load_track_cache()
    key = f"{title.strip().lower()} --- {artist.strip().lower()}"
    if key in cache:
        return cache[key]

    queries = [
        f"track:{title} artist:{artist}",
        f"{title} {artist}"
    ]

    for q in queries:
        try:
            res = spotify_api(f"/search?q={urllib.parse.quote(q)}&type=track&limit=1", token)
            items = res.get('tracks', {}).get('items', [])
            if items:
                uri = items[0]['uri']
                cache[key] = uri
                save_track_cache(cache)
                return uri
        except Exception:
            pass

    return None


def load_playlists_registry():
    if os.path.exists(PLAYLISTS_FILE):
        try:
            with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_playlists_registry(reg):
    with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reg, f, indent=2)


def upload_cover_image(token, playlist_id, image_filename):
    cover_path = os.path.join(COVERS_DIR, image_filename)
    if not os.path.exists(cover_path):
        return False
    try:
        with open(cover_path, 'rb') as f:
            b64_data = base64.b64encode(f.read())
        spotify_api(f"/playlists/{playlist_id}/images", token, method='PUT', is_image=True, raw_body=b64_data)
        return True
    except Exception as e:
        print(f"[Spotify] Cover upload warning for playlist {playlist_id}: {e}")
        return False


def sync_weekly_playlist(token, user_id, week_key, name, description, cover_file, ordered_tracks):
    """
    Creates or updates a Spotify playlist, rearranging songs to match exact show order,
    and sets the themed cover art and title.
    ordered_tracks: list of dicts with 'title' and 'artist'
    """
    registry = load_playlists_registry()
    pl_info = registry.get(week_key)

    track_uris = []
    for t in ordered_tracks:
        uri = search_track_cached(token, t['title'], t['artist'])
        if uri and uri not in track_uris:
            track_uris.append(uri)

    playlist_id = pl_info.get('id') if pl_info else None

    # Check if playlist exists or create new
    if not playlist_id:
        print(f"[Spotify] Creating playlist: \"{name}\"...")
        res = spotify_api(
            "/me/playlists",
            token,
            method='POST',
            payload={
                "name": name,
                "description": description,
                "public": True
            }
        )
        playlist_id = res['id']
        playlist_url = res['external_urls']['spotify']
        registry[week_key] = {
            'id': playlist_id,
            'url': playlist_url,
            'name': name
        }
        save_playlists_registry(registry)
        upload_cover_image(token, playlist_id, cover_file)
    else:
        # Update name and description if needed
        try:
            spotify_api(
                f"/playlists/{playlist_id}",
                token,
                method='PUT',
                payload={"name": name, "description": description}
            )
        except Exception:
            pass

    # Replace / Reorder all tracks in exact show broadcast sequence
    if track_uris:
        try:
            # PUT replaces all items in the playlist with the exact order in track_uris
            spotify_api(
                f"/playlists/{playlist_id}/items",
                token,
                method='PUT',
                payload={"uris": track_uris[:100]}
            )
            print(f"[Spotify] ✓ Synced \"{name}\": {len(track_uris)} songs in exact show sequence.")
        except Exception as e:
            print(f"[Spotify] Error updating tracks for {name}: {e}")

    # Ensure cover image is applied
    upload_cover_image(token, playlist_id, cover_file)
    return registry[week_key]['url']


def parse_song_string(song_raw):
    """Splits '“Song Title” · Artist Name' into title and artist."""
    if not song_raw or song_raw == 'TBA':
        return None, None
    s = song_raw.replace('“', '').replace('”', '').replace('"', '')
    if '·' in s:
        parts = s.split('·', 1)
        return parts[0].strip(), parts[1].strip()
    return s.strip(), ''


def sync_all_dwts_playlists(week_lineups, current_week_num=3):
    """
    Called by update_cheat_sheet.py or standalone to sync all playlists.
    """
    token = get_valid_access_token()
    if not token:
        print("[Spotify Sync] No valid Spotify authorization token found. Skipping playlist sync.")
        return False

    try:
        me = spotify_api('/me', token)
        user_id = me['id']
    except Exception as e:
        print(f"[Spotify Sync] Authentication check failed: {e}")
        return False

def ensure_cover_image(wk_num, theme_title):
    os.makedirs(COVERS_DIR, exist_ok=True)
    filename = f"week_{wk_num}.jpg" if isinstance(wk_num, int) else f"{wk_num}.jpg"
    out_path = os.path.join(COVERS_DIR, filename)
    if os.path.exists(out_path):
        return filename

    accent = (239, 206, 130)
    template_path = os.path.join(COVERS_DIR, 'template_ballroom_mirrorball.jpg')

    try:
        from PIL import Image, ImageDraw, ImageFont

        FONT_SERIF_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
        FONT_SANS_BOLD = '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'

        if os.path.exists(template_path):
            img = Image.open(template_path).resize((640, 640)).convert('RGBA')
            overlay = Image.new('RGBA', (640, 640), (10, 10, 14, 160))
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)
        else:
            img = Image.new('RGB', (640, 640), (15, 15, 16))
            draw = ImageDraw.Draw(img)
            for y in range(640):
                ratio = y / 640.0
                r = int(35 * (1 - ratio) + 15 * ratio)
                g = int(30 * (1 - ratio) + 15 * ratio)
                b = int(20 * (1 - ratio) + 16 * ratio)
                draw.line([(0, y), (640, y)], fill=(r, g, b))

        # Border & corner diamonds
        draw.rectangle([(24, 24), (616, 616)], outline=accent, width=2)
        draw.rectangle([(32, 32), (608, 608)], outline=(accent[0]//2, accent[1]//2, accent[2]//2), width=1)
        for cx, cy in [(24, 24), (616, 24), (24, 616), (616, 616)]:
            draw.polygon([(cx, cy-6), (cx+6, cy), (cx, cy+6), (cx-6, cy)], fill=accent)

        if os.path.exists(FONT_SERIF_BOLD):
            font_top = ImageFont.truetype(FONT_SERIF_BOLD, 22)
            font_kicker = ImageFont.truetype(FONT_SANS_BOLD, 17)
            font_title = ImageFont.truetype(FONT_SERIF_BOLD, 46)
            font_sub = ImageFont.truetype(FONT_SANS_BOLD, 16)
        else:
            font_top = ImageFont.load_default(size=22)
            font_kicker = ImageFont.load_default(size=17)
            font_title = ImageFont.load_default(size=44)
            font_sub = ImageFont.load_default(size=16)

        show_text = 'DANCING WITH THE STARS'
        bbox_show = draw.textbbox((0, 0), show_text, font=font_top)
        draw.text(((640 - (bbox_show[2] - bbox_show[0]))//2 + 2, 72), show_text, fill=(0, 0, 0), font=font_top)
        draw.text(((640 - (bbox_show[2] - bbox_show[0]))//2, 70), show_text, fill=(255, 255, 255), font=font_top)

        kicker_text = f'SEASON 35 · WEEK {wk_num}' if isinstance(wk_num, int) else None
        y_divider = 112
        if kicker_text:
            bbox_k = draw.textbbox((0, 0), kicker_text, font=font_kicker)
            draw.text(((640 - (bbox_k[2] - bbox_k[0]))//2 + 1, 107), kicker_text, fill=(0, 0, 0), font=font_kicker)
            draw.text(((640 - (bbox_k[2] - bbox_k[0]))//2, 106), kicker_text, fill=accent, font=font_kicker)
            y_divider = 138

        draw.line([(140, y_divider), (500, y_divider)], fill=accent, width=2)
        draw.polygon([(320, y_divider-6), (326, y_divider), (320, y_divider+6), (314, y_divider)], fill=accent)

        title_upper = (theme_title or f'Week {wk_num}').upper()
        words = title_upper.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(' '.join(cur_line)) > 14:
                lines.append(' '.join(cur_line))
                cur_line = []
        if cur_line:
            lines.append(' '.join(cur_line))
        if not lines:
            lines = [title_upper]

        y_text = 240 if len(lines) > 1 else 275
        for l in lines:
            bbox_l = draw.textbbox((0, 0), l, font=font_title)
            w_l = bbox_l[2] - bbox_l[0]
            draw.text(((640 - w_l)//2 + 3, y_text + 3), l, fill=(0, 0, 0), font=font_title)
            draw.text(((640 - w_l)//2, y_text), l, fill=(255, 255, 255), font=font_title)
            y_text += 58

        draw.line([(170, 480), (470, 480)], fill=(accent[0]//2, accent[1]//2, accent[2]//2), width=1)
        sub_text = 'COMPLETE SOUNDTRACK'
        bbox_sub = draw.textbbox((0, 0), sub_text, font=font_sub)
        draw.text(((640 - (bbox_sub[2] - bbox_sub[0]))//2, 510), sub_text, fill=accent, font=font_sub)

        img.convert('RGB').save(out_path, format='JPEG', quality=92, optimize=True)
        print(f"[Spotify] Generated new mirrorball cover artwork for Week {wk_num} ({theme_title}) -> {out_path}")
        return filename
    except Exception as e:
        print(f"[Spotify] Could not generate cover for {theme_title}: {e}")
        return "season_35.jpg" if os.path.exists(os.path.join(COVERS_DIR, "season_35.jpg")) else None


def sync_all_dwts_playlists(week_lineups, current_week_num=3):
    token = get_valid_access_token()
    if not token:
        print("[Spotify Sync] No valid Spotify authorization token found. Skipping playlist sync.")
        return False

    try:
        me = spotify_api('/me', token)
        user_id = me['id']
    except Exception as e:
        print(f"[Spotify Sync] Authentication check failed: {e}")
        return False

    all_season_tracks = []

    # Pre-configured themes for early weeks, dynamic fallback for all future weeks
    KNOWN_THEMES = {
        1: {
            'name': 'DWTS Season 35 · Week 1: Premiere (Birth-Year #1 Hits)',
            'desc': 'All songs from Dancing with the Stars Season 35 Week 1 (Premiere Night), synced in performance order.',
            'cover': 'week_1.jpg'
        },
        2: {
            'name': 'DWTS Season 35 · Week 2: Viral Hits Night',
            'desc': 'All songs from Dancing with the Stars Season 35 Week 2 (Viral Hits Night), synced in performance order.',
            'cover': 'week_2.jpg'
        },
        3: {
            'name': 'DWTS Season 35 · Week 3: Yacht Rock Night',
            'desc': 'All songs from Dancing with the Stars Season 35 Week 3 (Yacht Rock Night), synced in performance order.',
            'cover': 'week_3.jpg'
        }
    }

    for wk_num in sorted(week_lineups.keys()):
        info = week_lineups.get(wk_num)
        if not info:
            continue
        couples = info.get('couples', [])
        ordered_songs = []
        for c in couples:
            title, artist = parse_song_string(c.get('song', ''))
            if title:
                ordered_songs.append({'title': title, 'artist': artist, 'couple': c.get('name')})
                all_season_tracks.append({'title': title, 'artist': artist})

        if not ordered_songs:
            continue

        theme_name = info.get('theme', f'Week {wk_num}')
        if wk_num in KNOWN_THEMES:
            pl_name = KNOWN_THEMES[wk_num]['name']
            pl_desc = KNOWN_THEMES[wk_num]['desc']
            cover_file = KNOWN_THEMES[wk_num]['cover']
        else:
            pl_name = f'DWTS Season 35 · Week {wk_num}: {theme_name}'
            pl_desc = f'All songs from Dancing with the Stars Season 35 Week {wk_num} ({theme_name}), synced in performance order.'
            cover_file = ensure_cover_image(wk_num, theme_name)

        sync_weekly_playlist(
            token,
            user_id,
            f'week_{wk_num}',
            pl_name,
            pl_desc,
            cover_file,
            ordered_songs
        )

    # Also sync Master Season 35 soundtrack
    if all_season_tracks:
        sync_weekly_playlist(
            token,
            user_id,
            'season_35',
            'DWTS Season 35 · Complete Soundtrack (All Weeks)',
            'Every competitive song danced across Dancing with the Stars Season 35, updated weekly.',
            'season_35.jpg',
            all_season_tracks
        )

    return True


if __name__ == '__main__':
    load_env()
    client_id, client_secret, redirect_uri = get_credentials()
    if len(sys.argv) > 1 and sys.argv[1] == '--auth':
        auth_url = (
            f"https://accounts.spotify.com/authorize?"
            f"client_id={urllib.parse.quote(client_id)}&"
            f"response_type=code&"
            f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
            f"scope={urllib.parse.quote(SCOPES)}"
        )
        print("Please authorize the Spotify app by visiting this URL in your browser:")
        print(auth_url)
        code_input = input("\nEnter the redirected URL or code from the address bar: ").strip()
        if 'code=' in code_input:
            params = urllib.parse.parse_qs(urllib.parse.urlparse(code_input).query)
            code = params.get('code', [code_input])[0]
        else:
            code = code_input
        exchange_code_for_tokens(client_id, client_secret, code, redirect_uri)
        print("Authorization successful! Tokens saved.")
    else:
        print("Spotify Sync utility ready.")
