#!/usr/bin/env python3
# Construye la ROM traducida de Taiyou no Shinden - Asteka II a partir de la original intacta.
# Uso: python3 build.py ORIGINAL.rom   -> salida/Asteka2_ES.rom, salida/Asteka2_ES.ips, salida/softwaredb.xml
# Necesita Python 3 con Pillow y el ensamblador Pasmo en el PATH.
import sys, os, hashlib, subprocess, re
D = os.path.dirname(os.path.abspath(__file__))
SHA_ORIG = '414fd2a22076f45502c2329b45bda9f8730dcaae'
orig = open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, 'asteka2.rom'), 'rb').read()
assert hashlib.sha1(orig).hexdigest() == SHA_ORIG, 'la ROM original no es la buena (SHA1)'
rom = bytearray(orig) + b'\xff' * 0x40000          # 512 KB

AVISOS = []
def parche(dir_cpu, viejo, nuevo):
    o = dir_cpu - 0x4000                             # bancos 0-1 fijos en 4000h-7FFFh
    assert rom[o:o+len(viejo)] == bytes(viejo), 'bytes inesperados en %04X' % dir_cpu
    rom[o:o+len(nuevo)] = bytes(nuevo)

# ---------------- textos ----------------
CAR = {'á':0xA0,'é':0x82,'í':0xA1,'ó':0xA2,'ú':0xA3,'ü':0x81,'ñ':0xA4,'Ñ':0xA5,'¿':0xA8,'¡':0xAD,
       'É':0x90,'«':0xAE,'»':0xAF,'Á':0x41,'Í':0x49,'Ó':0x4F,'Ú':0x55}
def codifica(s, clave):
    out = bytearray(); i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i+1 < len(s):
            out.append({'n':0x0A,'t':0x09,'p':0x0C}[s[i+1]]); i += 2; continue
        if c in CAR: out.append(CAR[c])
        elif 0x20 <= ord(c) < 0x7f: out.append(ord(c))
        else: raise SystemExit('caracter no admitido %r en %s' % (c, clave))
        i += 1
    return bytes(out)

def lineas(b, ancho):
    """Simula el corte de lineas del motor: devuelve el numero de lineas."""
    x = 0; n = 1; prev = 0x20; i = 0
    while i < len(b):
        c = b[i]
        if c == 0x0A: x = 0; n += 1; prev = 0x20
        elif c == 0x0C: x = 0; n = 1; prev = 0x20
        elif c == 0x09: x = ((x + 1) & 0xF0) + 0x0F; prev = 0x20
        elif c == 0x20:
            prev = 0x20
            if x: x += 3
        else:
            if prev <= 0x20:
                j = i
                while j < len(b) and b[j] > 0x20: j += 1
                if x + 3*(j-i) > ancho - 1 and x: x = 0; n += 1
            if x + 3 > ancho - 1: x = 0; n += 1
            x += 3; prev = c
        i += 1
    return n

# contexto de cada texto (ancho en bytes = glifos*8, lineas maximas)
def contexto(clave):
    if not clave.startswith('@'): return (0xC0, 3, 'ventana')
    a = int(clave[1:], 16)
    if a < 0xAEE4: return (0x90, 1, 'menu')
    if a < 0xAF30: return (0x60, 1, 'recuadro')
    if a < 0xAFBE: return (0xC0, 3, 'ventana')
    if a < 0xB189: return (0x60, 1, 'recuadro')
    if a < 0xB1C1: return (0xC0, 3, 'ventana')
    if a < 0xB2FF: return (0xC0, 4, 'presentacion')
    if a == 0xB2FF: return (0x80, 2, 'reset')
    if a == 0xB312: return (0xC0, 4, 'presentacion')
    return (0xC0, 3, 'final')

def lee_textos():
    ent = []; clave = None; jp = es = None
    for ln in open(os.path.join(D, 'textos', 'traduccion.txt'), encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = re.match(r'^\[(@?[0-9A-F]{4})\]', ln)
        if m: clave = m.group(1); continue
        if ln.startswith('es:') and clave:
            t = ln[3:].strip()
            t = t.replace('{_}', ' ')
            if t: ent.append((clave, t))
    return ent

textos = lee_textos()
# los mensajes se buscan por la direccion de su texto japones
claves = {}
fin = []
for clave, t in textos:
    k = clave if clave.startswith('@') else clave
    a = int(k.lstrip('@'), 16)
    ctx = contexto(clave)
    if ctx[2] == 'final':
        fin.append((a, t)); continue
    b = codifica(t, clave)
    n = lineas(b, ctx[0])
    if n > ctx[1]: AVISOS.append('NO CABE (%d lineas, max %d) %s: %s' % (n, ctx[1], clave, t))
    claves[a] = b
# final: un solo texto (clave B347h), paginas separadas con \p
if fin:
    fin.sort()
    b = b'\x0c'.join(codifica(t, 'final') for a, t in fin)
    for pag in b.split(b'\x0c'):
        if lineas(pag, 0xC0) > 3: AVISOS.append('FINAL: pagina de mas de 3 lineas: %r' % pag)
    pasos = len(re.findall(rb'[^\x00-\x20]+', b)) + b.count(b'\x0c') + 1
    if pasos > 170: AVISOS.append('FINAL: %d pasos (max 170)' % pasos)
    print('final: %d pasos de 176' % pasos)
    claves[0xB347] = b

# reparto en bancos de 8 KB (paginas 17..31: banco par = textos, impar = motor)
tabla = bytearray(); pag = 17; ptr = 0x8000; bancos = {17: bytearray()}
for a in sorted(claves):
    b = claves[a] + b'\x00'
    if ptr + len(b) > 0xA000:
        pag += 1; ptr = 0x8000; bancos[pag] = bytearray()
        assert pag <= 31
    tabla += a.to_bytes(2, 'little') + bytes([pag]) + ptr.to_bytes(2, 'little')
    bancos[pag] += b; ptr += len(b)
print('textos: %d, paginas %d-%d, ultima con %d bytes' % (len(claves), 17, pag, len(bancos[pag])))

# ---------------- ensamblado ----------------
S = os.path.join(D, 'src'); O = os.path.join(D, 'obj'); os.makedirs(O, exist_ok=True)
fuente = open(os.path.join(D, 'fuente', 'SCREEN0.bin'), 'rb').read()
open(os.path.join(S, 'fuente.bin'), 'wb').write(fuente[0x100:0x800])
open(os.path.join(S, 'tabla.bin'), 'wb').write(tabla)
def asm(nombre):
    out = os.path.join(O, nombre + '.bin')
    r = subprocess.run(['pasmo', '--bin', nombre + '.asm', out, os.path.join(O, nombre + '.sym')], cwd=S, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
    return open(out, 'rb').read(), dict((l.split()[0], int(l.split()[2].rstrip('H'), 16)) for l in open(os.path.join(O, nombre + '.sym')) if 'EQU' in l)
subprocess.run([sys.executable, os.path.join(D, 'titulo', 'hace_titulo.py')], check=True)   # src/titulo.bin
stubs, ss = asm('stubs')
motor, sm = asm('motor')
titulo, st = asm('titulo')
assert len(titulo) <= 0x4000
assert len(stubs) <= 370, 'enganches demasiado largos'
assert len(motor) <= 0x2000, 'motor demasiado largo'
print('enganches %d bytes de 370; motor+fuente+tabla %d bytes de 8192' % (len(stubs), len(motor)))
assert rom[0x3E8E:0x3E8E+len(stubs)] == b'\xff' * len(stubs)
rom[0x3E8E:0x3E8E+len(stubs)] = stubs
rom[21*0x4000:21*0x4000+len(titulo)] = titulo           # pagina 21: titulo en castellano
for p, b in bancos.items():
    rom[p*0x4000:p*0x4000+len(b)] = b
    rom[p*0x4000+0x2000:p*0x4000+0x2000+len(motor)] = motor
J = lambda n: [0xC3, ss[n] & 0xff, ss[n] >> 8]
parche(0x5E7E, [0x87, 0x32, 0x00, 0x70], J('SRAM_EI'))      # S-RAM con bit 40h (ROM de 512 KB)
parche(0x5EE9, [0x87, 0x32, 0x00, 0x70], J('SRAM_DI'))
parche(0x4D23, [0x32, 0xE1, 0xE9], J('H_CADENA'))
parche(0x4CB8, [0x32, 0xE1, 0xE9], J('H_RANGO'))
parche(0x4D8E, [0x32, 0xE1, 0xE9], J('H_LENTA'))
parche(0x4ECD, [0x32, 0xE1, 0xE9], J('H_LENTA2'))
parche(0x4E15, [0x3E, 0x9C, 0x32], J('H_PREPFIN'))
parche(0x4E27, [0x3A, 0xE2, 0xE9], J('H_UNGLIFO'))
parche(0x58A7, [0xCD, 0x28, 0x69], [0xCD, ss['H_TITULO'] & 0xff, ss['H_TITULO'] >> 8])  # titulo en castellano
parche(0x58B5, [0xCD, 0x28, 0x69], [0xCD, ss['H_ASTEKA'] & 0xff, ss['H_ASTEKA'] >> 8])  # AZTECA II (lo pinta H_TITULO)
parche(0x540D, [0x11, 0x10, 0x08], [0x11, 0x10, 0x0A])  # resaltado del menu Ir: 20 px en vez de 16
parche(0x7C77, list(b'calacol'), list(b'caracol'))  # creditos del final: CALACOL -> CARACOL
parche(0x7C41, list(b'(asteka \\)'), list(b'(akteca \\)'))  # creditos: (ASTEKA II) -> (AZTECA II); la k se usa como z
parche(0xBCA4, [0, 0, 0, 61, 193, 152, 27, 1, 224, 27, 1, 152, 24, 195, 220, 0, 0, 0], [0, 0, 0, 63, 130, 24, 3, 0, 96, 12, 1, 128, 48, 131, 248, 0, 0, 0])  # glifo k de los creditos -> z (la k solo sale en ASTEKA)

# ---------------- salida ----------------
SAL = os.path.join(D, 'salida'); os.makedirs(SAL, exist_ok=True)
rom = bytes(rom)
open(os.path.join(SAL, 'Asteka2_ES.rom'), 'wb').write(rom)
sha = hashlib.sha1(rom).hexdigest()
# IPS (con registros RLE para los rellenos)
ips = bytearray(b'PATCH'); a = orig + b'\x00' * (len(rom) - len(orig)); i = 0; n0 = len(orig)
dif = lambda k: k >= n0 or a[k] != rom[k]
while i < len(rom):
    if not dif(i): i += 1; continue
    j = i
    while j < len(rom) and j - i < 0xFFFF and (dif(j) or any(dif(k) for k in range(j, min(j+6, len(rom))))): j += 1
    # trozos repetidos largos -> RLE
    k = i
    while k < j:
        r = k
        while r < j and rom[r] == rom[k] and r - k < 0xFFFF: r += 1
        if r - k >= 16:
            ips += k.to_bytes(3, 'big') + b'\x00\x00' + (r-k).to_bytes(2, 'big') + bytes([rom[k]]); k = r
        else:
            e = k
            while e < j:
                r = e
                while r < j and rom[r] == rom[e]: r += 1
                if r - e >= 16: break
                e = r
            e = min(e, k + 0xFFFF)
            ips += k.to_bytes(3, 'big') + (e-k).to_bytes(2, 'big') + rom[k:e]; k = e
    i = j
ips += b'EOF'
# comprobacion del IPS
r = bytearray(orig); k = 5
while ips[k:k+3] != b'EOF':
    o = int.from_bytes(ips[k:k+3], 'big'); n = int.from_bytes(ips[k+3:k+5], 'big'); k += 5
    if n == 0:
        n = int.from_bytes(ips[k:k+2], 'big'); v = ips[k+2:k+3] * n; k += 3
    else:
        v = ips[k:k+n]; k += n
    if len(r) < o + n: r += b'\x00' * (o + n - len(r))
    r[o:o+n] = v
assert bytes(r) == rom, 'el IPS no reproduce la ROM'
open(os.path.join(SAL, 'Asteka2_ES.ips'), 'wb').write(ips)
open(os.path.join(SAL, 'softwaredb.xml'), 'w').write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE softwaredb SYSTEM "softwaredb1.dtd">
<softwaredb>
<software>
  <title>Taiyou no Shinden - Asteka II (traduccion al castellano)</title>
  <system>MSX</system>
  <company>Tokyo Shoseki</company>
  <year>1988</year>
  <country>ES</country>
  <dump><megarom><type>ASCII8SRAM8</type><hash>%s</hash></megarom></dump>
</software>
</softwaredb>
''' % sha)
print('ROM %d KB SHA1 %s, IPS %d bytes' % (len(rom)//1024, sha, len(ips)))
for w in AVISOS: print('AVISO:', w)
