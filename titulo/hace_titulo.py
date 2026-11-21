#!/usr/bin/env python3
# Genera ../src/titulo.bin: el rectangulo de la pantalla de titulo (SCREEN 7, 4 bits/pixel, filas 24-95,
# bytes 16-239) con "El Templo del Sol" en lugar de los kanji 太陽の神殿 y "AZTECAII" en lugar de "ASTEKAII".
# En el original ese rectangulo es todo fondo azul, asi que se pinta desde cero.
# Letra del titulo: Ma Shan Zheng (pincel, SIL OFL 1.1); MaShanZheng-Titulo.ttf es un subconjunto con solo esas letras.
# AZTECAII: mismas letras que el ASTEKAII original (1 bit = 2 pixeles) mas una Z y una C dibujadas a juego.
# Uso: python3 hace_titulo.py [fuente.ttf]   (necesita Pillow)
import os, sys
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__))
FUENTE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, 'MaShanZheng-Titulo.ttf')
Y0, Y1, XB0, XB1 = 24, 96, 16, 240          # filas y bytes (2 pixeles por byte)
ROJO, AZUL, BLANCO = 8, 4, 11
a = [[AZUL]*512 for _ in range(212)]
def dib(s): return [[ch == '#' for ch in fila] for fila in s.split()]
L = {'A': dib('..####... ...###... ...###... ..##.##.. ..#..##.. ..#..##.. ..#####.. .##...##. .#....##. ##....###'),
     'T': dib('######## #..##..# ...##... ...##... ...##... ...##... ...##... ...##... ...##... ..####..'),
     'E': dib('####### .##...# .##.... .##.... .#####. .##.... .##.... .##.... .##...# #######'),
     'II': dib('##.### .#.##. .#.##. .#.##. .#.##. .#.##. .#.##. .#.##. .#.##. ##.###'),
     'Z': dib('.#######. .#....##. .....##.. ....##... ....##... ...##.... ...##.... ..##..... .##....#. ########.'),
     'C': dib('..####.# .##...## ##.....# ##...... ##...... ##...... ##...... ##...... .##....# ..#####.')}
# "El Templo del Sol"
S = 8; f = ImageFont.truetype(FUENTE, 40*S); t = 'El Templo del Sol'
bb = f.getbbox(t); w, h = bb[2]-bb[0], bb[3]-bb[1]
im = Image.new('L', (w+4*S, h+4*S), 0); ImageDraw.Draw(im).text((2*S-bb[0], 2*S-bb[1]), t, font=f, fill=255)
W, H = 410, 46
sc = min(W/(im.size[0]/S*2), H/(im.size[1]/S))
tw = int(im.size[0]/S*2*sc); th = int(im.size[1]/S*sc)
sm = im.resize((tw, th), Image.LANCZOS)
x0 = 256 - tw//2; y0 = 52 - th//2
for y in range(th):
    for x in range(tw):
        if sm.getpixel((x, y)) > 110: a[y0+y][x0+x] = ROJO
# "AZTECAII" (y 83-92, centrado en el byte 132 como el original)
pal = ['A', 'Z', 'T', 'E', 'C', 'A', 'II']
ancho = sum(len(L[p][0]) for p in pal) + len(pal) - 1
bx = 96 + 36 - ancho//2
for p in pal:
    for fy, fila in enumerate(L[p]):
        for fx, b in enumerate(fila):
            if b: a[83+fy][2*(bx+fx)] = a[83+fy][2*(bx+fx)+1] = BLANCO
    bx += len(L[p][0]) + 1
out = bytearray()
for y in range(Y0, Y1):
    for xb in range(XB0, XB1): out.append(a[y][2*xb] << 4 | a[y][2*xb+1])
open(os.path.join(D, '..', 'src', 'titulo.bin'), 'wb').write(out)
p = {AZUL: (0, 36, 252), ROJO: (216, 36, 36), BLANCO: (252, 252, 252)}
o = Image.new('RGB', (2*(XB1-XB0), Y1-Y0))
for y in range(Y0, Y1):
    for x in range(2*XB0, 2*XB1): o.putpixel((x-2*XB0, y-Y0), p[a[y][x]])
o.resize((o.size[0], 2*o.size[1]), Image.NEAREST).save(os.path.join(D, 'titulo_es.png'))
print('titulo.bin', len(out), 'bytes; texto %dx%d en x=%d y=%d' % (tw, th, x0, y0))
