---
titulo: Los tests que le faltan al hook de ingesta macro
archivos:
  - tests/test_hook_ingesta_macro.py
verificar:
  - uv run ruff check tests/test_hook_ingesta_macro.py
  - uv run pytest tests/test_hook_ingesta_macro.py -q
---

`scripts/hook_ingesta_macro.py` corre en **cada arranque de sesión** de Claude Code y no
tiene ni un test. Escribí `tests/test_hook_ingesta_macro.py`.

**No modifiques el módulo.** Si encontrás un defecto, escribí el test que lo demuestra
marcado con `@pytest.mark.xfail(reason="...")` y nombralo en tu reporte. Cambiar el módulo
para que el test pase es la forma más rápida de perder el hallazgo.

## Cómo importar el módulo bajo prueba

Está en `scripts/`, no es un paquete instalado. Mirá cómo lo resuelven
`tests/test_huerfanos.py` o cualquier otro test del repo que importe algo de `scripts/`, y
copiá ese patrón.

## Qué tiene que quedar cubierto

**`antiguedad_horas` y `esta_vencida`** son el corazón: el umbral de 6 h decide si se
dispara la ingesta, y **los dos modos del hook consultan la misma función**. Que sea una
sola es justamente lo que impide que el contexto afirme que el dato está fresco mientras el
otro modo lo está bajando. Cubrí: estado ausente, estado sin la marca de tiempo, marca
ilegible, justo por debajo del umbral, justo por encima, y exactamente en el umbral (mirá
el código para ver de qué lado cae, y escribí el test que refleja lo que hace, no lo que te
parece que debería hacer).

**`esta_vencida` con estado `None` tiene que devolver `True`.** Es fail-closed: si no
sabemos cuándo fue la última ingesta, se refresca. Escribí el test que lo fija, porque
invertirlo dejaría al sistema sin refrescar nunca en un clon nuevo.

**`lock_vigente`** decide si hay otra ingesta corriendo. Cubrí: sin archivo de lock, lock
recién creado (vigente), y lock más viejo que `LOCK_HUERFANO_MIN` (se ignora). Ese último
es el que importa: un proceso que murió sin limpiar el lock no puede dejar la ingesta
bloqueada para siempre. Usá `tmp_path` y parcheá la constante del módulo con
`monkeypatch.setattr`; **no escribas en `data/`**.

**`hora_chile`** convierte la marca UTC a hora de Chile. Cubrí una marca válida y una
inválida. Una entrada basura **no puede lanzar**: el hook nunca aborta la sesión.

**`texto_estado`** arma lo que se inyecta al contexto. Verificá que nombre las fuentes con
su status, que diga la antigüedad, y sobre todo que **cuando está vencida avise que los
datos van a cambiar durante la sesión**: citar una cifra leída antes del refresco es
publicar el dato de anoche con fecha de hoy, y ese aviso es la única defensa.

**`modo_estado`** imprime el envoltorio que Claude Code consume. Verificá que la salida sea
JSON parseable y que el contexto viaje **anidado** en
`hookSpecificOutput.additionalContext`: en la raíz se ignora en silencio, que es
exactamente la clase de fallo invisible que este repo pelea. Y que devuelva 0 **siempre**,
incluso con el archivo de estado ausente o corrupto: un fallo de red del BCCh no puede
impedir abrir Claude Code.

## Lo que NO tenés que hacer

- **No corras la ingesta de verdad** ni `pipeline_ingesta.py`: tarda ~55 s y golpea las
  APIs de bancos centrales. Todo lo que toque la red o subprocesos va parcheado.
- **No escribas en `data/` ni en `data central/`.** Usá `tmp_path` y `monkeypatch`.
- No cubras `modo_refrescar` end to end por la misma razón; alcanza con verificar que no
  lanza el pipeline cuando la ingesta está fresca.
