# `CLAUDE.md`: ni más ni menos que el flujo de entrega

**Fecha:** 2026-09-06
**Estado:** diseño aprobado por el director, pendiente de plan de implementación
**Depende de:** `docs/design/inventario-modulos/2026-09-06-inventario-modulos-design.md`, que va primero

---

## 1. El problema, medido

`CLAUDE.md` pesa **1.341 líneas / 100.901 bytes**, y se carga entero al arrancar cada sesión.
Son **43,1k tokens: el 5% de la ventana antes de que el director escriba la primera palabra**,
y lo pagan las dos runners en cada sesión de cada día.

Eso solo no lo justifica recortarlo. Lo que lo justifica es que **hay secciones enteras que no
tocan ni una vez el camino que termina en un mensaje entregado a un canal**: el generador del
PPTX de capacitación, el folleto de consulta, el manual de operaciones y su auditoría contra
el motor, el troubleshooting del CSS embebido del 12 de agosto, y un árbol del proyecto que ya
está desactualizado.

Y hay un segundo problema, más serio, que se descubrió midiendo esto.

---

## 2. `.agents/rules/proyecto.md` no es un extracto: es un fork

`CLAUDE.md` declara que ese archivo es "un extracto" de sí mismo. No lo es: nada lo genera
(`agy_workflows.py` solo produce `.agents/workflows/`), nada lo verifica, y ya se separó en
**las dos direcciones**.

| Concepto | `CLAUDE.md` | `proyecto.md` |
|---|---|---|
| Gates del escáner | **seis** (desde el 2026-09-04) | **cuatro** |
| `historial_despachos.json` | sí | **no** |
| `reloj_gi` y los momentos del día | sí | apenas |
| Suplemento de canal | sí, 11 menciones | **no** |
| Noticia oficial | sí | no |
| Hooks de ingesta | sí | no |
| Cierre semanal · UTF-8 y tuberías · trazado horizontal | **no** | sí |

**El de la bitácora es el que preocupa.** Los seis comandos están expuestos a Antigravity por
igual, envío incluido: AGY puede despachar y **no sabe que existe el archivo que impide
reenviar un canal que falló a la mitad**. Eso son mensajes duplicados en canales reales, que
es exactamente el daño que la bitácora existe para evitar.

Este spec cierra el fork. No es un efecto colateral del recorte: es la mitad del trabajo.

---

## 3. El criterio, y va escrito arriba del archivo

> **Acá vive lo que cambia lo que sale a un grupo hoy. Todo lo demás vive en `docs/` y se
> enlaza en una línea.**

Va como primer bloque de `CLAUDE.md`, antes del contexto. Sin el criterio escrito, el próximo
agregado se justifica solo: así llegó a 43k tokens, una sección razonable por vez.

El criterio incluye **las reglas de contenido** (tono, decimales, temporalidades, formato de
WhatsApp, diccionario de siglas), porque un mensaje que sale con el registro equivocado o con
`$889.6` en vez de `$889.60` no satisface la necesidad del canal aunque haya salido puntual.

---

## 4. Marcadores de ámbito

Cada `##` de `CLAUDE.md` declara a quién aplica, en un comentario HTML inmediatamente después
del encabezado:

```markdown
## El despacho: un lote por canal
<!-- ambito: ambos -->
```

| Valor | Va a |
|---|---|
| `ambos` | `CLAUDE.md` y `proyecto.md` |
| `claude` | Solo `CLAUDE.md`: hooks, el tool `Skill`, los slash commands como mecanismo |
| `agy` | Solo `proyecto.md`: OMEGA, y lo que dependa del entorno de Antigravity |

Un `###` **puede** sobrescribir el ámbito de su `##`, y hace falta: "La ingesta se engancha al
arranque de sesión" es un `###` bajo una sección de ámbito `ambos` y es `claude` puro, porque
los hooks no existen en AGY.

**Una sección sin marcador hace fallar al generador, no se asume.** Es el mismo mecanismo que
`clases_sin_momento` en la agenda de mercado: no impide que exista un caso nuevo, impide que se
quede fuera en silencio. Un ámbito por omisión convertiría cada sección nueva en una decisión
que nadie tomó.

**`agy` no es una categoría teórica.** OMEGA ya está documentado en el `CLAUDE.md` **global**
del director, y AGY no lee ese archivo. Repetirlo en el del proyecto es reabrir el fork; que
exista un ámbito propio es lo que permite que `proyecto.md` lo lleve sin duplicar nada.

---

## 5. El generador tiene que entender bloques de código

`scripts/agy_reglas.py`, mismo patrón que `agy_workflows.py`:

```bash
uv run python scripts/agy_reglas.py           # genera .agents/rules/proyecto.md
uv run python scripts/agy_reglas.py --check   # verifica (lo corre la suite)
```

**El parser lleva estado de fence, y no es una precaución teórica.** La línea 1231 de
`CLAUDE.md` es `# -> data/mensajes/2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt`: un
comentario de PowerShell dentro de un bloque ` ``` `. Un parser por regex la lee como un
encabezado H1 y parte el documento en un lugar que no existe.

Hoy hay exactamente una, medida. Pero los ejemplos de PowerShell con comentarios `#` están por
todo el repo y este archivo está lleno de bloques de código: el fantasma vuelve.

Además, `proyecto.md` conserva un preámbulo propio (a quién le habla, y que ante cualquier
contradicción manda `CLAUDE.md`) y su sección de ámbito `agy`. Todo lo demás sale de las
secciones marcadas, en el orden del original.

---

## 6. Los tests

| Test | Qué impone |
|---|---|
| `test_proyecto_md_esta_al_dia` | Regenera y compara. Es el que cierra el fork |
| `test_toda_seccion_declara_ambito` | Sin marcador, falla. Fail-closed |
| `test_el_parser_respeta_los_fences` | Fixture con un `# comentario` dentro de un bloque; el parser no lo cuenta como sección. Fija un defecto ya presente |
| `test_claude_md_no_pasa_del_presupuesto` | Tamaño en bytes contra el techo de §10 |
| `test_todo_enlace_a_docs_existe` | Cada puntero de una línea apunta a un archivo real |

**El último es el que sostiene la estrategia entera.** Si el plan es "puntero de una línea a
`docs/`", un puntero muerto es peor que no haber puesto nada: promete algo que no existe, y el
que lo sigue pierde el tiempo antes de darse cuenta.

Es también la mitad complementaria del contrato del spec de inventario. Ese verifica que todo
archivo que existe esté nombrado por la prosa; este verifica que toda prosa apunte a un archivo
que existe. **Son las dos direcciones del mismo invariante**, y por eso el inventario va
primero: fija el conjunto de código antes de que este reorganice el conjunto de prosa.

---

## 7. Qué sale, exhaustivo

Seis secciones migran a `docs/` con su puntero de una línea (**217 líneas**) y dos se funden en
Contexto sin migrar (8 líneas más, de las que sobreviven unas 3).

| Sección | Líneas | A dónde |
|---|---|---|
| Capacitaciones internas (PPTX) | 38 | `docs/documentos-largos.md` |
| Guía rápida (folleto de consulta) | 36 | ídem |
| Manual de Operaciones | 32 | ídem |
| Lo que el manual afirma vs. el motor | 34 | ídem |
| Estructura del proyecto | 56 | `docs/notas-implementacion.md` |
| Stories GI: CSS embebido (2026-08-12) | 21 | ídem |
| Rol paralelo del grupo | 5 | se funde en Contexto, no migra |
| Misión | 3 | ídem |

`docs/documentos-largos.md` recibe además **el cierre semanal**, que hoy no está en
`CLAUDE.md` en absoluto: son seis scripts vivos (`compilar_informe_cierre_semanal.py` más
`cierre_semanal_{contenido,datos,estilo}.py`) que van a un grupo, y solo `proyecto.md` los
documenta. Cerrar el fork también significa que lo que solo tenía AGY quede en algún lado.

---

## 8. Qué se comprime, y con qué regla

Nueve secciones concentran **543 líneas, el 40% del archivo**, y todas describen el flujo de
entrega: se quedan, comprimidas.

| Sección | Líneas |
|---|---|
| Un solo reloj: `config/agenda_mercado.json` | 73 |
| El `Score_GI` y sus gates | 71 |
| El "hasta dónde" del sesgo | 65 |
| Stories GI y generación de imágenes | 68 |
| El despacho: un lote por canal | 61 |
| El reloj de sucesos | 59 |
| Un canal vacío se suplementa | 57 |
| La noticia oficial | 50 |
| Un PDF adjunto sí lleva su pie | 39 |

**La regla: sobrevive el invariante y la razón en una frase; la medición, la tabla y la fecha
se van al doc enlazado.**

Así:

> El pie del editor de medios tope en 1.024 caracteres y descarta **renglones enteros**, no el
> final del texto, así que el mensaje mutilado se lee como completo. El texto va en el cuadro
> de conversación y el adjunto **después**. Medición y DOM: `docs/historia-forense.md`.

Y no así:

> El pie tope en 1.024 caracteres. El texto va antes del adjunto.

**La diferencia no es de estilo: es si la regla sobrevive.** Sin el "por qué" en una frase, la
próxima vez que alguien optimice el despacho va a poner el pie en el editor porque es más
directo, y el canal va a recibir un mensaje al que le faltan líneas sin que nadie lo note. Ese
archivo entero está escrito así porque cada regla sin su razón ya se revirtió una vez.

Lo que **no** se comprime, porque ya es regla pura: los formatos de mensaje, el tono, los
decimales, las temporalidades, el diccionario, el flujo de aprobación, el contrato de los MCP.

---

## 9. Lo que sube desde AGY, auditado uno por uno

| Tema | Veredicto | Por qué |
|---|---|---|
| **UTF-8 y tuberías en PowerShell** | Sube, **fusionado** con la Regla 2 existente | Si se rompe, la pieza sale al canal con `AN?LISIS`. Es hermana literal de la prohibición de escribir `$` por consola: las dos dicen "no escribas texto de cliente por la shell", por dos razones distintas. Que vivan en archivos separados **es** el fork |
| **Trazado horizontal obligatorio** | Sube **la mitad que falta** | `CLAUDE.md` ya lo exige para el gráfico del informe. No tiene la parte de Stories, que es la que nombra los campos del payload (`hitos`, `niveles`, `clase`, `rol`). Un gráfico mudo llega al canal igual |
| **USD/CLP mercado cerrado** | Sube el criterio, **sin la cifra** | Es real y ya se publicó (`data/informes/2026-08-27_nocturna/`), y el reloj puede disparar de madrugada. Ver abajo |
| **Cierre semanal** | A `docs/`, con una línea | Su contenido es de maqueta (páginas fijas, `_medir_desbordes`). Pero existe y va a un grupo |
| **OMEGA** | `ambito: agy` | Ya está en el `CLAUDE.md` global; AGY no lo lee. Es el caso que justifica el tercer valor del marcador |

### El precio congelado dentro de las reglas

El criterio del USD/CLP cerrado trae el cobre a **`$14.274,0 USD/t` escrito a mano**, en
`.agents/rules/proyecto.md:167` **y** en `.agents/skills/generar-reporte-editorial/SKILL.md:52`.

Es un precio del 27 de agosto congelado, con un decimal que además contradice el `digits = 0`
que el terminal reporta para `COPPER`. O sea: **el archivo que prohíbe hardcodear precios,
hardcodea un precio**, en dos lugares, y uno de ellos es una skill que AGY carga para redactar.

Se corrige acá porque este spec es el que rehace esos archivos. El criterio sube sin la cifra:
el nivel del cobre se lee del terminal en el momento, como cualquier otro precio.

---

## 10. El presupuesto

Un test falla si `CLAUDE.md` pasa del **tamaño de corte más 15%**, medido en **bytes**.

Bytes y no tokens: el conteo de tokens depende del tokenizador y cambia sin que el archivo
cambie, así que un test sobre tokens falla por razones ajenas al diff. La cifra de tokens queda
en el comentario del test, como referencia para entender qué se está protegiendo.

**El número se fija al terminar el recorte, no ahora.** Un techo estimado de antemano es un
techo inventado.

El 15% de margen es deliberado: con un techo exacto, el primer agregado legítimo obliga a
sacar otra cosa en el mismo commit, y eso convierte cualquier corrección chica en una
negociación. Con margen, **para subirlo hay que editar el número a propósito**, y eso deja
rastro en el diff: la decisión de agrandar el archivo se toma, no se acumula sola.

### Estimación, y una corrección

En la conversación previa estimé el resultado en ~620 líneas. **Contando las secciones una por
una, la estimación sube a ~855.** El error era mío por optimismo: había supuesto un factor de
compresión más agresivo del que la regla de §8 permite, porque conservar la razón en una frase
cuesta líneas.

| | Líneas |
|---|---|
| Hoy | 1.341 |
| Las seis que migran, más las dos que se funden | −222 |
| Las nueve comprimidas (543 → ~215) | −328 |
| Suben desde AGY | +35 |
| Criterio, marcadores y punteros | +30 |
| **Estimado** | **~855** |

De 43,1k a **~27,5k tokens**. Es un **36% menos**, no el 54% que había dicho.

---

## 11. Modo de falla

**El generador no puede romper el arranque de sesión.** `CLAUDE.md` lo lee la runner al
arrancar, no el generador: si `agy_reglas.py` falla, `CLAUDE.md` sigue intacto y lo único roto
es la suite. La dirección de la dependencia importa y conviene no invertirla nunca.

**Un `proyecto.md` desactualizado falla ruidoso, no silencioso.** Hoy la divergencia es
invisible: los cuatro gates contra seis llevaban dos días sin que nada lo notara. Con el test,
un cambio en una sección `ambos` que no se regenere pone la suite roja en el mismo commit.

**El riesgo real de este trabajo es sacar algo que sí importaba.** Lo acota que todo migra con
puntero y nada se borra: el peor caso es un salto extra para leer algo que estaba a mano. Por
eso la fase de migración va **antes** de la de compresión, que es la irreversible.

---

## 12. Fases

| Fase | Qué |
|---|---|
| 1 | Los tres archivos de `docs/`, con el contenido migrado **tal cual**. `CLAUDE.md` todavía sin tocar: nada se pierde si esto se revierte |
| 2 | Quitar de `CLAUDE.md` las seis secciones migradas y dejar sus punteros. Fundir Misión y Rol paralelo en Contexto |
| 3 | El criterio arriba, y los marcadores de ámbito en todas las secciones |
| 4 | `agy_reglas.py` con estado de fence, más los tres primeros tests de §6. **Acá se cierra el fork**: la suite compara por primera vez |
| 5 | Los tres temas que suben desde AGY, y el cobre hardcodeado en los dos lugares |
| 6 | La compresión de las nueve secciones y `docs/historia-forense.md`. Un commit por sección, para que cada compresión se pueda revisar y revertir sola |
| 7 | Medir, fijar el presupuesto y agregar sus dos tests |

**Las fases 4 y 6 van en ese orden a propósito.** Comprimir antes de tener el generador
significa comprimir sin que nada verifique que `proyecto.md` sigue coherente, y son 543 líneas
de contenido operativo: es justo donde un error se paga.

**La fase 6 se parte por sección** porque es la única irreversible de verdad. Una compresión
que se pasó de mano se revierte sola si tiene su commit; mezclada con otras ocho, no.

---

## 13. Qué cambió al implementarlo

Implementado el 2026-09-06. Tres cosas salieron distintas, y la primera invalida una premisa
central de este documento.

### 13.1 La premisa de la compresión era falsa

§8 daba por hecho que las nueve secciones forenses eran regla enterrada en relato, y que
conservar "el invariante más la razón en una frase" iba a recortarlas a la mitad. **Medido, el
recorte real fue del 12%: de 543 a 478 líneas.** Una sección incluso creció.

| Sección | Antes | Después |
|---|---|---|
| Un solo reloj | 73 | 49 |
| El "hasta dónde" del sesgo | 65 | 42 |
| El reloj de sucesos | 59 | 52 |
| El `Score_GI` y sus gates | 71 | 64 |
| Un PDF adjunto | 39 | 32 |
| Un canal vacío se suplementa | 57 | 53 |
| La noticia oficial | 50 | 46 |
| El despacho | 61 | **63** |
| Stories GI | 68 | **77** |

**El diagnóstico estaba mal, no la ejecución.** La razón en una frase **ya estaba escrita** en
casi todos los párrafos: lo único genuinamente movible eran las tablas de medición, las cifras
exactas y las fechas, y eso es entre 4 y 24 líneas por sección. Comprimir más habría significado
borrar reglas o sus razones, que es lo que §8 prohíbe explícitamente.

Así que la conclusión de fondo se invierte: **`CLAUDE.md` no pesaba 43k tokens por estar inflado.
Pesaba eso porque está denso.** Es una conclusión más útil que un archivo mutilado.

Las dos que crecieron lo hicieron por buenas razones: Stories GI recibió el trazado horizontal
obligatorio que solo tenía AGY, y el despacho quedó mejor explicado con la tabla afuera.

### 13.2 El resultado real, y las tres estimaciones que hice mal

| | Líneas | Bytes | Tokens aprox. |
|---|---|---|---|
| Antes | 1.341 | 100.901 | 43,1k |
| Después | 1.182 | 88.072 | **37,6k** |
| Reducción | **12%** | 12,7% | 12,8% |

Estimé 46% (~620 líneas), después 36% (~855) y el resultado fue 12%. **Las dos primeras
correcciones fueron por optimismo; la tercera fue por haber diagnosticado mal el problema.**

Conviene decir qué sí se logró, porque no es el tamaño:

- **El fork está cerrado**, que era el problema serio. `proyecto.md` ya no puede divergir.
- **Cuatro reglas que solo tenía AGY** están ahora en los dos archivos, generadas.
- **225 líneas** genuinamente ajenas al flujo de entrega salieron a `docs/`.
- **El cobre congelado** desapareció de las reglas y de la skill.
- El criterio está escrito arriba, con un presupuesto que lo sostiene.

### 13.3 El margen del presupuesto tuvo que bajar de 15% a ~4,5%

§10 pedía el tamaño de corte más 15%. Con el recorte real, ese margen ponía el techo en **101.282
bytes: por encima de los 100.901 con que el archivo empezó.** El presupuesto habría permitido
exactamente la regresión que existe para impedir.

Quedó en **92.000 bytes** contra los 88.072 actuales: unas 50 líneas de margen. Es el mismo
razonamiento del margen, aplicado a la reducción que de verdad hubo.

### 13.4 Lo que sí funcionó tal como estaba diseñado

- **El parser fence-aware encontró 55 secciones donde un regex encontraba 56.** El encabezado
  fantasma era real y habría partido el documento.
- **El fail-closed del ámbito** obligó a decidir las 51 secciones una por una, que es el punto.
- **El test de `proyecto.md` desactualizado falló en cuanto comprimí la primera sección**, antes
  de que yo me acordara de regenerar. Es la demostración de que el fork no puede volver.
