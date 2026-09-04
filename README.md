# DWTS Voting Shortcut Backend

Backend JSON configurations and auto-update manifest for the **DWTS Voting** iOS Shortcut.

📥 **[Install Shortcut (v1.4 iCloud Link)](https://www.icloud.com/shortcuts/6788cf4f1a00420380fa306c0bc5b4e3)**

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
[# Number] ➔ 1.4
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

### 2. Dynamic Dancers List & Multi-Dancer Voting (With Offline Fallback)

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

[Repeat with each item in Chosen Item]
│   [Repeat 10 times]
│   │   [Send Message "Repeat Item" to "Dancing With The Stars" (215-23)]
│   [End Repeat]
[End Repeat]
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
