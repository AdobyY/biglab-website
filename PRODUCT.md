# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary visitors are students, parents, school principals and teachers who are already involved in BIG Lab projects. Secondary visitors are researchers and collaborators who know the lab or may work with it.

## Product Purpose

The site explains BIG Lab's research, people, projects and results, and gives each audience a clear path to the information relevant to them. Success means the lab can maintain current content itself and visitors can understand the lab's work without university-site context.

## Positioning

BIG Lab studies how attitudes and behaviours form in individuals and spread through social ties, within groups and across society, combining psychology, sociology and network science.

## Operating Context

One lab administrator updates the site roughly monthly through Wagtail. The public site has no visitor accounts, forms or search. Content includes text, people, news, publications, collaborations, projects, images, videos and PDF documents.

## Capabilities and Constraints

- Django and Wagtail with SQLite.
- English and Czech content; other locales may be added later and partial translation is acceptable.
- Major sections remain separate top-level pages, with subsections rendered inline on their owning long page rather than requiring a separate visit for every child. Science research areas and project subsections use anchored headings and a contents navigation, through the default templates or a visible child-sections builder block. Child records and legacy standalone routes are retained; navigation to Science/Project children targets the parent-page anchor when inline rendering is enabled, otherwise it uses the child route.
- Parta is treated as a featured project until the lab supplies its final description.
- Prepared animations or simulations can be embedded; editors cannot author arbitrary JavaScript.
- The lab edits content directly without an approval workflow.

## Brand Commitments

The working name is BIG Lab / Behaviors of Individuals and Groups Lab. The shipped design uses a constellation as a metaphor for hidden interdependence, with navy and butter yellow, cream reading surfaces, brick accents, and Alegreya paired with Source Sans 3. `DESIGN.md` records the implemented visual system; the earlier mycelium and earthy-green alternatives are not the current design. The site is not required to follow the university visual identity.

## Evidence on Hand

- Public Czech and English BIG Lab pages on the Psychology Research Institute website.
- Current descriptions of the lab, six team members, five research areas, two 2026 publications, three projects, four collaborations and one news item.
- Google Docs requirements saved locally as `requirements.md` and `questios.md`.
- No approved standalone logo, final Parta copy, testimonials, performance claims or visitor data.

## Product Principles

- Make relationships visible: show how people, topics and projects connect.
- Let evidence lead: real research, people and outputs outrank marketing language.
- Keep editorial work simple enough for one occasional administrator.
- Design for readers outside the lab without flattening scientific specificity.

## Accessibility & Inclusion

The public site must remain keyboard usable, responsive, readable with reduced motion, and structured with semantic headings and accessible link labels.
