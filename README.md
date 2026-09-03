# DWTS Voting Shortcut Backend

Backend JSON configurations and auto-update manifest for the **DWTS Voting** iOS Shortcut.

📥 **[Install Shortcut (v1.2 iCloud Link)](https://www.icloud.com/shortcuts/fcd5b15aeb2d431391732c18b5667681)**

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

### 1. Auto-Update Checker (Top of Shortcut)

```text
[# Number] ➔ 1.1
[Set Variable] "CurrentVersion" to [# Number]
[URL] ➔ https://raw.githubusercontent.com/hoveeman/dwts-voting/main/version.json
[Get Contents of URL]
[Get Value for "version" in Contents of URL]

[If Dictionary Value is greater than CurrentVersion]
│
├── [Get Value for "notes" in Contents of URL]
├── [Show alert Dictionary Value] (Show Cancel Button enabled)
├── [Get Value for "url" in Contents of URL]
├── [Open Dictionary Value]
└── [Stop this shortcut]
[End If]
```

### 2. Dynamic Dancers List & Voting (Bottom of Shortcut)

```text
[URL] ➔ https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.json
[Get Contents of URL]
[Get Dictionary from Input]
[Get Value for "dancers" in Dictionary]
[Choose from Dictionary Value]

[Repeat 10 times]
│
└── [Send Message "Selected Item" to "Dancing With The Stars" (215-23)]
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
