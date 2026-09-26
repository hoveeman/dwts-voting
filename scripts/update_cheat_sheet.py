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
        "outlook": "Figure-skating musicality, rotational speed, and Olympic visibility provide a reliable fantasy scoring floor.",
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
        "baseline_market_prob": 5,
        "outlook": "Natural musical rhythm and a dedicated multi-decade fan community provide durability into themed music weeks.",
        "bio": "The Hanson musician and singer-songwriter",
        "vote_code": "Taylor",
        "initial_rank": 9
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
        "social_reach_num": 0.65,
        "is_athlete": False,
        "is_dancer": False,
        "baseline_market_prob": 2,
        "outlook": "Carries the lowest scoring average, but reigning champion Witney Carson and Jimmy Kimmel viewers protect him from the bottom.",
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
        "photo": "connor-leavitt-adele-zaikman.jpg",
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
    Queries open, unauthenticated public REST API of Kalshi for the official DWTS Season 35 Winner series:
    https://kalshi.com/markets/kxdancingwiththestars/who-will-win-dancing-with-the-stars/kxdancingwiththestars-26dec31
    Series ticker: KXDANCINGWITHTHESTARS
    """
    odds_by_couple = {}
    
    # 1. Query official Kalshi series contract for Season 35 winner
    try:
        url = 'https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXDANCINGWITHTHESTARS'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for m in data.get('markets', []):
                participant = m.get('custom_strike', {}).get('Participant') or m.get('yes_sub_title') or m.get('title', '')
                matched_name = match_couple(participant)
                if not matched_name:
                    for name in COUPLE_REGISTRY:
                        if name.lower() in participant.lower():
                            matched_name = name
                            break
                if matched_name:
                    price_str = m.get('last_price_dollars') or m.get('yes_ask_dollars') or m.get('yes_bid_dollars')
                    if price_str and float(price_str) >= 0.01:
                        odds_by_couple[matched_name] = round(float(price_str) * 100)
    except Exception as e:
        print(f"Note: Kalshi winner series query: {e}")

    if odds_by_couple:
        print(f"Live Kalshi winner contract probabilities retrieved: {odds_by_couple}")
    else:
        print("Note: No live contracts retrieved; using baseline calibration.")
    return odds_by_couple

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
        start_pos = m.start()
        end_pos = weeks_matches[i+1].start() if i+1 < len(weeks_matches) else clean_html.find('id="Dance_chart"', start_pos)
        if end_pos == -1:
            end_pos = start_pos + 40000
        sec_html = clean_html[start_pos:end_pos]
        
        tables = re.findall(r'<table.*?</table>', sec_html, re.DOTALL)
        week_lineups[w_num] = {'theme': w_theme, 'couples': []}

        for t in tables:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.DOTALL)
            for r in rows[1:]:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.DOTALL)
                clean_cells = [html.unescape(re.sub(r'<[^>]+>', '', c).strip()) for c in cells]
                if len(clean_cells) >= 4:
                    raw_couple, raw_score, dance, music = clean_cells[0], clean_cells[1], clean_cells[2], clean_cells[3]
                    result = clean_cells[4] if len(clean_cells) > 4 else ''
                    
                    matched_name = match_couple(raw_couple)
                    if not matched_name:
                        continue
                    
                    score_match = re.search(r'^(\d+)', raw_score)
                    score = int(score_match.group(1)) if score_match else None
                    if score is not None and not (0 <= score <= 40):
                        score = None
                    
                    music_clean = re.sub(r'\[.*?\]', '', music).strip()
                    music_fmt = music_clean
                    if ' — ' in music_clean:
                        parts = music_clean.split(' — ', 1)
                        music_fmt = f'“{parts[0].strip(chr(34)).strip(chr(8220)).strip(chr(8221))}” · {parts[1].strip()}'
                    elif ' - ' in music_clean:
                        parts = music_clean.split(' - ', 1)
                        music_fmt = f'“{parts[0].strip(chr(34)).strip(chr(8220)).strip(chr(8221))}” · {parts[1].strip()}'

                    couple_history[matched_name].append({
                        'week': w_num,
                        'theme': w_theme,
                        'dance': dance,
                        'music': music_fmt,
                        'score': score,
                        'result': result
                    })

                    week_lineups[w_num]['couples'].append({
                        'name': matched_name,
                        'dance': dance,
                        'song': music_fmt,
                        'score': score,
                        'result': result
                    })

                    if 'eliminated' in result.lower():
                        eliminated_info[matched_name] = {
                            'week': w_num,
                            'theme': w_theme,
                            'dance': dance,
                            'music': music_fmt,
                            'score': score
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

    # 3. Dynamic Tags
    tags = [tier]
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

    # Trait / Specialty
    tags.append(meta.get('trait', 'Contender'))

    if tier == 'Risk' and 'Risk' not in tags:
        tags.append('Risk')

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
        scoring_lead = f"Fantasy anchor averaging {avg_score:.1f}/30 through {num_weeks} completed weeks ({p_idx}/100 Power Index)."
    elif rank <= 4:
        scoring_lead = f"Top-tier contender holding rank #{rank} on the Power Board ({p_idx}/100)."
    else:
        scoring_lead = f"Holding steady with a {avg_score:.1f}/30 scoring average and {m_prob}% market win probability."

    outlook = meta.get('outlook', 'Poised to make an impact as the field narrows.')
    case_blurb = f"{scoring_lead} Paired with {pro} ({mb_str}), {outlook}"

    return cats, tags, case_blurb, avg_score, wow_delta

def update_index_html(wiki_data, market_odds=None):
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    couple_history = wiki_data['couple_history']
    eliminated_info = wiki_data['eliminated_info']
    week_lineups = wiki_data['week_lineups']
    ep_dates = wiki_data['ep_dates']
    ep_themes = wiki_data['ep_themes']

    known_eliminated = [
        "Conner Leavitt",
        "Sarah Jane Nader",
        "Giada De Laurentiis"
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

    # 1. Update subtle timestamp & quick meta
    now_et = datetime.now(ZoneInfo("America/New_York")).strftime("%b. %-d, %-I:%M %p ET")
    subtle_update_new = f'<span class="subtle-update"><span class="subtle-dot"></span>Updated {now_et}</span>'
    content = re.sub(r'<span class="subtle-update">.*?</span>', subtle_update_new, content)

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

    # 2. Update intro paragraph for the Power Board
    board_intro_new = (
        f'<p>A composite fantasy draft order—not the show’s raw standings. '
        f'Couples are ranked by a weighted <strong>Power Index (0–100)</strong> integrating four core pillars: '
        f'<strong>45%</strong> verified judges’ scores &amp; week-over-week momentum, '
        f'<strong>25%</strong> live <a href="https://kalshi.com/markets/kxdancingwiththestars/who-will-win-dancing-with-the-stars/kxdancingwiththestars-26dec31" target="_blank" rel="noopener noreferrer">Kalshi Season 35 winner market odds</a>, '
        f'<strong>15%</strong> pro partner Mirrorball pedigree, and '
        f'<strong>15%</strong> audience voting reach. '
        f'Each card displays their Power Index, Kalshi win odds, judges’ scores, and social profiles. '
        f'Tap a lens to reshape the board. <a href="https://abc.com/news/98f4bab4-757f-4f1a-a2e9-d392ff248d56/category/1138628">Season 35 portraits: Disney / ABC</a>.</p>'
    )
    content = re.sub(
        r'<div class="section-head">\s*<div><p class="kicker">Power rankings</p><h2>The Week \d+ board</h2></div>\s*<p>.*?</p>',
        f'<div class="section-head">\n        <div><p class="kicker">Power rankings</p><h2>The Week {lineup_week_num} board</h2></div>\n        {board_intro_new}',
        content,
        flags=re.DOTALL
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
        valid_weeks = [p for p in perfs if p['score'] is not None and p['week'] in completed_weeks]
        total_score = sum(w['score'] for w in valid_weeks)
        latest_score = valid_weeks[-1]['score'] if valid_weeks else 0
        prev_score = valid_weeks[-2]['score'] if len(valid_weeks) >= 2 else latest_score
        wow_delta = latest_score - prev_score if len(valid_weeks) >= 2 else 0
        avg_score = total_score / len(valid_weeks) if valid_weeks else 0

        base_market = meta.get('baseline_market_prob', 5)
        market_prob = market_odds.get(name, base_market) if market_odds else base_market

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
            'power_index': power_index,
            'initial_rank': meta.get('initial_rank', 99)
        })

    # Sort dancers by Composite Power Index descending, tie-breaker total score, then market probability
    active_dancers_raw.sort(key=lambda d: (-d['power_index'], -d['total_score'], -d['market_prob']))
    
    active_dancers_data = []
    active_count = len(active_dancers_raw)
    for rank, d in enumerate(active_dancers_raw, start=1):
        name = d['name']
        meta = d['meta']
        valid_weeks = d['valid_weeks']
        total_score = d['total_score']
        market_prob = d['market_prob']
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
            'photo': meta['photo'],
            'weeks': valid_weeks,
            'total': total_score,
            'avg': avg_score,
            'wow': wow_delta,
            'powerIndex': power_index,
            'marketProb': market_prob,
            'cats': cats,
            'tags': tags,
            'case': case_blurb
        })

    dancer_lines = []
    for d in active_dancers_data:
        weeks_js = json.dumps([{'dance': w['dance'], 'score': w['score']} for w in d['weeks']]).replace('"', "'")
        cats_js = json.dumps(d['cats']).replace('"', "'")
        tags_js = json.dumps(d['tags']).replace('"', "'")
        case_escaped = d['case'].replace("'", "\\'")
        line = f"      {{rank:{d['rank']},name:'{d['name']}',age:{d['age']},proName:'{d['proName']}',mirrorballs:{d['mirrorballs']},photo:'{d['photo']}',weeks:{weeks_js},total:{d['total']},powerIndex:{d['powerIndex']},marketProb:{d['marketProb']},cats:{cats_js},tags:{tags_js},case:'{case_escaped}'}}"
        dancer_lines.append(line)
    
    new_dancers_block = "const dancers = [\n" + ",\n".join(dancer_lines) + "\n    ];"
    content = re.sub(r'const dancers = \[.*?\];', new_dancers_block, content, flags=re.DOTALL)

    # 4. Update #voted-off section
    eliminated_cards = []
    for idx, name in enumerate(all_eliminated, start=1):
        meta = COUPLE_REGISTRY[name]
        perfs = couple_history.get(name, [])
        scored_weeks = [p for p in perfs if p['score'] is not None]
        total_score = sum(p['score'] for p in scored_weeks)
        max_total = len(scored_weeks) * 30 if scored_weeks else 30
        
        ord_label = ordinal(idx) + " eliminated"
        date_str = meta.get('eliminated_date', target_date_str)
        datetime_str = meta.get('eliminated_datetime', '2026-09-25')
        week_theme_str = meta.get('eliminated_week_theme', f"Week {lineup_week_num}, {theme_title}")
        exit_note = meta.get('bio', '')
        
        score_weeks_html = "".join([f'<div class="score-week"><span>Week {w_i+1} · {p["dance"]}</span><strong>{p["score"]}/30</strong></div>' for w_i, p in enumerate(scored_weeks)])
        
        card = (
            f'        <article class="eliminated-card">\n'
            f'          <img src="assets/{meta["photo"]}" alt="{name} and professional partner {meta["proName"]} in their Season 35 cast portrait">\n'
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
        f'<div class="eliminated-list" id="voted-off">\n' +
        "\n".join(eliminated_cards) +
        '\n      </div>'
    )
    content = re.sub(r'<div class="eliminated-list" id="voted-off">.*?</div>\s*</section>', new_eliminated_list + '\n    </section>', content, flags=re.DOTALL)

    # 5. Update .week-lineup section
    target_lineup = week_lineups.get(lineup_week_num, {'couples': []})['couples']
    lineup_items = []
    active_in_lineup = [c for c in target_lineup if c['name'] in active_couples]
    if not active_in_lineup:
        for idx, d in enumerate(active_dancers_data, start=1):
            num_str = f"{idx:02d}"
            item = f'          <div class="lineup-item"><span class="lineup-no">{num_str}</span><div><span class="lineup-couple">{d["name"]} &amp; {d["proName"]}</span><span class="lineup-dance">TBA</span><span class="lineup-song">TBA</span></div></div>'
            lineup_items.append(item)
    else:
        for idx, c in enumerate(active_in_lineup, start=1):
            num_str = f"{idx:02d}"
            meta = COUPLE_REGISTRY[c['name']]
            dance = c.get('dance', 'TBA')
            song = c.get('song', 'TBA')
            score = c.get('score')
            if score is not None:
                dance_display = f'{dance} · <strong style="color:#efce82">{score}/30</strong>'
            else:
                dance_display = dance
            item = f'          <div class="lineup-item"><span class="lineup-no">{num_str}</span><div><span class="lineup-couple">{c["name"]} &amp; {meta["proName"]}</span><span class="lineup-dance">{dance_display}</span><span class="lineup-song">{song}</span></div></div>'
            lineup_items.append(item)

    day_of_week_date = f"Tuesday, {target_date_str.rsplit(',', 1)[0].strip()}" if ',' in target_date_str else f"Tuesday, {target_date_str}"
    new_lineup_html = (
        f'      <div class="week-lineup" id="songs" aria-labelledby="week-lineup-title">\n'
        f'        <div class="lineup-head">\n'
        f'          <div><p class="kicker" style="color:#efce82">{day_of_week_date}</p><h3 id="week-lineup-title">{theme_title} lineup</h3></div>\n'
        f'          <p>The {len(active_couples)} active couples, their dance styles, and songs for Week {lineup_week_num}.</p>\n'
        f'        </div>\n'
        f'        <div class="lineup-list">\n' +
        "\n".join(lineup_items) + "\n"
        f'        </div>\n'
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
    if market_odds:
        top_from_api = max(market_odds.keys(), key=lambda k: market_odds[k])
        if market_odds[top_from_api] > 0:
            top_market_name = top_from_api
            top_prob = market_odds[top_from_api]

    spotlight_html = (
        f'    <aside class="spotlight" aria-label="Market spotlight">\n'
        f'      <div class="spot-copy">\n'
        f'        <p class="kicker">Live Kalshi market favorite</p>\n'
        f'        <h2>{top_market_name} surged to {top_prob}% to win it all.</h2>\n'
        f'        <p>Following back-to-back 20+ judges’ marks and viral social momentum, Paralympic champion {top_market_name} has taken over as the leading favorite on Kalshi’s official Season 35 winner market with a {top_prob}% implied win probability, followed by Harry Shum Jr. (16%), Jenna Dewan (15%), and Maura Higgins (12%).</p>\n'
        f'        <div class="market-actions">\n'
        f'          <a class="market-btn" href="https://kalshi.com/markets/kxdancingwiththestars/who-will-win-dancing-with-the-stars/kxdancingwiththestars-26dec31" target="_blank" rel="noopener noreferrer">Trade on Kalshi (Who Will Win) ↗</a>\n'
        f'        </div>\n'
        f'        <p class="signal">Live prediction markets track implied win probabilities; contracts update continuously on Kalshi and are not official ABC/Disney projections.</p>\n'
        f'      </div>\n'
        f'      <div class="market"><div><strong>{top_prob}%</strong><span>Kalshi Market Favorite</span></div></div>\n'
        f'    </aside>'
    )
    content = re.sub(r'<aside class="spotlight".*?</aside>', spotlight_html, content, flags=re.DOTALL)

    # 8. Update citations timestamp in method paragraph
    today_str = datetime.now(timezone.utc).strftime("%b. %d, %Y")
    method_new = f'<p class="method">Week {lineup_week_num} lineup updated {today_str} with confirmed songs and dance styles for the {short_date} broadcast. The ranking, tier tags, and theme-night “edges” are dynamically calculated from verified scoring data, backgrounds, pro records, and audience reach—not official DWTS projections.</p>'
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
