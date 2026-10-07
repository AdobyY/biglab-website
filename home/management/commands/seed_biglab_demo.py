"""Create a repeatable, explicitly labelled CMS training collection."""
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import Collection, Page

from home.blocks import CONTENT_BLOCKS, HOME_SECTION_BLOCKS
from home.models import (
    Collaboration, ContentPage, HomePage, InterfaceText, NewsIndexPage, NewsPage,
    PeopleIndexPage, PersonPage, ProjectPage, ProjectsIndexPage, Publication, SciencePage,
)
from home.ui import UI_LABELS

ASSETS = Path(__file__).resolve().parents[2] / "demo_content"
VIDEO = "https://www.youtube.com/watch?v=Ee6teO-RvAw"
SIMULATION = "https://ncase.me/crowds/"


def section(name, **fields):
    block = dict(HOME_SECTION_BLOCKS)[name]
    value = block.get_default()
    for key, raw in {"is_visible": True, "intro": "", "anchor": "", "theme": "paper", **fields}.items():
        if key in block.child_blocks:
            value[key] = block.child_blocks[key].to_python(raw)
    return name, value


def content(name, value):
    return name, dict(CONTENT_BLOCKS)[name].to_python(value)


def validate_page(page):
    """Use the same block validation as the editor, including collection rules."""
    page.full_clean()
    for field in ("body", "sections", "after_body"):
        stream = getattr(page, field)
        setattr(page, field, stream.stream_block.clean(stream))
    used = {"content", "home-sections", f"contents-{page.pk}"}
    used.update(f"section-{pk}" for pk in page.get_children().values_list("pk", flat=True))
    used.update(f"section-title-{pk}" for pk in page.get_children().values_list("pk", flat=True))
    inline = 0
    for item in page.sections:
        anchor = item.value.get("anchor")
        if anchor and anchor in used:
            raise CommandError(f"Duplicate anchor on {page.title}: {anchor}")
        if anchor:
            used.add(anchor)
        if item.block_type == "child_sections" and item.value.get("is_visible"):
            inline += 1
        for key, choices in item.value.items():
            if key.startswith("selected_"):
                for choice in choices or []:
                    if choice and choice.locale_id != page.locale_id:
                        raise CommandError(f"Wrong language in {page.title}: {key}")
                    if choice and key == "selected_areas" and not isinstance(choice.get_parent().specific, SciencePage):
                        raise CommandError("Research areas must be children of Science.")
    if inline > 1:
        raise CommandError("Use only one visible Child pages block per page.")


class Command(BaseCommand):
    help = "Add English/Czech Wagtail training pages, media and snippets. Manual only; preserves existing edits on repeat runs. Undo with seed_biglab --reset."

    def handle(self, *args, **options):
        for name in ("bubble-sort.gif", "editor-guide-uk.txt"):
            if not (ASSETS / name).is_file():
                raise CommandError(f"Missing bundled demo asset: {name}")
        homes = {}
        for code in ("en", "cs"):
            home = HomePage.objects.filter(depth=2, locale__language_code=code).first()
            if not home:
                raise CommandError("Import initial content first: python manage.py seed_biglab")
            homes[code] = home
        images = get_image_model()
        image_ids = []
        sources = [
            ("research-attitudes.jpg", "Research Attitudes"),
            ("research-group-dynamics.jpg", "Research Group Dynamics"),
            ("research-networks.jpg", "Research Networks"),
            ("research-segregation.jpg", "Research Segregation"),
            ("research-social-influence.jpg", "Research Social Influence"),
            ("satis-meeting.png", "Satis Meeting"),
            ("tibor-zingora.jpg", "Tibor Zingora"),
            ("utku-caybas.jpeg", "Utku Caybas"),
            ("zhe-dong.jpeg", "Zhe Dong"),
        ]
        for filename, title in sources:
            # File storage can add a unique suffix during an atomic reset.
            # The baseline's editorial image titles remain stable.
            image = (images.objects.filter(file__endswith="/" + filename).first()
                     or images.objects.filter(title=title).first())
            if not image:
                raise CommandError(f"Initial image missing: {filename}. Run seed_biglab first.")
            image_ids.append(image.pk)
        self.user = get_user_model().objects.filter(is_active=True, is_superuser=True).first()
        self.created = 0
        self.kept = 0
        self.entries = []
        self.new = set()
        self.logical_paths = {home.pk: "" for home in homes.values()}
        with transaction.atomic():
            self.gif = self.asset(images, "Demo · Bubble sort GIF (Swfung8, CC BY-SA 3.0)", "bubble-sort.gif")
            self.document = self.asset(get_document_model(), "Wagtail: навчальна інструкція українською", "editor-guide-uk.txt")
            self.gif.tags.add("cms-demo", "animation")
            self.document.tags.add("cms-demo", "guide")
            for code, home in homes.items():
                self.build(home, code, image_ids)
        self.stdout.write(self.style.SUCCESS(f"Demo ready: {self.created} pages created; {self.kept} existing examples preserved. English: /wagtail-showcase/; Czech: /cs/wagtail-showcase/"))
        self.stdout.write("Edit every example in /admin/. Repeating this command adds missing examples without overwriting your edits.")
        self.stdout.write("Return to the initial content manually: python manage.py seed_biglab --reset")

    def asset(self, model, title, filename):
        obj = model.objects.filter(title=title).first()
        if obj:
            return obj
        obj = model(title=title, collection=Collection.get_first_root_node())
        with (ASSETS / filename).open("rb") as stream:
            obj.file.save(filename, File(stream), save=False)
        obj.save()
        return obj

    def page(self, parent, model, slug, title, intro, *, menu=False, live=True, **fields):
        # Refetch the parent: Treebeard mutates path counters during child creation.
        parent = Page.objects.get(pk=parent.pk).specific
        logical_path=self.key(parent, slug)
        identity=uuid5(NAMESPACE_URL, "biglab-cms-demo/" + logical_path)
        # Identity survives a title/URL change or an editor moving a demo page.
        obj = model.objects.filter(locale=parent.locale,translation_key=identity).first()
        collision = parent.get_children().filter(slug=slug).specific().first()
        if obj is None and collision is not None:
            raise CommandError(f"The demo URL '{slug}' belongs to another page. Rename it or reset the initial content before creating demos.")
        if obj:
            if not isinstance(obj, model) or obj.locale_id != parent.locale_id:
                raise CommandError(f"Demo slug is occupied by a different page type: {slug}")
            self.kept += 1
            self.logical_paths[obj.pk]=logical_path+"/"
            self.entries.append(obj.pk)
            return obj
        if not model.can_create_at(parent):
            raise CommandError(f"Cannot add {model.__name__} under {parent.title}")
        obj = model(title=title, slug=slug, locale=parent.locale, intro=f"<p>{intro}</p>",
                    show_in_menus=menu, live=False,
                    translation_key=identity, **fields)
        parent.add_child(instance=obj)
        self.logical_paths[obj.pk]=logical_path+"/"
        self.new.add(obj.pk)
        self.created += 1
        self.entries.append(obj.pk)
        self.write(obj, live=live)
        return obj

    def key(self, parent, slug):
        # English and Czech demo trees share keys without sharing editorial text.
        relative = self.logical_paths.get(parent.pk,parent.url_path.split("/", 2)[-1])
        return relative + slug

    def write(self, obj, *, body=None, sections=None, after=None, live=True):
        if obj.pk not in self.new:
            return
        # A newly added child updates its parent's tree counters in the DB.
        # Keep editorial values but refresh those counters before publishing.
        obj.refresh_from_db(fields=["path", "depth", "numchild", "url_path"])
        if body is not None:
            obj.body = body
        if sections is not None:
            obj.sections = sections
        if after is not None:
            obj.after_body = after
        validate_page(obj)
        revision = obj.save_revision(user=self.user)
        if live:
            revision.publish(user=self.user)
        obj.refresh_from_db()

    def build(self, home, code, img):
        tr = lambda en, cs: en if code == "en" else cs
        p = lambda en, cs: "<p>" + tr(en, cs) + "</p>"
        A = lambda en, cs, **kw: section("about", title=tr(en, cs), **kw)
        def make(parent, model, slug, en, cs, text_en, text_cs, **kw):
            return self.page(parent, model, slug, tr(en, cs), tr(text_en, text_cs), **kw)
        hub = make(home, ContentPage, "wagtail-showcase", "Wagtail showcase", "Ukázky Wagtail",
                   "A local training collection. Every example can be edited in Wagtail; none describes a new BIG Lab research result.",
                   "Místní výuková kolekce. Každý příklad lze upravit ve Wagtail; nejde o nové výsledky výzkumu BIG Lab.", menu=True)
        layouts = make(hub, ContentPage, "editorial-layouts", "Editorial layouts", "Redakční rozvržení",
                       "Four text-and-image arrangements, readable long-form content and reusable calls to action.", "Čtyři rozvržení textu a obrázků, delší články a opakovaně použitelné výzvy k akci.", menu=True)
        media = make(hub, ContentPage, "media", "Images, motion & interaction", "Obrázky, pohyb a interakce",
                     "Explore galleries, comparison, slideshows, GIF animation, video and an external simulation.", "Vyzkoušejte galerie, porovnání, prezentace, GIF, video a externí simulaci.", menu=True)
        collections = make(hub, ContentPage, "collections", "Content collections", "Kolekce obsahu",
                           "Automatic lists update when records are published. Curated lists let you choose order and quantity.", "Automatické seznamy se aktualizují po publikování. Ruční výběr umožňuje nastavit pořadí a počet.", menu=True)
        guide = make(hub, ContentPage, "editor-guide", "Create, preview, publish", "Vytvořit, zobrazit, publikovat",
                     "Follow the exercises on the demonstration pages before editing the real site.", "Než začnete upravovat skutečný web, vyzkoušejte cvičení na ukázkových stránkách.", menu=True)
        story = make(layouts, ContentPage, "reading", "A page made for reading", "Stránka pro čtení",
                     "Demonstration article: headings, emphasis, lists, photography, a document and links in one reading flow.", "Ukázkový článek: nadpisy, zvýraznění, seznamy, fotografie, dokument a odkazy v jednom textu.", menu=True)
        appearance = make(layouts, ContentPage, "appearance", "Colour, backgrounds & visibility", "Barvy, pozadí a viditelnost",
                          "Content settings control section appearance. Use image backgrounds for short messages rather than long collections.", "Vzhled sekcí řídí nastavení obsahu. Obrázkové pozadí použijte pro krátká sdělení, nikoli pro dlouhé kolekce.")
        gallery = make(media, ContentPage, "gallery", "A photographic collection", "Fotografická kolekce",
                       "Existing BIG Lab library images demonstrate different grid densities and full-screen viewing.", "Obrázky ze stávající knihovny BIG Lab ukazují různé hustoty mřížky a celoobrazovkové zobrazení.", menu=True)
        comparison = make(media, ContentPage, "comparison-slider", "Compare & browse", "Porovnat a procházet",
                          "Two different library images demonstrate the comparison control. This is a layout example, not a before-and-after research claim.", "Dva různé obrázky z knihovny ukazují ovládání porovnání. Jde o rozvržení, nikoli o výsledek výzkumu.", menu=True)
        animation = make(media, ContentPage, "gif-animation", "GIF in the image library", "GIF v knihovně obrázků",
                         "The same image chooser accepts animated GIF files. Animation starts automatically, including in thumbnails.", "Stejný výběr obrázků podporuje animované GIF soubory. Animace se spouští automaticky i v miniaturách.")
        embeds = make(media, ContentPage, "video-simulation", "Watch & explore", "Sledovat a zkoumat",
                      "Prepared external media are embedded by URL. These are teaching examples by their credited creators.", "Připravená externí média se vkládají pomocí URL. Jde o výukové příklady uvedených autorů.")
        library = make(media, ContentPage, "documents-links", "Documents & useful links", "Dokumenty a užitečné odkazy",
                       "Upload a file once, reuse it on multiple pages and give each download a helpful label.", "Nahrajte soubor jednou, použijte ho na více stránkách a přidejte srozumitelný popisek.")
        nav = make(guide, ContentPage, "navigation", "Pages inside pages", "Stránky uvnitř stránek",
                   "A page tree can go beyond the main menu. Breadcrumbs and child-page navigation help readers find deeper content.", "Strom stránek může pokračovat pod hlavní nabídku. Drobečková navigace a seznam podstránek pomáhají najít hlubší obsah.", menu=True)
        deep = make(nav, ContentPage, "workshop", "Demo workshop", "Ukázkový workshop", "A second-level content page with its own child page.", "Podstránka druhé úrovně s vlastní další podstránkou.", menu=True)
        leaf = make(deep, ContentPage, "resources", "Workshop resources", "Materiály workshopu", "A third nested level. Publish parents before their children.", "Třetí vnořená úroveň. Nejprve publikujte rodiče, potom podstránky.", menu=True)
        draft = make(guide, ContentPage, "draft-exercise", "Demo: draft exercise", "Ukázka: cvičná rozpracovaná stránka", "This draft stays private until you publish it.", "Tento koncept zůstává neveřejný, dokud jej nepublikujete.", live=False)
        empty = make(guide, ContentPage, "empty-page", "Demo: a minimal page", "Ukázka: minimální stránka", "Even a page without a cover image or section builder can remain readable.", "I stránka bez úvodního obrázku a sekcí může být dobře čitelná.")
        people = make(home, PeopleIndexPage, "demo-people", "Demo: profile collection", "Ukázka: kolekce profilů", "Training profiles use existing library photographs. They do not add new team members.", "Výukové profily používají stávající fotografie. Nepřidávají nové členy týmu.")
        profiles = []
        formats = [(None, False, "small", "portrait", "cover"), (img[6], True, "small", "square", "cover"), (img[7], True, "large", "original", "contain"), (img[8], True, "standard", "portrait", "cover"), (img[6], False, "standard", "square", "contain")]
        names = [("Without a photograph", "Bez fotografie"), ("A compact square portrait", "Malý čtvercový portrét"), ("The complete photograph", "Celá fotografie"), ("A standard portrait", "Standardní portrét"), ("A deliberately hidden portrait", "Záměrně skrytý portrét")]
        for i, (portrait, shown, size, ratio, fit) in enumerate(formats):
            profile = make(people, PersonPage, f"profile-{i+1}", "Demo: " + names[i][0], "Ukázka: " + names[i][1], "This is a profile-format example, not a new person's biography.", "Toto je ukázka formátu profilu, nikoli životopis nové osoby.", role=tr("CMS layout example", "Ukázka rozvržení CMS"), portrait_id=portrait, show_portrait=shown, portrait_size=size, portrait_format=ratio, portrait_fit=fit, card_summary=p("Edit portrait size, ratio and crop independently. Existing photographs are reused only to demonstrate the controls.", "Velikost, poměr stran a ořez lze upravovat samostatně. Stávající fotografie pouze ukazují možnosti ovládání."))
            profiles.append(profile)
            self.write(profile, body=[content("text", p("The role, short card summary and full biography are separate fields. A profile can contain documents, links and any of the existing page sections.", "Role, krátký text na kartě a celý životopis jsou samostatná pole. Profil může obsahovat dokumenty, odkazy a další sekce."))])
        news = make(home, NewsIndexPage, "demo-news", "Demo: news collection", "Ukázka: novinky", "Example news items are ordered by publication date; unpublished articles are excluded.", "Ukázkové novinky jsou řazeny podle data; nepublikované články se nezobrazují.")
        articles=[]
        for i in range(4):
            title = tr(["Demo: an illustrated news article", "Demo: a text-only update", "Demo: a longer headline showing how a news list handles several lines while preserving the image, date and link", "Demo: an unpublished announcement"][i], ["Ukázka: novinka s obrázkem", "Ukázka: textová aktualita", "Ukázka: delší titulek zobrazující, jak seznam novinek zachází s více řádky při zachování obrázku, data a odkazu", "Ukázka: nepublikované oznámení"][i])
            article = self.page(news, NewsPage, f"article-{i+1}", title, tr("A training article for the CMS, with no new scientific claims.", "Cvičný článek pro CMS bez nových vědeckých tvrzení."), date=f"2020-03-{10+i:02}", cover_image_id=img[5] if i == 0 else img[0] if i == 2 else None, live=i!=3)
            articles.append(article)
            self.write(article, body=[content("heading", tr("Write a clear lead", "Napište srozumitelný úvod")), content("text", p("Start with the useful fact, add context and finish with the reader's next step. This paragraph is sample editorial copy.", "Začněte užitečnou informací, doplňte souvislosti a zakončete dalším krokem pro čtenáře. Tento odstavec je vzorový text.")), content("button", dict(label=tr("Back to all demo news", "Zpět na ukázkové novinky"), page=news.pk, url=""))], live=i!=3)
        projects = make(home, ProjectsIndexPage, "demo-projects", "Demo: project collection", "Ukázka: kolekce projektů", "Dates determine whether a project appears as current or finished. These records are fictional training examples.", "Data určují, zda se projekt zobrazí jako aktuální nebo dokončený. Záznamy jsou smyšlené výukové příklady.")
        project_list=[]
        for i, (slug, en, cs, end) in enumerate([( "open", "Demo: an open-ended project", "Ukázka: projekt bez konce", None), ("current", "Demo: an active project", "Ukázka: aktivní projekt", "2099-12-31"), ("finished", "Demo: a completed project", "Ukázka: dokončený projekt", "2020-12-31")]):
            project=make(projects, ProjectPage, slug, en, cs, "A fictional project used only to demonstrate content structure and date-based lists.", "Smyšlený projekt slouží pouze k ukázce struktury obsahu a seznamů podle data.", start_date="2020-01-01", end_date=end)
            project_list.append(project)
        project=project_list[1]
        project_children=[]
        for slug,en,cs in [("overview","Demo project overview","Přehled ukázkového projektu"),("audiences","Who this page is for","Pro koho je tato stránka"),("timeline","A readable project timeline","Přehledná časová osa"),("results","Results page structure","Struktura stránky s výsledky")]:
            child=make(project,ContentPage,slug,en,cs,"A training section with its own editable page. No actual project results or recruitment details are stated.","Výuková sekce má vlastní upravitelnou stránku. Neuvádí skutečné výsledky ani podmínky náboru.",menu=True)
            project_children.append(child)
            self.write(child,body=[content("heading",tr("A separate page, displayed inline","Samostatná stránka zobrazená uvnitř projektu")),content("text",p("Edit this child page and publish it. Its parent shows the content through Child pages — inline sections. Its anchor is based on the page ID, so renaming the title keeps the link stable.","Upravte a publikujte tuto podstránku. Rodič ji zobrazuje pomocí bloku Child pages — inline sections. Kotva vychází z ID stránky, takže přejmenování nezmění odkaz."))])
        audience=project_children[1]
        for slug,en,cs in [("parents","Demo: information for parents","Ukázka: informace pro rodiče"),("schools","Demo: information for schools","Ukázka: informace pro školy"),("students","Demo: information for students","Ukázka: informace pro žáky")]:
            child=make(audience,ContentPage,slug,en,cs,"This illustrates audience-specific pages, with no actual participant instructions.","Ukázka stránek pro různé skupiny neobsahuje skutečné pokyny pro účastníky.",menu=True)
            self.write(child,body=[content("text",p("Add confirmed audience-specific information here. Keep the parent page concise and put longer guidance on child pages.","Sem patří ověřené informace pro konkrétní skupinu. Rodičovskou stránku ponechte stručnou a delší pokyny umístěte na podstránky."))])
        science=make(home,SciencePage,"demo-science","Demo: research collection","Ukázka: kolekce výzkumu","Research area pages are children of Science. This collection demonstrates the structure without inventing research claims.","Výzkumné oblasti jsou podstránkami Výzkumu. Kolekce ukazuje strukturu bez vymyšlených vědeckých tvrzení.")
        areas=[]
        for i,(en,cs) in enumerate([("Demo: an individual perspective","Ukázka: pohled jednotlivce"),("Demo: relationships and influence","Ukázka: vztahy a vliv"),("Demo: networks and groups","Ukázka: sítě a skupiny")]):
            area=make(science,ContentPage,f"area-{i+1}",en,cs,"An illustrative research-area page. Replace this sample with approved copy before public use.","Ukázková stránka výzkumné oblasti. Před veřejným použitím nahraďte vzor schváleným textem.",cover_image_id=img[i])
            areas.append(area)
            self.write(area,body=[content("text",p("A research area can have a concise introduction, a supporting image and longer explanation. Select this page in a Research areas block to create a curated preview.","Výzkumná oblast může mít stručný úvod, podpůrný obrázek a delší vysvětlení. Vyberte ji v bloku Research areas pro ručně sestavený náhled."))])
        pub, created = Publication.objects.get_or_create(locale=home.locale,title=tr("Demo: a reusable publication record","Ukázka: opakovaně použitelný záznam publikace"),defaults=dict(translation_key=uuid5(NAMESPACE_URL,"biglab-cms-demo/publication"),authors=tr("CMS demonstration, not a research citation","Ukázka CMS, nikoli vědecká citace"),year=2000,publication_type=tr("Training record","Výukový záznam"),journal_or_publisher=tr("No publication claimed","Nejde o skutečnou publikaci")))
        Collaboration.objects.get_or_create(locale=home.locale,name=tr("Demo: a shared collaboration entry","Ukázka: sdílený záznam spolupráce"),defaults=dict(translation_key=uuid5(NAMESPACE_URL,"biglab-cms-demo/collaboration"),description=tr("A reusable CMS training record. It does not announce a partnership.","Opakovaně použitelný výukový záznam CMS. Neoznamuje nové partnerství."),website="https://wagtail.org/",sort_order=999))
        InterfaceText.objects.get_or_create(locale=home.locale,key="read_more",defaults=dict(translation_key=uuid5(NAMESPACE_URL,"biglab-cms-demo/read-more"),text=UI_LABELS[code]["read_more"]))
        self.write(layouts,sections=[section("text_image",title=tr("Text first, photograph alongside","Nejprve text, vedle fotografie"),text=p("Choose Text left, image right. A short introduction and one clear action work well in this layout.","Vyberte Text left, image right. Hodí se stručný úvod a jedna jasná akce."),image=img[5],image_caption=tr("Existing SATIS meeting photograph, reused as a layout example.","Stávající fotografie setkání SATIS jako ukázka rozvržení."),layout="text-left",button_label=tr("Read the example article","Přečíst ukázkový článek"),button_page=story.pk),section("text_image",title=tr("Image first","Nejprve obrázek"),text=p("Reverse the layout for an editorial rhythm. Keep the copy short and the photograph relevant.","Obraťte rozvržení pro redakční rytmus. Text má být krátký a fotografie relevantní."),image=img[1],image_caption=tr("Existing research library image.","Stávající obrázek z knihovny výzkumu."),layout="image-left"),section("text_image",title=tr("A full-width photograph","Fotografie přes celou šířku"),text=p("Use a sufficiently large source photograph for a wide section. This image has a larger original than the small research thumbnails.","Pro širokou sekci použijte dostatečně velký originál. Tato fotografie je větší než drobné obrázky výzkumu."),image=img[5],layout="full-image"),section("text_image",title=tr("Let the text carry the page","Nechte promluvit text"),text=p("Text only is useful for a clear explanation, even when an image is stored in the block. The layout setting determines what is shown.","Text only je vhodné pro jasné vysvětlení, i když je v bloku uložen obrázek. O zobrazení rozhoduje nastavení rozvržení."),image=img[0],layout="text-only",theme="midnight")])
        self.write(story,body=[content("heading",tr("Start with one useful idea","Začněte jednou užitečnou myšlenkou")),content("text",p("<b>Demonstration article.</b> Clear paragraphs help readers follow an idea. <i>Emphasis</i> should be used sparingly. An internal page link follows the chosen page even when its title changes.","<b>Ukázkový článek.</b> Jasné odstavce pomáhají sledovat myšlenku. <i>Zvýraznění</i> používejte střídmě. Interní odkaz sleduje vybranou stránku i po změně názvu.")),content("text",tr("<h3>A useful checklist</h3><ul><li>Use an informative title.</li><li>Write a short lead.</li><li>Give images a meaningful caption.</li></ul><h3>A practical sequence</h3><ol><li>Save a draft.</li><li>Check the preview.</li><li>Publish when ready.</li></ol>","<h3>Užitečný seznam</h3><ul><li>Použijte informativní název.</li><li>Napište krátký úvod.</li><li>Přidejte smysluplný popisek obrázku.</li></ul><h3>Praktický postup</h3><ol><li>Uložte koncept.</li><li>Zkontrolujte náhled.</li><li>Publikujte hotový obsah.</li></ol>")),content("image",dict(image=img[5],caption=tr("Existing BIG Lab photograph. This page demonstrates image captions.","Stávající fotografie BIG Lab. Stránka ukazuje popisky obrázků."))),content("document",dict(document=self.document.pk,label=tr("Download the Ukrainian editor guide","Stáhnout ukrajinský návod pro redaktora"))),content("button",dict(label=tr("Open the editor exercises","Otevřít cvičení pro redaktora"),page=guide.pk,url=""))],after=[content("text",p("Content after the sections is a separate field. Use it for a conclusion or related material.","Content after the sections je samostatné pole. Použijte ho pro závěr nebo související materiály."))])
        self.write(appearance,sections=[A("A quiet paper surface","Klidný papírový povrch",text=p("Cream is suitable for longer reading. This section has no decorative image background.","Krémová je vhodná pro delší čtení. Tato sekce nemá dekorativní obrázkové pozadí."),anchor="paper"),A("A midnight section","Tmavá sekce",text=p("The same editorial block can use the Midnight theme. Check all links and supporting text in Preview.","Stejný redakční blok může používat motiv Midnight. V náhledu zkontrolujte odkazy i doplňující text."),theme="midnight",anchor="midnight"),section("callout",title=tr("One message, one action","Jedno sdělení, jedna akce"),text=p("A short callout provides a deliberate colour change without making the entire article a banner.","Krátká výzva přináší barevnou změnu, aniž by celý článek vypadal jako banner."),theme="coral",button_label=tr("Explore media","Prozkoumat média"),button_page=media.pk,anchor="callout"),section("callout",title=tr("Photography as a short backdrop","Fotografie jako krátké pozadí"),text=p("Use the dark overlay to keep this short message readable. Long inline collections are easier to read on a plain surface.","Tmavé překrytí udržuje krátké sdělení čitelné. Dlouhé vnořené kolekce je lepší číst na jednolitém povrchu."),background_image=img[5],background_overlay="dark",background_position="center",theme="midnight",anchor="backdrop"),A("Demo: hidden section","Ukázka: skrytá sekce",text=p("This remains in the editor but does not appear on the public page.","Toto zůstává v editoru, ale nezobrazuje se na veřejné stránce."),is_visible=False,anchor="hidden-example")])
        self.write(gallery,sections=[section("gallery",title=tr("Three-column gallery with full-screen viewing","Galerie ve třech sloupcích s celoobrazovkovým zobrazením"),intro=p("Open an image, move to the next one and close with Escape. Captions help identify each photograph.","Otevřete obrázek, přejděte na další a zavřete pomocí Escape. Popisky pomáhají rozlišit fotografie."),images=[dict(image=x,caption=tr(f"Library image {i+1}",f"Obrázek z knihovny {i+1}")) for i,x in enumerate(img[:6])],columns="three"),section("gallery",title=tr("A quieter two-column gallery","Klidnější galerie ve dvou sloupcích"),images=[dict(image=img[0],caption=tr("Attitudes library image","Obrázek postojů")),dict(image=img[2],caption=tr("Network library image","Obrázek sítí"))],columns="two",enable_lightbox=False),section("gallery",title=tr("A compact four-column collection","Kompaktní kolekce ve čtyřech sloupcích"),images=[dict(image=x,caption="") for x in img[:4]],columns="four")])
        self.write(comparison,sections=[section("comparison",title=tr("Slide to compare two images","Posunutím porovnejte dva obrázky"),intro=p("Use the divider or focus the control and use the arrow keys. The two photographs are unrelated library examples.","Použijte oddělovač nebo ovladač zaměřte a stiskněte šipky. Fotografie jsou nezávislé ukázky z knihovny."),before_image=img[0],after_image=img[2],before_label=tr("Image A","Obrázek A"),after_label=tr("Image B","Obrázek B"),start_position=45),section("slider",title=tr("Browse at your own pace","Procházejte vlastním tempem"),intro=p("This slider does not start automatically. Use the previous and next controls, or the keyboard arrows.","Tato prezentace se nespouští automaticky. Použijte předchozí a další obrázek nebo klávesové šipky."),images=[dict(image=x,caption=tr(f"Slide {i+1}",f"Snímek {i+1}")) for i,x in enumerate(img[:3])],autoplay=False),section("slider",title=tr("An autoplay example with pause","Ukázka automatického přehrávání s pozastavením"),intro=p("The optional autoplay pauses during interaction. Use Pause to stop it completely.","Volitelné přehrávání se během interakce pozastaví. Tlačítkem Pause ho zastavíte."),images=[dict(image=x,caption="") for x in img[3:5]],autoplay=True,interval=8)])
        gif_credit='<p>Bubble sort animation by Swfung8, updated by Joshua Issac. <a href="https://commons.wikimedia.org/wiki/File:Bubble-sort-example-300px.gif">Wikimedia Commons source</a> · <a href="https://creativecommons.org/licenses/by-sa/3.0/">CC BY-SA 3.0</a>. Original file, unchanged.</p>'
        self.write(animation,body=[content("image",dict(image=self.gif.pk,caption=tr("An animated GIF stored in Wagtail Images. Animation starts automatically.","Animovaný GIF v knihovně Wagtail Images. Animace se spouští automaticky."))),content("text",gif_credit)],sections=[A("Use a GIF wherever a still image is accepted","Použijte GIF místo běžného obrázku",text=p("Upload the GIF in Images and select it with the normal chooser. Animation starts automatically in detail views and gallery thumbnails, without a start button. This small algorithm illustration is a format test rather than hero artwork.","Nahrajte GIF do Images a vyberte ho běžným ovladačem. Animace se spouští automaticky v detailu i v miniaturách galerie, bez tlačítka spuštění. Drobná ilustrace algoritmu slouží k testování formátu."))])
        self.write(embeds,sections=[section("video",title=tr("Wagtail's live-preview tutorial","Návod Wagtail k živému náhledu"),intro=p('A tutorial by the Wagtail team, inserted with a public YouTube URL. <a href="https://wagtail.org/blog/how-to-use-wagtail-live-preview/">Original tutorial</a>.', 'Návod týmu Wagtail vložený pomocí veřejné YouTube URL. <a href="https://wagtail.org/blog/how-to-use-wagtail-live-preview/">Původní návod</a>.'),video=VIDEO,theme="midnight"),section("simulation",title=tr("Explore a human network","Prozkoumejte síť lidí"),description=tr("The Wisdom and/or Madness of Crowds by Nicky Case. External educational example in English; use the start button inside the frame.","The Wisdom and/or Madness of Crowds od Nicky Case. Externí vzdělávací ukázka v angličtině; použijte tlačítko uvnitř rámu."),embed_url=SIMULATION)],after=[content("button",dict(label=tr("Open the simulation on its own site","Otevřít simulaci na původním webu"),page=None,url=SIMULATION))])
        self.write(library,body=[content("document",dict(document=self.document.pk,label=tr("Ukrainian editor guide (.txt)","Ukrajinský návod pro redaktora (.txt)"))),content("text",p("Download labels can differ even when the same document is reused. A prepared PDF or Word file can be uploaded in Documents in the same way.","Popisky stažení se mohou lišit i při použití stejného dokumentu. Připravené PDF nebo Word lze stejně nahrát do Documents.")),content("button",dict(label=tr("Open the layout examples","Otevřít ukázky rozvržení"),page=layouts.pk,url="")),content("button",dict(label=tr("Official Wagtail editor guide","Oficiální návod Wagtail"),page=None,url="https://guide.wagtail.org/en/"))],sections=[A("Video inside an article","Video uvnitř článku",text=p("A Video block is also available in Content before/after the sections, alongside text and images.","Blok Video je dostupný i v Content before/after the sections vedle textu a obrázků."))],after=[content("video",VIDEO)])
        self.write(leaf,body=[content("document",dict(document=self.document.pk,label=tr("Download the workshop example guide","Stáhnout ukázkový návod workshopu"))),content("simulation",dict(title=tr("An interactive block inside an article","Interaktivní blok uvnitř článku"),description=tr("Nicky Case's external teaching example. The same simulation type is also available as a full page section.","Externí výuková ukázka Nicky Case. Stejný typ simulace je dostupný i jako samostatná sekce."),embed_url=SIMULATION)),content("button",dict(label=tr("Open the original simulation","Otevřít původní simulaci"),page=None,url=SIMULATION))])
        self.write(deep,body=[content("text",p("This page deliberately uses the automatic In this section navigation rather than copying its child content inline.","Stránka záměrně používá automatickou navigaci In this section místo vkládání celého obsahu podstránek."))])
        self.write(nav,sections=[section("page_links",title=tr("Two columns of useful pages","Dva sloupce užitečných stránek"),pages=[dict(page=deep.pk,label="",description=tr("Continue into the page tree.","Pokračujte ve stromu stránek.")),dict(page=empty.pk,label="",description=tr("See an intentionally minimal page.","Prohlédněte si záměrně minimální stránku."))],columns="two"),section("page_links",title=tr("An editorial list of links","Redakční seznam odkazů"),pages=[dict(page=x.pk,label="",description="") for x in [story,library,appearance]],columns="list")])
        self.write(people,body=[content("text",p("These five examples test missing, square, full-image, cropped and hidden portraits. A lower carousel threshold makes the next/previous controls visible with a small sample.","Pět příkladů testuje chybějící, čtvercové, celé, ořezané a skryté portréty. Nižší práh karuselu zobrazí ovladače i pro malou kolekci."))],sections=[section("people",title=tr("Profile display options","Možnosti zobrazení profilů"),selected_people=[x.pk for x in profiles],limit=24,enable_carousel=True,carousel_after=3)],after=[content("text",p("This paragraph is placed below the people list using Content after the sections.","Tento odstavec je pod seznamem lidí díky Content after the sections."))])
        self.write(news,sections=[section("news_list",title=tr("All published demo articles","Všechny publikované ukázkové články"))])
        self.write(projects,sections=[section("project_list",title=tr("Current demo projects","Aktuální ukázkové projekty"),status="current"),section("project_list",title=tr("Completed demo projects","Dokončené ukázkové projekty"),status="finished")])
        self.write(project,sections=[section("child_sections",title=tr("Read the project sections","Přečíst sekce projektu"),anchor="project-content")])
        for other in (project_list[0],project_list[2]):
            self.write(other,body=[content("text",p("This page has no published child pages. The optional date fields and a short description are enough for a project entry.","Stránka nemá publikované podstránky. Pro projektový záznam stačí volitelná data a krátký popis."))])
        self.write(science,sections=[section("child_sections",title=tr("Research-area page examples","Ukázky stránek výzkumných oblastí")),section("publications"),section("collaborations")])
        self.write(collections,sections=[section("research",title=tr("A selected research preview","Vybraný náhled výzkumu"),selected_areas=[x.pk for x in reversed(areas)],limit=3,show_images=True),section("people",title=tr("A manually selected team preview","Ručně vybraný náhled profilů"),selected_people=[profiles[1].pk,profiles[0].pk,profiles[3].pk],limit=3,enable_carousel=False,show_roles=False),section("featured_project",project=project.pk,label=tr("Fictional CMS demonstration","Smyšlená ukázka CMS"),theme="coral"),section("updates",title=tr("Choose exactly which updates to show","Vyberte přesně zobrazené aktuality"),selected_news=[articles[1].pk,articles[0].pk,articles[3].pk],news_limit=3,selected_projects=[project_list[2].pk,project.pk],projects_limit=2,selected_publications=[pub.pk],publications_limit=1),section("page_links",title=tr("Open the full demonstration collections","Otevřít úplné ukázkové kolekce"),pages=[dict(page=x.pk,label="",description="") for x in [people,news,projects,science]],columns="two")])
        shared=make(collections,ContentPage,"shared-records","Shared records, funding & contact","Sdílené záznamy, financování a kontakty","Snippets are reused across pages in their language. Contact blocks use the site's actual configured details.","Snippets se používají na více stránkách ve stejné řeči. Kontaktní bloky používají skutečné nastavení webu.")
        self.write(shared,sections=[section("publications",title=tr("Publications from reusable records","Publikace ze sdílených záznamů")),section("collaborations",title=tr("Reusable collaboration entries","Sdílené záznamy spolupráce")),section("project_list",title=tr("All current and finished projects","Všechny aktuální i dokončené projekty"),status="all"),section("news_list"),section("financing",text=p("CMS training note: publish only confirmed funding information. This example deliberately makes no claim about a grant or sponsor.","Výuková poznámka: zveřejňujte pouze ověřené financování. Ukázka záměrně neuvádí grant ani sponzora.")),section("contact",title=tr("The site's configured contacts","Kontakty nastavené na webu"),text=p("This block reads the real site settings. Empty email or phone fields are omitted automatically.","Blok čte skutečné nastavení webu. Prázdný e-mail nebo telefon se nezobrazuje."))])
        self.write(media,sections=[section("page_links",title=tr("Choose a media example","Vyberte ukázku médií"),pages=[dict(page=x.pk,label="",description="") for x in [gallery,comparison,animation,embeds,library]],columns="two"),section("gallery",title=tr("A preview from the image library","Náhled knihovny obrázků"),images=[dict(image=x,caption="") for x in img[:3]],columns="three")])
        self.write(guide,body=[content("heading",tr("Create a page in the right place","Vytvořte stránku na správném místě")),content("text",p("In Pages, open the parent and select Add child page. A Content page can contain more Content pages; Parta can contain Content pages; People, News and Projects each accept their corresponding record type.","V Pages otevřete rodiče a vyberte Add child page. Content page může mít další Content pages; Parta může obsahovat Content pages; Lidé, Novinky a Projekty přijímají příslušný typ záznamu.")),content("heading",tr("Work safely with drafts and revisions","Pracujte s koncepty a verzemi")),content("text",tr("<ol><li>Open Draft exercise and change its introduction.</li><li>Choose Save draft in More actions.</li><li>Use Preview in mobile, tablet and desktop sizes.</li><li>Choose Publish when the content is ready.</li><li>Use History to view or restore an older revision.</li></ol><p>Publishing an independent language version does not translate it. An alias is a linked copy and follows its source until converted into a regular page.</p>","<ol><li>Otevřete cvičný koncept a změňte úvod.</li><li>Vyberte Save draft v More actions.</li><li>Zkontrolujte Preview pro mobil, tablet a počítač.</li><li>Hotový obsah publikujte pomocí Publish.</li><li>V History zobrazte nebo obnovte starší verzi.</li></ol><p>Publikování samostatné jazykové verze ji nepřekládá. Alias je propojená kopie a sleduje svůj zdroj, dokud ho nepřevedete na běžnou stránku.</p>")),content("heading",tr("Understand the section builder","Pochopte sestavování sekcí")),content("text",p("An empty builder uses the page's automatic layout. Adding sections replaces automatic lists, so keep a People, News, Projects or Child pages block when you need that collection. The header and content before/after remain separate. Drag sections to reorder them; turn off Show this section to keep an unpublished section in the editor.","Prázdný editor sekcí používá automatické rozvržení. Přidané sekce nahrazují automatické seznamy, proto ponechte příslušný blok Lidé, Novinky, Projekty nebo Podstránky. Hlavička a obsah před/za sekcemi jsou samostatné. Přetažením změňte pořadí; Show this section skryje blok bez smazání.")),content("heading",tr("Try shared content and translations","Vyzkoušejte sdílený obsah a překlady")),content("text",p("Publications, Collaborations and Interface texts are in Snippets. Each has a language. Image and document libraries are reusable across languages. Use the language switch to open the matching English/Czech demonstration page, then edit each text independently.","Publications, Collaborations a Interface texts jsou ve Snippets. Každý záznam má jazyk. Obrázky a dokumenty lze používat ve více jazycích. Přepínač jazyků otevře odpovídající ukázku v angličtině nebo češtině; texty upravujte samostatně.")),content("document",dict(document=self.document.pk,label=tr("Detailed instructions in Ukrainian","Podrobný návod v ukrajinštině")))],sections=[section("page_links",title=tr("Practice on these examples","Procvičte si tyto příklady"),pages=[dict(page=nav.pk,label="",description=""),dict(page=shared.pk,label="",description=""),dict(page=appearance.pk,label="",description="")],columns="three"),section("callout",title=tr("Ready to reset the training site?","Chcete obnovit výukový web?"),text=p("Run seed_biglab --reset manually to return to the saved initial content. Run seed_biglab_demo again whenever you need these examples. Neither command runs automatically at startup.","Ručně spusťte seed_biglab --reset pro návrat k uloženému počátečnímu obsahu. Příklady znovu vytvoří seed_biglab_demo. Ani jedna z těchto operací se nespouští automaticky při startu."),button_label=tr("Official Wagtail guide","Oficiální návod Wagtail"),button_url="https://guide.wagtail.org/en/")])
        self.write(draft,body=[content("text",p("Draft-only marker: change this paragraph, save a draft, preview it, and publish when ready. This text must not appear on public collection pages before publication.","Značka konceptu: upravte odstavec, uložte koncept, zobrazte náhled a hotovou stránku publikujte. Text se před publikováním nesmí objevit ve veřejných kolekcích."))],live=False)
        self.write(empty)
        # Show the same builder on a child page inside the real Parta tree.
        parta=ProjectPage.objects.child_of(home).filter(slug="parta").first()
        if parta:
            demo=make(parta,ContentPage,"cms-demo","Demo: project subpages","Ukázka: podstránky projektu","An explicit CMS training example inside Parta. Existing confirmed project content and draft audience pages remain separate.","Výslovná výuková ukázka CMS uvnitř Parta. Ověřený obsah i rozpracované stránky pro jednotlivé skupiny zůstávají samostatné.",menu=True)
            for slug,en,cs in [("for-parents","Demo: parent information","Ukázka: informace pro rodiče"),("for-schools","Demo: school information","Ukázka: informace pro školy")]:
                child=make(demo,ContentPage,slug,en,cs,"Illustrative audience structure, not participant instructions.","Ukázková struktura pro různé skupiny, nikoli pokyny účastníkům.",menu=True)
                self.write(child,body=[content("text",p("You can add another Content page here without editing Python or templates. Publish it and it appears in this section's navigation.","Další Content page zde přidáte bez úprav Pythonu nebo šablon. Po publikování se objeví v navigaci této sekce."))])
            self.write(demo,sections=[A("A short introduction","Krátký úvod",text=p("This block belongs to the child page. Its own children are linked below using the normal child-page navigation.","Blok patří této podstránce. Její další podstránky jsou propojeny běžnou navigací."))])
            # Repair only the clearly disposable title shown in the user's screenshot.
            bad=any(s.block_type=="child_sections" and s.value.get("title")=="dsfsdfsdfsd" for s in parta.sections)
            if bad:
                parta=parta.get_latest_revision_as_object()
                parta.refresh_from_db(fields=["path", "depth", "numchild", "url_path"])
                parta.sections=[section("child_sections",anchor="project-sections")]
                validate_page(parta)
                parta.save_revision(user=self.user).publish(user=self.user)
        self.write(hub,sections=[section("text_image",title=tr("Learn by editing real examples","Učte se na skutečných ukázkách"),text=p("Choose a collection below, inspect its public page, then open that page in Wagtail. Every layout here uses existing fields and blocks. These examples are local training material.","Vyberte kolekci, prohlédněte si veřejnou stránku a otevřete ji ve Wagtail. Všechna rozvržení používají stávající pole a bloky. Jde o místní výukový obsah."),image=img[5],image_caption=tr("Existing BIG Lab image library; no new event is claimed.","Stávající knihovna obrázků BIG Lab; nejde o nové oznámení události."),layout="image-left",button_label=tr("Start with the editor guide","Začít návodem pro redaktora"),button_page=guide.pk),section("page_links",title=tr("Explore the CMS in practice","Prozkoumejte CMS v praxi"),pages=[dict(page=x.pk,label="",description=tr(en,cs)) for x,en,cs in [(layouts,"Text, photography and section settings.","Text, fotografie a nastavení sekcí."),(media,"Galleries, slideshows, GIF, video and simulation.","Galerie, prezentace, GIF, video a simulace."),(collections,"Curated previews and automatically updated lists.","Ručně vybrané náhledy a automatické seznamy."),(guide,"Pages, drafts, languages, revisions and reset.","Stránky, koncepty, jazyky, verze a obnova.")]],columns="two"),section("callout",title=tr("Your own pages, without code changes","Vlastní stránky bez změn kódu"),text=p("Create a Content page under this collection or inside Parta. Combine the existing blocks, preview the result and publish it when ready.","Vytvořte Content page v této kolekci nebo uvnitř Parta. Kombinujte stávající bloky, zkontrolujte náhled a hotovou stránku publikujte."),button_label=tr("Explore page nesting","Prozkoumat vnořené stránky"),button_page=nav.pk,theme="midnight")])
        # Every demo includes a direct local CMS link; real website copy is untouched.
        for pk in set(self.entries) & self.new:
            obj=Page.objects.get(pk=pk).specific
            if not obj.live or obj.locale_id != home.locale_id:
                continue
            tail=content("text",p(f'Training example. <a href="/admin/pages/{pk}/edit/">Edit this page in Wagtail</a>.',f'Výuková ukázka. <a href="/admin/pages/{pk}/edit/">Upravit tuto stránku ve Wagtail</a>.'))
            obj.after_body=list((b.block_type,b.value) for b in obj.after_body)+[tail]
            self.write(obj)
