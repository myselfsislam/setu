"""Import investments from a statement (.xlsx / .csv). Uses a made-up statement and a fake price service. Prints PASS/FAIL."""
import os,sys,subprocess,time,json,zipfile,io,re
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT=8785
OUT=os.path.join(ROOT,'tests','.tmp');os.makedirs(OUT,exist_ok=True)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
R=[]
def check(name,cond,detail=''):
    R.append((name,bool(cond)));print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(detail) if detail else ''))
# --- a made-up holdings report, written as a real .xlsx (shared strings, deflate) ---
ROWS=[['Holdings report as on 13-11-2026'],[],['Name','TEST USER'],['PAN','ABCDE1234F'],[],
 ['Fund Name','ISIN','Total Units','Invested Value','Current Value','Folio Number'],
 ['Alpha Flexi Cap Fund Direct Plan Growth','INF000A01011','100.000','9000.00','10000.00','111'],
 ['Beta Liquid Fund Direct Plan Growth','INF000B01012','10.000','4000.00','4500.00','222'],
 ['Alpha Flexi Cap Fund Direct Plan Growth','INF000A01011','50.000','4500.00','5000.00','333'],
 ['Gamma Unknown Fund Direct Growth','INF000C01013','20.000','2000.00','2600.00','444']]
def col(i):
    s='';i+=1
    while i:i,r=divmod(i-1,26);s=chr(65+r)+s
    return s
def xlsx(path,rows):
    strs=[];idx={}
    def si(v):
        if v not in idx:idx[v]=len(strs);strs.append(v)
        return idx[v]
    sd=''.join('<row r="%d">%s</row>'%(r+1,''.join('<c r="%s%d" t="s"><v>%d</v></c>'%(col(c),r+1,si(v)) for c,v in enumerate(row))) for r,row in enumerate(rows))
    esc=lambda x:x.replace('&','&amp;').replace('<','&lt;')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr('xl/workbook.xml','<workbook/>')
        z.writestr('xl/sharedStrings.xml','<?xml version="1.0" encoding="UTF-8"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">%s</sst>'%''.join('<si><t>%s</t></si>'%esc(s) for s in strs))
        z.writestr('xl/worksheets/sheet1.xml','<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>'%sd)
X1=os.path.join(OUT,'holdings.xlsx');xlsx(X1,ROWS)
ROWS2=[r[:] for r in ROWS];ROWS2[6][2]='120.000';ROWS2[6][3]='11000.00'   # a newer statement: more units of Alpha
X2=os.path.join(OUT,'holdings-newer.xlsx');xlsx(X2,ROWS2)
CSV=os.path.join(OUT,'holdings.csv');open(CSV,'w').write('\n'.join(','.join('"%s"'%c for c in r) for r in ROWS))
BAD=os.path.join(OUT,'notes.txt');open(BAD,'w').write('hello')
# --- fake mfapi.in ---
FUNDS={'900001':('Alpha Flexi Cap Fund - Direct Plan - Growth','INF000A01011',100.0),'900002':('Beta Liquid Fund - Direct Plan - Growth','INF000B01012',460.0),
       '900003':('Alpha Flexi Cap Fund - Regular Plan - Growth','INF000A09999',95.0)}
hits={'latest_first':0}
def handle(route):
    u=urlparse(route.request.url);q=parse_qs(u.query);path=u.path
    if path=='/mf/search':
        t=q.get('q',[''])[0].lower();res=[{'schemeCode':int(c),'schemeName':n} for c,(n,i,p) in FUNDS.items() if any(w in n.lower() for w in t.split()[:1])]
        return route.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps(res))
    m=re.match(r'/mf/(\d+)(/latest)?$',path)
    if m and m.group(1) in FUNDS:
        n,isin,px=FUNDS[m.group(1)]
        if m.group(2) and m.group(1)=='900001' and 't' not in q:   # first try fails like a CDN copy without CORS; the fresh retry works
            hits['latest_first']+=1;return route.abort()
        pts=[{'date':'%02d-11-2026'%d,'nav':str(px-(13-d)*0.5)} for d in range(13,0,-1)]
        return route.fulfill(status=200,content_type='application/json',headers={'access-control-allow-origin':'*'},body=json.dumps({'meta':{'scheme_name':n,'isin_growth':isin,'isin_div_reinvestment':None},'data':pts[:1] if m.group(2) else pts}))
    return route.fulfill(status=404,body='[]',headers={'access-control-allow-origin':'*'})
def state(pg): return pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")
def imported(pg): return [h for h in (state(pg).get('holdings') or []) if h.get('imp')]
def open_import(pg):
    pg.locator('[data-tab="home"]:visible').first.click();pg.wait_for_timeout(150)
    pg.locator('.jump [data-sheet2="haddpick"]').click();pg.wait_for_timeout(150);pg.click('[data-impopen]');pg.wait_for_timeout(150)
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.clock.set_fixed_time('2026-11-15T10:00:00')
    for h in ['api.gdeltproject.org','www.gov.uk','api.frankfurter.dev','open.er-api.com']:pg.route(f'https://{h}/**',lambda r:r.abort())
    pg.route('https://api.mfapi.in/**',handle)
    pg.goto(f'http://localhost:{PORT}/');pg.wait_for_timeout(400)
    pg.click('[data-wz="next"]');pg.click('[data-wz="full"]');pg.fill('[data-k="name"]','T');pg.fill('[data-k="age"]','30');pg.fill('[data-k="moved"]','2026-01-10');pg.click('[data-wz="next"]')
    pg.fill('[data-k="salary"]','50000');pg.fill('[data-k="rent"]','1200');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(700)
    open_import(pg)
    check('Import sheet opens from Add an investment',pg.locator('label[for="impfile"]').count()==1)
    pg.set_input_files('#impfile',BAD);pg.wait_for_timeout(500)
    check('An unreadable file shows a clear message',pg.locator('.sheet [role="alert"]').count()==1)
    pg.set_input_files('#impfile',X1);pg.wait_for_selector('[data-impgo]',timeout=30000)
    txt=pg.inner_text('.sheet')
    check('Same fund in two folios becomes one',pg.locator('.implist .li').count()==3 and '2 folios' in txt,pg.locator('.implist .li').count())
    check('Funds matched by ISIN get live prices; others use the statement',pg.locator('.implist .livebadge').count()==2 and 'value from statement' in txt)
    check('Regular plan with a similar name is not picked',not any(h for h in ['Regular'] if h in txt))
    check('A failed price request is retried with a fresh copy',hits['latest_first']>=1)
    pg.click('[data-impgo]');pg.wait_for_timeout(1200)
    H=imported(pg);a=[h for h in H if h.get('isin')=='INF000A01011'][0];bq=[h for h in H if h.get('isin')=='INF000B01012'][0];c=[h for h in H if h.get('isin')=='INF000C01013'][0]
    check('Three holdings added',len(H)==3,len(H))
    check('Live fund keeps exact units and what you put in',a.get('src')=='mf' and a['code']=='900001' and abs(a['hold']['units']-150)<1e-6 and abs(a['hold']['paid']-13500)<0.01,a.get('hold'))
    check('Live fund is valued at the latest price',abs(a['value']-150*100.0)<0.5,a['value'])
    check('Liquid fund counts towards the emergency fund',bq.get('goal')=='emergency')
    check('Unmatched fund uses the statement value',not c.get('src') and abs(c['value']-2600)<0.01 and abs(c['paid']-2000)<0.01)
    check('Opens Wealth after importing',pg.locator('.whero').count()==1 and pg.locator('.subnav [data-tab="wport"][aria-selected="true"]').count()==1)
    # newer statement updates the same funds, never duplicates
    open_import(pg);pg.set_input_files('#impfile',X2);pg.wait_for_selector('[data-impgo]',timeout=30000)
    check('Re-import marks funds as updates',pg.locator('.implist >> text=updates your existing one').count()==3)
    pg.click('[data-impgo]');pg.wait_for_timeout(1000)
    H=imported(pg);a=[h for h in H if h.get('isin')=='INF000A01011'][0]
    check('Newer statement updates units, no duplicates',len(H)==3 and abs(a['hold']['units']-170)<1e-6,(len(H),a['hold']['units']))
    # CSV works too
    pg.evaluate("()=>{const s=JSON.parse(localStorage.getItem('setu-v1'));s.holdings=[];localStorage.setItem('setu-v1',JSON.stringify(s));}");pg.reload();pg.wait_for_timeout(500)
    open_import(pg);pg.set_input_files('#impfile',CSV);pg.wait_for_selector('[data-impgo]',timeout=30000)
    check('CSV statements import too',pg.locator('.implist .li').count()==3)
    pg.click('[data-close]');pg.wait_for_timeout(150)
    pg.locator('[data-sheet="settings"]:visible').first.click();pg.wait_for_timeout(200);pg.click('[data-setgrp="data"]');pg.wait_for_timeout(200)
    check('Settings lists Import investments',pg.locator('[data-set="import"]').count()==1)
    check('No page errors',not errs,errs[:2])
    b.close()
finally:
    srv.terminate()
    for f in (X1,X2,CSV,BAD):
        try:os.remove(f)
        except OSError:pass
bad=[n for n,ok in R if not ok]
print('\nIMPORT CHECKS: '+('ALL PASSED' if not bad else 'FAILED: '+', '.join(bad)))
sys.exit(1 if bad else 0)
