# Clear Money Sheets — site design brief

Status: draft for Nisal's OK (17 Oct 2026). Nothing is built yet.

## 1. What the research showed

Reviewed: Easlo (Notion templates), Simple Sheets (Excel templates), Vertex42 (spreadsheet library since 2003),
Thomas Frank templates (Notion), Aspire Budget (Google Sheets budget), Tiller (finance spreadsheets),
plus several Gumroad budget-sheet listings.

**Worth copying as patterns (not design or text):**
- **One promise, one button per block.** Easlo uses the same pattern for every offer: heading, one line, one CTA. That makes the page easy to scan.
- **Ownership and privacy as trust.** Tiller and Aspire both stress that the spreadsheet is yours, your data stays in your own file, and there's no bank login. That's true of our files too, so we can say it.
- **Compatibility stated plainly.** The weaker Gumroad listings bury it, or work in only one app. "Works in Excel and Google Sheets" is a real advantage for us, so it goes at the top.
- **Real screenshots and a comparison table.** Aspire's report screenshots and its comparison table answer "is this for me?" without any hype.
- **Free tools that lead to the paid one.** Thomas Frank's free templates each point to the paid version. Vertex42's financial calculators bring in search traffic.
- **Buy button repeated after each major section.** Tiller and Simple Sheets both do this.
- **Policies linked in the footer.** Refund, privacy and terms are always one click away. Payment processors check for them.

**Avoided on purpose (breaks our rules, or erodes trust):**
- Press-logo walls, install counts, star ratings and testimonials. We have none yet, and inventing them is off-limits.
- Value stacking with inflated "total value" numbers, countdown timers, and email gates before you can see products.

## 2. Audience
- People starting a New Year money reset (late Dec–Jan): mostly 22–45, on a phone, coming from Pinterest or Google.
- Comfortable with spreadsheets but don't want to build one. Want something that looks tidy and works on the first try.
- Worldwide, any currency. Many are cautious about apps that ask for bank logins.
- Sub-groups: people paid every two weeks, freelancers, and people paying off debt.

**What they need to see in 10 seconds:** what it is, that it works in their app, what it costs, that the download is instant, and that it's safe to pay.

## 3. Look and feel
Calm, warm, organised: "a tidy kitchen table", not "fintech dashboard". Lots of sand-coloured space, teal for structure, amber only where we want a click. Real product screenshots do the selling. No stock photos, no illustrations of features the files don't have.

### Colour palette (matches the product images)
| Token | Hex | Use |
|---|---|---|
| teal (brand) | `#1F5F6B` | headings, links, header/footer, secondary buttons |
| teal-dark | `#164650` | hover states, footer background |
| teal-tint | `#E3EEF0` | filter chips, table header, info boxes |
| sand (background) | `#F7F4EE` | page background, alternating sections |
| white | `#FFFFFF` | cards, product images |
| amber (accent) | `#E0A458` | primary Buy/CTA button background, small highlights |
| ink | `#1C2B2E` | body text; also the text colour on amber buttons |
| muted | `#55666A` | secondary text |
| line | `#E2DCCF` | borders, dividers |

Contrast checks (calculated): ink on sand 13.3:1, teal on sand 6.6:1, white on teal 7.2:1, ink on amber 6.7:1, muted on sand 5.5:1, teal on teal-tint 6.1:1 (all pass WCAG AA).
**Amber is never used for text** (only 2.2:1 on white). It is always a background with ink text on it.

### Fonts (free, self-hosted woff2, Latin subset only, about 70 KB total)
- Headings: **Fraunces** (warm serif, weight 600). Gives personality without fuss.
- Body and UI: **Inter** (400/600). Easy to read on phones, and its numbers line up in tables.
- Fallbacks: Georgia / system-ui. Fonts load with `font-display: swap`, so text never waits on them.
- Self-hosted rather than linked from Google Fonts: faster, and no third-party requests (simpler privacy page).

### Components
- Buttons: 48px minimum height, 10px radius. Primary = amber with ink text. Secondary = teal outline.
- Product card: white, 12px radius, real cover image (4:3), name, one-line benefit, price, "See details" and "Buy" buttons.
- Filter chips: real `<button>`s with `aria-pressed`, usable by keyboard. "All" selected by default.
- FAQ: native `<details>/<summary>`, which is keyboard-accessible with no JavaScript.
- Trust strip: 4 short items with simple line icons (inline SVG).
- Layout: max width 1120px, 16px side gutter on mobile. Single column at 375px, 2 columns at 768px, 3 columns at 1280px.

## 4. Data and build
- `site/products.json` is the single source for every product: slug, name, short promise, category, price, regular price, Lemon Squeezy URL (`LINK_TODO` until real), images, who it's for, what's inside, FAQ, and matching free tool.
- `site/build.py` (Python standard library + Pillow, both already installed) generates every HTML page, sitemap.xml and the WebP+JPEG images from `products/*/images`. Run `python site/build.py`, then commit and push (with your OK).
- **Bundle saving** = sum of the six products' current prices minus the bundle price, calculated by build.py. At today's launch prices: 9+9+5+7+9+5 = USD 44 vs USD 19, a saving of USD 25 (57%). I'll compare launch price to launch price rather than the bigger "regular" totals, so the number is honest.
- Any Buy button still on `LINK_TODO` shows as "Coming soon" (disabled), so nothing links to a dead page.

## 5. Pages and section order

**Home** `/`
1. Header: logo, Products, Free tools, Blog, About, plus a "Get the bundle" button. Collapses to a menu button on mobile.
2. Hero: one promise ("See your whole money picture in one spreadsheet. Excel or Google Sheets, any currency."), a sub-line, a "Get the bundle — USD 19" button and a "Browse the sheets" link, and the real bundle mockup image.
3. Trust strip: Works in Excel + Google Sheets · Any currency · Instant download · Secure checkout by Lemon Squeezy.
4. "What do you need help with?" filter chips (All, Budget, Debt, Savings, Paycheck, Freelance, Net worth) above the product grid of 6 cards.
5. Bundle section: what's included, the price, and the calculated saving.
6. How it works: 1. Buy and get the download link by email. 2. Open in Excel or upload to Google Sheets. 3. Follow the Start Here tab (about 5 minutes).
7. "Which sheet is right for me?" table: a row for each situation ("I'm paid every two weeks", "I have several debts", and so on), the sheet that fits, and its price.
8. Reviews placeholder: hidden until real reviews exist (nothing fake).
9. FAQ accordion: Google Sheets? Mac? Currency? Updates? Refunds? Is my data private? Not financial advice.
10. Final CTA, then footer.

**Product page** `/products/<slug>/` (×7, including the bundle)
1. Breadcrumb.
2. Gallery (main image + thumbnails, real images) beside name, promise, price, Buy button, and trust mini-list.
3. Who it's for.
4. What's inside (per tab).
5. How it works (3 steps).
6. Free tool link, where there's a matching one.
7. FAQ.
8. "Get it in the bundle" cross-sell with the saving.
9. Other sheets (2 cards).
10. Footer.

**Free tools** `/tools/`, a tool index plus one page per calculator, so each can rank in search:
- `/tools/debt-snowball-avalanche/`: compares both methods month by month (the same logic as the paid sheet) → Debt Payoff Calculator.
- `/tools/50-30-20-budget/` → 2027 Budget Planner.
- `/tools/savings-goal-calculator/` → Savings Goals Tracker.
- Each has a "not financial advice" note. Everything runs in the browser and nothing is sent anywhere.

**About** `/about/`: who makes the sheets and how they're built and tested (formula-checked, tested in Excel, LibreOffice and Google Sheets). Honest and short.
**Contact** `/contact/`: email (address to be confirmed), response time, what to include. A `mailto:` link only, no form service.
**Refund policy** `/refunds/`: same wording as listing.md (digital download; if it doesn't work, I fix it or refund you).
**Terms** `/terms/`: personal-use licence, no resale, not financial advice, Lemon Squeezy as merchant of record.
**Privacy** `/privacy/`: no cookies or trackers on the site, no data collected by the site; checkout data is handled by Lemon Squeezy (linked).
**Blog** `/blog/`: index (empty state: "Guides coming soon" with links to the free tools) plus `blog/_template.html` for future posts (article layout, product CTA box, Pinterest image slot).
**Also:** `404.html`, `sitemap.xml`, `robots.txt`, favicon (teal "C" mark, SVG + PNG), and Open Graph image per page (product cover; home uses the bundle image).

## 6. Quality checks before showing you
- Screenshots at 375 / 768 / 1280 px of every page type, with no horizontal scrolling.
- Page weight under 300 KB excluding images. Images in WebP with JPEG fallback and lazy-loaded below the fold.
- Keyboard pass (Tab through the filters, FAQ and gallery). All images have alt text. Headings in order.
- Calculators checked against hand-worked examples, with the debt tool matched to the paid sheet's numbers.
- Link check: no broken internal links. Each `LINK_TODO` listed in HANDOFF.md.
