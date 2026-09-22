from datetime import date
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from wagtail.images import get_image_model
from wagtail.models import Locale, Page, Site

from home.home_sections import ensure_home_sections
from home.models import (
    Collaboration,
    ContactSettings,
    ContentPage,
    HomePage,
    NewsIndexPage,
    NewsPage,
    PeopleIndexPage,
    PersonPage,
    ProjectPage,
    ProjectsIndexPage,
    Publication,
    SciencePage,
)


ASSET_DIR = Path(__file__).resolve().parents[2] / "seed_assets"


PEOPLE = [
    {
        "slug": "tibor-zingora",
        "title": "Tibor Žingora",
        "role": "Head of BIG Lab · Social psychologist",
        "image": "tibor-zingora.jpg",
        "profile_url": "https://www.muni.cz/en/people/362589-tibor-zingora",
        "en": (
            "Tibor Žingora, Ph.D. is a social psychologist studying how attitudes and behaviours "
            "emerge, evolve and spread among people. He examines how changes shaped by environments, "
            "relationships and experience translate into broader outcomes such as polarization, the "
            "diffusion of prejudice, or the adoption of health-protective and pro-environmental behaviours. "
            "His work combines psychology, sociology and network science using structural equation modelling, "
            "longitudinal social network analysis and agent-based modelling. Before founding BIG Lab, he worked "
            "at the University of Oxford, the University of Groningen and the Czech Academy of Sciences."
        ),
        "cs": (
            "Tibor Žingora, Ph.D. je sociální psycholog, který se zabývá tím, jak postoje a chování "
            "vznikají, vyvíjejí a šíří mezi lidmi. Zkoumá, jak se změny utvářené prostředím, vztahy a "
            "zkušenostmi promítají do širších jevů, jako je polarizace společnosti, šíření předsudků "
            "nebo přijímání chování podporujícího zdraví a ochranu životního prostředí. Ve své práci "
            "propojuje psychologii, sociologii a síťovou vědu a využívá strukturní modelování, longitudinální "
            "analýzu sociálních sítí a modelování založené na agentech. Před založením BIG Labu působil na "
            "Oxfordské univerzitě, Univerzitě v Groningenu a v Akademii věd ČR."
        ),
        "role_cs": "Vedoucí BIG Labu · sociální psycholog",
    },
    {
        "slug": "utku-caybas",
        "title": "Utku Caybas",
        "role": "Postdoctoral researcher",
        "image": "utku-caybas.jpeg",
        "en": (
            "Utku Caybas, Ph.D. is a postdoctoral researcher at BIG Lab. His research focuses on peer "
            "relations at school—including interactions, relationships and group processes—and their role "
            "in shaping students’ motivational beliefs in STEM. He uses longitudinal social network analysis "
            "and mixed-method designs. Utku completed his Ph.D. in Educational Psychology and Educational "
            "Technology at Michigan State University."
        ),
        "cs": (
            "Utku Caybas, Ph.D. je postdoktorandským výzkumníkem v BIG Labu. Jeho výzkum se zaměřuje "
            "na vrstevnické vztahy ve škole—interakce, vztahy a skupinové procesy—a jejich roli při "
            "utváření motivačních přesvědčení žáků v oblastech STEM. Využívá longitudinální analýzu "
            "sociálních sítí a smíšené metody. Doktorát z pedagogické psychologie a vzdělávacích "
            "technologií získal na Michiganské státní univerzitě."
        ),
        "role_cs": "Postdoktorandský výzkumník",
    },
    {
        "slug": "zhe-dong",
        "title": "Zhe Dong",
        "role": "Postdoctoral researcher",
        "image": "zhe-dong.jpeg",
        "profile_url": "https://www.muni.cz/en/people/529373-zhe-dong",
        "en": (
            "Zhe Dong, Ph.D. is a postdoctoral researcher working on friendship segregation, youth "
            "leadership and social networks. Using social network analysis and structural equation modelling, "
            "she investigates the antecedents and consequences of friendship segregation among adolescents. "
            "In 2026, she received her Ph.D. from the University of Groningen for research on positive and "
            "negative leadership in childhood."
        ),
        "cs": (
            "Zhe Dong, Ph.D. je postdoktorandskou výzkumnicí zabývající se segregací v přátelských "
            "vztazích, vedením mladých lidí a sociálními sítěmi. Pomocí analýzy sociálních sítí a "
            "strukturního modelování zkoumá příčiny a důsledky segregace v přátelských vztazích u "
            "dospívajících. V roce 2026 získala na Univerzitě v Groningenu doktorát zaměřený na pozitivní "
            "a negativní vedení v dětství."
        ),
        "role_cs": "Postdoktorandská výzkumnice",
    },
    {
        "slug": "michaela-krystofova",
        "title": "Michaela Kryštofová",
        "role": "Research assistant",
        "image": "michaela-krystofova.jpg",
        "en": (
            "Bc. Michaela Kryštofová is a research assistant at BIG Lab and a final-year Master’s student "
            "in Psychology preparing for doctoral study in the lab. Her work moves from individual differences "
            "toward questions about how attitudes and behaviours form, change and spread through social networks. "
            "She is particularly interested in bridging quantitative and qualitative methodologies."
        ),
        "cs": (
            "Bc. Michaela Kryštofová je výzkumnou asistentkou v BIG Labu a studentkou posledního ročníku "
            "magisterského studia psychologie, která se připravuje na doktorské studium v laboratoři. "
            "Její práce směřuje od individuálních rozdílů k otázkám, jak se postoje a chování utvářejí, "
            "mění a šíří prostřednictvím sociálních sítí. Zajímá se o propojování kvantitativních a "
            "kvalitativních metod."
        ),
        "role_cs": "Výzkumná asistentka",
    },
    {
        "slug": "olesja-nyjherova",
        "title": "Olesja Nyjherová",
        "role": "Data collection manager",
        "image": "olesja-nyjherova.jpeg",
        "profile_url": "https://www.muni.cz/en/people/581225-olesja-nyjherova",
        "en": (
            "Olesja Nyjherová is an undergraduate psychology student at Masaryk University. Her interests "
            "include psychometrics, research methodology and statistics, as well as developmental psychology. "
            "At BIG Lab, she manages data collection, bringing organization, precision and careful planning "
            "to the team’s fieldwork."
        ),
        "cs": (
            "Olesja Nyjherová je studentkou bakalářského studia psychologie na Masarykově univerzitě. "
            "Její odborné zájmy zahrnují psychometriku, statistiku, metodologii výzkumu a vývojovou "
            "psychologii. V BIG Labu zastává roli manažerky sběru dat, kde uplatňuje svůj smysl pro "
            "organizaci, preciznost a plánování."
        ),
        "role_cs": "Manažerka sběru dat",
    },
    {
        "slug": "ching-ting-ang",
        "title": "Ching Ting Ang",
        "role": "Doctoral researcher",
        "image": "ching-ting-ang.jpg",
        "en": (
            "Ching-Ting Ang, MSc, is a doctoral student whose research focuses on adolescent peer cliques, "
            "including their structural characteristics, developmental consequences and underlying social "
            "processes. She graduated in 2025 from the Erasmus Mundus Joint Master’s Degree in Global MINDs "
            "(Social and Cultural Psychology), delivered by SWPS University, the University of Oslo and the "
            "University of Limerick."
        ),
        "cs": (
            "Ching-Ting Ang, MSc, je doktorskou studentkou, jejíž výzkum se zaměřuje na vrstevnické skupiny "
            "v dospívání, včetně jejich strukturálních charakteristik, dopadů na vývoj a souvisejících "
            "sociálních procesů. V roce 2025 absolvovala společný magisterský program Erasmus Mundus Global "
            "MINDs v sociální a kulturní psychologii."
        ),
        "role_cs": "Doktorská výzkumnice",
    },
]


RESEARCH_AREAS = [
    ("development-and-spread", "Development and spread of attitudes and behaviours", "Vývoj a šíření postojů a chování", "research-attitudes.jpg"),
    ("social-influence", "Social influence", "Sociální vliv", "research-social-influence.jpg"),
    ("group-dynamics", "Intra- and intergroup dynamics", "Vnitroskupinová a meziskupinová dynamika", "research-group-dynamics.jpg"),
    ("segregation-and-prejudice", "Segregation, prejudice and intergroup relations", "Segregace, předsudky a meziskupinové vztahy", "research-segregation.jpg"),
    ("social-networks", "Social networks", "Sociální sítě", "research-networks.jpg"),
]


class Command(BaseCommand):
    help = "Populate the BIG Lab Wagtail site with public source content."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Refresh existing seed-owned fields.")

    def handle(self, *args, **options):
        self.force = options["force"]
        images = self._load_images()
        home = HomePage.objects.get(depth=2, locale__language_code="en")
        self._seed_english(home, images)
        self._seed_czech(home)
        self.stdout.write(self.style.SUCCESS("BIG Lab content is ready."))

    def _load_images(self):
        Image = get_image_model()
        result = {}
        for path in ASSET_DIR.iterdir():
            if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            title = path.stem.replace("-", " ").title()
            image = Image.objects.filter(title=title).first()
            if image is None:
                with path.open("rb") as source:
                    image = Image(title=title, file=File(source, name=path.name))
                    image.save()
            result[path.name] = image
        return result

    def _publish(self, page):
        page.save_revision().publish()
        return page

    def _seed_existing(self, page, *, marker="intro", **fields):
        """Populate a prepared page once, preserving later editor changes."""
        if self.force or not getattr(page, marker, None):
            for key, value in fields.items():
                setattr(page, key, value)
            self._publish(page)
        return page

    def _child(self, parent, model, slug, **fields):
        page = parent.get_children().type(model).filter(slug=slug).specific().first()
        created = page is None
        if page is None:
            page = model(slug=slug, **fields)
            parent.add_child(instance=page)
        needs_seed = created or self.force or not getattr(page, "intro", None)
        if not created and needs_seed:
            for key, value in fields.items():
                setattr(page, key, value)
        if needs_seed or not page.live:
            self._publish(page)
        return page

    def _seed_english(self, home, images):
        self._seed_existing(
            home,
            marker="hero_title",
            title="BIG Lab",
            draft_title="BIG Lab",
            hero_title="How do individual choices become collective change?",
            hero_summary=(
                "We study how attitudes and behaviours form in individuals—and how they spread through "
                "relationships, groups and society."
            ),
            intro=(
                "<p>BIG Lab brings together social psychology, sociology and network science to understand "
                "change at two connected levels: the person and the group.</p>"
            ),
            body=[
                ("heading", "From individual change to social spread"),
                (
                    "text",
                    "<p>Our work examines outcomes including prejudice, substance use, pro-environmental "
                    "behaviour, polarization and conflict. We combine longitudinal social network analysis, "
                    "computational modelling, experiments and real-world interventions.</p>",
                ),
            ],
            search_description="BIG Lab studies how attitudes and behaviours change and spread through social networks and groups.",
        )

        science = home.get_children().type(SciencePage).specific().first()
        self._seed_existing(
            science,
            title="Science",
            draft_title="Science",
            slug="science",
            show_in_menus=True,
            intro="<p>Five connected areas frame our research into individual change and social spread.</p>",
            body=[
                (
                    "text",
                    "<p>We move between individual experience, interpersonal influence and group-level patterns. "
                    "The same question is viewed through experiments, longitudinal network data and computational models.</p>",
                )
            ],
        )
        for slug, title, _, filename in RESEARCH_AREAS:
            self._child(
                science,
                ContentPage,
                slug,
                title=title,
                intro=f"<p>{title} is one of BIG Lab’s five connected research areas.</p>",
                cover_image=images[filename],
                body=[],
                show_in_menus=False,
            )

        team = home.get_children().type(PeopleIndexPage).specific().first()
        self._seed_existing(
            team,
            title="People",
            draft_title="People",
            slug="people",
            show_in_menus=True,
            intro="<p>We are a multidisciplinary team studying behaviour across people, relationships and groups.</p>",
        )
        for person in PEOPLE:
            self._child(
                team,
                PersonPage,
                person["slug"],
                title=person["title"],
                role=person["role"],
                portrait=images[person["image"]],
                profile_url=person.get("profile_url", ""),
                intro=f"<p>{person['en']}</p>",
                body=[],
                show_in_menus=False,
            )

        news_index = home.get_children().type(NewsIndexPage).specific().first()
        self._seed_existing(
            news_index,
            title="News",
            draft_title="News",
            slug="news",
            show_in_menus=True,
            intro="<p>Updates from BIG Lab, our projects and research community.</p>",
        )
        self._child(
            news_index,
            NewsPage,
            "research-meeting-with-satis-lab",
            title="Research meeting with the SATIS lab",
            date=date(2026, 5, 19),
            cover_image=images["satis-meeting.png"],
            intro="<p>Researchers from the SATIS lab joined us to present current work and exchange plans.</p>",
            body=[
                (
                    "text",
                    "<p>Like BIG Lab, SATIS Lab conducts social network analyses within schools. This shared "
                    "focus gave us an opportunity to exchange feedback, compare approaches and brainstorm together.</p>",
                )
            ],
            show_in_menus=False,
        )

        parta = home.get_children().type(ProjectPage).filter(slug="parta").specific().first()
        self._seed_existing(
            parta,
            title="Parta",
            draft_title="Parta",
            is_featured=True,
            show_in_menus=True,
            intro="<p>A dedicated BIG Lab project for students, parents and schools.</p>",
            body=[
                ("heading", "Project information is being prepared"),
                (
                    "text",
                    "<p>This page is ready for the confirmed project overview, audience information, timeline "
                    "and results. BIG Lab will publish those materials here as they become available.</p>",
                ),
            ],
        )
        for slug, title in (
            ("about-the-project", "About the project"),
            ("for-parents", "For parents"),
            ("for-schools", "For schools"),
            ("for-students", "For students"),
            ("timeline", "Timeline"),
            ("results", "Results"),
        ):
            self._child(
                parta,
                ContentPage,
                slug,
                title=title,
                intro="<p>This section is ready for confirmed Parta materials from the BIG Lab team.</p>",
                body=[],
                show_in_menus=True,
            )

        projects = home.get_children().type(ProjectsIndexPage).specific().first()
        self._seed_existing(
            projects,
            title="Projects",
            draft_title="Projects",
            slug="projects",
            show_in_menus=True,
            intro="<p>Current and completed research projects connected to the lab’s work.</p>",
        )
        self._child(
            projects,
            ProjectPage,
            "rethinking-segregation-within-schools",
            title="Rethinking Segregation within Schools",
            start_date=date(2026, 1, 1),
            end_date=date(2030, 12, 31),
            funder="Czech Science Foundation · JUNIOR STAR",
            external_url="https://www.muni.cz/en/research/projects/75245",
            intro="<p>Ways of spreading positive attitudes and behaviours among youth.</p>",
            body=[
                (
                    "text",
                    "<p>Within-school segregation may shape how behaviours diffuse among students. This project "
                    "integrates network science with group-based theories to explain how segregation affects the "
                    "spread of behaviours such as prejudice, and how understanding these mechanisms can improve "
                    "school interventions.</p><p>The research combines longitudinal social network analysis, "
                    "agent-based modelling, secondary and newly collected data, and intervention studies.</p>",
                )
            ],
            is_featured=False,
            show_in_menus=False,
        )
        self._child(
            projects,
            ProjectPage,
            "behavior-dynamics",
            title="Behavior Dynamics: From Individual Change to Social Spread",
            start_date=date(2025, 9, 1),
            end_date=date(2029, 8, 31),
            funder="Masaryk University · Grant Agency of Masaryk University",
            external_url="https://www.muni.cz/en/research/projects/74806",
            intro="<p>Building an interdisciplinary research programme around individual change and social diffusion.</p>",
            body=[
                (
                    "text",
                    "<p>The project connects two dimensions: how attitudes and behaviours change through personal "
                    "experience and environment, and how those changes propagate through interpersonal interaction "
                    "and social networks. It combines social psychology, sociology and computational modelling, "
                    "with a particular focus on segregation, prejudice and polarization.</p>",
                )
            ],
            is_featured=False,
            show_in_menus=False,
        )
        self._child(
            projects,
            ProjectPage,
            "selfharm-screening",
            title="Screening self-harm among older school-age children",
            start_date=date(2013, 1, 1),
            end_date=date(2013, 12, 31),
            funder="Masaryk University · Grant Agency of Masaryk University",
            external_url="https://www.muni.cz/en/research/projects/22035",
            intro="<p>A completed project evaluating psychometric tools for screening self-harm.</p>",
            body=[
                (
                    "text",
                    "<p>The project examined diagnostic questionnaire tools for identifying the occurrence and "
                    "forms of self-harm among older school-age children, together with related psychological and "
                    "social factors. Its findings were intended to support further research and preventive work.</p>",
                )
            ],
            is_featured=False,
            show_in_menus=False,
        )

        self._seed_publications(Locale.objects.get(language_code="en"))
        self._seed_collaborations(Locale.objects.get(language_code="en"))
        site = Site.objects.get(is_default_site=True)
        settings, _ = ContactSettings.objects.get_or_create(site=site)
        if self.force or not settings.address:
            settings.address = "Faculty of Social Studies, Masaryk University\nJoštova 10, 602 00 Brno, Czech Republic"
            settings.linkedin_url = "https://www.linkedin.com/company/inpsy-muni/"
            settings.instagram_url = "https://www.instagram.com/inpsy_muni/"
            settings.facebook_url = "https://www.facebook.com/inpsy.muni"
            settings.save()
        ensure_home_sections(home, force=self.force)

    def _seed_publications(self, locale):
        records = [
            {
                "title": "From Mate to Hate? Prejudice Socialization in Friendship Networks",
                "authors": "Chloe Bracegirdle, Tibor Žingora, Olivia Spiegler",
                "year": 2026,
                "publication_type": "Peer-reviewed scientific article",
                "journal_or_publisher": "American Psychologist",
                "doi_or_url": "https://doi.org/10.1037/amp0001662",
            },
            {
                "title": "Outgroup Friendships and Social Influence in the Development of Adolescent Attitudes Toward Secondary Outgroups",
                "authors": "Tibor Žingora, Chloe Bracegirdle, Tobias H. Stark, Olivia Spiegler",
                "year": 2026,
                "publication_type": "Peer-reviewed scientific article",
                "journal_or_publisher": "Journal of Personality and Social Psychology",
                "doi_or_url": "https://doi.org/10.1037/pspi0000530",
            },
        ]
        for record in records:
            publication, created = Publication.objects.get_or_create(
                locale=locale, title=record["title"], defaults=record
            )
            if self.force and not created:
                for key, value in record.items():
                    setattr(publication, key, value)
                publication.save()

    def _seed_collaborations(self, locale):
        records = [
            ("University of Groningen", "International collaboration", "https://www.rug.nl/", 10),
            ("University of Oxford", "International collaboration", "https://www.ox.ac.uk/", 20),
            ("Utrecht University", "International collaboration", "https://www.uu.nl/en", 30),
            (
                "Brno Lab of Intergroup Processes",
                "Institute of Psychology, Czech Academy of Sciences",
                "https://psu.cas.cz/en/institute/about-the-institute/",
                40,
            ),
        ]
        for name, description, website, order in records:
            collaboration, created = Collaboration.objects.get_or_create(
                locale=locale,
                name=name,
                defaults={"description": description, "website": website, "sort_order": order},
            )
            if self.force and not created:
                collaboration.description = description
                collaboration.website = website
                collaboration.sort_order = order
                collaboration.save()

    def _translation(self, source, locale, **fields):
        created = False
        try:
            translated = source.get_translation(locale).specific
        except ObjectDoesNotExist:
            translated = source.copy_for_translation(locale, copy_parents=True).specific
            created = True
        if translated.alias_of_id:
            translated.alias_of = None
            translated.save(update_fields=["alias_of"])
        if created or self.force or not getattr(translated, "intro", None):
            for key, value in fields.items():
                setattr(translated, key, value)
            return self._publish(translated)
        return translated

    def _seed_czech(self, home):
        cs = Locale.objects.get(language_code="cs")
        home_cs = self._translation(
            home,
            cs,
            title="BIG Lab",
            draft_title="BIG Lab",
            hero_title="Jak se individuální volby mění v kolektivní změnu?",
            hero_summary="Zkoumáme, jak se postoje a chování utvářejí u jednotlivců a jak se šíří vztahy, skupinami a společností.",
            intro="<p>BIG Lab propojuje sociální psychologii, sociologii a síťovou vědu, aby porozuměl změně na dvou propojených úrovních: u člověka a ve skupině.</p>",
            body=[
                ("heading", "Od individuální změny k sociálnímu šíření"),
                (
                    "text",
                    "<p>Zkoumáme jevy včetně předsudků, užívání návykových látek, proenvironmentálního "
                    "chování, polarizace a konfliktu. Kombinujeme longitudinální analýzu sociálních sítí, "
                    "počítačové modelování, experimenty a intervence v reálném prostředí.</p>",
                ),
            ],
            search_description="BIG Lab zkoumá, jak se postoje a chování mění a šíří prostřednictvím sociálních sítí a skupin.",
        )

        source_pages = {page.slug: page.specific for page in home.get_children().live()}
        science = source_pages["science"]
        science_cs = self._translation(
            science,
            cs,
            title="Výzkum",
            draft_title="Výzkum",
            slug="vyzkum",
            show_in_menus=True,
            intro="<p>Pět propojených oblastí rámuje náš výzkum individuální změny a sociálního šíření.</p>",
            body=[("text", "<p>Propojujeme individuální zkušenost, mezilidský vliv a skupinové vzorce prostřednictvím experimentů, longitudinálních síťových dat a počítačových modelů.</p>")],
        )
        for source, (_, _, title_cs, _) in zip(science.get_children().live().specific(), RESEARCH_AREAS):
            self._translation(
                source,
                cs,
                title=title_cs,
                draft_title=title_cs,
                intro=f"<p>{title_cs} je jednou z pěti propojených výzkumných oblastí BIG Labu.</p>",
            )

        team = source_pages["people"]
        team_cs = self._translation(
            team,
            cs,
            title="Lidé",
            draft_title="Lidé",
            slug="lide",
            show_in_menus=True,
            intro="<p>Jsme multidisciplinární tým zkoumající chování napříč lidmi, vztahy a skupinami.</p>",
        )
        source_people = {page.slug: page.specific for page in team.get_children().live()}
        for person in PEOPLE:
            self._translation(
                source_people[person["slug"]],
                cs,
                title=person["title"],
                draft_title=person["title"],
                role=person["role_cs"],
                intro=f"<p>{person['cs']}</p>",
            )

        news = source_pages["news"]
        news_cs = self._translation(
            news,
            cs,
            title="Novinky",
            draft_title="Novinky",
            slug="novinky",
            show_in_menus=True,
            intro="<p>Novinky z BIG Labu, našich projektů a výzkumné komunity.</p>",
        )
        news_item = news.get_children().type(NewsPage).live().specific().first()
        self._translation(
            news_item,
            cs,
            title="Výzkumné setkání s laboratoří SATIS",
            draft_title="Výzkumné setkání s laboratoří SATIS",
            intro="<p>Výzkumníci z laboratoře SATIS nám představili svou současnou práci a společně jsme sdíleli další plány.</p>",
            body=[("text", "<p>Stejně jako BIG Lab provádí SATIS Lab analýzy sociálních sítí ve školách. Společné zaměření nám umožnilo vyměnit si zpětnou vazbu, porovnat přístupy a společně hledat nové otázky.</p>")],
        )

        parta = source_pages["parta"]
        self._translation(
            parta,
            cs,
            title="Parta",
            draft_title="Parta",
            show_in_menus=True,
            intro="<p>Samostatný projekt BIG Labu pro žáky, rodiče a školy.</p>",
            body=[
                ("heading", "Informace o projektu připravujeme"),
                ("text", "<p>Na této stránce zveřejníme potvrzený popis projektu, informace pro jednotlivé skupiny, časovou osu a výsledky, jakmile budou k dispozici.</p>"),
            ],
        )
        parta_sections_cs = {
            "about-the-project": "O projektu",
            "for-parents": "Pro rodiče",
            "for-schools": "Pro školy",
            "for-students": "Pro žáky",
            "timeline": "Časová osa",
            "results": "Výsledky",
        }
        for source in parta.get_children().live().specific():
            self._translation(
                source,
                cs,
                title=parta_sections_cs[source.slug],
                draft_title=parta_sections_cs[source.slug],
                intro="<p>Tato sekce je připravena pro potvrzené materiály projektu Parta od týmu BIG Labu.</p>",
                show_in_menus=True,
            )

        projects = source_pages["projects"]
        self._translation(
            projects,
            cs,
            title="Projekty",
            draft_title="Projekty",
            slug="projekty",
            show_in_menus=True,
            intro="<p>Probíhající a dokončené projekty spojené s výzkumem laboratoře.</p>",
        )
        project_translations = {
            "rethinking-segregation-within-schools": (
                "Přehodnocení segregace ve školách",
                "<p>Způsoby šíření pozitivních postojů a chování mezi mladými lidmi.</p>",
            ),
            "behavior-dynamics": (
                "Dynamika chování: od individuální změny k sociálnímu šíření",
                "<p>Budování interdisciplinárního výzkumného programu zaměřeného na individuální změnu a sociální šíření.</p>",
            ),
            "selfharm-screening": (
                "Screening sebepoškozování u dětí staršího školního věku",
                "<p>Dokončený projekt ověřující psychometrické nástroje pro screening sebepoškozování.</p>",
            ),
        }
        for source in projects.get_children().live().specific():
            title, intro = project_translations[source.slug]
            self._translation(source, cs, title=title, draft_title=title, intro=intro)

        self._seed_publications(cs)
        self._seed_collaborations(cs)
        ensure_home_sections(home_cs, force=self.force)
