import os,sys,subprocess,time,json,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root
from playwright.sync_api import sync_playwright
srv=subprocess.Popen([sys.executable,'-m','http.server','8793'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
FAIL=0
URL='http://localhost:8793/'
sizes=[(320,640),(375,620),(390,700),(390,844),(430,932),(1024,768),(1280,800),(1366,768),(1440,900),(1920,1080)]
with sync_playwright() as p:
    b=p.chromium.launch()
    for (w,h) in sizes:
        ctx=b.new_context(viewport={'width':w,'height':h});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto(URL);pg.wait_for_timeout(300)
        pg.click('[data-wz="next"]');pg.fill('[data-k="name"]','Priya');pg.fill('[data-k="moved"]','2026-09-01');pg.click('[data-wz="next"]')
        wz2=pg.evaluate("(()=>{const m=document.querySelector('.wzshell');return m.scrollHeight-m.clientHeight})()")
        pg.fill('[data-k="salary"]','48000');pg.fill('[data-k="rent"]','1150');pg.click('[data-wz="next"]')
        pg.click('[data-debt="card"]');pg.fill('[data-f="bal"]','25000');pg.fill('[data-f="emi"]','5000');pg.click('[data-form="save"]');pg.wait_for_timeout(80)
        pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.fill('[data-k="retireAge"]','50');pg.click('[data-seg="homeOn"][data-v="true"]');pg.fill('[data-k="homeCost"]','7500000');pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(700)
        pg.evaluate("""()=>{const S0=JSON.parse(localStorage.getItem('setu-v1'));const cats=['groceries','transport','eating','shopping','other'];for(let d=1;d<=27;d++){S0.items.push({id:'s'+d,date:'2026-09-'+String(d).padStart(2,'0'),cat:cats[d%5],amt:5+(d*7)%40,note:'Item '+d});}S0.months={'2026-09':{salary:3150,carry:420}};localStorage.setItem('setu-v1',JSON.stringify(S0));}""")
        pg.reload();pg.wait_for_timeout(900)
        res=['wz2:'+('ok' if wz2<=2 else '+'+str(wz2))]
        for t in ['home','check','spend','wealth','goals']:
            pg.locator(f'[data-tab="{t}"]:visible').first.click();pg.wait_for_timeout(450)
            r=pg.evaluate("""(()=>{const m=document.querySelector('main');const els=[...m.children].filter(e=>getComputedStyle(e).display!=='none');
              const bx=els.map(e=>{const r=e.getBoundingClientRect();return {t:r.top,b:r.bottom,l:r.left,r:r.right}});let ov=0;
              for(let i=0;i<bx.length;i++)for(let j=i+1;j<bx.length;j++){const a=bx[i],c=bx[j];if(a.l<c.r-2&&c.l<a.r-2&&a.t<c.b-2&&c.t<a.b-2)ov++;}
              return [ov,m.scrollHeight-m.clientHeight,document.documentElement.scrollWidth-window.innerWidth]})()""")
            res.append(t+':'+('OVERLAP ' if r[0] else '')+('ok' if (r[1]<=2 or t in ('spend','goals','wealth')) else '+'+str(r[1]))+(' HSCROLL' if r[2]>0 else ''))
            pass
        print(w,h,res,errs);FAIL+=sum(1 for r in res if not r.endswith('ok'))+len(errs);ctx.close()
    b.close()
srv.terminate()
print('LAYOUT FAILURES:',FAIL);sys.exit(1 if FAIL else 0)
