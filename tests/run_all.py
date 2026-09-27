"""Runs every Setu check. Usage (from the repository root):
   pip install playwright && python -m playwright install --with-deps chromium && npm i axe-core@4
   python tests/run_all.py"""
import subprocess,sys,os
HERE=os.path.dirname(os.path.abspath(__file__))
failed=[]
for name in ['e2e.py','calc.py','a11y.py','layout.py']:
    print('\n===== '+name+' =====',flush=True)
    r=subprocess.run([sys.executable,os.path.join(HERE,name)])
    if r.returncode: failed.append(name)
print('\nALL CHECKS PASSED' if not failed else '\nFAILED: '+', '.join(failed))
sys.exit(1 if failed else 0)
