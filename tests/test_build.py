import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REHAB_PAGE = ROOT / "reabilitaciya" / "index.html"


class SiteBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, "build.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_build_creates_rehabilitation_landing_page(self) -> None:
        self.assertTrue(REHAB_PAGE.exists())

        html = REHAB_PAGE.read_text(encoding="utf-8")
        self.assertIn("Восстановление после травм и операций", html)
        self.assertIn("Олег Ефимов", html)
        self.assertIn("5,0", html)
        self.assertIn("9 отзывов", html)
        self.assertIn('href="../"', html)
        self.assertIn("https://t.me/Ol_Kim_E", html)

    def test_rehabilitation_page_uses_root_relative_shared_assets(self) -> None:
        html = REHAB_PAGE.read_text(encoding="utf-8")
        self.assertIn('href="../fonts/piazzolla-cyrillic.woff2"', html)
        self.assertIn('src="../assets/oleg-efimov.jpg"', html)
        self.assertNotIn("src=\"../foto/1.", html)

    def test_sitemap_contains_both_service_pages(self) -> None:
        sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(
            "https://dovnaravwork.github.io/stelki-tula/</loc>", sitemap
        )
        self.assertIn(
            "https://dovnaravwork.github.io/stelki-tula/reabilitaciya/</loc>",
            sitemap,
        )

    def test_rehabilitation_credentials_have_accessible_links(self) -> None:
        html = REHAB_PAGE.read_text(encoding="utf-8")
        self.assertEqual(html.count('class="credential-link"'), 4)
        self.assertEqual(html.count("Открыть документ"), 4)
        self.assertIn("520 часов", html)
        self.assertIn("506 часов", html)

    def test_artromot_rental_is_paired_with_the_avito_review(self) -> None:
        html = REHAB_PAGE.read_text(encoding="utf-8")
        section_start = html.index('id="artromot"')
        section_end = html.index("</section>", section_start)
        section = html[section_start:section_end]

        self.assertIn("Аренда Артромота", section)
        self.assertIn("для разработки коленного сустава", section)
        self.assertIn("всё показал, объяснил, подписали договор", section)
        self.assertIn("Роман", section)
        self.assertIn("Отзыв с Авито", section)


if __name__ == "__main__":
    unittest.main()
