"""Conversion shared by migration 0027 and the version 1 content snapshot reader."""
import json
from uuid import UUID, uuid5


SUPPLIED_CONTACT = UUID("22c77423-4ea1-5da8-863e-0d01e6896114")
OLD_TAGLINES = ("Behaviour, interactions and groups", "Chování, interakce a skupiny")
ENGLISH_TAGLINE = "behavior of individuals and groups"


def about_sections(raw):
    blocks = json.loads(raw) if isinstance(raw, str) else raw
    funding = [block for block in blocks if block["type"] == "financing"]
    slot = next((block for block in funding if block["value"].get("is_visible", True)), funding[0] if funding else None)
    result = []
    for block in blocks:
        if block is slot:
            result.append({**block, "type": "topic_network", "value": {
                "anchor": block["value"].get("anchor", ""), "is_visible": block["value"].get("is_visible", True),
            }})
        elif block["type"] not in {"financing", "contact"}:
            result.append(block)
    return json.dumps(result, ensure_ascii=False) if isinstance(raw, str) else result


def standalone_contact(sections, fallback_visible, translation_key, language):
    contacts = [block for block in sections if block["type"] == "contact"]
    visible = any(block["value"].get("is_visible", True) for block in contacts) if contacts else fallback_visible
    if not contacts:
        contacts = [{"type": "contact", "id": str(uuid5(translation_key, language)), "value": {
            "anchor": "contact", "is_visible": True, "show_email": True, "show_phone": True,
            "show_address": True, "show_people_link": True, "show_social_links": True,
        }}]
    title = "Kontakt" if language == "cs" else "Contact"
    return {"title": title, "draft_title": title, "slug": "contact", "show_in_menus": True, "sections": contacts}, visible


def upgrade_snapshot(data):
    pages = data["pages"]
    homes = [page for page in pages if page["model"] == "home.homepage"]
    families = {}
    for home in homes:
        families.setdefault(home["translation_key"], []).append(home)
    next_id = max(page["id"] for page in pages) + 1
    for home_key, translations in families.items():
        parents = {home["id"] for home in translations}
        children = [page for page in pages if page["parent"] in parents]
        keys = {page["translation_key"] for page in children if page["fields"]["slug"] in {"contact", "kontakt"}}
        keys.add(str(SUPPLIED_CONTACT))
        contacts = {page["parent"]: page for page in children if page["translation_key"] in keys}
        contact_key = next((UUID(page["translation_key"]) for page in contacts.values()), uuid5(UUID(home_key), "contact"))
        for home in translations:
            fields = home["fields"]
            fallback = fields.pop("show_contact_section", True)
            if home["id"] in contacts:
                contacts[home["id"]]["fields"]["show_in_menus"] = True
            else:
                contact, live = standalone_contact(fields["sections"], fallback, contact_key, home["locale"])
                pages.append({"model": "home.contentpage", "id": next_id, "fields": contact,
                              "parent": home["id"], "locale": home["locale"], "translation_key": str(contact_key), "live": live})
                next_id += 1
            fields["sections"] = about_sections(fields["sections"])
    for item in data["settings"]:
        if item["model"] == "home.contactsettings" and item["fields"].get("tagline") in OLD_TAGLINES:
            item["fields"]["tagline"] = ENGLISH_TAGLINE
    for item in data["snippets"]:
        fields = item["fields"]
        if item["model"] == "home.interfacetext" and fields["key"] == "footer_tagline" and fields["text"] in OLD_TAGLINES:
            fields["text"] = ENGLISH_TAGLINE
    data["version"] = 2
