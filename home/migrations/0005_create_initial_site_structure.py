from django.db import migrations


def create_initial_site_structure(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    HomePage = apps.get_model("home", "HomePage")
    SciencePage = apps.get_model("home", "SciencePage")
    PeopleIndexPage = apps.get_model("home", "PeopleIndexPage")
    NewsIndexPage = apps.get_model("home", "NewsIndexPage")
    ProjectsIndexPage = apps.get_model("home", "ProjectsIndexPage")
    ProjectPage = apps.get_model("home", "ProjectPage")

    homepage = HomePage.objects.filter(depth=2).first()
    if homepage is None:
        return

    pages = (
        (SciencePage, "Science", "science", True),
        (ProjectPage, "Parta", "parta", True),
        (ProjectsIndexPage, "Projects", "projects", True),
        (NewsIndexPage, "News", "news", True),
        (PeopleIndexPage, "Team", "team", False),
    )
    Page = apps.get_model("wagtailcore", "Page")
    children = Page.objects.filter(
        depth=homepage.depth + 1, path__startswith=homepage.path
    ).order_by("path")
    existing_slugs = set(children.values_list("slug", flat=True))
    last_child = children.last()
    next_path_number = int(last_child.path[-4:]) + 1 if last_child else 1

    for model, title, slug, show_in_menus in pages:
        if slug not in existing_slugs:
            content_type, _ = ContentType.objects.get_or_create(
                app_label="home", model=model._meta.model_name
            )
            model.objects.create(
                title=title,
                draft_title=title,
                slug=slug,
                content_type=content_type,
                path=f"{homepage.path}{next_path_number:04d}",
                depth=homepage.depth + 1,
                numchild=0,
                url_path=f"{homepage.url_path}{slug}/",
                locale=homepage.locale,
                show_in_menus=show_in_menus,
            )
            next_path_number += 1
            homepage.numchild += 1
    homepage.save(update_fields=["numchild"])


class Migration(migrations.Migration):
    dependencies = [("home", "0004_add_czech_locale_and_site_settings")]

    operations = [migrations.RunPython(create_initial_site_structure, migrations.RunPython.noop)]
