import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from html.parser import HTMLParser

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML


ROOT = Path(__file__).resolve().parents[1]


def article(**overrides):
    fields = {
        "title": "Test trip",
        "slug": "person-trip",
        "category": SimpleNamespace(name="findpenguins"),
        "relative_source_path": "articles/person/trip/trip.rst",
        "date": datetime(2026, 1, 1),
        "lang": "fr",
        "content": "",
        "url": "articles/person/trip/trip.html",
    }
    fields.update(overrides)
    return SimpleNamespace(**fields)


class TripTemplateTests(unittest.TestCase):
    def setUp(self):
        self.environment = Environment(
            loader=FileSystemLoader(ROOT / "themes/global/templates"),
            autoescape=select_autoescape(("html",)),
        )

    def render(self, trip, articles):
        return self.environment.get_template("trip.html").render(
            article=trip,
            articles=articles,
            pages=[],
            SITEURL=ROOT.as_uri(),
            SITENAME="Test site",
            DEFAULT_LANG="fr",
            THEME_STATIC_DIR="themes/global/static",
            AUTHOR="Test author",
        )

    def test_country_images_and_names_use_shared_root(self):
        trip = article(countries="Peru, Chile", countryflags="Peru|flags/pe-test.webp;Chile|")
        soup = BeautifulSoup(self.render(trip, [trip]), "html.parser")
        countries = soup.select_one(".trip-country-flags")
        self.assertEqual(countries.img["src"], f"{ROOT.as_uri()}/flags/pe-test.webp")
        self.assertIn("Peru", countries.get_text())
        self.assertIn("Chile", countries.get_text())
        self.assertEqual(len(countries.select("img")), 1)

    def test_missing_optional_metadata_and_no_footprints(self):
        trip = article()
        html = self.render(trip, [trip])
        self.assertIn("Aucune étape disponible.", html)
        self.assertIn("Compagnons de voyage", html)

    def test_itinerary_prefers_satellite_map_and_falls_back_to_trip_map(self):
        trip = article(tripmap="map_trip.webp", tripsatellitemap="satellite_trip.webp")
        html = self.render(trip, [trip])
        self.assertIn(f'src="{ROOT.as_uri()}/articles/person/trip/satellite_trip.webp"', html)
        trip.tripsatellitemap = ""
        html = self.render(trip, [trip])
        self.assertIn(f'src="{ROOT.as_uri()}/articles/person/trip/map_trip.webp"', html)

    def test_companions_are_displayed_in_both_trip_sections(self):
        trip = article(
            owner="Owner",
            companions="Alice|../alice.webp;Bob|https://example.com/bob.webp;Carol|",
        )
        html = self.render(trip, [trip])
        self.assertEqual(html.count('class="trip-companion-list"'), 2)
        for name in ("Alice", "Bob", "Carol"):
            self.assertEqual(html.count(f"<span>{name}</span>"), 2)
        self.assertNotIn("<span>Owner</span>", html)
        self.assertEqual(html.count(f'src="{ROOT.as_uri()}/articles/person/trip/../alice.webp"'), 2)
        self.assertEqual(html.count('src="https://example.com/bob.webp"'), 2)
        self.assertEqual(html.count('class="trip-companion-image"'), 4)

    def test_owner_is_shown_when_companions_are_missing(self):
        trip = article(owner="Owner")
        html = self.render(trip, [trip])
        self.assertEqual(html.count("<span>Owner</span>"), 2)

    def test_footprints_are_sorted_numerically_and_link_to_their_articles(self):
        trip = article()
        footprints = [
            article(
                title=f"Step {number}",
                slug=f"person-trip-etape-{number}",
                category=SimpleNamespace(name="footprint"),
                url=f"articles/person/trip/footprint_{number}/footprint.html",
            )
            for number in (10, 2, 1)
        ]
        unrelated = article(
            title="Another trip",
            slug="person-trip-other-etape-3",
            category=SimpleNamespace(name="footprint"),
        )
        html = self.render(trip, [trip, unrelated, *footprints])
        self.assertLess(html.index(">Step 1</span>"), html.index(">Step 2</span>"))
        self.assertLess(html.index(">Step 2</span>"), html.index(">Step 10</span>"))
        self.assertIn("/articles/person/trip/footprint_10/footprint.html", html)
        self.assertNotIn(">Another trip</span>", html)

    def test_footprints_display_their_step_numbers_inside_links(self):
        trip = article()
        footprints = [
            article(
                title=f"Destination {number}",
                slug=f"person-trip-etape-{number}",
                category=SimpleNamespace(name="footprint"),
                url=f"articles/person/trip/footprint_{number}/footprint.html",
            )
            for number in (10, 2, 1)
        ]

        class ContentsParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.entries = []
                self.link = None

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "a" and "/footprint_" in attrs.get("href", ""):
                    self.link = {"url": attrs["href"], "number": "", "text": ""}
                elif tag == "span" and self.link is not None:
                    self.field = "number" if attrs.get("class") == "trip-toc-number" else "text"

            def handle_data(self, data):
                if self.link is not None and hasattr(self, "field"):
                    self.link[self.field] += data

            def handle_endtag(self, tag):
                if tag == "span" and hasattr(self, "field"):
                    del self.field
                elif tag == "a" and self.link is not None:
                    self.entries.append(self.link)
                    self.link = None

        parser = ContentsParser()
        parser.feed(self.render(trip, [trip, *footprints]))
        self.assertEqual(
            [(entry["number"], entry["text"], entry["url"].rsplit("/", 2)[-2]) for entry in parser.entries],
            [("1", "Destination 1", "footprint_1"), ("2", "Destination 2", "footprint_2"), ("10", "Destination 10", "footprint_10")],
        )

    def test_contents_columns_hold_at_most_twenty_steps(self):
        trip = article()
        for count, expected in ((0, []), (1, [1]), (20, [20]), (21, [20, 1]), (40, [20, 20]), (41, [20, 20, 1])):
            with self.subTest(count=count):
                footprints = [
                    article(
                        title=f"Step {number}",
                        slug=f"person-trip-etape-{number}",
                        category=SimpleNamespace(name="footprint"),
                        url=f"articles/person/trip/footprint_{number}/footprint.html",
                    )
                    for number in range(1, count + 1)
                ]
                soup = BeautifulSoup(self.render(trip, [trip, *footprints]), "html.parser")
                columns = soup.select(".trip-toc-column")
                self.assertEqual([len(column.select("li")) for column in columns], expected)
                entries = soup.select(".trip-toc-column a")
                self.assertEqual([int(entry.select_one(".trip-toc-number").text) for entry in entries], list(range(1, count + 1)))
                self.assertEqual(
                    [entry["href"].rsplit("/", 2)[-2] for entry in entries],
                    [f"footprint_{number}" for number in range(1, count + 1)],
                )

    def test_long_printed_contents_preserves_all_footprint_links(self):
        trip = article()
        footprints = [
            article(
                title=f"Step {number}",
                slug=f"person-trip-etape-{number}",
                category=SimpleNamespace(name="footprint"),
                url=f"articles/person/trip/footprint_{number}/footprint.html",
            )
            for number in range(1, 101)
        ]
        rendered = HTML(string=self.render(trip, [trip, *footprints]), base_url=ROOT.as_uri()).render()
        links = [link for page in rendered.pages for link in page.links if "/footprint_" in link[1]]
        self.assertEqual(len({link[1] for link in links}), 100)

    def test_transport_icons_and_distances(self):
        trip = article(transport=(
            "bus 682 km; flight 581 km; car 233 km; 4x4 560 km; train 86 km; "
            "hiking 21 km; sailing 1 km; walking 1 km; motorboat 11 km; ferry 17 km; "
            "cruise ship 115 km; camper 156 km; bicycle 12 km; train"
        ))
        html = self.render(trip, [trip])
        for detail, icon, value in (
            ("bus 682 km", "bus", "682 km"),
            ("flight 581 km", "plane", "581 km"),
            ("car 233 km", "car", "233 km"),
            ("4x4 560 km", "car-side", "560 km"),
            ("train 86 km", "train", "86 km"),
            ("hiking 21 km", "person-hiking", "21 km"),
            ("sailing 1 km", "sailboat", "1 km"),
            ("walking 1 km", "person-walking", "1 km"),
            ("motorboat 11 km", "ship", "11 km"),
            ("ferry 17 km", "ship", "17 km"),
            ("cruise ship 115 km", "ship", "115 km"),
            ("camper 156 km", "caravan", "156 km"),
            ("bicycle 12 km", "route", "12 km"),
            ("train", "train", "train"),
        ):
            start = html.index(f'<li aria-label="{detail}" title="{detail}">')
            entry = html[start:html.index("</li>", start)]
            self.assertIn(f'class="fa-solid fa-{icon}"', entry)
            self.assertIn(f"<span>{value}</span>", entry)

    def test_contents_starts_on_printed_page_five(self):
        trip = article(owner="Traveller", description="A journey")
        rendered = HTML(string=self.render(trip, [trip]), base_url=ROOT.as_uri()).render()
        self.assertEqual(len(rendered.pages), 6)
        self.assertIn("trip-toc-title", rendered.pages[4].anchors)
        self.assertIn("trip-overview", rendered.pages[5].anchors)


if __name__ == "__main__":
    unittest.main()
