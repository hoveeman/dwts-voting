#!/usr/bin/env python3
"""
Generate pixel-perfect native app icons and splash assets for iOS and Android.
Ensures Android adaptive icons and splash screen adhere to the 66dp safe-zone specification
so no mirrorball facets, stars, stands, or badges get cropped by launcher masks or Android 12+ splash screens.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFilter

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ICON = os.path.join(ROOT_DIR, 'assets', 'icon-512-ballroom.png')
NAVY_BG = (16, 43, 85) # #102b55
DARK_BG = (17, 20, 22) # #111416 dark ballroom theme background

def extract_transparent_foreground(src_path):
    src = Image.open(src_path).convert('RGBA')
    w, h = src.size

    # Badge mask (rounded rectangle at bottom)
    badge_mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(badge_mask)
    draw.rounded_rectangle([147, 417, 364, 477], radius=15, fill=255)

    # Artwork mask
    mask = Image.new('L', (w, h), 0)
    for y in range(h):
        for x in range(w):
            if badge_mask.getpixel((x, y)) > 0:
                mask.putpixel((x, y), 255)
                continue
            r, g, b, _ = src.getpixel((x, y))
            # Background is dark navy: r < 30, g < 60, b > g
            if r < 30 and g < 60 and b > g:
                mask.putpixel((x, y), 0)
            else:
                mask.putpixel((x, y), 255)

    mask_smooth = mask.filter(ImageFilter.GaussianBlur(radius=0.7))

    fg = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for y in range(h):
        for x in range(w):
            r, g, b, _ = src.getpixel((x, y))
            a = mask_smooth.getpixel((x, y))
            if a > 0:
                fg.putpixel((x, y), (r, g, b, a))
    return fg

def main():
    print('[Icons] Generating native app icons and splash assets...')
    fg = extract_transparent_foreground(SRC_ICON)
    alpha = fg.split()[-1]
    tight_art = fg.crop(alpha.getbbox())

    # 1. iOS AppIcon (1024x1024 opaque)
    ios_icon_path = os.path.join(ROOT_DIR, 'ios', 'App', 'App', 'Assets.xcassets', 'AppIcon.appiconset', 'AppIcon-512@2x.png')
    if os.path.exists(os.path.dirname(ios_icon_path)):
        ios_im = Image.open(SRC_ICON).convert('RGB').resize((1024, 1024), Image.Resampling.LANCZOS)
        ios_im.save(ios_icon_path, 'PNG')
        print(' ✔ Generated iOS 1024x1024 AppIcon')

    # 2. iOS Splash Screen (2732x2732 dark #111416 ballroom background with centered mirrorball)
    # Visible width on a 9:19.5 iPhone screen with scaleAspectFill from 2732h is ~1260px.
    # Sizing mirrorball artwork width to 380px (~30.1% screen width) perfectly matches Android's 29.4% ratio.
    ios_splash_dir = os.path.join(ROOT_DIR, 'ios', 'App', 'App', 'Assets.xcassets', 'Splash.imageset')
    if os.path.exists(ios_splash_dir):
        splash_art_w = 380
        aspect = tight_art.height / tight_art.width
        splash_art_h = int(splash_art_w * aspect)
        ios_art_scaled = tight_art.resize((splash_art_w, splash_art_h), Image.Resampling.LANCZOS)

        ios_splash = Image.new('RGB', (2732, 2732), DARK_BG)
        paste_x = (2732 - splash_art_w) // 2
        paste_y = (2732 - splash_art_h) // 2
        ios_splash.paste(ios_art_scaled, (paste_x, paste_y), ios_art_scaled)

        for splash_fname in ['splash-2732x2732.png', 'splash-2732x2732-1.png', 'splash-2732x2732-2.png']:
            ios_splash.save(os.path.join(ios_splash_dir, splash_fname), 'PNG')
        print(' ✔ Generated iOS dark mirrorball splash images (2732x2732 @1x, @2x, @3x)')

    # 3. Android Mipmaps
    android_res = os.path.join(ROOT_DIR, 'android', 'app', 'src', 'main', 'res')
    densities = [
        ('mipmap-mdpi', 48, 108),
        ('mipmap-hdpi', 72, 162),
        ('mipmap-xhdpi', 96, 216),
        ('mipmap-xxhdpi', 144, 324),
        ('mipmap-xxxhdpi', 192, 432),
    ]

    for folder, size, fg_size in densities:
        dir_path = os.path.join(android_res, folder)
        if not os.path.exists(dir_path):
            continue

        # A) Adaptive Foreground (108dp canvas, safe area ~66dp)
        # Sizing artwork to ~52% of fg_size guarantees 100% visibility inside circular masks
        art_size = int(fg_size * 0.52)
        fg_scaled = fg.resize((art_size, art_size), Image.Resampling.LANCZOS)
        fg_canvas = Image.new('RGBA', (fg_size, fg_size), (0, 0, 0, 0))
        paste_xy = ((fg_size - art_size) // 2, (fg_size - art_size) // 2)
        fg_canvas.paste(fg_scaled, paste_xy, fg_scaled)
        fg_canvas.save(os.path.join(dir_path, 'ic_launcher_foreground.png'), 'PNG')

        # B) Legacy Square Launcher (100% opaque RGB to prevent launcher badge platters)
        leg_square = Image.new('RGB', (size, size), NAVY_BG)
        leg_art_size = int(size * 0.72)
        leg_fg = fg.resize((leg_art_size, leg_art_size), Image.Resampling.LANCZOS)
        leg_square.paste(leg_fg, ((size - leg_art_size) // 2, (size - leg_art_size) // 2), leg_fg)
        leg_square.save(os.path.join(dir_path, 'ic_launcher.png'), 'PNG')

        # C) Legacy Round Launcher (100% opaque RGB with NAVY_BG, not transparent corners)
        leg_round = Image.new('RGB', (size, size), NAVY_BG)
        leg_round.paste(leg_fg, ((size - leg_art_size) // 2, (size - leg_art_size) // 2), leg_fg)
        leg_round.save(os.path.join(dir_path, 'ic_launcher_round.png'), 'PNG')

        print(f' ✔ Generated Android {folder} (legacy: {size}x{size}, adaptive fg: {fg_size}x{fg_size})')

    # 4. Android 12+ Splash Screen Icon
    # Sized to 260x260 inside 432x432 canvas so the entire mirrorball, all 5 stars,
    # stand, and DWTS 35 badge fit 100% inside Android 12's 160dp splash circle without any clipping
    drawable_dir = os.path.join(android_res, 'drawable')
    splash_icon_path = os.path.join(drawable_dir, 'splash_icon.png')
    splash_art_size = 260
    splash_icon = fg.resize((splash_art_size, splash_art_size), Image.Resampling.LANCZOS)
    splash_canvas = Image.new('RGBA', (432, 432), (0, 0, 0, 0))
    splash_canvas.paste(splash_icon, ((432 - splash_art_size) // 2, (432 - splash_art_size) // 2), splash_icon)
    splash_canvas.save(splash_icon_path, 'PNG')
    print(' ✔ Generated Android 12+ Splash Icon (@drawable/splash_icon.png)')

    # 5. Android Legacy Splash Screens (Portrait & Landscape on #111416)
    aspect = tight_art.height / tight_art.width
    android_splashes = [
        ('drawable-port-mdpi', 320, 480, 93),
        ('drawable-port-hdpi', 480, 800, 139),
        ('drawable-port-xhdpi', 720, 1280, 211),
        ('drawable-port-xxhdpi', 960, 1600, 281),
        ('drawable-port-xxxhdpi', 1280, 1920, 376),
        ('drawable-land-mdpi', 480, 320, 93),
        ('drawable-land-hdpi', 800, 480, 139),
        ('drawable-land-xhdpi', 1280, 720, 211),
        ('drawable-land-xxhdpi', 1600, 960, 281),
        ('drawable-land-xxxhdpi', 1920, 1280, 376),
        ('drawable', 480, 320, 93),
    ]
    for folder, cw, ch, aw in android_splashes:
        target_dir = os.path.join(android_res, folder)
        if not os.path.exists(target_dir):
            continue
        ah = int(aw * aspect)
        art_res = tight_art.resize((aw, ah), Image.Resampling.LANCZOS)
        sp = Image.new('RGB', (cw, ch), DARK_BG)
        sp.paste(art_res, ((cw - aw) // 2, (ch - ah) // 2), art_res)
        sp.save(os.path.join(target_dir, 'splash.png'), 'PNG')
    print(' ✔ Generated Android legacy portrait & landscape splash screens')

    # 6. PWA Maskable Icons (for web manifest)
    for pwa_size, pwa_file in [(512, 'icon-maskable-512-ballroom.png'), (192, 'icon-maskable-192-ballroom.png')]:
        pwa_path = os.path.join(ROOT_DIR, 'assets', pwa_file)
        pwa_canvas = Image.new('RGB', (pwa_size, pwa_size), NAVY_BG)
        pwa_art_size = int(pwa_size * 0.60)
        pwa_fg = fg.resize((pwa_art_size, pwa_art_size), Image.Resampling.LANCZOS)
        pwa_canvas.paste(pwa_fg, ((pwa_size - pwa_art_size) // 2, (pwa_size - pwa_art_size) // 2), pwa_fg)
        pwa_canvas.save(pwa_path, 'PNG')
        print(f' ✔ Updated PWA maskable icon: {pwa_file}')

    print('[Icons] Generation complete!')

if __name__ == '__main__':
    main()
