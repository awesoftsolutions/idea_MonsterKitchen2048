# Monster Kitchen Asset Manifest
**Version**: 1.0
**Date**: 2026-07-31
**Status**: Active

## Overview

All 24 Monster Kitchen visual assets for the2048 game. Generated via `image_generation` tool following the Kawaii/Cooking Mama style guide. All assets are PNG format at 1024×1024 resolution.

## Style Guide

- **Art style**: Cute, rounded, cartoon/chibi with thick outlines (Kawaii meets Cooking Mama)
- **Color palette**: Soft pinks (#FFB5C5), warm yellows (#FFE4A0), sky blues (#A0D8EF), mint greens (#B5EAD7), lavender purples (#C5B3E6)
- **Lighting direction**: Top-left
- **Line weight**: Thick, bold outlines (2-3px at 1024×1024)
- **Proportions**: Chibi/cute — oversized heads, small bodies
- **Resolution**: 1024×1024 pixels, 1:1 aspect ratio, PNG format
- **Text constraint**: No baked-in text or numbers (exception: tile_17 title logo)

---

## Tile Sprites — Merge Chain (assets/tiles/)

| # | Filename | Tile Value | Description |
|---|----------|-----------|-------------|
| 01 | tile_01_blueberry.png | 2 | Single cute blueberry with happy face |
| 02 | tile_02_cupcake.png | 4 | Small cupcake with sprinkles and happy face |
| 03 | tile_03_pie.png | 8 | Slice of pie with a smile |
| 04 | tile_04_cake.png | 16 | Whole cake with candles, happy face |
| 05 | tile_05_birthday_cake.png | 32 | Tiered birthday cake, excited face |
| 06 | tile_06_wedding_cake.png | 64 | Giant wedding cake with sparkles, starry-eyed face |
| 07 | tile_07_rainbow_cake.png | 128 | Magical rainbow cake with glowing aura, amazed face |
| 08 | tile_08_trophy_cake.png | 256 | Golden trophy cake with crown, proud face |
| 09 | tile_09_galaxy_cake.png | 512 | Cosmic galaxy cake with swirling stars, awestruck face |
| 10 | tile_10_phoenix_cake.png | 1024 | Legendary phoenix cake with flame wings, triumphant face |
| 11 | tile_11_mega_cake.png | 2048 | ULTIMATE chef's masterpiece — dazzling mega-cake, ecstatic face, golden glow |

## Special Tiles (assets/tiles/)

| # | Filename | AssetLoader Key | Description |
|---|----------|----------------|-------------|
| 12 | tile_12_rotten.png | rotten_normal | Green/brown slimy food blob with X eyes and stink lines — yucky-funny, NOT scary |
| 13 | tile_13_rotten_warning.png | rotten_warning | Same rotten blob with yellow warning aura — contamination imminent |

## UI Elements (assets/ui/)

| # | Filename | AssetLoader Key | Component | Description |
|---|----------|----------------|-----------|-------------|
| 14 | tile_14_board_background.png | board_background | BoardRenderer | Kitchen countertop / cutting board with warm wood tones and subtle food decorations |
| 15 | tile_15_cell_empty.png | cell_empty | BoardRenderer | Subtle rounded-rectangle indent on board surface — shows where tiles sit |
| 16 | tile_16_score_card.png | score_card | HUD | Cute recipe card or chalkboard frame for displaying the score |
| 17 | tile_17_title_logo.png | title_logo | HUD | "Monster Kitchen 2048" in playful bubbly cartoon lettering (ONLY text-bearing asset) |
| 18 | tile_18_new_game_button.png | new_game_button | HUD | Cute rounded button styled like a kitchen timer or oven mitt |
| 19 | tile_19_game_over_overlay.png | game_over_overlay | BoardRenderer | Friendly game-over screen with sad monster chef — disappointed/cute, NOT scary |
| 20 | tile_20_win_overlay.png | win_overlay | BoardRenderer | Celebration screen with confetti and happy monster chef holding 2048 cake |
| 21 | tile_21_background_wallpaper.png | background_wallpaper | BoardRenderer | Subtle repeating pattern of tiny food items and kitchen utensils on warm pastel background |

## Mascot Sprites (assets/mascot/)

| # | Filename | AssetLoader Key | Description |
|---|----------|----------------|-------------|
| 22 | tile_22_mascot_idle.png | idle | Small round cute monster wearing chef hat and apron — friendly, colorful, 2-3 colors max |
| 23 | tile_23_mascot_happy.png | happy | Same mascot celebrating / clapping — joyful expression |
| 24 | tile_24_mascot_worried.png | worried | Same mascot looking concerned — for rotten tile appearances |

---

## AssetLoader Interface Mapping

### Tile Value → Sprite Mapping
| Tile Value | Filename |
|-----------|----------|
| 2 | tile_01_blueberry.png |
| 4 | tile_02_cupcake.png |
| 8 | tile_03_pie.png |
| 16 | tile_04_cake.png |
| 32 | tile_05_birthday_cake.png |
| 64 | tile_06_wedding_cake.png |
| 128 | tile_07_rainbow_cake.png |
| 256 | tile_08_trophy_cake.png |
| 512 | tile_09_galaxy_cake.png |
| 1024 | tile_10_phoenix_cake.png |
| 2048 | tile_11_mega_cake.png |
| >2048 | tile_11_mega_cake.png (fallback) |

### UI Sprite Keys
| Key | Filename |
|-----|----------|
| board_background | tile_14_board_background.png |
| cell_empty | tile_15_cell_empty.png |
| score_card | tile_16_score_card.png |
| title_logo | tile_17_title_logo.png |
| new_game_button | tile_18_new_game_button.png |
| game_over_overlay | tile_19_game_over_overlay.png |
| win_overlay | tile_20_win_overlay.png |
| background_wallpaper | tile_21_background_wallpaper.png |

### Mascot Sprite Keys
| Key | Filename |
|-----|----------|
| idle | tile_22_mascot_idle.png |
| happy | tile_23_mascot_happy.png |
| worried | tile_24_mascot_worried.png |

### Special Tile Keys
| Key | Filename |
|-----|----------|
| rotten_normal | tile_12_rotten.png |
| rotten_warning | tile_13_rotten_warning.png |

---

## Rendering Notes for Code Agent

- **Tile sprites** are rendered at cell_size × cell_size within the 4×4 grid. Cell size is computed from (700 - 2×margin) / 4.
- **Rotten overlays** are drawn as semi-transparent sprites on top of tile sprites at the same grid position.
- **Background wallpaper** fills the entire 700×800 window behind the board.
- **Board background** sits on top of the wallpaper, sized to the board area.
- **Empty cell slots** are drawn at each grid position where no tile is present.
- **Score card** is positioned in the HUD area above or beside the board.
- **Title logo** appears at the top of the window.
- **New game button** is positioned in the HUD area with a clickable Rect.
- **Game over / win overlays** are centered on the full 700×800 window.
- **Mascot sprites** are positioned beside the title in the HUD area.

## Visual Consistency Checklist

- [ ] All tile sprites share same line weight (thick, bold outlines)
- [ ] All tile sprites share same lighting direction (top-left)
- [ ] All tile sprites share same proportional scale (chibi/cute)
- [ ] Color palette is bright pastels only — no dark or muted tones
- [ ] No baked-in text or numbers (except tile_17 title logo)
- [ ] Rotten tiles (12, 13) are yucky-funny, not scary — suitable for 8-year-olds
- [ ] Warning state (13) is visually distinct from normal rotten (12) via yellow aura
- [ ] Mascot character is consistent across all 3 poses (same body, hat, apron, colors)
- [ ] UI elements match the same cartoon aesthetic as tile sprites
