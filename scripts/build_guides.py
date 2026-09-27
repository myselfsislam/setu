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


# ---------------- More guides (added 27 Sept 2026) ----------------
GUIDES.append(("isa-for-indians-in-the-uk",
 "ISAs for Indians in the UK: how they work and what's changing in 2027 | Setu",
 "A plain-English guide to ISAs for Indians living in the UK: the £20,000 allowance, cash vs stocks and shares, the Lifetime ISA, the 2027 cash ISA change, and what happens if you move back to India.",
 "ISAs for Indians in the UK: a simple guide",
 "An ISA lets you save or invest without paying UK tax on the interest or growth. Here's how it works for someone who has moved from India.",
 """
<div class="card"><h2 style="margin-top:0">The key numbers for 2026/27</h2>
<ul class="list"><li><b>£20,000</b> a year in total across all your ISAs (6 April 2026 to 5 April 2027).</li>
<li><b>Lifetime ISA:</b> up to £4,000 a year, which counts inside the £20,000.</li>
<li><b>Unused allowance is lost</b> on 5 April. It doesn't carry over.</li></ul></div>
<h2>What's changing in April 2027</h2>
<p>From 6 April 2027, people under 65 can put at most <b>£12,000 a year into cash ISAs</b>. The overall £20,000 limit stays, so the rest can go into a stocks and shares ISA. Money already in a cash ISA isn't affected. 2026/27 is the last tax year when under-65s can put the full £20,000 into cash.</p>
<h2>Cash ISA or stocks and shares ISA?</h2>
<ul class="list"><li><b>Cash ISA:</b> like a savings account with tax-free interest. Good for money you may need within a few years, such as an emergency fund.</li>
<li><b>Stocks and shares ISA:</b> invests in funds or shares. The value can fall as well as rise, so it suits money you won't need for 5 years or more.</li></ul>
<h2>The Lifetime ISA: read the small print</h2>
<p>You must open one before you turn 40. The government adds a 25% bonus (up to £1,000 a year), but you can only use it without a penalty for a <b>first home in the UK costing up to £450,000</b>, or from age 60. Taking money out for anything else, including a home in India, usually costs a 25% charge, so you can get back less than you put in. The government has said the Lifetime ISA will be replaced by a new first-time buyer ISA from April 2028.</p>
<h2>Why ISAs matter more after your first few years</h2>
<p>New arrivals may not pay UK tax on Indian income for their first 4 years if they claim the <a href="uk-tax-on-indian-income-4-year-relief.html">4-year foreign income relief</a>. After that, UK tax applies to interest and gains in India too. An ISA stays free of UK tax whatever happens, which is why many people build their long-term savings here.</p>
<h2>If you move back to India</h2>
<p>You can keep an ISA after you leave the UK, and it stays free of <b>UK</b> tax, but you can't add new money while you're not UK resident. India may tax the income and gains once you become resident there again, so plan any sale with a tax adviser, ideally during your RNOR years.</p>
<p><a href="../?tab=goals">Plan your long-term goals in Setu ›</a></p>
""",
 [("How much can I put in an ISA in 2026/27?", "£20,000 in total across all your ISAs between 6 April 2026 and 5 April 2027. A Lifetime ISA has its own £4,000 limit inside that."),
  ("Is the cash ISA limit changing?", "Yes. From 6 April 2027, under-65s can pay at most £12,000 a year into cash ISAs. The overall £20,000 limit stays the same."),
  ("Can I use a Lifetime ISA to buy a home in India?", "Not without a penalty. The bonus is only for a first home in the UK costing up to £450,000, or from age 60. Other withdrawals usually cost 25%."),
  ("Can I keep my ISA if I move back to India?", "Yes. It stays free of UK tax, but you can't add new money while you're not UK resident, and India may tax it once you're resident there.")]))

GUIDES.append(("uk-tax-on-indian-income-4-year-relief",
 "UK tax on Indian income: the 4-year FIG relief for new arrivals | Setu",
 "Do you pay UK tax on interest, rent or gains in India? How the 4-year foreign income and gains (FIG) relief works for people moving from India, who qualifies, and the catch.",
 "UK tax on your Indian income: the 4-year relief",
 "Once you're UK resident, the UK can tax your income from India too. New arrivals may get a 4-year break, but it has to be claimed and it isn't always worth it.",
 """
<div class="card"><h2 style="margin-top:0">In short</h2>
<ul class="list"><li>UK residents are taxed on their <b>worldwide</b> income and gains, including NRO and NRE interest, rent from a flat in India, and gains on Indian mutual funds.</li>
<li>If you hadn't lived in the UK for the <b>10 tax years</b> before you arrived, you may be able to claim relief on foreign income and gains for your <b>first 4 tax years</b> here.</li>
<li>It isn't automatic. You claim it each year on a <b>Self Assessment</b> tax return.</li></ul></div>
<h2>Who can claim</h2>
<p>The foreign income and gains (FIG) regime started on 6 April 2025 and replaced the old non-dom rules. You qualify in your first four tax years of UK residence if you weren't UK resident in any of the previous ten tax years. It's based on residence, not nationality. Your UK salary is taxed as normal; the relief only covers <b>foreign</b> income and gains.</p>
<h2>The catch: you lose your tax-free allowances</h2>
<p>In any year you claim, you give up your <b>£12,570 Personal Allowance</b> and your Capital Gains Tax annual exempt amount. For someone on a full UK salary with modest interest in India, that can cost more than the relief saves. It tends to help people with large income or gains in India. Work it out both ways, or ask a tax adviser, before claiming.</p>
<h2>How to claim</h2>
<ol class="list"><li>Register for Self Assessment with HMRC if you haven't before. If you became UK resident in a tax year, register by 5 October after that tax year ends.</li>
<li>Fill in the residence and foreign income pages of your tax return, listing the foreign income and gains you want relief on.</li>
<li>Claim within the time limit: for 2025/26, the deadline is 31 January 2028.</li></ol>
<h2>Don't forget India</h2>
<p>Income earned in India can still be taxed in India, for example NRO interest has tax deducted at source. The UK–India tax treaty helps avoid paying twice on the same income. Keep records of Indian tax paid.</p>
<p><a href="https://www.gov.uk/tax-foreign-income" rel="nofollow noopener">GOV.UK: tax on foreign income</a> · <a href="nro-vs-nre-account-uk.html">NRO vs NRE accounts</a></p>
""",
 [("Do I pay UK tax on NRE interest?", "It can be taxable in the UK because UK residents are taxed on worldwide income, even though India doesn't tax NRE interest. New arrivals may be able to claim the 4-year relief."),
  ("Who qualifies for the 4-year FIG relief?", "People in their first four tax years of UK residence who weren't UK resident in any of the ten tax years before they arrived."),
  ("Is the 4-year relief automatic?", "No. You claim it each year on a Self Assessment tax return. If you claim, you lose your Personal Allowance and Capital Gains Tax annual exempt amount for that year."),
  ("Is claiming always worth it?", "Not always. If your income from India is small, losing your £12,570 Personal Allowance can cost more than the tax you save.")]))

GUIDES.append(("nri-182-day-rule",
 "The 182-day rule: how many days can an NRI spend in India? | Setu",
 "How India decides if you're an NRI: the 182-day test, the 120-day rule for higher Indian incomes, deemed residence, and RNOR when you move back. Updated for the Income-tax Act 2025.",
 "The 182-day rule: staying an NRI while you live in the UK",
 "Your tax status in India depends mainly on how many days you spend there. Here's how the rules work for someone working in the UK.",
 """
<div class="card"><h2 style="margin-top:0">The simple version</h2>
<p>If you've moved to the UK for work, you'll generally stay a non-resident Indian (NRI) as long as you spend <b>fewer than 182 days in India</b> in an Indian tax year (1 April to 31 March). As an NRI, India only taxes income earned or received in India.</p></div>
<h2>The exceptions to watch</h2>
<ul class="list"><li><b>The 120-day rule:</b> if your Indian income (not counting foreign income) is over <b>₹15 lakh</b> in a year, you can become resident with 120 days in India if you also spent 365 days there over the previous four years.</li>
<li><b>Deemed residence:</b> an Indian citizen with Indian income over ₹15 lakh who isn't liable to tax in any other country can be treated as resident. Paying UK tax as a UK resident normally avoids this.</li>
<li><b>The year you leave:</b> Indian citizens who leave for a job abroad are judged on the 182-day test for that year.</li></ul>
<h2>What changed in 2026</h2>
<p>India's new Income-tax Act 2025 took effect on 1 April 2026. It replaces “previous year” and “assessment year” with a single <b>tax year</b>, but the residence tests above carry over with new section numbers, and NRE interest stays tax-free in India.</p>
<h2>When you move back: RNOR</h2>
<p>Returning NRIs often get a transition status called Resident but Not Ordinarily Resident (RNOR), usually for up to two or three years. During RNOR, most foreign income isn't taxed in India, which is a good window to sell UK investments or move savings home. Check the details with a tax adviser before you return.</p>
<h2>Keep a record</h2>
<p>Count your days from your passport stamps and boarding passes, and keep them. Setu's checklist reminds you each year.</p>
<p><a href="../?tab=check">Open your checklist in Setu ›</a></p>
""",
 [("How many days can an NRI stay in India?", "Generally fewer than 182 days in an Indian tax year (April to March). A 120-day limit can apply if your Indian income is over ₹15 lakh and you spent 365 days in India over the previous four years."),
  ("Did the new Income-tax Act change NRI rules?", "The Income-tax Act 2025, in force from 1 April 2026, mostly carries the residence rules over. It replaces previous year and assessment year with a single tax year."),
  ("What is RNOR?", "Resident but Not Ordinarily Resident: a transition status for many returning NRIs, during which most foreign income isn't taxed in India.")]))

GUIDES.append(("council-tax-for-new-arrivals",
 "Council tax explained for new arrivals from India | Setu",
 "What council tax is, how much it costs, who pays, the 25% single-person discount, and how to set it up when you move into a UK home.",
 "Council tax explained for new arrivals",
 "Council tax is a monthly local tax on your home. It's one of the first bills to set up after you move in, and there's a common discount many people miss.",
 """
<h2>What it pays for</h2>
<p>Council tax funds local services such as bin collections, roads, libraries and social care. It's charged per home, not per person, and is usually paid by the people who live there, including tenants.</p>
<h2>How much it costs</h2>
<p>Each home in England and Scotland is placed in a <b>band</b> (A to H in England) based on its value, and your council sets the charge for each band. In Wales there are bands A to I. The amount varies a lot between areas, so check your exact charge on your council's website before you agree a rent.</p>
<h2>Discounts to claim</h2>
<ul class="list"><li><b>Living alone:</b> a <b>25% single-person discount</b>. If your partner hasn't joined you yet, you may qualify until they arrive.</li>
<li><b>Full-time students</b> are usually disregarded, so a home where everyone is a student may pay nothing.</li>
<li>Your council may offer reductions if you're on a low income.</li></ul>
<h2>How to set it up</h2>
<ol class="list"><li>Find your council using your postcode on GOV.UK.</li><li>Register as the person responsible from the day you moved in.</li><li>Choose to pay over 10 or 12 months. Twelve smaller payments are easier to budget for.</li><li>Tell the council when anyone moves in or out, as it can change your bill.</li></ol>
<p><a href="https://www.gov.uk/council-tax" rel="nofollow noopener">GOV.UK: council tax</a> · <a href="moving-to-uk-from-india-money-checklist.html">Your first 90 days money checklist</a></p>
""",
 [("Do tenants pay council tax?", "Usually, yes. Council tax is normally paid by the people who live in the home, including tenants, unless your tenancy says it's included in the rent."),
  ("How much is the single-person discount?", "25% off your bill if you're the only adult living in the home."),
  ("Can I pay council tax monthly?", "Yes. Councils usually offer 10 monthly payments, and many let you choose 12.")]))

GUIDES.append(("emergency-fund-on-a-work-visa",
 "How big should your emergency fund be on a UK work visa? | Setu",
 "Why an emergency fund matters more on a Skilled Worker visa, how many months to save, where to keep it, and how to build it while paying EMIs in India.",
 "How big should your emergency fund be on a work visa?",
 "On a sponsored visa, losing your job starts a clock. A cash cushion gives you time to find a new sponsor without panic.",
 """
<div class="card"><h2 style="margin-top:0">Why it matters more on a work visa</h2>
<p>If your sponsored job ends, your employer must tell the Home Office, which usually shortens your permission to stay to around <b>60 days</b> (or less if your visa ends sooner). In that time you need to find a new sponsor, switch visa or leave. Savings mean you can focus on the right job, not the first one.</p></div>
<h2>How many months to save</h2>
<ul class="list"><li><b>Start with one month</b> of rent and bills sitting in your current account.</li>
<li><b>Build to 3 months</b> of essential UK costs as your first proper target.</li>
<li><b>Aim for 4 to 6 months</b> if you're the only earner, have a family here, or pay large EMIs in India. Remember flights home and a deposit if you have to move.</li></ul>
<h2>What to count</h2>
<p>Rent, council tax, energy, phone, food, travel, and any payments you must keep making in India, like loan EMIs. Leave out investing and nice-to-haves.</p>
<h2>Where to keep it</h2>
<p>An <b>easy-access savings account in the UK</b>, in pounds, so you can reach it quickly. A cash ISA keeps the interest free of UK tax. Avoid shares or locked deposits for this money.</p>
<h2>Build it alongside Indian EMIs</h2>
<ol class="list"><li>Pay off very expensive debt, like a credit card balance, first.</li><li>Then split what's left each month between the emergency fund and other goals.</li><li>Once the fund is full, move that money into long-term investing.</li></ol>
<p>Setu does this split for you and shows how many weeks your savings would last. <a href="../">Try it free ›</a></p>
""",
 [("How long do I have to find a new job on a Skilled Worker visa?", "Usually about 60 days after the Home Office shortens your permission, or less if your visa expires sooner. Check your own documents and get immigration advice if it happens."),
  ("How many months should my emergency fund cover?", "Build to at least 3 months of essential UK costs, and 4 to 6 months if you're the only earner, have family here, or pay large EMIs in India."),
  ("Where should I keep my emergency fund?", "In an easy-access UK savings account or cash ISA, in pounds, so you can reach it quickly.")]))

def main():
    os.makedirs(os.path.join(OUT, "guides"), exist_ok=True)
    for g in GUIDES:
        slug, title, desc, h1, lead, body, faq = g[:7]
        js = g[7] if len(g) > 7 else ""
        open(os.path.join(OUT, "guides", slug + ".html"), "w").write(page(slug, title, desc, h1, lead, body, faq, js))
    items = "".join(f'<div class="card"><h2 style="margin:0 0 6px;font-size:22px"><a href="{g[0]}.html">{html.escape(g[3])}</a></h2><p style="margin:0">{html.escape(g[2])}</p></div>' for g in GUIDES)
    open(os.path.join(OUT, "guides", "index.html"), "w").write(page("", "Money guides for Indians moving to the UK | Setu",
        "Free, plain-English guides for Indians in the UK: first 90 days, take-home pay in rupees, sending money home, NRO and NRE, ISAs, UK tax on Indian income, the 182-day rule, council tax and emergency funds.",
        "Money guides for Indians moving to the UK", "Plain-English guides and calculators. Free, with no sign-up.", items))
    urls = [f"{SITE_URL}/", f"{SITE_URL}/guides/"] + [f"{SITE_URL}/guides/{g[0]}.html" for g in GUIDES]
    open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")
    print("built", len(GUIDES), "guides")

if __name__ == "__main__":
    main()
