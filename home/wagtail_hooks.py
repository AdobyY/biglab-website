from wagtail import hooks
from django.templatetags.static import static
from django.utils.html import format_html


@hooks.register("insert_global_admin_css")
def shared_brand_styles():
    return format_html('<link rel="stylesheet" href="{}">', static("css/admin-brand.css"))


@hooks.register("construct_page_action_menu")
def make_publish_the_primary_page_action(menu_items, request, context):
    """Use Publish as the split button's primary action when it is available."""
    publish_index = next(
        (
            index
            for index, item in enumerate(menu_items)
            if item.name == "action-publish"
        ),
        None,
    )

    if publish_index is not None:
        menu_items.insert(0, menu_items.pop(publish_index))
