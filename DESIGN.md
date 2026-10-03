---
name: BIG Lab
description: A navy and butter constellation identity with cream reading surfaces and brick accents.
colors:
  navy: "#101e32"
  navy-light: "#1c3048"
  ink: "#182b3e"
  paper: "#f6f3e9"
  paper-deep: "#ebe6d9"
  yellow: "#f3dfa1"
  coral: "#a94737"
  muted: "#53616b"
  line: "#d6d5cb"
  dark-line: "#465467"
typography:
  display:
    fontFamily: "Alegreya, Georgia, serif"
    fontSize: "clamp(2.5rem, 4vw, 3.6rem)"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-.02em"
  headline:
    fontFamily: "Alegreya, Georgia, serif"
    fontSize: "clamp(1.8rem, 2.8vw, 2.4rem)"
    fontWeight: 500
    lineHeight: 1.12
    letterSpacing: "-.02em"
  title:
    fontFamily: "Alegreya, Georgia, serif"
    fontSize: "clamp(1.25rem, 1.8vw, 1.6rem)"
    fontWeight: 500
    lineHeight: 1.12
    letterSpacing: "-.02em"
  body:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.65
  hero-summary:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "1.06rem"
    lineHeight: 1.65
  navigation:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: ".88rem"
    fontWeight: 500
rounded:
  surface: "12px"
  thumbnail: "8px"
  control: "8px"
  circle: "50%"
spacing:
  section-gap: "2rem"
  module-gap: "4rem"
  section-block: "clamp(2.75rem, 4.5vw, 4.25rem)"
  section-block-mobile: "2.5rem"
  shell-gutter-desktop: "48px"
  shell-gutter-tablet: "32px"
  shell-gutter-mobile: "20px"
  shell-gutter-narrow: "16px"
components:
  button-primary:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.navy}"
    rounded: "{rounded.control}"
    padding: ".6rem 1.15rem"
  button-primary-hover:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.yellow}"
  button-primary-hover-dark-context:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.navy}"
  button-secondary-hero:
    backgroundColor: "transparent"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: ".6rem 1.15rem"
  button-secondary-hero-hover:
    backgroundColor: "{colors.navy-light}"
  button-dark:
    backgroundColor: "{colors.navy}"
    textColor: "{colors.yellow}"
    rounded: "{rounded.control}"
    padding: ".6rem 1.15rem"
  button-dark-hover:
    backgroundColor: "{colors.navy-light}"
---

# Design System: BIG Lab

## Overview

BIG Lab's shipped identity uses a constellation to express relationships among research topics. The navy header and homepage hero form one continuous opening, with butter-yellow headings, stars, and actions. Cream reading surfaces and occasional brick-colored sections carry the content below.

Alegreya's serif headings pair with Source Sans 3 for prose and interface text. Compact typography and bounded photos accompany open editorial sections, thin dividers, rounded imagery, and softly rectangular controls. A finite entrance introduces the research constellation, whose moving connections continue while visible.

This document records the current implementation, not a new design proposal. The source of truth is `config/static/css/config.css` and `config/static/js/config.js`, together with `config/templates/base.html`, the templates under `home/templates/home/`, and `config/static/fonts/fonts.css`. Frontmatter records the reused palette and representative desktop type roles; responsive and component-specific overrides are described below.

## Colors

### Primary

- **Navy** (`navy`): header, hero, footer, constellation labels, dark buttons, and midnight section backgrounds. The base template also uses it for the browser theme color.
- **Butter yellow** (`yellow`): hero headings, constellation stars and lines, brand mark, primary buttons, current language indicator, and the contact band. It is a substantial identity color, not merely a tiny signal accent.

### Secondary

- **Brick** (`coral`): the CSS token retains its historical name, but its shipped appearance is brick red. It supplies the coral section background, default focus outline, and native control accent.
- **Lighter navy** (`navy-light`): desktop submenu surfaces and dark-button hover states.

### Neutral

- **Cream paper** (`paper`): default page and section background, secondary hero copy, and text on brick sections.
- **Deeper paper** (`paper-deep`): portrait placeholders and media backing surfaces.
- **Ink** (`ink`): default text on light surfaces.
- **Muted** (`muted`): supporting copy, dates, roles, captions, and metadata on light surfaces.
- **Light line** (`line`) and **dark line** (`dark-line`): dividers and boundaries on their respective grounds.

Midnight sections use butter headings and cream supporting text; brick sections use cream for both. The legacy `lilac` section theme now resolves to cream paper: there is no separate lilac or mint palette token in the shipped stylesheet. Background-image sections use navy overlays, with none, light, default, and dark treatments defined in CSS.

## Typography

**Display and heading font:** Alegreya, with Georgia and serif fallbacks.

**Body and interface font:** Source Sans 3, with Segoe UI and sans-serif fallbacks.

The base template loads local font faces before the main stylesheet. `config/static/fonts/fonts.css` declares normal weights 400, 500, 600, and 700 for each family, with `font-display: swap`. `SOURCES.json` records the Google Fonts source URLs; the accompanying `Alegreya-OFL.txt` and `SourceSans3-OFL.txt` contain the SIL Open Font License 1.1. Page rendering uses local files rather than a Google Fonts stylesheet request.

### Hierarchy

- **Homepage display:** the frontmatter display role, constrained to 19ch on desktop. The text-only hero allows 24ch.
- **Page title:** Alegreya (500), `clamp(2.15rem, 3.8vw, 3.5rem)`, with the shared heading line height (1.12) and tracking (`-.02em`). Page headings allow 22ch.
- **Section heading and general title:** the frontmatter headline and title roles. Headings balance wrapping and allow long words to break.
- **Reading headings:** h2 uses `clamp(1.65rem, 2.5vw, 2.15rem)`; h3 uses `1.5rem`.
- **Body:** the root size is 17px on desktop and mobile. Reading content is capped at 72ch; paragraphs retain the body line height (1.65).
- **Introductions:** hero summary uses the frontmatter role and a 45ch measure; page introductions use `1.15rem` and 64ch; the About introduction uses `1.08rem`.
- **Interface and metadata:** Source Sans 3. Navigation uses the frontmatter navigation role; buttons use `.9rem` at weight 600; captions use `.85rem` with line height 1.5. Person names use Source Sans 3 at weight 600, rather than the heading serif.

Do not restore Anybody, Atkinson Hyperlegible Next, wide variable-font settings, or the former poster-sized heading scale: those describe the superseded design.

## Layout

The centered desktop shell is `min(1120px, calc(100% - 96px))`. Full-width section backgrounds align their inner content to this shell; builder sections inside content pages extend to the viewport edges.

The desktop homepage hero uses a near-balanced `1.05fr 1fr` grid, a 3rem gap, and a 520px minimum height, with `3rem 3.5rem` block padding. The text-only variant uses one column and a 400px desktop minimum height. About and financing sections use `.85fr 1.15fr` columns; text/image sections use equal columns, usually separated by 4rem. Reading copy remains narrower than the shell.

Builder sections use the frontmatter section-block spacing, with thin rules between adjacent sections. Research, project, collaboration, and publication lists are open rows with dividers, not numbered card grids. People indexes and previews within wide pages use four columns; the homepage preview retains six. Updates use three columns, with a slightly wider news column.

### Responsive behavior

- **At 1100px and below:** shell gutters become 32px; the header exposes the menu control and navigation becomes a vertical panel. The hero retains two columns with a 470px minimum height and a `clamp(2.35rem, 4.3vw, 3.1rem)` title. People grids and previews become three-column; updates become two-column with news spanning both.
- **At 760px and below:** shell gutters become 20px and root type remains 17px. The hero stacks, loses its minimum height, and uses `clamp(2.2rem, 7vw, 2.85rem)` for its title, with a 22ch measure and `2.5rem 2rem` block padding. Builder sections use 2.5rem block padding. About, media, profiles, and contact stack; people use two columns; updates, news, collaborations, and page-link grids use one. Research thumbnails remain visible in a smaller 110px column. The footer uses two columns with its lead spanning both.
- **At 380px and below:** shell gutters become 16px, the constellation becomes a vertical topic list without the decorative SVG, and the footer becomes single-column.

Inline subsections use a wrapping, outlined contents navigation with 8px corners and 44px minimum-height links, anchored section headings, and ruled boundaries. Their scroll margin is 2rem.

## Elevation & Depth

Most content is flat, separated by tonal bands and 1px rules. There is no general card-shadow system or radial hero gradient.

Desktop submenus have a soft shadow (`0 12px 24px rgb(0 0 0 / .18)`), removed in the stacked navigation. Constellation topic stars have a fine offset butter outline, without the former glow. Faint circular and elliptical outlines add orbital structure behind the topics. The image lightbox uses a dark backdrop (`rgb(8 16 28 / .9)`). Buttons lift by 2px on hover without a hard offset shadow.

## Shapes

The reused surface radius is 12px, applied to portraits, hero/media images, galleries, sliders, simulations, submenus, and the lightbox. Research thumbnails use 8px corners. Buttons and contents links use the shared control radius (8px); carousel and lightbox controls are circular. The slider pause control retains its separate pill treatment (100px), not the general action shape. Editorial bands and ruled list structures remain open rather than rounded containers.

Hero images use 5:4 on desktop, capped at 380px high, and 4:3 on mobile. Gallery images use 4:3, sliders and comparisons use 16:9, and person tiles default to 4:4.3. Named portrait options also support square, portrait (3:4), original ratio, and contain fitting.

## Components

### Header and navigation

A shared navy header contains the constellation mark, Source Sans 3 site name, the affiliation “Masaryk University · Czechia”, text navigation, and a native language disclosure linking to published translations of the current page. Header and footer use the same 1200px shell and 16px inherited interface type on every page; homepage CSS never overrides them. The header sticks at the top, gains a subtle shadow and translucent navy background after scrolling, and preserves its height to avoid layout shifts. The inner header has an 82px minimum height, becoming 84px at 1100px and 76px on mobile. The butter mark is 36px square, reducing to 35px on mobile, and can be replaced by an editor-supplied logo. Escape and outside clicks close language/navigation panels; the mobile menu scrolls within the viewport.

Hover and current navigation states use butter text and an underline. Desktop submenus use lighter navy, rounded corners, and separate disclosure buttons. At 1100px and below they become indented lists within the vertical navigation. The template provides `aria-expanded`, `aria-controls`, current-page indicators, and a labeled language navigation. CSS leaves navigation and submenus available when JavaScript is absent.

### Buttons and links

Primary buttons use a butter background with navy text; dark buttons reverse those roles. Both have 8px corners, `.6rem 1.15rem` padding, weight 600, line height 1.35, and a 46px minimum height. The outlined secondary hero action uses cream text, a transparent background, and a 1px dark-line border with the same geometry.

Hover depends on context: ordinary primary buttons become navy with butter text; primary buttons in the hero, midnight/brick sections, or image-background sections become cream with navy text. The dark variant uses lighter navy on hover. The secondary hero action gains a butter border and lighter-navy background. Primary/dark buttons lift 2px and their SVG arrows shift 3px right; color transitions take `.2s`, transforms `.3s` with `cubic-bezier(.16, 1, .3, 1)`. Active buttons move down 1px.

Ordinary links inherit their context color, with a thin underline offset by `.22em`; hover thickens the underline. List titles generally hide the underline until hover. The secondary hero action is styled as the outlined control above, not a plain underlined link.

### Constellation

The homepage constellation is a labeled navigation of actual research topics, not a force-directed or parallax sociogram. HTML links place topic labels and circular stars over a decorative SVG containing dust, curved connections, an orbit, and a central four-point star. Butter supplies the connections and stars; cream supplies the dust and caption.

The template marks the hero with `data-hero-entrance` and pairs topic links with SVG paths using indexed data attributes. `config.js` choreographs a one-shot opening through the Web Animations API (WAAPI), using `cubic-bezier(.16, 1, .3, 1)`, one iteration, and backwards fill:

- Heading, summary, and action links arrive from 10px below and opacity `.55`, over 700ms with short staggered delays.
- Connection paths draw over 1000ms, beginning at 400ms plus a topic stagger spread across at most 1000ms. The final path finishes by 2.4s.
- Topic links use the same 700ms arrival, beginning at 650ms plus that stagger; the positioned list items themselves are not transformed by the entrance.
- Dust fades from 40% of its computed opacity to its resting opacity over 1800ms after a 200ms delay. The central star scales from `.82` to `1` and opacity `.6` to `1` over 1100ms after a 100ms delay.

The entrance completes within 2.4s. The homepage canvas constellation then rotates continuously with traveling connection signals and a subtle central-star pulse; there is no manual pause control. Its rendering suspends outside the viewport or in a hidden tab and resumes automatically, while reduced motion keeps a static network. Non-touch pointer entry and keyboard focus highlight the corresponding connection. Hover and focused topics are tracked independently, so both paths can remain highlighted. Pointer leave/cancel and blur clear their respective states. Labels become cream and underlined on hover or visible keyboard focus; pointer hover also expands the topic-star outline.

Entrance animations are skipped for reduced motion or unavailable WAAPI. Any focus entering the hero cancels outstanding entrance animations immediately, as does a change to the reduced-motion preference. Markup and CSS are visible at rest without JavaScript; animation is enhancement, not a visibility prerequisite. Reduced motion retains immediate pointer/keyboard highlighting without animated transitions.

More than seven topics use a two-column list over subdued SVG linework. At 380px and below, the SVG and decorative orbital outlines are hidden while the topic links remain a readable vertical list.

### Editorial sections and lists

Reorderable builder sections share the shell and paper, midnight, or brick themes. They cover reading text, media, research, people, projects, publications, collaborations, financing, page links, galleries, callouts, embeds, and contact. The homepage also supports image and text-only hero layouts, and retains a legacy section fallback when its section stream is empty.

Research rows pair serif titles and summaries with rounded thumbnails. Publications pair a small year column with title and citation text. Projects use title, status, dates, funder, and introduction; collaborations use ruled entries with optional logos. Updates combine news, projects, and publications in responsive columns.

### People and media

People tiles use rounded portraits, sans-serif names, muted roles, and optional summaries. Missing portraits have an initials-style placeholder surface. Portraits are not styled with the former grayscale hover treatment; pointer hover applies a small scale (`1.035`) over `.5s` inside the rounded crop. Desktop profiles use a 280px portrait rail with a 3rem gap, with 220px/340px small/large variants. Profile headings use `clamp(2rem, 3.5vw, 3.25rem)`. On mobile the layout stacks, the portrait is capped at 260px (230px for small), and the heading is 2.4rem. Carousel mode uses horizontal scroll snapping and circular previous/next controls.

Media components include galleries, a dark image lightbox, before/after comparison, sliders with caption bands and circular controls, responsive video embeds, and bordered simulation frames. Media rounding follows the shared surface radius. Text/image block photos use contain fitting and a 370px height cap; full-image blocks are centered within 860px and capped at 460px high. Article/cover images use a 420px cap, while article-body figures use contain fitting and a 460px cap. Research thumbnails are 168×105px on desktop and 110×85px on mobile.

### Reading pages and inline subsections

Major pages reuse a spacious serif page heading, bounded introduction, body content, section stream, and optional after-body content. Science and project templates can render their child subsections inline, with an outlined, 8px-corner contents navigation and anchored headings; the child-sections builder block uses the same presentation. This is not a grid of links requiring a separate page visit for every subsection.

### Contact and footer

The contact band uses butter with navy text and a two-column introduction/details layout that stacks on mobile. The shared navy footer uses cream copy, butter headings and tagline, optional contact/social columns, and a ruled copyright row, with 4rem top padding and a 1.4rem site name on every page.

## Do's and Don'ts

- **Do** reuse the shipped navy, butter, cream, and brick tokens, serif/sans pairing, compact typography, bounded photos, rounded media, and 8px-corner action controls.
- **Do** retain open, ruled editorial lists and bounded reading measures instead of wrapping all content in cards.
- **Do** preserve the skip link, semantic headings and landmarks, labeled topic links, language navigation, and visible focus. The shipped focus outline is 3px brick with a 5px offset, changing to butter in the header, hero, footer, midnight sections, and brick sections.
- **Do** preserve reduced-motion handling in both CSS and JavaScript: CSS disables smooth scrolling and all CSS animations/transitions, and removes button/arrow/portrait hover transforms; JavaScript skips or cancels the finite hero entrance. Keep keyboard focus cancellation and the visible no-JavaScript resting state.
- **Do** keep the opening finite (at most 2.4s) and connection highlighting available to both pointer and keyboard users; do not make users wait for choreography to access links.
- **Do** keep optional images, summaries, contact fields, and translations optional in the existing templates.
- **Do** keep this document aligned with the stylesheet and local font declarations when the implementation changes.
- **Don't** restore obsolete lilac/mint accents, square buttons, numbered sociogram-era rows, grayscale portraits, parallax, or hard coral hover shadows as if they were current design rules.
- **Don't** describe the constellation as measured network data or imply quantitative meaning for its decorative connections.
- **Don't** mistake legacy theme names or retained subsection routes for a different visual system or a requirement to split the major reading pages.
- **Don't** treat this implementation record as proof of a final approved logo, final Parta copy, or new accessibility/performance validation.
