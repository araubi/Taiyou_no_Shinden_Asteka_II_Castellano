; Variables del motor de texto (zona FNKSTR de la BIOS, libre en un juego en ROM)
V_MODO   equ 0F87Fh   ; 0 cadena, 1 rango, 2 lenta, 3 lenta2
V_ANCHO  equ 0F880h   ; A original (glifos japoneses por linea)
V_NOENC  equ 0F881h   ; 1 = texto sin traducir (se pinta el original)
V_X0     equ 0F882h   ; x de inicio de linea (bytes, 2 pixeles por byte)
V_X      equ 0F883h
V_Y      equ 0F884h
V_XMAX   equ 0F885h
V_PAG    equ 0F886h   ; pagina (16 KB) del texto
V_PTR    equ 0F887h   ; 2 bytes, puntero del final
V_LENTA  equ 0F889h
V_PREV   equ 0F88Ah   ; caracter anterior (para saber si empieza palabra)
V_YMAX   equ 0F88Bh
V_GUARDA equ 0F88Ch   ; pagina guardada

; Rutinas del juego (banco fijo)
PON_PAGINA   equ 5E6Bh
VRAM_ESCRIBE equ 641Fh   ; D=y, E=x (bytes); deja DI
ESPERA_A     equ 4545h
ESPERA_LARGA equ 4EBAh
LEE_MANDOS   equ 5F5Dh
SONIDO       equ 5EC7h
BORRA_RECT   equ 6556h   ; HL = x,y  DE = ancho,alto
PUERTO_VDP   equ 0E800h

PAG_MOTOR equ 17          ; bancos 34 (textos) y 35 (motor)
MOTOR     equ 0A000h

PAG_TITULO equ 21         ; titulo en castellano (bancos 42-43)
TITULO     equ 8000h
PAG_ACTUAL equ 0E7FFh
