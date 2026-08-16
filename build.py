#!/usr/bin/env python3
"""Собирает статические страницы из src/. Запуск: python3 build.py."""

import json
import os
import pathlib


ROOT = pathlib.Path(__file__).parent
OUTPUT_ROOT = pathlib.Path(os.environ.get("SITE_OUTPUT_ROOT", ROOT)).resolve()
BASE_URL = "https://dovnaravwork.github.io/stelki-tula/"

FONTS = (ROOT / "src/fonts-local.css").read_text(encoding="utf-8")
BASE_STYLES = (ROOT / "src/styles.css").read_text(encoding="utf-8")
APP_JS = (ROOT / "src/app.js").read_text(encoding="utf-8")


def render_page(
    *,
    title: str,
    description: str,
    canonical_url: str,
    og_image_url: str,
    page_html: str,
    styles: str,
    jsonld: dict,
    asset_prefix: str = "",
) -> str:
    fonts = FONTS.replace("url(fonts/", f"url({asset_prefix}fonts/")
    structured_data = json.dumps(jsonld, ensure_ascii=False, indent=2)

    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical_url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical_url}">
<meta property="og:image" content="{og_image_url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#F3F5F2">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0D1719">
<link rel="icon" href="{asset_prefix}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{asset_prefix}apple-touch-icon.png">
<link rel="preload" href="{asset_prefix}fonts/piazzolla-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{asset_prefix}fonts/golostext-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">
{structured_data}
</script>
<style>
{fonts}
{BASE_STYLES}
{styles}</style>
<noscript><style>.reveal {{ opacity: 1 !important; transform: none !important; }}</style></noscript>
</head>
<body>
{page_html}
<script>
{APP_JS}</script>
</body>
</html>
'''


def write_page(path: pathlib.Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    relative_path = path.relative_to(OUTPUT_ROOT)
    print(
        f"{relative_path}: {len(html.splitlines())} lines, "
        f"{len(html.encode()) / 1024:.0f} KB"
    )


insole_title = "Индивидуальные бескаркасные стельки в Туле — от 3 000 ₽"
insole_description = (
    "Индивидуальные бескаркасные стельки в Туле: осмотр стопы, "
    "термоформирование, подгонка под обувь и одна бесплатная коррекция "
    "в течение 3 месяцев. Изготовление — от 3 000 ₽."
)
insole_jsonld = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": "Индивидуальные ортопедические стельки — мастер Олег Ефимов",
    "description": insole_description,
    "url": BASE_URL,
    "priceRange": "от 3 000 ₽",
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "Тула",
        "addressCountry": "RU",
    },
    "sameAs": [
        "https://t.me/Ol_Kim_E",
        "https://vk.ru/olegevgenievih",
    ],
    "makesOffer": {
        "@type": "Offer",
        "name": "Изготовление одной пары индивидуальных бескаркасных стелек",
        "price": "3000",
        "priceCurrency": "RUB",
        "description": (
            "Осмотр стоп и нижних конечностей, изготовление одной пары "
            "и одна бесплатная коррекция в течение 3 месяцев."
        ),
    },
}
insole_html = render_page(
    title=insole_title,
    description=insole_description,
    canonical_url=BASE_URL,
    og_image_url=f"{BASE_URL}og.png",
    page_html=(ROOT / "src/page.html").read_text(encoding="utf-8"),
    styles="",
    jsonld=insole_jsonld,
)
write_page(OUTPUT_ROOT / "index.html", insole_html)


rehab_url = f"{BASE_URL}reabilitaciya/"
rehab_title = "Физическая реабилитация в Туле — Олег Ефимов"
rehab_description = (
    "Индивидуальные занятия по физической реабилитации в Туле после травм "
    "и операций, при ограничении движений и хронической боли. ЛФК, массаж, "
    "суставные мобилизации, кинезиотейпирование и аренда Артромота."
)
rehab_jsonld = {
    "@context": "https://schema.org",
    "@type": "Service",
    "name": "Индивидуальная физическая реабилитация",
    "description": rehab_description,
    "url": rehab_url,
    "serviceType": "Физическая реабилитация",
    "areaServed": {"@type": "City", "name": "Тула"},
    "provider": {
        "@type": "Person",
        "name": "Олег Ефимов",
        "sameAs": [
            "https://t.me/Ol_Kim_E",
            "https://vk.ru/olegevgenievih",
        ],
    },
}
rehab_html = render_page(
    title=rehab_title,
    description=rehab_description,
    canonical_url=rehab_url,
    og_image_url=f"{BASE_URL}assets/oleg-efimov.jpg",
    page_html=(ROOT / "src/rehabilitation.html").read_text(encoding="utf-8"),
    styles=(ROOT / "src/rehabilitation.css").read_text(encoding="utf-8"),
    jsonld=rehab_jsonld,
    asset_prefix="../",
)
write_page(OUTPUT_ROOT / "reabilitaciya/index.html", rehab_html)


sitemap = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{BASE_URL}</loc>
    <lastmod>2026-08-16</lastmod>
  </url>
  <url>
    <loc>{rehab_url}</loc>
    <lastmod>2026-08-16</lastmod>
  </url>
</urlset>
'''
(OUTPUT_ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
