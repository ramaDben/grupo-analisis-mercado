# Piel compartida de Stories GI — `oportunidad` como estándar visual

**Fecha**: 2026-08-07
**Estado**: diseño aprobado, pendiente de implementación
**Origen**: decisión del director — fijar la plantilla `oportunidad` como estándar
para `alerta` y `recomendacion`.
**Antecedente**: `docs/superpowers/specs/2026-08-04-rediseno-stories-gi-design.md`
(rediseño que produjo `oportunidad`).

---

## 1. El problema

`oportunidad` nació del feedback del equipo: las piezas eran "todas iguales",
"planas", "no calientan a nadie". El rediseño resolvió eso para una plantilla —
escenario a sangre, color e imagen por activo, sello con pulso, tipografía de
titulares en Space Grotesk— y dejó a las otras diez con la línea anterior.

El resultado es peor que el punto de partida: ahora conviven **dos líneas
visuales** en el mismo canal. Un cliente que recibe una `oportunidad` el martes y
una `alerta` el miércoles no las lee como piezas de la misma casa.

## 2. La distinción que sostiene todo el diseño

`oportunidad` aporta dos cosas separables, y confundirlas es el error que esta
spec existe para evitar:

- **La piel** — cómo se ve la pieza: capas de fondo, color por activo, sello,
  tipografía, CTA, footer. Es lenguaje de marca y es trasladable sin costo
  editorial.
- **La estructura** — qué bloques tiene y en qué orden: hero con dos precios
  gigantes, tarjeta de evidencia del dato macro, ausencia deliberada de campos de
  operación. Esto responde a *un activo con un dato macro que lo origina*, y no
  es trasladable.

**Se estandariza la piel. La estructura de cada pieza la sigue mandando su
contenido.**

### Por qué no se estandariza la estructura

`recomendacion` obliga a mostrar entrada, TP y SL en pesos, volumen,
temporalidad, costo de mantención y firma acreditada. Con el hero de dos precios
de `oportunidad`, esos campos no caben o bajan a letra chica — y son exactamente
los que hacen que la pieza sea responsable en lugar de solo atractiva.

Hay además un límite editorial vigente que un layout común borraría: `oportunidad`
**invita a operar** y `recomendacion` **recomienda una operación**. La segunda
lleva firma acreditada y cuenta para el límite de 3 señales por semana; la primera
no. Hoy esa diferencia está protegida por un test que prohíbe los campos de señal
en `oportunidad`. Si las dos piezas se ven idénticas, el cliente deja de
distinguirlas aunque el código sí lo haga — y la protección se vuelve nominal.

## 3. Decisiones

### D1 · El gráfico sigue siendo tarjeta legible en `alerta` y `recomendacion`

En `oportunidad` el gráfico es **escenario**: se estira (`"ajuste": "llenar"`), se
le ocultan precios y rótulos, y solo queda la curva como atmósfera. Funciona
porque el precio ya está en 96 px en el bloque de cifras y repetirlo dentro del
SVG sería ruido.

En las otras dos el gráfico **es contenido**. En `recomendacion`, las tres líneas
—entrada, objetivo, stop— son donde se lee la relación riesgo/beneficio sin hacer
la división; a sangre y sin rótulos, esa lectura desaparece. En `alerta`, los
niveles punteados de soporte y resistencia son el dato que el cliente busca.

Conservan su contenedor, sus niveles y sus precios rotulados. Lo que sí cambia es
el color: la curva pasa a `var(--activo)` en lugar de `var(--acento)`, para que la
pieza se reconozca por su activo.

### D2 · La imagen del activo entra como fondo tenue a sangre

`oportunidad` puede darle a la imagen el 58 % del ancho porque su hero solo ocupa
el 62 % izquierdo. `alerta` y `recomendacion` son de dos columnas llenas —
editorial a la izquierda, gráfico a la derecha — y no tienen hueco libre.

La imagen va **detrás de todo el lienzo**, más apagada que en `oportunidad` y con
el velo encima. Aporta reconocimiento del activo sin disputar espacio a ningún
bloque.

**Subordinación explícita**: si el fondo compromete la legibilidad de un bloque,
gana el bloque. En `recomendacion` esto aplica en particular a la firma
acreditada, que no se mueve, no se achica y no compite con el fondo.

### D3 · La piel vive en un archivo, no en tres copias

Sale a `templates/stories/piel.css`, hermano de `marca.css`, y las tres plantillas
lo enlazan con `<link rel="stylesheet" href="piel.css">`.

Funciona por el mismo mecanismo que `marca.css` y que `fonts/`: `story_render.py`
escribe el HTML resuelto **dentro** de `templates/stories/` y lo navega con
`file://`, así que las rutas relativas resuelven. El renderer no se entera — cero
cambios en su contrato de tokens.

La alternativa de copiar el bloque a cada plantilla se descartó por la misma
razón que existe `marca.css`: cuando algo vive en tres copias, la tercera se queda
atrás y nadie lo nota hasta que sale una pieza descoordinada. La alternativa de
herencia de plantillas se descartó porque el renderer no tiene ese mecanismo y
agregarlo es un proyecto aparte.

**Orden de carga**: `marca.css` → `piel.css` → `<style>` de la plantilla. Cada
capa puede anular la anterior, y una plantilla siempre puede excepcionar.

### D4 · Reparto entre la hoja y las plantillas

| Entra a `piel.css` | Se queda en cada plantilla |
|---|---|
| `.foto-activo`, `.velo`, `.grilla` | Layout de columnas y bloques |
| `@font-face` de Space Grotesk y DM Sans | Tamaños tipográficos de cada bloque |
| `.sello` + `.pulso` | El texto del sello |
| `.cta` y sus partes | Si la pieza lleva CTA |
| Footer de marca y disclaimer | El texto del disclaimer |

`oportunidad.html` también adelgaza: pierde esas reglas y pasa a consumir la hoja.
Queda como las otras dos, no como la excepción — si la plantilla que definió el
estándar no lo consume, la hoja se desincroniza de ella al primer ajuste.

**La piel no toca ningún color de dirección, ningún nivel y ninguna cifra.** Sigue
vigente la regla del repo: si un color no está comunicando un número, va en el
acento; si lo está, va en `--sube`/`--baja`. Y `--activo` es identidad, nunca
dirección — colapsarlos haría que una pieza dorada bajista se leyera como alcista
dorada.

### D5 · Tipografía

Los titulares de `alerta` y `recomendacion` pasan de DM Sans 700 a Space Grotesk
800, igualando a `oportunidad`. DM Sans se conserva para párrafos.

El `@font-face` de Syne se elimina de ambas: está declarado pero **ninguna regla
lo usa** — las dos plantillas ya escriben todo en DM Sans y Space Grotesk. Es
peso muerto, no un cambio de criterio. (Syne sigue en `fonts/` porque otras ocho
plantillas la declaran; su retiro completo es trabajo aparte.)

## 4. Contrato de payload

Dos campos nuevos en los payloads de `alerta` y `recomendacion`:

| Campo | Qué hace | Ausente / vacío |
|---|---|---|
| `activo_slug` | Fija el color vía `body.activo-<slug>` (`oro`, `wti`, `us100`, `usdclp`) | Cae al acento de marca — comportamiento ya definido en `marca.css` |
| `activo_imagen` | Ruta a la foto de fondo (`assets/activos/<slug>.jpg`) | La pieza queda sin foto, solo con color |

Ambos **degradan sin romper**: una pieza que no los traiga se ve como hoy pero con
la piel nueva. Esto es deliberado — no todos los activos tienen imagen ni color
asignado, y la pieza tiene que salir igual.

La clave debe venir siempre en el payload aunque sea vacía: la guardia de
huérfanos de `build_html` aborta el render si falta, que es la convención del
repo para campos opcionales (token + CSS `:empty`).

Hay que actualizar en consecuencia: las fixtures de
`tests/fixtures/stories/payloads/`, el comando `/alerta` y la sección de `/story`
que arma el payload de `alerta` y `recomendacion`.

## 5. Verificación

- **Contrato**: `uv run pytest tests/test_story_render.py` — el test existente ya
  exige fixture por plantilla y ausencia de tokens huérfanos. Las fixtures
  extendidas con los dos campos nuevos lo mantienen verde.
- **Paleta**: `uv run python scripts/marca_tokens.py --check`, **extendido para
  escanear también los `.css` de la carpeta**. Hoy solo mira `*.html`, así que un
  hex suelto en `piel.css` pasaría inadvertido y la fuente única dejaría de serlo
  justo en el archivo nuevo.
- **Revisión visual**: `uv run --extra stories python scripts/rendir_todas.py` en
  los dos formatos. Es la única forma de ver si la familia quedó pareja — los
  defectos de consistencia no se detectan revisando de a una plantilla.
- **Legibilidad del fondo**: verificar sobre el render real que el fondo tenue no
  compromete la firma de `recomendacion` ni el disclaimer. Medido, no estimado.

## 6. Fuera de alcance

`dato_macro` y las otras seis plantillas **no** se tocan. Una vez que `piel.css`
exista, migrarlas es enlazar la hoja y borrar reglas, pero cada una tiene su
propia calibración de alturas y meterlas todas en un cambio es cómo se rompe algo
sin que nadie sepa cuál fue. Una plantilla por Change, mismo criterio que las
Fases B y C del roadmap de Stories GI.

Tampoco entra ningún cambio de estructura, de campos editoriales ni del límite de
3 señales por semana.

## 7. Deudas detectadas, no incluidas

Encontradas al revisar el motor para este diseño. Se documentan para que no se
pierdan; arreglarlas acá mezclaría dos trabajos.

1. **`MAPA` de `marca_tokens.py` desactualizado** — conserva los hex de la paleta
   anterior (`#0D0D1A` como `fondo`, `#3E91AF` como `acento`), que ya no son los de
   `marca.css` (`#000000` y `#50C0A8`). El modo `--check` sigue sirviendo, pero el
   modo migrador escribiría roles equivocados sobre una plantilla nueva.
2. **`rgba()` invisible al gate** — `alerta.html` tiene tres colores escritos como
   `rgba(232, 64, 64, …)`. El patrón del check solo reconoce hex de 6 dígitos, así
   que no los ve. Mismo agujero para los hex de 3 dígitos.
