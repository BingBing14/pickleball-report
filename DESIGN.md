# DESIGN.md: Group 1 Pickleball Tournament Report

Direction: **clean white court, scoreboard numbers.** The team color is White, so the
base is white paper with near-black ink. One court-green accent marks links, the
current page and winners. Results use dark scoreboard panels with large condensed
numerals. No gradients, no blobs, no stock imagery: real photos and real numbers only.

This direction was not based on reference sites (the UXKIN library was not
connected). It follows the brief's constraints and the rules below.

## Color (light only)

| Token | Value | Role |
| --- | --- | --- |
| `--paper` | `#FFFFFF` | Page background |
| `--surface` | `#F3F4F1` | Section bands, table stripes, cards |
| `--line` | `#DCDFD8` | Borders, dividers, table rules |
| `--ink` | `#14171A` | Body text, headings, scoreboard panel background |
| `--ink-2` | `#4A5058` | Secondary text, captions (7.9:1 on white) |
| `--accent` | `#0B6B4B` | Links, current page, winner marks, focus ring (6.6:1 on white) |
| `--accent-soft` | `#E3F1EA` | Background behind accent text (chips, current nav item) |
| `--on-ink` | `#FFFFFF` | Text on scoreboard panels |
| `--on-ink-2` | `#B9C0C7` | Secondary text on panels (9.4:1 on ink) |
| `--gold` / `--silver` / `--bronze` | `#B8860B` / `#7D858C` / `#9A5B2E` | Medal markers on the placings only (always paired with text) |

## Typography

- Display and numbers: **Barlow Condensed** 600/700, the scoreboard face. Scores use `font-variant-numeric: tabular-nums`.
- Body and UI: **Barlow** 400/500/600.
- Scale (px / line height): 14/1.4 (labels, uppercase, +0.06em) · 16/1.6 (body, minimum) · 18/1.6 (lead) · 22/1.3 (h3) · 28/1.2 (h2) · 40/1.05 (h1 mobile) · 56/1.0 (h1 desktop) · 64/1.0 (big score).
- Line length: max 68ch for prose.

## Spacing and layout

- 4-based scale: 4, 8, 12, 16, 24, 32, 48, 64, 96 (`--s1` to `--s9`).
- Content width 1120px, prose 68ch. Side gutter 16px on phones, 24px from 768px.
- Section spacing: 48px on phones, 64px from 768px.

## Shape and depth

- Radius: 4px (chips, inputs), 8px (cards, photos, panels). No pill shapes except chips.
- One shadow, for the sticky header and the open menu only: `0 1px 0 var(--line), 0 6px 16px rgba(20,23,26,.06)`.

## Components

- **Header**: sticky, white, site mark on the left, "Sections" menu button (44px tall) on the right. From 1024px a second row lists all 12 sections, numbered; the current one has the accent underline and `aria-current="page"`.
- **Page head**: section number label ("Section 08 of 12"), the exact section name as h1, one lead sentence.
- **Scoreboard card**: ink panel, match label + court + slot in small caps, two team rows with large numerals; the winner row in white with a green marker, the loser in `--on-ink-2`. A "time cap" chip when a match ended at 6 minutes.
- **Tables**: full-width, striped with `--surface`, numbers right-aligned and tabular, scroll horizontally inside their own wrapper on phones.
- **Fact list**: label/value pairs in a 2-column grid (1 column under 480px).
- **Buttons/links**: links are accent and underlined. Primary button: ink background, white text; secondary: white with ink border. Hover darkens; visible 3px accent focus ring on everything focusable.
- **Prev/Next**: two large cards at the page foot, at least 64px tall.
- **Back to top**: text link in the footer and a small fixed button after scrolling.
- **Footer**: course, section, group, instructor, date.

## Imagery and icons

- Photos are large, 8px radius, 3:2 crop in grids, always captioned, `alt` on every image, lazy-loaded.
- Logo: a tilted pickleball paddle (ink face, green edge guard, wrapped green grip) with an upright white "1", hitting a perforated ball. Source `src/logos/logo.svg`; it is also the browser-tab icon. Use it on light backgrounds only.
- No icon font. A few inline SVGs (menu, arrows, close) drawn at 2px stroke.
- Motion: only short fades on the menu and lightbox, turned off under `prefers-reduced-motion`.
