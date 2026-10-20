# Encargo: avatar "GI Trades" para un grupo de Telegram

Rama: NO toques git. Trabaja solo dentro de data/avatares_telegram/.

Objetivo: adaptar el logo de Grupo Inteligencia (GI) a una version "GI Trades" para el avatar de un grupo de Telegram
privado de analistas donde se comparten operaciones (trades).

REGLAS DURAS
- PROHIBIDO usar modelos de difusion / generacion de imagenes. Todo es HTML + CSS (+ SVG inline) que yo rindo con Playwright.
- Usa los logos reales como <img>: logo_letrero.png (color, sobre blanco) y logo_blanco.png (blanco, transparente). No redibujes ni re-trazes el logo.
- Colores: degradado de marca #3C8CAA -> #50C0A8 (acento #50C0A8). Lee templates/stories/marca.css y usa sus variables (var(--rol)); no escribas hex a mano salvo que no exista el token.
- Lienzo cuadrado 512x512 px (Telegram lo recorta en circulo: el contenido importante debe caber en un circulo inscrito de ~440 px, centrado).
- Texto "GI TRADES" legible en miniatura (se vera a 40 px). Sin precios, sin promesas de rentabilidad, sin flechas verdes/rojas de "ganancia".
- Sin guion largo (—, –) en ningun texto.
- Tono sobrio e institucional.

ENTREGA
Escribe 2 variantes: avatar_a.html (fondo oscuro, logo blanco) y avatar_b.html (fondo claro, logo a color).
Cada HTML autocontenido (rutas relativas a esta carpeta, CSS inline), body de 512x512 sin margen.
Responde con un resumen de 5 lineas, nada mas.
