# Renderizador de Reels da Prof. Tati (legenda + palavra grande atrás da pessoa).
# Uso: python3 render_reel.py saida.mp4 spec.json   (spec: src, segs, keep, kwy, capy, estilo)
# © Prof. Tati, com apoio de IA (Claude). Proibido copiar sem créditos.
import cv2, numpy as np, subprocess, math, sys, json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from ai_edge_litert.interpreter import Interpreter

SPEC = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
SRC = SPEC['src'] if SPEC else '/tmp/reelA/src.mp4'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/reelA/out.mp4'
W, H, FPS = 1080, 1920, 30
BUTTER = (249, 224, 118)
KWC = (255, 250, 240)
HOOK = os.environ.get('HOOK')
ESTILO = (SPEC or {}).get('estilo', 'limpo')   # 'limpo' (regras anti-cara-de-IA, 23/11) ou 'classico'
SANS = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
F_CAP = ImageFont.truetype('/tmp/fonts/Fraunces-700.ttf', 74)
F_KW = SANS if ESTILO == 'limpo' else '/tmp/fonts/Fraunces-900.ttf'
LIMITE = float(os.environ.get('LIMITE', '1e9'))   # para testes: renderiza só até este segundo

# trechos removidos (pausas), em segundos do original
CUTS = [(4.55, 4.78), (28.95, 29.30), (31.62, 32.02), (33.95, 99)]

# (inicio, fim, legenda de 1 linha, palavra-chave grande atrás | None)
SEGS = [
 (0.00, 1.00, 'Sabe por que a IA', HOOK),
 (1.00, 2.05, 'te dá respostas', 'GENÉRICAS?'),
 (2.10, 3.00, 'Falta uma dessas', None),
 (3.00, 3.75, '', '4 COISAS'),
 (3.77, 4.55, 'Primeiro:', 'PERSONA'),
 (4.80, 5.25, 'diga quem ela é', None),
 (5.27, 7.20, '"Você é professora', None),
 (7.20, 9.00, 'de ciências do 6º ano"', None),
 (9.03, 10.40, 'Segundo:', 'CONTEXTO'),
 (10.43, 12.00, 'conte sobre a sua turma', None),
 (12.00, 13.60, '"Meus alunos têm', None),
 (13.60, 14.45, 'dificuldade em', None),
 (14.45, 15.90, 'interpretação de texto"', None),
 (16.10, 17.60, 'Terceiro:', 'AÇÃO'),
 (17.95, 18.95, '"Crie uma atividade', None),
 (19.45, 20.80, 'sobre cadeia alimentar"', None),
 (21.00, 21.90, 'Quarto:', 'FORMATO'),
 (21.90, 22.85, 'como quer receber', None),
 (23.00, 25.10, '"Uma tabela com gabarito"', None),
 (26.00, 26.80, '', 'PERSONA'),
 (26.83, 27.62, '', 'CONTEXTO'),
 (27.63, 28.90, '', 'AÇÃO + FORMATO'),
 (29.30, 30.05, 'São as 4 partes', None),
 (30.05, 31.62, 'que todo prompt precisa', 'PROMPT'),
 (32.02, 33.00, 'Salva este vídeo', 'SALVA'),
 (33.00, 33.95, 'pra não esquecer', None),
]

if SPEC:
    SEGS = [tuple(x) for x in SPEC['segs']]
    KEEP = SPEC['keep']
else:
    KEEP = []; _l = 0.0
    for a, b in CUTS:
        if a > _l: KEEP.append((_l, a))
        _l = b
def kept(t):
    return any(a <= t < b for a, b in KEEP)

# ---------- segmentação ----------
seg = Interpreter(model_path='/tmp/seg/package/selfie_segmentation.tflite'); seg.allocate_tensors()
inp = seg.get_input_details()[0]['index']; outi = seg.get_output_details()[0]['index']
prev_mask = None
def person_mask(rgb):
    global prev_mask
    x = cv2.resize(rgb, (256, 256)).astype(np.float32) / 255.0
    seg.set_tensor(inp, x[None]); seg.invoke()
    m = seg.get_tensor(outi)[0, :, :, 0]
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    m = np.clip((m - 0.35) / 0.3, 0, 1)
    if prev_mask is not None: m = 0.6 * m + 0.4 * prev_mask
    prev_mask = m
    m = cv2.GaussianBlur(m, (0, 0), 3)
    return m[..., None]

# ---------- desenho ----------
def star(d, cx, cy, r, fill):
    pts = []
    for k in range(8):
        ang = math.pi / 4 * k - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.28
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)

def ease(p): return 1 - (1 - min(max(p, 0), 1)) ** 3

def kw_layer(text, p, t):
    """palavra grande, para ficar ATRÁS da pessoa (sans negrito no estilo limpo)"""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    size = 260
    while True:
        f = ImageFont.truetype(F_KW, size)
        b0 = d.textbbox((0, 0), text, font=f)
        if b0[2] - b0[0] <= 940 or size < 90: break
        size -= 8
    if ESTILO == 'limpo':
        s, a = 1.0, 255   # entra no corte, sem zoom nem fade
    else:
        s = 0.82 + 0.18 * ease(p / 0.18)
        a = int(255 * ease(p / 0.12))
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    T = Image.new('RGBA', (tw + 40, th + 60), (0, 0, 0, 0)); td = ImageDraw.Draw(T)
    sh = Image.new('RGBA', T.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((20 - bb[0], 26 - bb[1]), text, font=f, fill=(25, 18, 10, int(a * 0.55)))
    T.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    td.text((20 - bb[0], 20 - bb[1]), text, font=f, fill=KWC + (a,))
    T = T.resize((max(1, int(T.width * s)), max(1, int(T.height * s))), Image.LANCZOS)
    y = SPEC.get('kwy', 300) if SPEC else 300
    L.alpha_composite(T, (W // 2 - T.width // 2, y - T.height // 2 + 80))
    return L

def front_layer(cap, kw, p, t):
    if ESTILO == 'limpo':
        return front_limpo(cap, kw)
    return front_classico(cap, kw, p, t)

def quebra(d, palavras, f, larg):
    linhas, atual = [], []
    for w in palavras:
        teste = ' '.join(atual + [w]).replace('*', '')
        if atual and d.textlength(teste, font=f) > larg:
            linhas.append(atual); atual = [w]
        else:
            atual.append(w)
    if atual: linhas.append(atual)
    return linhas

def front_limpo(cap, kw):
    """Legenda em sans negrito, branca, sombra escura suave, sem contorno, no máximo 2 linhas,
    1 palavra de destaque em amarelo (*assim* no texto, ou a palavra-chave se ela estiver na frase).
    Entra no corte, sem animação; sem estrelinhas."""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if not cap: return L
    d = ImageDraw.Draw(L)
    palavras = cap.split()
    if '*' not in cap and kw:
        alvo = kw.lower().strip('?!.,')
        for k, w in enumerate(palavras):
            if w.lower().strip('?!.,"') == alvo:
                palavras[k] = '*' + w + '*'; break
    sz = 70
    while True:
        f = ImageFont.truetype(SANS, sz)
        linhas = quebra(d, palavras, f, 940)
        if len(linhas) <= 2 or sz <= 46: break
        sz -= 4
    y = SPEC.get('capy', 1430) if SPEC else 1430
    lh = int(sz * 1.22)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    pos = []
    for li, ln in enumerate(linhas):
        txt = ' '.join(ln).replace('*', '')
        x = W // 2 - int(d.textlength(txt, font=f)) // 2
        for w in ln:
            dest = w.startswith('*')
            limpa = w.replace('*', '')
            pos.append((x, y + li * lh, limpa, dest))
            sd.text((x, y + li * lh + 5), limpa, font=f, fill=(0, 0, 0, 165))
            x += int(d.textlength(limpa + ' ', font=f))
    L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    for x, yy, w, dest in pos:
        if dest:
            nucleo = w.rstrip('.,!?…:;"')
            d.text((x, yy), nucleo, font=f, fill=BUTTER + (255,))
            if nucleo != w:
                d.text((x + int(d.textlength(nucleo, font=f)), yy), w[len(nucleo):], font=f, fill=(255, 255, 255, 255))
        else:
            d.text((x, yy), w, font=f, fill=(255, 255, 255, 255))
    return L

def front_classico(cap, kw, p, t):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    if cap:
        a = int(255 * ease(p / 0.10))
        fc = F_CAP; sz = 74
        while d.textbbox((0, 0), cap, font=fc)[2] > 980 and sz > 44:
            sz -= 4; fc = ImageFont.truetype('/tmp/fonts/Fraunces-700.ttf', sz)
        bb = d.textbbox((0, 0), cap, font=fc)
        x = W // 2 - (bb[2] - bb[0]) // 2; y = SPEC.get('capy', 1430) if SPEC else 1430
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.text((x, y + 4), cap, font=fc, fill=(20, 15, 10, int(a * 0.85)))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        L.alpha_composite(sh)
        d.text((x, y), cap, font=fc, fill=BUTTER + (a,), stroke_width=3, stroke_fill=(30, 22, 12, int(a * 0.9)))
    if kw:
        # estrelinhas piscando em volta da palavra-chave
        tw = 300
        for i, (dx, dy, r, ph) in enumerate([(-1, -1, 30, 0), (1, -0.6, 22, 1.7), (0.85, 1.05, 16, 3.1), (-0.9, 0.9, 20, 4.4)]):
            k = 0.55 + 0.45 * math.sin(t * 7 + ph)
            rr = r * k * ease(p / 0.2)
            if rr > 2:
                star(d, W // 2 + dx * (tw + 160), (SPEC.get('kwy', 300) if SPEC else 300) + 85 + dy * 150, rr, (255, 246, 214, 235))
    return L

# ---------- vídeo ----------
cap = cv2.VideoCapture(SRC)
n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', OUT + '.v.mp4'], stdin=subprocess.PIPE)
i = 0
while True:
    ok, fr = cap.read()
    if not ok: break
    t = i / FPS; i += 1
    if t > LIMITE: break
    if not kept(t): continue
    rgb = cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LANCZOS4)
    bl = cv2.GaussianBlur(rgb, (0, 0), 2); rgb = cv2.addWeighted(rgb, 1.35, bl, -0.35, 0)
    m = person_mask(rgb)
    seg_now = [s for s in SEGS if s[0] <= t < s[1]]
    base = Image.fromarray(rgb).convert('RGBA')
    if seg_now:
        s0, s1, capt, kw = seg_now[0]; p = t - s0
        if kw:
            bg = Image.alpha_composite(base, kw_layer(kw, p, t))
            comp = np.array(bg.convert('RGB')).astype(np.float32) * (1 - m) + rgb.astype(np.float32) * m
            base = Image.fromarray(comp.astype(np.uint8)).convert('RGBA')
        base = Image.alpha_composite(base, front_layer(capt, kw, p, t))
    ff.stdin.write(np.array(base.convert('RGB')).tobytes())
ff.stdin.close(); ff.wait()

# áudio com os mesmos cortes
keep = KEEP
sel = '+'.join(f'between(t,{a},{b})' for a, b in keep)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', OUT + '.v.mp4', '-i', SRC,
                '-filter_complex', f"[1:a]aselect='{sel}',asetpts=N/SR/TB,afftdn=nf=-25,loudnorm=I=-14:TP=-1.5[a]",
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '160k', '-shortest', OUT], check=True)
print('ok', OUT)
