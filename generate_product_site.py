from __future__ import annotations

import html
import json
import os
import re
from collections import Counter
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
        if not img:
            continue
        low = img.lower()
        if low.endswith(".svg"):
            continue
        if "/flag/" in low or "flag/assets" in low or "/flags/" in low:
            continue
        if not any(ext in low for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            continue
        if any(tag in low for tag in ["20-20", "30-30", "49-49", "54-55", "70-70", "80x80", "80-80", "174-42", "297-40", "153-39", "396-132", "447-132", "1890-1062", "280-280"]):
            continue
        if "logo" in low and "kf/" not in low:
            continue
        normalized = (
            img.replace("_80x80.png", "")
            .replace(".jpg_960x960q80.jpg", ".jpg")
            .replace(".png_960x960q80.jpg", ".png")
            .replace(".jpg_480x480.jpg", ".jpg")
            .replace(".png_480x480.jpg", ".png")
        )
        if normalized not in out:
            out.append(normalized)
    preferred = [
        img for img in out
        if "sc04.alicdn.com" in img or "img.alicdn.com" in img or "_960x960" in img or "imgextra" in img
    ]
    if preferred:
        return preferred[:8]
    fallback = [img for img in out if "kf/" in img or "imgextra" in img or "alicdn.com" in img]
    return fallback[:8]


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
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
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

# Remove products whose hero image is clearly a repeated generic fallback rather than
# a product-specific image. We only apply this to duplicated imgextra CDN assets.
first_image_counts = Counter(item["images"][0] for item in products if item.get("images"))
generic_first_images = {
    url for url, count in first_image_counts.items()
    if count >= 5 and "img.alicdn.com/imgextra/" in url.lower()
}
if generic_first_images:
    products = [item for item in products if item["images"][0] not in generic_first_images]

category_counts = {}
for item in products:
    category_counts[item["category"]] = category_counts.get(item["category"], 0) + 1

(DATA_DIR / "products_clean.json").write_text(json.dumps({"products": products}, ensure_ascii=False, indent=2), encoding="utf-8")

# Remove stale product pages so old no-image pages do not remain addressable.
expected_product_files = {f"{item['slug']}.html" for item in products}
for old_page in PRODUCTS_DIR.glob("*.html"):
    if old_page.name not in expected_product_files:
        try:
            old_page.chmod(0o666)
            old_page.unlink()
        except PermissionError:
            # Leave locked files in place rather than failing the full site rebuild.
            pass

category_links = "".join(
    f'<a class="catalog-directory__link" href="#category-{slugify(name)}"><span>{html.escape(name)}</span><strong>{count}</strong></a>'
    for name, count in sorted(category_counts.items())
)

cards = []
current_category = None
for product in products:
    section_start = ""
    if product["category"] != current_category:
        current_category = product["category"]
        section_start = f"""
        <div class="catalog-section-heading" id="category-{slugify(current_category)}">
          <div>
            <h2>{html.escape(current_category)}</h2>
          </div>
          <p class="catalog-section-count">{category_counts[current_category]} products</p>
        </div>"""
    thumb_strip = "".join(
        f'<span class="product-card__thumb"><img src="{html.escape(img)}" alt="{html.escape(product["title"])} preview" /></span>'
        for img in product["images"][1:4]
    )
    image_block = f"""
  <div class="product-card__media">
    <div class="product-card__frame">
      <img src="{html.escape(product["images"][0])}" alt="{html.escape(product["title"])}" />
    </div>
    <div class="product-card__media-top">
      <span class="product-card__badge">{html.escape(product['category'])}</span>
      <span class="product-card__price-tag">{html.escape(product['price'])}</span>
    </div>
    <div class="product-card__thumbs">{thumb_strip}</div>
  </div>"""
    cards.append(
        f"""{section_start}<article class="product-card">
  {image_block}
  <div class="content">
    <div class="product-card__meta">
      <span class="product-card__moq">{html.escape(product['min_order'])}</span>
      <span class="product-card__sku">{len(product['images'])} views</span>
    </div>
    <h3>{html.escape(product['title'])}</h3>
    <p class="product-card__summary">{html.escape(product['summary'])}</p>
    <div class="product-card__footer">
      <a class="button ghost" href="./products/{html.escape(product['slug'])}.html">View Detail</a>
    </div>
  </div>
</article>"""
    )

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
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
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
          <div class="catalog-hero">
            <div class="catalog-hero__intro">
              <div class="breadcrumb"><a href="./index.html">Home</a><span>/</span><span>Catalog</span></div>
              <span class="eyebrow">Authorized Imported Product Library</span>
              <h1>Sportswear Products Reworked into the Independent-Site Style.</h1>
              <p class="lead">These products were imported from the authorized Alibaba store and normalized into a cleaner B2B catalog structure for independent-site use.</p>
            </div>
          </div>
        </div>
      </section>
      <section class="section-tight">
        <div class="container catalog-layout">
          <aside class="catalog-sidebar">
            <div class="catalog-directory catalog-directory--sidebar">
              <span class="catalog-directory__label">Product Directory</span>
              <div class="catalog-directory__grid">
                {category_links}
              </div>
            </div>
          </aside>
          <div class="catalog-main">
            <div class="product-grid">
              {"".join(cards)}
            </div>
          </div>
        </div>
      </section>
    </main>
    <footer class="footer"><div class="container"><div class="footer-note">(c) <span data-year></span> Yiwu Nanjian Hosiery Co., Ltd.</div></div></footer>
    <script src="./assets/app.js"></script>
  </body>
</html>"""

(BASE / "catalog.html").write_text(catalog_html, encoding="utf-8")

top_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
category_samples = []
for category_name, count in top_categories[:4]:
    sample = next((item for item in products if item["category"] == category_name and item["images"]), None)
    if not sample:
        continue
    category_samples.append(
        {
            "name": category_name,
            "count": count,
            "image": sample["images"][0],
            "summary": sample["summary"],
            "slug": sample["slug"],
        }
    )

hero_product = next((item for item in products if item["images"]), products[0])
hero_gallery = "".join(
    f'<span class="home-hero__mini"><img src="{html.escape(img)}" alt="{html.escape(hero_product["title"])} preview" /></span>'
    for img in hero_product["images"][:4]
)
home_stat_cards = [
    ("Catalog Entries", str(len(products)), "Filtered product pages currently live in the site catalog."),
    ("Top Category", top_categories[0][0], f"{top_categories[0][1]} listed products currently lead the assortment."),
    ("Equipment", "400+", "Imported professional machines supporting factory-scale output."),
]
home_stats = "".join(
    f'<article class="metric-card home-stat"><span class="product-stat__label">{html.escape(label)}</span><strong>{html.escape(value)}</strong><span class="muted">{html.escape(note)}</span></article>'
    for label, value, note in home_stat_cards
)
home_categories = "".join(
    f"""<article class="home-category-card">
      <div class="home-category-card__media">
        <img src="{html.escape(item['image'])}" alt="{html.escape(item['name'])}" />
      </div>
      <div class="content">
        <span class="eyebrow">{html.escape(item['name'])}</span>
        <h3>{html.escape(str(item['count']))} active listings</h3>
        <p>{html.escape(item['summary'])}</p>
        <p><a class="link" href="./catalog.html#category-{html.escape(slugify(item['name']))}">Jump to category</a></p>
      </div>
    </article>"""
    for item in category_samples
)
capability_rows = "".join(
    f"<tr><td>{html.escape(category)}</td><td>{count} products</td><td><a class=\"link\" href=\"./catalog.html#category-{html.escape(slugify(category))}\">View category</a></td></tr>"
    for category, count in top_categories
)

home_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Nanjian Hosiery | Activewear, Seamless Apparel and Private Label Manufacturing</title>
    <meta
      name="description"
      content="Independent B2B website for Yiwu Nanjian Hosiery Co., Ltd. featuring activewear categories, seamless apparel production capability and private label manufacturing support."
    />
    <meta name="robots" content="index,follow,max-image-preview:large" />
    <link rel="canonical" href="https://www.nanjianhosiery.com/" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="Nanjian Hosiery | Activewear and Manufacturing Directory" />
    <meta property="og:description" content="Browse the current sportswear product directory and factory capability profile for Yiwu Nanjian Hosiery Co., Ltd." />
    <meta property="og:url" content="https://www.nanjianhosiery.com/" />
    <meta property="og:image" content="{html.escape(hero_product['images'][0])}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="./assets/styles.css" />
  </head>
  <body>
    <header class="site-header">
      <div class="container header-inner">
        <a class="brand" href="./index.html">Nanjian <span>Hosiery</span></a>
        <nav class="nav" aria-label="Primary">
          <a href="./index.html" aria-current="page">Home</a>
          <a href="./catalog.html">Catalog</a>
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
      <section class="page-hero home-hero">
        <div class="container home-hero__grid">
          <div class="home-hero__copy">
            <span class="eyebrow">Reliable Activewear Manufacturer</span>
            <p class="home-kicker"><strong>{len(products)}+</strong> live catalog entries</p>
            <h1>Your Reliable Sportswear and Seamless Apparel Manufacturing Partner in China.</h1>
            <p class="lead">Yiwu Nanjian Hosiery Co., Ltd. now presents its current product structure around activewear, seamless apparel and private label supply. The homepage follows the live catalog so product emphasis, category counts and factory story stay aligned.</p>
            <div class="tag-row">
              <span class="tag">OEM and private label support</span>
              <span class="tag">{html.escape(top_categories[0][0])} leads the assortment</span>
              <span class="tag">Factory and catalog in one site</span>
            </div>
            <div class="tag-row">
              <a class="button primary" href="./catalog.html">Browse Product Catalog</a>
              <a class="button secondary" href="./contact.html">Request Pricing</a>
            </div>
            <div class="home-hero__stats">
              {home_stats}
            </div>
          </div>
          <div class="home-hero__visual">
            <div class="home-hero__panel">
              <div class="home-hero__image-wrap">
                <img src="{html.escape(hero_product['images'][0])}" alt="{html.escape(hero_product['title'])}" class="home-hero__image" />
              </div>
              <div class="home-hero__floating">
                <span class="eyebrow">{html.escape(hero_product['category'])}</span>
                <h3>{html.escape(hero_product['title'])}</h3>
                <p>{html.escape(hero_product['summary'])}</p>
              </div>
              <div class="home-hero__thumbs">{hero_gallery}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="section-tight">
        <div class="container">
          <div class="home-trustbar">
            <span>Factory area 10,000㎡+</span>
            <span>Building area 13,000㎡+</span>
            <span>400+ imported machines</span>
            <span>ISO9000:2000 aligned operation</span>
          </div>
        </div>
      </section>

      <section class="section section-alt">
        <div class="container">
          <span class="eyebrow">Our Capabilities</span>
          <h2>Development, manufacturing and category execution for activewear buyers.</h2>
          <div class="grid-3">
            <article class="card home-capability-card">
              <h3>Product Development and Category Mapping</h3>
              <p>We organize jumpsuits, sports bras, yoga tops, leggings, shorts, sets and men&apos;s sportswear into a cleaner product structure for wholesale and sourcing teams.</p>
            </article>
            <article class="card home-capability-card">
              <h3>Efficient and Stable Manufacturing System</h3>
              <p>The company profile highlights more than 400 sets of imported professional equipment alongside substantial factory and building area to support production scale.</p>
            </article>
            <article class="card home-capability-card">
              <h3>OEM and Private Label Supply Support</h3>
              <p>From category selection to inquiry handoff, the site is positioned to support buyers looking for factory-backed, customizable sportswear programs.</p>
            </article>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container">
          <span class="eyebrow">Our Products</span>
          <h2>Live category blocks pulled from the current product library.</h2>
          <div class="grid-4 section-tight">
            {home_categories}
          </div>
        </div>
      </section>

      <section class="section section-alt">
        <div class="container">
          <span class="eyebrow">Strengths</span>
          <h2>Current product structure and factory signals in one view.</h2>
          <div class="home-strengths">
            <article class="metric-card home-strength">
              <strong>{len(products)}</strong>
              <span class="muted">filtered product pages currently live</span>
            </article>
            <article class="metric-card home-strength">
              <strong>{top_categories[0][1]}</strong>
              <span class="muted">{html.escape(top_categories[0][0])} listings currently lead the catalog</span>
            </article>
            <article class="metric-card home-strength">
              <strong>400+</strong>
              <span class="muted">imported professional machine systems</span>
            </article>
            <article class="metric-card home-strength">
              <strong>10,000㎡+</strong>
              <span class="muted">factory footprint in Yiwu</span>
            </article>
          </div>
          <div class="spec-table" style="margin-top:1.5rem;">
            <table>
              <thead><tr><th>Category</th><th>Listings</th><th>Navigation</th></tr></thead>
              <tbody>
                {capability_rows}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="container cta-panel">
          <div>
            <span class="eyebrow">Inquiry Ready</span>
            <h2>Need a sportswear supplier with active category coverage and factory backing?</h2>
            <p class="lead">Send the product category, MOQ target, fabric direction and whether you need OEM or private label support. We can align the discussion around the current product structure on this site.</p>
          </div>
          <div class="tag-row">
            <a class="button primary" href="./contact.html">Send Inquiry</a>
            <a class="button ghost" href="./catalog.html">Explore Products</a>
          </div>
        </div>
      </section>
    </main>
    <footer class="footer">
      <div class="container">
        <div class="footer-grid">
          <div>
            <div class="brand">Nanjian <span>Hosiery</span></div>
            <p class="muted">Independent B2B website focused on activewear categories, seamless apparel and factory capability.</p>
          </div>
          <div>
            <h3>Catalog</h3>
            <p><a class="link" href="./catalog.html">Jumpsuits</a></p>
            <p><a class="link" href="./catalog.html">Sports Bras</a></p>
            <p><a class="link" href="./catalog.html">Yoga Sets</a></p>
          </div>
          <div>
            <h3>Factory</h3>
            <p><a class="link" href="./manufacturing.html">Equipment & Capacity</a></p>
            <p><a class="link" href="./sustainability.html">Quality & Compliance</a></p>
            <p><a class="link" href="./about.html">Company Overview</a></p>
          </div>
          <div>
            <h3>Contact</h3>
            <p class="muted">Yiwu Nanjian Hosiery Co., Ltd.</p>
            <p class="muted">lorenzhao678@gmail.com</p>
            <p><a class="link" href="./contact.html">Open inquiry form</a></p>
          </div>
        </div>
        <div class="footer-note">(c) <span data-year></span> Yiwu Nanjian Hosiery Co., Ltd.</div>
      </div>
    </footer>
    <script src="./assets/app.js"></script>
  </body>
</html>"""

(BASE / "index.html").write_text(home_html, encoding="utf-8")

for product in products:
    gallery = "".join(
        f'<img src="{html.escape(img)}" alt="{html.escape(product["title"])}" style="border-radius:16px;margin-bottom:1rem;" />'
        for img in product["images"]
    ) or '<div style="padding:1rem;border:1px dashed #c8c0b5;border-radius:16px;">No image imported for this item yet.</div>'
    bullets = "".join(f"<li>{html.escape(item)}</li>" for item in product["bullets"])
    hero_media = (
        f"""
        <div class="product-hero__stage" data-product-hero>
          <img src="{html.escape(product["images"][0])}" alt="{html.escape(product["title"])}" class="product-hero__main" data-product-main-image />
          <div class="product-hero__rail">
            {''.join(f'<button type="button" class="product-hero__mini{" is-active" if i == 0 else ""}" data-product-thumb data-image="{html.escape(img)}" data-alt="{html.escape(product["title"])} detail"><img src="{html.escape(img)}" alt="{html.escape(product["title"])} detail" /></button>' for i, img in enumerate(product["images"]))}
          </div>
        </div>"""
        if product["images"]
        else '<div style="min-height:420px;display:grid;place-items:center;color:#5f5a52;">No image imported</div>'
    )
    body = f"""
    <main>
      <section class="page-hero">
        <div class="container">
          <div class="breadcrumb"><a href="../index.html">Home</a><span>/</span><a href="../catalog.html">Catalog</a><span>/</span><span>{html.escape(product['category'])}</span></div>
          <div class="story-grid">
            <div class="hero-image" style="background:#f0eee8;">
              {hero_media}
            </div>
            <div>
              <span class="eyebrow">{html.escape(product['category'])}</span>
              <h1>{html.escape(product['title'])}</h1>
              <p class="lead">{html.escape(product['summary'])}</p>
              <div class="product-detail__stats">
                <article class="metric-card">
                  <span class="product-stat__label">Price</span>
                  <strong>{html.escape(product['price'])}</strong>
                </article>
                <article class="metric-card">
                  <span class="product-stat__label">MOQ</span>
                  <strong>{html.escape(product['min_order'])}</strong>
                </article>
              </div>
              <div class="tag-row">
                <a class="button primary" href="../contact.html">Request Quote</a>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section class="section section-alt">
        <div class="container">
          <article class="card">
            <h3>Independent-Site Copy</h3>
            <p>{html.escape(product['summary'])}</p>
            <ul class="mini-list">{bullets}</ul>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="container grid-2">
          <article class="card">
            <h3>Product Gallery</h3>
            <div class="product-gallery">{gallery}</div>
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
