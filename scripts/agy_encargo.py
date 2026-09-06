#!/usr/bin/env python
"""Delega un encargo a Antigravity y **mide** el resultado en vez de creerlo.

punto-de-entrada: lo corre el orquestador (Claude Code) a mano al delegar trabajo
a Antigravity; no lo llama ningún otro módulo.

Existe porque delegar a mano cuesta tres cosas que se pagaron el 2026-09-06:

1. **Armar la invocación cada vez.** `-p` tiene que ir último, `--print` pierde stdout
   en un no-TTY salvo que se desengancha stdin, y el `--print-timeout` por defecto de
   5 min mata un encargo real sin escribir nada. Tres detalles que no se recuerdan y
   que cada uno cuesta una corrida entera.
2. **No saber qué pasó.** Un fallo se ve como un archivo de salida de 0 bytes, igual
   que un encargo que todavía está pensando. Y el reporte de AGY **no es evidencia**:
   puede decir SUCCESS con comandos fallidos adentro.
3. **No saber qué tocó.** El nombre de los comandos que corrió no queda registrado en
   ninguna parte, así que para atribuirle un cambio hay que **diferenciar el árbol**.

De ahí las tres cosas que este módulo hace y que ninguna documentación reemplaza:

- **Mide el ámbito.** El encargo declara qué archivos le pertenecen; el orquestador
  saca una instantánea del árbol antes y después y compara. Un archivo de más se
  reporta como fuera de ámbito, y el veredicto es negativo aunque los tests pasen.
  **Mide la ventana, no la autoría**: lo que escribas vos mientras corre también
  aparece ahí, así que el árbol es de la delegación mientras dura. No se puede medir
  mejor, porque los comandos que agy corre no quedan registrados en ninguna parte.
- **Vuelve a correr los criterios de aceptación desde acá.** Lo que AGY diga que pasó
  es un dato, no una prueba. El veredicto sale de esta corrida.
- **Nunca afirma éxito por su cuenta.** El veredicto tiene tres partes que se informan
  por separado: cómo terminó AGY, si respetó el ámbito, y si la verificación pasó.

## El encargo

Un markdown con frontmatter que declara su contrato:

    ---
    titulo: El guardrail de texto de cliente
    archivos:
      - scripts/guardrails/texto_cliente.py
      - tests/test_guardrails_texto_cliente.py
    verificar:
      - uv run ruff check scripts/guardrails/texto_cliente.py
      - uv run pytest tests/test_guardrails_texto_cliente.py -q
    ---

    (el cuerpo: qué hay que escribir, con las firmas públicas fijadas)

`archivos` y `verificar` son **obligatorios**, y ese es el punto: un encargo sin ámbito
declarado no se puede auditar, y uno sin criterio de aceptación no se puede verificar.
Falta uno y el encargo no se manda.

**Fijá las firmas públicas en el cuerpo.** Dejar que las invente es el defecto de
contratos por nombre otra vez, multiplicado por la cantidad de encargos en paralelo.

## Uso

    uv run python scripts/agy_encargo.py delegar docs/agy/encargos/x.md
    uv run python scripts/agy_encargo.py delegar docs/agy/encargos/x.md --dry-run
    uv run python scripts/agy_encargo.py verificar docs/agy/encargos/x.md
    uv run python scripts/agy_encargo.py estado

`estado` existe por el punto 2: un proceso de agy vivo consume CPU, así que **la señal
de vida es el CPU y no el tamaño del archivo de salida**, que queda en 0 bytes hasta
que termina.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

if sys.platform == "win32":
    # La consola es cp1252 y este informe lleva acentos. Es la misma regla de
    # escritura del repo, aplicada a la salida propia: sin esto el informe sale
    # con `report?` y `AMBITO`. Mismo remedio que `hook_ingesta_macro.py`.
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):  # noqa: PERF203
            pass

RAIZ = Path(__file__).resolve().parent.parent
PREAMBULO = RAIZ / "docs" / "agy" / "preambulo.md"
BITACORA = RAIZ / "data" / "logs" / "agy"

# Los niveles, contra los slugs que `agy models` lista. Se nombran por rol y no por
# modelo para que subir de versión no obligue a tocar cada encargo.
TIERS: dict[str, str] = {
    "flash": "gemini-3.8-flash-high",
    "flash-lo": "gemini-3.8-flash-low",
    "pro": "gemini-3.1-pro-high",
}

CAMPOS_OBLIGATORIOS = ("archivos", "verificar")

# Rutas gitignoreadas que igual se vigilan. `git status` no las lista, así que sin
# esto una escritura ahí es INVISIBLE para el control de ámbito, y no es hipotético:
# el 2026-09-06 un encargo escribió en la bitácora operativa de verdad pese a que el
# encargo lo prohibía, y el informe salió limpio. La lista es corta a propósito
# (2,6 MB medidos) porque estas se hashean enteras en cada instantánea; barrer todo
# lo gitignoreado costaría 95 MB por corrida y traería `.venv` de arrastre.
VIGILADAS_IGNORADAS = ("data/logs", "data/stories", "data/charts", "data/mensajes")

# Un encargo real tarda entre 5 y 8 minutos: tres módulos medidos el 2026-09-06 dieron
# 295 s, 365 s y 432 s. El techo por defecto de agy son 5 min, que corta justo en la
# mitad de la distribución.
TIMEOUT_POR_DEFECTO = "25m"


# --------------------------------------------------------------------------
# El encargo


@dataclass(frozen=True)
class Encargo:
    ruta: Path
    titulo: str
    archivos: tuple[str, ...]
    verificar: tuple[str, ...]
    cuerpo: str

    @property
    def slug(self) -> str:
        return self.ruta.stem


def leer_encargo(ruta: Path) -> tuple[Encargo | None, list[str]]:
    """Parsea un encargo. Devuelve `(None, problemas)` si no se puede mandar.

    Fail-closed y con el motivo nombrado, mismo criterio que las exclusiones del
    escáner: un encargo mal declarado se rechaza acá, que cuesta un segundo, y no
    después de siete minutos de delegación.
    """
    problemas: list[str] = []
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as err:
        return None, [f"no se pudo leer {ruta}: {err}"]

    if not texto.startswith("---"):
        return None, [f"{ruta.name} no tiene frontmatter: falta declarar archivos y verificar"]

    _, _, resto = texto.partition("---")
    crudo, sep, cuerpo = resto.partition("\n---")
    if not sep:
        return None, [f"{ruta.name} tiene el frontmatter sin cerrar"]

    try:
        meta = yaml.safe_load(crudo) or {}
    except yaml.YAMLError as err:
        return None, [f"frontmatter inválido en {ruta.name}: {err}"]
    if not isinstance(meta, dict):
        return None, [f"el frontmatter de {ruta.name} no es un mapa"]

    for campo in CAMPOS_OBLIGATORIOS:
        valor = meta.get(campo)
        if not valor or not isinstance(valor, list):
            problemas.append(
                f"falta `{campo}` (lista no vacía): "
                + (
                    "sin ámbito declarado no se puede auditar qué tocó"
                    if campo == "archivos"
                    else "sin criterio de aceptación no se puede verificar"
                )
            )
    if problemas:
        return None, problemas

    return (
        Encargo(
            ruta=ruta,
            titulo=str(meta.get("titulo") or ruta.stem),
            archivos=tuple(str(a) for a in meta["archivos"]),
            verificar=tuple(str(v) for v in meta["verificar"]),
            cuerpo=cuerpo.lstrip("\n"),
        ),
        [],
    )


def componer(encargo: Encargo) -> str:
    """El preámbulo compartido, más el ámbito explícito, más el cuerpo.

    El ámbito viaja **también en el texto** y no solo en la medición: decirle qué
    archivos le pertenecen es más barato que descubrir después que escribió en otro.
    """
    lista = "\n".join(f"- `{a}`" for a in encargo.archivos)
    verif = "\n".join(f"- `{v}`" for v in encargo.verificar)
    return (
        PREAMBULO.read_text(encoding="utf-8")
        + "\n---\n\n"
        + f"# Encargo: {encargo.titulo}\n\n"
        + "## Los únicos archivos que podés tocar\n\n"
        + f"{lista}\n\n"
        + "Cualquier otro archivo que aparezca modificado invalida el encargo entero.\n\n"
        + "## Antes de terminar, corré y dejá en verde\n\n"
        + f"{verif}\n\n---\n\n"
        + encargo.cuerpo
    )


# --------------------------------------------------------------------------
# La medición del árbol


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True
    ).stdout


def instantanea() -> dict[str, str]:
    """Huella de todo lo que el árbol tiene sucio o sin rastrear.

    **Por qué se hashea el contenido y no basta la lista.** Un archivo limpio que se
    modifica aparece en el estado después y no antes, así que la lista sola lo
    detecta. Lo que la lista NO detecta es un archivo **que ya estaba sucio** y recibe
    más cambios: su línea de estado sigue siendo la misma. Acá eso pasa siempre, porque
    la ingesta macro deja dieciséis JSON de `data central/` modificados en cada
    arranque de sesión. Sin el hash, una escritura sobre uno de esos sería invisible.

    **Y por qué se caminan además unas carpetas gitignoreadas.** `git status` no las
    lista, así que una escritura ahí no aparece en ninguna instantánea. Tampoco es
    hipotético: el 2026-09-06 un encargo escribió en `data/logs/` pese a tenerlo
    prohibido, y el informe de ámbito salió limpio.
    """
    huellas: dict[str, str] = {}
    salida = _git("status", "--porcelain", "-uall", "-z")
    for entrada in salida.split("\0"):
        if len(entrada) < 4:
            continue
        rel = entrada[3:]
        ruta = RAIZ / rel
        if not ruta.is_file():
            huellas[rel] = "(ausente)"
            continue
        try:
            huellas[rel] = hashlib.sha1(ruta.read_bytes()).hexdigest()[:12]
        except OSError:
            huellas[rel] = "(ilegible)"

    for carpeta in VIGILADAS_IGNORADAS:
        base = RAIZ / carpeta
        if not base.is_dir():
            continue
        for ruta in base.rglob("*"):
            if not ruta.is_file():
                continue
            rel = ruta.relative_to(RAIZ).as_posix()
            try:
                huellas[rel] = hashlib.sha1(ruta.read_bytes()).hexdigest()[:12]
            except OSError:
                huellas[rel] = "(ilegible)"
    return huellas


def cambios(antes: dict[str, str], despues: dict[str, str]) -> list[str]:
    """Los archivos que cambiaron entre las dos instantáneas. Función pura."""
    tocados = {
        rel for rel in set(antes) | set(despues) if antes.get(rel) != despues.get(rel)
    }
    return sorted(tocados)


def fuera_de_ambito(tocados: list[str], declarados: tuple[str, ...]) -> list[str]:
    """Lo que se tocó y el encargo no declaraba. Función pura.

    Normaliza los separadores porque este repo corre en Windows y la mitad de las
    rutas llegan con barra invertida, mientras git siempre las devuelve con barra
    normal. Comparar sin normalizar reportaría todo como fuera de ámbito.
    """
    permitidos = {d.replace("\\", "/").lstrip("./") for d in declarados}
    return [t for t in tocados if t.replace("\\", "/") not in permitidos]


# --------------------------------------------------------------------------
# La invocación y su clasificación


@dataclass
class Resultado:
    codigo: str  # "ok" | "timeout" | "auth" | "cuota" | "vacio" | "ausente" | "error"
    detalle: str
    respuesta: str = ""
    conversacion: str = ""
    segundos: float = 0.0
    uso: dict = field(default_factory=dict)


def clasificar(rc: int, stdout: str, stderr: str) -> Resultado:
    """Traduce la salida de agy a un código estable. Función pura.

    Existe porque sin esto **todo fallo se ve igual**: un archivo de salida vacío. Y
    cada código tiene una acción distinta. Confundir un timeout con un problema de
    autenticación cuesta reintentar lo que no se va a arreglar reintentando.
    """
    texto = (stdout or "").strip()
    ruido = (stderr or "").lower()

    if not texto:
        if "not found" in ruido or "no such file" in ruido:
            return Resultado("ausente", "agy no está en el PATH")
        if "timeout" in ruido:
            return Resultado("timeout", "agy no respondió dentro del plazo")
        return Resultado("vacio", f"agy salió con {rc} sin escribir nada. stderr: {ruido[:200]}")

    try:
        env = json.loads(texto.splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return Resultado("error", f"la salida no es el envoltorio JSON esperado: {texto[:200]}")

    base = {
        "respuesta": env.get("response", ""),
        "conversacion": env.get("conversation_id", ""),
        "segundos": float(env.get("duration_seconds") or 0),
        "uso": env.get("usage") or {},
    }
    if env.get("status") == "SUCCESS":
        return Resultado("ok", "agy reportó SUCCESS", **base)

    err = (env.get("error") or "").lower()
    if "quota" in err or "rate limit" in err or "resource_exhausted" in err:
        return Resultado("cuota", "cuota o límite de tasa agotado", **base)
    if "auth" in err or "sign in" in err or "credential" in err:
        return Resultado("auth", "hace falta autenticarse: corré `agy` una vez de forma interactiva", **base)
    if "timeout" in err:
        return Resultado("timeout", "agy no respondió dentro del plazo", **base)
    return Resultado("error", (env.get("error") or "agy falló sin decir por qué")[:300], **base)


def invocar(prompt: str, tier: str, timeout: str) -> Resultado:
    """Corre agy con las banderas en el orden que funciona.

    Tres detalles que cada uno costó una corrida el 2026-09-06 y que están acá para no
    volver a recordarlos: `-p` va **último** porque toma el prompt como su valor,
    stdin va desenganchado porque `--print` pierde stdout en un no-TTY, y el plazo
    sube porque el de fábrica corta en la mitad de la distribución real.
    """
    if shutil.which("agy") is None:
        return Resultado("ausente", "agy no está en el PATH")
    cmd = [
        "agy",
        "--model", TIERS[tier],
        "--mode", "accept-edits",
        "--output-format", "json",
        "--print-timeout", timeout,
        "-p", prompt,
    ]
    with open(os.devnull, "rb") as vacio:
        proc = subprocess.run(cmd, cwd=RAIZ, stdin=vacio, capture_output=True, text=True)
    return clasificar(proc.returncode, proc.stdout, proc.stderr)


# --------------------------------------------------------------------------
# La verificación, corrida desde acá


@dataclass
class Comprobacion:
    comando: str
    rc: int
    cola: str

    @property
    def ok(self) -> bool:
        return self.rc == 0


def verificar(encargo: Encargo) -> list[Comprobacion]:
    """Corre los criterios de aceptación del encargo. **Este es el veredicto.**

    Lo que AGY reporte es un dato; esto es la prueba. Sin `shell=True` a propósito:
    los comandos vienen de un archivo del repo, pero pasarlos por un shell agrega una
    capa de interpretación que no hace falta y que en Windows además cambia según cuál
    shell tome.
    """
    salida: list[Comprobacion] = []
    for comando in encargo.verificar:
        try:
            proc = subprocess.run(
                shlex.split(comando), cwd=RAIZ, capture_output=True, text=True
            )
            cola = (proc.stdout or proc.stderr).strip().splitlines()
            salida.append(Comprobacion(comando, proc.returncode, cola[-1] if cola else ""))
        except (OSError, ValueError) as err:
            salida.append(Comprobacion(comando, 127, f"no se pudo ejecutar: {err}"))
    return salida


# --------------------------------------------------------------------------
# El informe


def informar(
    encargo: Encargo,
    res: Resultado,
    tocados: list[str],
    intrusos: list[str],
    comprobaciones: list[Comprobacion],
) -> int:
    """Imprime el informe y devuelve el código de salida.

    Las tres partes del veredicto se informan **por separado**: cómo terminó AGY, si
    respetó el ámbito, y si la verificación pasó. Colapsarlas en un booleano esconde
    justo el caso interesante, que es tests en verde con un archivo de más tocado.
    """
    print(f"\n=== {encargo.titulo} ===")
    print(f"AGY        {res.codigo}: {res.detalle}")
    if res.segundos:
        u = res.uso
        print(
            f"           {res.segundos:.0f} s · entrada {u.get('input_tokens', 0):,}"
            f" · salida {u.get('output_tokens', 0):,}"
            f" · pensamiento {u.get('thinking_tokens', 0):,}"
        )
    if res.conversacion:
        print(f"           conversación {res.conversacion} (seguila con `agy --conversation`)")

    print(f"\nÁMBITO     {len(tocados)} archivo(s) cambiaron")
    for t in tocados:
        print(f"           {'FUERA' if t in intrusos else '  ok '}  {t}")
    if intrusos:
        print("\n           Fuera de ámbito. El encargo no declaraba estos archivos, y")
        print("           un cambio no declarado no se puede atribuir: revisá el diff")
        print("           antes de quedarte con nada de esta corrida.")

    print("\nVERIFICADO desde acá, no por el reporte de AGY:")
    for c in comprobaciones:
        print(f"           {'ok  ' if c.ok else 'FALLA'}  {c.comando}")
        if not c.ok:
            print(f"                  {c.cola[:160]}")

    if res.respuesta:
        print("\nREPORTE de AGY (un dato, no una prueba):")
        for linea in res.respuesta.strip().splitlines()[:8]:
            print(f"           {linea[:150]}")

    if res.codigo != "ok":
        veredicto, codigo = "la delegación falló", 3
    elif intrusos:
        veredicto, codigo = "tocó archivos fuera de ámbito", 2
    elif not all(c.ok for c in comprobaciones):
        veredicto, codigo = "la verificación no pasó", 1
    else:
        veredicto, codigo = "ámbito respetado y verificación en verde", 0

    print(f"\nVEREDICTO  {veredicto}")
    if codigo == 0:
        print("           Falta lo que ninguna herramienta puede hacer: leer el código.")
    print()
    return codigo


def ruta_relativa(ruta: Path) -> str:
    """La ruta relativa a la raiz, o la absoluta si cae afuera. No lanza.

    `Path.relative_to` levanta ValueError ante una ruta relativa, y el encargo se
    invoca casi siempre asi (`docs/agy/encargos/x.md`). Ese fallo mato la bitacora
    DESPUES de una delegacion exitosa el 2026-09-06: el trabajo estaba hecho y el
    registro se perdio. Lo ultimo que hace el orquestador no puede ser lo que se
    cae.
    """
    try:
        return str(ruta.resolve().relative_to(RAIZ))
    except ValueError:
        return str(ruta)


def anotar(encargo: Encargo, res: Resultado, tocados, intrusos, comprobaciones) -> Path:
    """Deja la bitácora en `data/logs/agy/`, que está gitignoreada.

    Es estado generado, no historia editorial, mismo criterio que
    `data/.reloj_disparos.json`. Sirve para reconstruir qué se delegó y con qué
    resultado sin depender de que el contexto de la conversación sobreviva.
    """
    BITACORA.mkdir(parents=True, exist_ok=True)
    sello = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    destino = BITACORA / f"{sello}_{encargo.slug}.json"
    destino.write_text(
        json.dumps(
            {
                "encargo": ruta_relativa(encargo.ruta),
                "titulo": encargo.titulo,
                "agy": {
                    "codigo": res.codigo,
                    "detalle": res.detalle,
                    "conversacion": res.conversacion,
                    "segundos": res.segundos,
                    "uso": res.uso,
                    "respuesta": res.respuesta,
                },
                "archivos_declarados": list(encargo.archivos),
                "archivos_tocados": tocados,
                "fuera_de_ambito": intrusos,
                "verificacion": [
                    {"comando": c.comando, "rc": c.rc, "cola": c.cola} for c in comprobaciones
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return destino


# --------------------------------------------------------------------------
# Los verbos


def cmd_delegar(args) -> int:
    encargo, problemas = leer_encargo(Path(args.encargo))
    if encargo is None:
        print(f"El encargo no se puede mandar ({len(problemas)} problema(s)):", file=sys.stderr)
        for p in problemas:
            print(f"  {p}", file=sys.stderr)
        return 4

    prompt = componer(encargo)
    if args.dry_run:
        print(f"--- prompt compuesto ({len(prompt):,} caracteres) ---")
        print(prompt)
        print(f"--- modelo: {TIERS[args.tier]} · plazo: {args.timeout} ---")
        return 0

    antes = instantanea()
    res = invocar(prompt, args.tier, args.timeout)
    despues = instantanea()

    tocados = cambios(antes, despues)
    intrusos = fuera_de_ambito(tocados, encargo.archivos)
    comprobaciones = verificar(encargo) if res.codigo == "ok" else []

    codigo = informar(encargo, res, tocados, intrusos, comprobaciones)
    print(f"           bitácora: {anotar(encargo, res, tocados, intrusos, comprobaciones)}")
    return codigo


def cmd_verificar(args) -> int:
    """Corre solo los criterios de aceptación, sin delegar nada.

    Sirve después de arreglar algo a mano, y sirve para saber si el encargo declara
    criterios que de verdad corren antes de gastar siete minutos de delegación.
    """
    encargo, problemas = leer_encargo(Path(args.encargo))
    if encargo is None:
        for p in problemas:
            print(f"  {p}", file=sys.stderr)
        return 4
    comprobaciones = verificar(encargo)
    for c in comprobaciones:
        print(f"{'ok  ' if c.ok else 'FALLA'}  {c.comando}")
        if not c.ok:
            print(f"        {c.cola[:160]}")
    return 0 if all(c.ok for c in comprobaciones) else 1


def cmd_estado(args) -> int:
    """Qué procesos de agy están vivos, y las últimas delegaciones.

    **La señal de vida es el CPU, no el tamaño del archivo de salida.** agy escribe el
    envoltorio JSON recién al terminar, así que una salida de 0 bytes se ve igual en un
    encargo que está pensando y en uno colgado. Confundirlos costó tiempo el
    2026-09-06.
    """
    if sys.platform == "win32":
        ps = (
            "Get-Process agy -ErrorAction SilentlyContinue | "
            "Select-Object Id,@{n='CPU_s';e={[math]::Round($_.CPU,1)}},"
            "@{n='MB';e={[math]::Round($_.WorkingSet64/1MB)}},StartTime | Format-Table -AutoSize"
        )
        salida = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True
        ).stdout.strip()
    else:
        salida = subprocess.run(
            ["ps", "-o", "pid,time,rss,command", "-C", "agy"], capture_output=True, text=True
        ).stdout.strip()

    print("=== procesos de agy vivos (CPU creciendo = trabajando) ===")
    print(salida or "  ninguno")

    print("\n=== últimas delegaciones ===")
    if not BITACORA.is_dir():
        print("  sin bitácora todavía")
        return 0
    for archivo in sorted(BITACORA.glob("*.json"), reverse=True)[:5]:
        try:
            d = json.loads(archivo.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        fuera = len(d.get("fuera_de_ambito") or [])
        fallas = sum(1 for v in d.get("verificacion") or [] if v.get("rc"))
        print(
            f"  {archivo.stem:44s} agy={d['agy']['codigo']:8s}"
            f" fuera={fuera} fallas={fallas}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="verbo", required=True)

    d = sub.add_parser("delegar", help="manda un encargo y mide el resultado")
    d.add_argument("encargo", help="ruta al markdown del encargo")
    d.add_argument("--tier", choices=sorted(TIERS), default="flash")
    d.add_argument("--timeout", default=TIMEOUT_POR_DEFECTO)
    d.add_argument("--dry-run", action="store_true", help="compone el prompt y no delega")
    d.set_defaults(fn=cmd_delegar)

    v = sub.add_parser("verificar", help="corre solo los criterios de aceptación")
    v.add_argument("encargo")
    v.set_defaults(fn=cmd_verificar)

    e = sub.add_parser("estado", help="procesos vivos y últimas delegaciones")
    e.set_defaults(fn=cmd_estado)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
