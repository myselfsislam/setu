import os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from playwright.sync_api import sync_playwright
import subprocess,time,json,uuid,re
from urllib.parse import urlparse,parse_qs,unquote
PORT=8864
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
# A tiny stand-in for Supabase: email + password accounts, and one encrypted vault row per user
DB={};USERS={};LOG=[];CONFIRM_REQUIRED=set()
def fake(route):
  try:
    _fake(route)
  except Exception as ex:
    import traceback;traceback.print_exc();route.abort()
def session(uid,email):return {'access_token':'acc-'+uid,'refresh_token':'ref-'+uid,'expires_in':3600,'user':{'id':uid,'email':email}}
def uid_from(req):
    a=req.headers.get('authorization','');return a[len('Bearer acc-'):] if a.startswith('Bearer acc-') else None
def _fake(route):
    req=route.request;u=urlparse(req.url);path=u.path.replace('/sb','',1);q=parse_qs(u.query);body=json.loads(req.post_data) if req.post_data else {}
    def send(code,obj): route.fulfill(status=code,content_type='application/json',body=json.dumps(obj),headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'authorization, apikey, content-type, prefer','Access-Control-Allow-Methods':'*'})
    if req.method=='OPTIONS': return send(200,{})
    if path=='/auth/v1/signup':
        em=body['email']
        if em in USERS: return send(422,{'msg':'User already registered'})
        uid=str(uuid.uuid4());USERS[em]={'uid':uid,'pw':body['password']};LOG.append('signup '+em)
        return send(200,{'id':uid,'email':em}) if em in CONFIRM_REQUIRED else send(200,session(uid,em))
    if path=='/auth/v1/token':
        if q.get('grant_type',[''])[0]=='password':
            usr=USERS.get(body['email'])
            if not usr or usr['pw']!=body['password']: return send(400,{'error':'invalid_grant','error_description':'Invalid login credentials'})
            return send(200,session(usr['uid'],body['email']))
        uid=body['refresh_token'][4:];return send(200,{'access_token':'acc-'+uid,'refresh_token':'ref-'+uid,'expires_in':3600})
    if path=='/auth/v1/user':
        uid=uid_from(req);em=[e for e,x in USERS.items() if x['uid']==uid]
        if not em: return send(401,{'msg':'invalid JWT'})
        if req.method=='PUT': USERS[em[0]]['pw']=body['password'];LOG.append('password changed')
        return send(200,{'id':uid,'email':em[0]})
    if path=='/auth/v1/recover': LOG.append('recover '+body['email']);return send(200,{})
    if path=='/rest/v1/vaults':
        uid=uid_from(req)
        if not uid: return send(401,{'message':'JWT'})
        want=(q.get('user_id',[''])[0]).replace('eq.','')
        if req.method=='GET':
            row=DB.get(uid) if want==uid else None;return send(200,[row] if row else [])
        if req.method=='POST':
            if body['user_id']!=uid: return send(403,{'message':'rls'})
            DB[uid]=body;LOG.append('insert');return send(201,[body])
        if req.method=='PATCH':
            row=DB.get(uid)
            if not row: return send(200,[])
            if 'updated_at' in q:
                ua=unquote(q['updated_at'][0][3:])
                if row['updated_at']!=ua: LOG.append('patch-conflict');return send(200,[])
            row.update(body);LOG.append('patch');return send(200,[row])
    return send(404,{})
def page_with_sync(route):
    r=route.fetch();body=re.sub(r"var SYNC_CFG=\{url:'[^']*',anon:'[^']*'\};","var SYNC_CFG={url:'http://localhost:%d/sb',anon:'anon-key'};"%PORT,r.text())
    route.fulfill(response=r,body=body)
def ctx(b,w,h):
    c=b.new_context(viewport={'width':w,'height':h},service_workers='block');pg=c.new_page();pg.route(re.compile(r'.*:%d/(\?.*|index\.html.*|#.*)?$'%PORT),page_with_sync);pg.route(re.compile(r'.*/sb/.*'),fake);pg.route('https://static.cloudflareinsights.com/**',lambda r:r.abort());return c,pg
def open_account(pg):
    if pg.locator('.sheet #syemail').count(): return
    if pg.locator('[data-sheet="sync"]:visible').count(): pg.locator('[data-sheet="sync"]:visible').first.click()
    else:
        pg.click('[data-sheet="settings"]:visible');pg.click('[data-set="sync"]')
    pg.wait_for_timeout(200)
def form(pg,email,pw,create=False,again=None):
    open_account(pg)
    if create: pg.click('[data-syncmode="up"]');pg.wait_for_timeout(150)
    pg.fill('#syemail',email);pg.fill('#sypw',pw)
    if create: pg.fill('#sypw2',again if again is not None else pw)
    pg.click('[data-syncgo]');pg.wait_for_timeout(3500)
st=lambda pg:pg.evaluate("JSON.parse(localStorage.getItem('setu-v1'))")
errs=[];BAD=[]
def check(name,ok,info=''):
    print(('PASS ' if ok else 'FAIL ')+name,info if not ok else '')
    if not ok: BAD.append(name)
try:
  with sync_playwright() as p:
    b=p.chromium.launch()
    # Laptop A: sets up Setu, logs spending, creates an account
    cA,A=ctx(b,1440,900);A.on('pageerror',lambda e:errs.append('A '+str(e)))
    A.goto(f'http://localhost:{PORT}/');A.wait_for_timeout(250)
    A.click('[data-wz="next"]');A.click('[data-wz="full"]');A.fill('[data-k="name"]','Sohail');A.click('[data-wz="next"]');A.fill('[data-k="salary"]','72000');A.fill('[data-k="rent"]','1600');A.click('[data-wz="next"]');A.click('[data-wz="next"]');A.click('[data-wz="next"]');A.click('.foot [data-wz="finish"].go');A.wait_for_timeout(500)
    A.locator('[data-tab="home"]:visible').first.click();A.locator('[data-sheet="addspend"]:visible').first.click();A.wait_for_timeout(150);A.fill('#amt','12.5');A.fill('#note','Laptop coffee');A.click('[data-add]');A.wait_for_timeout(300)
    open_account(A);A.click('[data-syncmode="up"]');A.fill('#syemail','sohail@example.com');A.fill('#sypw','correct horse');A.fill('#sypw2','different one');A.click('[data-syncgo]');A.wait_for_timeout(300)
    check('Create account checks both passwords match','match' in A.inner_text('#syerr'))
    A.fill('#sypw2','correct horse');A.click('[data-syncgo]');A.wait_for_timeout(3500)
    check('Account created and data saved online',bool(DB) and A.locator('.sheet').count()==0,LOG)
    check('Saved data is encrypted','Sohail' not in json.dumps(DB) and 'Laptop coffee' not in json.dumps(DB))
    check('No email links or codes are used',not any(x.startswith('otp') for x in LOG))
    # Phone B: fresh, signs in with email and password
    cB,B=ctx(b,390,844);B.on('pageerror',lambda e:errs.append('B '+str(e)))
    B.goto(f'http://localhost:{PORT}/');B.wait_for_timeout(300);B.click('[data-sheet="sync"]');B.wait_for_timeout(200)
    check('New device shows a sign-in form',B.locator('#syemail').count()==1 and B.locator('#sypw').count()==1)
    form(B,'sohail@example.com','wrong password')
    check('Wrong password is refused clearly','don’t match' in B.inner_text('#syerr'),B.inner_text('#syerr'))
    B.fill('#sypw','correct horse');B.click('[data-syncgo]');B.wait_for_timeout(4000)
    SB=st(B);check('Phone gets the laptop data after signing in',SB.get('profile',{}).get('name')=='Sohail' and 'Laptop coffee' in [x['note'] for x in SB['items']])
    # both edit, then sync both ways
    B.locator('[data-tab="home"]:visible').first.click();B.wait_for_timeout(200);B.locator('[data-sheet="addspend"]:visible').first.click();B.wait_for_timeout(150);B.fill('#amt','4.2');B.fill('#note','Phone bus');B.click('[data-add]');B.wait_for_timeout(3500)
    A.locator('[data-sheet="addspend"]:visible').first.click();A.wait_for_timeout(150);A.fill('#amt','30');A.fill('#note','Laptop groceries');A.click('[data-add]');A.wait_for_timeout(3500)
    A.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");A.wait_for_timeout(2500)
    B.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");B.wait_for_timeout(2500)
    na=sorted(x['note'] for x in st(A)['items']);nb=sorted(x['note'] for x in st(B)['items'])
    check('Changes on either device show on both',na==nb and 'Phone bus' in na and 'Laptop groceries' in nb,(na,nb))
    iid=[x for x in st(B)['items'] if x['note']=='Laptop coffee'][0]['id']
    B.evaluate(f"()=>{{const S0=JSON.parse(localStorage.getItem('setu-v1'));S0.items=S0.items.filter(x=>x.id!=='{iid}');localStorage.setItem('setu-v1',JSON.stringify(S0));}}");B.reload();B.wait_for_timeout(500)
    B.locator('[data-tab="home"]:visible').first.click();B.locator('[data-sheet="addspend"]:visible').first.click();B.wait_for_timeout(150);B.fill('#amt','1');B.fill('#note','trigger');B.click('[data-add]');B.wait_for_timeout(3500)
    A.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");A.wait_for_timeout(2500)
    check('A delete on one device is removed on the other','Laptop coffee' not in [x['note'] for x in st(A)['items']])
    A.click('[data-sheet="settings"]:visible');A.click('[data-set="sync"]');A.wait_for_timeout(300)
    check('Account screen shows who is signed in','sohail@example.com' in A.inner_text('.sheet') and 'Synced' in A.inner_text('#syncstat'),A.inner_text('.sheet'))
    A.click('[data-syncsetpw]');A.wait_for_timeout(200);A.fill('#sypw','laptop pass 1');A.fill('#sypw2','laptop pass 1');A.click('[data-syncreset]');A.wait_for_timeout(3500)
    check('A signed-in device can set a password without any email',USERS['sohail@example.com']['pw']=='laptop pass 1' and not any(x.startswith('recover') for x in LOG))
    cP,P=ctx(b,390,844);P.on('pageerror',lambda e:errs.append('P '+str(e)));P.goto(f'http://localhost:{PORT}/');P.wait_for_timeout(300);P.click('[data-sheet="sync"]');P.wait_for_timeout(200)
    form(P,'sohail@example.com','laptop pass 1')
    check('That password then opens the data on a new device',(st(P).get('profile') or {}).get('name')=='Sohail' and P.locator('#syold').count()==0)
    # A device that already has newer data signs in: nothing is lost, both copies are combined
    cQ,Q=ctx(b,1280,800);Q.on('pageerror',lambda e:errs.append('Q '+str(e)));Q.goto(f'http://localhost:{PORT}/');Q.wait_for_timeout(250)
    Q.click('[data-wz="next"]');Q.fill('[data-k="salary"]','60000');Q.click('[data-wz="finish"]');Q.wait_for_timeout(500)
    Q.locator('[data-sheet="addspend"]:visible').first.click();Q.wait_for_timeout(150);Q.fill('#amt','9');Q.fill('#note','Only on this laptop');Q.click('[data-add]');Q.wait_for_timeout(300)
    Q.locator('[data-sheet="sync"]:visible').first.click() if Q.locator('[data-sheet="sync"]:visible').count() else (Q.click('[data-sheet="settings"]:visible'),Q.click('[data-set="sync"]'))
    Q.wait_for_timeout(200);form(Q,'sohail@example.com','laptop pass 1');Q.wait_for_timeout(1500)
    nq=[x['note'] for x in st(Q)['items']];P.evaluate("()=>document.dispatchEvent(new Event('visibilitychange'))");P.wait_for_timeout(2500);np=[x['note'] for x in st(P)['items']]
    check('Signing in on a device with its own data keeps everything',('Only on this laptop' in nq) and ('Phone bus' in nq) and ('Only on this laptop' in np),(nq,np))
    # Existing account whose copy was locked with an older passphrase: asked once, then switched to the password
    cM,M=ctx(b,390,844);M.on('pageerror',lambda e:errs.append('M '+str(e)));M.goto(f'http://localhost:{PORT}/');M.wait_for_timeout(300);M.click('[data-sheet="sync"]');M.wait_for_timeout(200)
    form(M,'old@example.com','oldpassphrase',create=True)
    USERS['old@example.com']['pw']='new password1'   # the account now signs in with a different secret than the one that locked the data
    salt0=DB[USERS['old@example.com']['uid']]['salt']
    cN,N=ctx(b,390,844);N.on('pageerror',lambda e:errs.append('N '+str(e)));N.goto(f'http://localhost:{PORT}/');N.wait_for_timeout(300);N.click('[data-sheet="sync"]');N.wait_for_timeout(200)
    form(N,'old@example.com','new password1')
    check('Old passphrase is asked for once',N.locator('#syold').count()==1)
    N.fill('#syold','oldpassphrase');N.click('[data-syncmigrate]');N.wait_for_timeout(4000)
    check('Saved copy is switched to the password',N.locator('.sheet').count()==0 and DB[USERS['old@example.com']['uid']]['salt']!=salt0)
    cO,O=ctx(b,390,844);O.on('pageerror',lambda e:errs.append('O '+str(e)));O.goto(f'http://localhost:{PORT}/');O.wait_for_timeout(300);O.click('[data-sheet="sync"]');O.wait_for_timeout(200)
    form(O,'old@example.com','new password1')
    check('Next device needs only email and password',O.locator('#syold').count()==0 and O.locator('.sheet').count()==0)
    # Forgot password: reset email, then a new password on a device that has the data
    open_account(B) if False else None
    uidS=USERS['sohail@example.com']['uid'];B.goto(f'http://localhost:{PORT}/#access_token=acc-{uidS}&expires_in=3600&refresh_token=ref-{uidS}&token_type=bearer&type=recovery');B.wait_for_timeout(1200)
    check('Reset link asks for a new password',B.locator('[data-syncreset]').count()==1 and 'access_token' not in B.url)
    B.fill('#sypw','brand new pass');B.fill('#sypw2','brand new pass');B.click('[data-syncreset]');B.wait_for_timeout(4000)
    cR,R=ctx(b,390,844);R.on('pageerror',lambda e:errs.append('R '+str(e)));R.goto(f'http://localhost:{PORT}/');R.wait_for_timeout(300);R.click('[data-sheet="sync"]');R.wait_for_timeout(200)
    form(R,'sohail@example.com','brand new pass')
    check('After a reset, the new password opens the data everywhere',(st(R).get('profile') or {}).get('name')=='Sohail' and R.locator('.sheet').count()==0)
    # Email confirmation switched on in Supabase: account waits for the email, then signs in
    CONFIRM_REQUIRED.add('confirm@example.com')
    cC,Cp=ctx(b,390,844);Cp.on('pageerror',lambda e:errs.append('C '+str(e)));Cp.goto(f'http://localhost:{PORT}/');Cp.wait_for_timeout(300);Cp.click('[data-sheet="sync"]');Cp.wait_for_timeout(200)
    form(Cp,'confirm@example.com','some password',create=True)
    check('If Supabase asks for email confirmation, Setu explains it','confirmation email' in Cp.inner_text('.sheet'))
    check('No page errors',not errs,errs[:3])
    b.close()
finally: srv.terminate()
print('SYNC CHECKS:', 'ALL PASSED' if not BAD else 'FAILED '+', '.join(BAD))
sys.exit(1 if BAD else 0)
