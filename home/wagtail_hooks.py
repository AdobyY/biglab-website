from wagtail import hooks


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
