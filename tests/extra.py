"""Invest extra money, and Moving back to India. Prints PASS/FAIL per check."""
import os,sys,subprocess,time,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8786
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://localhost:{PORT}/'
R=[]
def check(name,cond,detail=''):
    R.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(detail) if detail else ''))
def state(pg): return pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")
def put(pg,st): pg.evaluate("s=>localStorage.setItem('setu-v1',JSON.stringify(s))",st);pg.reload();pg.wait_for_selector('[data-tab="home"]:visible',timeout=8000)
def rows(pg): return pg.evaluate("[...document.querySelectorAll('.xrow')].map(r=>[r.querySelector('.xt b').textContent,+r.querySelector('.row-b>b').childNodes[0].textContent.replace(/[^0-9.]/g,'')])")
def amount(pg,v):
    pg.fill('#xamt',str(v));pg.wait_for_timeout(150)
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.clock.set_fixed_time('2026-11-15T10:00:00')
    for h in ['api.gdeltproject.org','www.gov.uk','api.mfapi.in','api.frankfurter.dev','open.er-api.com']:pg.route(f'https://{h}/**',lambda r:r.abort())
    pg.goto(URL);pg.wait_for_timeout(400)
    pg.click('[data-wz="next"]');pg.click('[data-wz="full"]');pg.fill('[data-k="name"]','T');pg.fill('[data-k="age"]','32');pg.fill('[data-k="moved"]','2023-04-01');pg.click('[data-wz="next"]')
    pg.fill('[data-k="salary"]','70000');pg.fill('[data-k="rent"]','1200');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(700)
    # seed: emergency fund full, an ISA with £5,000 paid in this tax year, Indian funds concentrated in one house
    st=state(pg);st['profile']['savedUK']=0
    st['holdings']=[{'id':'sav','name':'Easy saver','cty':'uk','type':'savings','value':20000,'paid':20000,'hist':[['2026-05-01',20000]],'goal':'emergency'},
      {'id':'isa','name':'Global ISA','cty':'uk','type':'isa','value':8000,'paid':7000,'hist':[['2026-01-01',2000],['2026-11-01',8000]],'contrib':[['2026-05-01',2500],['2026-09-01',2500]]},
      {'id':'q1','name':'Quant Small Cap','cty':'in','type':'mf','value':400000,'paid':300000,'hist':[['2026-06-01',400000]]},
      {'id':'m1','name':'Mirae ELSS','cty':'in','type':'mf','value':100000,'paid':90000,'hist':[['2026-06-01',100000]]}]
    put(pg,st)
    check('Home has a Spare money shortcut',pg.locator('.jump [data-sheet="xtra"]').count()==1)
    check('Plan card offers Invest extra money',pg.locator('.card.plan [data-sheet="xtra"]').count()==1)
    pg.locator('.jump [data-sheet="xtra"]').click();pg.wait_for_timeout(250)
    check('Invest extra sheet opens with an amount box and quick amounts',pg.locator('#xamt').count()==1 and pg.locator('[data-xamt="1000"]').count()==1)
    pg.click('[data-xamt="1000"]');pg.wait_for_timeout(150)
    r=rows(pg);check('Quick amount fills in and shows a plan',pg.input_value('#xamt')=='1000' and len(r)>=1,r)
    check('With the emergency fund full and no debts, £1,000 goes to the ISA',r and r[0][0]=='Stocks & shares ISA' and r[0][1]==1000,r)
    check('Shows the effect on the freedom date','sooner' in pg.inner_text('#xres'))
    # moving back unsure (default): no pension; beyond the ISA room, India long-term with a concentration hint
    amount(pg,20000);r=dict(rows(pg))
    check('ISA room accounts for £5,000 already paid in this tax year',r.get('Stocks & shares ISA')==15000,r)
    check('Not sure about moving back: no pension suggestion, the rest goes to India',('Top up your pension' not in r) and r.get('Long-term investing in India')==5000,r)
    check('India part shows rupees and the transfer checker','≈ ₹' in pg.inner_text('#xres') and pg.locator('#xres [data-sheet="transfer"]').count()==1)
    check('Concentrated Indian funds get a spread-the-risk hint','80% of your Indian funds are with Quant' in pg.inner_text('#xres'),pg.inner_text('#xres')[-400:])
    # staying in the UK: higher-rate taxpayer gets a pension share
    pg.select_option('#xback','never');pg.wait_for_timeout(200);r=dict(rows(pg))
    check('Staying in the UK on a higher salary: pension gets 30% before the ISA',r.get('Top up your pension')==6000 and r.get('Stocks & shares ISA')==14000,r)
    check('Moving-back choice is saved',state(pg)['profile']['backPlan']=='never')
    # record into the ISA
    pg.select_option('#xback','unsure');pg.wait_for_timeout(150)
    amount(pg,1000);check('ISA row defaults to recording in your ISA',pg.locator('[data-xh="0"]').input_value()=='isa')
    pg.click('[data-xrec]');pg.wait_for_timeout(300)
    isa=[h for h in state(pg)['holdings'] if h['id']=='isa'][0]
    check('Recording adds the money to the ISA',abs(isa['value']-9000)<0.01 and abs(isa['paid']-8000)<0.01,(isa['value'],isa['paid']))
    pg.locator('.jump [data-sheet="xtra"]').click();pg.wait_for_timeout(200);pg.fill('#xamt','500');pg.wait_for_timeout(150);r=dict(rows(pg))
    check('After recording, the ISA room shrinks',r.get('Stocks & shares ISA')==500 and pg.input_value('#xamt')=='500')
    pg.click('[data-close]');pg.wait_for_timeout(150)
    # emergency fund short comes first
    st=state(pg);st['holdings']=[h for h in st['holdings'] if h['id']!='sav'];st['profile']['savedUK']=1000;put(pg,st)
    pg.locator('.jump [data-sheet="xtra"]').click();pg.wait_for_timeout(200);amount(pg,800);r=rows(pg)
    check('A short emergency fund comes first',r[0][0]=='Emergency savings' and r[0][1]==800,r)
    pg.click('[data-xrec]');pg.wait_for_timeout(250)
    check('With no savings holding, recording adds to your savings figure',state(pg)['profile']['savedUK']==1800)
    # moving back: checklist section and ISA note
    pg.locator('[data-tab="plan"]:visible').first.click();pg.wait_for_timeout(150);pg.locator('[data-tab="check"]:visible').first.click();pg.wait_for_timeout(250)
    pg.click('[data-phase="back"]');pg.wait_for_timeout(200)
    check('Checklist has a Moving back section',pg.locator('#backsel').count()==1)
    pg.select_option('#backsel','never');pg.wait_for_timeout(250)
    check('Staying in the UK: nothing to do',pg.locator('[data-btick]').count()==0 and 'Nothing to do here' in pg.inner_text('main'))
    pg.select_option('#backsel','2029');pg.wait_for_timeout(250)
    check('Choosing a year lists the steps',pg.locator('[data-btick]').count()==8 and 'Moving back in 2029' in pg.inner_text('main'))
    pg.click('[data-btask="b-sell"]');pg.wait_for_timeout(200);txt=pg.inner_text('.sheet')
    check('Away 6 years: likely RNOR window explained','RNOR' in txt and 'March 2031' in txt,txt[:200])
    pg.click('[data-bclose]');pg.wait_for_timeout(200)
    check('Marking a step done ticks it',state(pg)['checks'].get('b-sell') is True and pg.locator('[data-btick="b-sell"][aria-checked="true"]').count()==1)
    pg.select_option('#backsel','2026');pg.wait_for_timeout(250);pg.click('[data-btask="b-sell"]');pg.wait_for_timeout(200)
    check('Away under 5 years: advises selling before moving back','before you move back' in pg.inner_text('.sheet'))
    pg.click('[data-close]');pg.wait_for_timeout(150)
    check('Checklist still fits on one screen with the new section',pg.evaluate("(()=>{const m=document.querySelector('main');return m.scrollHeight-m.clientHeight})()")<=400)
    pg.locator('[data-tab="wealth"]:visible').first.click();pg.wait_for_timeout(250);pg.locator('[data-wtype="uk:isa"]').first.click();pg.wait_for_timeout(250)
    check('ISA details show what happens if you move back',pg.locator('.sheet .isanote').count()==1 and 'Tax-free selling window' in pg.inner_text('.sheet'))
    pg.click('[data-close]');pg.wait_for_timeout(150)
    # month-end prompt (3 days before pay day)
    st=state(pg);st['profile']['payday']=1;st['profile']['savedUK']=50000;put(pg,st)
    ctx2=b.new_context(viewport={'width':390,'height':844});p2=ctx2.new_page();p2.on('pageerror',lambda e:errs.append(str(e)))
    for h in ['api.gdeltproject.org','www.gov.uk','api.mfapi.in','api.frankfurter.dev','open.er-api.com']:p2.route(f'https://{h}/**',lambda r:r.abort())
    p2.clock.set_fixed_time('2026-11-28T10:00:00');p2.goto(URL);p2.evaluate("s=>localStorage.setItem('setu-v1',JSON.stringify(s))",state(pg));p2.reload();p2.wait_for_selector('[data-tab="home"]:visible',timeout=8000)
    nud=p2.locator('.nudge[data-go="sheet:xtra"]')
    check('Near pay day, Home suggests investing what’s spare',nud.count()==1 and 'spare this month' in nud.inner_text(),p2.inner_text('.nudges')[:200] if p2.locator('.nudges').count() else 'no nudges')
    if nud.count():
        nud.click();p2.wait_for_timeout(250);check('The prompt opens Invest extra money with the spare amount filled in',p2.locator('#xamt').count()==1 and (p2.input_value('#xamt') or '0')!='0')
    ctx2.close()
    check('No page errors',not errs,errs[:3])
    b.close()
finally:
    srv.terminate()
bad=[n for n,ok in R if not ok]
print('\nEXTRA CHECKS: '+('ALL PASSED' if not bad else 'FAILED: '+', '.join(bad)))
sys.exit(1 if bad else 0)
