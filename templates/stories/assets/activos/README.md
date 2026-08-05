# Imágenes de activo para las Stories

Cada activo aporta una imagen que la pieza usa a la derecha. Hay **dos modos** de montarla, y
la diferencia importa porque cambia por completo lo que hay que conseguir.

| Activo | Archivo | Motivo |
|---|---|---|
| Oro (XAUUSD) | `oro.*` | Lingotes |
| Petróleo (WTI.spot) | `wti.*` | Barriles / refinería |
| Nasdaq 100 (US100.spot) | `us100.*` | Motivo tecnológico |
| Dólar/Peso (USDCLP) | `usdclp.*` | Banderas de EE.UU. y Chile |

---

## Modo A — Franja fotográfica (recomendado)

La foto ocupa la mitad derecha y se disuelve contra el negro con una máscara CSS. **No requiere
recorte, ni canal alfa, ni Photoshop.** Es el modo probado y el que da resultado más realista.

Clase: `.foto-activo` · Payload: `"activo_imagen": "../assets/activos/oro.jpg"`

**Qué se necesita**
- JPG o PNG, horizontal, ancho ≥ 1600 px.
- Foto oscura o de tonos medios. Las fotos claras o sobre fondo blanco no funden con el negro
  y dejan un bloque luminoso pegado al costado.
- El motivo hacia el centro-derecha del encuadre. El tercio izquierdo se disuelve bajo el texto,
  así que lo que caiga ahí no se va a ver.
- Sin texto, logos ni marcas de agua.
- Nada de personas ni manos: fechan la imagen y compiten con el mensaje.

**Dónde conseguirlas, en orden de conveniencia**

1. **Unsplash** y **Pexels** — licencia propia que permite uso comercial **sin atribución**. Es la
   vía más limpia y gratis. Buscar "gold bars", "oil barrels", "stock market", "flags".
2. **Canva Pro**, si GI ya lo tiene — biblioteca con licencia incluida y descarga directa.
3. **Adobe Stock / Shutterstock** — de pago, pero es donde está la mejor calidad y la licencia
   es inequívoca.
4. **Wikimedia Commons** — gratis pero con trampa: casi todo el material bueno está en CC BY-SA,
   que obliga a atribuir **y** a licenciar la pieza derivada bajo la misma licencia. Para una
   pieza de marca eso es inaceptable. Solo sirve lo marcado *Public domain* o *CC0*, y ahí la
   oferta es pobre.

Pasar la URL de la foto elegida basta: se descarga, se deja en esta carpeta y se apunta el
payload.

---

## Modo B — Objeto recortado

Un objeto con fondo transparente flotando sobre la pieza. Se ve más "producto", pero exige
recorte y por eso no es el modo por defecto.

Clase: `.ilustracion` (o `.ilustracion--foto` si es fotografía)

- PNG-24 con alfa, lado mayor ≥ 1200 px, fondo 100% transparente.
- **Defringe obligatorio**: el halo blanco de recorte es invisible sobre el lienzo blanco de un
  editor y se ve clarísimo sobre el negro de la pieza.
- Luz principal desde **arriba a la izquierda**, que es donde la pieza tiene su foco de color.
  Una foto iluminada desde la derecha se lee como pegada de otra escena.
- Sin sombra proyectada quemada: la sombra y el halo los pone el CSS y se tiñen del color del
  activo.

**Si no hay Photoshop**: el recorte se puede hacer con `rembg` (modelo local, gratis, sin subir
la imagen a ningún servicio) o con la función "quitar fondo" de Canva. No hace falta un editor
profesional.

---

## Licencia

Solo material propio o de banco con licencia comercial acreditable. Estas piezas se publican a
clientes: el origen de cada imagen tiene que poder demostrarse. Anotar la procedencia de cada
archivo acá abajo cuando se agregue.

| Archivo | Activo | Fuente | Licencia |
|---|---|---|---|
| `oro.jpg` | Oro (XAUUSD) | Generada con IA (Gemini), 4 ago 2026 | Propia |
| `wti.jpg` | Petróleo (WTI.spot) | Generada con IA (Gemini), 4 ago 2026 | Propia |
| `us100.jpg` | Nasdaq 100 (US100.spot) | Generada con IA (Gemini), 4 ago 2026 | Propia |
| `usdclp.jpg` | Dólar/Peso (USDCLP) | Generada con IA (Gemini), 4 ago 2026 | Propia |
| `plata.jpg` | Plata (XAGUSD) | Generada con IA (Gemini), 4 ago 2026 | Propia |
| `tech-circuito.jpg` | Acciones tecnológicas | Generada con IA (Gemini), 4 ago 2026 | Propia |
| `tech-baterias.jpg` | Acciones de movilidad/energía | Generada con IA (Gemini), 4 ago 2026 | Propia |

Todas normalizadas a 1800 px de ancho, JPG calidad 88. **Se les recortó el 8% inferior**: el
generador estampa su marca de agua abajo a la derecha y no puede viajar en una pieza de marca.
Los prompts que las produjeron están en `docs/design/stories-gi/imagenes-por-activo.md`.
