# Christmas Oathbreaker Challenge — GitHub Pages

This repo publishes the existing one-page site and builds a static `cards-index.json` from MTGJSON daily. No running backend or player exchange-rate input.

## Installation
1. Extract the ZIP, then upload **all files and the `.github/workflows/pages.yml` directory** to a public GitHub repository, keeping their folder paths.
2. Open **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions** (not *Deploy from a branch*).
3. Go to **Actions → Publish site and refresh MTGJSON prices → Run workflow**. The initial build may take a few minutes because it downloads large compressed datasets.
4. In **Settings → Pages**, keep or enter the existing custom domain (`oathbreaker.yourdomain.com`). Preserve the DNS CNAME already configured and enable Enforce HTTPS when available.
5. Visit your site and run a deck check. The website loads the built `cards-index.json` once and checks cards locally in JavaScript.

## Pricing rules
Minimum Cardmarket normal (non-foil) **retail reference price** across eligible English paper printings, excluding promo/alternative/foil-only/digital printings. The scheduled job automatically converts EUR to GBP using Frankfurter's reference FX rate. The JSON records the index generation and FX dates and the chosen printing set per card. Basic lands are always £0.00.

These are **market-guide reference prices**, not guaranteed currently purchasable listings or condition-specific live offers. An unpriced card is reported as unpriced, not as free. If a data update fails, the previous published site stays active; the interface displays the price snapshot date. Mass-wipe classification and infinite-command-zone combos remain subject to manual review.
