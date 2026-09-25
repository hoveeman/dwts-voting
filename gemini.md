# DWTS Season 35 Cheat Sheet — Project Guide & Documentation

This document contains all architectural details, data sources, automated update pipelines, validation rules, and hosting guides for the **DWTS Season 35 Fantasy Draft Cheat Sheet**.

---

## 1. Project Overview & File Structure

The project is a static, zero-dependency responsive web application recreating the Muse artifact (`dwts-season-35-cheat-sheet`).

```
/workspaces/dwtscheatsheet/
├── index.html                             # Main single-page web application
├── assets/                                # Full-resolution contestant & host portraits (17 files)
│   ├── amber-glenn-pasha-pashkov.jpg
│   ├── ciara-miller-brandon-armstrong.jpg
│   ├── conner-leavitt-adele-zaikman.jpg
│   ├── connor-wood-rylee-arnold.jpg
│   ├── dwts-hosts.jpg
│   ├── ezra-frech-daniella-karagach.jpg
│   ├── giada-de-laurentiis-alan-bersten.jpg
│   ├── guillermo-rodriguez-witney-carson.jpg
│   ├── harry-shum-jr-jenna-johnson.jpg
│   ├── jackson-olson-emma-slater.jpg
│   ├── jenna-dewan-val-chmerkovskiy.jpg
│   ├── julia-stiles-ezra-sosa.jpg
│   ├── maura-higgins-mark-ballas.jpg
│   ├── sarah-jane-nader-hailey-bills.jpg
│   ├── tatyana-ali-jan-ravnik.jpg
│   ├── taylor-hanson-britt-stewart.jpg
│   └── tyler-cameron-sharna-burgess.jpg
├── scripts/
│   └── validate_cheat_sheet.py           # Automated formatting compliance validator
├── dwts-cheat-sheet-implementation-plan.md# Original Muse implementation plan
└── gemini.md                              # This complete documentation file
```

---

## 2. Page Features & Formatting Rules

The cheat sheet follows strict formatting rules to maintain editorial consistency:

1. **Header**:
   - Week number, date, and theme title (e.g. *Week 3 draft board · Sept. 29, 2026*).
   - Broadcast details: Tuesdays 8/7c on ABC and Disney+.
2. **Active Power Board (13 Couples)**:
   - Filterable dynamically by: `All`, `Anchors`, `Sleepers`, `Dance edge`, `Athletes`, and `Social reach`.
   - **Score Boxes**: Formatted as `"Week N · Dance Style · score/30"` with running season totals out of $30 \times \text{completed weeks}$ (e.g. `40/60` after Week 2).
   - **Mirrorball Counts**: Worded explicitly as `"0 Mirrorballs"`, `"1 Mirrorball"`, `"2 Mirrorballs"`, `"3 Mirrorballs"`.
   - **Social Reach**: Verified handles and follower counts for both celebrity and pro partner.
   - **No per-judge score breakdowns** (e.g. `6/6/6` is omitted).
3. **Voted Off Section**:
   - Preserves eliminated couples chronologically with elimination dates, exit night dances, songs, and final season totals:
     - *Conner Leavitt & Adele Zaikman* (Sept. 15, 2026 · Week 1 Night 1 · Salsa · Final: 12/30)
     - *Sarah Jane Nader & Hailey Bills* (Sept. 16, 2026 · Week 1 Night 2 · Jive · Final: 14/30)
     - *Giada De Laurentiis & Alan Bersten* (Sept. 22, 2026 · Week 2 · Salsa · Final: 28/60)
4. **Draft-Day Rulebook / Voting**:
   - Explains online voting at `dwtsvote.abc.com` (10 votes/couple) and SMS voting to `21523` (10 votes/couple).
   - Direct link to Trent's Apple iOS SMS-voting shortcut: [iCloud Shortcut](https://www.icloud.com/shortcuts/3e951e5ba20b49dc82f5abded923b179).
5. **Theme-Night Edges & Lineup**:
   - Confirmed dances, songs, and performance order for the current week, plus tactical edges across the 11-week calendar.

---

## 3. Data Sources & Verification Rules

Every piece of data must adhere to strict sourcing rules before being added to `index.html`:

| Category | Primary Sources | What is Extracted |
|---|---|---|
| **Cast Pairings & Pro Résumés** | • [Wikipedia: Dancing with the Stars Season 35](https://en.wikipedia.org/wiki/Dancing_with_the_Stars_(American_TV_series)_season_35)<br>• [ABC / Disney Press Releases](https://abc.com/news/98f4bab4-757f-4f1a-a2e9-d392ff248d56/category/1138628)<br>• [Associated Press](https://990theanswer.com/news/entertainment/meet-the-2026-dancing-with-the-stars-cast/f1d587db5657824343c2b258b0695695) | Celebrity age, profession/claim to fame, assigned pro partner, and pro's historical Mirrorball trophy count. |
| **Weekly Scores, Dances & Eliminations** | • [Wikipedia: Season 35 Weekly Scoring Chart](https://en.wikipedia.org/wiki/Dancing_with_the_Stars_(American_TV_series)_season_35)<br>• [Entertainment Weekly Recaps](https://ew.com/dancing-with-the-stars-season-35-premiere-night-2-recap-12124737)<br>• Official ABC post-show press releases | Weekly judge totals out of 30, completed dance styles, elimination dates, exit dances/songs, and cumulative season points. |
| **Upcoming Themes, Songs & Dance Styles** | • [Entertainment Weekly Preview Coverage](https://ew.com/dancing-with-the-stars-season-35-week-2-theme-songs-dances-revealed-12126423)<br>• [Parade Theme Calendar](https://parade.com/tv/dancing-with-the-stars-season-35-themes-revealed)<br>• *JustJared*, *Dance Mogul*, & official DWTS releases | Upcoming theme title, each active couple's routine dance style, and song title/artist. |
| **Contestant & Host Portraits** | • [Disney / ABC Official Press Room](https://abc.com/news/98f4bab4-757f-4f1a-a2e9-d392ff248d56/category/1138628)<br>• [Parade Season 35 Gallery](https://parade.com/tv/dancing-with-the-stars-2026-season-35) | High-resolution official headshots for each couple and hosts (saved in `assets/`). |
| **Betting Markets & Power Shifts** | • [RotoWire DWTS Odds](https://www.rotowire.com/article/dancing-with-the-stars-odds-131116)<br>• [Action Network Market Movements](https://www.actionnetwork.com/news/who-got-eliminated-on-dancing-with-the-stars-dwts-season-35-winner-odds-shift-after-two-night-premiere)<br>• Prediction market contract tracking (e.g. Kalshi) | Implied win probabilities, top tier odds, and post-premiere market momentum shifts. |
| **Public Social Reach** | • [Social Blade](https://socialblade.com)<br>• Direct public profiles (Instagram & TikTok)<br>• Agency talent rosters (*MN2S*, *Social Veins*, *Heepsy*) | Verified approximate follower counts and handles for both the celebrity and pro partner. |
| **Ballroom Storylines & News** | • [USA Today Entertainment](https://www.usatoday.com/story/entertainment/tv-streaming/2026/09/17/andy-cohen-julia-stiles-apology-dancing-with-the-stars/91815226007/)<br>• [Palm Beach Post](https://www.palmbeachpost.com/story/entertainment/television/2026/09/16/dancing-with-stars-voting-crash-who-eliminated-went-home-when-how-watch-vote-tonight/91788281007/)<br>• [Primetimer](https://www.primetimer.com/features/dancing-with-the-stars-how-to-vote-for-celebrities-competing-in-season-35-details-explored) | Broadcast incidents, scoring adjustments, media storylines, and fan sentiment. |

### Verification Rules
1. **Two-Source Rule**: Every weekly announcement (theme, songs, dances) must be confirmed by **at least two independent publications**.
2. **Never Speculate**: Unannounced songs or themes are labeled **`TBA`**—never guessed.
3. **Date Grounding**: Dates and week numbers are grounded directly from the live system clock.
4. **Site Access / Permissions**: All information is gathered from public web pages; no manual approval or user confirmation is required to read these sources.

---

## 4. Weekly Automated Update Pipeline

- **Trigger Schedule**: Every Monday at **9:36 AM EDT** (`36 9 * * 1`)
- **First Run**: Monday, September 28, 2026

### Step-by-Step Execution:
1. **Determine Episode**: Find the Tuesday of the current week (day after Monday) to identify the upcoming episode number and date.
2. **Research & Cross-Check**: Collect the upcoming week's theme, songs, and dances, plus the previous episode's scores, dances, and eliminations across 2+ sources.
3. **Update `index.html`**:
   - Update header week number, date, and theme.
   - Append a new score box per active couple (`"Week N · Dance Style · score/30"`).
   - Recalculate running season totals out of $30 \times \text{weeks completed}$.
   - Move eliminated couples to the `Voted off` section with full exit stats.
   - Update the lineup with confirmed songs/dances.
   - Refresh storylines and update the citations timestamp.
4. **Validate**: Run `python3 scripts/validate_cheat_sheet.py` to ensure all formatting constraints pass.

---

## 5. Hosting & Deployment Guides

Since the project is completely static HTML/CSS/JS with local images, hosting is 100% free with zero configuration on either GitHub Pages or Cloudflare Pages.

### Option A: GitHub Pages (Recommended)

1. **Initialize Git and Commit**:
   ```bash
   git init
   git add .
   git commit -m "feat: complete DWTS Season 35 cheat sheet"
   ```

2. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```

3. **Enable GitHub Pages**:
   - Open your repository on GitHub.
   - Navigate to **Settings** → **Pages**.
   - Under **Build and deployment** → **Source**, select **Deploy from a branch**.
   - Set **Branch** to `main` and folder to `/(root)`, then click **Save**.
   - The site goes live at: `https://<your-username>.github.io/<repo-name>/`

4. *(Optional)* **Automated Weekly GitHub Action**:
   Create `.github/workflows/weekly-update.yml` to run the updater every Monday automatically in the cloud, commit changes, and trigger GitHub Pages redeployment.

---

### Option B: Cloudflare Pages

#### Method 1: Connected to GitHub (Auto-deploys on push)
1. Push your repository to GitHub using Option A.
2. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/) → **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**.
3. Select your repository.
4. Build configuration:
   - **Framework preset:** `None`
   - **Build command:** *(leave empty)*
   - **Build output directory:** `/` (root)
5. Click **Save and Deploy**. Cloudflare provisions a `*.pages.dev` domain with instant global edge caching and free custom domain support.

#### Method 2: Direct Deploy via Wrangler CLI
Deploy without pushing to git:
```bash
npx wrangler pages deploy . --project-name=dwts-cheat-sheet
```

---

## 6. Local Testing & Validation

- **Run formatting validation**:
  ```bash
  python3 scripts/validate_cheat_sheet.py
  ```
- **Preview locally**:
  ```bash
  python3 -m http.server 8000
  ```
  Open `http://localhost:8000` in any browser.
