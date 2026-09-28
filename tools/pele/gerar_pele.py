import numpy as np
from PIL import Image, ImageDraw
OUT='/home/user/antonio-junior-hub-pessoal/tools/pele/'
N=33
def sm(e0,e1,x): t=np.clip((x-e0)/(e1-e0),0,1); return t*t*(3-2*t)
def skin(rgb,pull=0.5,uni=0.3,sat=0.95,bright=0.02,warm=0.0,rng=25.0,mask=False):
    R,G,B=rgb[...,0],rgb[...,1],rgb[...,2]
    Y=0.2126*R+0.7152*G+0.0722*B; Cb=(B-Y)/1.8556; Cr=(R-Y)/1.5748
    C=np.sqrt(Cb*Cb+Cr*Cr); ang=np.degrees(np.arctan2(Cr,Cb))
    d=(ang-123+180)%360-180
    w=(1-sm(rng*0.4,rng,np.abs(d)))*sm(0.02,0.05,C)*(1-sm(0.24,0.34,C))*sm(0.04,0.12,Y)*(1-sm(0.9,0.98,Y))
    if mask: return np.stack([w,w,w],-1)
    na=np.radians(ang-d*pull*w); nc=C+(0.14-C)*uni*w; nc=nc*(1+(sat-1)*w)
    nCb=nc*np.cos(na)-warm*0.5*w; nCr=nc*np.sin(na)+warm*w; nY=Y+bright*w
    R2=nY+1.5748*nCr; B2=nY+1.8556*nCb; G2=(nY-0.2126*R2-0.0722*B2)/0.7152
    return np.clip(np.stack([R2,G2,B2],-1),0,1)
PRE={'NJ_Pele_Natural':dict(pull=0.5,uni=0.3,sat=0.95,bright=0.02),
     'NJ_Pele_Uniforme':dict(pull=0.75,uni=0.6,sat=0.92,bright=0.02),
     'NJ_Pele_Dourada':dict(pull=0.4,uni=0.25,sat=1.06,bright=0.03,warm=0.012)}
def write(fn,f):
    g=np.linspace(0,1,N); b,gg,r=np.meshgrid(g,g,g,indexing='ij')
    o=f(np.stack([r,gg,b],-1).reshape(-1,3))
    with open(OUT+fn+'.cube','w') as fh:
        fh.write(f'TITLE "{fn}"\n# NJFILMES - ajuste so nos tons de pele - entrada e saida Rec.709\nLUT_3D_SIZE {N}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n')
        for v in o: fh.write('%.6f %.6f %.6f\n'%tuple(v))
for k,v in PRE.items(): write(k,lambda x,v=v:skin(x,**v))
# preview: patches
pat=[('pele clara',(0.80,0.58,0.46)),('clara rosada',(0.86,0.55,0.50)),('media',(0.68,0.45,0.33)),('escura',(0.52,0.34,0.24)),('muito escura',(0.33,0.21,0.15)),
     ('avermelhada',(0.85,0.45,0.42)),('manchada',(0.78,0.47,0.40)),('amarelada',(0.75,0.62,0.40)),('laranja',(0.85,0.35,0.15)),('areia',(0.84,0.74,0.58)),('ceu',(0.55,0.72,0.92)),('verde',(0.22,0.45,0.18))]
S=70
cols=['Original']+list(PRE)+['Mascara (Natural)']
img=Image.new('RGB',(150+len(cols)*(S+8),40+len(pat)*(S//2+6)),(12,12,14)); d=ImageDraw.Draw(img)
for j,c in enumerate(cols): d.text((150+j*(S+8),12),c.replace('NJ_Pele_',''),fill=(246,196,69))
for i,(n,c) in enumerate(pat):
    y=40+i*(S//2+6); d.text((10,y+10),n,fill=(220,220,215)); a=np.array([c],dtype=float)
    outs=[a]+[skin(a,**v) for v in PRE.values()]+[skin(a,mask=True)]
    for j,o in enumerate(outs):
        x=150+j*(S+8); d.rectangle([x,y,x+S,y+S//2],fill=tuple(int(v*255) for v in o[0]))
img.save(OUT+'NJ_Pele_antes_depois.png')
