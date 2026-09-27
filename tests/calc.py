import os,sys,subprocess,time,json,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root
from playwright.sync_api import sync_playwright
import subprocess,time
PORT=8782
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
# expected annual tax + NI (no pension), 2026/27
def ruk(g):
    pa=12570 if g<=100000 else max(0,12570-(g-100000)/2);ti=max(0,g-pa)
    tax=0.2*min(ti,37700)+0.4*max(0,min(ti,125140)-37700)+0.45*max(0,ti-125140)
    ni=0.08*max(0,min(g,50270)-12570)+0.02*max(0,g-50270);return round((g-tax-ni)/12)
cases=[(30000,False,ruk(30000)),(50000,False,ruk(50000)),(72000,False,ruk(72000)),(110000,False,ruk(110000)),(130000,False,ruk(130000)),
       (50000,True,round((50000-8982.05-0.08*(50000-12570)-0)/12))]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();pg.goto(f'http://localhost:{PORT}/');pg.wait_for_timeout(300)
    pg.click('[data-wz="next"]');pg.click('[data-wz="next"]')
    for g,sco,exp in cases:
        pg.click(f'[data-seg="scot"][data-v="{"true" if sco else "false"}"]');pg.wait_for_timeout(80)
        pg.fill('[data-k="pension"]','0');pg.fill('[data-k="salary"]',str(g));pg.wait_for_timeout(80)
        got=int(''.join(ch for ch in pg.inner_text('#th').split('a month')[0] if ch.isdigit()))
        BAD=globals().get('BAD',0)+(0 if abs(got-exp)<=1 else 1);globals()['BAD']=BAD;print(('PASS' if abs(got-exp)<=1 else 'FAIL'),f"£{g:,} {'Scotland' if sco else 'rUK'}: app £{got:,}/month, expected £{exp:,}")
    b.close()
finally: srv.terminate()
sys.exit(1 if globals().get('BAD',0) else 0)
