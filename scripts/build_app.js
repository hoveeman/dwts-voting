#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const rootDir = path.resolve(__dirname, '..');
const wwwDir = path.join(rootDir, 'www');

console.log('[Build] Preparing www/ directory for Capacitor native build...');

if (fs.existsSync(wwwDir)) {
  fs.rmSync(wwwDir, { recursive: true, force: true });
}
fs.mkdirSync(wwwDir, { recursive: true });

const filesToCopy = [
  'index.html',
  'privacy.html',
  'manifest.webmanifest',
  'dancers.json',
  'dancers.txt',
  'live_state.json',
  'version.json',
  'spotify_tracks.json',
  'spotify_playlists.json',
  'sw.js',
  'favicon.ico'
];

for (const file of filesToCopy) {
  const src = path.join(rootDir, file);
  const dest = path.join(wwwDir, file);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, dest);
  }
}

// Copy assets directory recursively
function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

const assetsSrc = path.join(rootDir, 'assets');
const assetsDest = path.join(wwwDir, 'assets');
if (fs.existsSync(assetsSrc)) {
  copyDirSync(assetsSrc, assetsDest);
}

console.log(`[Build] Successfully assembled ${filesToCopy.length} files + assets directory into www/`);
