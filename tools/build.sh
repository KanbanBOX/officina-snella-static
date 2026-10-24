#!/usr/bin/env bash
# Rebuild the static mirror of www.officinasnella.com into ./docs
set -euo pipefail
cd "$(dirname "$0")/.."

BASE=https://www.officinasnella.com
OUT=docs
URLS=$(mktemp)
trap 'rm -f "$URLS"' EXIT

# the domain now points to GitHub Pages: the WordPress origin must be reached through /etc/hosts
if ! curl -fsS -o /dev/null "$BASE/wp-json/"; then
  echo "WordPress non raggiungibile su $BASE (il DNS punta a GitHub Pages)." >&2
  echo "Aggiungi temporaneamente a /etc/hosts:  3.123.199.162 www.officinasnella.com" >&2
  exit 1
fi

# seed: home page, every page/post/category/tag from the WP REST API, plus date/author archives
echo "$BASE/" > "$URLS"
for t in pages posts categories tags; do
  curl -fsS "$BASE/wp-json/wp/v2/$t?per_page=100&_fields=link" \
    | python3 -c 'import json,sys; [print(x["link"]) for x in json.load(sys.stdin)]' >> "$URLS"
done
for u in 2012/02/ 2012/07/ 2013/02/ 2013/11/ author/admin/ author/officinasnella/; do
  echo "$BASE/$u" >> "$URLS"
done

# post id -> path, used to rewrite ?p=NN shortlinks in the menu
for t in pages posts; do
  curl -fsS "$BASE/wp-json/wp/v2/$t?per_page=100&_fields=id,link"; echo
done | python3 -c '
import json, re, sys
d = {}
for line in sys.stdin:
    if line.strip():
        for x in json.loads(line):
            d[str(x["id"])] = re.sub(r"^https?://www\.officinasnella\.com/", "", x["link"])
json.dump(d, open("tools/shortlinks.json", "w"), indent=1, sort_keys=True)'

rm -rf "$OUT"
# wget exits 8 on the few bogus URLs it extracts from inline JS templates; that's expected
wget --mirror --page-requisites --convert-links --adjust-extension --restrict-file-names=windows \
  --no-host-directories --domains=www.officinasnella.com,officinasnella.com --no-parent \
  -e robots=off --wait=0.2 --no-verbose \
  --reject-regex='(xmlrpc\.php|wp-json|/feed/|wp-login|replytocom|/comments/|wlwmanifest|wp-admin|%7B|%5C|/http/)' \
  -i "$URLS" -P "$OUT" || [ $? -eq 8 ]

# self-hosted assets that replace third-party ones (e.g. Google Fonts)
cp -r static/. "$OUT/"
python3 tools/postprocess.py "$OUT"
[ -f CNAME ] && cp CNAME "$OUT/CNAME"
echo "Built $(find "$OUT" -name '*.html' | wc -l) pages in $OUT/"
