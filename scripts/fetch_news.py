"""Builds news.json for Setu. Runs on GitHub Actions every 3 hours.
Fetching on the server avoids browser CORS limits and needs no API keys."""
import json, re, time, urllib.parse, urllib.request, email.utils, datetime, html
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (compatible; SetuNewsBot/1.0; +https://myselfsislam.github.io/setu/)"}
NOW = datetime.datetime.now(datetime.timezone.utc)

# Topic ids match NTOPIC in index.html. Queries are written to pull market and money news only.
TOPICS = {
    "n50":    '(Sensex OR "Nifty 50") (market OR stocks OR shares OR index)',
    "nn50":   '"Nifty Next 50" index OR stocks',
    "mid":    '("Nifty Midcap" OR "midcap index" OR "mid-cap stocks" OR "midcap stocks")',
    "small":  '("Nifty Smallcap" OR "smallcap index" OR "small-cap stocks" OR "smallcap stocks")',
    "us":     '"S&P 500" (stocks OR index OR market)',
    "baf":    '("balanced advantage fund" OR "hybrid mutual fund" OR "hybrid funds")',
    "short":  '("debt mutual fund" OR "short duration fund" OR "India bond yields" OR "debt funds")',
    "liquid": '("liquid fund" OR "liquid funds" OR "debt mutual fund")',
    "fd":     '("fixed deposit rates" OR "FD rates" OR "NRE FD" OR "FD interest rates")',
    "gold":   '("gold price" OR "gold rate" OR "gold ETF") India',
    "fx":     '(rupee OR INR) (sterling OR "British pound" OR GBP) exchange rate',
    "mf":     '"mutual fund" (SIP OR NAV OR AMFI OR inflows OR returns)',
}
INDIA_TAX = 'NRI (CBDT OR "income tax" OR "Income-tax Act" OR TDS OR "tax return" OR RBI OR SEBI)'

# Every headline must mention its topic and read like money news.
TOPIC_WORDS = {
    "n50": ["sensex", "nifty"], "nn50": ["next 50", "nifty"], "mid": ["midcap", "mid-cap", "mid cap"],
    "small": ["smallcap", "small-cap", "small cap"], "us": ["s&p", "wall street", "nasdaq", "dow"],
    "baf": ["balanced advantage", "hybrid"], "short": ["debt fund", "debt mutual", "bond", "yield", "duration fund"],
    "liquid": ["liquid fund", "debt fund", "debt mutual", "money market"], "fd": ["fixed deposit", "fd ", "fds", "deposit rate", "nre"],
    "gold": ["gold"], "fx": ["rupee", "inr", "sterling", "pound", "gbp"], "mf": ["mutual fund", "sip", "nav", "amfi", "fund"],
    "india": ["tax", "cbdt", "tds", "itr", "rbi", "sebi", "nri", "income-tax"],
}
MONEY = ["market", "stock", "share", "index", "fund", "invest", "sip", "nav", "return", "rate", "yield", "bond", "price",
         "rupee", "inr", "sterling", "gbp", "sensex", "nifty", "rally", "fall", "gain", "surge", "slump", "record", "trade",
         "deposit", "interest", "rbi", "sebi", "tax", "etf", "portfolio", "inflow", "outflow", "earnings", "valuation", "currency", "forex"]
BLOCK = ["paxg", "pax gold", "convert 1", "usdc", "usdt", "tether", "-growth", "plan-growth", "fund-growth", "normal plan", "growth option", "mutual funds news", "mutual fund investment,", "nav today", "fund(g)", "direct plan", "regular plan", "regular-growth", "direct-growth", "idcw", "(g)", "interactive stock chart", "live |", "portfolio |", "technical analysis", "buy or sell", "xrp", "bitcoin", "ethereum", "crypto", "cricket", "football", "ipl", "match", "wicket", "film", "movie", "actor", "actress", "box office", "murder",
         "arrested", "horoscope", "recipe", "weather", "rain", "celebrity", "wedding", "song", "trailer"]

def relevant(title, tid):
    t = " " + title.lower() + " "
    if any(b in t for b in BLOCK):
        return False
    if not any(w in t for w in TOPIC_WORDS.get(tid, [])):
        return False
    return tid == "india" or any(w in t for w in MONEY)

def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def gnews(query, days, limit, region="IN", tid=None):
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
        key = " ".join(re.sub(r"[^a-z0-9 ]", " ", title.lower()).split()[:4])
        if not title or key in seen:
            continue
        seen.add(key)
        try:
            at = email.utils.parsedate_to_datetime(it.findtext("pubDate")).astimezone(datetime.timezone.utc)
        except Exception:
            continue
        if (NOW - at).days > days:
            continue
        if tid and not relevant(title, tid):
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


# ---------- UK fund / ETF prices for the Investments tab (weekly closes, 5 years) ----------
UK_FUNDS = [
    ("VWRP.L", "Vanguard FTSE All-World (Acc)"), ("VWRL.L", "Vanguard FTSE All-World (Dist)"),
    ("VUAG.L", "Vanguard S&P 500 (Acc)"), ("VUSA.L", "Vanguard S&P 500 (Dist)"),
    ("VHVG.L", "Vanguard FTSE Developed World (Acc)"), ("SWDA.L", "iShares Core MSCI World (Acc)"),
    ("HMWO.L", "HSBC MSCI World"), ("CSP1.L", "iShares Core S&P 500 (Acc)"),
    ("EQQQ.L", "Invesco EQQQ Nasdaq-100"), ("VFEG.L", "Vanguard FTSE Emerging Markets (Acc)"),
    ("ISF.L", "iShares Core FTSE 100"), ("VUKG.L", "Vanguard FTSE 100 (Acc)"),
    ("NDIA.L", "iShares MSCI India"), ("IGLT.L", "iShares Core UK Gilts"), ("SGLN.L", "iShares Physical Gold"),
]

def uk_prices():
    out = {}
    for sym, name in UK_FUNDS:
        try:
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(sym) + "?range=5y&interval=1wk"
            j = json.loads(get(url))["chart"]["result"][0]
            cur = (j.get("meta") or {}).get("currency", "GBP")
            div = 100.0 if cur == "GBp" else 1.0
            ts, closes = j.get("timestamp") or [], (j.get("indicators", {}).get("quote") or [{}])[0].get("close") or []
            pts = [[datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%d"), round(c / div, 4)]
                   for t, c in zip(ts, closes) if c]
            last = (j.get("meta") or {}).get("regularMarketPrice")
            if last:
                lt = datetime.datetime.fromtimestamp(j["meta"].get("regularMarketTime", ts[-1]), datetime.timezone.utc).strftime("%Y-%m-%d")
                if pts and pts[-1][0] == lt: pts[-1][1] = round(last / div, 4)
                else: pts.append([lt, round(last / div, 4)])
            if len(pts) > 10:
                out[sym] = {"name": name, "cur": "GBP" if cur in ("GBp", "GBP") else cur, "pts": pts}
        except Exception as e:
            print("price failed", sym, e)
        time.sleep(0.8)
    return out

def main():
    try:
        old = json.load(open("news.json"))
    except Exception:
        old = {}
    result = {"generated": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"), "topics": {}, "uk": [], "india": []}
    for tid, q in TOPICS.items():
        try:
            result["topics"][tid] = gnews(q, 4, 8, tid=tid)
        except Exception as e:
            print("topic failed", tid, e)
            result["topics"][tid] = old.get("topics", {}).get(tid, [])
        time.sleep(1.5)
    try:
        result["india"] = gnews(INDIA_TAX, 14, 6, tid="india")
    except Exception as e:
        print("india failed", e); result["india"] = old.get("india", [])
    try:
        result["uk"] = govuk()
    except Exception as e:
        print("gov.uk failed", e); result["uk"] = old.get("uk", [])
    try:
        result["prices"] = uk_prices() or old.get("prices", {})
    except Exception as e:
        print("prices failed", e); result["prices"] = old.get("prices", {})
    with open("news.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
    print("topics:", {k: len(v) for k, v in result["topics"].items()}, "uk:", len(result["uk"]), "india:", len(result["india"]), "prices:", len(result.get("prices", {})))

if __name__ == "__main__":
    main()
