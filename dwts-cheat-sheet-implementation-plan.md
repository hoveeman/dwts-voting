# DWTS Season 35 Cheat Sheet — Implementation Plan

How the cheat sheet is built, where its data comes from, and how it stays current every week.

## 1. What it is

- **Artifact:** `dwts-season-35-cheat-sheet` — a static web page hosted on Trent's Muse environment.
- **Public URL:** https://muse.ai/s/dwts-season-35-cheat-sheet-cxv6ltvnxxxmxxw
- **Built/edited via:** `artifact.edit` on the slug, which dispatches a web-artifact builder agent that rebuilds the page. Edits stay local until `artifact.share` publishes them to the public link.
- **Library:** the artifact also lives in the Muse Library for private viewing.

## 2. Page structure

1. **Week header** — week number, theme name (e.g. "Yacht Rock Night"), air date (DWTS Season 35 airs Tuesdays 8/7c on ABC/Disney+).
2. **Active couples (13 remaining)** — one card per couple:
   - Celebrity portrait, age, pro partner, pro's Mirrorball count ("1 Mirrorball" / "2 Mirrorballs").
   - Season running total out of 30 × weeks completed.
   - One score box per week: "Week N · Dance Style · score/30" (e.g. "Week 2 · Tango · 16/30").
   - Prose summary (debut recap, momentum, outlook) and tag pills (SLEEPER, NOSTALGIA, FRONTRUNNER, etc.).
   - Social links.
3. **Voted Off section** — eliminated couples in chronological order, each with elimination date and week, elimination-night dance/song/score, and final season total. Couples are moved here, never deleted.
4. **Rankings** — standings by season total.
5. **How to vote** — voting guide, including Trent's SMS-voting iOS Shortcut.

## 3. Data sources

| Fact | Source |
|---|---|
| Cast, pro pairings | Wikipedia "Dancing with the Stars (American TV series) season 35" |
| Weekly judges' scores, dance styles, eliminations | Wikipedia season 35 scoring chart + results |
| Weekly theme, per-couple songs and dance styles | JustJared, Parade, dancemogul, official DWTS announcements |
| Contestant portraits | Official DWTS headshots (built into the page) |

Rule: every weekly fact is cross-checked against at least two sources before it goes on the page. If the theme or songs haven't been announced yet, they're marked "TBA" — never invented.

## 4. Formatting rules (Trent's standing preferences)

- Score boxes: "Week N · Dance Style · score/30" plus a running season total out of 30 × weeks completed (60 after Week 2, 90 after Week 3, …).
- No per-judge breakdowns (e.g. "6/6/6") and no separate grayscale dance-style/known-for line.
- Weekly-win counts are worded "Mirrorball"/"Mirrorballs" ("0 Mirrorballs", "1 Mirrorball", "2 Mirrorballs").
- Eliminated couples move to the **Voted Off** section with date, week, dance, song, score, and final total.

## 5. Weekly update pipeline

Scheduled job: `dwts-cheat-sheet-weekly-update`, owned by the DWTS voting goal.

1. **When:** every Monday ~9:36 AM ET (first run: Mon Sep 28, 2026). Trent's standing request: "update that every week with theme for the week, the songs and active contestants for that week … every Monday and update the shared link."
2. **Determine the episode:** find the Tuesday of that week (the day after the Monday run) — that is the upcoming episode. Dates are grounded from the system date, never memory.
3. **Research:** `browser.search` (2–3 queries, e.g. "Dancing with the Stars Season 35 Week N theme songs dances") and open at least two independent sources. Collect the upcoming week's theme + per-couple songs/dances, plus the previous episode's scores, dances, and eliminations.
4. **Cross-check:** only publish what two sources agree on; "TBA" anything unannounced.
5. **Edit:** `artifact.edit` with the verified facts — add a new score box per couple ("Week N · Dance Style · score/30"), update season totals, and move eliminated couples to Voted Off.
6. **Publish:** `artifact.share` on the same slug so the public URL serves the new build. Platform rule: every publish/update of a shared link needs a fresh one-tap approval — there is no auto-publish mode. Trent has given standing approval, so the assistant always triggers the share without asking; the one-tap prompt itself can't be skipped.
7. **Report:** short chat note with week number, theme, air date, any elimination, and the link. Failures are always surfaced.
8. **Log:** observations go in the daily log `~/memory/YYYY-MM-DD.md`, not MEMORY.md.

## 6. Change history

- **Sep 19, 2026:** artifact created; weekly Tuesday 8:05 PM voting routine for Julia Stiles set up; iOS Shortcut linked.
- **Sep 25, 2026:** Voted Off section added (Conner & Adele, Sep 15; Sarah Jane & Hailey, Sep 16; Giada & Alan, Sep 22) — eliminated couples are tracked, never removed.
- **Sep 25, 2026:** score history added — weekly scores plus running season totals out of 30 × weeks.
- **Sep 25, 2026:** new score-box format — dance style moved into each week box; per-judge breakdowns and grayscale dance/known-for lines removed.
- **Sep 25, 2026:** win counts reworded to "Mirrorball"/"Mirrorballs".
- **Sep 25, 2026:** standing approval recorded — share link republishes after every update without asking; feature request filed with the Muse team asking for a true auto-publish option.
- **Sep 28, 2026 (scheduled):** first Monday weekly update runs — Week 4 research, scores through Week 3, share-link refresh.
