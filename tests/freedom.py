"""Freedom, Growth and Autopilot checks. Prints PASS/FAIL per check."""
import os,sys,subprocess,time,json
from datetime import date,timedelta
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8784
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://localhost:{PORT}/'
R=[]
def check(name,cond,detail=''):
    R.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(detail) if detail else ''))
def go(pg,parent,sub):
    pg.locator(f'[data-tab="{parent}"]:visible').first.click();pg.wait_for_timeout(150)
    pg.locator(f'[data-tab="{sub}"]:visible').first.click();pg.wait_for_timeout(250)
def state(pg): return pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")
def overflow(pg): return pg.evaluate("document.documentElement.scrollWidth-document.documentElement.clientWidth")
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(viewport={'width':390,'height':844},accept_downloads=True);pg=ctx.new_page()
    errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    for host in ['api.gdeltproject.org','www.gov.uk','api.mfapi.in','api.frankfurter.dev','open.er-api.com']:
        pg.route(f'https://{host}/**',lambda r:r.abort())
    pg.goto(URL);pg.wait_for_timeout(400)
    # quick setup through the wizard
    pg.click('[data-wz="next"]');pg.click('[data-wz="full"]')
    pg.fill('[data-k="name"]','Asha');pg.fill('[data-k="age"]','30');pg.fill('[data-k="moved"]','2026-01-10');pg.click('[data-wz="next"]')
    pg.fill('[data-k="salary"]','60000');pg.fill('[data-k="rent"]','1200');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]')
    pg.fill('[data-k="savedUK"]','8000');pg.fill('[data-k="invested"]','500000');pg.click('[data-wz="next"]')
    pg.fill('[data-k="retireAge"]','50');pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(800)
    check('Setup completes',pg.locator('.hero').count()==1)
    # easy mode: guided Home
    check('Home shows Get started with progress',pg.locator('.gstart').count()==1 and 'of 6 done' in pg.inner_text('.gstart'))
    check('Home shows shortcuts to every area',pg.locator('.jump .jt').count()==6)
    pg.locator('.jump [data-sheet2="haddpick"]').click();pg.wait_for_timeout(250)
    check('Add investment shortcut asks UK or India',pg.locator('.sheet [data-hadd="uk"]').count()==1 and pg.locator('.sheet [data-hadd="in"]').count()==1)
    pg.click('[data-close]');pg.wait_for_timeout(150)
    pg.locator('.jump [data-tab="free"]').click();pg.wait_for_timeout(300)
    check('Shortcut opens Freedom',pg.locator('#fihero').count()==1 and pg.locator('.guide').count()==1)
    pg.click('[data-gseen="free"]');pg.wait_for_timeout(200)
    check('Got it hides the page intro for good',pg.locator('.guide').count()==0 and state(pg)['seen'].get('g-free')==1)
    pg.locator('[data-tab="home"]:visible').first.click();pg.wait_for_timeout(250)
    check('Visiting Freedom ticks its Get started step','see when you could stop working' not in pg.inner_text('.gstart button.gs').lower() if pg.locator('.gstart button.gs').count() else True)
    pg.click('[data-gshide]');pg.wait_for_timeout(200)
    check('Get started can be hidden',pg.locator('.gstart').count()==0 and state(pg).get('gsHide')==1)
    st=state(pg);keep=st.get('holdings');st['holdings']=[];pg.evaluate("s=>localStorage.setItem('setu-v1',JSON.stringify(s))",st);pg.reload();pg.wait_for_timeout(500)
    pg.locator('[data-tab="wealth"]:visible').first.click();pg.wait_for_timeout(250)
    check('Wealth has three simple tabs',pg.locator('.subnav button').count()==3)
    check('Empty Wealth leads with what to do',pg.locator('main .guide').count()==1 and pg.locator('main .whero').count()==0 and pg.locator('.wctylinks [data-tab="wuk"]').count()==1)
    pg.locator('.wctylinks [data-tab="wuk"]').click();pg.wait_for_timeout(250)
    check('UK view has a way back and keeps Portfolio selected',pg.locator('.wback').count()==1 and pg.locator('.subnav [data-tab="wport"][aria-selected="true"]').count()==1)
    # seed a manual UK ISA holding so rules have a target
    st=state(pg);t0=(date.today()-timedelta(days=200)).isoformat()
    st['holdings']=[{'id':'isa1','name':'Global ISA','cty':'uk','type':'isa','value':10000,'paid':9000,'hist':[[t0,9000],[date.today().isoformat(),10000]]},
                    {'id':'sav1','name':'Easy saver','cty':'uk','type':'savings','value':8000,'paid':8000,'hist':[[t0,8000]]}]
    pg.evaluate("s=>localStorage.setItem('setu-v1',JSON.stringify(s))",st);pg.reload();pg.wait_for_timeout(600)
    # Freedom
    go(pg,'plan','free')
    check('Freedom view renders',pg.locator('#fihero').count()==1 and pg.locator('#fichart svg').count()==1)
    w0=pg.inner_text('#fiwhen');check('Freedom shows a date or status',len(w0)>3,w0)
    txt=pg.inner_text('main');check('Freedom number shown',"Freedom number" in txt)
    check('Levers list sooner/later effects','sooner' in pg.inner_text('#filev'),pg.inner_text('#filev')[:120])
    s=pg.locator('[data-fi="extra"]');s.evaluate("el=>{el.value=2000;el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}))}");pg.wait_for_timeout(150)
    w1=pg.inner_text('#fiwhen');check('Extra investing slider updates freedom date',w1!=w0,(w0,w1))
    check('Slider choice saved',state(pg).get('fi',{}).get('extra')==2000)
    pg.click('[data-fiwhere="uk"]');pg.wait_for_timeout(200)
    check('Switch to UK uses £',"£" in pg.inner_text('#fihero') and pg.locator('[data-fiwhere="uk"][aria-checked="true"]').count()==1)
    pg.click('[data-fireset]');pg.wait_for_timeout(200)
    check('Reset clears levers',state(pg).get('fi',{}).get('extra') in (None,0))
    check('Freedom: no horizontal overflow (phone)',overflow(pg)<=0,overflow(pg))
    # Autopilot
    go(pg,'wealth','wauto')
    check('Autopilot view renders',pg.locator('.apmon').count()==1 and pg.locator('.apsug .li').count()>=1)
    pg.click('[data-apnew]');pg.wait_for_timeout(200)
    start=(date.today()-timedelta(days=95)).isoformat()
    pg.fill('[data-f="name"]','ISA top-up');pg.select_option('[data-f="hid"]','isa1');pg.select_option('[data-f="how"]','so')
    pg.fill('[data-f="amt"]','500');pg.fill('[data-f="day"]','1');pg.fill('[data-f="start"]',start);pg.fill('[data-f="step"]','10')
    pg.click('[data-form="save"]');pg.wait_for_timeout(300)
    st=state(pg);isa=[h for h in st['holdings'] if h['id']=='isa1'][0];r=st['autoRules'][0]
    # manual holdings only record from the day the rule was made (no back-filling into past values)
    check('Automatic rule saved',r['name']=='ISA top-up' and r['amt']==500 and r['how']=='so')
    expect=500 if date.today().day==1 else 0
    check('Manual holding not back-filled before rule creation',abs(isa['value']-(10000+expect))<1,isa['value'])
    # simulate the rule having been made 95 days ago: the next load should record the missed months
    st['autoRules'][0]['made']=start;st['autoRules'][0]['done']={}
    pg.evaluate("s=>localStorage.setItem('setu-v1',JSON.stringify(s))",st);pg.reload();pg.wait_for_timeout(500);go(pg,'wealth','wauto')
    st=state(pg);isa=[h for h in st['holdings'] if h['id']=='isa1'][0];n=len(st['autoRules'][0]['done'])
    check('Automatic rule records missed months',n>=3 and abs(isa['value']-(10000+500*n))<1 and abs(isa['paid']-(9000+500*n))<1,(n,isa['value'],isa['paid']))
    pg.reload();pg.wait_for_timeout(500);go(pg,'wealth','wauto')
    st2=state(pg);isa2=[h for h in st2['holdings'] if h['id']=='isa1'][0]
    check('Reloading does not record twice',abs(isa2['value']-isa['value'])<1,isa2['value'])
    # manual reminder rule, due today
    pg.click('[data-apnew]');pg.wait_for_timeout(200)
    pg.fill('[data-f="name"]','Top up saver');pg.select_option('[data-f="hid"]','sav1');pg.select_option('[data-f="how"]','manual')
    pg.fill('[data-f="amt"]','200');pg.fill('[data-f="day"]',str(date.today().day));pg.click('[data-form="save"]');pg.wait_for_timeout(300)
    check('Manual rule shows Mark done',pg.locator('[data-apdone]').count()==1)
    pg.locator('[data-tab="home"]:visible').first.click();pg.wait_for_timeout(300)
    check('Home nudges the due payment','Autopilot payment' in pg.inner_text('main'))
    go(pg,'wealth','wauto')
    pg.click('[data-apdone]');pg.wait_for_timeout(300)
    sav=[h for h in state(pg)['holdings'] if h['id']=='sav1'][0]
    check('Mark done adds to the holding',abs(sav['value']-8200)<1,sav['value'])
    check('Done rule shows as done',pg.locator('[data-apdone]').count()==0 and '✓ Done' in pg.inner_text('.apmon'))
    with pg.expect_download() as dl: pg.click('[data-apics]')
    ics=open(dl.value.path()).read()
    check('Calendar file has monthly reminders',ics.startswith('BEGIN:VCALENDAR') and ics.count('BEGIN:VEVENT')==4 and 'RRULE:FREQ=MONTHLY' in ics,ics.count('BEGIN:VEVENT'))
    # edit + pause + remove
    pg.locator('[data-apedit]').first.click();pg.wait_for_timeout(200);pg.select_option('[data-f="off"]','1');pg.click('[data-form="save"]');pg.wait_for_timeout(200)
    check('Pause a rule',state(pg)['autoRules'][0].get('off') is True and 'Paused' in pg.inner_text('.aprules'))
    pg.locator('[data-apedit]').nth(1).click();pg.wait_for_timeout(200);pg.click('[data-form="delete"]');pg.wait_for_timeout(200)
    st=state(pg);sav=[h for h in st['holdings'] if h['id']=='sav1'][0]
    check('Remove a rule keeps past investments',len(st['autoRules'])==1 and abs(sav['value']-8200)<1)
    pg.locator('[data-apsug="0"]').click();pg.wait_for_timeout(200)
    check('Suggestion opens a prefilled rule',pg.locator('[data-f="amt"]').input_value() not in ('','0'))
    pg.click('[data-close]');pg.wait_for_timeout(150)
    pg.click('[data-sheet2="aphow"]');pg.wait_for_timeout(200)
    check('How-to sheet opens','salary sacrifice' in pg.inner_text('.sheet'))
    pg.click('[data-close]');pg.wait_for_timeout(150)
    check('Autopilot: no horizontal overflow (phone)',overflow(pg)<=0,overflow(pg))
    # Growth
    go(pg,'wealth','wgrow')
    g=pg.inner_text('main')
    check('Growth view renders',pg.locator('.wchartcard svg').count()==1 and 'You put in' in g and 'Milestones' in g)
    check('Growth projection table',pg.locator('.gtbl').count()>=1 and '10 years' in g)
    check('Growth: no horizontal overflow (phone)',overflow(pg)<=0,overflow(pg))
    # sync carries the new data
    keys=pg.evaluate("(()=>{const m=document.documentElement.innerHTML.match(/var SYNC_KEYS=\\[([^\\]]*)\\]/);return m?m[1]:''})()");check('Sync keys include Autopilot, Freedom and guided-setup state',all("'%s'"%k in keys for k in ['autoRules','fi','seen','gsHide','xtraSeen']),keys)
    # desktop
    pg.set_viewport_size({'width':1366,'height':900});pg.wait_for_timeout(300)
    for parent,sub in [('plan','free'),('wealth','wauto'),('wealth','wgrow')]:
        go(pg,parent,sub);check(f'{sub}: no horizontal overflow (desktop)',overflow(pg)<=0,overflow(pg))
    # dark mode renders
    pg.emulate_media(color_scheme='dark');pg.wait_for_timeout(150);go(pg,'plan','free')
    check('Freedom renders in dark mode',pg.locator('#fihero').count()==1)
    check('No page errors',not errs,errs[:3])
    b.close()
finally:
    srv.terminate()
bad=[n for n,ok in R if not ok]
print('\nFREEDOM CHECKS: '+('ALL PASSED' if not bad else 'FAILED: '+', '.join(bad)))
sys.exit(1 if bad else 0)
