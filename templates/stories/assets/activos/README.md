# Imágenes de activo para las Stories

Cada activo aporta una imagen que la pieza usa a la derecha. Hay **dos modos** de montarla, y
la diferencia importa porque cambia por completo lo que hay que conseguir.

El nombre del archivo **es el `activo_slug`** de la pieza, sin excepción: `usdjpy` → `usdjpy.jpg` →
`body.activo-usdjpy`. Es lo que permite derivar imagen y color del mismo dato.

### En disco hoy

| Activo | Archivo | Motivo | Procedencia |
|---|---|---|---|
| Oro (XAUUSD) · GLD.US | `oro.jpg` | Lingotes en bóveda | Aprobada por el equipo; fija el estándar |
| Petróleo (WTI.spot) | `wti.jpg` | Barriles / refinería | Generada con IA |
| Plata (XAGUSD) | `plata.jpg` | Metal / lingotes plata | Generada con IA |
| Nasdaq 100 (US100.spot) · QQQ.US | `us100.jpg` | Rack de GPUs, luz fría | Generada con IA |
| Dólar/Peso (USDCLP) | `usdclp.jpg` | Textura de grabado, abstracta | Generada con IA |
| Bitcoin (BTCUSD) | `bitcoin.jpg` | Circuito ámbar | Generada con IA |
| MercadoLibre (#MELI) | `meli.jpg` | Sector / paquetería e-commerce | Generada con IA |
| Semiconductores (SOXX.US) | `tech-circuito.jpg` | Circuito, luz fría | Generada con IA |
| — (sin asignar) | `tech-baterias.jpg` | Genérica de sector | Generada con IA |
| S&P 500 (US500.spot) · SPY.US | `us500.jpg` | Fachada corporativa rascacielos Wall St | Generada con IA |
| Dow Jones (US30.spot) | `us30.jpg` | Columnata clásica Wall St / NYSE | Generada con IA |
| Russell 2000 (IWM.US) | `iwm.jpg` | Hub logístico automatizado / robótica | Generada con IA |
| Dólar/Yen (USDJPY) | `usdjpy.jpg` | Distrito financiero de Tokio de noche | Generada con IA |
| Euro/Dólar (EURUSD) | `eurusd.jpg` | Arquitectura angular Fráncfort / BCE | Generada con IA |
| Libra/Dólar (GBPUSD) | `gbpusd.jpg` | Columnas Banco de Inglaterra de noche | Generada con IA |
| Ethereum (ETHUSD) | `eth.jpg` | Prisma octaédrico cristal/grafeno índigo | Generada con IA |
| Solana (SOLUSD) | `sol.jpg` | Chip procesador cuántico cian/magenta | Generada con IA |
| Litecoin (LTCUSD) | `ltc.jpg` | Lingote titanio/plata criptográfico | Generada con IA |
| Cardano (ADAUSD) | `ada.jpg` | Red de nodos azul cobalto / topología | Generada con IA |
| Dogecoin (DOGUSD) | `doge.jpg` | Medallón de oro macizo sobre grafito | Generada con IA |

### Catálogo completo de imágenes

El universo completo de 20 activos para escaneo y renderizado de stories cuenta con su asset visual normalizado (1800×924 px, JPG calidad 88, recorte inferior de marca de agua aplicado).


---

## Modo A — Franja fotográfica (recomendado)

La foto ocupa la mitad derecha y se disuelve contra el negro con una máscara CSS. **No requiere
recorte, ni canal alfa, ni Photoshop.** Es el modo probado y el que da resultado más realista.

Clase: `.foto-activo` · Payload: `"activo_imagen": "assets/activos/oro.jpg"`

> **Sin `../` al principio.** La ruta se resuelve contra la carpeta de la plantilla, porque el HTML
> resuelto se escribe a un archivo temporal *dentro* de `templates/stories/` justamente para que los
> assets relativos resuelvan. Un `../` sale de esa carpeta y no encuentra nada. Antes eso rendía la
> pieza sin foto y sin error; desde el fail-fast de `story_render.py` detiene el render con un
> mensaje que nombra la ruta esperada.

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
| `meli.jpg` | Mercado Libre (#MELI) | Generada con IA (Gemini), 6 ago 2026 | Propia |
| `bitcoin.jpg` | Bitcoin (BTCUSD) | Generada con IA (Gemini), 9 ago 2026 | Propia |
| `us500.jpg` | S&P 500 (US500.spot) · SPY.US | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `us30.jpg` | Dow Jones (US30.spot) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `iwm.jpg` | Russell 2000 (IWM.US) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `usdjpy.jpg` | Dólar/Yen (USDJPY) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `eurusd.jpg` | Euro/Dólar (EURUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `gbpusd.jpg` | Libra/Dólar (GBPUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `eth.jpg` | Ethereum (ETHUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `sol.jpg` | Solana (SOLUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `ltc.jpg` | Litecoin (LTCUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `ada.jpg` | Cardano (ADAUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |
| `doge.jpg` | Dogecoin (DOGUSD) | Generada con IA (Gemini), 25 ago 2026 | Propia |

> **Nota de recorte para `bitcoin.jpg`.** El 8 % inferior del estándar no alcanzó:
> Gemini estampó su marca de agua más arriba de lo habitual, a un 15,9 % del borde.
> Se recortó el **17 %** y se verificó por píxel que no quedara rastro. Si otra
> imagen llega con la marca en otra posición, medirla antes de recortar en vez de
> aplicar el 8 % a ciegas.
>
> Es además la segunda imagen de Bitcoin: la primera se descartó por venir sin
> procedencia declarada, y porque era una moneda — motivo equivocado para este
> activo (ver el prompt en `docs/design/stories-gi/imagenes-por-activo.md`).

Todas normalizadas a 1800 px de ancho, JPG calidad 88. **Se les recortó el 8% inferior**: el
generador estampa su marca de agua abajo a la derecha y no puede viajar en una pieza de marca.
Los prompts que las produjeron están en `docs/design/stories-gi/imagenes-por-activo.md`.
