#!/usr/bin/env python3
"""Собирает index.html из src/. Запуск: python3 build.py"""
import pathlib

ROOT = pathlib.Path(__file__).parent
SITE_URL = 'https://dovnaravwork.github.io/stelki-tula/'
TITLE = 'Индивидуальные ортопедические стельки в Туле — изготовление по стопе'
DESCRIPTION = ('Индивидуальные ортопедические стельки в Туле: диагностика стопы, '
               'формовка по вашей стопе, подгонка под обувь и коррекция после носки. '
               'Запись у мастера в Telegram.')

fonts = (ROOT / 'src/fonts-local.css').read_text()
styles = (ROOT / 'src/styles.css').read_text()
page = (ROOT / 'src/page.html').read_text()
js = (ROOT / 'src/app.js').read_text()

jsonld = f'''{{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Индивидуальные ортопедические стельки — мастер Олег",
  "description": "{DESCRIPTION}",
  "url": "{SITE_URL}",
  "address": {{
    "@type": "PostalAddress",
    "addressLocality": "Тула",
    "addressCountry": "RU"
  }},
  "sameAs": [
    "https://t.me/Ol_Kim_E",
    "https://vk.ru/olegevgenievih"
  ]
}}'''

html = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<link rel="canonical" href="{SITE_URL}">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:url" content="{SITE_URL}">
<meta property="og:image" content="{SITE_URL}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#F3F5F2">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#0D1719">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="preload" href="fonts/piazzolla-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="fonts/golostext-cyrillic.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">
{jsonld}
</script>
<style>
{fonts}
{styles}</style>
<noscript><style>.reveal {{ opacity: 1 !important; transform: none !important; }}</style></noscript>
</head>
<body>
{page}
<script>
{js}</script>
</body>
</html>
'''

(ROOT / 'index.html').write_text(html)
print(f'index.html: {len(html.splitlines())} lines, {len(html.encode()) / 1024:.0f} KB')
