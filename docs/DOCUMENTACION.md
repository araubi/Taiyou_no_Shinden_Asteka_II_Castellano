# Documentación técnica de la traducción

Cómo está hecho el juego original por dentro y qué cambia la traducción. Las direcciones son de la CPU (Z80) salvo que se diga «ROM».

## 1. El cartucho

* ROM de 256 KB con mapper **ASCII8** y 8 KB de **S-RAM** para guardar partidas (en openMSX, `ASCII8SRAM8`).
* La parte 4000h-7FFFh (bancos 0 y 1) queda fija. En 8000h-BFFFh se ponen **páginas de 16 KB** (dos bancos seguidos) con `PON_PAGINA` (5E6Bh), que recibe la página en A y la anota en E7FFh. La página 16 es la S-RAM.
* La pantalla es **SCREEN 7** (512×212, 16 colores, 2 píxeles por byte).

| Bancos | Página | Contenido |
|---|---|---|
| 0-1 | fija | Código principal: arranque, textos, mapa, menús, guardar, VDP. Hueco libre en 7E8Eh-7FFFh. |
| 2-3 | 1 | Datos, música (reproductor PSG en 76DFh, llamado desde la interrupción) y la letra de los créditos. |
| 4-7 | 2-3 | Gráficos y datos. |
| 8-9 | 4 | **Textos**: tabla de mensajes, mensajes y cadenas. |
| 10-31 | 5-15 | Letra japonesa, dibujos de los lugares (comprimidos) y más datos. |

## 2. Los textos del original

* Letra propia de **16×16** a 1 bit por punto (545 glifos), que se copia a la VRAM en 1A000h. No tiene todas las letras latinas: el menú «ＬＯＡＤ» se escribe con un círculo en lugar de la O.
* Codificación de un byte por glifo, con prefijos FDh y FEh para los glifos altos y FFh como fin de cadena.
* **Mensajes**: tabla de 456 entradas en 8000h (número de mensaje en BCD y puntero). No llevan terminador: acaban donde empieza el siguiente. Se pintan con `IMPRIME_RANGO` (4CB8h) en la ventana de abajo, **2 líneas de 24 glifos**.
* **Cadenas** acabadas en FFh (AE9Bh-B3F5h): menús, lugares, objetos, las 73 cosas que se pueden señalar, la presentación y el final. Se pintan con `IMPRIME_CADENA` (4D23h) o letra a letra con `IMPRIME_CADENA_LENTA` (4D8Eh y 4ECDh). El final sale glifo a glifo con `IMPRIME_UN_GLIFO` (4E27h), al ritmo del desplazamiento de la imagen.

## 3. Cómo está hecha la traducción

### 3.1 ROM de 512 KB

La ROM pasa de 256 a 512 KB. Todo lo nuevo va en los bancos añadidos y en la parte original solo se tocan unos pocos bytes:

| Página | Uso |
|---|---|
| 17-20 | Banco par: textos en castellano. Banco impar: el motor de texto con la letra y la tabla de textos (el motor se repite en cada página para que siempre esté a mano). |
| 21 | El rótulo del título. |

Con 512 KB la S-RAM ya no se activa con el bit 20h del número de banco, sino con el **40h**. Se corrige en `PON_PAGINA` (5E7Eh y 5EE9h).

### 3.2 Enganches

En el código fijo se cambian instrucciones de 3 bytes por saltos a los enganches (`src/stubs.asm`, en el hueco libre de 7E8Eh). Cada enganche pone la página del motor, llama al motor y vuelve a dejar la página que había:

| Dirección | Original | Para qué |
|---|---|---|
| 4CB8h | `IMPRIME_RANGO` | Mensajes. |
| 4D23h | `IMPRIME_CADENA` | Cadenas. |
| 4D8Eh, 4ECDh | Cadenas lentas | Presentación y textos letra a letra. |
| 4E15h, 4E27h | Final | Prepara el texto del final y lo pinta palabra a palabra. |
| 5E7Eh, 5EE9h | `PON_PAGINA` | S-RAM con el bit 40h. |
| 58A7h, 58B5h | Título | Pinta «El Templo del Sol» y «AZTECAII». |
| 540Dh | Menú de direcciones | Resaltado de 20 píxeles en lugar de 16. |

Cada texto en castellano se busca por la **dirección del texto japonés** al que sustituye (la clave de `textos/traduccion.txt`). Si algún texto no estuviera traducido, el motor pintaría el original.

### 3.3 El motor de texto

* Letra **SCREEN0 de 6×8** (3 bytes de SCREEN 7 por letra): **3 líneas de 64 caracteres** en la ventana de mensajes, en lugar de 2 de 24.
* Corte de líneas por palabras, tildes, ñ, ü, ¿, ¡ y comillas « ».
* Variables en la zona de las teclas de función de la BIOS (FNKSTR, F87Fh), que el juego no usa.
* `build.py` simula el corte de líneas y avisa si algún texto no cabe en su sitio: ventana (3 líneas), recuadros de lugar y objeto (32 caracteres), menús (48), presentación y final.

### 3.4 Título y créditos

* El rótulo japonés (太陽の神殿) es un dibujo de 1 bit que se pinta en rojo con la rutina 6928h. La traducción pinta en su lugar un rectángulo de SCREEN 7 (filas 24-95) con «El Templo del Sol» en letra de pincel y «AZTECAII». `titulo/hace_titulo.py` lo genera.
* Los créditos del final ya venían en letras latinas, con una letra de 12×12 (en 79F8h de la página 1, 18 bytes por letra) y una tabla de letras en 7BB2h. Se cambia «calacol» por «caracol» y «(asteka II)» por «(azteca II)». La letra no tenía z, así que se dibuja en el sitio de la k, que solo se usaba en esa palabra.

## 4. El guion

El juego funciona con un guion interno que se recorre en cada orden:

| Código | Significado |
|---|---|
| 01 | Mensaje. |
| 02 | Cambio de escena. |
| 03 | Si la marca está puesta... |
| 04 / 05 | Pone / quita una marca. |
| 0A | Muerte. |
| 0B | Final. |

* Las marcas y el estado de la partida están en E500h-E6FFh (512 bytes, que es lo que se guarda en la S-RAM, con dos sumas de control al final).
* La **hora** está en E6E5h y va de 0 a 119 en cuatro fases. Con el pectoral lavado, la gema hace de reloj solar: roja, negra, amarilla y blanca. Algunos sucesos solo pasan en una fase (ver la [guía](GUIA_ASTEKA2.md)).
* El mapa es de 6×6 pantallas. La fila y la columna actuales están en E6E0h y E6E1h, y `sub_60E4` repinta la pantalla.

## 5. Curiosidades

* **«CALACOL»:** los créditos del original escriben así El Caracol, confundiendo la l y la r.
* **Anacronismos:** entre los objetos hay una tirita (la marca Band-Aid) y un mechero.
* **Maya, no azteca:** todos los lugares (El Caracol, Las Monjas, El Castillo, el Cenote Sagrado...) son de Chichén Itzá, que es una ciudad maya, aunque la serie se llame «Azteca».
* **Esperas por CPU:** las pausas son bucles de CPU, no esperas por cuadros. En un turbo R con R800 el texto lento va mucho más deprisa.
* **Música:** de Takahito Abe (Falcom). La canción del final se llama «See you again», como la del final del primer *Ys*.

## 6. Pruebas

Todo se probó en openMSX con un Sony HB-F900: detección del mapper, presentación, todos los lugares, objetos, menús, guardar y cargar (también tras reiniciar), la pantalla de reinicio, el final y los créditos. La partida se jugó entera solo con el teclado siguiendo la guía.
