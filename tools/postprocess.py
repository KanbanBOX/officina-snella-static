#!/usr/bin/env python3
"""Clean up a wget mirror of www.officinasnella.com for static hosting.

- strips query-string suffixes wget baked into asset filenames
  (e.g. jquery.js@ver=1.12.4 -> jquery.js, style.css@ver=4.9.34.css -> style.css)
- removes WordPress head cruft that needs a live backend (feeds, oEmbed, xmlrpc, emoji)
- removes the GDPR Cookie Compliance banner and its assets
- points the Google Fonts stylesheet to the self-hosted copy in fonts/
- replaces the Google Maps embed on the contact page with a link
- removes backend-only, empty and outdated pages; fixes or unwraps links to pages that don't exist
- makes the WordPress 404 page (fetched by build.sh) usable as GitHub Pages' 404.html
- turns ".../index.html" links into directory links
- rewrites leftover absolute links to the original domain into relative ones
"""
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "site")
DOMAIN_RE = r"https?:(?:\\?/){2}(?:www\.)?officinasnella\.com"

# name.ext@query[.html|.css] -> name.ext
ASSET_SUFFIX_RE = re.compile(
    r"(\.(?:js|css|woff2?|ttf|eot|svg|png|jpe?g|gif))@[^\"'\s)#<>]*?(?:\.html|\.css)?(?=[\"'\s)#<>])"
)
# fonts served as text/html get ".html" appended by wget --adjust-extension
FONT_HTML_RE = re.compile(r"(\.(?:woff2?|ttf|eot|otf))\.html(?=$|[\"'\s)#?<>])")
HEAD_CRUFT = [
    r'<link rel=["\'](?:pingback|EditURI|wlwmanifest|https://api\.w\.org/|shortlink)["\'][^>]*>\s*',
    r'<link rel=["\']alternate["\'] type=["\'](?:application/rss\+xml|application/json\+oembed|text/xml\+oembed)["\'][^>]*>\s*',
    r'<link rel=["\']dns-prefetch["\'] href=["\'](?:https?:)?//s\.w\.org/?["\'][^>]*>\s*',
    r'<meta name=["\']generator["\'][^>]*>\s*',
    r'<script type=["\']text/javascript["\']>\s*window\._wpemojiSettings.*?</script>\s*',
    r'<style type=["\']text/css["\']>\s*img\.wp-smiley.*?</style>\s*',
]
# GDPR Cookie Compliance plugin: banner, settings modal, CSS and JS (the static site sets no cookies)
COOKIE_BANNER = [
    r'<link rel=["\']stylesheet["\'] id=["\']moove_gdpr_frontend-css["\'][^>]*>\s*',
    r'<style id=["\']moove_gdpr_frontend-inline-css["\'].*?</style>\s*',
    r'\s*<!--copyscapeskip-->.*?<!--/copyscapeskip-->',
    r'<script type=["\']text/javascript["\']>\s*/\* <!\[CDATA\[ \*/\s*var moove_frontend_gdpr_scripts.*?</script>\s*',
    r'<script type=["\']text/javascript["\'] src=["\'][^"\']*gdpr-cookie-compliance/[^"\']*["\']>\s*</script>\s*',
    r'<script type=["\']text/javascript["\']>\s*var gdpr_consent__strict.*?</script>\s*',
]
MAPS_LINK = "https://www.google.com/maps/search/?api=1&amp;query=Simal+Business+Center%2C+Via+Zamenhof+817%2C+36100+Vicenza"
# pages that only make sense with the WordPress backend, are empty, or are outdated
REMOVED_PAGES = [
    "event-registration", "transactions", "thank-you", "registration-cancelled", "eventi",
    "tag", "category/senza-categoria", "sitecal", "sedi-dei-corsi",
]
# links to the original domain that moved or were malformed in the WordPress content
MOVED_LINKS = {
    "/calendario-dei-corsi/": "corsi/calendario-dei-corsi/",
    "/lancio-del-progetto-officina-snella/http/www.facebook.com/OfficinaSnella": "https://www.facebook.com/OfficinaSnella",
}
COOKIE_PLUGIN_DIR ="wp-content/plugins/gdpr-cookie-compliance"


with open(os.path.join(os.path.dirname(__file__), "shortlinks.json")) as fh:
    SHORTLINKS = json.load(fh)
# "foo.html" files that duplicate an existing "foo/index.html"
DUPLICATES = []


def find_duplicates():
    for dirpath, _, files in os.walk(ROOT):
        for f in files:
            p = os.path.join(dirpath, f)
            if f.endswith(".html") and os.path.isfile(os.path.join(p[:-5], "index.html")):
                DUPLICATES.append(os.path.relpath(p, ROOT))


def clean_name(name):
    name = FONT_HTML_RE.sub(r"\1", name)
    m = re.match(r"(.+?\.(?:js|css|woff2?|ttf|eot|svg|png|jpe?g|gif))@.*$", name)
    return m.group(1) if m else name


def rename_assets():
    for dirpath, _, files in os.walk(ROOT):
        for f in files:
            new = clean_name(f)
            if new != f:
                src, dst = os.path.join(dirpath, f), os.path.join(dirpath, new)
                if os.path.exists(dst):
                    os.remove(src)
                else:
                    os.rename(src, dst)


def relpath_to_root(path):
    rel = os.path.relpath(ROOT, os.path.dirname(path))
    return "" if rel == "." else rel + "/"


def fix_text(path, text):
    text = ASSET_SUFFIX_RE.sub(r"\1", text)
    text = FONT_HTML_RE.sub(r"\1", text)
    if not path.endswith(".html"):
        return text
    for pat in HEAD_CRUFT + COOKIE_BANNER:
        text = re.sub(pat, "", text, flags=re.S | re.I)
    prefix = relpath_to_root(path)
    if os.path.relpath(path, ROOT) == "404.html":
        # served at any URL, so it needs root-relative links; it was fetched raw (not via wget)
        prefix = "/"
        text = re.sub(r'((?:href|src)=["\'])' + DOMAIN_RE + r'/?', r"\1/", text)
        text = re.sub(r'((?:href|src)=["\']/[^"\'?]*)\?ver=[^"\']*', r"\1", text)
        text = text.replace("Error 404 - Page Not Found", "Errore 404 - Pagina non trovata")
        text = text.replace("The page you are looking for could not be found.", "La pagina che cerchi non esiste.")
    # Google Fonts -> self-hosted copy in static/fonts (copied to the site root by build.sh)
    text = re.sub(
        r'<link href=["\']https://fonts\.googleapis\.com/css\?family=Droid\+Sans[^"\']*["\']',
        f"<link href='{prefix}fonts/droid-sans.css'",
        text,
    )
    # images still linked to the old staging host (now offline) -> local copy
    text = re.sub(r'(src=["\'])https?://officinasnella\.nextep\.it/', lambda m: m.group(1) + prefix, text)
    # Google Maps embed (loads Google on page view) -> plain link
    text = re.sub(
        r'<iframe[^>]*src="https://www\.google\.com/maps/embed[^"]*"[^>]*></iframe>(?:<br />\s*<small></small>)?',
        '<a href="' + MAPS_LINK + '" target="_blank" rel="noopener"><strong>Apri la mappa su Google Maps</strong></a>',
        text,
    )
    # ?p=NN shortlinks (saved by wget as index.html@p=NN.html) -> real page
    text = re.sub(
        r'(["\'])(?:\.\./)*index\.html@p=(\d+)\.html(?=["\'#])',
        lambda m: m.group(1) + prefix + SHORTLINKS.get(m.group(2), ""),
        text,
    )
    # slash-less duplicates (e.g. corsi/corsi-per-team-di-lavoro.html) -> directory page
    def dedupe(m):
        target = os.path.relpath(os.path.normpath(os.path.join(os.path.dirname(path), m.group(2))), ROOT)
        return m.group(1) + prefix + target[:-5] + "/" if target in DUPLICATES else m.group(0)
    text = re.sub(r'(href=["\'])([^"\'#:]+\.html)(?=["\'#])', dedupe, text)
    # absolute links to pages that exist in the mirror -> relative
    def abs_to_rel(m):
        target = m.group(1)
        local = os.path.join(ROOT, target.lstrip("/"))
        if os.path.isfile(os.path.join(local, "index.html")) or os.path.isfile(local):
            return f'href="{prefix}{target.lstrip("/")}"' if target.strip("/") else f'href="{prefix or "./"}"'
        return m.group(0)
    text = re.sub(r'href="' + DOMAIN_RE + r'(/[^"#?]*)?"', lambda m: abs_to_rel(m) if m.group(1) is not None else f'href="{prefix or "./"}"', text)
    # remaining links to the original domain: moved pages get their new target, the rest
    # (pages that don't exist in the mirror, e.g. yearly archives) become plain text
    def moved_or_unwrap(m):
        target = MOVED_LINKS.get(m.group(2))
        if target is None:
            return m.group(4)
        if not target.startswith("http"):
            target = prefix + target
        return m.group(1) + target + m.group(3) + m.group(4) + "</a>"
    text = re.sub(
        r'(<a\s[^>]*href=["\'])' + DOMAIN_RE + r'(/[^"\'#?]*)(["\'][^>]*>)(.*?)</a>',
        moved_or_unwrap,
        text,
        flags=re.S,
    )
    # foo/index.html -> foo/  ;  index.html -> ./
    text = re.sub(r'(href=["\'])((?:[^"\'#:]*/)?)index\.html(?=["\'#])', lambda m: m.group(1) + (m.group(2) or "./"), text)
    return text


def main():
    for page in REMOVED_PAGES:
        shutil.rmtree(os.path.join(ROOT, page), ignore_errors=True)
    rename_assets()
    find_duplicates()
    for dirpath, _, files in os.walk(ROOT):
        for f in files:
            if not f.endswith((".html", ".css", ".js")):
                continue
            p = os.path.join(dirpath, f)
            with open(p, encoding="utf-8", errors="surrogateescape") as fh:
                text = fh.read()
            new = fix_text(p, text)
            if new != text:
                with open(p, "w", encoding="utf-8", errors="surrogateescape") as fh:
                    fh.write(new)
    for f in os.listdir(ROOT):
        if re.fullmatch(r"index\.html@p=\d+\.html", f):
            os.remove(os.path.join(ROOT, f))
    for dup in DUPLICATES:
        os.remove(os.path.join(ROOT, dup))
    shutil.rmtree(os.path.join(ROOT, COOKIE_PLUGIN_DIR), ignore_errors=True)
    # GitHub Pages: don't run Jekyll, serve files as-is
    open(os.path.join(ROOT, ".nojekyll"), "w").close()


if __name__ == "__main__":
    main()
