import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import subprocess,time,json,uuid,re
from urllib.parse import urlparse,parse_qs,unquote
PORT=8864
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
DB={};USERS={};LOG=[]
def fake(route):
  try:
    _fake(route)
  except Exception as ex:
    import traceback;traceback.print_exc();route.abort()
def _fake(route):
    req=route.request;u=urlparse(req.url);path=u.path.replace('/sb','',1);q=parse_qs(u.query);body=json.loads(req.post_data) if req.post_data else {}
    def send(code,obj): route.fulfill(status=code,content_type='application/json',body=json.dumps(obj),headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization, apikey, content-type, prefer','Access-Control-Allow-Methods':'*'})
    if req.method=='OPTIONS': return send(200,{})
    if path=='/auth/v1/otp': LOG.append('otp '+body['email']);USERS.setdefault(body['email'],str(uuid.uuid4()));return send(200,{})
    if path=='/auth/v1/verify':
        if body.get('token')!='123456': return send(400,{'msg':'Token has expired or is invalid'})
        uid=USERS[body['email']];return send(200,{'access_token':'acc-'+uid,'refresh_token':'ref-'+uid,'expires_in':3600,'user':{'id':uid}})
    if path=='/auth/v1/token': uid=body['refresh_token'][4:];return send(200,{'access_token':'acc-'+uid,'refresh_token':'ref-'+uid,'expires_in':3600})
    if path=='/rest/v1/vaults':
        auth=req.headers.get('authorization','');uid=auth[len('Bearer acc-'):] if auth.startswith('Bearer acc-') else None
        if not uid: return send(401,{'message':'JWT'})
        want=(q.get('user_id',[''])[0]).replace('eq.','')
        if req.method=='GET':
            row=DB.get(uid) if want==uid else None;return send(200,[row] if row else [])
        if req.method=='POST':
            if body['user_id']!=uid: return send(403,{'message':'rls'})
            DB[uid]=body;LOG.append('insert');return send(201,[body])
        if req.method=='PATCH':
            row=DB.get(uid);ua=unquote(q.get('updated_at',['eq.'])[0][3:])
            if not row or row['updated_at']!=ua: LOG.append('patch-conflict');return send(200,[])
            row.update(body);LOG.append('patch');return send(200,[row])
    return send(404,{})
def page_with_sync(route):
    r=route.fetch();body=r.text().replace("var SYNC_CFG={url:'',anon:''};","var SYNC_CFG={url:'http://localhost:%d/sb',anon:'anon-key'};"%PORT)
    route.fulfill(response=r,body=body)
def ctx(b,w,h):
    c=b.new_context(viewport={'width':w,'height':h},service_workers='block');pg=c.new_page();pg.route(re.compile(r'.*:%d/(\?.*|index\.html.*|#.*)?$'%PORT),page_with_sync);pg.route(re.compile(r'.*/sb/.*'),fake);pg.route('https://static.cloudflareinsights.com/**',lambda r:r.abort());return c,pg
def signin(pg,email,pw,new):
    pg.click('[data-sheet="settings"]:visible') if pg.locator('[data-sheet="settings"]:visible').count() else None
    if pg.locator('[data-set="sync"]').count(): pg.click('[data-set="sync"]')
    pg.wait_for_timeout(200);pg.fill('#syemail',email);pg.click('[data-syncsend]');pg.wait_for_timeout(400)
    pg.fill('#sycode','111111');pg.click('[data-syncverify]');pg.wait_for_timeout(400);bad=pg.inner_text('#syerr')
    pg.fill('#sycode','123456');pg.click('[data-syncverify]');pg.wait_for_timeout(500)
    title=pg.inner_text('.sheet h2');pg.fill('#sypass',pw)
    if new: pg.fill('#sypass2',pw)
    pg.click('[data-syncpass]');pg.wait_for_timeout(4000);return bad,title
st=lambda pg:pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")
errs=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    cA,A=ctx(b,1440,900);A.on('pageerror',lambda e:errs.append('A '+str(e)))
    A.goto(f'http://localhost:{PORT}/');A.wait_for_timeout(250)
    A.click('[data-wz="next"]');A.fill('[data-k="name"]','Sohail');A.click('[data-wz="next"]');A.fill('[data-k="salary"]','72000');A.fill('[data-k="rent"]','1600');A.click('[data-wz="next"]');A.click('[data-wz="next"]');A.click('[data-wz="next"]');A.click('.foot [data-wz="finish"].go');A.wait_for_timeout(500)
    A.locator('[data-tab="spend"]:visible').first.click();A.fill('#amt','12.5');A.fill('#note','Laptop coffee');A.click('[data-add]');A.wait_for_timeout(300)
    bad,title=signin(A,'sohail@example.com','correct horse battery',True);print('A wrong code msg:',bad,'| A pass step:',title)
    print('server row after A:',bool(DB),'| data looks encrypted:', 'Sohail' not in json.dumps(DB),'| log',LOG[-2:])
    # Phone B: fresh, signs in, enters passphrase
    cB,B=ctx(b,390,844);B.on('pageerror',lambda e:errs.append('B '+str(e)))
    B.goto(f'http://localhost:{PORT}/');B.wait_for_timeout(300);B.click('[data-sheet="movehelp"]');B.wait_for_timeout(200);B.click('.sheet [data-sheet="sync"]');B.wait_for_timeout(200)
    B.fill('#syemail','sohail@example.com');B.click('[data-syncsend]');B.wait_for_timeout(400);B.fill('#sycode','123456');B.click('[data-syncverify]');B.wait_for_timeout(500)
    print('B step:',B.inner_text('.sheet h2'));B.fill('#sypass','wrong passphrase');B.click('[data-syncpass]');B.wait_for_timeout(3000);print('B wrong pass:',B.inner_text('#syerr'))
    B.fill('#sypass','correct horse battery');B.click('[data-syncpass]');B.wait_for_timeout(4000)
    SB=st(B);print('B got profile:',SB.get('profile',{}).get('name'),'| items',[x['note'] for x in SB['items']])
    # both edit, then sync both ways
    B.locator('[data-tab="spend"]:visible').first.click();B.wait_for_timeout(200);B.fill('#amt','4.2');B.fill('#note','Phone bus');B.click('[data-add]');B.wait_for_timeout(3500)
    A.fill('#amt','30');A.fill('#note','Laptop groceries');A.click('[data-add]');A.wait_for_timeout(3500)
    A.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");A.wait_for_timeout(2500)
    B.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");B.wait_for_timeout(2500)
    na=sorted(x['note'] for x in st(A)['items']);nb=sorted(x['note'] for x in st(B)['items']);print('A items:',na);print('B items:',nb,'| same:',na==nb)
    # delete on B propagates
    iid=[x for x in st(B)['items'] if x['note']=='Laptop coffee'][0]['id']
    B.evaluate(f"()=>{{const S0=JSON.parse(localStorage.getItem('setu-v1'));S0.items=S0.items.filter(x=>x.id!=='{iid}');localStorage.setItem('setu-v1',JSON.stringify(S0));}}");B.reload();B.wait_for_timeout(500)
    B.locator('[data-tab="spend"]:visible').first.click();B.fill('#amt','1');B.fill('#note','trigger');B.click('[data-add]');B.wait_for_timeout(3500)
    A.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");A.wait_for_timeout(2500)
    print('deleted on B, gone on A:', 'Laptop coffee' not in [x['note'] for x in st(A)['items']])
    A.click('[data-sheet="settings"]:visible');A.click('[data-set="sync"]');A.wait_for_timeout(300);print('A status:',A.inner_text('#syncstat'))
    BAD=[]
    if not na==nb: BAD.append('items differ')
    if 'Laptop coffee' in [x['note'] for x in st(A)['items']]: BAD.append('delete not synced')
    if 'Sohail' in json.dumps(DB): BAD.append('server data not encrypted')
    if errs: BAD.append('page errors')
    print('SYNC CHECKS:', 'ALL PASSED' if not BAD else 'FAILED '+', '.join(BAD))
    b.close()
finally: srv.terminate()
sys.exit(1 if 'BAD' in dir() and BAD else 0)
