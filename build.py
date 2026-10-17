"""Build the Clear Money Sheets store site from site/products.json.

Usage:  python site/build.py
Edit prices, checkout links and product text in site/products.json, then run this.
Writes HTML pages, sitemap.xml, robots.txt, favicons and web images into site/.
Needs Python 3 + Pillow (pip install pillow). No other tools.
"""
import json
import shutil
from datetime import date
from html import escape
from pathlib import Path

from PIL import Image, ImageDraw

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
DATA = json.loads((SITE / "products.json").read_text(encoding="utf-8"))
CFG = DATA["site"]
BASE = CFG["base_url"].rstrip("/")
PRODUCTS = DATA["products"]
BUNDLE = DATA["bundle"]
BY_SLUG = {p["slug"]: p for p in PRODUCTS}
BY_SLUG[BUNDLE["slug"]] = BUNDLE
TODAY = date.today().isoformat()
SEPARATE_TOTAL = sum(p["price"] for p in PRODUCTS)
SAVING = SEPARATE_TOTAL - BUNDLE["price"]
SAVING_PCT = round(SAVING / SEPARATE_TOTAL * 100)
TODO_LINKS = []

TOOLS = [
    {"slug": "debt-snowball-avalanche", "name": "Debt snowball vs avalanche calculator",
     "short": "Debt snowball vs avalanche",
     "blurb": "Enter your debts and see your debt-free date and total interest under both methods.",
     "product": "debt-payoff-calculator",
     "description": "Free debt snowball vs avalanche calculator. Enter your debts and see your debt-free date, payoff order and total interest for both methods."},
    {"slug": "50-30-20-budget", "name": "50/30/20 budget calculator", "short": "50/30/20 budget split",
     "blurb": "Split your take-home pay into needs, wants and savings, and compare it with what you spend now.",
     "product": "2027-budget-planner",
     "description": "Free 50/30/20 budget calculator. Split your monthly take-home pay into needs, wants and savings, with your own percentages."},
    {"slug": "savings-goal-calculator", "name": "Savings goal calculator", "short": "Savings goal timeline",
     "blurb": "See when you'll reach a savings goal, and how much a month you need to hit a target date.",
     "product": "savings-goals-tracker",
     "description": "Free savings goal calculator. See when you'll reach your goal and how much you need to save each month to hit a target date."},
]
TOOL_BY_SLUG = {t["slug"]: t for t in TOOLS}


def e(s):
    return escape(str(s), quote=True)


def short(p):
    return p.get("short_name", p["name"])


def money(n):
    return f"{CFG['currency']} {n:g}"


# ---------------------------------------------------------------- images
IMG_OUT = SITE / "assets" / "img"
WIDTHS = (800, 1200)


def build_images():
    """Make WebP + JPEG copies (800 and 1200 wide) of every product image, plus a 1200x630 social image."""
    for p in PRODUCTS + [BUNDLE]:
        src_dir = ROOT / "products" / p["folder"] / "images"
        out_dir = IMG_OUT / p["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        for img in p["images"]:
            src = src_dir / img["file"]
            stem = Path(img["file"]).stem
            targets = [out_dir / f"{stem}-{w}.{ext}" for w in WIDTHS for ext in ("webp", "jpg")]
            if all(t.exists() and t.stat().st_mtime >= src.stat().st_mtime for t in targets):
                continue
            im = Image.open(src).convert("RGB")
            for w in WIDTHS:
                h = round(im.height * w / im.width)
                r = im.resize((w, h), Image.LANCZOS)
                r.save(out_dir / f"{stem}-{w}.webp", "WEBP", quality=80, method=6)
                r.save(out_dir / f"{stem}-{w}.jpg", "JPEG", quality=82, optimize=True, progressive=True)
        # Social preview (Open Graph): cover centred on sand, 1200x630
        cover = src_dir / p["images"][0]["file"]
        og = out_dir / "og.jpg"
        if not og.exists() or og.stat().st_mtime < cover.stat().st_mtime:
            im = Image.open(cover).convert("RGB")
            canvas = Image.new("RGB", (1200, 630), "#F7F4EE")
            h = 630
            w = round(im.width * h / im.height)
            canvas.paste(im.resize((w, h), Image.LANCZOS), ((1200 - w) // 2, 0))
            canvas.save(og, "JPEG", quality=82, optimize=True)


def picture(slug, img, width=800, sizes="(min-width: 1024px) 360px, (min-width: 640px) 50vw, 100vw", eager=False, extra_attr=""):
    stem = Path(img["file"]).stem
    base = f"/assets/img/{slug}/{stem}"
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<picture><source type="image/webp" srcset="{base}-800.webp 800w, {base}-1200.webp 1200w" sizes="{sizes}">'
            f'<img src="{base}-{width}.jpg" srcset="{base}-800.jpg 800w, {base}-1200.jpg 1200w" sizes="{sizes}" '
            f'width="{width}" height="{width * 3 // 4}" alt="{e(img["alt"])}" {loading}{extra_attr}></picture>')


def build_favicons():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1F5F6B"/>'
           '<rect x="14" y="16" width="36" height="6" rx="3" fill="#F7F4EE"/><rect x="14" y="29" width="24" height="6" rx="3" fill="#F7F4EE"/>'
           '<rect x="14" y="42" width="30" height="6" rx="3" fill="#E0A458"/></svg>')
    (SITE / "favicon.svg").write_text(svg, encoding="utf-8")
    for size, name in ((32, "favicon-32.png"), (180, "apple-touch-icon.png")):
        s = size / 64
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, size - 1, size - 1), radius=round(14 * s), fill="#1F5F6B")
        for x, y, w, col in ((14, 16, 36, "#F7F4EE"), (14, 29, 24, "#F7F4EE"), (14, 42, 30, "#E0A458")):
            d.rounded_rectangle((x * s, y * s, (x + w) * s, (y + 6) * s), radius=3 * s, fill=col)
        im.save(SITE / name)


# ---------------------------------------------------------------- shared bits
LOGO = ('<svg width="32" height="32" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#1F5F6B"/>'
        '<rect x="14" y="16" width="36" height="6" rx="3" fill="#F7F4EE"/><rect x="14" y="29" width="24" height="6" rx="3" fill="#F7F4EE"/>'
        '<rect x="14" y="42" width="30" height="6" rx="3" fill="#E0A458"/></svg>')

ICONS = {
    "sheet": '<path d="M4 4h16v16H4z M4 10h16 M4 15h16 M10 4v16"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18 M12 3c3 3.5 3 14.5 0 18 M12 3c-3 3.5-3 14.5 0 18"/>',
    "download": '<path d="M12 4v11 M7 10l5 5 5-5 M5 20h14"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "check": '<path d="M5 12l5 5 9-10"/>',
    "menu": '<path d="M4 7h16 M4 12h16 M4 17h16"/>',
}


def icon(name, size=22):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


TRUST = [("sheet", "Works in Excel + Google Sheets"), ("globe", "Any currency"),
         ("download", "Instant download"), ("lock", "Secure checkout by Lemon Squeezy")]


def trust_list():
    return '<ul class="trust-list">' + "".join(f"<li>{icon(i, 20)}{e(t)}</li>" for i, t in TRUST) + "</ul>"


def buy_button(p, label=None, extra_class=""):
    url = p.get("checkout_url", "")
    if url.startswith("http"):
        text = label or f"Buy now · {money(p['price'])}"
        return f'<a class="btn btn-primary {extra_class}" href="{e(url)}">{e(text)}</a>'
    if p["slug"] not in [s for s, _ in TODO_LINKS]:
        TODO_LINKS.append((p["slug"], p["name"]))
    return (f'<a class="btn btn-primary {extra_class}" role="link" aria-disabled="true">Coming soon</a>')


def product_url(slug):
    return f"/products/{slug}/"


def faq_html(items):
    return '<div class="faq">' + "".join(
        f'<details><summary>{e(q["q"])}</summary><div><p>{e(q["a"])}</p></div></details>' for q in items) + "</div>"


def card(p, heading="h3"):
    return f"""<article class="card" data-category="{e(p['category'])}">
  <a class="card-img" href="{product_url(p['slug'])}" tabindex="-1" aria-hidden="true">{picture(p['slug'], p['images'][0])}</a>
  <div class="card-body">
    <span class="tag">{e(p['category_label'])}</span>
    <{heading}><a href="{product_url(p['slug'])}">{e(p['name'])}</a></{heading}>
    <p>{e(p['promise'])}</p>
    <div class="card-foot"><span class="price">{money(p['price'])}</span>
      <a class="btn btn-secondary" href="{product_url(p['slug'])}">See what's inside<span class="visually-hidden"> {e(p['name'])}</span></a></div>
  </div>
</article>"""


NAV = [("/#sheets", "Spreadsheets", "sheets"), ("/tools/", "Free tools", "tools"), ("/blog/", "Blog", "blog"), ("/about/", "About", "about")]


def layout(path, title, description, body, active=None, og_image=None, extra_head="", scripts=("main",), noindex=False):
    canonical = BASE + path
    og = BASE + (og_image or f"/assets/img/{BUNDLE['slug']}/og.jpg")
    nav = "".join(
        f'<li><a href="{href}"{" aria-current=\"page\"" if key == active else ""}>{label}</a></li>' for href, label, key in NAV)
    bundle_href = BUNDLE["checkout_url"] if BUNDLE["checkout_url"].startswith("http") else product_url(BUNDLE["slug"])
    script_tags = "".join(f'<script src="/assets/js/{s}.js" defer></script>' for s in scripts)
    shop_links = "".join(f'<li><a href="{product_url(p["slug"])}">{e(short(p))}</a></li>' for p in PRODUCTS)
    tool_links = "".join(f'<li><a href="/tools/{t["slug"]}/">{e(t["short"])}</a></li>' for t in TOOLS)
    return f"""<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{canonical}">'}
<meta property="og:site_name" content="{e(CFG['name'])}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1F5F6B">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/fraunces-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/css/style.css">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/">{LOGO}<span>{e(CFG['name'])}</span></a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav"><span class="visually-hidden">Menu</span>{icon('menu', 24)}</button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul>{nav}<li><a class="btn btn-primary" href="{e(bundle_href)}">Get the bundle</a></li></ul>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <a class="logo" href="/" style="color:#fff">{LOGO}<span>{e(CFG['name'])}</span></a>
        <p style="margin-top:12px;max-width:30em">{e(CFG['tagline'])} Any currency, instant download, no subscriptions.</p>
        <p>Questions? <a href="mailto:{e(CFG['email'])}">{e(CFG['email'])}</a></p>
      </div>
      <div><h2>Spreadsheets</h2><ul>{shop_links}<li><a href="{product_url(BUNDLE['slug'])}">The bundle</a></li></ul></div>
      <div><h2>Free tools</h2><ul>{tool_links}<li><a href="/blog/">Blog</a></li></ul></div>
      <div><h2>Help</h2><ul><li><a href="/about/">About</a></li><li><a href="/contact/">Contact</a></li><li><a href="/refunds/">Refund policy</a></li><li><a href="/terms/">Terms</a></li><li><a href="/privacy/">Privacy</a></li></ul></div>
    </div>
    <div class="footer-bottom">© {date.today().year} {e(CFG['name'])}. Payments are processed by Lemon Squeezy. These spreadsheets are planning tools, not financial advice.</div>
  </div>
</footer>
{script_tags}
</body>
</html>
"""


def write(path, html):
    out = SITE / path.lstrip("/")
    if path.endswith("/"):
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


PAGES = []  # (path, priority) for sitemap


def page(path, *args, sitemap=True, priority="0.6", **kw):
    write(path, layout(path, *args, **kw))
    if sitemap:
        PAGES.append((path, priority))


# ---------------------------------------------------------------- home
def build_home():
    chips = [("all", "All")] + [(p["category"], p["category_label"]) for p in PRODUCTS]
    chip_html = "".join(f'<button type="button" class="chip" data-filter="{k}" aria-pressed="{"true" if k == "all" else "false"}">{e(v)}</button>'
                        for k, v in chips)
    rows = ""
    for s in DATA["situations"]:
        p = BY_SLUG[s["slug"]]
        rows += (f'<tr><td>{e(s["need"])}</td><td data-label="Best fit"><a href="{product_url(p["slug"])}">{e(p["name"])}</a></td>'
                 f'<td class="num" data-label="Price">{money(p["price"])}</td></tr>')
    bundle_list = "".join(f'<li><a href="{product_url(p["slug"])}">{e(p["name"])}</a></li>' for p in PRODUCTS)
    reviews = DATA.get("reviews") or []
    reviews_html = ""
    if reviews:  # only real reviews, added by hand to products.json
        reviews_html = ('<section class="section" aria-labelledby="reviews-h"><div class="wrap"><h2 id="reviews-h">What buyers say</h2><div class="grid grid-3">'
                        + "".join(f'<figure class="card-plain"><blockquote>{e(r["text"])}</blockquote><figcaption class="muted small">{e(r["name"])}, {e(r["product"])}</figcaption></figure>' for r in reviews)
                        + "</div></div></section>")
    bundle_href = BUNDLE["checkout_url"] if BUNDLE["checkout_url"].startswith("http") else product_url(BUNDLE["slug"])
    body = f"""
<section class="hero">
  <div class="wrap">
    <div>
      <span class="eyebrow">Spreadsheets for Excel &amp; Google Sheets</span>
      <h1>See your whole money picture in one place</h1>
      <p class="lead">Simple, ready-made spreadsheets for budgeting, paying off debt, saving, planning paychecks and tracking net worth. Type in your numbers and the dashboards do the rest.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="{e(bundle_href)}">Get the bundle · {money(BUNDLE['price'])}</a>
        <a class="btn btn-secondary" href="#sheets">Browse the spreadsheets</a>
      </div>
      <p class="hero-note">All six spreadsheets for {money(BUNDLE['price'])}, or from {money(min(p['price'] for p in PRODUCTS))} each. One-time price, no subscription.</p>
    </div>
    <div class="mockup">{picture(BUNDLE['slug'], BUNDLE['images'][0], width=1200, sizes="(min-width: 900px) 560px, 100vw", eager=True)}</div>
  </div>
</section>

<section class="trust" aria-label="Why buy here">
  <ul>{''.join(f'<li>{icon(i)}{e(t)}</li>' for i, t in TRUST)}</ul>
</section>

<section class="section" id="sheets" aria-labelledby="sheets-h">
  <div class="wrap">
    <div class="section-head">
      <h2 id="sheets-h">What do you need help with?</h2>
      <p class="muted">Pick a topic, or browse all six spreadsheets.</p>
    </div>
    <div class="filters" role="group" aria-label="Filter spreadsheets by topic">{chip_html}</div>
    <p id="filter-status" class="visually-hidden" aria-live="polite"></p>
    <div class="grid grid-3">
      {''.join(card(p) for p in PRODUCTS)}
    </div>
  </div>
</section>

<section class="section section-teal" aria-labelledby="bundle-h">
  <div class="wrap bundle-box">
    <div>
      <span class="eyebrow">Best value</span>
      <h2 id="bundle-h">Money Reset 2027: all six spreadsheets</h2>
      <p>Everything for a fresh start: plan your spending, clear your debt, fund your goals, map your paychecks, set aside freelance tax and track your net worth.</p>
      <ul>{bundle_list}</ul>
    </div>
    <div>
      <dl class="saving">
        <dt>Bought separately</dt><dd>{money(SEPARATE_TOTAL)}</dd>
        <dt>Bundle price</dt><dd>{money(BUNDLE['price'])}</dd>
        <dt class="total">You save</dt><dd class="total">{money(SAVING)} ({SAVING_PCT}%)</dd>
      </dl>
      <div class="btn-row"><a class="btn btn-primary" href="{e(bundle_href)}">Get the bundle · {money(BUNDLE['price'])}</a>
        <a class="btn btn-light" href="{product_url(BUNDLE['slug'])}">What's in the bundle</a></div>
      <p class="saving-note" style="margin-top:12px">Saving compares today's prices of the six spreadsheets with the bundle price.</p>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="how-h">
  <div class="wrap">
    <div class="section-head"><h2 id="how-h">How it works</h2></div>
    <ol class="steps">
      <li><h3>Buy and download</h3><p>Pay securely through Lemon Squeezy. Your download link arrives by email straight away.</p></li>
      <li><h3>Open it your way</h3><p>Open the .xlsx in Excel, or upload it to Google Drive and open it with Google Sheets.</p></li>
      <li><h3>Follow the Start Here tab</h3><p>Type your numbers into the yellow cells. Setup takes about five minutes.</p></li>
    </ol>
  </div>
</section>

<section class="section section-white" aria-labelledby="which-h">
  <div class="wrap">
    <div class="section-head"><h2 id="which-h">Which spreadsheet is right for me?</h2><p class="muted">Find your situation on the left.</p></div>
    <div class="table-wrap"><table class="stack-table">
      <thead><tr><th scope="col">If this sounds like you…</th><th scope="col">Best fit</th><th scope="col">Price</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </div>
</section>
{reviews_html}
<section class="section" aria-labelledby="faq-h">
  <div class="wrap narrow">
    <h2 id="faq-h">Questions</h2>
    {faq_html(DATA['common_faq'])}
  </div>
</section>

<section class="section section-white cta-band" aria-labelledby="cta-h">
  <div class="wrap narrow">
    <h2 id="cta-h">Start 2027 knowing where your money goes</h2>
    <p class="muted">Pick one spreadsheet, or get all six in the bundle.</p>
    <div class="btn-row"><a class="btn btn-primary" href="{e(bundle_href)}">Get the bundle · {money(BUNDLE['price'])}</a>
      <a class="btn btn-secondary" href="/tools/">Try a free calculator</a></div>
  </div>
</section>"""
    page("/", f"{CFG['name']}: budget & money spreadsheets",
         "Budget, debt payoff, savings, paycheck, freelancer and net worth spreadsheets for Excel and Google Sheets. Any currency, instant download.",
         body, priority="1.0")


# ---------------------------------------------------------------- product pages
def gallery(p):
    imgs = p["images"]
    main = picture(p["slug"], imgs[0], width=1200, sizes="(min-width: 900px) 600px, 100vw", eager=True)
    thumbs = ""
    if len(imgs) > 1:
        for i, img in enumerate(imgs):
            stem = Path(img["file"]).stem
            b = f"/assets/img/{p['slug']}/{stem}"
            thumbs += (f'<a href="{b}-1200.jpg" data-full="{b}-1200.jpg" data-full-webp="{b}-1200.webp" data-alt="{e(img["alt"])}" '
                       f'aria-current="{"true" if i == 0 else "false"}"><img src="{b}-800.jpg" width="88" height="66" alt="Show image {i + 1}: {e(img["alt"])}" loading="lazy"></a>')
        thumbs = f'<div class="thumbs" aria-label="More images">{thumbs}</div>'
    return f'<div><div class="gallery-main" id="gallery-main">{main}</div>{thumbs}</div>'


def product_jsonld(p):
    data = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["promise"],
            "image": [f"{BASE}/assets/img/{p['slug']}/{Path(i['file']).stem}-1200.jpg" for i in p["images"]],
            "brand": {"@type": "Brand", "name": CFG["name"]},
            "offers": {"@type": "Offer", "price": str(p["price"]), "priceCurrency": CFG["currency"],
                       "availability": "https://schema.org/InStock", "url": BASE + product_url(p["slug"])}}
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def build_product(p, is_bundle=False):
    common = [q for q in DATA["common_faq"] if q["q"].startswith(("Does it work in Google", "Which currency", "How do I get", "What if something"))]
    faq = p["faq"] + common + [{"q": "Is this financial advice?", "a": "No. It's a planning and tracking tool based on the numbers you enter."}]
    others = [o for o in PRODUCTS if o["slug"] != p["slug"]]
    if not is_bundle:
        i = [o["slug"] for o in PRODUCTS].index(p["slug"])
        others = [PRODUCTS[(i + 1) % len(PRODUCTS)], PRODUCTS[(i + 2) % len(PRODUCTS)]]
    tool = TOOL_BY_SLUG.get(p.get("tool") or "")
    if is_bundle:
        inside = ('<div class="grid grid-3">' + "".join(card(o) for o in PRODUCTS) + "</div>")
        inside_head = "The six spreadsheets inside"
        steps = ["Buy and get one download with all six .xlsx files by email.", "Open them in Excel, or upload them to Google Drive and open with Google Sheets.",
                 "Start with the Budget Planner, then add whichever others fit your situation. Each has its own Start Here tab."]
    else:
        inside = '<div class="inside-list">' + "".join(f'<div><h3>{e(x["title"])}</h3><p>{e(x["text"])}</p></div>' for x in p["inside"]) + "</div>"
        inside_head = "What's inside"
        steps = ["Buy and get your download link by email straight away.", "Open the .xlsx in Excel, or upload it to Google Drive and open with Google Sheets.", p["first_step"]]
    saving_box = f"""<dl class="saving" style="background:var(--teal-tint);border-color:var(--line);color:var(--ink)">
        <dt>Bought separately</dt><dd>{money(SEPARATE_TOTAL)}</dd><dt>Bundle price</dt><dd>{money(BUNDLE['price'])}</dd>
        <dt class="total" style="border-color:var(--line)">You save</dt><dd class="total" style="border-color:var(--line)">{money(SAVING)} ({SAVING_PCT}%)</dd></dl>"""
    tool_html = ""
    if tool:
        tool_html = f"""<div class="callout" style="margin-top:28px"><h3>Try it free first</h3>
        <p>Our free <a href="/tools/{tool['slug']}/">{e(tool['name'].lower())}</a> gives you a quick answer in your browser. The spreadsheet keeps the full picture, month by month.</p></div>"""
    cross = ""
    if not is_bundle:
        cross = f"""
<section class="section section-white" aria-labelledby="bundle-h">
  <div class="wrap two-col">
    <div>
      <h2 id="bundle-h">Get it in the bundle</h2>
      <p>{e(p['name'])} is one of the six spreadsheets in <a href="{product_url(BUNDLE['slug'])}">Money Reset 2027</a>. If more than one part of your money needs attention, the bundle costs less than buying three separately.</p>
      <div class="btn-row">{buy_button(BUNDLE, label=f"Get the bundle · {money(BUNDLE['price'])}")}<a class="btn btn-secondary" href="{product_url(BUNDLE['slug'])}">See the bundle</a></div>
    </div>
    <div>{saving_box}</div>
  </div>
</section>
<section class="section" aria-labelledby="more-h">
  <div class="wrap">
    <h2 id="more-h">You might also need</h2>
    <div class="grid">{''.join(card(o) for o in others)}</div>
  </div>
</section>"""
    label = "Bundle" if is_bundle else p["category_label"]
    price_line = (f'<span class="price">{money(p["price"])} <small>one-time, all six files</small></span>' if is_bundle
                  else f'<span class="price">{money(p["price"])} <small>one-time</small></span>')
    body = f"""
<nav class="breadcrumb wrap" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/#sheets">Spreadsheets</a></li><li aria-current="page">{e(short(p))}</li></ol></nav>
<div class="wrap product-top">
  {gallery(p)}
  <div class="buy-box">
    <span class="tag">{e(label)}</span>
    <h1 style="font-size:clamp(1.6rem,5vw,2.3rem)">{e(p['name'])}</h1>
    <p class="lead">{e(p['promise'])}</p>
    {price_line}
    {buy_button(p, extra_class="btn-block")}
    {trust_list()}
    {'' if is_bundle else f'<p class="small muted" style="margin:16px 0 0">Or get it with five more in the <a href="{product_url(BUNDLE["slug"])}">bundle for {money(BUNDLE["price"])}</a>.</p>'}
  </div>
</div>

<section class="section section-white" aria-labelledby="who-h">
  <div class="wrap two-col">
    <div><h2 id="who-h">Who it's for</h2><ul class="check-list">{''.join(f'<li>{e(w)}</li>' for w in p['who_for'])}</ul></div>
    <div><h2>How it works</h2><ol class="steps" style="grid-template-columns:1fr">{''.join(f'<li><p style="color:var(--ink)">{e(s)}</p></li>' for s in steps)}</ol>{tool_html}</div>
  </div>
</section>

<section class="section" aria-labelledby="inside-h">
  <div class="wrap"><h2 id="inside-h">{inside_head}</h2>{inside}
    <p class="small muted" style="margin-top:16px">Works in Microsoft Excel (Windows, Mac, web) and Google Sheets. No macros or add-ons. Use any currency. Example rows are clearly marked so you can delete them.</p></div>
</section>
{saving_box_section() if is_bundle else ''}
<section class="section {'section-white' if is_bundle else ''}" aria-labelledby="pfaq-h">
  <div class="wrap narrow"><h2 id="pfaq-h">Questions</h2>{faq_html(faq)}
    <div class="btn-row" style="margin-top:24px">{buy_button(p)}</div></div>
</section>
{cross}"""
    title = ("Money Reset 2027: all 6 money spreadsheets in one bundle" if is_bundle
             else f"{short(p)} Spreadsheet for Excel & Google Sheets")
    page(product_url(p["slug"]), title, p["seo_description"], body, active="sheets",
         og_image=f"/assets/img/{p['slug']}/og.jpg", extra_head=product_jsonld(p), priority="0.9")


def saving_box_section():
    return f"""<section class="section section-teal" aria-labelledby="save-h">
  <div class="wrap two-col">
    <div><h2 id="save-h">What you save</h2><p>Each spreadsheet is also sold on its own. Buying all six separately costs {money(SEPARATE_TOTAL)}; the bundle is {money(BUNDLE['price'])}.</p></div>
    <div><dl class="saving"><dt>Bought separately</dt><dd>{money(SEPARATE_TOTAL)}</dd><dt>Bundle price</dt><dd>{money(BUNDLE['price'])}</dd>
      <dt class="total">You save</dt><dd class="total">{money(SAVING)} ({SAVING_PCT}%)</dd></dl></div>
  </div>
</section>"""


# ---------------------------------------------------------------- tools
def tool_upsell(t):
    p = BY_SLUG[t["product"]]
    return f"""<div class="callout tool-upsell"><h3>Want the full picture?</h3>
<p>The <a href="{product_url(p['slug'])}">{e(p['name'])}</a> spreadsheet does this and more, month by month, and saves your numbers. {money(p['price'])}, works in Excel and Google Sheets.</p>
<div class="btn-row"><a class="btn btn-primary" href="{product_url(p['slug'])}">See the {e(short(p))}</a></div></div>"""


def tool_page(t, form_html, explain_html, faq):
    body = f"""
<nav class="breadcrumb wrap" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li><li><a href="/tools/">Free tools</a></li><li aria-current="page">{e(t['short'])}</li></ol></nav>
<div class="page-head wrap narrow"><h1>{e(t['name'])}</h1><p class="lead muted">{e(t['blurb'])} Free, no sign-up. Your numbers stay in your browser.</p></div>
<div class="wrap narrow" style="padding-bottom:48px">
  {form_html}
  {tool_upsell(t)}
  <div class="prose" style="padding:32px 0 0">{explain_html}</div>
  <h2>Questions</h2>
  {faq_html(faq + [{"q": "Is this financial advice?", "a": "No. It's a calculator based on the numbers you enter. For advice on your situation, talk to a qualified professional."}])}
</div>"""
    page(f"/tools/{t['slug']}/", f"{t['name'].capitalize()} (free) | {CFG['name']}", t["description"], body, active="tools",
         og_image=f"/assets/img/{t['product']}/og.jpg", scripts=("main", "tools"), priority="0.8")


def num_field(id_, label, hint="", value="", step="any", required=False):
    return (f'<div class="field"><label for="{id_}">{label}</label>'
            f'<input type="number" id="{id_}" inputmode="decimal" min="0" step="{step}" value="{value}"{" required" if required else ""}'
            f'{f" aria-describedby=\"{id_}-hint\"" if hint else ""}>'
            f'{f"<span class=\"hint\" id=\"{id_}-hint\">{hint}</span>" if hint else ""}</div>')


def build_tools():
    cards = ""
    for t in TOOLS:
        p = BY_SLUG[t["product"]]
        cards += f"""<article class="card"><div class="card-body"><h2 style="font-size:1.3rem"><a href="/tools/{t['slug']}/">{e(t['name'])}</a></h2>
<p>{e(t['blurb'])}</p><p class="small">Goes with: <a href="{product_url(p['slug'])}">{e(p['name'])}</a></p>
<div class="card-foot"><a class="btn btn-secondary" href="/tools/{t['slug']}/">Open calculator<span class="visually-hidden">: {e(t['name'])}</span></a></div></div></article>"""
    body = f"""<div class="page-head wrap"><h1>Free money calculators</h1><p class="lead muted">Quick answers, right in your browser. No sign-up, and nothing you type leaves your device.</p></div>
<section class="section" style="padding-top:24px"><div class="wrap"><div class="grid grid-3">{cards}</div></div></section>"""
    page("/tools/", f"Free budget, debt and savings calculators | {CFG['name']}",
         "Free debt snowball vs avalanche, 50/30/20 budget and savings goal calculators. No sign-up; your numbers stay in your browser.", body, active="tools", priority="0.8")

    # Debt snowball vs avalanche
    t = TOOL_BY_SLUG["debt-snowball-avalanche"]
    form = f"""<form id="debt-form" class="tool" novalidate>
  <fieldset><legend>Your debts</legend>
    <p class="small muted">Example debts are filled in. Replace them with yours, or remove the ones you don't need.</p>
    <div id="debt-rows" class="debt-rows"></div>
    <button type="button" id="add-debt" class="btn btn-secondary" style="margin-top:12px">+ Add a debt</button>
  </fieldset>
  {num_field("debt-extra", "Extra you can pay each month", "On top of all the minimum payments. Try 0 to see minimums only.", "150")}
  <button type="submit" class="btn btn-primary btn-block">Compare snowball and avalanche</button>
  <div id="debt-results" class="results" hidden aria-live="polite"></div>
</form>
<template id="debt-row-template"><div class="debt-row">
  <div class="field"><label>Debt name</label><input type="text" data-f="name" autocomplete="off"></div>
  <div class="field"><label>Balance</label><input type="number" data-f="balance" inputmode="decimal" min="0" step="any"></div>
  <div class="field"><label>Interest rate (APR %)</label><input type="number" data-f="apr" inputmode="decimal" min="0" step="any"></div>
  <div class="field"><label>Minimum / month</label><input type="number" data-f="min" inputmode="decimal" min="0" step="any"></div>
  <button type="button" class="remove">Remove</button>
</div></template>"""
    explain = """<h2>Snowball vs avalanche, in plain words</h2>
<p>Both methods have you pay the minimum on every debt each month and put any extra money toward one debt at a time. When a debt is paid off, its minimum payment is added to the extra and rolls on to the next one. The only difference is the order.</p>
<ul><li><strong>Snowball</strong> pays the smallest balance first. You clear whole debts sooner, which many people find motivating.</li>
<li><strong>Avalanche</strong> pays the highest interest rate first. It usually costs less interest in total.</li></ul>
<p>With a small gap between the two, pick the one you'll actually stick with. The calculator shows the real difference with your numbers.</p>"""
    tool_page(t, form, explain, [
        {"q": "Why do both methods sometimes finish in the same month?", "a": "The total you pay each month is the same under both methods; only the order changes. That often moves the finish date very little, while the interest total can differ more."},
        {"q": "What does \"minimum payments don't cover the interest\" mean?", "a": "If a debt's interest each month is more than you pay, the balance never falls. Raise the extra payment until it does."}])

    # 50/30/20
    t = TOOL_BY_SLUG["50-30-20-budget"]
    form = f"""<form id="split-form" class="tool" novalidate>
  {num_field("split-income", "Monthly take-home pay", "After tax, what actually lands in your account.", "3000", required=True)}
  <fieldset><legend>Your split (percent)</legend><div class="fields-2" style="grid-template-columns:repeat(3,1fr)">
    {num_field("split-needs-pct", "Needs %", "", "50")}{num_field("split-wants-pct", "Wants %", "", "30")}{num_field("split-savings-pct", "Savings %", "", "20")}
  </div></fieldset>
  <fieldset><legend>What you spend now (optional)</legend><div class="fields-2" style="grid-template-columns:repeat(3,1fr)">
    {num_field("split-needs-now", "Needs")}{num_field("split-wants-now", "Wants")}{num_field("split-savings-now", "Savings")}
  </div></fieldset>
  <button type="submit" class="btn btn-primary btn-block">Show my split</button>
  <div id="split-results" class="results" hidden aria-live="polite"></div>
</form>"""
    explain = """<h2>What is the 50/30/20 rule?</h2>
<p>It's a simple starting point for a budget: about half of your take-home pay goes to <strong>needs</strong> (housing, utilities, groceries, insurance, minimum debt payments), about 30% to <strong>wants</strong> (eating out, subscriptions, hobbies, travel) and about 20% to <strong>savings and extra debt payments</strong>.</p>
<p>It isn't a rule you have to hit exactly. In an expensive city, needs can easily take 60% or more. Use the percentages that fit your life and adjust as things change.</p>"""
    tool_page(t, form, explain, [
        {"q": "Are debt payments a need or savings?", "a": "Minimum payments are a need. Anything extra you pay to clear debt faster counts with savings."},
        {"q": "Should I use gross or take-home pay?", "a": "Take-home pay: the amount that actually reaches your account after tax and deductions."}])

    # Savings goal
    t = TOOL_BY_SLUG["savings-goal-calculator"]
    form = f"""<form id="savings-form" class="tool" novalidate>
  <div class="fields-2">
    {num_field("sav-target", "Savings goal", "The total you want to have.", "5000", required=True)}
    {num_field("sav-saved", "Already saved", "", "500")}
    {num_field("sav-monthly", "You can save each month", "", "250")}
    <div class="field"><label for="sav-date">Target date (optional)</label><input type="month" id="sav-date" placeholder="2027-12" aria-describedby="sav-date-hint"><span class="hint" id="sav-date-hint">Year and month, for example 2027-12.</span></div>
  </div>
  <button type="submit" class="btn btn-primary btn-block">Show my timeline</button>
  <div id="savings-results" class="results" hidden aria-live="polite"></div>
</form>"""
    explain = """<h2>How the timeline is worked out</h2>
<p>The calculator takes what's left to save, divides it by your monthly amount and rounds up to whole months, counting from this month. If you add a target date, it also works out the monthly amount you'd need to arrive on time and tells you whether you're on track.</p>
<p>It assumes no interest, so if your savings earn interest you'll get there a little sooner.</p>
<h2>Saving for more than one thing?</h2>
<p>Most people are: an emergency fund, a trip, a yearly bill. Sinking funds (setting aside a little each month for a bill you know is coming) take the sting out of big annual expenses.</p>"""
    tool_page(t, form, explain, [
        {"q": "What's a sinking fund?", "a": "Money you set aside bit by bit for an expense you know is coming, like car insurance or holidays, so it doesn't land all at once."}])


# ---------------------------------------------------------------- info pages
def prose_page(path, title, description, h1, html, sitemap=True):
    body = f'<div class="page-head wrap narrow"><h1>{e(h1)}</h1></div><div class="wrap narrow prose">{html}</div>'
    page(path, f"{title} | {CFG['name']}", description, body, sitemap=sitemap, priority="0.3")


def build_info():
    em = f'<a href="mailto:{e(CFG["email"])}">{e(CFG["email"])}</a>'
    prose_page("/about/", "About", f"About {CFG['name']}: who makes the spreadsheets and how they're built and tested.", "About Clear Money Sheets", f"""
<p class="lead">Clear Money Sheets makes simple, honest spreadsheets for everyday money jobs: budgeting, paying off debt, saving, planning paychecks, freelance income and net worth.</p>
<p>It's a one-person shop run by Nisal. The idea is simple: a good spreadsheet is still one of the best money tools there is. It's private, it works offline, it costs once rather than every month, and you can see exactly how every number is calculated.</p>
<h2>How the spreadsheets are made</h2>
<ul>
<li><strong>Built from a script.</strong> Each file is generated by code, so a fix or improvement goes into every copy.</li>
<li><strong>Checked for errors.</strong> Every formula is recalculated and checked before release. Each file ships with zero formula errors.</li>
<li><strong>Tested like a buyer would use it.</strong> Example data, awkward cases (a debt that never pays off, a bill due on the 31st, spending more than you earn) and numbers checked by hand.</li>
<li><strong>Made for Excel and Google Sheets.</strong> Only widely supported functions, no macros, no add-ons. Use any currency.</li>
<li><strong>Easy to start.</strong> Every file has a Start Here tab, yellow cells for your input, and example rows clearly marked for deletion.</li>
</ul>
<h2>What we don't do</h2>
<p>No income promises, no fake reviews, no countdown timers, no subscription. These are planning tools, not financial advice.</p>
<p>Questions or ideas for a spreadsheet you'd like to see? Email {em}.</p>""")

    prose_page("/contact/", "Contact", f"Contact {CFG['name']} for help with a spreadsheet, an order or a refund.", "Contact", f"""
<div class="card-plain"><p style="margin:0"><strong>Email:</strong> {em}</p><p class="muted" style="margin:6px 0 0">I usually reply within 1–2 days.</p></div>
<h2>To help me help you quickly</h2>
<ul><li>Which spreadsheet it's about.</li><li>Whether you're using Excel (Windows, Mac or web) or Google Sheets.</li>
<li>For order questions, your order number from the Lemon Squeezy receipt email.</li><li>A screenshot, if something looks wrong.</li></ul>
<p>Please don't send passwords or bank details. I'll never ask for them.</p>""")

    prose_page("/refunds/", "Refund policy", f"Refund policy for {CFG['name']} digital downloads.", "Refund policy", f"""
<p class="lead">Because these spreadsheets are instant digital downloads, I can't take them back once they're delivered. But if something doesn't work, email me and I'll fix it or refund you.</p>
<h2>How to ask</h2>
<ul><li>Email {em} with your order number and what's wrong.</li>
<li>I'll reply within 1–2 days, usually with a fix or a corrected file.</li>
<li>If I can't fix it, I'll refund you in full. Refunds go back to your original payment method through Lemon Squeezy, our payment provider.</li></ul>
<h2>Bought the wrong one?</h2>
<p>Email me and we'll sort it out, for example by switching you to the spreadsheet you meant to buy.</p>
<p class="small muted">Last updated {date.today().strftime('%d %B %Y')}.</p>""")

    prose_page("/terms/", "Terms", f"Terms of sale and use for {CFG['name']}.", "Terms", f"""
<p class="small muted">Last updated {date.today().strftime('%d %B %Y')}.</p>
<h2>Who we are</h2>
<p>{e(CFG['name'])} is run by {e(CFG['owner'])} in Sri Lanka. Contact: {em}.</p>
<h2>Buying</h2>
<p>Orders are processed by Lemon Squeezy, which acts as the merchant of record and handles payment, sales tax and VAT, and receipts. Prices are shown in {e(CFG['currency'])}. Any tax due is added at checkout. You'll get a download link by email when your payment is complete.</p>
<h2>Your licence</h2>
<ul><li>When you buy a spreadsheet, you may use it for your own personal or household finances, and for your own business if you're a freelancer or sole trader.</li>
<li>You may make copies and edit them for your own use.</li>
<li>You may not resell, share, give away or publish the files or edited versions of them, or offer them as templates of your own.</li></ul>
<h2>Not financial, tax or legal advice</h2>
<p>The spreadsheets and calculators are planning tools. Results depend entirely on the numbers you enter and the assumptions stated in each file. They aren't financial, tax, investment or legal advice. For decisions about your situation, talk to a qualified professional.</p>
<h2>If something doesn't work</h2>
<p>See the <a href="/refunds/">refund policy</a>. If a file doesn't work as described, I'll fix it or refund you.</p>
<h2>Liability</h2>
<p>To the extent the law allows, our total liability for any claim relating to a purchase is limited to the amount you paid for it. Nothing here limits rights you have under consumer law that can't be excluded.</p>
<h2>Changes</h2>
<p>These terms may be updated. The version that applies to your purchase is the one shown on the date you bought.</p>""")

    prose_page("/privacy/", "Privacy", f"Privacy policy for {CFG['name']}: no cookies, no tracking, and what happens when you buy.", "Privacy", f"""
<p class="small muted">Last updated {date.today().strftime('%d %B %Y')}.</p>
<h2>The short version</h2>
<p>This website doesn't use cookies, analytics or advertising trackers, and doesn't load third-party scripts or fonts. The free calculators run entirely in your browser: nothing you type is sent anywhere.</p>
<h2>Hosting</h2>
<p>The site is hosted on GitHub Pages. Like any web host, GitHub may log technical information such as your IP address to keep the service secure. See the <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub privacy statement</a>.</p>
<h2>When you buy</h2>
<p>Checkout is run by Lemon Squeezy. They collect your name, email, payment and billing details to process the order; see the <a href="https://www.lemonsqueezy.com/privacy">Lemon Squeezy privacy policy</a>. We receive order details (such as your name, email, country and what you bought) so we can deliver your files and help with support or refunds. We never see your full card details.</p>
<h2>When you email us</h2>
<p>We keep your emails so we can reply and help later if needed.</p>
<h2>What we don't do</h2>
<p>We don't sell or rent your information, and we don't add you to a mailing list without your permission.</p>
<h2>Your choices</h2>
<p>To see or delete the information we hold about you, email {em}.</p>
<h2>The spreadsheets themselves</h2>
<p>The files you buy are yours. Whatever you type into them stays on your computer, or in your own Google Drive if you use Google Sheets. It isn't sent to us.</p>""")


# ---------------------------------------------------------------- blog
def build_blog():
    tools = "".join(f'<li><a href="/tools/{t["slug"]}/">{e(t["name"])}</a></li>' for t in TOOLS)
    body = f"""<div class="page-head wrap narrow"><h1>Money guides</h1><p class="lead muted">Practical how-tos for budgeting, paying off debt and saving.</p></div>
<div class="wrap narrow prose"><div class="card-plain"><h2 style="margin-top:0">Guides coming soon</h2>
<p>The first guides are on their way. In the meantime, try a free calculator:</p><ul>{tools}</ul></div></div>"""
    page("/blog/", f"Money guides: budgeting, debt and saving how-tos | {CFG['name']}",
         "Practical, no-hype guides to budgeting, paying off debt, saving and tracking net worth with a spreadsheet.", body, active="blog", priority="0.5")

    # Template for future posts. Copy blog/_template.html to blog/<slug>/index.html and replace the {{...}} parts.
    p = PRODUCTS[0]
    body = f"""<article class="wrap narrow prose" style="padding-top:32px">
<nav class="breadcrumb" aria-label="Breadcrumb" style="padding:0 0 12px"><ol><li><a href="/">Home</a></li><li><a href="/blog/">Guides</a></li><li aria-current="page">{{{{SHORT_TITLE}}}}</li></ol></nav>
<h1>{{{{TITLE}}}}</h1>
<p class="post-meta">{{{{DATE, e.g. 2 December 2026}}}} · {{{{N}}}} min read</p>
<p class="lead">{{{{INTRO: 1–2 sentences saying what the reader will be able to do after reading.}}}}</p>
<h2>{{{{SECTION HEADING}}}}</h2>
<p>{{{{Body text. 600–900 words in total. Useful, specific, no income promises.}}}}</p>
<div class="post-cta"><h2 style="margin-top:0;font-size:1.3rem">{{{{PRODUCT CTA HEADING, e.g. Do this in a spreadsheet}}}}</h2>
<p>{{{{One sentence on how the matching spreadsheet helps.}}}}</p>
<a class="btn btn-primary" href="/products/{{{{PRODUCT_SLUG}}}}/">See the {{{{PRODUCT NAME}}}}</a></div>
<!-- Pinterest image (1000x1500) for this post: /assets/img/blog/{{{{POST_SLUG}}}}-pin.jpg, also referenced in feed.xml -->
</article>"""
    page("/blog/_template.html", "{{TITLE}} | " + CFG["name"], "{{DESCRIPTION: 150 characters or fewer}}", body, active="blog",
         sitemap=False, noindex=True)


def build_404():
    body = f"""<div class="page-head wrap narrow" style="padding-bottom:56px"><h1>Page not found</h1>
<p class="lead muted">That page doesn't exist, or it has moved.</p>
<div class="btn-row"><a class="btn btn-primary" href="/">Go to the home page</a><a class="btn btn-secondary" href="/#sheets">Browse the spreadsheets</a></div></div>"""
    write("/404.html", layout("/404.html", f"Page not found | {CFG['name']}", "Page not found.", body, noindex=True))


def build_meta_files():
    urls = "".join(f"<url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>\n" for p, pr in PAGES)
    (SITE / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /blog/_template.html\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")


def main():
    old = SITE / "images"  # the first one-page version's images
    if old.exists():
        shutil.rmtree(old)
    build_images()
    build_favicons()
    build_home()
    for p in PRODUCTS:
        build_product(p)
    build_product(BUNDLE, is_bundle=True)
    build_tools()
    build_info()
    build_blog()
    build_404()
    build_meta_files()
    print(f"Built {len(PAGES)} pages + 404 + blog template. Bundle saving: {money(SAVING)} ({SAVING_PCT}%) vs {money(SEPARATE_TOTAL)} separately.")
    if TODO_LINKS:
        print("Checkout links still LINK_TODO (shown as 'Coming soon'):")
        for slug, name in TODO_LINKS:
            print(f"  - {name} ({slug})")


if __name__ == "__main__":
    main()
