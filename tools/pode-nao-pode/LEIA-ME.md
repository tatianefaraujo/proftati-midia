# Formato "Pode × Não pode" (aprovado pela Tati em 26/11/2026)

Tati grava falando cada item e dizendo "isso pode" / "não pode", apontando para cima: direita da tela = PODE, esquerda = NÃO PODE.

Passos:
1. Proxy 1080x1920 do .mov; transcrição com faster-whisper (palavras com tempo).
2. Cortar pausas e tentativas erradas: `python3 cut.py entrada.mp4 cortado.mp4 '[[ini,fim],...]'` (vídeos longos: cortar por partes e usar concat).
3. Spec JSON (ver exemplo-parte1.json): hook, itens (texto, curto, v=pode|nao, ini=início da leitura, g=momento do "pode/não pode", stamp), fim, words (legenda palavra a palavra).
4. `python3 render_pnp.py spec.json cortado.mp4 reel.mp4` → lista no alto (lado da mão), frase embaixo, selo, legenda de 1 palavra (pode verde, não pode vermelho, IA/MEC amarelo).
5. Som: `python3 sfx.py spec.json DURAÇÃO sfx.wav` (ding no PODE, bonk no NÃO PODE, whoosh quando a frase sobe; sons gerados por código, sem direitos de terceiros) e mixar com amix normalize=0.
