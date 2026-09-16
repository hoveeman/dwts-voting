# DWTS Voting Shortcut Backend

Backend JSON configurations and auto-update manifest for the **DWTS Voting** iOS Shortcut.

📥 **[Install Shortcut (v1.5 iCloud Link)](https://www.icloud.com/shortcuts/adb52f4b74424194a18caa038fad8b73)**

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
[# Number] ➔ 1.5
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

### 2. Dynamic Dancers List & Multi-Dancer Voting (With Notifications)

```text
[URL] ➔ https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.json
[Get Contents of URL]

[If Contents of URL contains "dancers"]
│   [Get Value for "dancers" in Contents of URL]
│   [Set Variable "VotingList" to Dictionary Value]
[Otherwise]
│   <!-- Offline or 404 backup -->
│   [List of active dancers]
│   [Set Variable "VotingList" to List]
[End If]

[Choose from List "VotingList" (Select Multiple: ON)]

[Show Notification "💃🕺 Casting votes now... This may take a minute!"]

[Repeat with each item in Chosen Item]
│   [Split Text "Repeat Item" by Custom " & "]
│   [Get First Item from List]
│   [Set Variable "VoteCode" to Item from List]
│   │
│   [Repeat 10 times]
│   │   [Send Message "VoteCode" to "Dancing With The Stars" (215-23)]
│   [End Repeat]
[End Repeat]

[Show Notification "🪩 All votes have been cast!"]
```

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

1. **Judges' Share (%):**
   $$\text{Judges' Share (\%)} = \left( \frac{\text{Couple's Judges' Score}}{\text{Total Judges' Points Awarded to All Couples}} \right) \times 100$$

2. **Viewer Vote Share (%):**
   $$\text{Viewer Share (\%)} = \left( \frac{\text{Couple's Total Public Votes (Online + SMS)}}{\text{Total Public Votes Cast Across All Couples}} \right) \times 100$$

3. **Combined Final Score (%):**
   $$\text{Combined Total (\%)} = \text{Judges' Share (\%)} + \text{Viewer Share (\%)} $$

The couple with the **lowest combined percentage** is placed in jeopardy and eliminated.

### 3. Example Scenario

Suppose **5 couples** remain on a night where 4 judges give scores out of 40. The judges award a total of **150 points** across the night, and viewers cast a combined total of **1,000,000 votes** (SMS + Online):

| Couple | Judges' Score (out of 40) | Judges' Share Calculation | Judges' Share (%) | Public Votes (SMS + Online) | Public Share Calculation | Public Share (%) | Combined Total Calculation | Combined Total (%) | Result |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Couple A** | 36 | `(36 / 150) × 100` | **24.0%** | 150,000 | `(150,000 / 1,000,000) × 100` | **15.0%** | `24.0% + 15.0%` | **39.0%** | Safe |
| **Couple B** | 24 | `(24 / 150) × 100` | **16.0%** | 350,000 | `(350,000 / 1,000,000) × 100` | **35.0%** | `16.0% + 35.0%` | **51.0%** | Safe |
| **Couple C** | 30 | `(30 / 150) × 100` | **20.0%** | 80,000 | `(80,000 / 1,000,000) × 100` | **8.0%** | `20.0% + 8.0%` | **28.0%** | **Eliminated** |
| **Couple D** | 33 | `(33 / 150) × 100` | **22.0%** | 220,000 | `(220,000 / 1,000,000) × 100` | **22.0%** | `22.0% + 22.0%` | **44.0%** | Safe |
| **Couple E** | 27 | `(27 / 150) × 100` | **18.0%** | 200,000 | `(200,000 / 1,000,000) × 100` | **20.0%** | `18.0% + 20.0%` | **38.0%** | Safe |
| **Total** | **150** | `(150 / 150) × 100` | **100.0%** | **1,000,000** | `(1,000,000 / 1,000,000) × 100` | **100.0%** | `100.0% + 100.0%` | **200.0%** | — |

#### How Each Metric Is Calculated:
- **Judges' Share (%):** Take the couple's score, divide by the night's total judge points awarded (`150`), and multiply by 100.  
  *Example (Couple A):* `(36 / 150) × 100 = 24.0%`
- **Public Share (%):** Take the couple's total received votes (SMS + Online), divide by the total public votes cast (`1,000,000`), and multiply by 100.  
  *Example (Couple A):* `(150,000 / 1,000,000) × 100 = 15.0%`
- **Combined Total (%):** Add the couple's Judges' Share to their Public Share.  
  *Example (Couple A):* `24.0% + 15.0% = 39.0%`

> **💡 Why Fan Votes Can Dominate:** Judges' scores are typically tightly clustered (e.g., scores of 7, 8, and 9 only differ by a few percentage points of the total score pool). By contrast, viewer voting percentages can fluctuate dramatically (e.g., Couple B's 35% vs. Couple C's 8%). A dedicated fanbase casting votes via both SMS and online can readily propel a couple with lower technical scores safely past elimination.

