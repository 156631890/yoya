from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


WS_ENDPOINT = "ws://127.0.0.1:9333/devtools/browser/80ba6e03-94ba-4e95-a52e-69e9ebd378c7"
STORE_URL = "https://mcduii.en.alibaba.com/"
OUTPUT = Path(__file__).with_name("mcduii_products.json")


def norm_url(url: str) -> str:
    return url.split("?")[0].rstrip("/")


def dedupe(seq: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in seq:
      if item not in seen:
        seen.add(item)
        out.append(item)
    return out


def first_text(items: list[str]) -> str:
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip()
        if cleaned:
            return cleaned
    return ""


def scrape_product(page, url: str) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(3000)
    data = page.evaluate(
        """() => {
          const clean = (s) => (s || '').replace(/\\s+/g, ' ').trim();
          const title = clean(document.querySelector('h1')?.innerText);
          const body = clean(document.body.innerText);
          const priceCandidates = [...document.querySelectorAll('body *')]
            .map(el => clean(el.innerText))
            .filter(t => /^\\$\\d/.test(t) || /^US\\$\\d/.test(t))
            .slice(0, 20);
          const minOrder = body.match(/Min\\. Order\\s*\\d+[\\w\\s]+/i)?.[0] || '';
          const imgs = [...document.querySelectorAll('img[src]')]
            .map(img => img.currentSrc || img.src)
            .filter(Boolean);
          const descNodes = [...document.querySelectorAll('body *')]
            .map(el => clean(el.innerText))
            .filter(t => t.length > 80 && !t.startsWith('$'))
            .slice(0, 20);
          return {
            title,
            body,
            priceCandidates,
            minOrder,
            images: [...new Set(imgs)],
            descNodes
          };
        }"""
    )
    images = [
        img
        for img in data["images"]
        if "alicdn.com" in img or "alibaba.com" in img
    ]
    description = first_text(data["descNodes"])
    if not description:
        description = data["body"][:1200]
    return {
        "url": url,
        "title": data["title"],
        "price_candidates": data["priceCandidates"][:10],
        "min_order": data["minOrder"],
        "description": description,
        "images": images[:20],
    }


with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(WS_ENDPOINT)
    context = browser.contexts[0]

    store_page = None
    for pg in context.pages:
        if "mcduii.en.alibaba.com" in pg.url:
            store_page = pg
            break
    if store_page is None:
        store_page = context.new_page()
        store_page.goto(STORE_URL, wait_until="domcontentloaded", timeout=120000)

    store_page.bring_to_front()
    store_page.wait_for_timeout(3000)

    seed_pages = [
        STORE_URL,
        "https://mcduii.en.alibaba.com/productlist.html",
    ]

    category_urls = []
    product_urls = []

    for seed in seed_pages:
        store_page.goto(seed, wait_until="domcontentloaded", timeout=120000)
        store_page.wait_for_timeout(4000)
        links = store_page.evaluate(
            """() => [...document.querySelectorAll('a[href]')].map(a => a.href).filter(Boolean)"""
        )
        for link in links:
            if "productgrouplist" in link:
                category_urls.append(norm_url(link))
            if "alibaba.com/product-detail/" in link:
                product_urls.append(norm_url(link))

    category_urls = dedupe(category_urls)

    for category in category_urls:
        try:
            store_page.goto(category, wait_until="domcontentloaded", timeout=120000)
            store_page.wait_for_timeout(3500)
            for _ in range(3):
                store_page.mouse.wheel(0, 4000)
                store_page.wait_for_timeout(1200)
            links = store_page.evaluate(
                """() => [...document.querySelectorAll('a[href]')].map(a => a.href).filter(Boolean)"""
            )
            for link in links:
                if "alibaba.com/product-detail/" in link:
                    product_urls.append(norm_url(link))
        except Exception as exc:
            print("CATEGORY_ERR", category, exc)

    product_urls = dedupe(product_urls)
    print("CATEGORY_COUNT", len(category_urls))
    print("PRODUCT_URL_COUNT", len(product_urls))

    product_page = context.new_page()
    products = []
    for idx, product_url in enumerate(product_urls, start=1):
        try:
            item = scrape_product(product_page, product_url)
            products.append(item)
            print(f"[{idx}/{len(product_urls)}] {item['title']}")
        except Exception as exc:
            print("PRODUCT_ERR", product_url, exc)
        time.sleep(1)

    OUTPUT.write_text(
        json.dumps(
            {
                "store_url": STORE_URL,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "category_urls": category_urls,
                "products": products,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Saved {len(products)} products to {OUTPUT}")

    product_page.close()
    browser.close()
