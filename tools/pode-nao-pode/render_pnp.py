import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
BOLD = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
SEMI = '/usr/share/fonts/truetype/google-fonts/Poppins-SemiBold.ttf'
import os
if not os.path.exists(SEMI): SEMI = BOLD
GREEN, RED, YEL, INK = (46, 160, 90), (214, 64, 64), (249, 224, 118), (28, 26, 24)
spec = json.load(open(sys.argv[1])); src, out = sys.argv[2], sys.argv[3]
F = lambda p, s: ImageFont.truetype(p, s)

def wrap(d, text, font, maxw):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def card(text, size=60, sub=None, fill=(255, 255, 255), ink=INK, maxw=900):
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    f = F(BOLD, size)
    lines = wrap(tmp, text, f, maxw - 80)
    lh = int(size * 1.22)
    fs = F(SEMI, 30)
    subl = wrap(tmp, sub, fs, maxw - 80) if sub else []
    h = 60 + lh * len(lines) + (16 + 40 * len(subl) if subl else 0)
    w = maxw
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((20, 26, w + 20, h + 26), 34, fill=(0, 0, 0, 90))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 20, h + 20), 34, fill=fill + (245,))
    y = 50
    for ln in lines:
        d.text((20 + w / 2, y), ln, font=f, fill=ink, anchor='ma'); y += lh
    if subl:
        y += 16
        for ln in subl:
            d.text((20 + w / 2, y), ln, font=fs, fill=(110, 104, 96), anchor='ma'); y += 40
    return im

def pill(text, color, size=54):
    f = F(BOLD, size); tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    tw = tmp.textlength(text, font=f)
    im = Image.new('RGBA', (int(tw) + 90, size + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), im.height // 2, fill=color + (255,))
    d.text((im.width / 2, im.height / 2), text, font=f, fill=(255, 255, 255) if color != YEL else INK, anchor='mm')
    return im

def chip(text, color):
    f = F(SEMI, 34); tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    lines = wrap(tmp, text, f, 370)
    h = 24 + 44 * len(lines)
    im = Image.new('RGBA', (420, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 419, h - 1), 20, fill=(20, 20, 20, 200))
    d.rounded_rectangle((0, 0, 10, h - 1), 5, fill=color + (255,))
    y = 11
    for ln in lines:
        d.text((30, y), ln, font=f, fill=(255, 255, 255)); y += 44
    return im

COLX = {'nao': 30, 'pode': 630}
HEADY = 110
BOT = 1580
heads = {'nao': pill('NÃO PODE', RED, 40), 'pode': pill('PODE', GREEN, 40)}
CARD_Y = 170
ease = lambda t: 1 - (1 - t) ** 3

items = spec['items']
for it in items:
    it['card'] = card(it['texto'])
    if it['v'] != 'dep': it['chip'] = chip(it['curto'], GREEN if it['v'] == 'pode' else RED)
# chip slots
slot = {'nao': HEADY + 80, 'pode': HEADY + 80}
for it in items:
    if it['v'] == 'dep': continue
    it['dest'] = (COLX[it['v']], slot[it['v']]); slot[it['v']] += it['chip'].height + 12
hook = card(spec['hook'], 50, spec.get('hook_sub'))
fim = card(spec['fim'], 54, spec.get('fim_sub'))
for it in items: it['stampim'] = pill(it.get('stamp', 'PODE!' if it['v']=='pode' else 'NÃO PODE'), GREEN if it['v']=='pode' else RED, 50)
SHOW_HEADS = items[0]['ini']

def paste(base, im, x, y, a=1.0):
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(x), int(y)))

WORDS = spec.get('words', [])
for i, x in enumerate(WORDS):
    nxt = WORDS[i+1][1] if i+1 < len(WORDS) else x[1] + 0.8
    x[2] = min(nxt, x[1] + 0.6)
FW = F(BOLD, 104)
_wc = {}
def word_im(w):
    if w in _wc: return _wc[w]
    base = w.strip().strip('.,?!:').lower()
    col = (255, 255, 255)
    if base == 'pode' and w.endswith(' '): col = (255, 120, 120)
    elif base in ('pode',): col = (120, 230, 150)
    elif base in ('não', 'nao'): col = (255, 120, 120)
    elif base in ('ia', 'mec'): col = YEL
    tmp = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    tw = int(tmp.textlength(w.strip(), font=FW))
    im = Image.new('RGBA', (tw + 60, 170), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((30, 30), w.strip(), font=FW, fill=(0, 0, 0, 170))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(7)))
    ImageDraw.Draw(im).text((30, 22), w.strip(), font=FW, fill=col)
    _wc[w] = im; return im
WORD_Y = 1100

def overlay(t):
    o = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    stamping = any(it['g'] <= t < it['f'] for it in items)
    for i, (w, a, b) in enumerate(WORDS):
        if not stamping and a <= t < b:
            if w.strip('.,!?').lower() == 'pode' and i > 0 and WORDS[i-1][0].strip('.,').lower() in ('não', 'nao'): w = w + ' '
            im = word_im(w); k = min(1, (t - a) / 0.08); sc = 1.12 - 0.12 * k
            im2 = im.resize((int(im.width * sc), int(im.height * sc)))
            top = 9999
            if t < spec['hook_fim']: top = BOT - hook.height
            if t >= spec['fim_ini']: top = BOT - fim.height
            for it2 in items:
                if it2['ini'] <= t < it2['f']: top = BOT - it2['card'].height - 70
            wy = min(WORD_Y, top - 150)
            paste(o, im2, (W - im2.width) / 2, wy - (im2.height - im.height) / 2)
            break
    if t < spec['hook_fim']:
        a = min(1, t / 0.25, (spec['hook_fim'] - t) / 0.25)
        paste(o, hook, (W - hook.width) / 2, BOT - hook.height, max(a, 0))
    if t >= SHOW_HEADS:
        a = min(1, (t - SHOW_HEADS) / 0.3)
        for k, hx in COLX.items(): paste(o, heads[k], hx, HEADY, a)
    for it in items:
        g = it['g']; c = it['card']; cx = (W - c.width) / 2; CY = BOT - c.height
        if it['ini'] <= t < it['f']:
            a = min(1, (t - it['ini']) / 0.25)
            paste(o, c, cx, CY, a)
            if t >= g:
                s = it['stampim']; k = min(1, (t - g) / 0.15)
                sc = 1.25 - 0.25 * k
                s2 = s.resize((int(s.width * sc), int(s.height * sc)))
                paste(o, s2, (W - s2.width) / 2, CY - s2.height + 22, k)
        if it['v'] == 'dep':
            if g + 0.8 <= t < g + 3.2:
                a = min(1, (g + 3.2 - t) / 0.3)
                paste(o, c, cx, CARD_Y, a)
                s = STAMP['dep']; paste(o, s, (W - s.width) / 2, CARD_Y + c.height - 10, a)
            continue
        if it['f'] <= t < it['f'] + 0.45:
            k = ease((t - it['f']) / 0.45); ch = it['chip']; dx, dy = it['dest']
            sx, sy = (W - ch.width) / 2, CY + 40
            paste(o, ch, sx + (dx - sx) * k, sy + (dy - sy) * k, 0.4 + 0.6 * k)
        elif t >= it['f'] + 0.45:
            paste(o, it['chip'], *it['dest'])
    if t >= spec['fim_ini']:
        a = min(1, (t - spec['fim_ini']) / 0.3)
        paste(o, fim, (W - fim.width) / 2, BOT - fim.height, a)
    return o

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src]))
lim = float(os.environ.get('LIMITE', dur))
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-t', str(lim), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', src, '-t', str(lim), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
n = 0; fs = W * H * 3
while True:
    b = dec.stdout.read(fs)
    if len(b) < fs: break
    fr = Image.frombytes('RGB', (W, H), b).convert('RGBA')
    fr.alpha_composite(overlay(n / FPS))
    enc.stdin.write(fr.convert('RGB').tobytes()); n += 1
enc.stdin.close(); enc.wait(); print('frames', n)
