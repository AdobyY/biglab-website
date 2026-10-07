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
