"""Markets & News panel: hidden on phones, collapsed on laptops, open on big screens; toggles and remembers."""
import os,sys,subprocess,time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
PORT=8815
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
BAD=[]
def check(n,c,d=''):
    print(('PASS ' if c else 'FAIL ')+n+(' | '+str(d) if d else ''));
    if not c:BAD.append(n)
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    for (w,h,exp) in [(390,844,'none'),(1024,768,'collapsed'),(1440,900,'collapsed'),(1920,1080,'dock')]:
        ctx=b.new_context(viewport={'width':w,'height':h});pg=ctx.new_page()
        pg.route('https://static.cloudflareinsights.com/**',lambda r:r.abort())
        pg.goto(f'http://localhost:{PORT}/');pg.wait_for_timeout(300)
        pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.fill('[data-k="salary"]','48000');pg.fill('[data-k="rent"]','1150');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.click('[data-wz="next"]');pg.click('.foot [data-wz="finish"].go');pg.wait_for_timeout(700)
        mode=lambda:pg.evaluate("document.getElementById('rail').className.replace('rail mode-','')")
        check(f'{w}px default is {exp}',mode()==exp,mode())
        if exp!='none':
            pg.click('[data-railtoggle]');pg.wait_for_timeout(300);m1=mode()
            check(f'{w}px toggles',m1!=exp,m1)
            pg.reload();pg.wait_for_timeout(600);check(f'{w}px remembers choice',mode()==m1,mode())
            if m1=='overlay':
                pg.keyboard.press('Escape');pg.wait_for_timeout(200);check(f'{w}px Esc closes overlay',mode()=='collapsed',mode())
        ctx.close()
    b.close()
finally: srv.terminate()
sys.exit(1 if BAD else 0)
