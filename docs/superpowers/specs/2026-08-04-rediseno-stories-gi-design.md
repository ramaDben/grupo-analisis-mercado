# Rediseño de las Stories GI — de informe a invitación

**Fecha**: 2026-08-04 · **Estado**: implementado (plantilla `oportunidad` integrada)
**Prototipo**: `templates/stories/_exploracion/oportunidad.html` (prototipo archivado)
**Piezas de referencia**: `data/stories/_revision/oro_gi_horizontal.png` · `oro_gi_vertical.png`

---

## Implementación

Estado: completada en el repositorio.
Cambios aplicados:
- templates/stories/oportunidad.html — nueva plantilla integrada (horizontal + vertical via CSS responsive).
- templates/stories/assets/activos/* — imágenes IA-normalizadas disponibles (oro/plata/wti/us100/usdclp).
- templates/stories/marca.css — tokens de color por activo añadidos (`--activo-oro`, etc.).
- scripts/marca_tokens.py — mapa actualizado; `--check` pasa para todas las plantillas.
- scripts/story_grafico.py — `recorrido.ajuste` soporta `llenar` -> `preserveAspectRatio="none"` (escenario a sangre).
- tests/fixtures/stories/payloads/oportunidad.json — payload de prueba añadido.

Deuda técnica cerrada:
1) `preserveAspectRatio` parametrizado para gráficos de escenario.
2) Fixture de prueba para la plantilla `oportunidad`.
3) Paleta movida a `marca.css` y verificada con `scripts/marca_tokens.py --check`.

Notas:
- Las decisiones pendientes en la spec (titular: número redondo vs motor, y color exacto del precio actual) se dejaron como opciones editoriales; los tokens permiten cambiarlos sin tocar plantillas.

---

## 1. El problema

El director revisó las piezas del 4 de agosto y las devolvió con tres frases: *"no calientan a
nadie"*, *"muy plano"*, *"somos una empresa de tecnología de trading con IA"*. Después precisó lo
que faltaba: **"que informe claramente PERO que invite a invertir"**.

El diagnóstico separó dos problemas que venían juntos:

- **De forma**: todo el lienzo en el mismo rango tonal, composición ortogonal de informe bancario,
  el dato compitiendo con seis bloques del mismo peso visual, el gráfico relegado al pie y nada que
  comunicara que detrás hay un motor.
- **De fondo**: la pieza terminaba en "esto significa X". Un dato de vacantes de empleo no mueve a
  nadie por bonito que se vea. Lo que mueve es un activo, una dirección, un precio y una acción.

Rediseñar solo la estética habría producido piezas preciosas que siguen sin invitar a operar.

---

## 2. Las decisiones

### 2.1 El protagonista es el activo operable, no el indicador

La pieza se reordena: **activo → dirección → titular con precio → los dos precios → la razón → CTA**.
El dato macro baja a tarjeta lateral. Deja de ser la noticia y pasa a ser la evidencia.

Consecuencia aceptada: **una pieza, un activo**. El mensaje de `/dato_macro` lista tres activos
impactados; esta pieza se juega por uno. El foco es lo que la hace vender.

### 2.2 La tarjeta de dato dice la lectura, no la cifra

Arriba **"MENOS EMPLEOS EN EE.UU."** en grande; abajo *"7,36 millones de puestos sin cubrir · se
esperaban 7,44 M"* en chico. Es regla del sistema, no decisión de esta pieza: **arriba lo que
significa, abajo el número que lo prueba**. Aplica igual a inflación ("suben los precios"), a
inventarios ("hay más petróleo guardado") y a tasas ("el crédito queda más caro").

El motivo lo dio el director en una frase: *"ese dato es inútil solo"*.

### 2.3 El titular nombra un precio del motor, no una figura técnica

*"El oro sube y busca los 4.100"* en vez de *"El oro va por sus máximos"*. El nivel sale de
`get_asset_levels`, no de una lectura editorial. Y el titular no usa una sola palabra de jerga: la
explicación tampoco (*"En Estados Unidos se están abriendo menos empleos"*).

**Tensión con una regla existente**: el repo obliga a decir "soporte/resistencia" y prohíbe
"techo/suelo". Se resolvió dejando el titular y la explicación sin jerga y manteniendo
"RESISTENCIA" solo como rótulo de la cifra, acompañado de **"SI LA ROMPE, VA A"**, que dice lo
mismo en palabras que cualquiera entiende.

### 2.4 Los dos precios son el corazón

`PRECIO AHORA → HACIA DÓNDE VA`, ambos al mismo tamaño, con una flecha entre medio. El objetivo no
es una nota al pie: es la razón por la que alguien opera. El nivel intermedio ("primero tiene que
romper 4.078,77") baja a nota.

### 2.5 Tipografía

Space Grotesk para titulares y cifras. Se compararon cuatro candidatas con el mismo contenido
(`data/stories/_revision/tipo_*.png`) porque el equipo reportó que la tipografía anterior era
*"molesta a la vista, ruidosa"*.

**Syne queda fuera del sistema.** En peso 800 cierra contraformas y cansa la vista — el mismo
defecto por el que ya había quedado fuera del folleto de capacitación. Que el equipo lo detectara
por su cuenta confirma un problema real, no una preferencia.

Montserrat quedó descargada y probada (`data/stories/_revision/oro_montserrat_*.png`) por ser la
familia de las infografías del Departamento de Estudios. El director prefirió mantener Space
Grotesk. Ambas quedan disponibles.

### 2.6 Color

Tres roles que no se mezclan:

| Rol | Token | Dónde |
|---|---|---|
| **Marca** | `--acento` (verde GI) | Titular, precio actual, tarjeta, CTA, cromo |
| **Identidad del activo** | `--activo` | Nombre del activo, halo, tono de la imagen |
| **Dirección de mercado** | `--sube` / `--baja` | Píldora de dirección, precio objetivo, veredicto |

`--activo` se define por activo: oro `#E8B44C`, WTI `#E8783C`, US100 `#4C86E8`, USD/CLP `#C9743A`.

Esto **extiende** la regla de color del repo sin romperla: `--sube`/`--baja` siguen siendo semántica
intocable. Si identidad y dirección se colapsaran en un token, una pieza dorada bajista se leería
como alcista dorada.

**Decisión abierta**: hoy el precio actual está en verde de marca y el objetivo en verde de
dirección — dos verdes tan parecidos que el par deja de leerse como "de acá hacia allá". Se propuso
devolver el precio actual a blanco. Pendiente de resolución del director.

### 2.7 Imagen por activo

Cada activo trae su fotografía. Se descartaron los bancos libres: lo que hay con licencia limpia es
pobre y lo bueno está en CC BY-SA, que obliga a licenciar la pieza derivada igual — inaceptable para
marca.

**Las imágenes se generan con IA y son propias.** El recetario vive en
`docs/design/stories-gi/imagenes-por-activo.md`: seis parámetros de look extraídos de la foto que el
equipo aprobó, un prompt base y un prompt por activo. Las primeras siete ya están generadas y
normalizadas en `templates/stories/assets/activos/`.

Dos cuidados que impone el medio: el generador estampa marca de agua abajo a la derecha (se recorta
el 8% inferior al normalizar), y en billetes los modelos inventan texto ilegible, además del terreno
legal que implica reproducir moneda.

### 2.8 El gráfico es escenario, no adorno

La serie real de MT5 ocupa el lienzo completo detrás del contenido. Somos una empresa de datos: el
dato no puede estar de adorno al pie.

Compite con el texto, y eso se resolvió **apagándolo por zonas** con una máscara vertical (12% de
opacidad en la banda de los precios) en vez de moverlo. Se probaron ambas opciones
(`vert_A_grafico_arriba.png` vs `vert_B_grafico_mascara.png`): moverlo solo traslada el estorbo al
titular, y deja de funcionar en cuanto el bloque de texto cambia de alto.

### 2.9 Los dos formatos

Un archivo, `@media (max-aspect-ratio: 1/1)`, igual que el resto del sistema. En vertical:

- La imagen **no va centrada ni grande**: probada así, le robaba el protagonismo a la dirección y a
  los precios. Queda a la derecha y a media escala.
- La ilustración y la tarjeta entran al flujo; flotándolas, el apilado las ignoraba y el CTA se iba
  fuera del lienzo (296 px medidos).
- El handle de la marca desaparece: el logo ya identifica a GI y liberar ese ancho evita que el CTA
  se parta en tres líneas.

Todo medido con Playwright, no estimado.

---

## 3. Contrato de datos

```json
{
  "plantilla": "oportunidad",
  "sello": "MOTOR GI · ANÁLISIS EN VIVO",
  "fecha_hora": "4 AGO 2026 · 11:26 CLT",
  "activo_nombre": "ORO",
  "activo_ticker": "XAU/USD",
  "activo_slug": "oro",
  "activo_imagen": "../assets/activos/oro.jpg",
  "modo_imagen": "foto-activo",
  "sesgo": "Alcista",
  "direccion_etiqueta": "SUBIENDO",
  "titular": "El oro sube y busca los 4.100",
  "razon": "En Estados Unidos se están abriendo menos empleos. Eso acerca la baja de tasas…",
  "precio": "4.076,92",
  "objetivo_rotulo": "Hacia dónde va",
  "objetivo": "4.115,90",
  "nota_nivel": "Primero tiene que romper 4.078,77",
  "dato_rotulo": "Por qué sube",
  "dato_lectura": "Menos empleos en EE.UU.",
  "dato_detalle": "7,36 millones de puestos sin cubrir · se esperaban 7,44 M",
  "dato_veredicto": "Peor de lo esperado",
  "cta": "¿Quieres aprovechar este movimiento?",
  "cta_sub": "Habla hoy con tu analista",
  "recorrido": { "serie": [], "marcadores": [] }
}
```

`modo_imagen` elige entre `foto-activo` (franja fundida, recomendado) e `ilustracion` (objeto
recortado). Los precios respetan los `digits` de `config/activos.json`.

---

## 4. Límite editorial

La pieza **invita a operar; no recomienda una operación**. Nombra activo, dirección, precio actual,
objetivo y CTA al analista. **No lleva entrada, TP, SL ni volumen**: eso la convertiría en señal,
con firma acreditada y contando para el límite de 3 por semana. La regla existe porque una
recomendación induce una operación y tiene que constar quién la respalda.

---

## 5. Alcance

**Incluye**: una plantilla nueva, `oportunidad`, en los dos formatos, con imagen y color por activo.

**No incluye** (queda para Changes posteriores):

- Migrar `alerta` y `dato_macro` de producción al lenguaje nuevo.
- El resto de las plantillas del sistema.
- Integrarla como tipo de `/story` y su comando fuente.

---

## 6. Deuda técnica

1. **`story_grafico.py` emite `preserveAspectRatio="xMidYMid meet"`** y el escenario a sangre
   necesita `none`. Hoy se parchea sobre el JSON; debe parametrizarse en el script.
2. **El prototipo vive fuera de producción** (`_exploracion/`) y por eso no tiene fixture ni pasa por
   `test_story_render.py`. Al promoverlo hay que agregar
   `tests/fixtures/stories/payloads/oportunidad.json` — el test lo exige y es lo que corresponde.
3. **`marca_tokens.py --check` va a fallar** cuando esto entre a producción: la paleta por activo
   está hardcodeada en la plantilla. Los cuatro colores deben mudarse a `marca.css` como tokens.
4. **Las fuentes nuevas** (Montserrat ×4, Sora, Outfit, Manrope, Space Grotesk 700) están en el repo;
   las que no se usen conviene borrarlas antes del merge.

---

## 7. Verificación

- Medición de layout con Playwright en ambos formatos: sin desbordes ni solapamientos.
- `pytest tests/test_story_render.py` → 66 passed (el prototipo no participa todavía).
- Piezas generadas con datos reales del motor: Oro 4.076,92 y serie de 72 velas H1 de MT5, JOLTS de
  junio desde el calendario Investing.

## 8. Decisiones pendientes del director

1. El par de precios en dos verdes casi iguales (§2.6).
2. Si el titular nombra el número redondo (4.100) o el nivel exacto del motor (4.116). Hoy la pieza
   muestra 4.100 en el titular y 4.115,90 en el bloque.
3. Si esta plantilla reemplaza a `dato_macro` como pieza 1 de la agenda diaria o convive con ella.
