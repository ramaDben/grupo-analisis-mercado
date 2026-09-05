# Inventario de módulos: qué corre, qué está declarado, qué sobra

**Fecha:** 2026-09-05
**Estado:** diseño aprobado por el director, pendiente de plan de implementación
**Precede a:** la reestructuración de `CLAUDE.md` (spec aparte, todavía sin escribir)

---

## 1. Por qué esto va antes que la reestructuración de `CLAUDE.md`

Dos razones, y la segunda es la que apura.

**El mapa de destino necesita saber qué código sobrevive.** La estrategia entera de la
reestructuración es "puntero de una línea a `docs/`". Un puntero a la documentación de un
script que está por borrarse es peor que no haber puesto nada: promete algo que no existe, y
el que lo sigue pierde el tiempo antes de darse cuenta.

**Y hay un riesgo activo.** `scripts/generar_grafico_spread_bonos.py` tiene en sus líneas
33-35 `jgb_oficial_10y = 2.882`, `us_10y_val = 4.70` y `spread_val = 1.82` escritos a mano.
Está disponible, corre, y produce un gráfico de aspecto institucional con tasas de hace dos
semanas adentro. El problema no es que ocupe lugar. Es que funciona.

Es exactamente el género contra el que `CLAUDE.md` ya advierte con
`generar_graficos_drivers.py`: *"tiene las series escritas a mano y produce piezas de aspecto
institucional a partir de números que nadie midió"*. La advertencia estaba escrita y el repo
tenía tres más del mismo tipo sin que nadie los contara.

---

## 2. Lo medido

Barrido sobre 77 módulos candidatos (`scripts/`, `src/`, `tools/`) y 10 plantillas, contra un
índice de 797 archivos del repo.

| Grupo | Qué es | Cuántos |
|---|---|---|
| A | Cero menciones en todo el repo | 15 |
| B | Solo nombrados en prosa, ningún módulo los llama | 6 |
| — | El resto: llamados por otro módulo | 56 |

El grupo A pesa **2.677 líneas**.

---

## 3. El hallazgo que define el diseño

**"Sin referencias en el repo" no es "muerto", y confundirlos borra cosas vivas.**

El primer barrido puso a `generar_calculadora.py` en la lista de huérfanos. Está vivo: la
tarea de Windows `GI-CalculadoraLotaje` (verificada `Ready`) corre
`scripts/refrescar_calculadora.cmd`, que lo invoca, lee MT5 y publica en un sitio público de
GitHub Pages. El detector no lo vio porque no escaneaba `.cmd`.

Corregido el escaneo, el resultado se invierte de forma instructiva: `generar_calculadora.py`
sale de la lista y **entra `refrescar_calculadora.cmd`**, porque su invocador es el Programador
de tareas y vive fuera del repo.

De ahí sale la forma del diseño. Hay tres invocadores que el repo no puede ver:

1. El Programador de tareas de Windows.
2. Un `.cmd` o `.bat` que a su vez llama a un módulo.
3. El director, corriendo algo a mano cuando lo necesita.

**Ninguna cantidad de análisis estático los encuentra.** Hay que declararlos.

---

## 4. La regla de justificación

Un módulo o plantilla está justificado si se cumple **al menos una**:

1. **Otro módulo lo llama** (import, `subprocess`, referencia en un `.cmd`/`.bat`/`.json` de
   configuración).
2. **La prosa operativa lo nombra con su comando**: `CLAUDE.md`, `.agents/rules/`,
   `.claude/commands/`, `.agents/workflows/`, y las guías operativas de `docs/`.
3. **Declara su punto de entrada externo** con el encabezado de §6.

Nada más justifica. En particular, **no** justifican:

- Un doc de diseño en `docs/design/` o `docs/archive/`. Es la historia de por qué se
  construyó, no evidencia de que se use. `templates/parte_postventa.txt` sobrevivió al primer
  filtro exactamente así: lo nombran dos docs de julio de una función que `CLAUDE.md` declara
  retirada. Un doc de diseño de algo retirado es la lápida, no el uso.
- Aparecer en `.git/index` o en un caché de herramientas.

---

## 5. Dos refinamientos que un barrido ingenuo no tiene

### 5.1 Los huérfanos son transitivos, así que el detector itera a punto fijo

`templates/calculadoras/instrucciones.html` tiene un solo referente:
`scripts/instrucciones_simulador.py`. Que a su vez no lo referencia nadie.

Una pasada lo declara justificado, porque alguien lo nombra. Dos pasadas lo encuentran. El
detector repite el barrido sacando en cada vuelta los que ya quedaron injustificados, hasta
que una vuelta no saca a nadie. Sin eso, una cadena muerta de tres eslabones se esconde
detrás de su propio primer eslabón.

### 5.2 El detector nunca borra

Su única acción es **fallar la suite**. El borrado es siempre un commit de una persona que
miró el archivo.

Esto no es cautela decorativa: la invocación dinámica existe (`importlib`, un `subprocess` con
el nombre armado por concatenación) y es invisible al análisis de texto. Un detector que
borrara solo convertiría un falso positivo en pérdida de código. Un detector que falla
convierte el mismo falso positivo en una línea de encabezado.

---

## 6. El encabezado `punto-de-entrada`

Una línea de comentario en las primeras 20 del archivo:

```python
# punto-de-entrada: tarea programada de Windows GI-CalculadoraLotaje
```

```powershell
# punto-de-entrada: lo corre el director a mano cuando revisa el simulador
```

**Va en el archivo y no en un JSON de inventario**, por la doctrina que este repo ya paga
caro: un JSON con nombres de archivo es un contrato por nombre, se desincroniza al primer
renombre, y falla por la razón equivocada. El encabezado viaja con el archivo, sobrevive al
`git mv`, y lo ve cualquiera que lo abra.

El texto libre después de los dos puntos es obligatorio y no vacío: **"declarado" sin decir
quién lo llama es la misma opacidad con otro nombre.**

---

## 7. El detector

`scripts/huerfanos.py`, mismo patrón que `agy_workflows.py` y `marca_tokens.py`:

```bash
uv run python scripts/huerfanos.py           # informa
uv run python scripts/huerfanos.py --check   # falla si hay injustificados (lo corre la suite)
```

Alcance: `scripts/`, `src/`, `tools/`, `templates/`.
Índice: `.py .md .ps1 .cmd .bat .json .toml .yaml .yml .txt .html .css`, excluyendo
`__pycache__`, `.git`, `.venv`, `node_modules`, `data/`, `brand_atomic_system/` y `archive/`.

**`archive/` se excluye a propósito**: es donde vive lo retirado y sus referencias no deben
mantener vivo a nadie. Es el mismo criterio que descarta los docs de diseño.

**Solo se juzgan archivos rastreados por git.** Lo no rastreado y lo gitignoreado no es el
repo: es el escritorio de alguien. Sin esta regla, un archivo de trabajo a medias pone la
suite roja en la máquina de quien lo escribió y en ninguna otra, que es la peor clase de test.

No es hipotético en las dos direcciones. `scripts/spanish_test.py` (28 líneas) aparecía como
huérfano en el primer barrido y está **gitignoreado a propósito** en `.gitignore:96`: la
decisión ya estaba tomada y el detector la habría vuelto a abrir. Y hoy mismo hay un
`scripts/hook_ingesta_macro.py` sin commitear en el árbol de trabajo, de otra rama.

La salida nombra, por cada injustificado, su tamaño y las dos acciones posibles: declararlo o
borrarlo. Un detector que dice "hay 9 problemas" sin decir cuáles no es auditable, que es la
misma regla que ya se le exige al escáner con sus exclusiones.

---

## 8. Los tests

| Test | Qué impone |
|---|---|
| `test_no_hay_modulos_injustificados` | Todo módulo y plantilla cumple una de las tres vías de §4 |
| `test_el_detector_escanea_cmd_y_bat` | Lee la fuente del detector y falla si esas extensiones salen del índice. Es el bug que ya se cometió una vez |
| `test_el_detector_itera_a_punto_fijo` | Con una cadena muerta de tres eslabones armada en la fixture, los encuentra a los tres |
| `test_un_doc_de_diseno_no_justifica` | Un módulo nombrado solo desde `docs/design/` sigue apareciendo como injustificado |
| `test_el_encabezado_exige_un_motivo` | `# punto-de-entrada:` sin texto después no cuenta como declaración |
| `test_el_detector_no_borra` | Barre la fuente del detector: ni `unlink`, ni `rmtree`, ni `os.remove`. Mismo mecanismo que `test_el_reloj_no_puede_enviar_nada_a_whatsapp` |

El segundo y el sexto son los que valen. El segundo fija un error ya cometido para que no
vuelva; el sexto impide que alguien "mejore" el detector agregándole el borrado automático, que
es la evolución natural y la equivocada.

---

## 9. El barrido de esta spec

**Se borra** (evidencia por archivo, no criterio general):

| Archivo | Líneas | Evidencia |
|---|---|---|
| `scripts/temp_clean.py` | 17 | Nombre temporal, cero referencias |
| `scripts/temp_strip.py` | 16 | Ídem |
| `scripts/generar_piezas_impacto_warsh.py` | 479 | Escribe a `.gemini/antigravity-cli/brain/5ad0bb37-…`, un directorio de sesión de AGY con UUID. No puede volver a funcionar |
| `scripts/generar_grafico_spread_bonos.py` | 170 | Tasas escritas a mano en las líneas 33-35 |
| `scripts/generar_grafico_usdjpy_cpi.py` | 117 | No lee nada de disco: el gráfico no tiene fuente de datos |
| `scripts/generar_cierre_semanal_story.py` | 646 | Superado por `compilar_informe_cierre_semanal.py`, que es el que la prosa operativa documenta |
| `scripts/generar_resumen_semanal_pdf.py` | 190 | Ídem |
| `templates/parte_postventa.txt` | — | De `/postventa`, retirado. Solo lo nombran dos docs de diseño de julio |

**Total: 1.635 líneas más una plantilla.**

**Se declara con encabezado** (siguen existiendo, ahora dicen quién los llama):

| Archivo | Declaración propuesta |
|---|---|
| `scripts/refrescar_calculadora.cmd` | Tarea programada `GI-CalculadoraLotaje`, verificada `Ready` |
| `scripts/auditar_espacios.py` | Herramienta manual |
| `scripts/recortar_activo.py` | Herramienta manual |
| `scripts/reparar_mensajes_txt.py` | Herramienta manual |
| `scripts/exportar_preview_editorial.py` | Herramienta manual |
| `scripts/generar_graficos_sesion_asiatica.py` | Herramienta manual, **a confirmar**: lee MT5, así que no comparte el defecto de los otros generadores |
| `scripts/ejecutar_agenda_macro.ps1` | Pendiente de registro en el Programador de tareas; lo toma la spec de cobertura de eventos macro |

**Queda pendiente de tu confirmación** el par `scripts/instrucciones_simulador.py` (149) +
`templates/calculadoras/instrucciones.html`. Es el huérfano transitivo de §5.1 y `simulador_gi.py`
sí está vivo, así que puede ser una pieza legítima del simulador que simplemente nadie invoca
desde el repo. No lo borro sin que lo mires.

**Ya justificados por prosa operativa, sin tocar**: `simulador_gi.py`, `folleto_fundamental.py`,
`verificar_capacitacion.py`, `instalar_reloj.ps1` (los nombra `CLAUDE.md` con su comando) y
`compilar_manual_pdf.py` (lo nombra `.agents/rules/proyecto.md`).

---

## 10. Lo que esta spec NO hace

- **No toca `docs/`.** Un doc sin referencias no es residuo: casi ningún doc se referencia. El
  desorden de `docs/` (auditorías forenses sueltas, carpetas con nombre de reporte) es un
  trabajo aparte y lo absorbe la reestructuración de `CLAUDE.md`.
- **No toca `config/` ni `conceptos/`.** Mismo motivo: un JSON de configuración leído por su
  nombre completo desde código no siempre aparece como referencia textual, y el detector daría
  falsos positivos.
- **No borra nada en `data/`.** Es estado generado e historia editorial, con sus propias reglas.
- **No corrige el precio del cobre hardcodeado** en `.agents/rules/proyecto.md:167` y
  `.agents/skills/generar-reporte-editorial/SKILL.md:52`. Es el mismo género de defecto y se
  encontró en este barrido, pero vive en las reglas, no en el código: lo arregla la
  reestructuración de `CLAUDE.md`, que es la que rehace esos archivos. **Queda anotado acá para
  que no se pierda entre las dos specs.**

---

## 11. Fases

| Fase | Qué | Injustificados al terminar |
|---|---|---|
| 1 | `scripts/huerfanos.py` con las tres vías de §4, iteración a punto fijo y `--check`. Sin tocar ningún archivo del repo | 17 |
| 2 | Los seis tests de §8. En este punto la suite está **roja**, y eso es correcto: mide el estado real | 17 |
| 3 | Los siete encabezados `punto-de-entrada` de §9 | 10 |
| 4 | El barrido de §9, en un commit propio y separado, para que revertirlo sea un `git revert` limpio | 2 |
| 5 | El par del simulador, según lo que decidas | 0 |

Los 17 de partida son los 14 del grupo A que git rastrea, más
`scripts/ejecutar_agenda_macro.ps1` (que solo aparece en un doc de diseño, y §4 no lo acepta),
más los dos huérfanos que aparecen recién en la segunda vuelta del punto fijo:
`templates/parte_postventa.txt` y `templates/calculadoras/instrucciones.html`.

**Las fases 3 y 4 van separadas a propósito.** Declarar es reversible leyendo el diff; borrar
1.635 líneas mezcladas con encabezados nuevos hace ilegible el commit que hay que revisar.

---

## 12. Cómo se engancha con la reestructuración de `CLAUDE.md`

Hay un acoplamiento real y conviene nombrarlo antes de que muerda.

Cuatro módulos están justificados **solo porque `CLAUDE.md` los nombra**
(`simulador_gi.py`, `folleto_fundamental.py`, `verificar_capacitacion.py`,
`instalar_reloj.ps1`). La reestructuración va a mover buena parte de esa prosa a `docs/`. Si el
detector solo mira `CLAUDE.md`, esos cuatro pasan a injustificados el día que se mueva el
párrafo, y la suite se pone roja por una razón que no tiene nada que ver con ellos.

Por eso la vía 2 de §4 define un **conjunto de prosa operativa**, no un archivo. La
reestructuración agrega ahí los destinos que cree, y el test de enlaces muertos que esa spec
propone es la otra mitad del mismo contrato: uno verifica que la prosa apunte a archivos que
existen, este verifica que los archivos que existen estén nombrados por la prosa.

Son las dos direcciones del mismo invariante, y por eso conviene que este vaya primero: fija
el conjunto de código antes de que la otra spec reorganice el conjunto de prosa.
