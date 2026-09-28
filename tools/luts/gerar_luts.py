import numpy as np
from PIL import Image, ImageDraw, ImageFont
OUT='/home/user/antonio-junior-hub-pessoal/tools/luts/'
N=33
def clip(a): return np.clip(a,0,1)
def luma(c): return c[...,0]*0.2126+c[...,1]*0.7152+c[...,2]*0.0722
def sat(c,s): l=luma(c)[...,None]; return l+(c-l)*s
def scurve(x,k): return x-k*np.sin(2*np.pi*x)/(2*np.pi)
def shoulder(x,p):  # soft highlight rolloff above p, slope 1 at p
    r=1-p; y=np.where(x>p,p+r*np.tanh((x-p)/r),x); return y
def toe(x,a): return x+a*x*(1-x)**4
def hue(c):
    r,g,b=c[...,0],c[...,1],c[...,2]; mx=np.max(c,-1); mn=np.min(c,-1); d=mx-mn+1e-9
    h=np.where(mx==r,((g-b)/d)%6,np.where(mx==g,(b-r)/d+2,(r-g)/d+4))*60
    return h,(mx-mn)
def hue_sat(c,center,width,s):
    h,ch=hue(c); dist=np.abs(((h-center+180)%360)-180)
    w=np.clip(1-dist/width,0,1)**2*np.clip(ch*6,0,1)
    l=luma(c)[...,None]; f=(1+(s-1)*w)[...,None]; return l+(c-l)*f
def skin_protect(c,orig_s,new):  # keep skin hue (~25deg) closer to orig
    h,ch=hue(orig_s); dist=np.abs(((h-25+180)%360)-180); w=(np.clip(1-dist/25,0,1)**2*np.clip(ch*5,0,1))[...,None]*0.5
    return new*(1-w)+c*w

def base(c):  # NJ Correção Base — neutra, Rec.709
    x=clip(c)
    y=scurve(x,0.12)
    y=shoulder(y,0.9)
    s=sat(y,1.06)
    return clip(skin_protect(y,x,s))

def fimi_normal(c):
    x=clip(c)
    y=x*np.array([1.025,1.0,0.965])
    y=toe(clip(y),0.25)
    y=shoulder(y,0.78)
    y=scurve(clip(y),0.06)
    y=sat(y,0.93)
    y=hue_sat(y,205,45,0.9)   # céu/mar menos berrante
    y=hue_sat(y,100,40,0.92)   # verde menos neon
    return clip(y)

def fimi_log(c):
    x=clip(c)
    y=clip((x-0.09)/(0.86-0.09))
    y=scurve(y,0.35)
    y=y**1.04
    y=shoulder(y,0.86)
    y=sat(y,1.45)
    y=y*np.array([1.01,1.0,0.985])
    return clip(base(clip(y))*0.5+clip(y)*0.5)

def write_cube(fn,title,f):
    g=np.linspace(0,1,N); b,gg,r=np.meshgrid(g,g,g,indexing='ij')
    rgb=np.stack([r,gg,b],-1).reshape(-1,3); o=f(rgb)
    with open(OUT+fn,'w') as fh:
        fh.write(f'TITLE "{title}"\n# NJFILMES - Salvador, BA - 33x33x33 - entrada e saida Rec.709\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        for v in o: fh.write('%.6f %.6f %.6f\n'%tuple(v))
    return o.reshape(N,N,N,3)  # [b][g][r]

def apply(lut,img):
    p=clip(img)*(N-1); i0=np.floor(p).astype(int); i1=np.minimum(i0+1,N-1); f=p-i0
    def L(ri,gi,bi): return lut[bi,gi,ri]
    r0,g0,b0=i0[...,0],i0[...,1],i0[...,2]; r1,g1,b1=i1[...,0],i1[...,1],i1[...,2]
    fr,fg,fb=f[...,0:1],f[...,1:2],f[...,2:3]
    c00=L(r0,g0,b0)*(1-fr)+L(r1,g0,b0)*fr; c10=L(r0,g1,b0)*(1-fr)+L(r1,g1,b0)*fr
    c01=L(r0,g0,b1)*(1-fr)+L(r1,g0,b1)*fr; c11=L(r0,g1,b1)*(1-fr)+L(r1,g1,b1)*fr
    return (c00*(1-fg)+c10*fg)*(1-fb)+(c01*(1-fg)+c11*fg)*fb

def fimi_suave(c):
    x=clip(c); return clip(x*0.5+fimi_normal(x)*0.5)
def fimi_dourado(c):
    y=fimi_normal(c)
    y=y*np.array([1.02,1.0,0.968])                 # quente
    l=luma(y)[...,None]
    y=y+ (np.array([0.0,0.006,0.018])*(1-l)**2)     # sombras levemente frias/teal
    y=y+ (np.array([0.015,0.008,-0.012])*l**2)      # altas douradas
    y=hue_sat(y,30,35,1.1)                          # laranja/pele/areia um pouco mais ricos
    y=scurve(clip(y),0.05)
    return clip(y)
import os
for f in os.listdir(OUT):
    if f.endswith('.cube'): os.remove(OUT+f)
L1=write_cube('NJ_FIMI_Mini3_Normal_Correcao.cube','NJ FIMI Mini 3 Normal Correcao',fimi_normal)
L2=write_cube('NJ_FIMI_Mini3_Normal_Suave.cube','NJ FIMI Mini 3 Normal Suave',fimi_suave)
L3=write_cube('NJ_FIMI_Mini3_Normal_Dourado_Salvador.cube','NJ FIMI Mini 3 Normal Dourado Salvador',fimi_dourado)
# synthetic drone scene (ideal)
W,H=480,300; yy,xx=np.mgrid[0:H,0:W]/np.array([H,W])[:,None,None]
img=np.zeros((H,W,3))
sky=(yy<0.32)[...,None]; sea=((yy>=0.32)&(yy<0.6+0.05*np.sin(xx*9)))[...,None]; sand=~(sky|sea)
skyc=np.stack([0.55+0.25*yy,0.72+0.2*yy,0.92-0.05*yy],-1)
seac=np.stack([0.12+0.1*xx,0.45+0.1*xx,0.52+0.05*np.sin(xx*30)*0.3],-1)*(0.85+0.15*np.sin(yy*60))[...,None]
sandc=np.stack([0.84,0.74,0.58],-1)*(0.9+0.1*np.sin(xx*40+yy*20))[...,None]
img=np.where(sky,skyc,np.where(sea,seac,sandc))
img[int(H*.62):int(H*.8),int(W*.05):int(W*.25)]=[0.22,0.45,0.18]   # vegetação
img[int(H*.66):int(H*.78),int(W*.34):int(W*.42)]=[0.80,0.58,0.46]  # pele clara
img[int(H*.66):int(H*.78),int(W*.44):int(W*.52)]=[0.52,0.34,0.24]  # pele escura
img[int(H*.66):int(H*.78),int(W*.56):int(W*.66)]=[0.85,0.35,0.15]  # guarda-sol laranja
img[int(H*.88):,:]=np.linspace(0,1,W)[None,:,None]                   # rampa de cinza
img[int(H*.06):int(H*.14),int(W*.78):int(W*.9)]=[1.0,0.98,0.93]      # sol/nuvem estourando
ideal=clip(img)
# simulate FIMI Normal (frio, contrastado, saturado)
normal=clip(sat(scurve(ideal*np.array([0.97,1.0,1.05]),0.2),1.2))
# simulate Log (lavado)
log=clip(0.09+(0.86-0.09)*scurve(sat(ideal,0.62),-0.3))
def tag(a,t):
    im=Image.fromarray((clip(a)*255).astype('uint8')); d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,22],fill=(0,0,0)); d.text((6,5),t,fill=(246,196,69)); return im
rows=[[tag(normal,'FIMI Mini 3 Normal (simulado)'),tag(apply(L1,normal),'+ NJ Correcao')],
      [tag(normal,'FIMI Mini 3 Normal (simulado)'),tag(apply(L2,normal),'+ NJ Correcao Suave')],
      [tag(normal,'FIMI Mini 3 Normal (simulado)'),tag(apply(L3,normal),'+ NJ Correcao + Dourado Salvador')]]
sheet=Image.new('RGB',(W*2+12,H*3+24),(12,12,14))
for i,r in enumerate(rows):
    for j,im in enumerate(r): sheet.paste(im,(j*(W+12),i*(H+12)))
sheet.save('/home/user/antonio-junior-hub-pessoal/tools/luts/NJ_LUTs_antes_depois.jpg',quality=90)
# sanity
for n,L in [('correcao',L1),('suave',L2),('dourado',L3)]:
    print(n,'black',L[0,0,0].round(3),'white',L[-1,-1,-1].round(3),'mid',L[16,16,16].round(3))
