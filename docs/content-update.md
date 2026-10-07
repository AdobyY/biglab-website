# Client content update — 7 October 2026

The client CONTENT document supplied complete EN/CS biographies for Petra Paličková,
Michaela Kryštofová, Adéla Franková and Olesja Nyjherová. These are now imported in
full. Ching Ting Ang's role is updated; the other original biographies are retained.
Petra and Adéla have paired EN/CS profiles. Petra and Michaela use the supplied photos
with editable focal crops; Adéla uses the requested grey silhouette. Verified MUNI
links from the document are retained. Olesja's existing portrait is unchanged.

Both homepages have ten editable builder sections, plus the existing funding and
contact sections. Methods summarize the existing verified mission; publications,
collaborations and completed projects use the existing CMS records. The Czech mission
block now contains a translation of the existing English mission and methods.
Science also exposes completed projects in a continuous reading layout. Navigation groups
Lab/People/News under About and projects/publications/collaboration under Science.

Under PARTA, school, parent and student drafts now belong to About the project;
timeline and results remain siblings. The accidental published Czech student stub is
unpublished. The requested detailed PARTA copy is still absent from the source document.

## GIF uploads

Upload a GIF through the same Wagtail image chooser used for JPG/PNG (current maximum
10 MiB). Normal resize/crop renditions preserve frames, timing, loop settings and
transparency using Pillow/Willow, without an ImageMagick installation. Article images,
profile images and text/image sections display a still poster until the visitor presses
Play; Pause returns to the poster. Playback stops when scrolled out of view or when the
tab becomes hidden. Linked team/news/gallery thumbnails and comparisons use still
posters to keep their existing link/slider controls accessible. An animated portrait
plays on the profile detail view. Section backgrounds use their own rendition helper.

The client's network GIF files are available in the shared Drive but have not been
imported into this update. The homepage retains its existing interactive network.

## Content still needed from the lab

- Personal email/contact details for each member (the source explicitly says to write these).
- Final lab mission/funding wording, if the new document is intended to replace existing copy.
- New news, publications, collaboration and completed-project entries beyond the existing records.
- PARTA overview and audience copy for schools, parents and students; timeline and results.

The document marks these as "to be written"; no expanded approved descriptions are
provided for them. Empty personal contact fields remain empty.

The updated local CMS content is exported into `home/seed_content/content.json` with
its original assets for the existing seed workflow. A pre-import SQLite backup is
kept in the ignored `.impeccable/implementation-20261007/` directory. No deployment
was performed.

## Verification

The layout follow-up removes redundant Contents strips from the homepage and Science,
including Science's duplicate sidebar. People now displays all eight profiles in a
regular grid. Optional carousel tracks reset fixed grid columns to prevent zero-width
cards. The homepage adds the existing SATIS meeting photo, larger research images,
consistent line icons, three method columns and a symbolic PARTA audience diagram.
The editable CMS content is preserved in both languages and exported again.

The subsequent homepage density revision uses equal research entries with bounded
thumbnails and one shared Science introduction; full topic descriptions remain on
Science. The homepage team becomes a static compact directory with names and roles
beside small portraits (above them on mobile). News/projects use their actual column
count. Methods, PARTA, publications, completed projects, collaborators, discovery and
contact now use tighter spacing and bounded graphics. The large detail-page portraits
and editor-controlled internal-page carousel remain available. Research and team
catalogues at Oxford Internet Institute and MIT Media Lab informed the browsing layout;
their content and imagery were not imported.

This revision passes the same 26 relevant tests and the 46-page route/anchor checks.
Chrome confirms 104px research thumbnails and 110px team portraits on desktop, 76px
research thumbnails and 100px team portraits at 390px, and no overflow at 320px.
The EN/CS variants and both homepage palettes retain the new shared layout. Both
layout detector passes have no findings. `git diff --check` passes.

For this follow-up, the 26 relevant frontend, homepage and animated-image tests pass.
Chrome confirms all eight optional carousel cards retain their width at desktop and
390 px, and Czech People/mobile homepage have no horizontal overflow. Both homepage
designs show the new visuals; Science has no duplicate Contents navigation. All 46
published pages pass the route, heading, anchor and internal-link checks. Migration
drift and whitespace checks pass. The earlier full-suite verification below predates
this layout follow-up.

- All 127 Django tests pass, including animated crop/resize, timing/loop, transparency,
  poster controls and the updated missing-portrait contract.
- `manage.py check`, migration drift check and `git diff --check` pass.
- All 46 published local EN/CS pages return HTTP 200, with one H1, unique IDs and
  no broken internal destinations or nested buttons inside links.
- Chrome checks confirm desktop and 390 px Czech mobile layouts without overflow
  or broken images; mobile About disclosure and Escape work. V2 publications and
  corrected collaboration widths are visually confirmed. A local interaction harness
  confirms GIF Play/Pause switches between the animated rendition and its poster.
- One static Impeccable scan reports no primary findings; advisory scale/color
  suggestions were reviewed against the existing identity and requested grey silhouette.

October editorial design follow-up:
- References reviewed on their official sites: Kinfolk Stories and Pentagram's
  Isomorphic Labs case study. Their column rhythm, serif hierarchy and scientific
  grid informed the composition; no third-party photographs or copy were imported.
- Homepage collections now share a left title rail. Research uses a five-topic
  photographic index, People a four-column portrait gallery, and Publications
  prominent unbroken years. Methods, PARTA, updates, collaborators and discovery
  links retain distinct compositions within the same spacing and type system.
- The 26 relevant frontend, homepage and animated-image tests pass. All 46 published
  pages pass route, heading, anchor and internal-link checks. No backend or content
  changes were required for this design pass.
- Chrome inspection covers desktop, 1000px, 390px and 320px, English and Czech,
  and both homepage palettes: no horizontal overflow or broken loaded images.
  Publication year wrapping was corrected and confirmed on desktop and mobile.
- The static detector reports no primary findings; typography advisories reflect
  the intentionally expanded editorial scale, now recorded in DESIGN.md.
  Git whitespace checks pass. Screenshots are retained in the ignored local
  .impeccable/layout-repair-20261007/ evidence directory.

October photographic composition follow-up (supersedes the collection rail above):
- Research and People now use the full homepage shell. Lighter display headings
  contrast with sans-serif topic links, profile names and citation titles. Portraits
  are bounded at 210 × 240px instead of enlarged landscape crops.
- Research progressively adds one still photograph that follows pointer hover and
  keyboard focus. Native topic links continue to navigate to their actual anchors.
  The no-JavaScript collection and no-image fallback remain usable; mobile uses
  a two-column photographic index. No animation or new dependency was added.
- All 26 relevant Django tests pass, as do the 46 published-page route, heading,
  ID and internal-link checks. The script passes syntax and dependency-free behavior
  checks for initialization, hover/focus, missing images, GIF posters and idempotence.
- Chrome confirms desktop, 1000px, 390px and 320px layouts, both languages and both
  palettes, with no horizontal overflow or broken loaded images. Keyboard Tab
  updates the selected photograph to the focused topic. Portrait cropping and
  the denser research heading were corrected in the final bounded review.
- One static detector pass has no primary findings; type scale advisories were
  reviewed against the intended display/interface contrast and recorded in DESIGN.md.
  Git whitespace checks pass. Local screenshot evidence uses premium-*.jpg under
  the ignored .impeccable/layout-repair-20261007/ directory.
