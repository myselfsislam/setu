import os,sys,subprocess,time,json,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root
from playwright.sync_api import sync_playwright
import subprocess,time,json,collections
PORT=8781
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
AXE=open(os.path.join(ROOT,'node_modules','axe-core','axe.min.js')).read()
allv=collections.defaultdict(set)
def scan(pg,label):
    pg.add_script_tag(content=AXE)
    res=pg.evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}}).then(r=>r.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,n:v.nodes.length,t:v.nodes.slice(0,2).map(x=>x.target.join(' ')+' :: '+(x.failureSummary||'').split('\\n')[1])})))")
    for v in res: allv[(v['id'],v['impact'],v['help'])].add(label+' x'+str(v['n'])+' '+'; '.join(v['t'])[:220])
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    for scheme in ('light','dark'):
      for (w,h) in [(390,844),(1440,900)]:
        ctx=b.new_context(viewport={'width':w,'height':h},color_scheme=scheme);pg=ctx.new_page()
        for host in ['api.gdeltproject.org','www.gov.uk','api.mfapi.in','api.frankfurter.dev']:pg.route(f'https://{host}/**',lambda r:r.abort())
        pg.goto(f'http://localhost:{PORT}/');pg.wait_for_timeout(300);tag=f'{scheme}/{w}'
        scan(pg,tag+' intro');pg.click('[data-wz="next"]');scan(pg,tag+' step1');pg.click('[data-wz="next"]')
        pg.fill('[data-k="salary"]','48000');pg.fill('[data-k="rent"]','1150');scan(pg,tag+' step2');pg.click('[data-wz="next"]')
        pg.click('[data-debt="card"]');pg.wait_for_timeout(300);scan(pg,tag+' debt sheet');pg.fill('[data-f="bal"]','25000');pg.click('[data-form="save"]');pg.wait_for_timeout(100)
        scan(pg,tag+' step3');pg.click('[data-wz="next"]');scan(pg,tag+' step4');pg.click('[data-wz="next"]');pg.click('[data-seg="homeOn"][data-v="true"]');pg.fill('[data-k="homeCost"]','7500000');pg.fill('[data-k="retireAge"]','50');scan(pg,tag+' step5')
        pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(1500)
        pg.evaluate("()=>{const S0=JSON.parse(localStorage.getItem('setu-v1'));for(let d=1;d<=10;d++)S0.items.push({id:'s'+d,date:'2026-09-'+String(d).padStart(2,'0'),cat:'groceries',amt:10+d,note:'Shop '+d});localStorage.setItem('setu-v1',JSON.stringify(S0));}");pg.reload();pg.wait_for_timeout(1200)
        for t in ['home','check','spend','goals']:
            pg.locator(f'[data-tab="{t}"]:visible').first.click();pg.wait_for_timeout(900);scan(pg,tag+' '+t)
        pg.locator('[data-tab="goals"]:visible').first.click();pg.click('[data-funds="retire"]');pg.wait_for_timeout(500);scan(pg,tag+' funds sheet');pg.click('[data-close]')
        pg.click('[data-sheet="settings"]:visible');pg.wait_for_timeout(300);scan(pg,tag+' settings');pg.click('[data-set="transfer"]');pg.wait_for_timeout(300);scan(pg,tag+' transfer');pg.click('[data-close]')
        if w>1400:
            pg.click('[data-rtab="news"]');pg.wait_for_timeout(600);scan(pg,tag+' news')
        ctx.close()
    b.close()
finally: srv.terminate()
for (i,imp,hlp),where in sorted(allv.items(),key=lambda x:x[0][1] or ''):
    print(f'[{imp}] {i}: {hlp}');[print('    ',w) for w in sorted(where)[:5]]
print('TOTAL rule types:',len(allv))
sys.exit(1 if allv else 0)
