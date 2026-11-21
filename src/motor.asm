; Motor de texto en castellano para Taiyou no Shinden - Asteka II
; Va en A000h (banco impar de cada pagina 17..31); los textos van en 8000h (banco par).
; Fuente de 6x8 pixeles: SCREEN0 de theNestruo/msxbios-tools.
	include "comun.inc"
	org MOTOR

	jp M_TEXTO
	jp M_PREPFIN
	jp M_UNGLIFO

;----------------------------------------------------------------------------
; HL = direccion del texto japones (clave), DE = x,y, V_ANCHO, V_MODO.
; Devuelve CY=1 si se corto con ESPACIO (modo lento). V_NOENC=1 si no hay traduccion.
;----------------------------------------------------------------------------
M_TEXTO:
	xor a
	ld (V_NOENC),a
	push de
	call BUSCA
	pop de
	jr nc,MT_SI
	ld a,1
	ld (V_NOENC),a
	or a
	ret
MT_SI:
	ld (V_PAG),a
	push hl
	call PON_PAGINA
	pop hl
	ld a,d
	inc a                   ; margen de 2 pixeles a la izquierda
	ld (V_X0),a
	ld (V_X),a
	ld a,(V_ANCHO)
	add a,a
	add a,a
	add a,a
	add a,d
	ld (V_XMAX),a
	ld a,0FFh
	ld (V_YMAX),a
	ld b,2
	ld a,(V_ANCHO)
	cp 18h
	jr z,MT_Y
	; una sola linea: centrada en la fila de 16 pixeles
	push hl
	ld c,0
MT_MIDE:
	ld a,(hl)
	inc hl
	or a
	jr z,MT_MIDIO
	cp 09h
	jr z,MT_MIDE           ; tabulador: se centra igual
	cp 20h
	jr c,MT_LARGA          ; salto de linea: no centrar
	ld a,c
	add a,3
	jr c,MT_LARGA
	ld c,a
	jr MT_MIDE
MT_MIDIO:
	ld a,(V_ANCHO)
	add a,a
	add a,a
	add a,a
	cp c
	jr c,MT_LARGA
	ld b,4
MT_LARGA:
	pop hl
MT_Y:
	ld a,e
	add a,b
	ld (V_Y),a
	ld a,(V_MODO)
	and 2
	ld (V_LENTA),a
	xor a
	ld (V_PREV),a
	; sigue en IMPRIME

;----------------------------------------------------------------------------
; Pinta el texto de HL (acaba en 00h). 09h = tabulador (16 bytes), 0Ah = salto de linea.
; Corta las lineas por palabras. CY=1 si se pulsa ESPACIO en modo lento.
;----------------------------------------------------------------------------
IMPRIME:
	ld a,(hl)
	or a
	ret z
	ld a,(V_LENTA)
	or a
	jr z,IM_1
	push hl
	call LEE_MANDOS
	pop hl
	cp 20h
	scf
	ret z
IM_1:
	ld a,(hl)
	inc hl
	cp 0Ah
	jr nz,IM_2
	call NUEVA_LINEA
	ld a,20h
	ld (V_PREV),a
	jp IMPRIME
IM_2:
	cp 09h
	jr nz,IM_3
	ld a,(V_X0)
	dec a                   ; los huecos de los menus se cuentan sin el margen
	ld b,a
	ld a,(V_X)
	sub b
	and 0F0h
	add a,10h
	add a,b
	ld (V_X),a
	ld a,20h
	ld (V_PREV),a
	jp IMPRIME
IM_3:
	cp 20h
	jr nz,IM_4
	ld (V_PREV),a
	ld a,(V_X0)
	ld b,a
	ld a,(V_X)
	cp b
	jp z,IMPRIME            ; sin espacios al principio de linea
	add a,3
	ld (V_X),a
	jp IMPRIME
IM_4:
	ld c,a
	ld a,(V_PREV)
	cp 21h
	ld a,c
	ld (V_PREV),a
	jr nc,IM_5              ; dentro de una palabra
	; principio de palabra: cabe?
	dec hl
	call MIDE_PALABRA       ; B = ancho en bytes
	inc hl
	ld a,(V_X)
	add a,b
	jr c,IM_SALTO
	ld b,a
	ld a,(V_XMAX)
	cp b
	jr nc,IM_5
IM_SALTO:
	ld a,(V_X0)
	ld b,a
	ld a,(V_X)
	cp b
	call nz,NUEVA_LINEA
IM_5:
	; letra suelta que no cabe (palabra mas larga que la linea)
	ld a,(V_X)
	add a,3
	ld b,a
	ld a,(V_XMAX)
	cp b
	call c,NUEVA_LINEA
	ld a,c
	push hl
	call PINTA_CAR
	pop hl
	ld a,(V_LENTA)
	or a
	jp z,IMPRIME
	push hl
	ld hl,0B9E9h
	call SONIDO
	ld hl,0C00h
IM_ESP:
	dec hl
	ld a,h
	or l
	jr nz,IM_ESP
	pop hl
	jp IMPRIME

NUEVA_LINEA:
	ld a,(V_X0)
	ld (V_X),a
	ld a,(V_Y)
	add a,10
	ld (V_Y),a
	ret

; HL = principio de la palabra -> B = ancho en bytes (3 por letra), conserva HL
MIDE_PALABRA:
	push hl
	ld b,0
MP_1:
	ld a,(hl)
	inc hl
	cp 21h
	jr c,MP_2
	ld a,b
	add a,3
	ld b,a
	jr nc,MP_1
	ld b,0FFh
MP_2:
	pop hl
	ret

;----------------------------------------------------------------------------
; Pinta el caracter A en (V_X,V_Y) y avanza V_X 3 bytes (6 pixeles).
; Pixel encendido = color 0Bh, apagado = 0 (como los glifos originales).
;----------------------------------------------------------------------------
PINTA_CAR:
	sub 20h
	ld l,a
	ld h,0
	add hl,hl
	add hl,hl
	add hl,hl
	ld de,FUENTE
	add hl,de
	ld a,(V_Y)
	ld d,a
	ld a,(V_X)
	ld e,a
	add a,3
	ld (V_X),a
	ld a,(PUERTO_VDP)
	ld c,a
	ld b,8
PC_FILA:
	call VRAM_ESCRIBE
	ld a,(hl)
	inc hl
	call PC_PAR
	call PC_PAR
	call PC_PAR
	ei
	inc d
	djnz PC_FILA
	ret
PC_PAR:
	rlca
	rlca
	push af
	and 3
	push hl
	ld hl,PARES
	add a,l
	ld l,a
	jr nc,$+3
	inc h
	ld a,(hl)
	out (c),a
	pop hl
	pop af
	ret
PARES:
	db 00h,0Bh,0B0h,0BBh

;----------------------------------------------------------------------------
; BUSCA: HL = clave (direccion japonesa) -> A = pagina, HL = texto; CY=1 si no esta.
;----------------------------------------------------------------------------
BUSCA:
	ex de,hl
	ld hl,TABLA
BU_1:
	ld c,(hl)
	inc hl
	ld b,(hl)
	inc hl
	ld a,b
	or c
	scf
	ret z
	ld a,c
	cp e
	jr nz,BU_2
	ld a,b
	cp d
	jr nz,BU_2
	ld a,(hl)
	inc hl
	ld c,(hl)
	inc hl
	ld h,(hl)
	ld l,c
	or a
	ret
BU_2:
	inc hl
	inc hl
	inc hl
	jr BU_1

;----------------------------------------------------------------------------
; Final: el texto sale palabra a palabra, una por llamada (la llama el bucle del desplazamiento).
; 0Ch = pagina nueva (espera y borra la ventana).
;----------------------------------------------------------------------------
M_PREPFIN:
	ld hl,0B347h
	call BUSCA
	jr nc,PF_1
	ld a,1
	ld (0E9E2h),a
	ret
PF_1:
	ld (V_PAG),a
	ld (V_PTR),hl
	ld a,20h
	ld (V_X0),a
	ld (V_X),a
	ld (0E9E3h),a
	ld a,0E0h
	ld (V_XMAX),a
	ld a,9Dh
	ld (V_Y),a
	ld a,9Ch
	ld (0E9E1h),a
	xor a
	ld (0E9E2h),a
	ld (V_LENTA),a
	ret

M_UNGLIFO:
	ld a,(V_PAG)
	call PON_PAGINA
	ld hl,(V_PTR)
UG_1:
	ld a,(hl)
	or a
	jr z,UG_FIN
	cp 20h
	jr nz,UG_2
	inc hl
	ld a,(V_X0)
	ld b,a
	ld a,(V_X)
	cp b
	jr z,UG_1
	add a,3
	ld (V_X),a
	jr UG_1
UG_2:
	cp 0Ch
	jr nz,UG_3
	inc hl
	ld (V_PTR),hl
	jp PAGINA_FIN
UG_3:
	cp 0Ah
	jr nz,UG_4
	inc hl
	ld (V_PTR),hl
	jr UG_NL
UG_4:
	call MIDE_PALABRA
	ld a,(V_X)
	add a,b
	jr c,UG_5
	ld b,a
	ld a,(V_XMAX)
	cp b
	jr nc,UG_6
UG_5:
	push hl
	call UG_NL
	pop hl
UG_6:
	ld a,(hl)
	cp 21h
	jr c,UG_7
	inc hl
	push hl
	call PINTA_CAR
	pop hl
	jr UG_6
UG_7:
	ld (V_PTR),hl
	ret
UG_FIN:
	ld a,1
	ld (0E9E2h),a
	ret
UG_NL:
	call NUEVA_LINEA
	ld a,(V_Y)
	cp 9Dh+30
	ret c
PAGINA_FIN:
	call ESPERA_LARGA
	call ESPERA_LARGA
	call ESPERA_LARGA
	call ESPERA_LARGA
	ld hl,209Ch
	ld de,0C020h
	call BORRA_RECT
	ld a,(V_X0)
	ld (V_X),a
	ld a,9Dh
	ld (V_Y),a
	ld a,(V_PAG)
	jp PON_PAGINA

FUENTE:
	incbin "fuente.bin"
TABLA:
	incbin "tabla.bin"
	dw 0
FIN_MOTOR:
