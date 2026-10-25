---
titulo: Catálogo de motivos y banco de imágenes ilustrativas del correo
archivos:
  - config/motivos_imagen.json
  - scripts/analista/ilustracion.py
  - tests/test_analista_ilustracion.py
  - .gitignore
verificar:
  - uv run ruff check scripts/analista/ilustracion.py tests/test_analista_ilustracion.py
  - uv run pytest tests/test_analista_ilustracion.py -q
---

El correo de `/oportunidad` abre con una noticia acompañada **siempre** de una imagen ilustrativa
(spec `docs/superpowers/specs/2026-10-24-correo-noticia-de-apertura-design.md` §2; léelo). Las
imágenes se guardan en un banco por motivo y se reutilizan; agy genera una nueva solo cuando falta.
Escribe el catálogo, el módulo y sus tests. **No toques ningún otro archivo.** No generes imágenes
reales: en los tests el generador es un doble.

Trabaja en este orden: primero `tests/test_analista_ilustracion.py`, córrelo y comprueba que falla
porque el módulo no existe; después el módulo; después vuelve a correrlo.

## 1. `config/motivos_imagen.json`

```json
{
  "_nota": "Catálogo cerrado de motivos de las imágenes ilustrativas del correo (spec 2026-10-24 §2). Lo edita el director.",
  "prohibiciones": "Sin logos, sin marcas, sin texto ni números legibles, sin banderas, sin sellos de país, sin personas reconocibles; fotografía sobria, luz cálida, formato horizontal 16:9.",
  "motivos": {
    "<id>": {"descripcion": "<para qué noticias sirve>", "prompt": "<descripción de la escena, una o dos frases>"}
  }
}
```

Los ids son exactamente estos nueve: `oro_lingotes`, `banco_central` (edificio genérico con columnas,
sin nombre ni bandera), `billetes_dolar` (billetes de dólar sin números de serie legibles),
`peso_chileno` (monedas y billetes genéricos de tonos chilenos, sin escudo ni texto legible), `cobre`
(cátodos o bobinas de cobre), `petroleo` (barriles o refinería genérica), `bolsa_pantallas`
(pantallas con gráficos de velas desenfocados, sin cifras legibles), `tecnologia` (chips o
servidores), `acciones_generico` (sala de operaciones desenfocada, sin personas reconocibles).
Ningún prompt nombra una marca, una empresa, un país ni pide texto. El JSON se escribe en UTF-8.

## 2. `scripts/analista/ilustracion.py`

Firmas fijas (no las cambies; otros módulos ya las usan por nombre):

```python
from analista import RAIZ
from analista.generador_imagen import Generador, ImagenNoGenerada

CONFIG = RAIZ / "config" / "motivos_imagen.json"
BANCO = RAIZ / "data" / "imagenes_ilustrativas"
COOLDOWN_DIAS = 7

def motivos(ruta: Path = CONFIG) -> dict[str, dict[str, str]]: ...
def prompt_de(motivo: str, ruta: Path = CONFIG) -> str: ...
def elegir(motivo: str, hoy: date, generar: Generador | None, banco: Path = BANCO,
           ahora: datetime | None = None) -> tuple[Path | None, str | None]: ...
```

- `motivos` devuelve el dict `motivos` del JSON.
- `prompt_de` devuelve `prompt + " " + prohibiciones`; `KeyError` si el motivo no está.
- `elegir` devuelve `(ruta, aviso)`, en este orden de preferencia:
  1. Una imagen de `banco/<motivo>/` (`*.png`, `*.jpg`) **sin uso en los últimos `COOLDOWN_DIAS`
     días**, o nunca usada. Entre varias, la de uso más antiguo (las nunca usadas primero).
     `aviso = None`.
  2. Si no hay y `generar` no es `None`: `generar(prompt_de(motivo), banco / motivo / f"{ahora:%Y%m%d-%H%M%S}.png")`.
     `ahora` por defecto es `datetime.now()`. `aviso = None`.
  3. Si `generar` levanta `ImagenNoGenerada` (o es `None` y no hubo 1): la imagen del motivo de uso
     más antiguo aunque esté en cooldown, con `aviso` que diga que se repitió una imagen reciente.
  4. Si el motivo no tiene ninguna imagen: `(None, aviso)` con un aviso que diga que la noticia sale
     sin imagen.
- El uso vive en `banco / "uso.json"`: `{"<motivo>/<archivo>": "AAAA-MM-DD"}`. Cada vez que `elegir`
  devuelve una ruta, anota `hoy` para esa imagen. Escribir con
  `Path.write_text(json.dumps(..., ensure_ascii=False, indent=2), encoding="utf-8")`. Un `uso.json`
  ausente o ilegible cuenta como vacío.
- Un motivo fuera del catálogo levanta `KeyError` (lo hace `prompt_de`, pero `elegir` también lo
  verifica antes de mirar el banco).
- Docstring del módulo en español, breve, con el porqué (mira el estilo de
  `scripts/analista/generador_imagen.py`).

## 3. `.gitignore`

Agrega una línea `data/imagenes_ilustrativas/` con un comentario de una línea: son imágenes
generadas que se rehacen solas.

## 4. Tests (`tests/test_analista_ilustracion.py`)

Importa como `tests/test_analista_generador_imagen.py` (agrega `src/` y `scripts/` a `sys.path`).
Usa `tmp_path` como banco y PNG falsos (`b"\x89PNG\r\n\x1a\n" + b"\x00" * 64`). Tests mínimos, con
estos nombres:

- `test_prompt_lleva_las_prohibiciones`: `"Sin logos" in prompt_de("oro_lingotes")`.
- `test_motivo_desconocido_levanta`: `prompt_de("bandera_chile")` y `elegir("bandera_chile", ...)` levantan `KeyError`.
- `test_catalogo_tiene_los_nueve_motivos`: el conjunto de ids es exactamente el de arriba.
- `test_ningun_prompt_pide_marca_ni_texto`: ningún prompt contiene "logo de", "marca de", "texto que diga", "bandera de".
- `test_elige_una_sin_uso_reciente`: `a.png` usada hace 2 días, `b.png` hace 9 → devuelve `b.png`, aviso `None`, y `uso.json` queda con `b.png` en `hoy`.
- `test_prefiere_la_nunca_usada`: `a.png` usada hace 9 días y `c.png` sin uso → `c.png`.
- `test_genera_si_todas_estan_en_cooldown`: las dos usadas hace 1 día, `generar` doble que escribe un PNG en la ruta que recibe → devuelve esa ruta nueva, dentro de `banco/oro_lingotes/`, y el doble recibió un prompt con "Sin logos".
- `test_si_falla_la_generacion_usa_la_mas_antigua`: `generar` levanta `ImagenNoGenerada` → devuelve la de uso más antiguo y un aviso no vacío.
- `test_sin_banco_ni_generador_devuelve_none`: banco vacío, `generar=None` → `(None, aviso)` con aviso no vacío.
- `test_uso_ilegible_cuenta_como_vacio`: `uso.json` con `"{roto"` → elige sin levantar.

## Reporte

Responde con la lista de archivos tocados y la salida de los dos comandos de `verificar`.
