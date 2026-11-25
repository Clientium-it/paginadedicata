"""montage.py WORKDIR PORT: screenshot the header of every page in WORKDIR/out into WORKDIR/montage.png (local preview only)."""
import os,glob,sys,subprocess,time,shutil
from playwright.sync_api import sync_playwright
from PIL import Image
W,PORT=sys.argv[1],sys.argv[2];M=W+'/mirror';shutil.rmtree(M,ignore_errors=True);os.makedirs(M+'/isd')
os.symlink(os.path.expanduser('~/paginadedicata/isd/assets'),M+'/isd/assets');os.symlink(os.path.expanduser('~/paginadedicata/assets'),M+'/assets')
S=sorted(os.path.basename(d.rstrip('/')) for d in glob.glob(W+'/out/*/') if os.path.basename(d.rstrip('/'))!='assets')
for s in S: shutil.copytree(f'{W}/out/{s}',f'{M}/isd/{s}')
srv=subprocess.Popen(['python3','-m','http.server',PORT,'--directory',M],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
C='/Users/stevenkoja5/Library/Caches/ms-playwright/chromium-1248/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
try:
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=C);pg=b.new_page(viewport={'width':1200,'height':160});ims=[]
        for s in S:
            pg.goto(f'http://127.0.0.1:{PORT}/isd/{s}/');pg.wait_for_timeout(400);f=f'{W}/h_{s}.png';pg.screenshot(path=f);ims.append(Image.open(f).crop((0,0,700,90)))
        O=Image.new('RGB',(1400,90*((len(ims)+1)//2)),'white')
        for i,im in enumerate(ims): O.paste(im,((i%2)*700,(i//2)*90))
        O.save(W+'/montage.png');print(len(S),S)
finally: srv.kill()
