# DWTS Voting Shortcut Backend

Backend JSON configurations for the **DWTS Voting** iOS Shortcut.

## 📡 Raw Endpoints (for Apple Shortcuts)

- **Dancers List**:  
  `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.json`

- **Version Manifest**:  
  `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/version.json`

---

## ⚙️ Shortcut Setup

### 1. Dynamic Dancers List
Replace the hardcoded **List** block in your Shortcut with:
1. **URL** ➔ `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/dancers.json`
2. **Get Contents of URL**
3. **Choose from List** (Select `[Contents of URL]` as the input)

### 2. Auto-Update Checker (Top of Shortcut)
1. **Number** ➔ `1.0` (Save to variable `CurrentVersion`)
2. **URL** ➔ `https://raw.githubusercontent.com/hoveeman/dwts-voting/main/version.json`
3. **Get Contents of URL**
4. **Get Dictionary Value** for key `version` from `[Contents of URL]` (as Number)
5. **If** `Dictionary Value` is greater than `CurrentVersion`:
   - **Get Dictionary Value** for key `notes` from `[Contents of URL]`
   - **Get Dictionary Value** for key `url` from `[Contents of URL]`
   - **Show Alert** ("A new version is available: [notes]. Would you like to download?")
   - **Open URL** (`[url]`)
   - **Stop This Shortcut**
6. **End If**

---

## 🔄 How to Push Updates

- **Eliminating a dancer**: Simply edit `dancers.json` on GitHub. All users will see the updated roster immediately without needing to re-download the shortcut.
- **Updating shortcut logic**:
  1. Update your shortcut locally and bump `CurrentVersion` (e.g. `1.1`).
  2. Create a new iCloud share link.
  3. Edit `version.json` on GitHub with `"version": 1.1`, the new `"url"`, and release `"notes"`.
