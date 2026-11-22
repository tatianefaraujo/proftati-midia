"""Carrosséis @proftatiaraujo nos 2 formatos aprovados (22/11/2026): GUIA e VOZ.
Uso: python3 carrossel.py spec.json pasta_saida
spec = {"formato":"guia"|"voz", "serie":"PDI SEM MISTÉRIO #01", "foto":"/caminho.jpg", "slides":[...]}
Tipos de slide:
  guia: {"t":"capa","tag":"PDI · INCLUSÃO","titulo":"Meta de PDI que dá para <hl>medir</hl>","sub":"..."}
        {"t":"compara","tag":"LEITURA","titulo":"...","nao":"...","sim":"...","porque":"..."}
        {"t":"lista","tag":"PASSO A PASSO","titulo":"...","itens":[["Título curto","explicação"],...]}
        {"t":"texto","tag":"...","titulo":"...","corpo":"<p>...</p>"}
        {"t":"cta","tag":"CHECKLIST","titulo":"...","check":["...",...],"palavra":"FICHA","brinde":"a ficha da turma"}
  voz:  {"t":"capa","titulo":"Aluno quieto não é aluno que <hl>aprendeu.</hl>","sub":"..."}
        {"t":"frase","frase":"Silêncio pode ser <y>o aluno que não sabe perguntar.</y>","expl":"..."}
        {"t":"cta","frase":"...","palavra":"CONTEXTO","brinde":"5 contextos prontos"}
Marcações: <hl>grifo amarelo</hl>  <y>texto amarelo</y>  <b>negrito</b>.
"""
import base64, json, sys, os, re
from playwright.sync_api import sync_playwright
FD='/tmp/fonts/'
def b64(p): return base64.b64encode(open(p,'rb').read()).decode()
Y='#F9E076'; K='#17130F'; CR='#FBF7EE'
def css():
    F={k:b64(FD+v) for k,v in {'s':'InstrumentSerif.ttf','f9':'Fraunces-900.ttf','i5':'Inter-500.ttf','i8':'Inter-800.ttf'}.items()}
    return f"""@font-face{{font-family:S;src:url(data:font/ttf;base64,{F['s']})}}@font-face{{font-family:R;src:url(data:font/ttf;base64,{F['f9']})}}
@font-face{{font-family:I;font-weight:500;src:url(data:font/ttf;base64,{F['i5']})}}@font-face{{font-family:I;font-weight:800;src:url(data:font/ttf;base64,{F['i8']})}}
*{{margin:0;padding:0;box-sizing:border-box}} body{{width:1080px;height:1350px;font-family:I;color:{K};position:relative;overflow:hidden}}
.grid{{position:absolute;inset:0;background:{CR};background-image:linear-gradient(#e9e1cf 1.5px,transparent 1.5px),linear-gradient(90deg,#e9e1cf 1.5px,transparent 1.5px);background-size:54px 54px}}
.tag{{display:inline-block;background:{K};color:{Y};font-weight:800;font-size:26px;letter-spacing:.16em;padding:12px 22px}}
.serie{{position:absolute;top:60px;right:70px;background:{Y};color:{K};font-weight:800;font-size:22px;letter-spacing:.08em;padding:10px 18px;border-radius:12px}}
h1{{font-family:R;font-weight:900;line-height:1.02;letter-spacing:-.02em}}
hl{{background:{Y};box-shadow:0 0 0 0;padding:0 8px;border-radius:6px;-webkit-box-decoration-break:clone;box-decoration-break:clone;background:linear-gradient(180deg,transparent 52%,{Y} 52%,{Y} 94%,transparent 94%)}}
.dark hl{{background:{Y};color:{K};padding:0 12px;border-radius:10px}} y{{color:{Y}}}
.card{{background:#fff;border-radius:22px;box-shadow:0 6px 24px rgba(0,0,0,.07);padding:30px 34px}}
.pill{{display:inline-block;font-weight:800;font-size:26px;padding:8px 18px;border-radius:10px}}
.no{{background:#EDE6D6;color:#7A6F5C}} .ok{{background:{Y}}}
.foot{{position:absolute;left:80px;right:80px;bottom:46px;display:flex;justify-content:space-between;font-size:24px;font-weight:800}}
.foot .p{{background:{Y};color:{K};padding:6px 18px;border-radius:99px}}
.st{{position:absolute;color:#D9A441;font-family:R}} .body p{{margin-top:22px}}"""
def st(l): return ''.join(f'<span class="st" style="top:{t}px;left:{x}px;font-size:{z}px">✦</span>' for t,x,z in l)
def tsize(txt,big,small,lim):  # encolhe título longo
    n=len(re.sub('<[^>]+>','',txt)); return big if n<=lim else max(small,int(big*lim/n))
def foot(dark,last):
    c=' style="color:#fff"' if dark else ''
    mid='siga para mais' if last else 'salva pra depois'; r='' if last else 'arrasta →'
    return f'<div class="foot"{c}><span>@proftatiaraujo</span><span class="p">{mid}</span><span>{r}</span></div>'
def guia(s,serie,n,N,foto):
    top=f'<div class="grid"></div><span class="serie">{serie}{"" if n==1 else f" · {n}/{N}"}</span>'
    if s['t']=='capa':
        fz=tsize(s['titulo'],118,84,34)
        ph=f'<img src="data:image/jpeg;base64,{b64(foto)}" style="position:absolute;right:70px;bottom:120px;width:300px;height:300px;object-fit:cover;object-position:50% 25%;border-radius:50%;border:8px solid {Y}">' if foto else ''
        return top+f'''<div style="position:absolute;left:80px;right:80px;top:150px"><span class="tag">{s['tag']}</span>
<h1 style="margin-top:40px;font-size:{fz}px">{s['titulo']}</h1><p style="font-size:42px;line-height:1.4;margin-top:44px;color:#4A4234;max-width:{'600' if foto else '900'}px">{s.get('sub','')}</p></div>{ph}{st([(1020,90,60),(1110,170,28)])}'''
    fz=tsize(s['titulo'],84,62,30)
    head=f'<div style="position:absolute;left:80px;right:80px;top:140px"><span class="tag">{s["tag"]}</span><h1 style="margin-top:30px;font-size:{fz}px">{s["titulo"]}</h1>'
    if s['t']=='compara':
        return top+head+f'''<div style="display:flex;gap:28px;margin-top:46px"><div class="card" style="flex:1"><span class="pill no">✕ ASSIM NÃO</span><p style="font-family:S;font-size:50px;line-height:1.1;margin-top:24px;color:#9A8F7A">{s['nao']}</p></div>
<div class="card" style="flex:1.3"><span class="pill ok">✓ ASSIM SIM</span><p style="font-family:S;font-size:48px;line-height:1.1;margin-top:24px">{s['sim']}</p></div></div>
<div class="card" style="margin-top:28px;font-size:34px;line-height:1.5"><b>Por quê:</b> {s['porque']}</div></div>'''
    if s['t']=='lista':
        its=''.join(f'<div class="card" style="margin-top:20px;display:flex;gap:26px;align-items:flex-start"><span style="font-family:R;font-size:54px;line-height:1;color:#D9A441;min-width:46px">{i+1}</span><div><b style="font-size:38px">{a}</b><p style="font-size:32px;line-height:1.4;margin-top:6px;color:#4A4234">{b}</p></div></div>' for i,(a,b) in enumerate(s['itens']))
        return top+head+f'<div style="margin-top:30px">{its}</div></div>'
    if s['t']=='texto':
        return top+head+f'<div class="card body" style="margin-top:40px;font-size:38px;line-height:1.5">{s["corpo"]}</div></div>'
    if s['t']=='cta':
        ch=''.join(f'<div>☑ {c}</div>' for c in s['check'])
        return top+head+f'''<div class="card" style="margin-top:40px;font-size:38px;line-height:1.9">{ch}</div>
<div style="margin-top:30px;background:{K};color:#fff;border-radius:22px;padding:32px 40px;font-size:38px;line-height:1.4;font-weight:800">💬 Comente <span style="color:{Y}">{s['palavra']}</span> e receba {s['brinde']} no Direct.</div></div>'''
def voz(s,serie,n,N,foto):
    sr=f'<span class="serie">{serie}{"" if n==1 else f" · {n}/{N}"}</span>'
    if s['t']=='capa':
        fz=tsize(s['titulo'],118,86,40)
        return f'''<div class="dark"><div style="position:absolute;inset:0;background:{K}"></div><img src="data:image/jpeg;base64,{b64(foto)}" style="position:absolute;left:0;top:0;width:1080px;height:990px;object-fit:cover;object-position:50% {s.get('y','30')}%">
<div style="position:absolute;left:0;right:0;top:560px;height:440px;background:linear-gradient(180deg,rgba(23,19,15,0),{K})"></div>{sr}
<div style="position:absolute;left:80px;right:80px;bottom:140px;color:#fff"><h1 style="font-family:S;font-weight:400;font-size:{fz}px;line-height:1.04">{s['titulo']}</h1>
<p style="font-size:40px;line-height:1.35;margin-top:30px;color:#EDE4CF">{s.get('sub','')}</p></div>{st([(1010,960,46),(1070,1010,22)])}</div>'''
    body=f'<p style="font-family:S;font-size:{tsize(s["frase"],92,70,70)}px;line-height:1.06;margin-top:30px">{s["frase"]}</p>'
    if s['t']=='frase':
        body+=f'<p style="font-size:40px;line-height:1.5;margin-top:56px;color:#D9D0BC;border-left:10px solid {Y};padding-left:28px">{s["expl"]}</p>'
    else:
        body+=f'<div style="margin-top:60px;background:{Y};color:{K};border-radius:22px;padding:32px 40px;font-size:38px;line-height:1.4;font-weight:800">💬 Comente {s["palavra"]} e receba {s["brinde"]} no Direct.</div>'
        if s.get('expl'): body+=f'<p style="font-size:36px;line-height:1.5;margin-top:36px;color:#D9D0BC">{s["expl"]}</p>'
    return f'<div class="dark"><div style="position:absolute;inset:0;background:{K}"></div>{sr}<div style="position:absolute;left:80px;right:80px;top:190px;color:#fff"><p style="font-family:R;color:{Y};font-size:110px;line-height:1">✦</p>{body}</div></div>'
def render(spec,out):
    os.makedirs(out,exist_ok=True); C=css(); N=len(spec['slides']); fn=guia if spec['formato']=='guia' else voz
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/google-chrome');pg=b.new_page(viewport={'width':1080,'height':1350})
        for i,s in enumerate(spec['slides'],1):
            dark=spec['formato']=='voz'
            html=fn(s,spec['serie'],i,N,spec.get('foto'))+foot(dark,i==N)
            pg.set_content(f'<html><head><meta charset="utf-8"><style>{C}</style></head><body>{html}</body></html>');pg.wait_for_timeout(200)
            pg.screenshot(path=f'{out}/{i:02d}.jpg',type='jpeg',quality=90)
        b.close()
if __name__=='__main__': render(json.load(open(sys.argv[1])),sys.argv[2])
