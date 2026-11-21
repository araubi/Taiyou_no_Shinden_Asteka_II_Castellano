; Titulo en castellano: copia un rectangulo de 224 bytes x 56 filas (SCREEN 7) a la pagina 0 de la VRAM.
	include "comun.inc"
	org TITULO
	ld a,(PUERTO_VDP)
	ld c,a
	ld hl,DATOS
	ld d,24                 ; primera fila
T_FILA:
	ld e,16                 ; primer byte (x = 32)
	call VRAM_ESCRIBE
	ld b,224
T_BYTE:
	outi                    ; outi + jp nz: ritmo seguro para el V9938
	jp nz,T_BYTE
	ei
	inc d
	ld a,d
	cp 96
	jr nz,T_FILA
	ret
DATOS:
	incbin "titulo.bin"
