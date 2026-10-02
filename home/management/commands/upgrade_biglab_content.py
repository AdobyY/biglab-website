"""Opt-in repairs for exact, previously shipped BIG Lab scaffolding."""

import json
from contextlib import nullcontext
from copy import deepcopy

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import transaction

from home.home_sections import default_home_sections
from home.management.commands.seed_biglab import FINANCING, PROJECT_BODIES_CS
from home.models import Collaboration, ContentPage, HomePage, ProjectPage


MISSION = {
    "en": {
        "hero_title": "How do individual choices become collective change?",
        "hero_summary": "We study how attitudes and behaviours form in individuals—and how they spread through relationships, groups and society.",
        "heading": "From individual change to social spread",
        "intro": "<p>BIG Lab brings together social psychology, sociology and network science to understand change at two connected levels: the person and the group.</p>",
        "text": "<p>Our work examines outcomes including prejudice, substance use, pro-environmental behaviour, polarization and conflict. We combine longitudinal social network analysis, computational modelling, experiments and real-world interventions.</p>",
    },
    "cs": {
        "hero_title": "Jak se individuální volby mění v kolektivní změnu?",
        "hero_summary": "Zkoumáme, jak se postoje a chování utvářejí u jednotlivců a jak se šíří vztahy, skupinami a společností.",
        "heading": "Od individuální změny k sociálnímu šíření",
        "intro": "<p>BIG Lab propojuje sociální psychologii, sociologii a síťovou vědu, aby porozuměl změně na dvou propojených úrovních: u člověka a ve skupině.</p>",
        "text": "<p>Zkoumáme jevy včetně předsudků, užívání návykových látek, proenvironmentálního chování, polarizace a konfliktu. Kombinujeme longitudinální analýzu sociálních sítí, počítačové modelování, experimenty a intervence v reálném prostředí.</p>",
    },
}

SECTION_LABELS_EN = {
    "about": {"title": MISSION["en"]["heading"], "intro": MISSION["en"]["intro"], "text": MISSION["en"]["text"]},
    "research": {"title": "Research areas", "link_label": "All science"},
    "people": {"title": "People behind the research", "link_label": "Full team"},
    "featured_project": {"label": "PARTA / BIG LAB", "button_label": "About the project"},
    "updates": {"title": "In progress"},
}
PARTA_INTRO = {
    "en": "<p>A dedicated BIG Lab project for students, parents and schools.</p>",
    "cs": "<p>Samostatný projekt BIG Labu pro žáky, rodiče a školy.</p>",
}
PARTA_BODY = {
    "en": [
        ("heading", "Project information is being prepared"),
        ("text", "<p>This page is ready for the confirmed project overview, audience information, timeline and results. BIG Lab will publish those materials here as they become available.</p>"),
    ],
    "cs": [
        ("heading", "Informace o projektu připravujeme"),
        ("text", "<p>Na této stránce zveřejníme potvrzený popis projektu, informace pro jednotlivé skupiny, časovou osu a výsledky, jakmile budou k dispozici.</p>"),
    ],
}

# Exact historical bodies, not the current English translation (which editors may change).
PROJECT_BODIES_EN = {
    "rethinking-segregation-within-schools": (
        "<p>Within-school segregation may shape how behaviours diffuse among students. This project "
        "integrates network science with group-based theories to explain how segregation affects the "
        "spread of behaviours such as prejudice, and how understanding these mechanisms can improve "
        "school interventions.</p><p>The research combines longitudinal social network analysis, "
        "agent-based modelling, secondary and newly collected data, and intervention studies.</p>"
    ),
    "behavior-dynamics": (
        "<p>The project connects two dimensions: how attitudes and behaviours change through personal "
        "experience and environment, and how those changes propagate through interpersonal interaction "
        "and social networks. It combines social psychology, sociology and computational modelling, "
        "with a particular focus on segregation, prejudice and polarization.</p>"
    ),
    "selfharm-screening": (
        "<p>The project examined diagnostic questionnaire tools for identifying the occurrence and "
        "forms of self-harm among older school-age children, together with related psychological and "
        "social factors. Its findings were intended to support further research and preventive work.</p>"
    ),
}

PLACEHOLDER_INTROS = {
    "en": "<p>This section is ready for confirmed Parta materials from the BIG Lab team.</p>",
    "cs": "<p>Tato sekce je připravena pro potvrzené materiály projektu Parta od týmu BIG Labu.</p>",
}
PARTA_SLUGS = {
    "about-the-project", "for-parents", "for-schools", "for-students", "timeline", "results",
}
INTERNATIONAL_PARTNERS = {"University of Groningen", "University of Oxford", "Utrecht University"}


def published_without_draft(page):
    return page.live and not page.has_unpublished_changes and not page.alias_of_id


def recognized_empty_home(home):
    language = home.locale.language_code
    if language not in MISSION or not published_without_draft(home):
        return False
    titles = {"About BIG Lab", MISSION[language]["hero_title"]}
    headings = {MISSION[language]["heading"]}
    if language == "cs":
        titles.add("O BIG Lab")
        headings.add(MISSION["en"]["heading"])
    if home.hero_title not in titles or home.hero_summary or home.intro or home.body:
        return False
    if not home.sections or home.sections[0].block_type != "about":
        return False
    about = home.sections[0].value
    if (
        about.get("title") not in headings or about.get("anchor") != "about"
        or about.get("is_visible") is False or str(about.get("intro", ""))
        or str(about.get("text", ""))
    ):
        return False
    # Clearing previously supplied/editor-written content is not an untouched scaffold.
    for content in home.revisions.values_list("content", flat=True):
        # Wagtail's revision serializer stores StreamFields as JSON strings.
        body = content.get("body") or []
        sections = content.get("sections") or []
        try:
            if isinstance(body, str):
                body = json.loads(body)
            if isinstance(sections, str):
                sections = json.loads(sections)
        except (TypeError, ValueError):
            return False
        if content.get("intro") or body or content.get("hero_summary"):
            return False
        if not isinstance(sections, list):
            return False
        if sections and sections[0].get("type") == "about":
            previous = sections[0].get("value", {})
            if previous.get("intro") or previous.get("text"):
                return False
    return True


class Command(BaseCommand):
    help = "Dry-run exact legacy scaffold repairs; take a backup before opting in with --apply."

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="Publish matched repairs and unpublish exact Parta placeholders.")
        mode.add_argument("--dry-run", action="store_true", help="Report counts only (the default); write nothing.")

    def handle(self, *args, **options):
        apply = options["apply"]
        counts = dict(
            home_mission=0, home_financing=0, czech_home_section_fields=0,
            czech_home_mission_fields=0, czech_featured_project_links=0,
            czech_parta_intro=0, czech_parta_body=0,
            parta_placeholders=0, czech_project_bodies=0, czech_collaborations=0,
        )
        # Serialize opt-in writes with editor writes on the configured SQLite database.
        with transaction.atomic() if apply else nullcontext():
            for home in HomePage.objects.filter(depth=2).select_related("locale"):
                language = home.locale.language_code
                if language not in MISSION or not published_without_draft(home):
                    continue
                mission = MISSION[language]
                empty_scaffold = recognized_empty_home(home)
                changes = {}
                field = home._meta.get_field("sections")
                sections = deepcopy(field.get_prep_value(home.sections))
                sections_changed = False
                if empty_scaffold:
                    counts["home_mission"] += 1
                    changes.update(
                        hero_title=mission["hero_title"], hero_summary=mission["hero_summary"],
                        intro=mission["intro"], body=[("heading", mission["heading"]), ("text", mission["text"])],
                    )
                    sections[0]["value"].update(intro=mission["intro"], text=mission["text"])
                    sections_changed = True

                if language == "cs":
                    defaults = dict(default_home_sections(home))
                    defaults["about"].update(title=mission["heading"], intro=mission["intro"], text=mission["text"])
                    for section in sections:
                        value = section["value"]
                        if (
                            section["type"] == "featured_project"
                            and value.get("anchor") == "featured-project"
                            and value.get("label") == "PARTA / BIG LAB"
                            and value.get("button_label") in {"About the project", "O projektu"}
                        ):
                            source = ProjectPage.objects.filter(
                                pk=value.get("project"), slug="parta", locale__language_code="en",
                            ).first()
                            if (
                                source is not None and published_without_draft(source)
                                and str(source.intro) == PARTA_INTRO["en"]
                                and [(block.block_type, str(block.value)) for block in source.body] == PARTA_BODY["en"]
                            ):
                                try:
                                    translated = source.get_translation(home.locale).specific
                                except ObjectDoesNotExist:
                                    translated = None
                                if translated is not None and published_without_draft(translated):
                                    value["project"] = translated.pk
                                    counts["czech_featured_project_links"] += 1
                                    sections_changed = True
                        for key, english in SECTION_LABELS_EN.get(section["type"], {}).items():
                            czech = defaults[section["type"]][key]
                            if section["value"].get(key) == english and czech != english:
                                section["value"][key] = czech
                                counts["czech_home_section_fields"] += 1
                                sections_changed = True
                    if str(home.intro) == MISSION["en"]["intro"]:
                        changes["intro"] = mission["intro"]
                        counts["czech_home_mission_fields"] += 1
                    if [(block.block_type, str(block.value)) for block in home.body] == [
                        ("heading", MISSION["en"]["heading"]), ("text", MISSION["en"]["text"]),
                    ]:
                        body_field = home._meta.get_field("body")
                        body = deepcopy(body_field.get_prep_value(home.body))
                        body[0]["value"], body[1]["value"] = mission["heading"], mission["text"]
                        changes["body"] = body_field.to_python(body)
                        counts["czech_home_mission_fields"] += 1

                # A populated Czech mission may predate the funding field too. A field
                # marker (even empty) or any earlier funding text still forbids refilling.
                source_mission = (
                    language == "cs" and home.hero_title in {"About BIG Lab", "O BIG Lab", mission["hero_title"], MISSION["en"]["hero_title"]}
                    and home.hero_summary in {"", mission["hero_summary"], MISSION["en"]["hero_summary"]}
                    and str(home.intro) in {mission["intro"], MISSION["en"]["intro"]}
                    and bool(sections) and sections[0]["type"] == "about"
                    and sections[0]["value"].get("title") in {mission["heading"], MISSION["en"]["heading"]}
                )
                financing = (
                    (empty_scaffold or source_mission)
                    and hasattr(home, "about_financing") and not home.about_financing
                    and not home.revisions.filter(content__has_key="about_financing").exists()
                )
                if financing:
                    changes["about_financing"] = FINANCING[language]
                    counts["home_financing"] += 1
                if sections_changed:
                    changes["sections"] = field.to_python(sections)
                if apply and changes:
                    for key, value in changes.items():
                        setattr(home, key, value)
                    home.save_revision().publish()

            for parta in ProjectPage.objects.filter(slug="parta", locale__language_code__in=PLACEHOLDER_INTROS).select_related("locale"):
                if parta.locale.language_code == "cs" and published_without_draft(parta):
                    changes = {}
                    if str(parta.intro) == PARTA_INTRO["en"]:
                        changes["intro"] = PARTA_INTRO["cs"]
                        counts["czech_parta_intro"] += 1
                    if [(block.block_type, str(block.value)) for block in parta.body] == PARTA_BODY["en"]:
                        body_field = parta._meta.get_field("body")
                        body = deepcopy(body_field.get_prep_value(parta.body))
                        for block, (_, text) in zip(body, PARTA_BODY["cs"]):
                            block["value"] = text
                        changes["body"] = body_field.to_python(body)
                        counts["czech_parta_body"] += 1
                    if apply and changes:
                        for key, value in changes.items():
                            setattr(parta, key, value)
                        parta.save_revision().publish()
                for child in ContentPage.objects.child_of(parta).filter(slug__in=PARTA_SLUGS):
                    if (
                        published_without_draft(child)
                        and str(child.intro) == PLACEHOLDER_INTROS[parta.locale.language_code]
                        and not child.body and not child.after_body and not child.sections
                    ):
                        counts["parta_placeholders"] += 1
                        if apply:
                            child.unpublish()

            for project in ProjectPage.objects.filter(locale__language_code="cs", slug__in=PROJECT_BODIES_EN):
                if not published_without_draft(project):
                    continue
                if (
                    len(project.body) == 1 and project.body[0].block_type == "text"
                    and str(project.body[0].value) == PROJECT_BODIES_EN[project.slug]
                ):
                    counts["czech_project_bodies"] += 1
                    if apply:
                        field = project._meta.get_field("body")
                        body = deepcopy(field.get_prep_value(project.body))
                        body[0]["value"] = PROJECT_BODIES_CS[project.slug]
                        project.body = field.to_python(body)
                        project.save_revision().publish()

            collaborators = Collaboration.objects.filter(
                locale__language_code="cs", name__in=INTERNATIONAL_PARTNERS,
                description="International collaboration",
            )
            counts["czech_collaborations"] = collaborators.count()
            if apply:
                collaborators.update(description="Mezinárodní spolupráce")

        self.stdout.write("Applied repairs:" if apply else "Dry run (no writes; use --apply after backup):")
        for action, count in counts.items():
            self.stdout.write(f"{action}: {count}")
        self.stdout.write(f"total_actions: {sum(counts.values())}")
