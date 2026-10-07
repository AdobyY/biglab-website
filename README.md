# BIG Lab website

Wagtail CMS website for BIG Lab. Runtime content is stored in SQLite and Wagtail's media directory;
neither belongs in Git.

The repository includes the responsive frontend, editable page and homepage-section models,
source-attributed photos from the previous BIG Lab site, and a repeatable initial-content seeder.

## Local development

```bash
uv run python manage.py migrate
uv run python manage.py seed_biglab
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

The public site is available at `/`, the Czech version at `/cs/`, and the CMS at `/admin/`.

The Wagtail **Promote → Show in menus** option controls the generated header navigation. Top-level
pages appear as primary links; marked child pages appear in accessible nested menus under their
nearest marked parent. A child can only be reached through the menu when its parent is also marked.

## SQLite concurrency

SQLite remains the project database. It is configured in WAL mode with a 20-second busy timeout and
immediate write transactions so Wagtail page saves, live preview, and editing-session updates wait for
one another instead of intermittently raising `database is locked`. Run only one application server
against this file and avoid running migrations or the content seeder while an editor is publishing.

## Editorial structure

- The root page is **About BIG Lab**.
- Add **Science**, **Team**, **News**, **Projects**, or a featured project such as **Parta** beneath it.
- Add people beneath Team, news items beneath News, and projects beneath Projects.
- Science and project subsections appear inline on their owning major page, with anchor links.
  Child records and standalone URLs remain available; hiding the inline collection makes links
  fall back to those standalone pages.

Every editable page has text, image, video, document, button, and prepared-simulation blocks.
Publications and collaborations are snippets; contact details are under **Settings → Contact settings**.
The root’s **About / financing information** field describes the two funded projects documented by
Masaryk University; keep claims source-backed and do not add unconfirmed grants or contact details.

The homepage and content pages have a **Page section builder** in the page editor.
**A nonempty section builder replaces the default content layout and automatic lists; it does not
append to them.** Header introductions remain visible, and existing main content stays stored.
Clear the builder to return to the default layout. Hidden sections remain saved.
The initial homepage is About-first, followed by research, people, Parta and updates, using the
navy / butter-yellow / cream / brick palette. Financing is a separate root-page field and can also
be placed through the financing section. Empty editors, including old revisions, open with visible
editable default containers; deliberately clearing and saving the builder still restores the default layout.

To put text **below the people list**, add blocks to
**Content below the automatic list / sections**, or add a **People** section followed by
**About / editorial text** in the builder.
Do not put that text in the header introduction, which appears above the list.

Editors can **Save draft**, **Preview**, then **Publish** directly; no approval workflow is required.
Saving a draft alone does not change the public site. To remove content temporarily, unpublish it
instead of deleting it. Keep originals and revisions until a backup has been verified.

In the section builder, editors can add,
duplicate, remove, hide, and drag sections into a new order. Available sections include editorial
text, text with image, research areas, people, featured project, updates, selected pages, gallery,
image comparison, slider, call to action, video, and a trusted animation/simulation embed.
Full automatic collections are available for people, research, news, projects, publications,
collaborations, and inline child sections, alongside financing and contact sections. Galleries
may open images in a keyboard-accessible full-screen lightbox. Every section can use a reusable
Wagtail image as its background with a controlled overlay and focal position. The hero remains a stable branded
area with dedicated title, summary, layout (constellation, image, or text-only), and image controls.

For text beneath an individual team photo, open that person's page and edit **Team card caption**.
Profiles remain visible even without a portrait.
Each person page also provides controlled portrait display options: show/hide, small/standard/large,
portrait/square/original ratio, and crop-to-fill/show-whole-image. Images are uploaded once; Wagtail
generates the required renditions for every context.

Data-driven homepage sections support curation without losing automatic updates:

- **People:** optionally choose and drag specific profiles into order, set a maximum, show/hide roles,
  and enable a responsive carousel after a chosen threshold. An empty selection uses the published team.
- **Research:** optionally choose and order specific research pages, or leave the selection empty to
  use the current research tree; image visibility and maximum count remain configurable.
- **Updates:** optionally choose and order news, projects, and publication snippets independently,
  customize their headings and limits, or leave each list empty to show the newest records automatically.

Featured projects, selected-page links, galleries, sliders, and all image lists already use explicit
chooser fields and drag ordering, so editors do not need template changes for those sections.

The `seed_biglab` command synchronizes the committed development snapshot in `home/seed_content/`.
It copies page text (including the hero), sections and their order, both languages, original images,
documents, publications, collaborations, interface labels, contacts and homepage colors. Page/image
IDs are remapped for the destination database. Menu visibility and published/draft states match
development, so a draft Parta child does not appear in production navigation. Unrelated destination
records are retained. Accounts, passwords, permissions, revision history and runtime credentials are
not exported; the destination hostname/port are preserved.

After changing development content, refresh the snapshot, commit it and push:

The snapshot files become public when committed to this public repository, including draft content;
include only material intended for that distribution.

```bash
uv run python manage.py export_biglab_content
# Commit home/seed_content/ together with the relevant source changes, then push.
```

An explicit `python manage.py seed_biglab` replaces the snapshot-managed content with the exported
development version, including restoring blank fields and matching publication states. Container
startup uses `seed_biglab --if-changed`: it applies each new snapshot once, storing its checksum on the
persistent media volume, and preserves later CMS edits across restarts of the same snapshot. To
deliberately reapply it, run the command without `--if-changed`. `--bundle-dir` can select an exported
snapshot; `export_biglab_content --output-dir` can create one outside the default directory.

For manual CMS testing, return all editorial content to that snapshot with:

```bash
python manage.py seed_biglab --reset
```

This resets pages and subpages, drafts, sections, publications, collaborations, interface labels,
images, documents and site design/contact settings. Added test content is removed. Accounts, the
default site's hostname/port and root editor permissions are preserved. The command requires a
single-site installation and cannot be combined with `--if-changed` or `--bootstrap`.
The baseline is the committed `home/seed_content/` snapshot; keep it unchanged while testing.
Run `export_biglab_content` only when intentionally replacing that baseline with new approved content.

When handing the site over to editors, set `SEED_INITIAL_CONTENT=0` in Railway's service variables
and apply the deployment. The container then only migrates the database and starts the server;
content changes in the CMS persist across deployments. Startup never uses `--reset`.

The legacy source initializer remains available as `seed_biglab --bootstrap`; it preserves existing
editor records and is intended only for initial source scaffolding, not development synchronization.
Parta's unfilled audience, timeline, results and contact pages remain editable drafts until real
materials are available. Source image provenance is in `home/seed_assets/`; renditions are generated
on the destination and remain in `media/`.

### Repairing an existing legacy installation

The legacy `--bootstrap` initializer intentionally does not repair already-published scaffolding. For installations
created with the old defaults, first pause editorial work and create and verify a **database + media
backup** using the procedure below. Then inspect the read-only repair report:

```bash
uv run python manage.py upgrade_biglab_content
# Equivalent explicit report-only mode:
uv run python manage.py upgrade_biglab_content --dry-run
# Only after the backup has been verified and the report reviewed:
uv run python manage.py upgrade_biglab_content --apply
```

For Docker, use `docker compose exec app python manage.py upgrade_biglab_content` and add `--apply`
only after taking the maintenance-window backup. The report contains action counts, not personal
information. Default and `--dry-run` modes write nothing. `--apply` publishes recognized repairs
directly, without approval, and is idempotent.

Repairs are deliberately narrow:

- Fill the root mission and first About block only when its known default hero and section headings
  match, its mission fields are blank, and revision history contains no earlier mission content.
  Preserve the page title, section IDs, other sections and editor settings.
- Add the verified funding explanation only on a recognized blank root or a recognized source-backed
  Czech mission, with no existing funding content and no financing-field revision marker. A marker
  is respected even when empty; previously populated or intentionally cleared funding is not restored.
- Unpublish only the six recognized Parta child placeholders whose introductions exactly match the
  old English/Czech holding text and whose body, sections and supporting content are empty. Keep
  the pages, fields and revisions editable; do not delete them or invent contact details.
- Translate Czech homepage section headings and buttons only when they exactly match the old English
  defaults. Translate About paragraphs and root mission content only when they exactly match the
  supplied English source; preserve custom headings, text, settings, order and block IDs. The
  language-neutral `PARTA / BIG LAB` label stays unchanged.
- Repair a recognized legacy Czech featured-Parta chooser pointing at the English holding page only
  when its corresponding live Czech translation exists and has no draft. Do not replace custom
  selections. This prevents an English project introduction from being displayed on the Czech home.
- Translate the Czech Parta introduction only when it exactly matches the old English seed intro,
  and its holding body only when the complete heading/text pair matches the historical seed.
  These fields are checked independently; custom project copy is not replaced.
- Replace another Czech project's body only if its single text block exactly equals the historical
  English seed body. Translate only the known international collaboration snippets with the exact
  old English description; preserve custom descriptions.

Draft/unpublished pages, aliases and pages with unpublished changes are skipped. Custom text and
custom blank sections are not filled. If the report skips something, review it in the CMS rather
than relaxing these guards. Preview both languages after applying and retain the backup.

## Languages

English and Czech locales are created initially. Administrators can add any Django-supported
language under **Settings → Locales**. Page-tree synchronization creates linked language copies
(aliases). Publishing the original also updates and publishes these copies with the original text;
this behaviour is intentional. The editor displays a notice about this before publishing.
For an independent translation, open **Status → Switch locales**, select the language and choose
**Convert this alias into an ordinary page**, then edit and publish it. Existing independent
translations are edited separately. The language switcher lists published language versions,
including aliases; a published alias is not proof that its content has been translated.

The **Editors** group can create, edit and publish pages, manage images/documents, publications,
collaborations, interface texts, translations, contacts and the Version 2 palette. It cannot manage
users or groups. Migration `0018_editor_content_permissions` adds these content permissions to
the existing group without changing membership or removing other permissions.

**Save** on publications, collaborations and interface texts still applies immediately to every
page that displays that record in its language. These shared records have no draft workflow;
their editor displays this explicitly.

Small interface labels are editable through the **Interface texts** snippet (`InterfaceText`): select
the locale and use the same key in every language (for example `people` or `skip_content`). Missing
overrides use built-in labels. Page titles, section headings and body text are edited on the page,
not in the interface-text snippet.

**Česky:** Obsah upravujte v **Stránky**. Neprázdný sestavovač sekcí nahrazuje výchozí rozložení,
původní text nemaže. Text pod týmem vložte do **Content after the lists**, nebo za sekci **People**
přidejte textovou sekci. **Save draft** změny pouze uloží; **Publish** je zveřejní bez schvalování.
Překládat lze jen vybrané stránky. Popisky rozhraní upravujte ve snippetu **Interface texts**.
Sekce Party zveřejněte až po doplnění potvrzených materiálů.

### Moving Parta later without losing content

Use Wagtail’s **Move** action on the existing Parta page to place it beneath Projects; do not delete
and recreate it. Children and revisions move with it, and the homepage stays the site root. Review
both locales and move the corresponding translated page as necessary. A move changes the URL from
`/parta/` to `/projects/parta/`: verify Wagtail’s generated redirects in **Settings → Redirects**, add
any missing old paths, test child URLs and update external links. Homepage page-chooser links use
page IDs and continue to point at the moved page. Do not rerun the initial seeder after restructuring
the page tree: it identifies prepared records by their original location and slug.

## Production

The test deployment runs on Railway using its generated HTTPS domain. A custom domain can be
connected later through the hosting platform.
Generate the runtime application secret locally; optional SMTP credentials are needed only for email.
Django does not load environment files itself; pass variables through the hosting platform or Docker.
Never commit runtime credentials or pass them to `docker build`. `config.settings.build` imports only
base settings and uses a public build-only constant for `collectstatic`; runtime uses production
settings and requires its own real secret. Both use compressed WhiteNoise static storage.
The production settings require `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and
`WAGTAILADMIN_BASE_URL` and enable HTTPS redirects, secure cookies, HSTS, and compressed
WhiteNoise delivery for versioned CSS/JavaScript.

SQLite and media must live on persistent storage. Mount one writable directory at `/data` and use:

```env
SQLITE_PATH=/data/db.sqlite3
MEDIA_ROOT=/data/media
```

Set `SEED_INITIAL_CONTENT=1` to synchronize each new development snapshot during container startup.
Startup runs migrations and `seed_biglab --if-changed` before Gunicorn. Set it to `0` to disable
automatic snapshot updates while retaining the command for explicit runs.
Only one application process should write to the SQLite database; scale vertically rather than by
running multiple containers against the same file. On Railway, the application serves registered
raster Wagtail renditions at `/media/images/`; documents, originals and arbitrary uploads are not
exposed by this endpoint. This is separate from WhiteNoise static-file delivery. Set
`SERVE_PUBLIC_IMAGE_RENDITIONS=0` when a dedicated proxy serves these images instead.

### Railway

Deploy the repository's `main` branch with the Dockerfile and attach a volume at `/data`.
Set the required production variables above to the generated Railway hostname and HTTPS URL.
Railway supplies `PORT`; the entrypoint binds Gunicorn to it. At startup the entrypoint makes the
mounted directory writable, then switches to the `wagtail` user before migrations, optional
seeding and serving requests. Image builds use the isolated build settings and need no runtime secret.

### Example: Docker Compose with Caddy HTTPS

The repository’s `compose.yaml` runs one Gunicorn worker with two threads, persistent SQLite/media,
and Caddy on ports 80/443. The application port is not published. Only Caddy may supply trusted
forwarded HTTPS headers. Caddy automatically requests/renews certificates once DNS points to the
server and ports 80/443 are reachable. Do not run multiple app replicas against SQLite.
Caddy serves `/media/images/` from the read-only shared volume (originals and Wagtail renditions).
Documents remain behind Wagtail’s document-serving URLs/access checks, not an unrestricted media
file server; arbitrary uploaded files must not become executable public HTML.

Example Linux host installation (paths below are examples, not commands already run):

1. Place the checkout in `/srv/biglab`. Install Docker Engine and the Compose plugin.
2. Point the domain’s A/AAAA records at the host; allow ports 80 and 443.
3. Create a private `/etc/biglab-runtime.env` containing `DJANGO_SECRET_KEY=<locally generated random secret>`
   and `SEED_INITIAL_CONTENT=0`. Set it to owner-only permissions. Generate a secret with
   `python -c "import secrets; print(secrets.token_urlsafe(64))"` and store it securely.
4. Create `/etc/biglab-deploy.env` with `DOMAIN=your-registered-hostname` (no scheme or path).
   For an interactive shell set `export DOMAIN=your-registered-hostname` as well. Compose refuses
   to start without it; no real hostname is hardcoded.
5. Create `/srv/biglab/backups`, writable by the image’s `wagtail` user. Determine its numeric ID with
   `docker compose run --rm --no-deps app id`, then set ownership accordingly; do not use mode 777.
6. Run `docker compose build`, then `docker compose up -d`. Startup performs migrations. On an
   existing installation, take a backup and stop editors before this step. For a genuinely new
   installation only, run `docker compose exec app python manage.py seed_biglab` once.
7. Run `docker compose exec app python manage.py createsuperuser`. In **Settings → Sites**, set
   hostname to the real domain, port 443 and root to BIG Lab; do not create a replacement root page.
8. Run `docker compose exec app python manage.py check --deploy`. Verify HTTPS, admin login,
   CSRF-protected publishing, English/Czech URLs, uploaded images, document links and redirects.

Keep `/etc/biglab-runtime.env` outside the checkout and Docker build context, with owner-only
permissions. Never copy it into the repository or image. Keep backups outside the checkout as well.

## Backups

The command uses SQLite’s online backup API for a consistent database snapshot. Media is copied
separately: for a consistent **database + media** archive, pause publishing/uploads and stop the app
while running it in a one-off container. For local development with no active editors:

```bash
uv run python manage.py backup_site --output-dir /path/to/backups
```

For the Compose deployment:

```bash
docker compose stop app
docker compose run --rm --no-deps app python manage.py backup_site --output-dir /backups
docker compose start app
```

Always restart the app even if the backup fails. Archives contain `db.sqlite3`, `media/` (when media
exists) and `manifest.json`. Treat the database archive as sensitive: it contains CMS account data.

For Linux/systemd automation, copy `deploy/biglab-backup.service` and `deploy/biglab-backup.timer`
to `/etc/systemd/system/`, run `systemctl daemon-reload`, then
`systemctl enable --now biglab-backup.timer`. These examples assume `/srv/biglab`, Docker at
`/usr/bin/docker`, and `DOMAIN` in `/etc/biglab-deploy.env`; adapt them to the host. The service pauses
the app, writes to the host backup directory and restarts it even on failure. Monitor with
`systemctl status biglab-backup.service` and `journalctl -u biglab-backup.service`. Backups introduce
a short overnight maintenance window.

**Offsite step (not automated):** copy each successful archive to independent storage, for example
an encrypted backup bucket or another machine using `scp`. Keep multiple dated copies; verify their
checksums after transfer. The same server, Docker volume or attached disk is not an offsite backup.
Set a retention policy only after confirming a restore; keep an offsite copy before deleting old files.

### Restore and verify

1. Test in an isolated staging installation first, using the same application version as the archive.
   Inspect `tar -tzf /path/to/biglab-backup-YYYYMMDDTHHMMSSZ.tar.gz` and `manifest.json`. Extract only
   trusted archives into an empty directory, not over a running installation.
2. Stop the app (`docker compose stop app`) and take a safety backup of the current installation.
   Never use `docker compose down -v`, which destroys persistent volumes.
3. Restore `db.sqlite3` and the entire `media/` directory into the mounted `/data` volume using an
   administrator-controlled restore container or hosting storage tools. Replace the old media
   directory rather than merging it. With all writers stopped, remove old `db.sqlite3-wal` and
   `db.sqlite3-shm` sidecars before replacing the database; never delete sidecars on a live database.
   Restore ownership/read-write access for the container’s `wagtail` user. Do not restore over Caddy’s
   certificate data. Restored archives need no `seed_biglab` run.
4. Before starting the app, use `sqlite3 /path/to/restored/db.sqlite3 'PRAGMA integrity_check;'` on the
   restored file; require `ok`. Compare media file counts with the manifest and spot-check originals
   and documents. Keep the untouched source archive until verification succeeds.
5. Start the app (`docker compose start app`). Check login, page revisions, draft/live state, both
   languages, image renditions, PDF downloads and Parta links. If deploying a newer code version,
   run migrations only after the original-version restore is verified. Record the restore date and
   result, and repeat this exercise periodically.

## Shared logo

Change **Settings → Contact settings → Logo** once to update the website
header, footer, browser icon, admin sidebar, login screens and editor userbar in
both languages. The supplied BIG Lab image is also the default when this field
is empty. Upload replacements through the existing Wagtail image chooser.

## Content still awaiting confirmation

The Parta page is implemented and editable, but intentionally contains a short holding text rather
than invented project details. Replace it in the CMS when the lab supplies the confirmed overview,
timeline and materials. Contact email and phone can be added under **Settings → Contact settings**.

## Verification

Internal pages share tree-based breadcrumbs in both languages and published-sibling navigation.
Science/project child sections use a sticky desktop contents rail with compact illustrations and
native anchor links; the mobile layout stacks. These defaults also apply to the child-sections builder.
Team and News omit redundant default section headings while retaining editor-supplied custom titles.
Portrait size, format, fitting, visibility, section order, and content remain editable in Wagtail.

```bash
uv run python manage.py test
uv run python manage.py check
DJANGO_SETTINGS_MODULE=config.settings.production \
DJANGO_SECRET_KEY='replace-with-a-long-random-secret-value' \
DJANGO_ALLOWED_HOSTS='example.org' \
DJANGO_CSRF_TRUSTED_ORIGINS='https://example.org' \
WAGTAILADMIN_BASE_URL='https://example.org' \
uv run python manage.py check --deploy
```
