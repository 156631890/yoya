from __future__ import annotations

import json
import re
import time
from pathlib import Path

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


def flatten_jsonld(node) -> list[dict]:
    out = []
    if isinstance(node, dict):
        out.append(node)
        for value in node.values():
            out.extend(flatten_jsonld(value))
    elif isinstance(node, list):
        for value in node:
            out.extend(flatten_jsonld(value))
    return out


def norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def clean_image_list(images: list[str]) -> list[str]:
    out = []
    for img in images:
        if not img:
            continue
        low = img.lower()
        if not ("alicdn.com" in low or "alibaba.com" in low):
            continue
        if any(tag in low for tag in [".svg", "/flag/", "flag/assets", "/flags/", "20-20", "30-30", "49-49", "54-55", "70-70", "80x80", "80-80", "174-42", "297-40", "153-39", "396-132", "447-132", "1890-1062", "280-280"]):
            continue
        candidate = (
            img.replace("_80x80.png", "")
            .replace(".jpg_960x960q80.jpg", ".jpg")
            .replace(".png_960x960q80.jpg", ".png")
            .replace(".jpg_480x480.jpg", ".jpg")
            .replace(".png_480x480.jpg", ".png")
        )
        if candidate not in out:
            out.append(candidate)
    return out


def image_candidates_from_jsonld(value) -> list[str]:
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(image_candidates_from_jsonld(item))
    elif isinstance(value, dict):
        for key in ("url", "contentUrl", "image", "@id"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                out.append(candidate)
            elif isinstance(candidate, (list, dict)):
                out.extend(image_candidates_from_jsonld(candidate))
    return out


def extract_listing_cards(page) -> list[dict]:
    return page.evaluate(
        """() => {
          const clean = (s) => (s || '').replace(/\\s+/g, ' ').trim();
          const toAbs = (u) => {
            if (!u) return '';
            if (u.startsWith('//')) return 'https:' + u;
            return u;
          };
          return [...document.querySelectorAll('.icbu-product-card, [data-id]')]
            .map(card => {
              const link = card.querySelector('a[href*="alibaba.com/product-detail/"]');
              if (!link) return null;
              const title = clean(link.getAttribute('title') || link.textContent || '');
              const price = clean(card.querySelector('.price')?.innerText || card.querySelector('.num')?.innerText || '');
              const minOrder = clean(card.querySelector('.moq')?.innerText || '');
              const imgEl = card.querySelector('img');
              const img = toAbs(
                imgEl?.currentSrc
                || imgEl?.src
                || imgEl?.getAttribute('data-src')
                || imgEl?.getAttribute('data-lazyload-src')
                || imgEl?.getAttribute('data-origin')
                || imgEl?.getAttribute('data-img-src')
                || ''
              );
              return {
                url: toAbs(link.href),
                title,
                price,
                min_order: minOrder,
                image: img
              };
            })
            .filter(Boolean);
        }"""
    )


def scrape_product(page, url: str, listing_fallback: dict | None = None) -> dict:
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(5000)
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
          const attrs = ['src', 'data-src', 'data-lazyload-src', 'data-origin', 'data-img-src', 'data-image'];
          const imgs = [...document.querySelectorAll('img')]
            .flatMap(img => attrs.map(attr => img.getAttribute(attr) || '').concat(img.currentSrc || ''))
            .filter(Boolean);
          const backgroundImgs = [...document.querySelectorAll('[style*=\"background\"]')]
            .map(el => getComputedStyle(el).backgroundImage || '')
            .map(bg => (bg.match(/url\\([\"']?(.*?)[\"']?\\)/) || [])[1] || '')
            .filter(Boolean);
          const descNodes = [...document.querySelectorAll('body *')]
            .map(el => clean(el.innerText))
            .filter(t => t.length > 80 && !t.startsWith('$'))
            .slice(0, 20);
          const jsonld = [...document.querySelectorAll('script[type="application/ld+json"]')]
            .map(el => el.textContent || '')
            .filter(Boolean);
          const metaImage = document.querySelector('meta[property="og:image"]')?.content || '';
          const metaDescription = document.querySelector('meta[property="og:description"]')?.content
            || document.querySelector('meta[name="description"]')?.content
            || '';
          return {
            title,
            body,
            priceCandidates,
            minOrder,
            images: [...new Set(imgs.concat(backgroundImgs))],
            descNodes,
            jsonld,
            metaImage,
            metaDescription
          };
        }"""
    )
    jsonld_items = []
    for block in data["jsonld"]:
        try:
            jsonld_items.extend(flatten_jsonld(json.loads(block)))
        except Exception:
            continue

    product_ld = next(
        (
            item for item in jsonld_items
            if str(item.get("@type", "")).lower() == "product"
        ),
        {},
    )
    offers = product_ld.get("offers") if isinstance(product_ld.get("offers"), dict) else {}
    ld_images = image_candidates_from_jsonld(product_ld.get("image"))
    title = norm_text(product_ld.get("name") or data["title"])
    description = norm_text(product_ld.get("description") or first_text(data["descNodes"]) or data["metaDescription"] or data["body"][:1200])
    images = clean_image_list(ld_images + [data["metaImage"]] + data["images"])
    price_candidates = list(data["priceCandidates"][:10])
    offer_price = offers.get("price")
    if offer_price:
        offer_price_text = f"${offer_price}"
        if offer_price_text not in price_candidates:
            price_candidates.insert(0, offer_price_text)
    if listing_fallback:
        if not title:
            title = norm_text(listing_fallback.get("title", ""))
        if not description or description.startswith("try{!function()"):
            description = title or norm_text(listing_fallback.get("title", ""))
        if not images:
            images = clean_image_list([listing_fallback.get("image", "")])
        if not price_candidates and listing_fallback.get("price"):
            price_candidates = [listing_fallback["price"]]
    return {
        "url": url,
        "title": title,
        "price_candidates": price_candidates[:10],
        "min_order": data["minOrder"] or (listing_fallback or {}).get("min_order", ""),
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
    listing_map = {}

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
            cards = extract_listing_cards(store_page)
            for card in cards:
                url = norm_url(card["url"])
                listing_map[url] = {
                    "title": card["title"],
                    "price": card["price"],
                    "min_order": card["min_order"],
                    "image": card["image"],
                }
                product_urls.append(url)
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
            item = scrape_product(product_page, product_url, listing_map.get(product_url))
            if not item["title"] and product_url in listing_map:
                fallback = listing_map[product_url]
                item["title"] = fallback["title"]
                if fallback["price"] and not item["price_candidates"]:
                    item["price_candidates"] = [fallback["price"]]
                if fallback["min_order"] and not item["min_order"]:
                    item["min_order"] = fallback["min_order"]
                if fallback["image"] and not item["images"]:
                    item["images"] = clean_image_list([fallback["image"]])
            products.append(item)
            print(f"[{idx}/{len(product_urls)}] {item['title']}")
        except Exception as exc:
            fallback = listing_map.get(product_url)
            if fallback:
                item = {
                    "url": product_url,
                    "title": fallback["title"],
                    "price_candidates": [fallback["price"]] if fallback["price"] else [],
                    "min_order": fallback["min_order"],
                    "description": fallback["title"],
                    "images": clean_image_list([fallback["image"]]),
                }
                products.append(item)
                print(f"[{idx}/{len(product_urls)}] FALLBACK {item['title']}")
            else:
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
