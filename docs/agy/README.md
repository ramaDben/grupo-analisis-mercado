# Delegarle trabajo a Antigravity

Antigravity (`agy`) es el segundo runner del repo. Además de ejecutar los workflows de
`.agents/workflows/`, se le puede **delegar trabajo puntual** desde una sesión de Claude
Code: escribe el código, y Claude Code lo verifica y lo commitea.

El orquestador es `scripts/agy_encargo.py`. Este documento dice cuándo usarlo y por qué
tiene la forma que tiene; el cómo está en su docstring.

```bash
uv run python scripts/agy_encargo.py delegar docs/agy/encargos/x.md
uv run python scripts/agy_encargo.py delegar docs/agy/encargos/x.md --dry-run
uv run python scripts/agy_encargo.py verificar docs/agy/encargos/x.md
uv run python scripts/agy_encargo.py estado
```

## El reparto: qué delegar y qué no

| Se delega | Se queda de este lado |
|---|---|
| Módulos bien especificados con firmas ya fijadas | El **contrato**: qué firmas, qué vocabulario, qué invariantes |
| Baterías de tests exhaustivas | Los tests de **contrato**, que son los que impiden que el sistema se desarme |
| Migraciones mecánicas repetidas en muchos archivos | Cualquier decisión de arquitectura |
| Lecturas largas que se resumen a un digesto | La revisión, los commits y los PR |

**Un encargo chico es una pérdida.** El viaje de ida y vuelta cuesta entre cinco y ocho
minutos: tres módulos medidos el 2026-09-06 dieron 295 s, 365 s y 432 s. Por debajo de ese
umbral conviene escribirlo directamente.

**Lo que mejor salió fue lo que estaba más especificado.** Los tres encargos que
funcionaron traían las firmas públicas literales, el vocabulario cerrado, y una lista de
casos que **no** debían fallar. Dejar que invente una firma es el defecto recurrente del
repo —dos módulos que se hablan por nombre sin que nada verifique que coinciden—
multiplicado por la cantidad de encargos en paralelo.

## Por qué el orquestador mide en vez de creer

Tres cosas se pagaron delegando a mano el 2026-09-06, y las tres están resueltas en el
script:

**El reporte de AGY no es evidencia.** Puede terminar en `SUCCESS` con comandos fallidos
adentro. Por eso el encargo declara sus criterios de aceptación en `verificar`, y el
orquestador **los vuelve a correr desde acá**. El veredicto sale de esa corrida, no del
reporte.

**Los comandos que corrió no quedan registrados en ninguna parte**, así que para
atribuirle un cambio hay que diferenciar el árbol. El encargo declara en `archivos` qué le
pertenece, y el orquestador saca una instantánea antes y después. Un archivo de más se
reporta **fuera de ámbito**, y el veredicto es negativo aunque los tests estén en verde.

> La instantánea hashea el contenido y no se conforma con la lista de archivos sucios. Acá
> la ingesta macro deja dieciséis JSON de `data central/` modificados en cada arranque de
> sesión: si un encargo escribiera sobre uno de ellos, su línea de estado no cambiaría y
> el cambio sería invisible.

**La instantánea mide la ventana, no la autoría, y esa distinción importa.** Compara el
árbol antes contra el árbol después: cualquier cosa que cambie en el medio aparece como
fuera de ámbito, incluido lo que escribas vos. Pasó en la primera corrida real, el
2026-09-06: el informe acusó a `docs/agy/README.md`, que estaba escribiendo yo mientras la
delegación corría.

**Entonces el árbol es de la delegación mientras dura.** No es una limitación que se pueda
arreglar midiendo mejor, porque los comandos que agy corre no quedan registrados en ninguna
parte y no hay nada que consultar para atribuir un cambio. Si tenés que trabajar en
paralelo, que sea en otro worktree.

**Un fallo se ve igual que un encargo pensando**: un archivo de salida vacío. El
orquestador clasifica el resultado (`cuota`, `auth`, `timeout`, `vacio`, `ausente`) porque
cada uno tiene una acción distinta, y confundir un timeout con un problema de
autenticación cuesta reintentar lo que no se arregla reintentando. Para saber si sigue
vivo, `estado` mira el **CPU del proceso**: agy escribe su envoltorio JSON recién al
terminar.

## El veredicto tiene tres partes, y no se colapsan

`delegar` sale con `0` solo si las tres dan bien. Los códigos separan el motivo:

| Código | Qué pasó |
|---|---|
| `0` | ámbito respetado y verificación en verde |
| `1` | la verificación no pasó |
| `2` | tocó archivos fuera de ámbito |
| `3` | la delegación falló (cuota, auth, timeout, salida vacía) |
| `4` | el encargo está mal declarado y no se mandó |

Colapsarlas en un booleano escondería justo el caso interesante: tests en verde con un
archivo de más tocado.

**Y un `0` no cierra el trabajo.** Falta lo que ninguna herramienta puede hacer, que es
leer el código. Lo que el orquestador garantiza es que no vas a leer código creyendo que
algo pasó cuando no pasó.

## Antes de delegar

- **Rama propia, siempre.** El encargo no puede commitear (está prohibido en el preámbulo)
  pero deja el árbol sucio, y revisar un diff mezclado con otro trabajo es más caro que
  haberlo escrito.
- **Nombrá la rama en el encargo si importa.** El 2026-09-05 un diagnóstico salió mal
  porque AGY leyó la versión vieja de un documento: la rama era otra. Es una fuente de
  error que no existe trabajando solo.
- **`--dry-run` primero** cuando el encargo es largo: muestra el prompt compuesto sin
  gastar la corrida.

## Permisos

`agy` lee `~/.gemini/antigravity-cli/settings.json`. Al 2026-09-06 ese archivo tiene
`toolPermission: always-proceed` y `trustedWorkspaces` incluyendo `C:\`, o sea que **agy
auto-aprueba cualquier herramienta en cualquier ruta**, sin ningún flag. Eso hace
innecesario `--dangerously-skip-permissions`, y también hace que las prohibiciones del
preámbulo (no enviar por WhatsApp, no commitear) sean una **instrucción y no una barrera**.

El permiso angosto sería reemplazar esa línea por una regla
`write_file(C:\Users\bbrav\grupo-analisis-mercado)`, que concede escritura recursiva bajo
esa ruta y nada más. Decisión pendiente del director: es configuración global de la
máquina y toca todos los usos de agy, no solo este.

## Lo que queda fuera, a propósito

- **Medición de costo.** El envoltorio JSON trae `usage` y el orquestador lo imprime, pero
  no hay tarifas ni acumulado. Cuando delegar sea rutina, ahí se justifica.
- **Encargos en varios turnos.** El envoltorio trae `conversation_id` y `agy --conversation
  <id>` retoma la conversación, así que se puede iterar sobre un encargo sin volver a
  pagar la lectura del repo. No está implementado porque todavía no hizo falta.
- **El plugin `antigravity-for-claude-code`.** Da auditoría de trayectoria, medición de
  costo y comandos de barra. Se evaluó el 2026-09-06 y se descartó por ahora: su hook de
  `SessionStart` inyecta contexto en cada arranque, y en este repo ya hay dos inyecciones
  compitiendo por el mismo espacio.
