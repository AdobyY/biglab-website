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
- A project may contain ordinary sub-pages, allowing Parta to begin as one page and grow later.

Every editable page has text, image, video, document, button, and prepared-simulation blocks. Publications, collaborations, and site contact details are edited from the Wagtail admin menus.

The homepage has a section builder under **Pages → BIG Lab → Edit → Sections**. Editors can add,
duplicate, remove, hide, and drag sections into a new order. Available sections include editorial
text, text with image, research areas, people, featured project, updates, selected pages, gallery,
image comparison, slider, call to action, video, and a trusted animation/simulation embed. Galleries
may open images in a keyboard-accessible full-screen lightbox. Every section can use a reusable
Wagtail image as its background with a controlled overlay and focal position. The hero remains a stable branded
area and is edited through its two dedicated fields.

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

The `seed_biglab` command uploads the source images and creates the initial English and Czech content
from the previous site. It can be run again safely: missing prepared content is restored, while
editor-written page content and additional pages are preserved. `seed_biglab --force` deliberately
refreshes seed-owned fields and must not be used on a live site without a backup. Imported source
files and their provenance are in `home/seed_assets/`; generated Wagtail renditions stay in `media/`.

## Languages

English and Czech locales are created initially. Administrators can add any Django-supported
language under **Settings → Locales**, then use the page translation action and publish the result.
The language switcher only lists published translations of the current page.

## Production

Copy `.env.example` to a secure environment configuration and replace every placeholder. Django does
not read this file itself; pass the variables through the hosting platform or Docker's `--env-file`.
The production settings require `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, and
`WAGTAILADMIN_BASE_URL` and enable HTTPS redirects, secure cookies, HSTS, and compressed
WhiteNoise delivery for versioned CSS/JavaScript.

SQLite and media must live on persistent storage. Mount one writable directory at `/data` and use:

```env
SQLITE_PATH=/data/db.sqlite3
MEDIA_ROOT=/data/media
```

For a first container deployment, set `SEED_INITIAL_CONTENT=1`. Startup runs migrations and the
repeatable seeder before Gunicorn. It can be changed to `0` after the first successful deployment.
Only one application process should write to the SQLite database; scale vertically rather than by
running multiple containers against the same file. The hosting proxy must expose `MEDIA_ROOT` at
`/media/`; this is intentionally not handled by WhiteNoise because uploaded files are mutable.

## Backups

Create a consistent archive of the live SQLite database and all uploaded media with:

```bash
uv run python manage.py backup_site --output-dir /path/to/backups
```

Copy the resulting `biglab-backup-*.tar.gz` away from the application server. A usable backup must
contain both `db.sqlite3` and `media/`; schedule this command with the hosting provider and test a
restore before launch.

## Content still awaiting confirmation

The Parta page is implemented and editable, but intentionally contains a short holding text rather
than invented project details. Replace it in the CMS when the lab supplies the confirmed overview,
timeline and materials. Contact email and phone can be added under **Settings → Contact settings**.

## Verification

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
