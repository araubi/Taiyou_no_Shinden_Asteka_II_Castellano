; Enganches en el banco fijo (hueco libre 7E8Eh-7FFFh del banco 1)
	include "comun.inc"
	org 7E8Eh

; --- PON_PAGINA: la S-RAM se activa con el bit 40h en una ROM de 512 KB ---
SRAM_EI:
	ld a,40h
	ld (7000h),a
	ei
	ret
SRAM_DI:
	ld a,40h
	ld (7000h),a
	ret

; --- Rutinas de texto ---
H_CADENA:
	ld (V_ANCHO),a
	xor a
	jr H_COMUN
H_RANGO:
	ld (V_ANCHO),a
	ld a,1
	jr H_COMUN
H_LENTA:
	ld (V_ANCHO),a
	ld a,2
	jr H_COMUN
H_LENTA2:
	ld (V_ANCHO),a
	ld a,3
H_COMUN:
	ld (V_MODO),a
	push bc
	push hl
	push de
	ld a,PAG_MOTOR
	call PON_PAGINA
	call MOTOR
	pop de
	pop hl
	pop bc
	push af                 ; CY = cortado con ESPACIO
	ld a,4
	call PON_PAGINA
	ld a,(V_NOENC)
	or a
	jr nz,ORIGINAL
	ld a,(V_MODO)
	cp 1
	jr nz,PASA_FF
	ld h,b
	ld l,c
	pop af
	ret
PASA_FF:
	ld a,(hl)
	inc hl
	inc a
	jr nz,PASA_FF
	pop af
	ret
ORIGINAL:
	pop af
	push hl
	ld a,(V_MODO)
	add a,a
	ld hl,TABLA_ORIG
	add a,l
	ld l,a
	jr nc,$+3
	inc h
	ld a,(hl)
	inc hl
	ld h,(hl)
	ld l,a
	ex (sp),hl
	ld a,(V_ANCHO)
	ld (0E9E1h),a
	ret
TABLA_ORIG:
	dw 4D26h,4CBBh,4D91h,4ED0h

; --- Final ---
H_PREPFIN:
	push hl
	push bc
	ld a,(0E7FFh)
	ld (V_GUARDA),a
	ld a,PAG_MOTOR
	call PON_PAGINA
	call MOTOR+3
	ld a,(V_GUARDA)
	call PON_PAGINA
	pop bc
	pop hl
	ld de,0B347h
	ret
H_UNGLIFO:
	ld a,(0E9E2h)
	or a
	ret nz
	push hl
	push bc
	push de
	ld a,PAG_MOTOR
	call PON_PAGINA
	call MOTOR+6
	ld a,4
	call PON_PAGINA
	pop de
	pop bc
	pop hl
	ret
FIN_STUBS:

; --- Pantalla de titulo: en lugar de pintar los kanji (call 6928h en 58A7h) pinta "El Templo del Sol" ---
H_TITULO:
	ld a,(PAG_ACTUAL)
	push af
	ld a,PAG_TITULO
	call PON_PAGINA
	call TITULO
	pop af
	jp PON_PAGINA
; --- "ASTEKAII" (call 6928h en 58B5h): ya lo pinta H_TITULO como "AZTECA II"; solo deja la pagina 6 como la rutina original ---
H_ASTEKA:
	ld a,6
	jp PON_PAGINA
