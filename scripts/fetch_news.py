"""Builds news.json for Setu. Runs on GitHub Actions every 3 hours.
Fetching on the server avoids browser CORS limits and needs no API keys."""
import json, re, time, urllib.parse, urllib.request, email.utils, datetime, html
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (compatible; SetuNewsBot/1.0; +https://myselfsislam.github.io/setu/)"}
NOW = datetime.datetime.now(datetime.timezone.utc)

# Topic ids match NTOPIC in index.html
TOPICS = {
    "n50":    '"Nifty 50" OR Sensex',
    "nn50":   '"Nifty Next 50"',
    "mid":    'midcap India stocks',
    "small":  'smallcap India stocks',
    "us":     '"S&P 500"',
    "baf":    '"balanced advantage fund" OR "hybrid fund" India',
    "short":  '"debt fund" OR "bond yields" India',
    "liquid": '"liquid fund" OR "debt fund" India',
    "fd":     '"fixed deposit" rates OR "FD rates"',
    "gold":   'gold price India',
    "fx":     'rupee pound OR "GBP INR" OR rupee sterling',
    "mf":     '"mutual fund" India SIP',
}
INDIA_TAX = 'NRI (CBDT OR "income tax" OR RBI OR SEBI OR "Income-tax Act")'

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def gnews(query, days, limit, region="IN"):
    q = f"{query} when:{days}d"
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q) +
           f"&hl=en-{region}&gl={region}&ceid={region}:en")
    root = ET.fromstring(get(url))
    out, seen = [], set()
    for it in root.iter("item"):
        title = html.unescape((it.findtext("title") or "").strip())
        src_el = it.find("source")
        src = (src_el.text or "").strip() if src_el is not None else ""
        if src and title.endswith(" - " + src):
            title = title[: -(len(src) + 3)]
        key = re.sub(r"\W+", " ", title.lower())[:70]
        if not title or key in seen:
            continue
        seen.add(key)
        try:
            at = email.utils.parsedate_to_datetime(it.findtext("pubDate")).astimezone(datetime.timezone.utc)
        except Exception:
            continue
        if (NOW - at).days > days:
            continue
        out.append({"t": title, "u": it.findtext("link"), "d": src, "at": at.strftime("%Y-%m-%dT%H:%M:%SZ")})
    out.sort(key=lambda a: a["at"], reverse=True)
    return out[:limit]

def govuk():
    url = ("https://www.gov.uk/api/search.json?filter_organisations=hm-revenue-customs"
           "&filter_organisations=hm-treasury&order=-public_timestamp&count=8"
           "&fields=title&fields=link&fields=public_timestamp")
    data = json.loads(get(url))
    return [{"t": r["title"], "u": "https://www.gov.uk" + r["link"], "d": "GOV.UK",
             "at": r.get("public_timestamp", "")} for r in data.get("results", []) if r.get("title") and r.get("link")][:6]

def main():
    try:
        old = json.load(open("news.json"))
    except Exception:
        old = {}
    result = {"generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "topics": {}, "uk": [], "india": []}
    for tid, q in TOPICS.items():
        try:
            result["topics"][tid] = gnews(q, 4, 8)
        except Exception as e:
            print("topic failed", tid, e)
            result["topics"][tid] = old.get("topics", {}).get(tid, [])
        time.sleep(1.5)
    try:
        result["india"] = gnews(INDIA_TAX, 14, 6)
    except Exception as e:
        print("india failed", e); result["india"] = old.get("india", [])
    try:
        result["uk"] = govuk()
    except Exception as e:
        print("gov.uk failed", e); result["uk"] = old.get("uk", [])
    with open("news.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    print("topics:", {k: len(v) for k, v in result["topics"].items()}, "uk:", len(result["uk"]), "india:", len(result["india"]))

if __name__ == "__main__":
    main()
