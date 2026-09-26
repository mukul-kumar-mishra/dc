# DestroCorp website — destrocorp.com
# Static only. Zero npm dependencies, zero external requests, zero backend.
# Deploy: copy the contents of website/ to any static host (Caddy, nginx, Cloudflare Pages, S3+CF).

## Structure
website/
  index.html  about.html  contact.html  privacy.html  terms.html
  refunds.html  shipping.html  cookies.html  security.html  accessibility.html
  404.html  robots.txt  sitemap.xml  manifest.webmanifest
  brands/kirvyn.html  brands/auditscan.html  brands/buildopsy.html
  assets/css/main.css  assets/js/main.js  assets/img/logo.svg, logo-512.png, og-cover.png
  assets/img/brands/ (copied from pulseflow + auditscan app folders)

## Before go-live
1. Add real company details to Contact/About + legal pages when ready
   (address, grievance officer name, registration numbers for payment KYC).
2. Mirror the 6 legal pages in the footer of kirvyn.com, auditscan.sh, buildopsy.com
   (identical company info — payment providers check this).
3. Submit sitemap in Google Search Console + Bing Webmaster Tools.
4. Verify: https, HSTS, no mixed content, 404 returns 404 status.

## Theme
- Single maroon + gold light theme. No toggle, no theme JS.

## Caddy snippet (add to existing Caddyfile)
destrocorp.com, www.destrocorp.com {
    root * /var/www/destrocorp
    file_server
    encode gzip zstd
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=(self), payment=()"
        Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; font-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self' mailto:"
    }
    handle_errors { rewrite * /404.html }
    redir /index.html / permanent
}

## License / IP hygiene (read this)
- All HTML/CSS/JS in website/ (except assets/img/brands/) is hand-written for
  DestroCorp. No third-party frameworks, fonts, or JS libraries — so there is
  nothing to attribute, nothing that phones home, and nothing that can bill you.
- assets/img/brands/* are COPIES of your own product logos (kirvyn, auditscan)
  plus the official buildopsy.com logo (downloaded from buildopsy.com/images/logo.png
  for use on this parent-company page — replace if their brand rules require it).
  Originals stay in their repos; these copies keep destrocorp.com self-contained.
- System font stack only (no Google Fonts) = no cross-border font fetch = GDPR-clean + fastest load.
- If you later add analytics: use a self-hosted, cookieless option (e.g. Plausible
  self-hosted, MIT licence) behind the existing opt-in consent manager. Never add
  Google Analytics without a DPA + explicit consent + IP anonymisation.
