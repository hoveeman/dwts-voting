# DWTS Voting Shortcut Backend & Season 35 Cheat Sheet

Backend JSON configurations, auto-update manifest for the **DWTS Voting** iOS Shortcut, and the live interactive **DWTS Season 35 Fantasy Draft Cheat Sheet**.

🌐 **Live Website**: [https://hoveeman.github.io/dwts-voting/](https://hoveeman.github.io/dwts-voting/)  
📥 **iOS Shortcut**: [Install Shortcut (v1.6 iCloud Link)](https://www.icloud.com/shortcuts/3e951e5ba20b49dc82f5abded923b179)

---

## 📡 Live Endpoints (for Apple Shortcuts)

- **Dancers List (JSON)**:  
  `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.json`

- **Version Manifest**:  
  `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/version.json`

- **Dancers List (Plain Text fallback)**:  
  `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.txt`

---

## ⚙️ Shortcut Architecture

### 1. Auto-Update Checker (Top of Shortcut with Release Notes & "Vote First")

```text
[# Number] ➔ 1.6
[Set Variable] "CurrentVersion" to [# Number]
[URL] ➔ https://raw.githubusercontent.com/hoveeman/dwts-voting/main/version.json
[Get Contents of URL]

[If Contents of URL contains "version"]
│   [Get Dictionary from Contents of URL]
│   [Get Value for "version" in Dictionary]
│   [If Dictionary Value is greater than CurrentVersion]
│   │   [Get Value for "notes" in Contents of URL]
│   │   [Set Variable "ReleaseNotes" to Dictionary Value]
│   │   [Text] "Update is available!

What's New:
[ReleaseNotes]"
│   │   [Choose from Menu Text]
│   │   ├── ⬇️ Update Now
│   │   │   [Get Value for "url" in Contents of URL]
│   │   │   [Open URL Dictionary Value]
│   │   │   [Stop this shortcut]
│   │   └── 🪩 Vote First
│   │       <!-- Continues to voting immediately -->
│   │   [End Menu]
│   [End If]
[End If]
```

### 2. Dynamic Dancers List & Multi-Dancer Voting (v1.6+ Full Names Architecture)

```text
[URL] ➔ https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.json
[Get Contents of URL]

[If Contents of URL contains "dancers_v2"]
│   [Get Dictionary from Contents of URL]
│   [Get Value for "dancers_v2" in Dictionary]
│   [Set Variable "DancersDict" to Dictionary Value]
│   [Get Dictionary Keys from DancersDict]
│   [Set Variable "VotingList" to Dictionary Keys]
[Otherwise]
│   <!-- Fallback for legacy v1.5 or offline -->
│   [Get Value for "dancers" in Dictionary]
│   [Set Variable "VotingList" to Dictionary Value]
[End If]

[Choose from List "VotingList" (Select Multiple: ON)]

[Show Notification "💃🕺 Casting votes now... This may take a minute!"]

[Repeat with each item in Chosen Item]
│   <!-- Look up exact SMS keyword from the dictionary -->
│   [Get Value for "Repeat Item" in DancersDict]
│   [Set Variable "VoteCode" to Dictionary Value]
│   │
│   [Repeat 10 times]
│   │   [Send Message "VoteCode" to "Dancing With The Stars" (215-23)]
│   [End Repeat]
[End Repeat]

[Show Notification "🪩 All votes have been cast!"]
```

> **Note for v1.5 Backward Compatibility:** `dancers.json` retains the legacy `"dancers"` array so older shortcuts won't fail if a user skips or delays the update.

---

## 🔄 How to Push Updates

### For Weekly Dancer Eliminations (Zero-Maintenance for Users)
1. Open [dancers.json](https://github.com/hoveeman/dwts-voting/blob/main/dancers.json) directly on GitHub.
2. Delete the eliminated contestant(s) and commit changes.
3. **No new shortcut or iCloud link needed.** Every user's shortcut will automatically show the updated roster on their next run.

### For Shortcut Feature / Logic Changes
1. Update your shortcut locally in the Shortcuts app.
2. Bump the internal version number at the top (e.g., `# 1.1` ➔ `# 1.2`).
3. Click the Share button ➔ **Copy iCloud Link**.
4. Open [version.json](https://github.com/hoveeman/dwts-voting/blob/main/version.json) on GitHub and update:
   - `"version"`: `1.2`
   - `"url"`: `"<new iCloud link>"`
   - `"notes"`: `"<description of changes>"`
5. When users run the shortcut, they will be prompted to update and tap **Replace**.

---

## 🧮 How Votes & Elimination Scores Are Tallied

*Dancing with the Stars* determines eliminations using a **50/50 weighted split** between judges' scores and viewer votes. Because judges award points while viewers cast raw votes, the show converts both sides into **percentages of the night's total** before adding them together.

### 1. Combining Text (SMS) & Online Votes

- **1:1 Equal Weighting:** Votes cast via SMS and votes cast online carry equal weight (1 text vote = 1 online vote).
- **Vote Limits:** Viewers can cast up to **10 votes online** (via [dwtsvote.abc.com](https://dwtsvote.abc.com)) and **10 votes via SMS** (texting the celebrity's first name to `21523`), allowing up to **20 votes per couple** per voting window.
- **Total Public Votes:** All valid SMS and online votes received for a couple are summed to determine that couple's total viewer vote count.

### 2. The 50/50 Percentage Formula

```text
                     Couple's Judges' Score
Judges' Share (%) = ──────────────────────────── × 100
                     Night's Total Judge Points

                    Couple's Received Public Votes
Public Share (%)  = ────────────────────────────── × 100
                      Night's Total Public Votes

Combined Score    = Judges' Share (%) + Public Share (%)
```

The couple with the **lowest combined percentage** is placed in jeopardy and eliminated.

### 3. Example Scenario

Suppose **5 couples** remain on a night with **3 judges** (each awarding up to 10 points, for a maximum score of **30** per couple). 

The judges award a combined total of **120 points** across all routines, and viewers cast **1,000,000 total votes** (SMS + Online):

| Couple | Judges' Score (Max 30) | Judges' Share (%) | Public Votes (SMS + Web) | Public Share (%) | Combined Total (%) | Result |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Couple A** | 27 | **22.5%** | 150,000 | **15.0%** | **37.5%** | Safe |
| **Couple B** | 18 | **15.0%** | 350,000 | **35.0%** | **50.0%** | Safe |
| **Couple C** | 24 | **20.0%** | 80,000 | **8.0%** | **28.0%** | **Eliminated** |
| **Couple D** | 21 | **17.5%** | 170,000 | **17.0%** | **34.5%** | Safe |
| **Couple E** | 30 | **25.0%** | 250,000 | **25.0%** | **50.0%** | Safe |
| **Total** | **120** | **100.0%** | **1,000,000** | **100.0%** | **200.0%** | — |

#### 📱 Step-by-Step Calculation Breakdown

To easily follow the exact math on any screen size:

* **Couple A:**
  * **Judges' Share:** `(27 / 120) × 100 = 22.5%`
  * **Public Share:** `(150,000 / 1,000,000) × 100 = 15.0%`
  * **Combined Total:** `22.5% + 15.0% = 37.5%` *(Safe)*

* **Couple B:** *(Low judges' score, massive fan vote)*
  * **Judges' Share:** `(18 / 120) × 100 = 15.0%`
  * **Public Share:** `(350,000 / 1,000,000) × 100 = 35.0%`
  * **Combined Total:** `15.0% + 35.0% = 50.0%` *(Safe)*

* **Couple C:** *(Decent judges' score, lowest fan vote)*
  * **Judges' Share:** `(24 / 120) × 100 = 20.0%`
  * **Public Share:** `(80,000 / 1,000,000) × 100 = 8.0%`
  * **Combined Total:** `20.0% + 8.0% = 28.0%` *(Eliminated)*

* **Couple D:**
  * **Judges' Share:** `(21 / 120) × 100 = 17.5%`
  * **Public Share:** `(170,000 / 1,000,000) × 100 = 17.0%`
  * **Combined Total:** `17.5% + 17.0% = 34.5%` *(Safe)*

* **Couple E:** *(Perfect 30 score + high fan vote)*
  * **Judges' Share:** `(30 / 120) × 100 = 25.0%`
  * **Public Share:** `(250,000 / 1,000,000) × 100 = 25.0%`
  * **Combined Total:** `25.0% + 25.0% = 50.0%` *(Safe)*

> **💡 Why Fan Votes Can Dominate:** Judges' scores usually stay within a narrow range (e.g., scores of 6, 7, 8, 9 only vary by a few percentage points of the total score pool). By contrast, viewer voting percentages can fluctuate dramatically (e.g., Couple B's 35% vs. Couple C's 8%). A dedicated fanbase casting votes via both SMS and online can readily propel a couple with lower technical scores safely past elimination.

---

## 🪩 Season 35 Cheat Sheet & Daily Worker

The repository includes the full interactive web application for the **DWTS Season 35 Fantasy Draft Cheat Sheet**:

- **Live URL**: [https://hoveeman.github.io/dwts-voting/](https://hoveeman.github.io/dwts-voting/)
- **Daily Automated Updates**: Powered by a GitHub Actions worker ([`.github/workflows/daily-update.yml`](.github/workflows/daily-update.yml)) running daily at 11:00 PM ET. The worker scrapes live scoring, songs, dance choices, and eliminations from Wikipedia, updating `index.html` and synchronizing the iOS shortcut endpoints (`dancers.json`, `dancers.txt`).

