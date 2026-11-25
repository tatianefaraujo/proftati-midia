#!/usr/bin/env python3
"""Revisor dos carrosséis do @proftatiaraujo.

Confere uma pasta de post (posts/AAAA-MM-DD-HHh-nome/) antes de ela ir para a Tati:
slides (tamanho, espaço até o rodapé, margens, letra legível, slide lotado, capa)
e legenda (nome, tamanho, hashtags, brinde, direitos autorais).

Uso:  python3 tools/revisor.py posts/<pasta> [posts/<pasta2> ...]
Sai com código 1 se algum item der ✗ (refazer antes de mandar).
Gera <pasta>/revisao.md e /tmp/revisao-<pasta>.jpg (miniaturas para olhar).

© Prof. Tati, com apoio de IA (Claude). Proibido copiar sem créditos.
"""
import os, re, sys, glob, subprocess, statistics
from PIL import Image, ImageDraw
import numpy as np

W, H = 1080, 1350
RODAPE_Y = 1255        # a faixa do rodapé (@proftatiaraujo · salva pra depois · arrasta) começa aqui
FOLGA_MIN = 30         # o conteúdo tem que terminar pelo menos 30 px acima do texto do rodapé
RODAPE_TEXTO = 1262    # onde começam as letras do rodapé
MARGEM = 36            # nada de conteúdo colado nas bordas laterais
TOPO_TAG = 100         # faixa da etiqueta de cima (pode ter letra pequena)
LETRA_MIN = 18         # palavras de texto corrido abaixo disso (px): não dá para ler no celular (✗)
LETRA_AVISO = 22       # entre 18 e 22 px: lê, mas no limite (⚠)
PALAVRAS_MAX = 70      # acima disso o slide está lotado
CAPA_MAX = 14          # palavras no título da capa
PALAVRAS_BRINDE = {"CONTEXTO", "PROMPTS", "FICHA", "DESAFIO"}


def fundo_liso(a):
    """True se o slide tem fundo de cor lisa (formato GUIA). Foto (VOZ) dá False."""
    bordas = np.concatenate([a[TOPO_TAG:RODAPE_Y, :20].reshape(-1, 3), a[TOPO_TAG:RODAPE_Y, -20:].reshape(-1, 3)])
    bg = np.median(bordas, axis=0)
    interior = np.abs(a[TOPO_TAG:RODAPE_Y:4, ::4] - bg).sum(axis=2) < 45
    return bordas.std(axis=0).mean() < 18 and interior.mean() > 0.45, bg


def ocr(path):
    out = subprocess.run(["tesseract", path, "-", "-l", "por", "--psm", "11", "tsv"],
                         capture_output=True, text=True).stdout
    words = []
    for ln in out.splitlines()[1:]:
        p = ln.split("\t")
        if len(p) < 12 or not p[11].strip():
            continue
        try:
            conf = float(p[10])
        except ValueError:
            continue
        if conf < 55:
            continue
        x, y, w, h = map(int, p[6:10])
        words.append(dict(t=p[11].strip(), x=x, y=y, w=w, h=h))
    return words


def checar_slide(path, idx, total):
    res = []  # (nivel, texto) nivel: ok / aviso / erro
    im = Image.open(path)
    if im.size != (W, H):
        res.append(("erro", f"tamanho {im.size[0]}×{im.size[1]} (precisa 1080×1350)"))
    if os.path.getsize(path) > 8 * 1024 * 1024:
        res.append(("erro", "arquivo maior que 8 MB"))
    if im.format != "JPEG":
        res.append(("erro", "não é JPEG"))
    a = np.asarray(im.convert("RGB")).astype(int)
    liso, bg = fundo_liso(a)
    if liso:
        dif = np.abs(a - bg).sum(axis=2) > 120  # >120 ignora o quadriculado do fundo
        linhas_c = np.where(dif[TOPO_TAG:].sum(axis=1) > 3)[0] + TOPO_TAG
        blocos = []
        for y in linhas_c:
            if blocos and y - blocos[-1][1] <= 12:
                blocos[-1][1] = y
            else:
                blocos.append([y, y])
        # o último bloco é o rodapé (@proftatiaraujo · salva pra depois · arrasta)
        if blocos and blocos[-1][1] > 1150 and blocos[-1][0] < 1238:
            rodape_ini = RODAPE_Y
            res.append(("erro", "o conteúdo encosta no rodapé (texto colado na faixa do @proftatiaraujo)"))
        elif len(blocos) >= 2 and blocos[-1][0] > 1150:
            rodape_ini = blocos[-1][0]
            fim = blocos[-2][1]
            folga = rodape_ini - fim
            if folga < FOLGA_MIN:
                res.append(("erro", f"o conteúdo encosta no rodapé (sobram {max(folga,0)} px; mínimo {FOLGA_MIN})"))
        else:
            rodape_ini = RODAPE_Y
            if blocos and blocos[-1][1] > 1150:
                res.append(("erro", "não achei o rodapé separado do conteúdo (texto colado no rodapé?)"))
        miolo = dif[TOPO_TAG:rodape_ini - 2]
        cols = np.where(miolo.sum(axis=0) > 3)[0]
        if len(cols) and (cols.min() < MARGEM or cols.max() > W - MARGEM):
            res.append(("erro", "conteúdo colado na borda lateral"))
    words = ocr(path)
    corpo = [w for w in words if TOPO_TAG < w["y"] < RODAPE_Y and re.search(r"[A-Za-zÀ-ú]{3,}", w["t"])]
    if corpo:
        cand = [w for w in corpo if w["t"].islower() and len(w["t"]) >= 4]
        pequenas = [w for w in cand if w["h"] < LETRA_MIN]
        limite = [w for w in cand if LETRA_MIN <= w["h"] < LETRA_AVISO]
        if len(pequenas) >= 6:
            ex = " ".join(w["t"] for w in pequenas[:6])
            res.append(("erro", f"letra pequena demais para o celular ({len(pequenas)} palavras, ex.: \"{ex}\")"))
        elif len(limite) >= 6:
            res.append(("aviso", "letra no limite da leitura no celular; se der, aumentar ou cortar texto"))
        if len(corpo) > PALAVRAS_MAX:
            res.append(("erro", f"slide lotado ({len(corpo)} palavras; máximo {PALAVRAS_MAX})"))
    if idx == 0:
        alturas = [w["h"] for w in corpo]
        if alturas:
            corte = max(alturas) * 0.7
            titulo = [w["t"] for w in sorted(corpo, key=lambda w: (w["y"] // 40, w["x"])) if w["h"] >= corte and w["y"] < 800]
            txt = " ".join(titulo)
            if len(titulo) > CAPA_MAX:
                res.append(("erro", f"título da capa longo demais ({len(titulo)} palavras): \"{txt}\""))
            elif txt:
                res.append(("aviso", f"capa: tem posição da Tati (opinião/chamado, não só tema) e é verdadeira? → \"{txt}\""))
            else:
                res.append(("aviso", "capa: não consegui ler o título; conferir à mão se promete um resultado concreto"))
    if not [r for r in res if r[0] == "erro"]:
        res.insert(0, ("ok", "tamanho, rodapé, margens e letra"))
    return res, words


def checar_legenda(pasta):
    nome = os.path.basename(pasta.rstrip("/"))
    res = []
    txt = os.path.join(pasta, nome + ".txt")
    if not os.path.exists(txt):
        outros = glob.glob(os.path.join(pasta, "*.txt"))
        res.append(("erro", f"legenda {nome}.txt não existe" + (f" (achei {os.path.basename(outros[0])}: renomear)" if outros else "")))
        return res, None
    s = open(txt, encoding="utf-8").read().strip()
    if len(s) > 2200:
        res.append(("erro", f"legenda com {len(s)} caracteres (máximo 2.200)"))
    tags = re.findall(r"#\w+", s)
    if len(tags) > 5:
        res.append(("erro", f"{len(tags)} hashtags (máximo 5)"))
    if re.search(r"__\w+__|\{\{|\[LEGENDA|PLACEHOLDER|lorem", s, re.I):
        res.append(("erro", "legenda com texto provisório (placeholder)"))
    m = re.search(r"Comente\s+\"?“?([A-ZÇÃÕÉ]{4,})", s)
    palavra = m.group(1) if m else None
    if not palavra:
        res.append(("erro", "falta o \"Comente PALAVRA\" do brinde"))
    elif palavra not in PALAVRAS_BRINDE:
        res.append(("erro", f"palavra do brinde \"{palavra}\" não tem automação (use {', '.join(sorted(PALAVRAS_BRINDE))})"))
    if "©" not in s or "Proibido" not in s and "direitos reservados" not in s:
        res.append(("erro", "falta o aviso de direitos autorais (© Prof. Tati ... Proibido copiar sem créditos)"))
    if "IA" not in s and "Claude" not in s:
        res.append(("aviso", "a legenda não diz que teve apoio de IA"))
    primeira = s.splitlines()[0]
    if len(primeira) > 160:
        res.append(("aviso", f"primeira linha longa ({len(primeira)} caracteres); o SEO fica melhor até ~150"))
    if not [r for r in res if r[0] == "erro"]:
        res.insert(0, ("ok", f"{len(s)} caracteres, {len(tags)} hashtags, brinde {palavra}, direitos autorais"))
    return res, palavra


def miniaturas(paths, destino, marcas):
    tw, th = 270, 338
    c = Image.new("RGB", (tw * len(paths), th + 30), "white")
    d = ImageDraw.Draw(c)
    for k, p in enumerate(paths):
        c.paste(Image.open(p).convert("RGB").resize((tw, th)), (k * tw, 0))
        d.text((k * tw + 8, th + 8), f"{k+1:02d} {marcas[k]}", fill=(0, 0, 0))
    c.save(destino, quality=85)


def revisar(pasta):
    nome = os.path.basename(pasta.rstrip("/"))
    slides = sorted(glob.glob(os.path.join(pasta, "*.jpg")))
    if not slides and glob.glob(os.path.join(pasta, "*.mp4")):
        print(f"# {nome}: é Reel, não carrossel (pulei)\n")
        return 0
    linhas = [f"# Revisão · {nome}", ""]
    erros = 0
    if not 2 <= len(slides) <= 10:
        linhas.append(f"✗ carrossel com {len(slides)} slides (precisa de 2 a 10)")
        erros += 1
    textos_ultimo = ""
    marcas = []
    for i, p in enumerate(slides):
        res, words = checar_slide(p, i, len(slides))
        if i == len(slides) - 1:
            textos_ultimo = " ".join(w["t"] for w in words)
        tem_erro = any(r[0] == "erro" for r in res)
        marcas.append("✗" if tem_erro else "ok")
        for nivel, t in res:
            sim = {"ok": "✓", "aviso": "⚠", "erro": "✗"}[nivel]
            linhas.append(f"{sim} Slide {i+1}: {t}")
            erros += nivel == "erro"
    res, palavra = checar_legenda(pasta)
    for nivel, t in res:
        sim = {"ok": "✓", "aviso": "⚠", "erro": "✗"}[nivel]
        linhas.append(f"{sim} Legenda: {t}")
        erros += nivel == "erro"
    if palavra and palavra not in textos_ultimo.upper() and "COMENTE" not in textos_ultimo.upper():
        linhas.append(f"⚠ Último slide: não achei o \"Comente {palavra}\" no slide (só na legenda)")
    linhas += ["", f"**Resultado: {len(slides) and (len(slides) - marcas.count('✗'))} de {len(slides)} slides ok; "
               + ("pode ir para a Tati.**" if erros == 0 else f"{erros} item(ns) para refazer.**"),
               "", "Falta conferir à mão: automação da palavra do brinde ligada no Hypello; capa e 1ª linha da legenda com posição da Tati (regra 24/11, ver claude/posicionamento-carrosseis.md)."]
    open(os.path.join(pasta, "revisao.md"), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    if slides:
        miniaturas(slides, f"/tmp/revisao-{nome}.jpg", marcas)
    print("\n".join(linhas))
    print()
    return erros


if __name__ == "__main__":
    total = sum(revisar(p) for p in sys.argv[1:])
    sys.exit(1 if total else 0)
