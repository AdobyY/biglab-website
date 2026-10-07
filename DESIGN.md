---
name: BIG Lab
description: A navy and butter homepage with a contained spatial network plus a dark homepage with a full-width abstract field.
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

BIG Lab has two homepage versions sharing the same editorial content, local fonts, navigation, footer structure, and all section geometry below the hero. Version 1 remains the default, pairing navy/butter copy with its restored contained spatial network and real research-topic links on the right, followed by cream reading surfaces and occasional brick-colored sections. Version 2 uses one continuous dark surface and an abstract relationship field across its complete opening. Hollow junctions and curved connections express interaction and influence without a central hub. The constellation brand mark remains in the shared header, while neither hero uses a central star or orbital traces.

Alegreya's serif headings pair with Source Sans 3 for prose and interface text. Bounded photos accompany open editorial sections, thin dividers, rounded imagery, and softly rectangular controls. Version 1 pairs copy on the left with its contained three-dimensional network on the right. Version 2 centers the unchanged copy within a quiet area of its full-width network; research-topic navigation belongs to the common research section below, rather than its decorative opening. Below the two distinct heroes, the versions differ in palette rather than spacing, typography, image size, or layout.

This document records the current implementation, not a new design proposal. Shared sources are `config/static/css/config.css`, `config/static/js/config.js`, `config/templates/base.html`, the templates under `home/templates/home/`, and `config/static/fonts/fonts.css`. Both versions load `homepage.css` for shared homepage geometry. Version 1 adds `home/includes/hero_v1.html`, `homepage-v1.css`, `homepage-v1.js`, and `hero-v1-entrance.js`. Version 2 adds `hero-network.css`, the palette-only `homepage-v2.css`, `homepage.js`, and `hero-network.js` under the corresponding static directories. `design-switch.css` styles the small version control. Frontmatter records the baseline palette and representative desktop type roles; Version 2's editable palette and component-specific overrides are described below.

### Homepage version selection

The homepage always defaults to Version 1. Only the exact query parameter `?design=2` selects Version 2; there is no editor setting that changes the default and no local-storage preference. A small fixed control at the bottom right shows V1/V2 and switches through a normal GET link. It retains the current language path and all other query parameters, adds `design=2` when entering Version 2, and removes the parameter when returning to Version 1. Language links on Version 2 retain its version parameter. Both versions use the same stored page content, rather than copied editorial pages.

## Colors

The palette below remains the baseline for Version 1 and internal pages. Version 2 overrides it only on its homepage.

### Primary

- **Navy** (`navy`): header, hero, footer, dark buttons, and midnight section backgrounds. The base template also uses it for the browser theme color.
- **Butter yellow** (`yellow`): hero headings, network nodes and strands, brand mark, primary buttons, current language indicator, and the contact band. It is a substantial identity color, not merely a tiny signal accent.

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

### Version 2 editable palette

Wagtail's **Homepage design (Version 2)** settings expose one palette per site, shared across all languages. All five fields use native color controls and strict six-digit hexadecimal validation (`#RRGGBB`); they cannot contain arbitrary CSS values. They apply only to the Version 2 homepage, including its header, footer, sections, controls, and network.

| Setting | Default | Role |
| --- | --- | --- |
| `background` | `#0b141e` | Continuous dark surface |
| `foreground` | `#eeeae0` | Primary text |
| `accent` | `#dac99c` | Actions, active junctions, and relationship highlights |
| `muted` | `#a6b4bd` | Supporting text and metadata |
| `network_secondary` | `#7f9d98` | Secondary network connections and accents |

Version 2 remaps the existing CSS theme tokens to these values and uses subtle mixed-color dividers. Its homepage sections share the same background instead of alternating paper, butter, and brick bands. Palette changes do not alter Version 1, other pages, or their editor content.

## Typography

**Display and heading font:** Alegreya, with Georgia and serif fallbacks.

**Body and interface font:** Source Sans 3, with Segoe UI and sans-serif fallbacks.

The base template loads local font faces before the main stylesheet. `config/static/fonts/fonts.css` declares normal weights 400, 500, 600, and 700 for each family, with `font-display: swap`. `SOURCES.json` records the Google Fonts source URLs; the accompanying `Alegreya-OFL.txt` and `SourceSans3-OFL.txt` contain the SIL Open Font License 1.1. Page rendering uses local files rather than a Google Fonts stylesheet request.

### Hierarchy

- **Homepage display:** Version 1 uses Alegreya at `clamp(2.65rem, 4.35vw, 3.7rem)`, a 1.08 line height, `-.025em` tracking, and a 19ch maximum measure. Version 2 uses `clamp(3.3rem, 5.45vw, 4.6rem)`, a 1.04 line height, `-.03em` tracking, and a 940px maximum width, centered with balanced wrapping. Other hero variants retain their separate bounded measures.
- **Page title:** Alegreya (500), `clamp(2.15rem, 3.8vw, 3.5rem)`, with the shared heading line height (1.12) and tracking (`-.02em`). Page headings allow 22ch.
- **Section heading and general title:** the frontmatter headline and title roles. Headings balance wrapping and allow long words to break.
- **Reading headings:** h2 uses `clamp(1.65rem, 2.5vw, 2.15rem)`; h3 uses `1.5rem`.
- **Body:** the root size is 17px on desktop and mobile. Reading content is capped at 72ch; paragraphs retain the body line height (1.65).
- **Introductions:** Version 1's hero summary is `1.04rem` with a 43ch maximum width. Version 2's summary is centered, `1.05rem` with a 1.7 line height and 53ch maximum width. Page introductions use `1.15rem` and 64ch; the About introduction uses `1.08rem`.
- **Interface and metadata:** Source Sans 3. Navigation uses the frontmatter navigation role; buttons use `.9rem` at weight 600; captions use `.85rem` with line height 1.5. Person names use Source Sans 3 at weight 600, rather than the heading serif.

Do not restore Anybody, Atkinson Hyperlegible Next, wide variable-font settings, or the former poster-sized heading scale: those describe the superseded design.

## Layout

The centered desktop shell is `min(1120px, calc(100% - 96px))`. Full-width section backgrounds align their inner content to this shell; builder sections inside content pages extend to the viewport edges.

Version 1 uses a `.95fr 1.05fr` desktop hero grid with zero-minimum tracks, a 3rem gap, and a 620px inner minimum height, with copy on the left and a contained spatial network up to 560px wide on the right. Topic links keep their established positions and destinations, while network activity changes without replacing text or shifting its width. Version 2's decorative network spans the complete opening behind one centered copy column. Its inner minimum height is `clamp(640px, calc(100svh - 145px), 840px)`, with 6rem top and 7rem bottom padding. Neither hero has a topic caption; Version 2 also has no topic-navigation ribbon. Image and text-only hero variants retain their optional editorial media. Reading copy remains narrower than the shell.

Builder sections in both versions share `clamp(3rem, 5vw, 4.5rem)` block spacing and thin rules between adjacent sections. About and financing use `.85fr 1.15fr` editorial columns. Research uses two columns with a featured first row spanning both, pairing its larger heading and summary with a wide image; later rows retain smaller bounded thumbnails. People previews use six columns on desktop, updates use their common three-column layout, and Parta/contact keep the same heading sizes, spacing, and image geometry in both versions. Version 1 retains its cream/butter/brick bands; Version 2 changes these surfaces and text colors to its editable dark palette. Other page indexes retain their existing layouts.

### Responsive behavior

- **At 1100px and below:** shell gutters become 32px; the header exposes the menu control and navigation becomes a vertical panel. Version 1 retains two hero columns with a 510px inner minimum height. Version 2 stays centered, with a `clamp(3rem, 6vw, 4rem)` title. Both homepage people previews become three-column; other page grids retain their responsive rules.
- **At 760px and below:** shell gutters become 20px. Version 1's hero stacks; Version 2 keeps centered copy with a `clamp(2.3rem, 7.3vw, 3.3rem)` title and a full-section decorative canvas. Its inner minimum height becomes `clamp(630px, calc(100svh - 145px), 790px)`, with 5.5rem top and 6.5rem bottom padding. Its network has no topic links to resize. Shared below-hero sections use 3.5rem block spacing; About, media, profiles, and contact stack, people use two columns, and research/updates use one. Research rows in both versions place a small image beside the title and the summary below. Parta/contact headings use the same 1.8rem mobile size. The footer uses two columns with its lead spanning both.
- **At 380px and below:** shell gutters become 16px and the footer becomes single-column. Version 1 retains positioned topic labels for small collections and switches dense collections to a vertical list. Its mobile hero footnote reserves 7.5rem on the right for the fixed version control. Version 2 continues to use a decorative field independent of research-topic count.

Inline subsections use a wrapping, outlined contents navigation with 8px corners and 44px minimum-height links, anchored section headings, and ruled boundaries. Their scroll margin is 2rem.

## Elevation & Depth

Most content is flat, separated by tonal bands and 1px rules. There is no general card-shadow system or radial hero gradient.

Desktop submenus have a soft shadow (`0 12px 24px rgb(0 0 0 / .18)`), removed in the stacked navigation. Version 1 retains the original slowly rotating spherical network, using projected depth and straight local connections behind fixed topic labels. Version 2 uses curved relationships and hollow junctions across the section behind a soft copy mask. Neither uses a central star, radial glow, dust, orbital rings, or center spokes. The image lightbox uses a dark backdrop (`rgb(8 16 28 / .9)`). Buttons lift by 2px on hover without a hard offset shadow.

## Shapes

The reused surface radius is 12px, applied to portraits, hero/media images, galleries, sliders, simulations, submenus, and the lightbox. Research thumbnails use 8px corners. Buttons and contents links use the shared control radius (8px); carousel and lightbox controls are circular. The slider pause control retains its separate pill treatment (100px), not the general action shape. Editorial bands and ruled list structures remain open rather than rounded containers.

Hero images use 5:4 on desktop, capped at 380px high, and 4:3 on mobile. Gallery images use 4:3, sliders and comparisons use 16:9, and person tiles default to 4:4.3. Named portrait options also support square, portrait (3:4), original ratio, and contain fitting.

## Components

### Header and navigation

A shared header contains the constellation mark, Source Sans 3 site name, the affiliation “Masaryk University · Czechia”, text navigation, and a native language disclosure linking to published translations of the current page. Header and footer use the same 1200px shell and 16px inherited interface type on every page. Version 1 and internal pages keep the navy/butter palette; Version 2 deliberately applies its editable palette to the homepage's shared header and footer without changing their structure. The header sticks at the top, gains a subtle shadow after scrolling, and preserves its height to avoid layout shifts. Its baseline scrolled surface is translucent navy, while Version 2 keeps its continuous dark background. The inner header has an 82px minimum height, becoming 84px at 1100px and 76px on mobile. The mark is 36px square, reducing to 35px on mobile, and can be replaced by an editor-supplied logo. Escape and outside clicks close language/navigation panels; the mobile menu scrolls within the viewport.

Hover and current navigation states use butter text and an underline. Desktop submenus use lighter navy, rounded corners, and separate disclosure buttons. At 1100px and below they become indented lists within the vertical navigation. The template provides `aria-expanded`, `aria-controls`, current-page indicators, and a labeled language navigation. CSS leaves navigation and submenus available when JavaScript is absent.

### Buttons and links

Primary buttons use a butter background with navy text; dark buttons reverse those roles. Both have 8px corners, `.6rem 1.15rem` padding, weight 600, line height 1.35, and a 46px minimum height. The outlined secondary hero action uses cream text, a transparent background, and a 1px dark-line border with the same geometry.

Hover depends on context: ordinary primary buttons become navy with butter text; primary buttons in the hero, midnight/brick sections, or image-background sections become cream with navy text. The dark variant uses lighter navy on hover. The secondary hero action gains a butter border and lighter-navy background. Primary/dark buttons lift 2px and their SVG arrows shift 3px right; color transitions take `.2s`, transforms `.3s` with `cubic-bezier(.16, 1, .3, 1)`. Active buttons move down 1px.

Ordinary links inherit their context color, with a thin underline offset by `.22em`; hover thickens the underline. List titles generally hide the underline until hover. The secondary hero action is styled as the outlined control above, not a plain underlined link.

### Version 1 restored spatial network

The default homepage uses `home/includes/hero_v1.html`: copy and actions sit on the left, with the restored decorative spherical network and real research-topic links on the right. Its former central star, dust, orbital traces, center spokes, and Research areas / movement caption have been removed. Labels retain their actual destinations and fixed geometry; hover never substitutes words or changes their width. Butter supplies the contained network's relationships and active states, without implying measured research data.

`homepage-v1.js` retains the original seed-42 topology: 150 nodes distributed in three dimensions at radii of 125–180, with straight relationships between nodes less than 66 units apart. Projected depth, cursor proximity, click waves, and topic hover/focus highlighting remain. Topic groups follow longitude without changing copy or layout. Automatic rotation runs at .06 radians per second; yaw/pitch interpolation uses .055, vertical pointer sensitivity .42, and breathing amplitude .018 for a gentler response. Short influence strokes travel along actual connections, with ambient waves every seven seconds. Scroll retains the original expansion and rotation response. Dust, orbital ellipses, and energy rings around nodes are omitted.

`hero-v1-entrance.js` introduces topic links in a finite stagger, while shared `config.js` introduces the heading, summary, and actions. The established topic-navigation scale is intentionally smaller than editorial headings: `.78rem` on desktop, `.74rem` at 1100px, `.76rem` at 760px, and `.7rem` at 380px; label backing retains its 4px corner radius. Topic markers use 10px circles with a quiet fixed outline. Collections of more than seven topics retain the dense wrapping list, becoming single-column at 380px; the original canvas engine runs only for smaller collections.

The canvas suspends offscreen or in a hidden tab and has no manual pause control. Reduced motion retains a static graph with immediate topic hover/focus highlighting and no ambient or scroll motion. Without JavaScript, a static SVG of straight network connections remains behind the usable topic links; it contains no central star, center spokes, or orbital traces.

### Version 2 abstract relationship field

Version 2 centers the unchanged editorial copy within one full-section abstract relationship field. The decorative canvas is `aria-hidden` and independent of the number or identity of research topics. Hollow circular junctions represent individuals through their connections, without profile medallions or measured research data. There is no topic navigation, topic caption, hover-label repetition, central star, orbital diagram, or fixed set of topic hubs in this opening. Research content remains in the Science section below.

`hero-network.js` distributes junctions through deterministic rejection sampling with minimum spacing: 104 on wide screens, 76 below 1100px, and 46 below 600px. Resting junctions have radii between 2.4px and 4.2px and are hollow rather than glowing points. Nearest-neighbor ties form a distributed graph, capped at four connections per junction, with bridges joining disconnected paths and up to eight additional distant ties. Cubic curves vary in strength, curvature, and stroke width; idle local lines range approximately from 0.8px to 1.25px. Muted secondary color supplies resting junctions and connections; accent supplies their active states.

Pointer attention locally stretches the connections and warms their color. Nearby junctions move toward the pointer by at most 10px per axis; curve control points can move by up to 24px within a 230px influence radius. The nearest junction starts a graph cascade at a 0.65s cooldown. Influence appears as a stroked reveal along a 0.17-length section of the actual curve, without a flying particle head or tail. Signals propagate for up to three hops with diminishing strength, branching to at most three initial and two later routes; at most 28 packets are live. Clicking or tapping empty hero space activates the two nearest junctions without intercepting actions. Ambient influence starts after one second and repeats every 3.4s. There are no cursor trails, profile pictograms, chat marks, radial glows, topic-focus interactions, or repeated hover labels.

Slow shared motion reshapes the complete field rather than moving separate topic groups. Scroll progress smoothly changes junction geometry and connection curvature, while copy, actions, and hit targets remain fixed. A soft canvas mask erases the illustration behind the measured heading, summary, actions, and footnote, without adding an opaque card. Canvas bounds update on resize and scroll; topology rebuilds when the section's dimensions change.

Rendering uses one approximately 30fps loop with a device-pixel ratio capped at 1.75. It suspends outside the viewport or in a hidden tab and resumes automatically. Reduced motion disables pointer deformation, graph cascades, ambient motion, and scroll rearrangement, retaining the static relationship field. The canvas is available for the constellation layout even with zero research topics; image and text-only layouts omit it.

The opening's motion is a decorative enhancement: absent JavaScript leaves all copy and actions visible and usable, with an empty decorative canvas. There is no pause button. Shared entrance animations remain finite, are skipped when motion is reduced or WAAPI is unavailable, and cancel immediately when keyboard focus enters the hero or the motion preference changes. Both versions use the same research-section content and Research areas fallback heading; editor-supplied section titles remain respected.

### Editorial sections and lists

Reorderable builder sections share the shell and paper, midnight, or brick themes. They cover reading text, media, research, people, projects, publications, collaborations, financing, page links, galleries, callouts, embeds, and contact. The homepage also supports image and text-only hero layouts, and retains a legacy section fallback when its section stream is empty.

Research rows pair serif titles and summaries with rounded thumbnails. Publications pair a small year column with title and citation text. Projects use title, status, dates, funder, and introduction; collaborations use ruled entries with optional logos. Updates combine news, projects, and publications in responsive columns.

### People and media

People tiles use rounded portraits, sans-serif names, muted roles, and optional summaries. Missing portraits have an initials-style placeholder surface. Portraits are not styled with the former grayscale hover treatment; pointer hover applies a small scale (`1.035`) over `.5s` inside the rounded crop. Desktop profiles use a 280px portrait rail with a 3rem gap, with 220px/340px small/large variants. Profile headings use `clamp(2rem, 3.5vw, 3.25rem)`. On mobile the layout stacks, the portrait is capped at 260px (230px for small), and the heading is 2.4rem. Carousel mode uses horizontal scroll snapping and circular previous/next controls.

Media components include galleries, a dark image lightbox, before/after comparison, sliders with caption bands and circular controls, responsive video embeds, and bordered simulation frames. Media rounding follows the shared surface radius. Text/image block photos use contain fitting and a 370px height cap; full-image blocks are centered within 860px and capped at 460px high. Article/cover images use a 420px cap, while article-body figures use contain fitting and a 460px cap. Research thumbnails are 168×105px on desktop and 110×85px on mobile.

### Reading pages and inline subsections

All internal pages load `internal-pages.css`, with a shared page-heading include and localized breadcrumbs generated from the actual Wagtail tree. Collection headings pair the title with a bounded introduction on desktop and stack on mobile. Neutral sections align to the same reading grid, including Wagtail's StreamField wrappers; colored and background-image sections retain full-width surfaces. Empty body fields create no layout containers. Team and News suppress repeated default section titles and links to themselves while preserving custom editor headings.

Science and project subsections share an inline collection: a 230px sticky contents rail and anchored editorial rows on desktop, becoming an ordinary contents list on mobile. Topic images sit beside their summaries at 220px wide (160px on intermediate screens), then become bounded illustrations below the text on narrow phones. Each subsection links back to contents. `internal-pages.js` progressively marks the current section while reading; native anchor navigation remains usable without JavaScript. Publications and collaborations follow as separate sections.

The Team index uses three columns with standard portraits capped at 240px, retaining editor-controlled small/large, aspect-ratio and fit options; mobile uses two columns. Individual profiles align the portrait with the name, role and readable biography, with a full-width reading column when the portrait is missing or hidden. News uses editorial image/text rows rather than oversized tiles; project lists pair names and dates with summaries and funding details. Standalone content covers are capped at 720px wide / 300px high, and news covers at 860px / 380px. Profiles, news, research details and projects have a shared parent / previous / next navigation containing only published siblings, with research destinations respecting the parent's inline-section configuration.

### Contact and footer

The baseline contact band uses butter with navy text and a two-column introduction/details layout that stacks on mobile. The shared footer has optional contact/social columns and a ruled copyright row, with 4rem top padding and a 1.4rem site name on every page. Version 1 and internal pages keep its navy background, cream copy, and butter headings/tagline. Version 2 keeps the same structure on its continuous homepage background, using the editable foreground and accent colors.

## Do's and Don'ts

- **Do** preserve Version 1 and internal pages' navy, butter, cream, and brick identity. Keep Version 2's editable palette scoped to its homepage, while retaining the serif/sans pairing, bounded photos, rounded media, and softly rectangular controls.
- **Do** retain open, ruled editorial lists and bounded reading measures instead of wrapping all content in cards.
- **Do** preserve the skip link, semantic headings and landmarks, labeled research links, language navigation, and visible focus. The baseline focus outline is 3px brick with a 5px offset, changing to butter in the header, hero, footer, midnight sections, and brick sections. Version 2 uses its editable accent for focus.
- **Do** preserve reduced-motion handling in both CSS and JavaScript: CSS disables smooth scrolling and all CSS animations/transitions, and removes button/arrow/portrait hover transforms; JavaScript skips or cancels the finite hero entrance. Keep keyboard focus cancellation and the visible no-JavaScript resting state.
- **Do** keep content entrance finite and controls immediately accessible. Keep Version 1's topic labels fixed during pointer and keyboard interaction. Keep Version 2's copy and hit targets stationary during ongoing pointer and scroll motion; its network must remain independent of research-topic navigation. Below both heroes, share section geometry and vary only the palette.
- **Do** keep optional images, summaries, contact fields, and translations optional in the existing templates.
- **Do** keep this document aligned with the stylesheet and local font declarations when the implementation changes.
- **Don't** restore obsolete lilac/mint accents, square buttons, numbered sociogram-era rows, grayscale portraits, text parallax, or hard coral hover shadows as if they were current design rules.
- **Don't** describe either decorative network as measured data or imply quantitative meaning for its node prominence or connections.
- **Don't** mistake legacy theme names or retained subsection routes for a different visual system or a requirement to split the major reading pages.
- **Don't** treat this implementation record as proof of a final approved logo, final Parta copy, or new accessibility/performance validation.

The October content update adds editable methods, publications, completed projects,
collaborations and discovery links to both homepages. About groups Lab, People and News;
Science exposes its published research sections and publication/collaboration/project
anchors. Homepage and Science omit the redundant Contents strips and sidebar. Science
uses a continuous full-width reading column with bounded research images. The homepage
mission pairs its existing copy with the real SATIS meeting photo, bounded at 340px
high. Homepage collections share an editorial title rail at roughly one quarter of
the content width. Display headings range from 2.3 to 3.15rem and become 2.1rem on
mobile. Research is a five-column photographic index of equal topics with images
capped at 124px high, becoming three columns below 1100px and horizontal rows with
76px thumbnails on mobile. A shared Science introduction
replaces repetitive preview descriptions; the full topic text remains on Science.
There is no oversized featured first topic. The homepage team is a static four-column
gallery with 104 × 130px portraits above serif names and muted roles. Below 1100px it
becomes three columns; on mobile it has two columns with 80 × 100px portraits. All selected
members remain visible without carousel controls. Updates fit their actual column
count, with 172 × 140px news thumbnails and grouped project rows. Method illustrations,
italic PARTA lettering, prominent publication years, collaborators and discovery links
give each collection its own rhythm within the shared grid. Sections use 3.25rem
desktop / 2.5rem mobile padding. Homepage collection titles use 1.2–1.8rem serif type;
supporting copy uses .85–1rem sans-serif type. The People index
shows all eight members in a regular three/two-column grid; optional carousel tracks
explicitly reset inherited fixed columns so every portrait retains its width.
Missing portraits use a neutral grey silhouette. GIF detail images start on a still
poster, with explicit localized Play/Pause controls; linked thumbnails use the poster.

Editorial references: Kinfolk Stories (https://www.kinfolk.com/stories/) for ruled
photographic columns and confident serif hierarchy; Pentagram's Isomorphic Labs
case study (https://www.pentagram.com/work/isomorphic-labs) for a coherent scientific
identity organized around a grid. These inform composition; BIG Lab retains its own
palette, fonts, photographs and geometric illustrations.
