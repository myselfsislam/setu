"""Builds Setu's static guide pages, sitemap and robots.txt.
Change SITE_URL once when you move to your own domain, then run:  python scripts/build_guides.py"""
import json, os, html, datetime

SITE_URL = "https://myselfsislam.github.io/setu"   # no trailing slash
CF_BEACON_TOKEN = "7e9e4c80e7b2452fa72ee68caac0c878"                                # Cloudflare Web Analytics token (optional)
GOOGLE_VERIFY = "nbaqICzAz7xt_QFklwBTVEIaW-CLCYUgbwLPEBsHKlE"                                  # Google Search Console verification code (optional)
TODAY = datetime.date(2026, 9, 27).isoformat()
OUT = "."

CSS = """
@font-face{font-family:Figtree;src:url(../fonts/figtree.woff2) format('woff2');font-weight:400 800;font-display:swap}
@font-face{font-family:'Bricolage Grotesque';src:url(../fonts/bricolage.woff2) format('woff2');font-weight:600 800;font-display:swap}
:root{--bg:#F4F2FB;--card:#fff;--ink:#1A1446;--soft:#625E88;--rule:#E8E4F4;--indigo:#4B3BE0;--t-indigo:#ECE9FF;--marigold:#FFB020;--mint:#0C7F60}
@media (prefers-color-scheme:dark){:root{--bg:#0F0C24;--card:#1B1740;--ink:#F0EEFF;--soft:#B3AEDB;--rule:#2E2860;--indigo:#9184FF;--t-indigo:#2A2466;--mint:#6FE3BF}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.6 Figtree,system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--indigo)}header,main,footer{max-width:760px;margin:0 auto;padding:0 20px}
header{display:flex;align-items:center;justify-content:space-between;padding-top:20px}
.brand{display:flex;align-items:center;gap:10px;font:800 22px 'Bricolage Grotesque',sans-serif;color:var(--ink);text-decoration:none}
.cta{display:inline-block;background:#4B3BE0;color:#fff;font-weight:800;text-decoration:none;padding:12px 20px;border-radius:14px}
h1,h2,h3{font-family:'Bricolage Grotesque',sans-serif;line-height:1.15}h1{font-size:40px;margin:28px 0 10px}h2{font-size:26px;margin:34px 0 8px}h3{font-size:19px;margin:22px 0 4px}
.lead{font-size:19px;color:var(--soft)}.card{background:var(--card);border-radius:20px;padding:18px 20px;margin:16px 0;box-shadow:0 10px 30px -22px rgba(40,24,140,.5)}
.note{font-size:14px;color:var(--soft)}.crumbs{font-size:14px;color:var(--soft);margin-top:18px}.crumbs a{color:var(--soft)}
label{display:block;font-weight:700;font-size:14px;margin:10px 0 4px}input,select{width:100%;font:inherit;padding:10px 12px;border-radius:12px;border:1.5px solid var(--rule);background:var(--card);color:var(--ink)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.out{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}.out div{background:var(--t-indigo);border-radius:14px;padding:10px 12px}.out b{display:block;font:800 22px 'Bricolage Grotesque',sans-serif}
ul.list li,ol.list li{margin:6px 0}footer{padding:30px 20px 50px;font-size:14px;color:var(--soft)}
.phase{display:inline-block;font-size:12px;font-weight:800;background:var(--t-indigo);color:var(--indigo);border-radius:8px;padding:2px 8px;margin-right:6px}
@media (max-width:560px){h1{font-size:31px}.grid,.out{grid-template-columns:1fr}}
"""

LOGO = '<svg width="28" height="28" viewBox="0 0 40 40" aria-hidden="true"><path d="M9.5 30.5 C9.5 19 30.5 21 30.5 9.5" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-dasharray="0.1 6.4"/><circle cx="9.5" cy="30.5" r="7" fill="#FFB020"/><circle cx="30.5" cy="9.5" r="7" fill="#4B3BE0"/></svg>'

def page(slug, title, desc, h1, lead, body, faq=None, extra_js=""):
    url = f"{SITE_URL}/guides/{slug}.html" if slug else f"{SITE_URL}/guides/"
    ld = [{"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": desc,
           "datePublished": TODAY, "dateModified": TODAY, "inLanguage": "en-GB",
           "author": {"@type": "Organization", "name": "Setu"}, "publisher": {"@type": "Organization", "name": "Setu"},
           "mainEntityOfPage": url, "image": f"{SITE_URL}/og.png"},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Setu", "item": f"{SITE_URL}/"},
              {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{SITE_URL}/guides/"}] +
              ([{"@type": "ListItem", "position": 3, "name": h1, "item": url}] if slug else [])}]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
        body += '<h2>Common questions</h2>' + ''.join(f'<h3>{html.escape(q)}</h3><p>{html.escape(a)}</p>' for q, a in faq)
    beacon = (f'<script defer src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{{"token":"{CF_BEACON_TOKEN}"}}\'></script>' if CF_BEACON_TOKEN else "")
    verify = f'<meta name="google-site-verification" content="{GOOGLE_VERIFY}">' if GOOGLE_VERIFY else ""
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large">{verify}
<meta name="theme-color" content="#4B3BE0"><link rel="icon" href="../icons/setu-192.png"><link rel="apple-touch-icon" href="../icons/apple-touch-icon.png">
<meta property="og:type" content="article"><meta property="og:site_name" content="Setu"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE_URL}/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" href="../fonts/figtree.woff2" as="font" type="font/woff2" crossorigin>
<style>{CSS}</style>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head><body>
<header><a class="brand" href="../">{LOGO}Setu</a><a class="cta" href="../">Open the free app</a></header>
<main>
<nav class="crumbs" aria-label="Breadcrumb"><a href="../">Setu</a> › <a href="./">Guides</a>{(' › ' + html.escape(h1)) if slug else ''}</nav>
<h1>{html.escape(h1)}</h1><p class="lead">{lead}</p>
{body}
<div class="card"><h2 style="margin-top:0">Plan your money in one place</h2><p>Setu is a free, private money planner for Indians moving to the UK: take-home pay in pounds and rupees, a first-90-days checklist, spending tracker, and goals for a home and retirement in India. No sign-up. Your data stays on your device.</p><a class="cta" href="../">Open Setu</a></div>
<p class="note">General information, not financial, tax or legal advice. Rules change, so check official sources before acting. Last updated {datetime.date.fromisoformat(TODAY).strftime('%d %B %Y').lstrip('0')}.</p>
</main>
<footer><a href="../">Setu</a> · <a href="./">All guides</a> · Free and private. No accounts, no tracking cookies.</footer>
{extra_js}{beacon}
</body></html>"""

GUIDES = []

# 1. First 90 days checklist
GUIDES.append(("moving-to-uk-from-india-money-checklist",
 "Moving to the UK from India: money checklist for your first 90 days | Setu",
 "A step-by-step money checklist for Indians moving to the UK: NRO and NRE accounts, UK bank, National Insurance, tax code, council tax, ISA, pension and Indian tax.",
 "Moving to the UK from India: your first 90 days money checklist",
 "Everything to sort out with your money in India and the UK, in the order most people need it.",
 """
<h2>Before you leave, or straight after: in India</h2>
<ol class="list">
<li><b>Change your savings account to NRO.</b> Once you move abroad for work, your bank must be told. Your normal savings account becomes an NRO account (for money earned in India). The account number usually stays the same, so EMIs keep running.</li>
<li><b>Open an NRE account</b> for money you send from the UK. NRE interest is tax-free in India and the money can be moved back out freely.</li>
<li><b>Update your mutual funds and shares.</b> Tell each fund house and your broker that you now live abroad, so they update your status and linked bank account.</li>
<li><b>Tell your lenders and card providers</b> which account to take payments from, so nothing bounces.</li>
<li><b>Keep your Indian phone number</b> active. Bank OTPs, UPI and Aadhaar all depend on it.</li>
</ol>
<h2>Weeks 1–2 in the UK</h2>
<ol class="list">
<li><b>Set up your eVisa.</b> Employers and landlords check your status online with a share code. <a href="https://www.gov.uk/evisa" rel="nofollow noopener">GOV.UK: eVisas</a></li>
<li><b>Open a UK bank account</b> so you can be paid. Many app-based banks only need a passport and UK address.</li>
<li><b>Get your National Insurance number.</b> <a href="https://www.gov.uk/apply-national-insurance-number" rel="nofollow noopener">GOV.UK: apply for a National Insurance number</a></li>
<li><b>Register with a GP.</b> It's free, and your visa's health surcharge already covers NHS care.</li>
<li><b>Set up council tax.</b> If you live alone you can usually get 25% off. <a href="https://www.gov.uk/council-tax" rel="nofollow noopener">GOV.UK: council tax</a></li>
</ol>
<h2>Month 1</h2>
<ol class="list">
<li><b>Check your first payslip.</b> For most people the tax code is 1257L. An emergency code such as 0T, W1 or M1 can mean you're paying too much for now. <a href="https://www.gov.uk/tax-codes" rel="nofollow noopener">GOV.UK: tax codes</a></li>
<li><b>Keep one month of rent and bills</b> in your UK account before investing anything.</li>
<li><b>Pick a low-cost way to send money home.</b> Compare the rupees delivered, not just the fee.</li>
<li><b>Keep proof of your arrival date</b> (boarding pass or passport stamp). It affects your tax position in both countries.</li>
</ol>
<h2>By day 90</h2>
<ol class="list">
<li><b>Build an emergency fund</b> of 3–6 months of UK costs.</li>
<li><b>Look at your workplace pension.</b> You're enrolled automatically, and your employer adds money too.</li>
<li><b>Learn about ISAs:</b> up to £20,000 a year of saving or investing with no UK tax. <a href="https://www.gov.uk/individual-savings-accounts" rel="nofollow noopener">GOV.UK: ISAs</a></li>
<li><b>Check UK tax on your Indian income.</b> As a UK resident, your worldwide income can be taxed here. New arrivals may be able to claim relief on foreign income for 4 years through Self Assessment. <a href="https://www.gov.uk/tax-foreign-income" rel="nofollow noopener">GOV.UK: tax on foreign income</a></li>
<li><b>Plan your Indian tax return.</b> If you spent under 182 days in India in the year you left, you usually file as an NRI.</li>
</ol>
""",
 [("Do I have to change my Indian savings account after moving to the UK?", "Yes. Once you become a non-resident Indian, resident savings accounts should be changed to NRO accounts. Your bank can usually do this without changing the account number."),
  ("What is the difference between NRO and NRE accounts?", "An NRO account holds money earned in India, such as rent or interest, and its interest is taxable in India. An NRE account holds money earned abroad, its interest is tax-free in India, and the money can be moved back out freely."),
  ("What tax code should be on my first UK payslip?", "Most people with one job have the tax code 1257L. Codes such as 0T, W1 or M1 are emergency codes and can mean you are paying too much tax until HMRC updates them.")]))

# 2. Take-home pay in pounds and rupees (interactive)
calc_js = """<script>
(function(){var rate=129;function bt(ti,b){var t=0,lo=0;for(var i=0;i<b.length;i++){if(ti>lo)t+=(Math.min(ti,b[i][0])-lo)*b[i][1];lo=b[i][0];}return t;}
var RUK=[[37700,.2],[125140,.4],[Infinity,.45]],SCO=[[3967,.19],[16956,.2],[31092,.21],[62430,.42],[125140,.45],[Infinity,.48]];
function th(g,pp,s){var pa=12570;if(g>100000)pa=Math.max(0,12570-(g-100000)/2);var pen=Math.max(0,Math.min(g,50270)-6240)*pp/100,ti=Math.max(0,g-pen-pa),tax=bt(ti,s?SCO:RUK),ni=.08*Math.max(0,Math.min(g,50270)-12570)+.02*Math.max(0,g-50270);return {m:(g-tax-ni-pen)/12,tax:tax,ni:ni,pen:pen};}
function f(n,c){return (c==='₹'?'₹':'£')+Math.round(n).toLocaleString(c==='₹'?'en-IN':'en-GB');}
function run(){var g=+document.getElementById('g').value||0,pp=+document.getElementById('p').value||0,s=document.getElementById('s').value==='1',r=th(g,pp,s);
 document.getElementById('o1').textContent=f(r.m,'£');document.getElementById('o2').textContent=f(r.m*rate,'₹');document.getElementById('o3').textContent=f(r.tax/12,'£');document.getElementById('o4').textContent=f(r.ni/12,'£');}
['g','p','s'].forEach(function(i){document.getElementById(i).addEventListener('input',run);});run();
fetch('https://api.frankfurter.dev/v1/latest?base=GBP&symbols=INR').then(function(r){return r.json();}).then(function(j){if(j&&j.rates&&j.rates.INR){rate=j.rates.INR;document.getElementById('rt').textContent='Using today’s rate: ₹'+rate.toFixed(2)+' = £1.';run();}}).catch(function(){});})();
</script>"""
GUIDES.append(("uk-salary-after-tax-in-rupees",
 "UK salary after tax in rupees: 2026/27 take-home pay calculator | Setu",
 "See your UK take-home pay each month in pounds and Indian rupees. Uses 2026/27 income tax and National Insurance rates, including Scotland.",
 "UK take-home pay calculator, in pounds and rupees",
 "Enter your yearly salary to see what reaches your bank each month, and what that is in rupees at today's rate.",
 """
<div class="card">
<div class="grid"><div><label for="g">Yearly salary before tax (£)</label><input id="g" type="number" inputmode="decimal" value="48000"></div>
<div><label for="p">Your pension contribution (%)</label><input id="p" type="number" inputmode="decimal" value="5"></div></div>
<label for="s">Where do you live?</label><select id="s"><option value="0">England, Wales or Northern Ireland</option><option value="1">Scotland</option></select>
<div class="out" aria-live="polite"><div>Take-home each month<b id="o1">£</b></div><div>In rupees<b id="o2">₹</b></div><div>Income tax each month<b id="o3">£</b></div><div>National Insurance each month<b id="o4">£</b></div></div>
<p class="note" id="rt">Using an approximate rate of ₹129 = £1.</p></div>
<h2>How it's worked out</h2>
<p>For 2026/27, the first £12,570 is tax-free (the Personal Allowance). In England, Wales and Northern Ireland, income above that is taxed at 20% up to £50,270, 40% up to £125,140 and 45% above. The allowance shrinks by £1 for every £2 earned over £100,000.</p>
<p>Scotland has six bands: 19%, 20%, 21%, 42%, 45% and 48%. National Insurance is the same everywhere in the UK: 8% on earnings between £12,570 and £50,270, and 2% above.</p>
<p>Your workplace pension is estimated on "qualifying earnings" between £6,240 and £50,270, which is how most auto-enrolment schemes work. Your payslip is the final word.</p>
""",
 [("How much is £50,000 after tax in the UK?", "In England, Wales or Northern Ireland, a £50,000 salary with no pension contributions leaves about £3,293 a month after income tax and National Insurance in 2026/27. In Scotland it is about £3,169 a month."),
  ("Is National Insurance different in Scotland?", "No. National Insurance is set UK-wide, so it is the same in Scotland. Only income tax bands differ.")],
 calc_js))

# 3. Sending money home: hidden cost
xfer_js = """<script>
(function(){var mid=129;function f(n){return '₹'+Math.round(n).toLocaleString('en-IN');}
function run(){var A=+document.getElementById('a').value||0,F=+document.getElementById('fee').value||0,R=+document.getElementById('r').value||0;var got=(A-F)*R,fair=A*mid,lost=Math.max(0,fair-got);
document.getElementById('x1').textContent=f(got);document.getElementById('x2').textContent=f(fair);document.getElementById('x3').textContent=f(lost)+' ('+(fair?(lost/fair*100).toFixed(1):0)+'%)';document.getElementById('x4').textContent=f(lost*12);}
['a','fee','r'].forEach(function(i){document.getElementById(i).addEventListener('input',run);});run();
fetch('https://api.frankfurter.dev/v1/latest?base=GBP&symbols=INR').then(function(r){return r.json();}).then(function(j){if(j&&j.rates&&j.rates.INR){mid=j.rates.INR;document.getElementById('m').textContent='Today’s mid-market rate: ₹'+mid.toFixed(2)+' = £1 (European Central Bank).';if(!document.getElementById('r').dataset.touched)document.getElementById('r').value=(mid*0.975).toFixed(2);run();}}).catch(function(){});
document.getElementById('r').addEventListener('input',function(){this.dataset.touched=1;});})();
</script>"""
GUIDES.append(("send-money-uk-to-india-hidden-cost",
 "Sending money from the UK to India: the hidden cost in the exchange rate | Setu",
 "Banks hide most of their charge in a worse exchange rate. Check how many rupees you lose on each UK to India transfer against today's mid-market rate.",
 "Sending money from the UK to India: spot the hidden cost",
 "The fee is only part of the price. Most of the cost is hidden in the exchange rate you're given.",
 """
<div class="card">
<div class="grid"><div><label for="a">You send (£)</label><input id="a" type="number" inputmode="decimal" value="500"></div><div><label for="fee">Their fee (£)</label><input id="fee" type="number" inputmode="decimal" value="0"></div></div>
<label for="r">Rate they offer (₹ for £1)</label><input id="r" type="number" inputmode="decimal" step="any" value="125.8">
<div class="out" aria-live="polite"><div>Your family receives<b id="x1">₹</b></div><div>At the real rate<b id="x2">₹</b></div><div>Hidden cost each time<b id="x3">₹</b></div><div>If you send monthly, per year<b id="x4">₹</b></div></div>
<p class="note" id="m">Compared with an approximate mid-market rate of ₹129 = £1.</p><p style="margin:10px 0 0"><a href="../?open=transfer">Use the full checker in Setu, with yearly totals ›</a></p></div>
<h2>What the "mid-market rate" is</h2>
<p>The mid-market rate is the midpoint between what banks pay and charge each other for currency. It's the rate you see on Google or the European Central Bank's daily reference rates. No provider gives you exactly this rate for free, but some get much closer than others.</p>
<h2>How to compare providers fairly</h2>
<ol class="list"><li>Enter the same amount in pounds with each provider.</li><li>Look at the <b>total rupees your family will receive</b>, after all fees.</li><li>Choose whichever delivers the most. A "zero fee" transfer with a poor rate can cost more than one with a small, clear fee.</li></ol>
""",
 [("Why is the exchange rate I get lower than on Google?", "Google shows the mid-market rate. Most banks and many transfer services add a margin to it, which is how they make money on the exchange. That margin is a cost to you even when the fee is shown as zero."),
  ("What is the cheapest way to send money from the UK to India?", "It changes from day to day and depends on the amount. The fair test is the total number of rupees received after all fees, compared across providers on the same day.")],
 xfer_js))

# 4. NRO vs NRE
GUIDES.append(("nro-vs-nre-account-uk",
 "NRO vs NRE accounts explained for Indians living in the UK | Setu",
 "NRO or NRE? What each Indian bank account is for, how interest is taxed in India and the UK, and what to do when you move to the UK.",
 "NRO vs NRE accounts: which do you need in the UK?",
 "Once you live abroad, your Indian bank accounts change. Here's what each account is for, in plain English.",
 """
<div class="card"><h2 style="margin-top:0">At a glance</h2>
<ul class="list"><li><b>NRO (Non-Resident Ordinary):</b> for money earned in India, such as rent, dividends, pension or interest. Your old savings account becomes this.</li>
<li><b>NRE (Non-Resident External):</b> for money you earn abroad and send to India. Interest is tax-free in India, and the money can be moved back out freely.</li></ul></div>
<h2>When you move to the UK</h2>
<p>Tell your bank that you have become a non-resident. It will change your resident savings account to an NRO account, usually keeping the same account number so existing EMIs and SIPs keep running. Open an NRE account for money you send from the UK.</p>
<h2>How the interest is taxed</h2>
<p><b>In India:</b> NRO interest is taxable, and tax is usually deducted at source. NRE interest is tax-free in India.</p>
<p><b>In the UK:</b> as a UK resident, your worldwide income can be taxed here, including interest on Indian accounts, even if it's tax-free in India. New arrivals may be able to claim relief on foreign income for their first 4 years through Self Assessment. <a href="https://www.gov.uk/tax-foreign-income" rel="nofollow noopener">GOV.UK: tax on foreign income</a></p>
<h2>Which account for what?</h2>
<ul class="list"><li>Sending UK salary home to save or invest → <b>NRE</b>.</li><li>Rent from a flat in India, or interest on old deposits → <b>NRO</b>.</li><li>EMIs on Indian loans → usually paid from <b>NRO</b>, topped up from NRE if needed.</li></ul>
""",
 [("Is NRE interest taxable in the UK?", "It can be. India does not tax NRE interest, but UK residents can be taxed on worldwide income. New arrivals may be able to claim a 4-year relief on foreign income, which has to be claimed through Self Assessment."),
  ("Can I keep my resident savings account after moving to the UK?", "No. Once you become a non-resident Indian, resident accounts should be changed to NRO accounts. Ask your bank to do this.")]))

def main():
    os.makedirs(os.path.join(OUT, "guides"), exist_ok=True)
    for g in GUIDES:
        slug, title, desc, h1, lead, body, faq = g[:7]
        js = g[7] if len(g) > 7 else ""
        open(os.path.join(OUT, "guides", slug + ".html"), "w").write(page(slug, title, desc, h1, lead, body, faq, js))
    items = "".join(f'<div class="card"><h2 style="margin:0 0 6px;font-size:22px"><a href="{g[0]}.html">{html.escape(g[3])}</a></h2><p style="margin:0">{html.escape(g[2])}</p></div>' for g in GUIDES)
    open(os.path.join(OUT, "guides", "index.html"), "w").write(page("", "Money guides for Indians moving to the UK | Setu",
        "Free, plain-English guides for Indians in the UK: first 90 days checklist, take-home pay in rupees, sending money home, NRO and NRE accounts.",
        "Money guides for Indians moving to the UK", "Plain-English guides and calculators. Free, with no sign-up.", items))
    urls = [f"{SITE_URL}/", f"{SITE_URL}/guides/"] + [f"{SITE_URL}/guides/{g[0]}.html" for g in GUIDES]
    open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    print("built", len(GUIDES), "guides")

if __name__ == "__main__":
    main()
