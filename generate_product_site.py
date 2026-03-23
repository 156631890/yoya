from __future__ import annotations

import html
import json
import re
from pathlib import Path


BASE = Path(__file__).parent
SOURCE = BASE / "mcduii_products.json"
DATA_DIR = BASE / "data"
PRODUCTS_DIR = BASE / "products"
DATA_DIR.mkdir(exist_ok=True)
PRODUCTS_DIR.mkdir(exist_ok=True)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:90] or "product"


def extract_price(candidates: list[str]) -> str:
    for item in candidates:
        prices = re.findall(r"\$\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?", item)
        if prices:
            return prices[0]
    return "Contact for quote"


def clean_images(images: list[str]) -> list[str]:
    out = []
    for img in images:
        low = img.lower()
        if low.endswith(".svg"):
            continue
        if "/flag/" in low or "flag/assets" in low:
            continue
        if "imgextra" in low:
            continue
        if not any(ext in low for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            continue
        if any(tag in low for tag in ["20-20", "30-30", "49-49", "54-55", "70-70", "80x80", "80-80"]):
            continue
        if "logo" in low and "kf/" not in low:
            continue
        if "tps-" in low and "960x960" not in low and "kf/" not in low:
            continue
        if img not in out:
            out.append(img)
    return out[:6]


def infer_category(title: str) -> str:
    low = title.lower()
    mapping = [
        ("Menswear", ["track suit for men", "for men", "men's", " mens ", "unisex", "basketball"]),
        ("Kidswear", ["girls", "children", "kids"]),
        ("Tennis Wear", ["tennis", "golf", "skirt", "dress", "badminton"]),
        ("Sports Bra", ["bra", "vest"]),
        ("Jumpsuit", ["jumpsuit", "bodysuit"]),
        ("Yoga Top", ["top", "jacket", "hoodie", "shirt", "cardigan", "sweatshirt"]),
        ("Yoga Shorts", ["shorts"]),
        ("Yoga Leggings", ["legging", "pants", "trousers", "flare"]),
        ("Yoga Set", ["set", "outfit", "2-piece", "two-piece"]),
    ]
    for label, words in mapping:
        if any(word in low for word in words):
            return label
    return "Sportswear"


def compact_title(title: str) -> str:
    text = re.sub(r"\b(2025|new|cross-border|women's|women|for women)\b", "", title, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" -")
    return text[:88] if len(text) > 88 else text


def make_summary(title: str, category: str) -> str:
    low = title.lower()
    features = []
    if "seamless" in low:
        features.append("seamless knit construction")
    if "quick-dry" in low or "quick dry" in low:
        features.append("quick-dry performance")
    if "high waist" in low or "high-waisted" in low:
        features.append("high-waist fit")
    if "breathable" in low:
        features.append("breathable wearability")
    if "plus size" in low:
        features.append("plus-size support")
    if "zipper" in low:
        features.append("zip-front styling")
    if "brushed" in low:
        features.append("soft brushed handfeel")
    features = features[:3] or ["factory-supported wholesale production", "platform-ready styling", "OEM/ODM sourcing support"]
    return f"{category} developed for wholesale and private label buyers with {', '.join(features)}."


def make_bullets(title: str, category: str, price: str) -> list[str]:
    low = title.lower()
    bullets = [f"Category: {category}", f"Price reference: {price}", "Factory source: Yiwu Mcdull Sports Goods Co., Ltd."]
    if "seamless" in low:
        bullets.append("Construction: seamless performance knit")
    if "spandex" in low or "nylon" in low:
        bullets.append("Material cue: nylon / spandex performance blend")
    if "plus size" in low:
        bullets.append("Fit note: includes plus-size market demand")
    return bullets[:5]


def page_shell(title: str, description: str, body: str, current: str = "") -> str:
    nav = {name: "" for name in ["home", "catalog", "manufacturing", "sustainability", "about", "faq", "contact"]}
    if current:
        nav[current] = ' aria-current="page"'
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description)}" />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="../assets/styles.css" />
  </head>
  <body>
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="../index.html">Nanjian <span>Hosiery</span></a>
        <nav class="nav" aria-label="Primary">
          <a href="../index.html"{nav["home"]}>Home</a>
          <a href="../catalog.html"{nav["catalog"]}>Catalog</a>
          <a href="../manufacturing.html"{nav["manufacturing"]}>Manufacturing</a>
          <a href="../sustainability.html"{nav["sustainability"]}>Sustainability</a>
          <a href="../about.html"{nav["about"]}>About</a>
          <a href="../faq.html"{nav["faq"]}>FAQ</a>
          <a href="../contact.html"{nav["contact"]}>Inquiry</a>
        </nav>
        <a class="header-cta" href="../contact.html">Contact Factory</a>
      </div>
    </header>
    {body}
    <footer class="footer"><div class="container"><div class="footer-note">(c) <span data-year></span> Yiwu Nanjian Hosiery Co., Ltd.</div></div></footer>
    <script src="../assets/app.js"></script>
  </body>
</html>"""


raw = json.loads(SOURCE.read_text(encoding="utf-8"))
products = []
used = set()

for item in raw["products"]:
    title = (item.get("title") or "").strip()
    if not title:
        continue
    price = extract_price(item.get("price_candidates", []))
    category = infer_category(title)
    clean_title = compact_title(title)
    slug = slugify(clean_title)
    if slug in used:
        slug = f"{slug}-{len(used)+1}"
    used.add(slug)
    images = clean_images(item.get("images", []))
    if not images:
        continue
    desc = item.get("description") or ""
    if not desc or desc.lower().startswith("what are you looking for"):
        desc = make_summary(title, category)
    product = {
        "slug": slug,
        "title": clean_title,
        "original_title": title,
        "category": category,
        "price": price,
        "min_order": item.get("min_order") or "MOQ shown on request",
        "summary": make_summary(title, category),
        "bullets": make_bullets(title, category, price),
        "description": desc,
        "images": images,
        "source_url": item["url"],
    }
    products.append(product)

products.sort(key=lambda x: (x["category"], x["title"]))
category_counts = {}
for item in products:
    category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

(DATA_DIR / "products_clean.json").write_text(json.dumps({"products": products}, ensure_ascii=False, indent=2), encoding="utf-8")

cards = []
for product in products:
    cards.append(
        f"""<article class="product-card">
  <img src="{html.escape(product['images'][0])}" alt="{html.escape(product['title'])}" />
  <div class="content">
    <span class="eyebrow">{html.escape(product['category'])}</span>
    <h3>{html.escape(product['title'])}</h3>
    <p>{html.escape(product['summary'])}</p>
    <div class="tag-row">
      <span class="chip">{html.escape(product['price'])}</span>
      <a class="button ghost" href="./products/{html.escape(product['slug'])}.html">View Detail</a>
    </div>
  </div>
</article>"""
    )

category_lines = "".join(f"<li>{html.escape(k)}: {v} products</li>" for k, v in sorted(category_counts.items()))
catalog_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Imported Product Catalog | Mcdull Sports Goods Product Library</title>
    <meta name="description" content="Imported product library based on the authorized Alibaba store, rewritten into the website style for independent-site presentation." />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="canonical" href="https://www.nanjianhosiery.com/catalog.html" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="./assets/styles.css" />
  </head>
  <body>
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="./index.html">Nanjian <span>Hosiery</span></a>
        <nav class="nav" aria-label="Primary">
          <a href="./index.html">Home</a>
          <a href="./catalog.html" aria-current="page">Catalog</a>
          <a href="./manufacturing.html">Manufacturing</a>
          <a href="./sustainability.html">Sustainability</a>
          <a href="./about.html">About</a>
          <a href="./faq.html">FAQ</a>
          <a href="./contact.html">Inquiry</a>
        </nav>
        <a class="header-cta" href="./contact.html">Contact Factory</a>
      </div>
    </header>
    <main>
      <section class="page-hero">
        <div class="container">
          <div class="breadcrumb"><a href="./index.html">Home</a><span>/</span><span>Catalog</span></div>
          <span class="eyebrow">Authorized Imported Product Library</span>
          <h1>{len(raw['products'])} Sportswear Products Reworked into the Independent-Site Style.</h1>
          <p class="lead">These products were imported from the authorized Alibaba store and normalized into a cleaner B2B catalog structure for independent-site use.</p>
          <div class="grid-2">
            <article class="card"><h3>Library Scope</h3><ul class="mini-list"><li>Total imported products: {len(products)}</li>{category_lines}</ul></article>
            <article class="card"><h3>Catalog Notes</h3><ul class="mini-list"><li>Titles were compacted for cleaner storefront presentation.</li><li>Price fields were normalized from Alibaba page output.</li><li>Main image links currently use source CDN URLs.</li></ul></article>
          </div>
        </div>
      </section>
      <section class="section-tight">
        <div class="container product-grid">
          {"".join(cards)}
        </div>
      </section>
    </main>
    <footer class="footer"><div class="container"><div class="footer-note">(c) <span data-year></span> Yiwu Nanjian Hosiery Co., Ltd.</div></div></footer>
    <script src="./assets/app.js"></script>
  </body>
</html>"""

(BASE / "catalog.html").write_text(catalog_html, encoding="utf-8")

for product in products:
    gallery = "".join(
        f'<img src="{html.escape(img)}" alt="{html.escape(product["title"])}" style="border-radius:16px;margin-bottom:1rem;" />'
        for img in product["images"][:4]
    )
    bullets = "".join(f"<li>{html.escape(item)}</li>" for item in product["bullets"])
    body = f"""
    <main>
      <section class="page-hero">
        <div class="container">
          <div class="breadcrumb"><a href="../index.html">Home</a><span>/</span><a href="../catalog.html">Catalog</a><span>/</span><span>{html.escape(product['category'])}</span></div>
          <div class="story-grid">
            <div class="hero-image" style="background:#f0eee8;">
              <img src="{html.escape(product['images'][0])}" alt="{html.escape(product['title'])}" style="mix-blend-mode:normal;opacity:1;" />
            </div>
            <div>
              <span class="eyebrow">{html.escape(product['category'])}</span>
              <h1>{html.escape(product['title'])}</h1>
              <p class="lead">{html.escape(product['summary'])}</p>
              <div class="chip-row">
                <span class="chip">{html.escape(product['price'])}</span>
                <span class="chip">{html.escape(product['min_order'])}</span>
              </div>
              <div class="tag-row">
                <a class="button primary" href="../contact.html">Request Quote</a>
                <a class="button secondary" href="{html.escape(product['source_url'])}">View Source Item</a>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section class="section section-alt">
        <div class="container grid-2">
          <article class="card">
            <h3>Independent-Site Copy</h3>
            <p>{html.escape(product['summary'])}</p>
            <ul class="mini-list">{bullets}</ul>
          </article>
          <article class="card">
            <h3>Original Source Title</h3>
            <p>{html.escape(product['original_title'])}</p>
            <p class="muted">Source URL: <a class="link" href="{html.escape(product['source_url'])}">{html.escape(product['source_url'])}</a></p>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="container grid-2">
          <article class="card">
            <h3>Product Gallery</h3>
            {gallery}
          </article>
          <article class="card">
            <h3>Product Note</h3>
            <p>{html.escape(product['description'][:900])}</p>
          </article>
        </div>
      </section>
    </main>"""
    page = page_shell(f"{product['title']} | Nanjian Hosiery Product Detail", product["summary"], body, current="catalog")
    (PRODUCTS_DIR / f"{product['slug']}.html").write_text(page, encoding="utf-8")

print(f"Generated {len(products)} products, catalog page, and detail pages in {PRODUCTS_DIR}")
