---
name: BIG Lab
description: A research observatory that makes invisible social influence legible.
colors:
  midnight-field: "#0d1934"
  ink: "#12192c"
  paper: "#f7f5ef"
  signal-yellow: "#f6dc74"
  pale-lilac: "#e8e5f3"
  data-coral: "#b63d34"
  network-mint: "#c7e8d0"
  white: "#ffffff"
  deep-blue-glow: "#213660"
  muted-text: "#5a6375"
  pale-blue-text: "#d9def0"
  footer-muted: "#b9c1d2"
  midnight-line: "rgba(13,25,52,.2)"
  light-line: "rgba(255,255,255,.2)"
typography:
  display:
    fontFamily: "Anybody, Arial, sans-serif"
    fontSize: "clamp(3.3rem, 8vw, 8rem)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-.065em"
    fontVariation: "\"wdth\" 108"
  section-heading:
    fontFamily: "Anybody, Arial, sans-serif"
    fontSize: "clamp(2.3rem, 4.4vw, 4.7rem)"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-.045em"
    fontVariation: "\"wdth\" 108"
  body:
    fontFamily: "Atkinson Hyperlegible Next, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.55
  intro:
    fontFamily: "Atkinson Hyperlegible Next, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "Atkinson Hyperlegible Next, Arial, sans-serif"
    fontSize: ".8rem"
    fontWeight: 700
    lineHeight: 1.55
    letterSpacing: ".13em"
rounded:
  square: "0px"
  circle: "50%"
spacing:
  compact: ".7rem"
  control-x: "1.15rem"
  section-gap: "2rem"
  module: "4rem"
  section: "8rem"
  shell-gutter-desktop: "32px"
  shell-gutter-tablet: "20px"
  shell-gutter-mobile: "16px"
components:
  button-primary:
    backgroundColor: "{colors.signal-yellow}"
    textColor: "{colors.midnight-field}"
    rounded: "{rounded.square}"
    padding: ".72rem 1.15rem"
    height: "50px"
  button-light:
    backgroundColor: "{colors.white}"
    textColor: "{colors.midnight-field}"
    rounded: "{rounded.square}"
    padding: ".72rem 1.15rem"
    height: "50px"
  page-surface:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
  dark-surface:
    backgroundColor: "{colors.midnight-field}"
    textColor: "{colors.white}"
    rounded: "{rounded.square}"
---

# Design System: BIG Lab

## Overview

**Creative North Star: “The Social-Network Atlas”**

BIG Lab’s visual system makes hidden interdependence visible. It behaves like a research observatory rather than a generic university site: large editorial statements establish the question, numbered rows catalogue the evidence, and connected nodes reveal the people, themes, and projects that form the lab’s work.

The interface combines scientific precision with human warmth. Midnight blue creates depth; pale paper and lilac keep long-form reading calm; butter yellow, coral, mint, and white act as scarce data signals. Hairline rules, square corners, terse labels, and oversized variable type give the system its exacting editorial character.

**Key characteristics:**

- A live sociogram—not a stock photograph—is the homepage’s primary artifact.
- Evidence, people, and research outputs outrank promotional language.
- Oversized type and asymmetrical grids create hierarchy; rules and numbering create order.
- Most surfaces are flat and square. Circles belong to network nodes and the provisional constellation mark.
- English and Czech content share the same layouts, with room for text expansion.

## Colors

The palette is a midnight observatory punctuated by warm research signals and quiet paper-like reading surfaces.

### Primary

- **Midnight Field** (`#0d1934`): hero, footer, brand linework, and the main dark ground. It is also the browser theme color.
- **Signal Yellow** (`#f6dc74`): primary actions, the brand-mark node fill, and the lead sociogram node.

### Secondary

- **Data Coral** (`#b63d34`): the shipped coral token. Use for section indices, active language state, metadata, link underlines, and the featured-project band.
- **Pale Lilac** (`#e8e5f3`): the people-section surface and one sociogram node; it softens the system without weakening contrast.
- **Network Mint** (`#c7e8d0`): a supporting node color reserved for diagrams and related data accents.

### Neutral

- **Paper** (`#f7f5ef`): default page and tile background.
- **Ink** (`#12192c`): default body and heading color on light surfaces.
- **White** (`#ffffff`): text on dark fields, light button surface, and one network node.
- **Muted Text** (`#5a6375`): dates, roles, publishers, and supporting metadata. Nearby legacy values `#566079` and `#5d6678` serve the same contextual role; prefer the canonical token in new work.
- **Pale Blue Text** (`#d9def0`) and **Footer Muted** (`#b9c1d2`): secondary copy on midnight surfaces.
- **Midnight Line** (`rgba(13,25,52,.2)`): dividers and grid seams on light surfaces. Use `rgba(255,255,255,.2)` or the subtler `.12` variant on dark surfaces.
- **Deep Blue Glow** (`#213660`): the center of the network’s radial field; it is atmospheric, not a general-purpose surface.

**The Signal Scarcity Rule.** Yellow, coral, lilac, and mint identify action, state, or a meaningful data category. Do not scatter them as decoration.

**The Effective Coral Rule.** New components use `#b63d34`; do not introduce a brighter coral unless the palette and contrast checks are deliberately revised everywhere.

## Typography

**Display Font:** Anybody, with Arial and sans-serif fallbacks
**Body Font:** Atkinson Hyperlegible Next, with Arial and sans-serif fallbacks

**Character:** Anybody supplies wide, compact, poster-like authority for the lab’s ideas. Atkinson Hyperlegible Next keeps dense scientific copy, metadata, navigation, and bilingual content highly readable. Both are loaded from Google Fonts in `config.css`; if external font loading fails, Arial preserves the sans-serif structure but not the brand character.

### Hierarchy

- **Display** (700 by inherited heading default, `clamp(3.3rem, 8vw, 8rem)`, `0.98`, `-.065em`): page titles. Homepage and profile variants use their own bounded clamps, but retain the same tight rhythm.
- **Section Heading** (700 by inherited heading default, `clamp(2.3rem, 4.4vw, 4.7rem)`, `0.98`, `-.045em`): numbered section titles and major editorial transitions.
- **Row Title** (600, usually `clamp(1.5rem, 3vw, 3.2rem)`, about `1`): research, project, publication, and card titles.
- **Intro** (400, `1.25rem`–`1.35rem`, `1.55`): summaries and opening paragraphs, generally constrained to 670–750px.
- **Body** (400, `17px` desktop / `16px` mobile, `1.55`): reading copy. Long-form article text is `1.15rem` and capped at 760px.
- **Label** (600–700, `.8rem`–`.88rem`, up to `.13em`): kickers, navigation, dates, metadata, and indexes. Kicker and metadata labels are uppercase.

Set Anybody headings with `font-variation-settings: "wdth" 108`. Keep display tracking tight; do not apply the display face to paragraphs or long metadata. Use semantic heading levels independently of visual scale.

## Layout

The global shell is `min(1440px, calc(100vw - 64px))`, centered. At 980px it becomes `calc(100vw - 40px)`; at 680px it becomes `calc(100vw - 32px)`. Full-bleed midnight, lilac, and coral bands may extend beyond the shell, but their content realigns to the same gutters.

Desktop layouts are deliberately asymmetric. The homepage hero uses roughly a 38/62 split between statement and sociogram. Editorial page heroes place a narrow index or kicker in the first column and content in the remaining three quarters. Profile and project detail pages pair a stable media/metadata rail with a flexible reading column. List views use rules, indices, and image columns instead of floating rounded cards.

Vertical rhythm is generous: major sections typically use 5–10rem of block space, with 8–9rem common on desktop. Internal modules commonly use 1–4rem. Maintain the contrast between spacious page-level intervals and compact information rows.

### Responsive behavior

- **Above 980px:** preserve the asymmetric hero, six-person portrait run, three-column updates and people grids, and visible image columns in research/project rows.
- **At 980px and below:** stack the hero, expose the 48px menu control and dark dropdown navigation, reduce portraits to three columns, updates and people to two columns, and simplify project rows.
- **At 680px and below:** use 16px shell gutters and base type; reduce the header to 76px; stack content rails and all major grids; hide decorative list thumbnails; reduce portraits to two columns; convert row text such as “Explore” to the compact `↗`; and make the footer single-column.
- **Short desktop viewports (981px+ and 800px high or less):** compress hero padding and display type so the question and actions remain visible while the network still fills the viewport below the 92px header.

Do not force desktop column structures onto narrow screens. Reordering may simplify presentation, but document order and semantic relationships must remain intact.

## Elevation & Depth

The system is flat by default. Depth comes from tonal fields, borders, image crops, overlapping responsive movement, and the sociogram’s radial gradient—not from persistent card shadows. The one intentional shadow is the button hover response: `3px 3px 0 #b63d34`, paired with a `translate(-3px, -3px)` offset so the control feels like a lifted print block.

**The Flat-by-Default Rule.** Resting surfaces use color and `1px` rules. Do not add soft drop shadows, glass effects, or floating cards.

## Shapes

Square corners are the dominant form language. Buttons, bands, cards, image frames, list rows, and reading surfaces have no radius. Structure comes from straight rules and rectangular crops: `3/4` or `4/5` for portraits, `16/9` for news, and shallow landscape crops for research.

Circles are semantic exceptions. They represent people or topics in the sociogram and form the endpoints of the provisional constellation brand mark. The large circular outline around the network is orbital context, not a reusable card shape.

Use 1px borders for section boundaries, table-like grids, project navigation, and embeds. Avoid pill shapes and gratuitous rounding; they conflict with the research-atlas vocabulary.

## Components

### Header and navigation

The desktop header is a 92px-high shell with a bottom hairline. The provisional brand mark connects four yellow-filled nodes with crossed navy lines; pair it with the bold Anybody wordmark. Navigation is compact and text-led. Desktop hover/focus grows a 2px coral underline from left to right over 200ms.

At 980px and below, replace the link row with the three-line 48px menu control. The menu opens as a full-width midnight panel below the header, uses a vertical link stack, reports state through `aria-expanded`, and closes on Escape while returning focus to the trigger. Keep language switching available beside the menu control.

Wagtail's `Show in menus` flag is the navigation source of truth at every supported tree level. Marked child pages appear in a square midnight submenu beneath their marked parent. Submenus have independent disclosure buttons, preserve parent-page links, expose the current page with `aria-current`, close on Escape, and become indented disclosure lists inside the mobile panel.

### Buttons and text links

- **Primary:** square, signal-yellow surface, midnight text, 1px yellow border, 50px minimum height, `.72rem 1.15rem` padding, and weight 700.
- **Light:** the same geometry with a white surface and border; used against coral or other saturated fields.
- **Hover:** shift 3px up and left and expose the hard coral shadow below and right.
- **Text link:** underlined on dark surfaces with a 5px underline offset. Rich-text links use a 2px coral decoration and 4px offset.

Buttons communicate a bounded action; arrows (`→` or `↗`) communicate navigation or an external destination. Preserve minimum 44px interactive height in header links and 50–52px in primary/project controls.

### Sociogram

The homepage network is the signature component. It occupies the hero’s visual majority, uses real research-area labels, and links its topic nodes to real pages. Dashed lilac lines describe relationships; differently colored circles distinguish nodes without implying a quantitative legend. Pointer movement shifts the SVG by at most 13px in either axis, and node hover/focus scales circles to `1.12` while turning them white. All motion is disabled when reduced motion is requested.

Keep the SVG’s accessible group labels and each linked node’s explicit accessible name. Never replace the network with a generic stock hero or animate it continuously.

### Numbered editorial rows

Research, project, publication, and section-navigation rows share a catalogue logic: small coral or numeric index, large Anybody title, supporting image or text, directional arrow, and a 1px rule. Hover may reveal color or slightly expand the image; it should not turn the row into a raised card. On mobile, remove optional imagery before compressing the title or tap target.

### People and image tiles

Portraits begin in grayscale and reveal color on hover; desktop preview portraits may alternate vertically to establish rhythm. Index tiles meet edge to edge with line-colored seams and a paper background. Names use Anybody, roles use muted body type, and portraits retain consistent crops within each context.

### Reading pages and metadata

Long-form bodies are centered or aligned to the main content rail, capped near 760px, and use `1.15rem` body text. Intro text is wider and larger but remains below display hierarchy. Project metadata uses uppercase small labels and plain definition lists. Project-section links form a square, bordered three-column index on desktop and a single column on mobile.

### Featured and update modules

The featured Parta band is a full-width coral interruption with white text and a light button. Treat it as a singular emphasis, not a reusable default card. Update columns separate latest news, active projects, and publications with small uppercase headings and ruled links; they collapse from three columns to two and then one.

### Homepage section builder

The branded hero and sociogram stay structurally fixed. Everything below them is assembled in Wagtail from reorderable, duplicable, removable, and individually hideable sections. Editors may use editorial text, text with image, research, people, featured project, updates, selected-page links, gallery, callout, video, or trusted simulation blocks. Every section follows the same shell, theme tokens, square geometry, and responsive rules described above; arbitrary HTML and pasted JavaScript are intentionally excluded.

Advanced media remains controlled: galleries may enable a full-screen lightbox, comparisons use a single horizontal reveal control, and sliders provide manual keyboard controls with optional motion-aware autoplay. Section backgrounds always use the image library, a fixed position choice, and a contrast overlay. Person portraits use named size, ratio, and fit options rather than arbitrary dimensions, so editorial flexibility cannot break the grid.

Dynamic sections use the same curation rule: an explicit ordered selection overrides the automatic source, while an empty selection follows the current published content. People become a keyboard-operable, scroll-snap carousel only after the editor's threshold is exceeded; desktop shows the configured number of portraits and mobile shows two. Research retains its catalogue rows, and Updates lets news, projects, and publication snippets be curated independently without turning the section into a generic card carousel.

## Do's and Don'ts

### Motion and accessibility

- **Do** preserve the skip link, semantic landmarks and heading hierarchy, descriptive navigation labels, `aria-current`, and accessible names on diagram links.
- **Do** retain visible keyboard focus. The shipped treatment is a 3px white outline with 3px offset and a contrasting midnight outer ring; verify it against both light and dark surfaces whenever colors change.
- **Do** keep interaction motion brief (150–250ms), spatially small, and directly tied to hover, focus, or pointer movement.
- **Do** honor `prefers-reduced-motion: reduce` by disabling smooth scrolling, transitions, animations, and sociogram parallax.
- **Do** keep touch targets at least 44px high and test both English and Czech at every breakpoint.
- **Don't** use color, hover, or motion as the only way to reveal meaning or access content.
- **Don't** introduce autoplay, looping ambient motion, or dense animation into reading surfaces.

### Imagery and provenance

- **Do** use real BIG Lab people, meetings, and research imagery before decorative stock. Portraits and research images are editorial evidence.
- **Do** preserve Wagtail’s responsive renditions and `loading="lazy"` on below-the-fold imagery. Maintain consistent `object-fit: cover` crops per component.
- **Do** record every shipping raster’s source, license or permission basis, retrieval date, and intended use. Current seed-image provenance lives in `home/seed_assets/SOURCES.md`; all listed files came from the public BIG Lab/Masaryk University page supplied for the project on 2026-09-21.
- **Don't** mistake Wagtail files in `media/images` and `media/original_images` for independent sources; they are derivatives and copies of the documented seed assets.
- **Don't** add uncredited imagery, AI-generated scientific evidence, decorative portraits, or generic “research” stock to fill space.

### Maintenance guidance

- **Do** treat `config/static/css/config.css` as the implementation source of truth and this file as its design contract. When tokens or breakpoints change, update both in the same change.
- **Do** reuse the existing CSS custom properties (`--navy`, `--ink`, `--paper`, `--yellow`, `--lilac`, `--coral`, `--mint`, `--line`, `--shell`) before adding one-off values. Consolidate legacy muted-text literals when touching those components.
- **Do** preserve Wagtail template semantics and editor-managed content. New components must handle missing optional images, links, translations, dates, and summaries without leaving visual holes.
- **Do** validate new work at desktop, 980px, and 680px boundaries, plus a short desktop viewport. Check keyboard operation, focus visibility, reduced motion, long Czech strings, and image-less content.
- **Don't** turn the design into a conventional university hero plus rounded card grid. The sociogram, numbered evidence rows, asymmetric editorial layouts, and square modules are the identity.
- **Don't** invent a final logo or imply that the Parta description is approved; both remain unresolved product inputs.
- **Don't** duplicate overrides at the end of the stylesheet. If a token changes, edit its canonical `:root` value so computed behavior and documentation stay aligned.
