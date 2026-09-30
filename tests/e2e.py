import os,sys,subprocess,time,json,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root
"""End-to-end functional audit of Setu. Prints PASS/FAIL per check."""
from playwright.sync_api import sync_playwright
import subprocess,time,json,re,os
PORT=8780
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://localhost:{PORT}/'
R=[]
def check(name,cond,detail=''):
    R.append((name,bool(cond),detail));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(detail) if detail else ''))
def fit(pg,sel='main'):
    return pg.evaluate(f"(()=>{{const m=document.querySelector('{sel}');return m?m.scrollHeight-m.clientHeight:0}})()")
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True);pg=ctx.new_page()
    errs=[];cons=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:cons.append(m.text) if m.type=='error' else None)
    pg.on('dialog',lambda d:d.accept())
    for host in ['api.gdeltproject.org','www.gov.uk','api.mfapi.in','api.frankfurter.dev','open.er-api.com']:
        pg.route(f'https://{host}/**',lambda r:r.abort())
    pg.goto(URL);pg.wait_for_timeout(400)
    check('Intro loads',pg.locator('.introhero').count()==1)
    # --- Wizard with XSS attempts and edge values ---
    pg.click('[data-wz="next"]')
    pg.fill('[data-k="name"]','<img src=x onerror=alert(1)>');pg.fill('[data-k="age"]','29');pg.fill('[data-k="moved"]','2026-09-01')
    pg.click('[data-wz="next"]')
    check('Step 2 Continue disabled without salary',pg.locator('[data-wz="next"]').is_disabled())
    pg.fill('[data-k="salary"]','48000');pg.fill('[data-k="rent"]','1150')
    check('Step 2 Continue enabled',not pg.locator('[data-wz="next"]').is_disabled())
    th=pg.inner_text('#th');check('Take-home hint shows',('£3,0' in th) or ('£3,1' in th),th)
    pg.click('[data-wz="next"]')
    for key,bal,emi in [('card','25000','5000'),('personal','300000','16500'),('car','1100000','23000')]:
        pg.click(f'[data-debt="{key}"]');pg.fill('[data-f="bal"]',bal);pg.fill('[data-f="emi"]',emi);pg.click('[data-form="save"]');pg.wait_for_timeout(80)
    check('Debt total shown',"₹14.3 L" in pg.inner_text('.hintline'),pg.inner_text('.hintline'))
    pg.click('[data-debt="car"]');pg.click('[data-form="delete"]');pg.wait_for_timeout(80)
    check('Debt remove works',"₹3.3 L" in pg.inner_text('.hintline'),pg.inner_text('.hintline'))
    pg.click('[data-wz="next"]');pg.fill('[data-k="savedUK"]','1000');pg.fill('[data-k="invested"]','600000');pg.fill('[data-k="sip"]','5000');pg.click('[data-wz="next"]')
    pg.fill('[data-k="retireAge"]','50');pg.click('[data-seg="homeOn"][data-v="true"]');pg.fill('[data-k="homeCost"]','7500000');pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(900)
    check('Home renders after setup',pg.locator('.hero').count()==1)
    check('XSS name escaped (no img element)',pg.locator('main img').count()==0 and pg.evaluate("!document.querySelector('img[src=\"x\"]')"))
    check('Home fits (390x844)',fit(pg)<=2,fit(pg))
    # plan sums equal money left (+carry)
    left=pg.evaluate("(()=>{const t=document.querySelector('.hero .big').textContent;return +t.replace(/[^0-9.-]/g,'')})()")
    check('Plan shows steps without money amounts',pg.locator('.step').count()>=2 and not any(c in pg.inner_text('.card.plan') for c in '£₹'),pg.inner_text('.card.plan')[:80])
    pg.click('.herohow');pg.wait_for_timeout(300)
    vals=pg.evaluate("[...document.querySelectorAll('.calct tr')].map(r=>{const t=r.querySelector('th').childNodes[0].textContent.trim(),v=(r.querySelector('td .cg')||r.querySelector('td')).textContent;const m=v.match(/£([\\d,.-]+)/);return [t,m?+m[1].replace(/,/g,''):0]})")
    mi=[v for t,v in vals if t.startswith('= Money in')][0];lf=[v for t,v in vals if t.startswith('= Left')][0];costs=sum(v for t,v in vals if t.startswith('−'))
    check('Left to save = money in minus all costs',abs(mi-costs-lf)<=6 and abs(lf-left)<=1,(mi,costs,lf,left))
    pg.click('[data-close]');pg.wait_for_timeout(200)
    # nudges clickable
    pg.locator('.nudge').first.click();pg.wait_for_timeout(300);check('Nudge opens something',pg.locator('.sheet').count()==1 or pg.locator('[aria-current="page"]:visible').inner_text()!='Home')
    if pg.locator('[data-close]').count():pg.click('[data-close]')
    pg.locator('[data-tab="home"]:visible').first.click();pg.wait_for_timeout(200)
    # plan sheet
    pg.locator('.step').first.click();pg.wait_for_timeout(300);check('Plan step sheet opens',pg.locator('.sheet h2').count()==1);pg.click('[data-close]')
    # --- Checklist ---
    pg.locator('[data-tab="check"]:visible').first.click();pg.wait_for_timeout(300)
    for t in ['nro','nre','kyc','lenders','sim']:pg.click(f'[data-tick="{t}"]');pg.wait_for_timeout(60)
    check('Phase complete marker',pg.locator('.ph.full').count()>=1)
    pg.click('[data-tick="sim"]');check('Untick works',pg.locator('[data-tick="sim"][aria-checked="false"]').count()==1)
    pg.click('[data-task="nre"]');pg.wait_for_timeout(200);check('Task sheet opens',pg.locator('.sheet h2').inner_text()=='Open an NRE account');pg.click('[data-close]')
    pg.click('[data-task="nro"]');pg.wait_for_timeout(200);check('Task pop-up has no email or link box',pg.locator('.sheet .emailcta,.sheet .official').count()==0);pg.click('[data-close]');pg.wait_for_timeout(200)
    pg.click('.iact[data-email="nro"]');pg.wait_for_timeout(200)
    check('Email draft opens with placeholders',pg.locator('#emBody').count()==1 and '[account number]' in pg.input_value('#emBody') and 'square brackets' in pg.inner_text('#emHint'))
    check('Email draft escapes user name',pg.locator('.sheet img').count()==0)
    pg.fill('#emSub','Test subject');pg.wait_for_timeout(100);check('Open-in-email link follows edits','Test%20subject' in (pg.get_attribute('#emOpen','href') or ''))
    pg.click('[data-close]')
    check('Checklist fits',fit(pg)<=2,fit(pg))
    # --- Spending ---
    pg.locator('[data-tab="spend"]:visible').first.click();pg.wait_for_timeout(300)
    pg.fill('#amt','-5');pg.click('[data-add]');check('Negative amount rejected',pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.length")==0)
    pg.click('[data-cat="groceries"]');pg.fill('#amt','42.5');pg.fill('#note','<script>alert(1)</script>Tesco');pg.keyboard.press('Enter');pg.wait_for_timeout(200)
    check('Enter key adds spending',pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.length")==1)
    check('Note escaped in table',pg.locator('.stbl script').count()==0 and '<script>' in pg.locator('.twhat').first.inner_text())
    pg.click('[data-undo]');pg.wait_for_timeout(200);check('Undo removes',pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.length")==0)
    for amt,note,cat in [('42','Tesco','groceries'),('35','Oyster','transport'),('18.5','Dishoom','eating')]:
        pg.click(f'[data-cat="{cat}"]');pg.fill('#amt',amt);pg.fill('#note',note);pg.click('[data-add]');pg.wait_for_timeout(100)
    pg.locator('tr[data-item]').first.click();pg.wait_for_timeout(200);pg.fill('[data-f="amt"]','20');pg.click('[data-form="save"]');pg.wait_for_timeout(200)
    check('Edit spending saves',20 in pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.map(x=>x.amt)"))
    pg.locator('tr[data-item]').first.click();pg.wait_for_timeout(200);pg.click('[data-form="delete"]');pg.wait_for_timeout(200)
    check('Delete spending works',pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.length")==2)
    pg.click('[data-sheet="settings"]:visible');pg.click('[data-set="budgets"]');pg.wait_for_timeout(200);pg.click('.sheet [data-cat-edit="groceries"]');pg.fill('[data-f="budget"]','250');pg.click('[data-form="save"]');pg.wait_for_timeout(300)
    check('Budget edit via Settings works','£250' in pg.inner_text('.sheet'));pg.click('[data-close]')
    pg.click('[data-monthin]');pg.fill('[data-f="salary"]','3100');pg.fill('[data-f="carry"]','200');pg.click('[data-form="save"]');pg.wait_for_timeout(200)
    check('Money in saved','£3,300' in pg.inner_text('.moneyin'),pg.inner_text('.moneyin').replace('\n',' '))
    pg.click('.rchip');pg.click('[data-recur="new"]');pg.fill('[data-f="name"]','Netflix');pg.fill('[data-f="amt"]','10.99');pg.fill('[data-f="day"]',str(__import__('datetime').date.today().day));pg.click('[data-form="save"]');pg.wait_for_timeout(400)
    check('Repeating cost auto-added',any(x['note']=='Netflix' for x in pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items")))
    pg.click('[data-close]');pg.wait_for_timeout(200)
    pg.fill('#sq','oys');pg.wait_for_timeout(150);check('Search filters',pg.locator('tr[data-item]').count()==1);pg.fill('#sq','')
    with pg.expect_download() as dl: pg.click('[data-csv="month"]')
    txt=open(dl.value.path()).read();check('CSV export valid',txt.startswith('Date,What') and txt.count('\n')>=2)
    check('Cannot go back before the day you started',pg.locator('[data-month]').first.is_disabled())

    pg.click('.mimid');pg.wait_for_timeout(200);pg.fill('[data-cost="rent"]','1200');pg.fill('[data-cost="everyday"]','500');pg.click('[data-costs-save]');pg.wait_for_timeout(300)
    P=pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")
    check('Monthly costs editor saves',P['profile']['rent']==1200 and P['profile']['everyday']==500,(P['profile']['rent'],P['profile']['everyday']))
    pg.click('.mimid');pg.wait_for_timeout(200);pg.fill('#iitems .irow:nth-child(1) .iname','Term insurance');pg.click('[data-iadd]');pg.fill('#iitems .irow:last-child .iname','Phone bill');pg.fill('#iitems .irow:last-child .ival','500');pg.click('[data-costs-save]');pg.wait_for_timeout(300)
    P2=pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")['profile']
    check('India payments can be renamed and added',[x['name'] for x in P2['indiaItems']][:1]==['Term insurance'] and any(x['name']=='Phone bill' and x['amt']==500 for x in P2['indiaItems']) and P2['indiaOther']==sum(x['amt'] for x in P2['indiaItems'] if x['kind']!='invest'))
    before=pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")['profile']
    pg.click('.mimid');pg.wait_for_timeout(200);pg.select_option('#iitems .irow:last-child .isrc','in');pg.click('[data-costs-save]');pg.wait_for_timeout(300)
    P3=pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")['profile']
    check('India payment can be paid from the Indian account',P3['indiaItems'][-1].get('src')=='in' and 'Indian account' in pg.inner_text('.moneyin') or P3['indiaItems'][-1].get('src')=='in')
    check('Personal spending equals category budgets',abs(sum(c['budget'] for c in P['cats'])-P['profile']['everyday'])<1)
    pg.click('.mlabel');pg.wait_for_timeout(200);pg.select_option('[data-f="payday"]','25');pg.click('[data-form="save"]');pg.wait_for_timeout(300)
    check('Month can start on pay day',' – ' in pg.inner_text('.mlabel') and pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).profile.payday")==25,pg.inner_text('.mlabel'))
    pg.click('.mlabel');pg.wait_for_timeout(200);pg.select_option('[data-f="payday"]','1');pg.click('[data-form="save"]');pg.wait_for_timeout(300)
    pg.fill('#amt','5');pg.fill('#note','Past bus');pg.fill('#sdt','2026-08-03');pg.click('[data-add]');pg.wait_for_timeout(300)
    check('Dates before you started are not allowed',pg.get_attribute('#sdt','min')==pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).startDate") and '2026-08-03' not in pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.map(x=>x.date)"))

    pg.select_option('#sr','all');pg.wait_for_timeout(300);check('Date range filter shows everything since you started',pg.locator('tr[data-item]').count()>=3 and 'since' in pg.inner_text('.tblcard .row-b'))
    pg.select_option('#sr','cycle');pg.wait_for_timeout(200)
    check('Category buttons need no sideways scrolling',pg.evaluate("(()=>{const c=document.querySelector('.v-spend .chips');return c.scrollWidth<=c.clientWidth})()"))
    sp0=pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.length");pg.click('.chips [data-cat="invest"]');pg.fill('#amt','200');pg.fill('#note','ISA');pg.click('[data-add]');pg.wait_for_timeout(300)
    check('Investments can be logged and are not counted as spending',pg.locator('.invline').count()==1 and pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.some(x=>x.cat==='invest')"))
    check('Spending has no sideways scroll',pg.evaluate('document.documentElement.scrollWidth-innerWidth')<=0)
    check('Spending log shows rows in full',pg.evaluate("(()=>{const w=document.querySelector('.tblwrap');return !w||w.scrollHeight<=w.clientHeight+2})()"))
    # --- Goals ---
    pg.locator('[data-tab="goals"]:visible').first.click();pg.wait_for_timeout(300)
    pg.click('[data-funds="retire"]');pg.wait_for_timeout(400);pg.click('[data-choose="retire:n50"]');pg.wait_for_timeout(300)
    check('Fund choice saved',pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).profile.retFund")=='n50')
    pg.click('[data-sheet="goals"]');pg.fill('[data-f="retireAge"]','55');pg.click('[data-form="save"]');pg.wait_for_timeout(300)
    check('Goals edit works','55' in pg.inner_text('main'))
    check('Rates and pound-to-rupee are at the top of Goals',pg.evaluate("document.querySelector('main').children[1].className")=='gtop')
    check('Goals has no sideways scroll',pg.evaluate('document.documentElement.scrollWidth-innerWidth')<=0)
    # --- Settings ---
    pg.click('[data-sheet="settings"]:visible');pg.wait_for_timeout(200);rows=pg.locator('[data-set]').count();check('Settings rows',rows>=8,rows)
    pg.click('[data-set="transfer"]');pg.wait_for_timeout(300);pg.fill('#tfA','500');pg.fill('#tfF','3');pg.fill('#tfR','120');pg.wait_for_timeout(100)
    check('Transfer checker computes','Hidden cost' in pg.inner_text('#tfOut'));pg.click('[data-close]')
    pg.click('[data-sheet="settings"]:visible');pg.click('[data-set="assume"]');pg.fill('[data-f="inf"]','7');pg.click('[data-form="save"]');pg.wait_for_timeout(200)
    check('Assumptions save',pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).profile.inf")==7)
    pg.click('[data-sheet="settings"]:visible');pg.click('[data-set="backup"]');pg.wait_for_timeout(200)
    with pg.expect_download() as dl: pg.click('[data-bkfile]')
    bk=json.load(open(dl.value.path()));check('Backup file valid',bk.get('v')==1 and bk.get('profile'))
    pg.click('[data-close]')
    # edit setup preserves data, cancel discards
    pg.click('[data-sheet="settings"]:visible');pg.click('[data-set="setup"]');pg.wait_for_timeout(200);pg.click('[data-wz="cancel"]');pg.wait_for_timeout(200)
    check('Cancel setup returns to app',pg.locator('main').count()==1)
    # persistence across reload
    pg.reload();pg.wait_for_timeout(600);check('Data persists after reload',pg.locator('main').count()==1 and pg.evaluate("!!JSON.parse(localStorage.getItem('setu-v1')).profile"))
    # reset
    pg.click('[data-sheet="settings"]:visible');pg.click('[data-set="reset"]');pg.wait_for_timeout(300)
    check('Start over clears data',pg.locator('.introhero').count()==1)
    # restore
    pg.click('.foot [data-sheet="backup"]');pg.wait_for_timeout(200);open(os.path.join(ROOT,'.bk-test.json'),'w').write(json.dumps(bk));pg.set_input_files('#bkin',os.path.join(ROOT,'.bk-test.json'));pg.wait_for_timeout(500)
    check('Restore from file works',pg.locator('main').count()==1 and pg.evaluate("JSON.parse(localStorage.getItem('setu-v1')).items.length")>=2)
    check('No page errors',not errs,errs[:3])
    check('No console errors (excluding blocked network)',not [c for c in cons if 'net::' not in c and 'Failed to load' not in c and 'CORS' not in c],cons[:3])
    ctx.close()
    # --- old-format data migration ---
    ctx=b.new_context();pg=ctx.new_page();pe=[];pg.on('pageerror',lambda e:pe.append(str(e)))
    pg.goto(URL)
    old={"v":1,"profile":{"name":"Old","age":33,"moved":"2026-07-26","household":"couple","salary":72000,"pension":5,"rent":1600,"bills":350,"everyday":900,"india":96389,"fx":129,"debt":"card","debtINR":25000,"invested":2600000,"savedUK":0,"efMonths":4,"retireAge":43,"retireSpend":75000,"homeOn":True,"homeCost":15000000,"homeYear":2031,"homeSaved":0,"inf":6,"ret":10,"wd":3.5},"checks":{},"items":[],"cats":None}
    pg.evaluate("s=>localStorage.setItem('setu-v1',s)",json.dumps(old));pg.reload();pg.wait_for_timeout(600)
    check('Old data migrates without errors',pg.locator('.hero').count()==1 and not pe,pe[:2])
    ctx.close()
    # --- corrupted storage ---
    ctx=b.new_context();pg=ctx.new_page();pe=[];pg.on('pageerror',lambda e:pe.append(str(e)))
    pg.goto(URL);pg.evaluate("localStorage.setItem('setu-v1','{not json')");pg.reload();pg.wait_for_timeout(400)
    check('Corrupted storage falls back to intro',pg.locator('.introhero').count()==1 and not pe,pe[:2])
    ctx.close()
    b.close()
finally:
    srv.terminate()
print('\nSUMMARY: %d passed, %d failed'%(sum(1 for r in R if r[1]),sum(1 for r in R if not r[1])))
sys.exit(1 if any(not r[1] for r in R) else 0)
