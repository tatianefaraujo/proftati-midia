import json, sys, numpy as np, wave
SR=48000
spec=json.load(open(sys.argv[1])); dur=float(sys.argv[2]); out=sys.argv[3]
rng=np.random.default_rng(1)
def env(n,a=0.005,r=0.3):
    t=np.arange(n)/SR; e=np.minimum(1,t/a)*np.exp(-t/r); return e
def ding(f1,f2):
    n=int(.55*SR); t=np.arange(n)/SR
    x=np.zeros(n); h=int(.09*SR)
    x+= np.sin(2*np.pi*f1*t)*env(n,.003,.12)
    x[h:]+= (np.sin(2*np.pi*f2*t)*env(n,.003,.18))[:n-h]
    x+=0.25*np.sin(2*np.pi*2*f2*t)*env(n,.003,.06)
    return 0.32*x
def bonk():
    n=int(.4*SR); t=np.arange(n)/SR
    f=220*np.exp(-t*3)
    x=np.sign(np.sin(2*np.pi*np.cumsum(f)/SR))*0.5+np.sin(2*np.pi*np.cumsum(f)/SR)
    return 0.16*x*env(n,.003,.09)
def whoosh():
    n=int(.45*SR); t=np.arange(n)/SR
    w=rng.standard_normal(n)
    # sweep bandpass via simple one-pole lowpass with varying coefficient
    y=np.zeros(n); a=0
    c=np.linspace(0.02,0.35,n)
    for i in range(n): a+= c[i]*(w[i]-a); y[i]=a
    y=y-np.convolve(y,np.ones(30)/30,'same')
    e=np.sin(np.pi*np.clip(t/.45,0,1))**2
    return 0.9*y*e/ (np.abs(y).max()+1e-9)*0.35
buf=np.zeros(int((dur+1)*SR))
def add(x,t):
    i=int(t*SR); buf[i:i+len(x)]+=x[:len(buf)-i]
for it in spec['items']:
    add(ding(880,1318) if it['v']=='pode' else bonk(), it['g'])
    add(whoosh(), it['f']-0.05)
buf=np.clip(buf,-1,1)
with wave.open(out,'w') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((buf*32767).astype('<i2').tobytes())
