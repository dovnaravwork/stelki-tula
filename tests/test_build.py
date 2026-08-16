import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://dovnaravwork.github.io/stelki-tula/"


class SiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids = set()
        self.references = []
        self.canonical = None
        self.og_url = None
        self.jsonld = []
        self._jsonld_chunks = None

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(attributes["id"])

        for attribute in ("href", "src"):
            if attributes.get(attribute):
                self.references.append(attributes[attribute])

        if tag == "link" and "canonical" in attributes.get("rel", "").split():
            self.canonical = attributes.get("href")
        if tag == "meta" and attributes.get("property") == "og:url":
            self.og_url = attributes.get("content")
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self._jsonld_chunks = []

    def handle_data(self, data: str) -> None:
        if self._jsonld_chunks is not None:
            self._jsonld_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._jsonld_chunks is not None:
            self.jsonld.append(json.loads("".join(self._jsonld_chunks)))
            self._jsonld_chunks = None


def parse_page(path: Path) -> SiteHTMLParser:
    parser = SiteHTMLParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def contrast_ratio(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        channels = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class SiteBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.output_root = Path(cls._temporary_directory.name)
        environment = os.environ.copy()
        environment["SITE_OUTPUT_ROOT"] = str(cls.output_root)
        subprocess.run(
            [sys.executable, "build.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        cls.home_page = cls.output_root / "index.html"
        cls.rehab_page = cls.output_root / "reabilitaciya" / "index.html"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_build_creates_rehabilitation_landing_page(self) -> None:
        self.assertTrue(self.rehab_page.exists())

        html = self.rehab_page.read_text(encoding="utf-8")
        self.assertIn("Восстановление после травм и операций", html)
        self.assertIn("Олег Ефимов", html)
        self.assertIn("5,0", html)
        self.assertIn("9 отзывов", html)
        self.assertIn('href="../"', html)
        self.assertIn("https://t.me/Ol_Kim_E", html)

    def test_insole_page_presents_current_offer_and_real_work_photos(self) -> None:
        html = self.home_page.read_text(encoding="utf-8")

        self.assertIn("Бескаркасные стельки", html)
        self.assertIn("от 3 000 ₽", html)
        self.assertIn("1 бесплатная коррекция", html)
        self.assertIn("в течение 3 месяцев", html)
        self.assertEqual(html.count('class="work-photo"'), 3)
        self.assertIn('alt="Индивидуальные стельки на стопах, вид спереди"', html)
        self.assertIn('alt="Стельки с индивидуальными корректирующими элементами"', html)
        self.assertIn('alt="Посадка индивидуальной стельки, вид сбоку"', html)
        self.assertIn("assets/certificate-lower-limb-insoles.webp", html)
        self.assertNotIn("Здесь появятся фотографии", html)

    def test_generated_files_match_committed_github_pages_outputs(self) -> None:
        for relative_path in (
            Path("index.html"),
            Path("reabilitaciya/index.html"),
            Path("sitemap.xml"),
        ):
            self.assertEqual(
                (self.output_root / relative_path).read_bytes(),
                (ROOT / relative_path).read_bytes(),
                f"Run python3 build.py and commit {relative_path}",
            )

    def test_all_local_page_references_and_fragments_resolve(self) -> None:
        for generated_page in (self.home_page, self.rehab_page):
            relative_page = generated_page.relative_to(self.output_root)
            production_page = ROOT / relative_page
            html = generated_page.read_text(encoding="utf-8")
            parser = parse_page(generated_page)
            references = parser.references + re.findall(
                r"url\((?:[\"']?)([^)\"']+)", html
            )

            for reference in references:
                parsed = urlparse(reference)
                if parsed.scheme in ("http", "https", "data"):
                    continue
                if reference.startswith("#"):
                    self.assertIn(reference[1:], parser.ids)
                    continue

                target = (production_page.parent / parsed.path).resolve()
                try:
                    target.relative_to(ROOT)
                except ValueError:
                    self.fail(f"Reference escapes site root: {relative_page} -> {reference}")
                if target.is_dir():
                    target = target / "index.html"
                self.assertTrue(
                    target.exists(),
                    f"Broken local reference: {relative_page} -> {reference}",
                )

    def test_rehabilitation_metadata_uses_exact_page_url(self) -> None:
        parser = parse_page(self.rehab_page)
        expected_url = f"{SITE_URL}reabilitaciya/"
        self.assertEqual(parser.canonical, expected_url)
        self.assertEqual(parser.og_url, expected_url)
        self.assertEqual(len(parser.jsonld), 1)
        self.assertEqual(parser.jsonld[0]["url"], expected_url)
        self.assertEqual(parser.jsonld[0]["provider"]["name"], "Олег Ефимов")

    def test_sitemap_contains_exact_service_urls(self) -> None:
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        tree = ET.parse(self.output_root / "sitemap.xml")
        locations = [
            element.text for element in tree.findall("s:url/s:loc", namespace)
        ]
        self.assertEqual(
            locations,
            [SITE_URL, f"{SITE_URL}reabilitaciya/"],
        )

    def test_rehabilitation_credentials_have_accessible_links(self) -> None:
        html = self.rehab_page.read_text(encoding="utf-8")
        self.assertEqual(html.count('class="credential-link"'), 4)
        self.assertEqual(html.count("Открыть документ"), 4)
        self.assertIn("520 часов", html)
        self.assertIn("506 часов", html)

    def test_rehabilitation_document_previews_are_not_cropped(self) -> None:
        css = (ROOT / "src/rehabilitation.css").read_text(encoding="utf-8")
        document_image_rule = re.search(
            r"\.credential-link\s*>\s*img\s*\{(?P<body>.*?)\}",
            css,
            re.DOTALL,
        )

        self.assertIsNotNone(document_image_rule)
        self.assertRegex(document_image_rule.group("body"), r"object-fit:\s*contain\s*;")

    def test_insole_credential_preview_is_not_cropped(self) -> None:
        css = (ROOT / "src/styles.css").read_text(encoding="utf-8")
        document_image_rule = re.search(
            r"\.insole-credential\s*>\s*img\s*\{(?P<body>.*?)\}",
            css,
            re.DOTALL,
        )

        self.assertIsNotNone(document_image_rule)
        self.assertRegex(document_image_rule.group("body"), r"object-fit:\s*contain\s*;")

    def test_insole_gallery_has_an_intentional_featured_composition(self) -> None:
        html = self.home_page.read_text(encoding="utf-8")
        css = (ROOT / "src/styles.css").read_text(encoding="utf-8")
        feature_rule = re.search(
            r"\.work-card--feature\s*\{(?P<body>.*?)\}",
            css,
            re.DOTALL,
        )

        self.assertEqual(
            html.count('class="work-card work-card--feature reveal"'),
            1,
        )
        self.assertIsNotNone(feature_rule)
        self.assertRegex(feature_rule.group("body"), r"grid-row:\s*span\s+2\s*;")

    def test_rehabilitation_documents_use_preview_above_description(self) -> None:
        css = (ROOT / "src/rehabilitation.css").read_text(encoding="utf-8")
        credential_rule = re.search(
            r"\.credential-link\s*\{(?P<body>.*?)\}",
            css,
            re.DOTALL,
        )

        self.assertIsNotNone(credential_rule)
        self.assertRegex(
            credential_rule.group("body"),
            r"grid-template-rows:\s*minmax\([^;]+\)\s+1fr\s*;",
        )

    def test_artromot_rental_is_paired_with_the_avito_review(self) -> None:
        html = self.rehab_page.read_text(encoding="utf-8")
        section_start = html.index('id="artromot"')
        section_end = html.index("</section>", section_start)
        section = html[section_start:section_end]

        self.assertIn("Аренда Артромота", section)
        self.assertIn("для разработки коленного сустава", section)
        self.assertIn("всё показал, объяснил, подписали договор", section)
        self.assertIn("Роман", section)
        self.assertIn("Отзыв с Авито", section)

    def test_small_text_and_panel_focus_meet_contrast_thresholds(self) -> None:
        css = (ROOT / "src/styles.css").read_text(encoding="utf-8")
        root_tokens = re.search(r":root\s*\{(.*?)\}", css, re.DOTALL)
        self.assertIsNotNone(root_tokens)
        colors = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", root_tokens.group(1)))

        self.assertGreaterEqual(contrast_ratio(colors["faint"], colors["paper"]), 4.5)
        self.assertGreaterEqual(
            contrast_ratio(colors["panel-focus"], colors["panel"]), 3.0
        )
        self.assertIn(".artromot-section :focus-visible", css)
        self.assertIn(".contact-panel :focus-visible", css)


if __name__ == "__main__":
    unittest.main()
