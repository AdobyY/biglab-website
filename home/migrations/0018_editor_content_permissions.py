"""Grant the existing Editors role content permissions, without account administration."""
from django.db import migrations


def grant_editor_permissions(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    GroupPagePermission = apps.get_model("wagtailcore", "GroupPagePermission")
    group, _ = Group.objects.get_or_create(name="Editors")

    def permission(app_label, model, action, codename=None):
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model=model)
        code = codename or f"{action}_{model}"
        permission, _ = Permission.objects.get_or_create(
            content_type=content_type, codename=code,
            defaults={"name": f"Can {action} {model}"},
        )
        return permission

    for model in ("publication", "collaboration", "interfacetext"):
        for action in ("view", "add", "change", "delete"):
            group.permissions.add(permission("home", model, action))
    for model in ("contactsettings", "homepagedesignsettings"):
        for action in ("view", "change"):
            group.permissions.add(permission("home", model, action))
    for app_label, model in (("wagtailimages", "image"), ("wagtaildocs", "document")):
        for action in ("view", "add", "change", "delete"):
            group.permissions.add(permission(app_label, model, action))
    group.permissions.add(permission("simple_translation", "simpletranslation", "submit", "submit_translation"))
    root = Page.objects.filter(depth=1).first()
    if root:
        for action in ("add", "change", "publish", "lock"):
            GroupPagePermission.objects.get_or_create(
                group=group, page=root, permission=permission("wagtailcore", "page", action),
            )

    Collection = apps.get_model("wagtailcore", "Collection")
    GroupCollectionPermission = apps.get_model("wagtailcore", "GroupCollectionPermission")
    collection = Collection.objects.filter(depth=1).first()
    if collection:
        for app_label, model in (("wagtailimages", "image"), ("wagtaildocs", "document")):
            for action in ("add", "change", "choose"):
                GroupCollectionPermission.objects.get_or_create(
                    group=group, collection=collection, permission=permission(app_label, model, action),
                )


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0017_admin_editorial_clarity"),
        ("simple_translation", "0001_initial"),
        ("wagtaildocs", "0014_alter_document_file_size"),
    ]
    operations = [migrations.RunPython(grant_editor_permissions, migrations.RunPython.noop)]
