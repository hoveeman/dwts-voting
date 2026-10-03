#!/usr/bin/env python3
"""
Automated updater for DWTS Season 35 Cheat Sheet and Voting Shortcut.
Scrapes latest episode scores, songs, dance styles, and eliminations from Wikipedia,
dynamically computes fantasy tiers, momentum tags, and sleeper picks,
updates index.html, dancers.json, and dancers.txt, and validates the output.
"""

import sys
import os
import re
import html
import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HTML_FILE = os.path.join(WORKSPACE_DIR, 'index.html')
DANCERS_JSON = os.path.join(WORKSPACE_DIR, 'dancers.json')
DANCERS_TXT = os.path.join(WORKSPACE_DIR, 'dancers.txt')
VALIDATE_SCRIPT = os.path.join(WORKSPACE_DIR, 'scripts', 'validate_cheat_sheet.py')

WIKI_URL = 'https://en.wikipedia.org/api/rest_v1/page/html/Dancing_with_the_Stars_(American_TV_series)_season_35'
WIKI_FALLBACK_URL = 'https://en.wikipedia.org/wiki/Dancing_with_the_Stars_(American_TV_series)_season_35'

# Master registry of Season 35 couples with static profile metadata
COUPLE_REGISTRY = {
    "Maura Higgins": {
        "short": "Maura & Mark",
        "celeb_first": "Maura",
        "pro_first": "Mark",
        "proName": "Mark Ballas",
        "age": 35,
        "mirrorballs": 3,
        "photo": "maura-higgins-mark-ballas.jpg",
        "trait": "No dance experience",
        "social_reach_num": 6.0,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 25,
        "outlook": "Mark’s three Mirrorballs and their immense reality fandom make the partnership built for a deep finale run.",
        "bio": "The <i>Love Island</i> star and TV personality",
        "vote_code": "Maura",
        "initial_rank": 1
    },
    "Harry Shum Jr.": {
        "short": "Harry & Jenna",
        "celeb_first": "Harry",
        "pro_first": "Jenna",
        "proName": "Jenna Johnson",
        "age": 44,
        "mirrorballs": 2,
        "photo": "harry-shum-jr-jenna-johnson.jpg",
        "trait": "Pro dance background",
        "social_reach_num": 3.5,
        "is_athlete": False,
        "is_dancer": True,
        "baseline_market_prob": 20,
        "outlook": "Possesses the highest technical ceiling in the cast; the only obvious challenge is overcoming ringer perception.",
        "bio": "The <i>Glee</i> and <i>Crazy Rich Asians</i> actor",
        "vote_code": "Harry",
        "initial_rank": 2
    },
    "Jenna Dewan": {
        "short": "Jenna & Val",
        "celeb_first": "Jenna",
        "pro_first": "Val",
        "proName": "Val Chmerkovskiy",
        "age": 45,
        "mirrorballs": 3,
        "photo": "jenna-dewan-val-chmerkovskiy.jpg",
        "trait": "Pro dance background",
        "social_reach_num": 12.0,
        "is_athlete": False,
        "is_dancer": True,
        "baseline_market_prob": 22,
        "outlook": "A true professional dancer paired with a three-time champion. Her high scoring floor makes her an elite anchor.",
        "bio": "The <i>Step Up</i> actress and dancer",
        "vote_code": "Jenna",
        "initial_rank": 3
    },
    "Ezra Frech": {
        "short": "Ezra & Daniella",
        "celeb_first": "Ezra",
        "pro_first": "Daniella",
        "proName": "Daniella Karagach",
        "age": 21,
        "mirrorballs": 1,
        "photo": "ezra-frech-daniella-karagach.jpg",
        "trait": "Paralympic champion",
        "social_reach_num": 1.5,
        "is_athlete": True,
        "is_dancer": False,
        "baseline_market_prob": 17,
        "outlook": "Elite athletic body awareness combined with a pro renowned for unlocking dynamic, unconventional choreography.",
        "bio": "The Paralympic track and field champion",
        "vote_code": "Ezra",
        "initial_rank": 4
    },
    "Amber Glenn": {
        "short": "Amber & Pasha",
        "celeb_first": "Amber",
        "pro_first": "Pasha",
        "proName": "Pasha Pashkov",
        "age": 26,
        "mirrorballs": 0,
        "photo": "amber-glenn-pasha-pashkov.jpg",
        "trait": "U.S. figure skater",
        "social_reach_num": 3.9,
        "is_athlete": True,
        "is_dancer": False,
        "baseline_market_prob": 14,
        "outlook": "Figure-skating musicality, rotational speed, and Olympic visibility provide a reliable scoring floor.",
        "bio": "The U.S. champion figure skater",
        "vote_code": "Amber",
        "initial_rank": 5
    },
    "Julia Stiles": {
        "short": "Julia & Ezra",
        "celeb_first": "Julia",
        "pro_first": "Ezra",
        "proName": "Ezra Sosa",
        "age": 45,
        "mirrorballs": 0,
        "photo": "julia-stiles-ezra-sosa.jpg",
        "trait": "Nostalgia icon",
        "social_reach_num": 1.7,
        "is_athlete": False,
        "is_dancer": True,
        "baseline_market_prob": 10,
        "outlook": "Deep cross-generational nostalgia, screen dance memory, and the season’s cleanest motivational storyline.",
        "bio": "The <i>Save the Last Dance</i> and <i>10 Things I Hate About You</i> actress",
        "vote_code": "Julia",
        "initial_rank": 6
    },
    "Tyler Cameron": {
        "short": "Tyler & Sharna",
        "celeb_first": "Tyler",
        "pro_first": "Sharna",
        "proName": "Sharna Burgess",
        "age": 33,
        "mirrorballs": 1,
        "photo": "tyler-cameron-sharna-burgess.jpg",
        "trait": "Bachelor Nation",
        "social_reach_num": 3.2,
        "is_athlete": True,
        "is_dancer": False,
        "baseline_market_prob": 8,
        "outlook": "Athletic frame, broad reality fanbase, and a returning champion pro give him higher upside than middle-pack scores suggest.",
        "bio": "The <i>Bachelorette</i> fan favorite and television personality",
        "vote_code": "Tyler",
        "initial_rank": 7
    },
    "Jackson Olson": {
        "short": "Jackson & Emma",
        "celeb_first": "Jackson",
        "pro_first": "Emma",
        "proName": "Emma Slater",
        "age": 28,
        "mirrorballs": 1,
        "photo": "jackson-olson-emma-slater.jpg",
        "trait": "3M+ social reach",
        "social_reach_num": 3.2,
        "is_athlete": True,
        "is_dancer": False,
        "baseline_market_prob": 6,
        "outlook": "Elite social reach and Banana Ball entertainment value give him an exceptional public voting cushion.",
        "bio": "The Savannah Bananas baseball star and content creator",
        "vote_code": "Jackson",
        "initial_rank": 8
    },
    "Taylor Hanson": {
        "short": "Taylor & Britt",
        "celeb_first": "Taylor",
        "pro_first": "Britt",
        "proName": "Britt Stewart",
        "age": 43,
        "mirrorballs": 0,
        "photo": "taylor-hanson-britt-stewart.jpg",
        "trait": "Musician timing",
        "social_reach_num": 0.5,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 1,
        "outlook": "Natural musical rhythm and a dedicated multi-decade fan community provide durability into themed music weeks.",
        "bio": "The Hanson musician and singer-songwriter was eliminated after a foxtrot to “What a Fool Believes” by The Doobie Brothers that scored 18.",
        "vote_code": "Taylor",
        "initial_rank": 9,
        "eliminated_date": "September 29, 2026",
        "eliminated_datetime": "2026-09-29",
        "eliminated_order": "4th eliminated",
        "eliminated_week_theme": "Week 3, Yacht Rock Night"
    },
    "Connor Wood": {
        "short": "Connor & Rylee",
        "celeb_first": "Connor",
        "pro_first": "Rylee",
        "proName": "Rylee Arnold",
        "age": 31,
        "mirrorballs": 0,
        "photo": "connor-wood-rylee-arnold.jpg",
        "trait": "Comedy podcast",
        "social_reach_num": 1.5,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 4,
        "outlook": "Rapidly growing digital following and podcast listener loyalty keep him safe while his technique develops.",
        "bio": "The comedian and podcast host (Fibula)",
        "vote_code": "Connor",
        "initial_rank": 10
    },
    "Ciara Miller": {
        "short": "Ciara & Brandon",
        "celeb_first": "Ciara",
        "pro_first": "Brandon",
        "proName": "Brandon Armstrong",
        "age": 30,
        "mirrorballs": 0,
        "photo": "ciara-miller-brandon-armstrong.jpg",
        "trait": "Bravo fandom",
        "social_reach_num": 1.0,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 7,
        "outlook": "Bravo and Traitors viewers are notoriously reliable voters; steady technical growth can push her deep into the bracket.",
        "bio": "The <i>Summer House</i> and <i>The Traitors</i> star",
        "vote_code": "Ciara",
        "initial_rank": 11
    },
    "Tatyana Ali": {
        "short": "Tatyana & Jan",
        "celeb_first": "Tatyana",
        "pro_first": "Jan",
        "proName": "Jan Ravnik",
        "age": 47,
        "mirrorballs": 0,
        "photo": "tatyana-ali-jan-ravnik.jpg",
        "trait": "Fresh Prince icon",
        "social_reach_num": 2.5,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 4,
        "outlook": "The Alfonso Ribeiro reunion and cross-generational warmth generate huge audience affection and voting momentum.",
        "bio": "The <i>Fresh Prince of Bel-Air</i> actress and singer",
        "vote_code": "Tatyana",
        "initial_rank": 12
    },
    "Guillermo Rodriguez": {
        "short": "Guillermo & Witney",
        "celeb_first": "Guillermo",
        "pro_first": "Witney",
        "proName": "Witney Carson",
        "age": 55,
        "mirrorballs": 2,
        "photo": "guillermo-rodriguez-witney-carson.jpg",
        "trait": "Fan favorite",
        "social_reach_num": 4.5,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 2,
        "outlook": "Carries a modest scoring floor, but reigning champion Witney Carson and Jimmy Kimmel's nightly ABC audience provide an impenetrable fan voting shield.",
        "bio": "The <i>Jimmy Kimmel Live!</i> personality",
        "vote_code": "Guillermo",
        "initial_rank": 13
    },
    "Giada De Laurentiis": {
        "short": "Giada & Alan",
        "celeb_first": "Giada",
        "pro_first": "Alan",
        "proName": "Alan Bersten",
        "age": 56,
        "mirrorballs": 1,
        "photo": "giada-de-laurentiis-alan-bersten.jpg",
        "baseline_market_prob": 1,
        "bio": "The celebrity chef was eliminated after a salsa to “Bella Ciao” by Becky G that scored 12.",
        "vote_code": "Giada",
        "eliminated_date": "September 22, 2026",
        "eliminated_datetime": "2026-09-22",
        "eliminated_order": "3rd eliminated",
        "eliminated_week_theme": "Week 2, Viral Hits Night"
    },
    "Sarah Jane Nader": {
        "short": "Sarah Jane & Hailey",
        "celeb_first": "Sarah Jane",
        "pro_first": "Hailey",
        "proName": "Hailey Bills",
        "age": 25,
        "mirrorballs": 0,
        "photo": "sarah-jane-nader-hailey-bills.jpg",
        "photo_position": "center 40%",
        "baseline_market_prob": 1,
        "bio": "The <i>Love Thy Nader</i> star was eliminated after a jive to “Sk8er Boi” by Avril Lavigne that scored 14.",
        "vote_code": "Sarah",
        "eliminated_date": "September 16, 2026",
        "eliminated_datetime": "2026-09-16",
        "eliminated_order": "2nd eliminated",
        "eliminated_week_theme": "Week 1, Premiere Night 2"
    },
    "Conner Leavitt": {
        "short": "Conner & Adele",
        "celeb_first": "Conner",
        "pro_first": "Adele",
        "proName": "Adele Zaikman",
        "age": 29,
        "mirrorballs": 0,
        "photo": "conner-leavitt-adele-zaikman.jpg",
        "baseline_market_prob": 1,
        "bio": "The <i>Secret Lives of Mormon Wives</i> cast member was eliminated after a salsa to “Whoomp! (There It Is)” by Tag Team that scored 12.",
        "vote_code": "Conner",
        "eliminated_date": "September 15, 2026",
        "eliminated_datetime": "2026-09-15",
        "eliminated_order": "1st eliminated",
        "eliminated_week_theme": "Week 1, Premiere Night 1"
    }
}

def ordinal(n):
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def mirrorball_label(count):
    return f"{count} Mirrorball{'s' if count != 1 else ''}"

def count_to_word(n):
    words = {
        16: "Sixteen", 15: "Fifteen", 14: "Fourteen", 13: "Thirteen",
        12: "Twelve", 11: "Eleven", 10: "Ten", 9: "Nine",
        8: "Eight", 7: "Seven", 6: "Six", 5: "Five", 4: "Four",
        3: "Three", 2: "Two", 1: "One"
    }
    return words.get(n, str(n))

def get_spotify_track_url(song):
    if not song:
        return None
    tracks_file = os.path.join(WORKSPACE_DIR, 'spotify_tracks.json')
    if os.path.exists(tracks_file):
        try:
            with open(tracks_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            raw = song.replace('“', '').replace('”', '').replace('"', '').strip()
            if '·' in raw:
                title, artist = raw.split('·', 1)
                k1 = f"{title.strip().lower()} --- {artist.strip().lower()}"
                k2 = f"{title.strip().lower()} {artist.strip().lower()}".replace('&', 'and').replace('feat.', '').replace('  ', ' ').strip()
                if k1 in mapping:
                    return mapping[k1]
                if k2 in mapping:
                    return mapping[k2]
                title_clean = title.strip().lower()
                if title_clean in mapping:
                    return mapping[title_clean]
            else:
                k = raw.lower().replace('&', 'and').replace('feat.', '').replace('  ', ' ').strip()
                if k in mapping:
                    return mapping[k]
                for mk, url in mapping.items():
                    if mk == k or mk.startswith(f"{k} ---") or mk.startswith(f"{k} "):
                        return url
        except Exception:
            pass
    return None

def make_music_links_html(song, indent="              "):
    if not song or song == 'TBA' or not song.strip():
        return ''
    clean_text = song.replace('“', '').replace('”', '').replace('"', '').replace('&amp;', '&').replace('·', ' ')
    clean_text = ' '.join(clean_text.split())
    direct_url = get_spotify_track_url(song)
    if direct_url:
        spotify_url = direct_url
    else:
        encoded = urllib.parse.quote(clean_text)
        spotify_url = f"https://open.spotify.com/search/{encoded}"

    clean_attr = html.escape(clean_text)
    spotify_svg = '<svg viewBox="0 0 24 24" class="music-icon" aria-hidden="true"><path fill="currentColor" d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.503 17.308c-.218.357-.681.472-1.038.254-2.853-1.743-6.444-2.138-10.673-1.171-.408.093-.812-.162-.905-.57-.093-.408.162-.812.57-.905 4.634-1.059 8.604-.614 11.792 1.354.357.218.472.681.254 1.038zm1.47-3.267c-.275.447-.862.59-1.309.315-3.265-2.008-8.243-2.59-12.106-1.417-.502.152-1.034-.136-1.186-.638-.152-.502.136-1.034.638-1.186 4.417-1.341 9.907-.7 13.648 1.603.447.275.59.862.315 1.309zm.126-3.41c-3.916-2.325-10.374-2.54-14.116-1.403-.6.182-1.24-.165-1.422-.765-.182-.6.165-1.24.765-1.422 4.301-1.306 11.431-1.057 15.932 1.616.54.321.716 1.02.395 1.56-.321.54-1.02.716-1.56.395z"/></svg>'

    return (
        f'\n{indent}<div class="music-links">'
        f'<a href="{spotify_url}" target="_blank" rel="noopener noreferrer" class="music-btn spotify-btn" title="Listen to {clean_attr} on Spotify" aria-label="Listen to {clean_attr} on Spotify">{spotify_svg}<span>Spotify</span></a>'
        f'</div>'
    )


def match_couple(raw_text):
    clean = re.sub(r'\[.*?\]|\{.*?\}|\".*?\"', '', raw_text).strip().lower()
    for name, data in COUPLE_REGISTRY.items():
        celeb = data["celeb_first"].lower()
        pro = data["pro_first"].lower()
        if (celeb in clean and pro in clean) or (name.lower() in clean):
            return name
    return None

def fetch_prediction_market_data():
    """
    Queries open, unauthenticated public REST API of Kalshi for:
    1. Official DWTS Season 35 Winner series:
       https://kalshi.com/markets/kxdancingwiththestars/who-will-win-dancing-with-the-stars/kxdancingwiththestars-26dec31
       Series ticker: KXDANCINGWITHTHESTARS
    2. Official DWTS Season 35 Weekly Elimination series:
       https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXDWTSELIMINATION&status=open
       Series ticker: KXDWTSELIMINATION
    Returns dict: {'winner': winner_odds, 'elimination': elim_odds}
    """
    winner_odds = {}
    elim_odds = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    # 1. Query official Kalshi series contract for Season 35 winner
    try:
        url = 'https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXDANCINGWITHTHESTARS'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for m in data.get('markets', []):
                participant = m.get('custom_strike', {}).get('Participant') or m.get('yes_sub_title') or m.get('title', '')
                matched_name = match_couple(participant)
                if not matched_name:
                    for name in COUPLE_REGISTRY:
                        if name.lower() in participant.lower() or COUPLE_REGISTRY[name]['celeb_first'].lower() in participant.lower():
                            matched_name = name
                            break
                if matched_name:
                    price_str = m.get('last_price_dollars') or m.get('yes_ask_dollars') or m.get('yes_bid_dollars')
                    if price_str and float(price_str) >= 0.01:
                        winner_odds[matched_name] = round(float(price_str) * 100)
    except Exception as e:
        print(f"Note: Kalshi winner series query: {e}")

    # 2. Query official Kalshi series contract for Weekly Elimination
    try:
        url = 'https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXDWTSELIMINATION&status=open'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for m in data.get('markets', []):
                participant = m.get('custom_strike', {}).get('Participant') or m.get('yes_sub_title') or m.get('title', '')
                matched_name = match_couple(participant)
                if not matched_name:
                    for name in COUPLE_REGISTRY:
                        if name.lower() in participant.lower() or COUPLE_REGISTRY[name]['celeb_first'].lower() in participant.lower():
                            matched_name = name
                            break
                if matched_name:
                    price_str = m.get('last_price_dollars') or m.get('yes_ask_dollars') or m.get('yes_bid_dollars')
                    if price_str:
                        elim_odds[matched_name] = round(float(price_str) * 100)
    except Exception as e:
        print(f"Note: Kalshi elimination series query: {e}")

    if winner_odds or elim_odds:
        print(f"Live Kalshi contracts retrieved: {len(winner_odds)} winner ({winner_odds}), {len(elim_odds)} weekly elimination ({elim_odds})")
    else:
        print("Note: No live Kalshi contracts retrieved; using baseline calibration.")
    return {'winner': winner_odds, 'elimination': elim_odds}

def fetch_wiki_html():
    req = urllib.request.Request(WIKI_URL, headers={'User-Agent': 'DWTSVotingCheatSheet/1.0 (contact: admin@example.com)'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"Warning: Primary Wikipedia REST API failed: {e}. Trying fallback...")
        fallback_req = urllib.request.Request(WIKI_FALLBACK_URL, headers={'User-Agent': 'DWTSVotingCheatSheet/1.0'})
        with urllib.request.urlopen(fallback_req, timeout=15) as resp:
            return resp.read().decode('utf-8')

def parse_wikipedia_data(raw_html):
    clean_html = re.sub(r'<sup\b[^>]*>.*?</sup>', '', raw_html, flags=re.DOTALL)
    clean_html = re.sub(r'<span\b[^>]*class=\"[^\"]*mw-ref[^\"]*\"[^>]*>.*?</span>', '', clean_html, flags=re.DOTALL)

    ep_dates = {}
    ep_themes = {}
    ep_pos = clean_html.find('id="Episodes"')
    if ep_pos != -1:
        t_start = clean_html.find('<table', ep_pos)
        t_end = clean_html.find('</table>', t_start)
        for r in re.findall(r'<tr[^>]*>(.*?)</tr>', clean_html[t_start:t_end+8], re.DOTALL):
            cells = [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.DOTALL)]
            if len(cells) >= 5 and cells[1].isdigit():
                ep_num = int(cells[1])
                title = cells[2].strip('"').strip()
                date_match = re.search(r'([A-Za-z]+\s+\d+,\s+\d{4})', cells[4].replace('\xa0', ' '))
                date_str = date_match.group(1) if date_match else cells[4]
                ep_dates[ep_num] = date_str
                ep_themes[ep_num] = title

    pattern = r'<h3[^>]*>Week\s+(\d+):\s*([^<]+)</h3>'
    weeks_matches = list(re.finditer(pattern, clean_html))
    
    couple_history = {name: [] for name in COUPLE_REGISTRY}
    eliminated_info = {}
    week_lineups = {}

    for i, m in enumerate(weeks_matches):
        w_num = int(m.group(1))
        w_theme = m.group(2).strip()
        theme_artist = None
        if w_theme.lower().endswith(' night'):
            cand = w_theme[:-6].strip()
            non_artist_themes = {'premiere', 'opening', 'viral hits', 'yacht rock', 'disney', 'halloween', 'most memorable year', 'latin', 'semifinals', 'finals', 'finale', 'quarterfinals'}
            if cand.lower() not in non_artist_themes:
                theme_artist = cand

        start_pos = m.start()
        end_pos = weeks_matches[i+1].start() if i+1 < len(weeks_matches) else clean_html.find('id="Dance_chart"', start_pos)
        if end_pos == -1:
            end_pos = start_pos + 40000
        sec_html = clean_html[start_pos:end_pos]
        
        tables = re.findall(r'<table.*?</table>', sec_html, re.DOTALL)
        week_lineups[w_num] = {'theme': w_theme, 'couples': []}

        for t in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
            table_artist = theme_artist
            if rows:
                h_cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', rows[0], re.DOTALL)
                if len(h_cells) >= 4:
                    h_text = html.unescape(re.sub(r'<[^>]+>', '', h_cells[3])).strip()
                    m_artist = re.search(r'^(.*?)\s+(?:music|songs)$', h_text, re.IGNORECASE)
                    if m_artist:
                        table_artist = m_artist.group(1).strip()

            for r in rows[1:]:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.DOTALL)
                clean_cells = [html.unescape(re.sub(r'<[^>]+>', '', c).strip()) for c in cells]
                if len(clean_cells) >= 4:
                    raw_couple, raw_score, dance, music = clean_cells[0], clean_cells[1], clean_cells[2], clean_cells[3]
                    result = clean_cells[4] if len(clean_cells) > 4 else ''
                    
                    matched_name = match_couple(raw_couple)
                    if not matched_name:
                        continue
                    
                    score_match = re.search(r'^(\d+)(?:\s*\(([\d\s,]+)\))?', raw_score)
                    if score_match:
                        score = int(score_match.group(1))
                        if not (0 <= score <= 40):
                            score = None
                        breakdown_str = score_match.group(2)
                        judge_scores = [int(x.strip()) for x in breakdown_str.split(',') if x.strip().isdigit()] if breakdown_str else []
                    else:
                        score = None
                        judge_scores = []
                    
                    music_clean = re.sub(r'\[.*?\]', '', music).strip()
                    music_fmt = music_clean
                    if ' — ' in music_clean:
                        parts = music_clean.split(' — ', 1)
                        music_fmt = f'“{parts[0].strip(chr(34)).strip(chr(8220)).strip(chr(8221))}” · {parts[1].strip()}'
                    elif ' - ' in music_clean:
                        parts = music_clean.split(' - ', 1)
                        music_fmt = f'“{parts[0].strip(chr(34)).strip(chr(8220)).strip(chr(8221))}” · {parts[1].strip()}'
                    elif table_artist and music_clean and music_clean.upper() != 'TBA':
                        clean_title = music_clean.strip(chr(34)).strip(chr(8220)).strip(chr(8221)).strip("'\" \t")
                        if clean_title:
                            music_fmt = f'“{clean_title}” · {table_artist}'

                    couple_history[matched_name].append({
                        'week': w_num,
                        'theme': w_theme,
                        'dance': dance,
                        'music': music_fmt,
                        'score': score,
                        'judge_scores': judge_scores,
                        'result': result
                    })

                    week_lineups[w_num]['couples'].append({
                        'name': matched_name,
                        'dance': dance,
                        'song': music_fmt,
                        'score': score,
                        'judge_scores': judge_scores,
                        'result': result
                    })

                    if 'eliminated' in result.lower():
                        eliminated_info[matched_name] = {
                            'week': w_num,
                            'theme': w_theme,
                            'dance': dance,
                            'music': music_fmt,
                            'score': score,
                            'judge_scores': judge_scores
                        }

    return {
        'ep_dates': ep_dates,
        'ep_themes': ep_themes,
        'couple_history': couple_history,
        'eliminated_info': eliminated_info,
        'week_lineups': week_lineups
    }

def update_dancers_json_and_txt(active_couples):
    dancers_v1 = []
    dancers_v2 = {}
    
    for name in active_couples:
        meta = COUPLE_REGISTRY[name]
        dancers_v1.append(meta["short"])
        full_pair = f"{name} & {meta['proName']}"
        dancers_v2[full_pair] = meta["vote_code"]

    with open(DANCERS_JSON, 'w', encoding='utf-8') as f:
        json.dump({"dancers": dancers_v1, "dancers_v2": dancers_v2}, f, indent=2)
        f.write('\n')
    print(f"Updated {DANCERS_JSON}: {len(dancers_v1)} active couples.")

    with open(DANCERS_TXT, 'w', encoding='utf-8') as f:
        for pair in dancers_v1:
            f.write(f"{pair}\n")
    print(f"Updated {DANCERS_TXT}: {len(dancers_v1)} active couples.")

def compute_power_index(avg_score, wow_delta, market_prob, mirrorballs, social_reach_num, is_athlete, is_dancer):
    """
    Calculates composite Power Index (0-100) weighting:
    - 45% Judges' Score Baseline & Momentum
    - 25% Official Kalshi Winner Market Odds (kxdancingwiththestars)
    - 15% Pro Partner Mirrorball Pedigree
    - 15% Fan Voting Reach & Background Buffer
    """
    # 1. Scoring floor (0-100 scale, avg_score out of 30)
    score_comp = (avg_score / 30.0) * 100.0
    score_comp += min(max(wow_delta * 1.5, -6.0), 6.0)
    score_comp = min(max(score_comp, 0.0), 100.0)

    # 2. Kalshi Market probability component (33% leader scales to ~100)
    market_comp = min(market_prob * 3.03, 100.0)

    # 3. Pro Mirrorball pedigree
    mb_map = {0: 50.0, 1: 70.0, 2: 85.0, 3: 100.0}
    pro_comp = mb_map.get(mirrorballs, 60.0)

    # 4. Fan voting & background buffer
    if social_reach_num >= 8.0:
        social_comp = 100.0
    elif social_reach_num >= 3.5:
        social_comp = 85.0
    elif social_reach_num >= 2.0:
        social_comp = 72.0
    elif social_reach_num >= 1.0:
        social_comp = 60.0
    else:
        social_comp = 48.0

    if is_dancer:
        social_comp = min(social_comp + 8.0, 100.0)
    elif is_athlete:
        social_comp = min(social_comp + 5.0, 100.0)

    power_val = (0.45 * score_comp) + (0.25 * market_comp) + (0.15 * pro_comp) + (0.15 * social_comp)
    return round(power_val, 1)

def compute_dynamic_attributes(name, valid_weeks, total_score, rank, active_count, meta, market_prob=None, power_index=None):
    """
    Computes dynamic categories, tags, and case blurb based on actual scoring data, power index, and prediction markets.
    """
    num_weeks = len(valid_weeks)
    avg_score = total_score / num_weeks if num_weeks > 0 else 0
    latest_score = valid_weeks[-1]['score'] if valid_weeks else 0
    prev_score = valid_weeks[-2]['score'] if num_weeks >= 2 else latest_score
    wow_delta = latest_score - prev_score if num_weeks >= 2 else 0

    p_idx = power_index if power_index is not None else 50.0
    m_prob = market_prob if market_prob is not None else 5

    # 1. Determine Tier based on Power Index & Standing
    if rank <= 4 or p_idx >= 68.0:
        tier = 'Anchor'
    elif p_idx < 42.0 or rank >= active_count:
        tier = 'Risk'
    elif rank <= 8 or p_idx >= 50.0:
        tier = 'Sleeper'
    else:
        tier = 'Contender'

    # 2. Dynamic Categories (cats)
    cats = []
    if tier == 'Anchor' or p_idx >= 68.0:
        cats.append('anchor')
    if tier == 'Sleeper':
        cats.append('sleeper')
    if meta.get('is_athlete'):
        cats.append('athlete')
    if meta.get('is_dancer'):
        cats.append('dance')
    if meta.get('social_reach_num', 0) >= 1.0:
        cats.append('social')

    # 3. Dynamic Tags (Celebrity background trait, live market odds, score momentum)
    tags = []
    trait = meta.get('trait')
    if trait and trait not in ('Contender', 'Risk', 'Sleeper', 'Anchor'):
        tags.append(trait)

    # Market win probability tag
    tags.append(f'{m_prob}% Market')

    # Momentum / Trend
    if wow_delta >= 4:
        tags.append(f'Surging (+{wow_delta})')
    elif wow_delta >= 2:
        tags.append(f'Riser (+{wow_delta})')
    elif wow_delta <= -3:
        tags.append(f'Dip ({wow_delta})')
    elif avg_score >= 20.0:
        tags.append('20+ avg')
    else:
        tags.append('Steady')

    # 4. Dynamic Case Blurb
    pro = meta['proName']
    mb = meta['mirrorballs']
    mb_str = f"{mb} Mirrorball{'s' if mb != 1 else ''}"
    latest_dance = valid_weeks[-1]['dance'] if valid_weeks else 'routine'
    
    if rank == 1:
        scoring_lead = f"Ranks #1 on the composite Power Board ({p_idx}/100) with a {avg_score:.1f}/30 scoring average and {m_prob}% market win odds."
    elif m_prob >= 24:
        scoring_lead = f"Prediction market favorite ({m_prob}% implied win odds) holding a strong {avg_score:.1f}/30 judges' scoring floor."
    elif wow_delta >= 3:
        scoring_lead = f"Surged +{wow_delta} points in the latest round ({latest_score}/30 {latest_dance}) with a {p_idx}/100 Power Index."
    elif wow_delta <= -3:
        scoring_lead = f"Overcame a temporary scoring dip ({wow_delta} WoW), bolstered by a {p_idx}/100 Power Index."
    elif avg_score >= 20.0:
        scoring_lead = f"Consistent scorer averaging {avg_score:.1f}/30 through {num_weeks} completed weeks ({p_idx}/100 Power Index)."
    elif rank <= 4:
        scoring_lead = f"Top-tier contender holding rank #{rank} on the Power Board ({p_idx}/100)."
    else:
        scoring_lead = f"Holding steady with a {avg_score:.1f}/30 scoring average and {m_prob}% market win probability."

    outlook = meta.get('outlook', 'Poised to make an impact as the field narrows.')
    case_blurb = f"{scoring_lead} Paired with {pro} ({mb_str}), {outlook}"

    return cats, tags, case_blurb, avg_score, wow_delta

def get_judge_meta_list(num_judges):
    if num_judges == 3:
        return [('CA', 'Carrie Ann Inaba'), ('D', 'Derek Hough'), ('B', 'Bruno Tonioli')]
    elif num_judges == 4:
        return [('CA', 'Carrie Ann Inaba'), ('D', 'Derek Hough'), ('G', 'Guest Judge'), ('B', 'Bruno Tonioli')]
    else:
        return [(f'J{i+1}', f'Judge {i+1}') for i in range(num_judges)]

def render_score_box_html(score, judge_scores=None, is_leader=False, max_score=30, indent="            "):
    score_class = 'lineup-score-box leader' if is_leader else 'lineup-score-box'
    if not judge_scores:
        return (
            f'{indent}<div class="{score_class}">\n'
            f'{indent}  <div class="score-total"><strong>{score}</strong><span>/{max_score}</span></div>\n'
            f'{indent}</div>'
        )
    
    judge_meta = get_judge_meta_list(len(judge_scores))
    tooltip_parts = [f"{name}: {val}" for (_, name), val in zip(judge_meta, judge_scores)]
    box_tooltip = " · ".join(tooltip_parts)
    
    cols_html = "".join([
        f'<div class="judge-col"><span class="judge-abbr" title="{name}">{abbr}</span><span class="judge-val">{val}</span></div>'
        for (abbr, name), val in zip(judge_meta, judge_scores)
    ])
    
    return (
        f'{indent}<div class="{score_class}">\n'
        f'{indent}  <div class="score-total"><strong>{score}</strong><span>/{max_score}</span></div>\n'
        f'{indent}  <div class="score-judges" title="{box_tooltip}">\n'
        f'{indent}    {cols_html}\n'
        f'{indent}  </div>\n'
        f'{indent}</div>'
    )

def update_index_html(wiki_data, market_odds=None):
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract winner and weekly elimination odds dictionaries
    if isinstance(market_odds, dict) and ('winner' in market_odds or 'elimination' in market_odds):
        winner_odds = market_odds.get('winner', {})
        elim_odds = market_odds.get('elimination', {})
    elif isinstance(market_odds, dict):
        winner_odds = market_odds
        elim_odds = {}
    else:
        winner_odds = {}
        elim_odds = {}

    couple_history = wiki_data['couple_history']
    eliminated_info = wiki_data['eliminated_info']
    week_lineups = wiki_data['week_lineups']
    ep_dates = wiki_data['ep_dates']
    ep_themes = wiki_data['ep_themes']

    known_eliminated = [
        "Conner Leavitt",
        "Sarah Jane Nader",
        "Giada De Laurentiis",
        "Taylor Hanson"
    ]
    all_eliminated = list(known_eliminated)
    for name in eliminated_info:
        if name not in all_eliminated:
            all_eliminated.append(name)

    active_couples = [name for name in COUPLE_REGISTRY if name not in all_eliminated]

    all_weeks = sorted(week_lineups.keys())
    current_week_num = all_weeks[-1] if all_weeks else 3
    
    current_lineup = week_lineups.get(current_week_num, {'couples': []})
    current_scores_done = all(c.get('score') is not None for c in current_lineup['couples']) if current_lineup['couples'] else False
    
    lineup_week_num = current_week_num
    if current_scores_done and (current_week_num + 1) in week_lineups:
        lineup_week_num = current_week_num + 1

    ep_idx = lineup_week_num + 1
    target_date_str = ep_dates.get(ep_idx, "September 29, 2026")
    theme_title = ep_themes.get(ep_idx, week_lineups.get(lineup_week_num, {}).get('theme', 'Yacht Rock Night'))
    theme_title = theme_title.strip('"').strip()
    short_date = target_date_str.replace("September", "Sept.").replace("October", "Oct.").replace("November", "Nov.")

    # 1. Update subtle timestamp, kicker, board title, hero subtitle & quick meta
    now_et = datetime.now(ZoneInfo("America/New_York")).strftime("%b. %-d, %-I:%M %p ET")
    subtle_update_new = f'<span class="subtle-update"><span class="subtle-dot"></span>Updated {now_et}</span>'
    content = re.sub(r'<span class="subtle-update">.*?(?=\s*</div>)', subtle_update_new, content, flags=re.DOTALL)

    content = re.sub(
        r'<span class="kicker">Power rankings\s*·\s*Week \d+\s*·\s*[^<]+</span>',
        f'<span class="kicker">Power rankings · Week {lineup_week_num} · {short_date}</span>',
        content
    )
    content = re.sub(
        r'<h1>The Week \d+ board</h1>',
        f'<h1>The Week {lineup_week_num} board</h1>',
        content
    )
    hero_sub_new = f'<p class="hero-sub">{count_to_word(len(active_couples))} couples remain. Track proven technique against fandom, momentum, and the one thing fans can’t ignore: theme-night fit.</p>'
    content = re.sub(
        r'<p class="hero-sub">\w+ couples remain\..*?</p>',
        hero_sub_new,
        content
    )

    quick_meta_new = (
        f'<div class="quick-meta">\n'
        f'            <span>Season 35</span>\n'
        f'            <span class="sep">/</span>\n'
        f'            <span>{len(active_couples)} couples active</span>\n'
        f'            <span class="sep">/</span>\n'
        f'            <span>{len(all_eliminated)} eliminated</span>\n'
        f'            <span class="sep">/</span>\n'
        f'            <span>Next live show: Tuesday, 8/7c</span>\n'
        f'          </div>'
    )
    content = re.sub(r'<div class="quick-meta">.*?</div>', quick_meta_new, content, flags=re.DOTALL)

    # Automatically keep the trajectory chart "All N" filter count in sync with active couples
    content = re.sub(
        r'<button class="chart-filter([^"]*)" data-traj="all">All \d+</button>',
        rf'<button class="chart-filter\1" data-traj="all">All {len(active_couples)}</button>',
        content
    )

    # Guardrail 1: Round-Completion Gate for Leaderboard & Composite Power Index
    # A week is only considered "completed" if all currently active couples have a valid score recorded.
    # During the Tuesday 8-10 PM ET broadcast, early dancers will have Week N scores recorded on Wikipedia
    # before late dancers have performed. Gating leaderboard aggregation to completed rounds ensures
    # the main Power Board remains fair, normalized (e.g. all out of 60), and free of mid-broadcast scoring skew.
    # Individual live scores for the current in-progress week are displayed directly in the Week Lineup card.
    completed_weeks = set()
    all_weeks = set()
    for perfs in couple_history.values():
        for p in perfs:
            all_weeks.add(p['week'])

    for w in all_weeks:
        scored_active = sum(
            1 for name in active_couples
            if any(p['week'] == w and p['score'] is not None for p in couple_history.get(name, []))
        )
        if scored_active == len(active_couples):
            completed_weeks.add(w)

    print(f"Verified completed weeks across all active couples: {sorted(list(completed_weeks))}")

    # 3. Build dancers array in JS with COMPOSITE POWER INDEX & MARKET ODDS
    active_dancers_raw = []
    for name in active_couples:
        meta = COUPLE_REGISTRY[name]
        perfs = couple_history.get(name, [])
        valid_weeks = [p for p in perfs if p['score'] is not None]
        for p in valid_weeks:
            p['is_live'] = (p['week'] not in completed_weeks)
        total_score = sum(w['score'] for w in valid_weeks)
        latest_score = valid_weeks[-1]['score'] if valid_weeks else 0
        prev_score = valid_weeks[-2]['score'] if len(valid_weeks) >= 2 else latest_score
        wow_delta = latest_score - prev_score if len(valid_weeks) >= 2 else 0
        avg_score = total_score / len(valid_weeks) if valid_weeks else 0

        base_market = meta.get('baseline_market_prob', 5)
        market_prob = winner_odds.get(name, base_market) if winner_odds else base_market
        elim_risk = elim_odds.get(name, None) if elim_odds else None

        power_index = compute_power_index(
            avg_score=avg_score,
            wow_delta=wow_delta,
            market_prob=market_prob,
            mirrorballs=meta['mirrorballs'],
            social_reach_num=meta.get('social_reach_num', 1.0),
            is_athlete=meta.get('is_athlete', False),
            is_dancer=meta.get('is_dancer', False)
        )

        active_dancers_raw.append({
            'name': name,
            'meta': meta,
            'valid_weeks': valid_weeks,
            'total_score': total_score,
            'latest_score': latest_score,
            'avg_score': avg_score,
            'wow_delta': wow_delta,
            'market_prob': market_prob,
            'elim_risk': elim_risk,
            'power_index': power_index,
            'initial_rank': meta.get('initial_rank', 99)
        })

    # Sort dancers by Composite Power Index descending, tie-breaker avg score, then market probability
    active_dancers_raw.sort(key=lambda d: (-d['power_index'], -d['avg_score'], -d['market_prob']))
    
    active_dancers_data = []
    active_count = len(active_dancers_raw)
    for rank, d in enumerate(active_dancers_raw, start=1):
        name = d['name']
        meta = d['meta']
        valid_weeks = d['valid_weeks']
        total_score = d['total_score']
        market_prob = d['market_prob']
        elim_risk = d.get('elim_risk')
        power_index = d['power_index']

        cats, tags, case_blurb, avg_score, wow_delta = compute_dynamic_attributes(
            name, valid_weeks, total_score, rank, active_count, meta, market_prob=market_prob, power_index=power_index
        )

        active_dancers_data.append({
            'rank': rank,
            'name': name,
            'age': meta['age'],
            'proName': meta['proName'],
            'mirrorballs': meta['mirrorballs'],
            'socialReach': meta.get('social_reach_num', 1.0),
            'photo': meta['photo'],
            'weeks': valid_weeks,
            'total': total_score,
            'avg': avg_score,
            'wow': wow_delta,
            'powerIndex': power_index,
            'marketProb': market_prob,
            'elimRisk': elim_risk,
            'cats': cats,
            'tags': tags,
            'case': case_blurb
        })

    dancer_lines = []
    for d in active_dancers_data:
        weeks_js = json.dumps([{'dance': w['dance'], 'score': w['score'], 'isLive': w.get('is_live', False), 'judges': w.get('judge_scores', [])} for w in d['weeks']]).replace('"', "'")
        cats_js = json.dumps(d['cats']).replace('"', "'")
        tags_js = json.dumps(d['tags']).replace('"', "'")
        case_escaped = d['case'].replace("'", "\\'")
        elim_js = f"{d['elimRisk']}" if d.get('elimRisk') is not None else "null"
        line = f"      {{rank:{d['rank']},name:'{d['name']}',age:{d['age']},proName:'{d['proName']}',mirrorballs:{d['mirrorballs']},socialReach:{d.get('socialReach', 1.0)},photo:'{d['photo']}',weeks:{weeks_js},total:{d['total']},powerIndex:{d['powerIndex']},marketProb:{d['marketProb']},elimRisk:{elim_js},wow:{d['wow']},cats:{cats_js},tags:{tags_js},case:'{case_escaped}'}}"
        dancer_lines.append(line)
    
    new_dancers_block = "const dancers = [\n" + ",\n".join(dancer_lines) + "\n    ];"
    content = re.sub(r'const dancers = \[.*?\];', new_dancers_block, content, flags=re.DOTALL)

    # 3b. Update static projected bottom 2 and risk filter count
    def calc_proj_order(d_list):
        has_elim = any(d.get('elimRisk') is not None for d in d_list)
        items = []
        for d in d_list:
            scored = [w['score'] for w in d['weeks'] if w.get('score') is not None]
            if not scored:
                w_score = 15.0
            else:
                n = len(scored)
                total_w = n * (n + 1) / 2
                w_score = sum(((i + 1) / total_w) * s for i, s in enumerate(scored))
            items.append({
                'name': d['name'],
                'w_score': w_score,
                'market_prob': d['marketProb'],
                'elim_risk': d.get('elimRisk'),
                'mirrorballs': d['mirrorballs'],
                'social_reach': d.get('socialReach', 1.0)
            })
        total_w_score = sum(x['w_score'] for x in items) or 1.0
        if has_elim:
            total_safety = sum(max(5.0, 100.0 - (x['elim_risk'] if x['elim_risk'] is not None else 10.0) * 2.0) for x in items) or 1.0
            for x in items:
                j_share = (x['w_score'] / total_w_score) * 100.0
                e_risk = x['elim_risk'] if x['elim_risk'] is not None else 10.0
                safety = max(5.0, 100.0 - e_risk * 2.0)
                m_share = (safety / total_safety) * 100.0
                p_boost = x['mirrorballs'] * 1.5
                s_boost = min(x['social_reach'] * 1.5, 12.0)
                x['raw_fan'] = (m_share * 0.45) + (s_boost * 0.35) + (p_boost * 0.20) + 1.0
                x['j_share'] = j_share
        else:
            total_mkt = sum(x['market_prob'] for x in items) or 1.0
            for x in items:
                j_share = (x['w_score'] / total_w_score) * 100.0
                m_share = (x['market_prob'] / total_mkt) * 100.0
                p_boost = x['mirrorballs'] * 1.5
                s_boost = min(x['social_reach'] * 1.5, 12.0)
                x['raw_fan'] = (m_share * 0.45) + (s_boost * 0.35) + (p_boost * 0.20) + 1.0
                x['j_share'] = j_share
        total_fan = sum(x['raw_fan'] for x in items) or 1.0
        for x in items:
            f_share = (x['raw_fan'] / total_fan) * 100.0
            x['combined'] = 0.5 * x['j_share'] + 0.5 * f_share
        items.sort(key=lambda x: x['combined'], reverse=True)
        return items

    proj_sorted = calc_proj_order(active_dancers_data)
    if len(proj_sorted) >= 2:
        b1 = proj_sorted[-1]['name']
        b2 = proj_sorted[-2]['name']
        bubble = proj_sorted[-3]['name'] if len(proj_sorted) >= 3 else ''
        b2_html = f'<span id="bottom2-alert-text"><strong>Projected Bottom 2:</strong> {b2} &amp; {b1}{f" ({bubble} on bubble)" if bubble else ""}</span>'
        content = re.sub(r'<span id="bottom2-alert-text">.*?</span>', b2_html, content)
    content = re.sub(r'<button class="risk-filter-btn active" data-risk-filter="all">All \d+ Couples</button>', f'<button class="risk-filter-btn active" data-risk-filter="all">All {len(active_dancers_data)} Couples</button>', content)

    # 4. Update #voted-off section
    eliminated_cards = []
    for idx, name in enumerate(all_eliminated, start=1):
        meta = COUPLE_REGISTRY[name]
        perfs = couple_history.get(name, [])
        scored_weeks = [p for p in perfs if p['score'] is not None]
        total_score = sum(p['score'] for p in scored_weeks)
        max_total = len(scored_weeks) * 30 if scored_weeks else 30
        
        ord_label = meta.get('eliminated_order', ordinal(idx) + " eliminated")
        date_str = meta.get('eliminated_date', target_date_str)
        if 'eliminated_datetime' in meta:
            datetime_str = meta['eliminated_datetime']
        else:
            try:
                datetime_str = datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
            except Exception:
                datetime_str = datetime.now().strftime("%Y-%m-%d")

        if 'eliminated_week_theme' in meta:
            week_theme_str = meta['eliminated_week_theme']
        elif name in eliminated_info:
            e_w = eliminated_info[name].get('week', lineup_week_num)
            e_t = eliminated_info[name].get('theme', theme_title)
            week_theme_str = f"Week {e_w}, {e_t}"
        else:
            week_theme_str = f"Week {lineup_week_num}, {theme_title}"

        if 'eliminated_note' in meta:
            exit_note = meta['eliminated_note']
        elif "was eliminated" in meta.get('bio', ''):
            exit_note = meta['bio']
        elif name in eliminated_info and eliminated_info[name].get('dance'):
            e_info = eliminated_info[name]
            dance_str = e_info['dance'].lower() if e_info['dance'] else 'routine'
            music_str = f" to {e_info['music']}" if e_info['music'] else ""
            score_str = f" that scored {e_info['score']}" if e_info.get('score') else ""
            exit_note = f"{meta.get('bio', name)} was eliminated after a {dance_str}{music_str}{score_str}."
        else:
            exit_note = meta.get('bio', '')
        
        score_weeks_items = []
        for w_i, p in enumerate(scored_weeks):
            js = p.get('judge_scores', [])
            badge = ""
            if js:
                meta_j = get_judge_meta_list(len(js))
                tip = " · ".join([f"{n}: {val}" for (_, n), val in zip(meta_j, js)])
                badge = f' <span class="score-judges-badge" title="{tip}">({",".join(map(str, js))})</span>'
            score_weeks_items.append(f'<div class="score-week"><span>Week {w_i+1} · {p["dance"]}</span><strong>{p["score"]}/30{badge}</strong></div>')
        score_weeks_html = "".join(score_weeks_items)
        
        img_style = f' style="object-position: {meta["photo_position"]};"' if "photo_position" in meta else ""
        card = (
            f'        <article class="eliminated-card">\n'
            f'          <img src="assets/{meta["photo"]}"{img_style} alt="{name} and professional partner {meta["proName"]} in their Season 35 cast portrait">\n'
            f'          <div class="eliminated-copy">\n'
            f'            <time class="eliminated-date" datetime="{datetime_str}">{ord_label} · {date_str}</time>\n'
            f'            <h3>{name}</h3>\n'
            f'            <p class="partner">with {meta["proName"]} · {mirrorball_label(meta["mirrorballs"])} · {week_theme_str}</p>\n'
            f'            <div class="final-score" aria-label="Final season score: {total_score} out of {max_total}"><span>Final total</span><strong>{total_score}/{max_total}</strong></div>\n'
            f'            <div class="score-history" aria-label="Weekly judges\' scores">{score_weeks_html}</div>\n'
            f'            <p class="exit-note">{exit_note}</p>\n'
            f'          </div>\n'
            f'        </article>'
        )
        eliminated_cards.append(card)

    new_eliminated_list = (
        f'<div class="eliminated-list">\n' +
        "\n".join(eliminated_cards) +
        '\n      </div>'
    )
    content = re.sub(r'<div class="eliminated-list">.*?</div>\s*</section>', new_eliminated_list + '\n    </section>', content, flags=re.DOTALL)

    # 5. Update .week-lineup / Scores & Songs section
    target_lineup = week_lineups.get(lineup_week_num, {'couples': []})['couples']
    active_in_lineup = [c for c in target_lineup if c['name'] in active_couples]
    if not active_in_lineup:
        active_in_lineup = [{'name': d['name'], 'dance': 'TBA', 'song': 'TBA', 'score': None, 'result': ''} for d in active_dancers_data]

    day_of_week_date = f"Tuesday, {target_date_str.rsplit(',', 1)[0].strip()}" if ',' in target_date_str else f"Tuesday, {target_date_str}"

    scored_couples = [c for c in active_in_lineup if c.get('score') is not None]
    unscored_couples = [c for c in active_in_lineup if c.get('score') is None]

    if scored_couples and len(scored_couples) == len(active_in_lineup):
        # Case A: All couples have performed! (Official Leaderboard - Stays for the week)
        scored_sorted = sorted(scored_couples, key=lambda c: (-c['score'], c['name']))
        top_score = scored_sorted[0]['score'] if scored_sorted else 30
        
        leaderboard_items = []
        for rank_idx, c in enumerate(scored_sorted, start=1):
            num_str = f"#{rank_idx}"
            meta = COUPLE_REGISTRY[c['name']]
            dance = c.get('dance', 'TBA')
            song = c.get('song', 'TBA')
            score = c.get('score', 0)
            is_leader = (score == top_score)
            leader_badge = '<span class="leader-tag">High Score</span>' if is_leader else ''
            elim_badge = '<span class="elim-tag">Eliminated</span>' if ('eliminated' in c.get('result', '').lower()) else ''
            music_links = make_music_links_html(song, indent="              ")
            score_box = render_score_box_html(score, c.get('judge_scores', []), is_leader=is_leader, indent="            ")
            
            item = (
                f'          <div class="lineup-item">\n'
                f'            <span class="lineup-no">{num_str}</span>\n'
                f'            <div>\n'
                f'              <span class="lineup-couple">{c["name"]} &amp; {meta["proName"]}{leader_badge}{elim_badge}</span>\n'
                f'              <span class="lineup-dance">{dance}</span>\n'
                f'              <span class="lineup-song">{song}</span>{music_links}\n'
                f'            </div>\n'
                f'{score_box}\n'
                f'          </div>'
            )
            leaderboard_items.append(item)

        head_kicker = f'{day_of_week_date} · Week {lineup_week_num} Scores'
        head_title = f'{theme_title}: Scores &amp; Songs'
        head_desc = f'Final judges’ standings and complete music lineup for all {len(active_in_lineup)} couples in Week {lineup_week_num}.'
        
        lineup_content_html = (
            f'        <div class="lineup-group">\n'
            f'          <h4 class="lineup-group-title">Week {lineup_week_num} Leaderboard</h4>\n'
            f'          <div class="lineup-list">\n' +
            "\n".join(leaderboard_items) + "\n"
            f'          </div>\n'
            f'        </div>'
        )

    elif scored_couples and unscored_couples:
        # Case B: Live show in progress! (Tonight’s Leaderboard + Up Next)
        scored_sorted = sorted(scored_couples, key=lambda c: (-c['score'], c['name']))
        top_score = scored_sorted[0]['score'] if scored_sorted else 30
        
        danced_items = []
        for rank_idx, c in enumerate(scored_sorted, start=1):
            num_str = f"#{rank_idx}"
            meta = COUPLE_REGISTRY[c['name']]
            dance = c.get('dance', 'TBA')
            song = c.get('song', 'TBA')
            score = c.get('score', 0)
            is_leader = (score == top_score)
            leader_badge = '<span class="leader-tag">Leader</span>' if is_leader else ''
            music_links = make_music_links_html(song, indent="              ")
            score_box = render_score_box_html(score, c.get('judge_scores', []), is_leader=is_leader, indent="            ")
            
            item = (
                f'          <div class="lineup-item">\n'
                f'            <span class="lineup-no">{num_str}</span>\n'
                f'            <div>\n'
                f'              <span class="lineup-couple">{c["name"]} &amp; {meta["proName"]}{leader_badge}</span>\n'
                f'              <span class="lineup-dance">{dance}</span>\n'
                f'              <span class="lineup-song">{song}</span>{music_links}\n'
                f'            </div>\n'
                f'{score_box}\n'
                f'          </div>'
            )
            danced_items.append(item)

        up_next_items = []
        for c_idx, c in enumerate(unscored_couples, start=1):
            num_str = f"{c_idx:02d}"
            meta = COUPLE_REGISTRY[c['name']]
            dance = c.get('dance', 'TBA')
            song = c.get('song', 'TBA')
            music_links = make_music_links_html(song, indent="              ")
            
            item = (
                f'          <div class="lineup-item">\n'
                f'            <span class="lineup-no">{num_str}</span>\n'
                f'            <div>\n'
                f'              <span class="lineup-couple">{c["name"]} &amp; {meta["proName"]}</span>\n'
                f'              <span class="lineup-dance">{dance}</span>\n'
                f'              <span class="lineup-song">{song}</span>{music_links}\n'
                f'            </div>\n'
                f'            <div class="lineup-pending-box">Up next</div>\n'
                f'          </div>'
            )
            up_next_items.append(item)

        head_kicker = f'<span class="live-dot-inline"></span> Live Show in Progress · {len(scored_couples)} of {len(active_in_lineup)} danced'
        head_title = f'{theme_title}: Scores &amp; Songs'
        head_desc = f'Real-time live show scores and music lineup. {scored_sorted[0]["name"]} leads tonight with {top_score}/30.'

        lineup_content_html = (
            f'        <div class="lineup-group">\n'
            f'          <h4 class="lineup-group-title">Tonight’s Leaderboard ({len(scored_couples)} Danced)</h4>\n'
            f'          <div class="lineup-list">\n' +
            "\n".join(danced_items) + "\n"
            f'          </div>\n'
            f'        </div>\n'
            f'        <div class="lineup-group" style="margin-top:32px">\n'
            f'          <h4 class="lineup-group-title">Up Next Tonight ({len(unscored_couples)} Remaining)</h4>\n'
            f'          <div class="lineup-list">\n' +
            "\n".join(up_next_items) + "\n"
            f'          </div>\n'
            f'        </div>'
        )

    else:
        # Case C: Pre-show (Upcoming show lineup)
        scheduled_items = []
        for c_idx, c in enumerate(active_in_lineup, start=1):
            num_str = f"{c_idx:02d}"
            meta = COUPLE_REGISTRY[c['name']]
            dance = c.get('dance', 'TBA')
            song = c.get('song', 'TBA')
            music_links = make_music_links_html(song, indent="              ")
            
            item = (
                f'          <div class="lineup-item">\n'
                f'            <span class="lineup-no">{num_str}</span>\n'
                f'            <div>\n'
                f'              <span class="lineup-couple">{c["name"]} &amp; {meta["proName"]}</span>\n'
                f'              <span class="lineup-dance">{dance}</span>\n'
                f'              <span class="lineup-song">{song}</span>{music_links}\n'
                f'            </div>\n'
                f'            <div class="lineup-pending-box">Scheduled</div>\n'
                f'          </div>'
            )
            scheduled_items.append(item)

        head_kicker = f'{day_of_week_date} · Live at 8/7c'
        head_title = f'{theme_title}: Scores &amp; Songs'
        head_desc = f'The {len(active_in_lineup)} active couples, their dance styles, and songs for Week {lineup_week_num}. Scores will populate here live as routines air.'

        lineup_content_html = (
            f'        <div class="lineup-group">\n'
            f'          <h4 class="lineup-group-title">Confirmed Week {lineup_week_num} Performance Lineup</h4>\n'
            f'          <div class="lineup-list">\n' +
            "\n".join(scheduled_items) + "\n"
            f'          </div>\n'
            f'        </div>'
        )

    # Build expandable past weeks archive (e.g. Week 2, Week 1)
    past_weeks = [w for w in sorted(week_lineups.keys(), reverse=True) if w < lineup_week_num]
    past_weeks_blocks = []
    
    # Look up Spotify playlists registry if available
    playlists_reg_file = os.path.join(WORKSPACE_DIR, 'spotify_playlists.json')
    sp_reg = {}
    if os.path.exists(playlists_reg_file):
        try:
            with open(playlists_reg_file, 'r', encoding='utf-8') as f:
                sp_reg = json.load(f)
        except Exception:
            pass

    sp_icon_svg = '<svg viewBox="0 0 24 24" class="music-icon" aria-hidden="true"><path fill="currentColor" d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.503 17.308c-.218.357-.681.472-1.038.254-2.853-1.743-6.444-2.138-10.673-1.171-.408.093-.812-.162-.905-.57-.093-.408.162-.812.57-.905 4.634-1.059 8.604-.614 11.792 1.354.357.218.472.681.254 1.038zm1.47-3.267c-.275.447-.862.59-1.309.315-3.265-2.008-8.243-2.59-12.106-1.417-.502.152-1.034-.136-1.186-.638-.152-.502.136-1.034.638-1.186 4.417-1.341 9.907-.7 13.648 1.603.447.275.59.862.315 1.309zm.126-3.41c-3.916-2.325-10.374-2.54-14.116-1.403-.6.182-1.24-.165-1.422-.765-.182-.6.165-1.24.765-1.422 4.301-1.306 11.431-1.057 15.932 1.616.54.321.716 1.02.395 1.56-.321.54-1.02.716-1.56.395z"/></svg>'

    current_sp_url = sp_reg.get(f'week_{lineup_week_num}', {}).get('url') or f"https://open.spotify.com/search/{urllib.parse.quote(theme_title + ' Dancing With The Stars')}"
    season_sp_url = sp_reg.get('season_35', {}).get('url') or "https://open.spotify.com/playlist/73k9Xl6wFg7xAWOpG69Yux"

    for pw in past_weeks:
        pw_info = week_lineups[pw]
        pw_theme = pw_info.get('theme', f'Week {pw}')
        pw_couples = pw_info.get('couples', [])
        pw_scored = [c for c in pw_couples if c.get('score') is not None]
        if not pw_scored:
            continue
        
        pw_sorted = sorted(pw_scored, key=lambda c: (-c['score'], c['name']))
        pw_top_score = pw_sorted[0]['score'] if pw_sorted else 30
        
        pw_items = []
        for r_idx, c in enumerate(pw_sorted, start=1):
            num_str = f"#{r_idx}"
            meta = COUPLE_REGISTRY.get(c['name'], {})
            dance = c.get('dance', 'TBA')
            song = c.get('song', 'TBA')
            score = c.get('score', 0)
            is_leader = (score == pw_top_score)
            leader_badge = '<span class="leader-tag">High Score</span>' if is_leader else ''
            elim_badge = '<span class="elim-tag">Eliminated</span>' if ('eliminated' in c.get('result', '').lower()) else ''
            music_links = make_music_links_html(song, indent="                  ")
            score_box = render_score_box_html(score, c.get('judge_scores', []), is_leader=is_leader, indent="                ")
            
            item = (
                f'              <div class="lineup-item">\n'
                f'                <span class="lineup-no">{num_str}</span>\n'
                f'                <div>\n'
                f'                  <span class="lineup-couple">{c["name"]} &amp; {meta.get("proName", "")}{leader_badge}{elim_badge}</span>\n'
                f'                  <span class="lineup-dance">{dance}</span>\n'
                f'                  <span class="lineup-song">{song}</span>{music_links}\n'
                f'                </div>\n'
                f'{score_box}\n'
                f'              </div>'
            )
            pw_items.append(item)
        
        ep_date_val = ep_dates.get(pw + 1, '')
        date_snippet = f" · {ep_date_val.rsplit(',', 1)[0]}" if ep_date_val else ''
        
        pw_sp_url = sp_reg.get(f'week_{pw}', {}).get('url') or f"https://open.spotify.com/search/{urllib.parse.quote('DWTS Season 35 ' + pw_theme)}"

        details_block = (
            f'          <details class="past-week-details">\n'
            f'            <summary>\n'
            f'              <div class="pw-summary-left">\n'
            f'                <span class="pw-summary-title">Week {pw} · {pw_theme}{date_snippet}</span>\n'
            f'                <span class="pw-summary-meta">{len(pw_couples)} couples · High score: {pw_top_score}/30</span>\n'
            f'              </div>\n'
            f'              <span class="pw-chevron">▼</span>\n'
            f'            </summary>\n'
            f'            <div class="pw-body">\n'
            f'              <div class="week-playlist-actions" style="margin: 10px 0 14px 0;">\n'
            f'                <a href="{pw_sp_url}" target="_blank" rel="noopener noreferrer" class="playlist-btn spotify-playlist-btn" title="Listen to Week {pw} Playlist on Spotify">{sp_icon_svg}<span>Week {pw} Playlist</span></a>\n'
            f'              </div>\n'
            f'              <div class="lineup-list">\n' +
            "\n".join(pw_items) + "\n"
            f'              </div>\n'
            f'            </div>\n'
            f'          </details>'
        )
        past_weeks_blocks.append(details_block)
    
    past_weeks_html = ""
    if past_weeks_blocks:
        past_weeks_html = (
            f'\n        <div class="past-weeks-wrap">\n'
            f'          <div class="past-weeks-header">\n'
            f'            <h4>Past Week Archives</h4>\n'
            f'            <span>Tap to expand previous songs &amp; scores</span>\n'
            f'          </div>\n' +
            "\n".join(past_weeks_blocks) + "\n"
            f'        </div>'
        )

    new_lineup_html = (
        f'      <div class="week-lineup" id="scores" aria-labelledby="week-lineup-title">\n'
        f'        <span id="songs" style="scroll-margin-top:60px"></span>\n'
        f'        <div class="lineup-head">\n'
        f'          <div><p class="kicker" style="color:#efce82">{head_kicker}</p><h3 id="week-lineup-title">{head_title}</h3></div>\n'
        f'          <div>\n'
        f'            <p>{head_desc}</p>\n'
        f'            <div class="week-playlist-actions">\n'
        f'              <a href="{current_sp_url}" target="_blank" rel="noopener noreferrer" class="playlist-btn spotify-playlist-btn" title="Listen to Week {lineup_week_num} Playlist on Spotify">{sp_icon_svg}<span>Week {lineup_week_num} Playlist</span></a>\n'
        f'              <a href="{season_sp_url}" target="_blank" rel="noopener noreferrer" class="playlist-btn master-playlist-btn" title="Listen to Full Season 35 Soundtrack on Spotify">{sp_icon_svg}<span>Full Season 35 Playlist</span></a>\n'
        f'            </div>\n'
        f'          </div>\n'
        f'        </div>\n'
        f'{lineup_content_html}'
        f'{past_weeks_html}\n'
        f'      </div>'
    )
    content = re.sub(r'<div class="week-lineup"[^>]*>.*?</div>\s*<div class="calendar"[^>]*>', new_lineup_html + '\n\n      <div class="calendar" id="schedule" aria-label="Season 35 theme calendar">', content, flags=re.DOTALL)

    # 6. Highlight current week in theme calendar & update newly announced themes
    content = re.sub(r'<div class="cal-row current">', '<div class="cal-row">', content)
    content = re.sub(
        rf'<div class="cal-row">(<b>Week {lineup_week_num}</b>)',
        r'<div class="cal-row current">\1',
        content
    )
    # If Week 5 theme is announced on Wikipedia (Episode 6), update it in the calendar
    w5_theme = ep_themes.get(6, '')
    if w5_theme and 'tba' not in w5_theme.lower() and 'to be' not in w5_theme.lower():
        content = re.sub(
            r'(<div class="cal-row[^>]*><b>Week 5</b><time>[^<]*</time><span>)TBA.*?(</span></div>)',
            rf'\g<1>{w5_theme}\g<2>',
            content
        )

    # 7. Update spotlight market card
    top_market_name = "Ezra Frech"
    top_prob = 33
    runners_up_str = "Harry Shum Jr. (12%), Maura Higgins (12%), and Jenna Dewan (11%)"
    if winner_odds:
        sorted_market = sorted([(k, v) for k, v in winner_odds.items() if k in active_couples], key=lambda x: -x[1])
        if sorted_market and sorted_market[0][1] > 0:
            top_market_name, top_prob = sorted_market[0]
            runners_up = sorted_market[1:4]
            if runners_up:
                runners_up_parts = [f"{name} ({prob}%)" for name, prob in runners_up]
                if len(runners_up_parts) == 1:
                    runners_up_str = runners_up_parts[0]
                elif len(runners_up_parts) == 2:
                    runners_up_str = f"{runners_up_parts[0]} and {runners_up_parts[1]}"
                else:
                    runners_up_str = f"{', '.join(runners_up_parts[:-1])}, and {runners_up_parts[-1]}"

    spotlight_html = (
        f'    <aside class="spotlight" aria-label="Market spotlight">\n'
        f'      <div class="spot-copy">\n'
        f'        <p class="kicker">Live Kalshi market favorite</p>\n'
        f'        <h2>{top_market_name} surged to {top_prob}% to win it all.</h2>\n'
        f'        <p>Following back-to-back 20+ judges’ marks and viral social momentum, Paralympic champion {top_market_name} has taken over as the leading favorite on Kalshi’s Season 35 winner market with a {top_prob}% implied win probability, followed by {runners_up_str}.</p>\n'
        f'        <div class="market-actions">\n'
        f'          <a class="market-btn" href="https://kalshi.com/markets/kxdancingwiththestars/who-will-win-dancing-with-the-stars/kxdancingwiththestars-26dec31" target="_blank" rel="noopener noreferrer">Trade on Kalshi (Who Will Win) ↗</a>\n'
        f'          <a class="market-btn" href="https://kalshi.com/markets/kxdwtselimination" target="_blank" rel="noopener noreferrer" style="background:transparent;border:1px solid var(--line);color:var(--ink)">Weekly Elimination Market ↗</a>\n'
        f'        </div>\n'
        f'        <p class="signal">Live prediction markets track implied win probabilities; contracts update continuously on Kalshi and are not affiliated with or endorsed by ABC or Disney.</p>\n'
        f'      </div>\n'
        f'      <div class="market"><div><strong>{top_prob}%</strong><span>Kalshi Market Favorite</span></div></div>\n'
        f'    </aside>'
    )
    content = re.sub(r'<aside class="spotlight".*?</aside>', spotlight_html, content, flags=re.DOTALL)

    # 8. Update citations timestamp in method paragraph
    today_str = datetime.now(timezone.utc).strftime("%b. %d, %Y")
    method_new = f'<p class="method">Week {lineup_week_num} lineup updated {today_str} with confirmed songs and dance styles for the {short_date} broadcast. The ranking and tier tags are dynamically calculated from verified scoring data, backgrounds, pro records, and audience reach—not affiliated with or endorsed by DWTS or ABC.</p>'
    content = re.sub(r'<p class="method">.*?</p>', method_new, content)

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {HTML_FILE} successfully with dynamic scoring metrics.")

    # 9. Sync dancers.json and dancers.txt in Power Index order for the iOS Shortcut
    active_couples_ranked = [d['name'] for d in active_dancers_data]
    update_dancers_json_and_txt(active_couples_ranked)

def main():
    print("=== DWTS Season 35 Automated Updater ===")
    print(f"Time (UTC): {datetime.now(timezone.utc).isoformat()}")
    
    print("Fetching latest data from Wikipedia...")
    wiki_html = fetch_wiki_html()
    print(f"Wikipedia HTML fetched: {len(wiki_html)} bytes.")

    print("Parsing Wikipedia scoring & episode data...")
    wiki_data = parse_wikipedia_data(wiki_html)

    print(f"Identified {len(wiki_data['week_lineups'])} weeks of data.")
    print(f"Identified {len(wiki_data['eliminated_info'])} eliminated couples.")

    print("Fetching prediction market data from Kalshi & Polymarket public APIs...")
    market_odds = fetch_prediction_market_data()

    # Automatically sync Spotify playlists with latest show order, songs, and cover artwork
    # Runs before update_index_html so spotify_playlists.json and spotify_tracks.json
    # have the latest week playlist URL and direct song links ready to be embedded into index.html
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from spotify_sync import sync_all_dwts_playlists
        print("Syncing Spotify playlists with latest show sequence...")
        current_wk = max(wiki_data['week_lineups'].keys()) if wiki_data.get('week_lineups') else 4
        sync_all_dwts_playlists(wiki_data['week_lineups'], current_wk)
    except Exception as e:
        print(f"[Spotify Sync Note]: {e}")

    print("Updating index.html, dancers.json, and dancers.txt with dynamic scoring & market data...")
    update_index_html(wiki_data, market_odds)

    print("Running formatting validation check...")
    res = os.system(f"python3 {VALIDATE_SCRIPT}")
    if res != 0:
        print("ERROR: Validation script failed!")
        return 1

    print("All updates applied and verified successfully.")
    return 0

if __name__ == '__main__':
    sys.exit(main())
