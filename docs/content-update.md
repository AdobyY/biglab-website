# Client content update — 12 November 2026

The supplied `CONTENT.docx` is fully represented in the committed bilingual baseline
in `home/seed_content/`. Original documents and logo files are retained unchanged in
`home/seed_assets/supplied/`; asset provenance is in `home/seed_assets/SOURCES.md`.
The snapshot is the source used by the existing `seed_biglab` command. Runtime
pages, images and settings remain editable through their existing Wagtail owners.

## Imported content

- Complete Czech/English lab description and INPSY affiliation, retaining the
  interactive network on the homepage.
- Eight team profiles. All supplied biographies, roles and personal emails are
  transferred. Tibor is Head / Vedoucí; Michaela and Ang are PhD candidates.
  Petra and Michaela retain their supplied portraits; Olesja's portrait is unchanged;
  Adéla uses the existing grey silhouette. The repeated team introduction is removed.
- Six news items per language, with publication dates from the document. Automatic
  lists show the newest first. SATIS retains its photo and links; the EUSN2026 item
  uses the photograph embedded in Word. The interview and Ang profile links work.
- Publications retain linked titles, authors, year and journal. The publication-type
  field is blank, as requested. Collaborating institutions use the existing shared
  snippets, corrected names/descriptions and clickable websites.
- PARTA overview, About the project, complete audience pages for schools, parents
  and students, eligibility, research phases, benefits and working internal buttons.
- A seven-period timeline covering spring 2026 through spring 2029. Period labels,
  dates and descriptions are editable in the Timeline content block. The most recent
  start date on or before today receives the localized current-period badge, without
  JavaScript. The badge describes the scheduled period, not verified research progress.
- Shared contact email `biglab@muni.cz`, office 2.53, Joštova 218/10, 602 00 Brno,
  a map and People link. Contact introductions use localized Interface text; the
  actual contact details and logo remain in Contact settings. Contact pages and
  homepage blocks reuse these owners.
- Results remain unpublished. Finished-project sections are hidden; the historical
  self-harm project is unpublished. Existing current-project records and verified
  funding text remain available.

Editorial instructions, bracketed button placeholders and the sample timeline image
are not published as copy. Brackets become real internal links or the existing map.
The original RGB PDF supplies the shared emblem; its vector full-logo export is
available in `config/static/images/biglab-logo-full.svg`.

## Repeatable commands

```powershell
uv run python manage.py migrate
uv run python manage.py seed_biglab --check
uv run python manage.py seed_biglab
uv run python manage.py runserver
```

`--check` is read-only. It validates models, identities, page-tree order, locales,
internal references, required original files and SHA-256 checksums before importing.
Malformed snapshots stop before any content is changed, including with `--reset`.

An explicit `seed_biglab` restores snapshot-managed fields, ordering and publication
states while preserving unrelated records. Pages use translation identity; snippets
also use translation identity before their natural names, so renamed partners do
not create duplicate entries. Repeated runs do not duplicate pages, media or revisions.

To return the entire editorial site to this baseline after testing:

```powershell
uv run python manage.py seed_biglab --reset
```

This removes added editorial test content. Accounts, passwords, the site's domain,
port and root editor permissions remain. Startup continues to use `--if-changed`,
which applies a changed baseline once and preserves subsequent CMS edits on restarts.

To intentionally replace the committed baseline with future published CMS changes:

```powershell
uv run python manage.py export_biglab_content
uv run python manage.py seed_biglab --check
```

Export only material intended for the repository, including drafts. Source Word/PDF
files are retained for provenance; they are not parsed at application startup.

## Verification

`home/test_supplied_content.py` compares every supplied prose paragraph with the
baseline, checks bilingual records/contacts/visibility and tests timeline date
boundaries and chronological validation. Snapshot tests cover repeat imports,
restoring edited fields, renamed snippets, reset, ID remapping and corrupt input.

Validation on 12 November 2026: all 163 Django tests pass; system checks, migration
drift and whitespace checks pass. All 66 published pages plus six homepage/About
variants (72 routes) render successfully with one H1, unique IDs, existing media
and valid internal destinations/anchors. A repeated seed updates zero pages and
adds no revisions. Live HTTP checks also pass for EN/CS homepages, timeline,
school information and Contact. Browser visual inspection could not be completed
because the browser-control host was unavailable. Local HTTP preview was checked
on port 8010, since port 8000 belongs to another local application.
