"""Genera los workflows de Antigravity (AGY) que apuntan a los comandos del repo.

Antigravity ejecuta comandos como *workflows*: archivos markdown en
`.agents/workflows/` que se invocan con `/nombre`, igual que los slash commands
de Claude Code. Pero son dos runners distintos leyendo dos carpetas distintas, y
el mismo comando en dos archivos es el problema que ya conocemos: a la segunda
copia, una queda atrás y nadie se entera hasta que una pieza sale mal.

Por eso cada workflow es un PUNTERO de pocas líneas al comando canónico de
`.claude/commands/`, no una copia. La definición vive en un solo lugar y AGY la
lee de ahí.

Hay además una razón dura: **Antigravity limita cada workflow a 12.000
caracteres**. `story.md` tiene más de 43.000, y `dato_macro.md` y `apertura.md`
pasan de 14.000. Copiarlos es imposible, no solo indeseable.

    uv run python scripts/agy_workflows.py            # genera
    uv run python scripts/agy_workflows.py --check    # verifica, no escribe

El `--check` falla si falta un workflow, si quedó desactualizado o si alguno se
pasó del límite. Es lo que mantiene a AGY a la par cuando se toca un comando.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_COMANDOS = RAIZ / ".claude" / "commands"
DIR_WORKFLOWS = RAIZ / ".agents" / "workflows"

# Tope de Antigravity por archivo de workflow. Un puntero pesa ~1 KB, así que el
# margen es enorme — la constante está para que el --check lo verifique en vez de
# confiar en que sigue siendo así.
LIMITE_CARACTERES = 12_000

# Los comandos expuestos a AGY, con la línea que lo describe en el listado de
# `/`. El alcance es deliberado: las piezas visuales y los datos que las
# alimentan. Los comandos de día, los educativos y los internos siguen siendo de
# Claude Code hasta que haya una razón para moverlos.
#
# Para exponer uno nuevo: agregarlo acá y correr el script. No crear el archivo
# a mano — el --check lo marcaría como desactualizado.
COMANDOS = {
"story": "Genera una Story de marca GI a partir de una plantilla (dato_macro, alerta, recomendacion, quote, breaking, encuesta, edu, flash, postventa).",
    "oportunidad": "Genera la pieza que invita a operar: imagen más mensaje de WhatsApp. No es una señal: sin entrada, TP ni SL.",
    "alerta": "Detecta qué está moviendo el mercado ahora y genera la alerta urgente para el grupo.",
    "carrusel": "Carrusel de una tanda diaria: el escáner elige el Top 3 del universo con el Score_GI, y el comando escribe el texto y rinde las Stories.",
    "informe": "Informe de la jornada: PDF institucional en la apertura, mensaje con gráfico al cierre.",
    "dato_macro": "Lista los datos económicos del día y arma la pieza del que elija el director, en modo anticipación o resultado.",
    "apertura": "Niveles técnicos del día: pregunta activo, temporalidad e indicador, y arma el mensaje de apertura.",
    "chart": "Genera un screenshot de MT5 con el indicador y la temporalidad elegidos.",
    "accion": "Ejecuta el comando accion de la misma forma que Claude Code.",
    "actualizacion": "Ejecuta el comando actualizacion de la misma forma que Claude Code.",
    "concepto": "Ejecuta el comando concepto de la misma forma que Claude Code.",
    "curriculo": "Ejecuta el comando curriculo de la misma forma que Claude Code.",
    "domingo": "Ejecuta el comando domingo de la misma forma que Claude Code.",
    "earnings": "Ejecuta el comando earnings de la misma forma que Claude Code.",
    "encuesta": "Ejecuta el comando encuesta de la misma forma que Claude Code.",
    "estado": "Ejecuta el comando estado de la misma forma que Claude Code.",
    "jueves": "Ejecuta el comando jueves de la misma forma que Claude Code.",
    "lunes": "Ejecuta el comando lunes de la misma forma que Claude Code.",
    "martes": "Ejecuta el comando martes de la misma forma que Claude Code.",
    "miercoles": "Ejecuta el comando miercoles de la misma forma que Claude Code.",
    "noticia": "Ejecuta el comando noticia de la misma forma que Claude Code.",
    "postventa": "Ejecuta el comando postventa de la misma forma que Claude Code.",
    "pregunta": "Ejecuta el comando pregunta de la misma forma que Claude Code.",
    "rencuesta": "Ejecuta el comando rencuesta de la misma forma que Claude Code.",
    "respuesta": "Ejecuta el comando respuesta de la misma forma que Claude Code.",
    "señal": "Ejecuta el comando señal de la misma forma que Claude Code.",
    "ventas": "Ejecuta el comando ventas de la misma forma que Claude Code.",
    "viernes_am": "Ejecuta el comando viernes_am de la misma forma que Claude Code.",
    "viernes_pm": "Ejecuta el comando viernes_pm de la misma forma que Claude Code.",
}

PLANTILLA = """# /{nombre}

{descripcion}

## Cómo ejecutar este comando

1. Lee `.agents/rules/proyecto.md`. Son las reglas del proyecto que aplican a
   toda pieza: tono, decimales, hora de Chile y flujo de aprobación.
2. Lee `.claude/commands/{nombre}.md` **completo**. Ese archivo es la definición
   canónica de este comando y manda sobre cualquier resumen, incluido este.
3. Ejecuta sus pasos tal como están escritos, sin saltarte ninguno.

## Los argumentos

`.claude/commands/{nombre}.md` está escrito para otro runner y espera sus
argumentos en un marcador llamado `$ARGUMENTS`. Acá **ese marcador no se
sustituye solo**: los argumentos son lo que el director escribió después de
`/{nombre}` en su mensaje.

Antes de seguir los pasos del comando, toma ese texto y úsalo en todos los
lugares donde el archivo diga `$ARGUMENTS`. Si el director no escribió nada
después del comando, trata `$ARGUMENTS` como vacío — el propio comando define
qué hacer en ese caso, y normalmente es preguntarle al director en vez de
elegir por él.

Nunca inventes un argumento que no te dieron. En este proyecto elegir el activo
o el tipo de pieza por cuenta propia es decidir qué se le manda al cliente.

## Los datos

Si el comando pide datos de mercado, salen del MCP `market-data`; si pide la
hora, del reloj del sistema. Nunca los inventes ni los busques en la web — esas
dos reglas están en el archivo de reglas y valen también acá.

---
<!-- Generado por scripts/agy_workflows.py. No editar a mano: el próximo
     `--check` lo marcaría como desactualizado. Para cambiar lo que hace el
     comando, se edita `.claude/commands/{nombre}.md`. -->
"""


def _contenido(nombre: str, descripcion: str) -> str:
    return PLANTILLA.format(nombre=nombre, descripcion=descripcion)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="no escribe; falla si algún workflow falta o quedó desactualizado",
    )
    args = parser.parse_args(argv)

    problemas = 0
    DIR_WORKFLOWS.mkdir(parents=True, exist_ok=True)

    for nombre, descripcion in sorted(COMANDOS.items()):
        comando = DIR_COMANDOS / f"{nombre}.md"
        if not comando.exists():
            print(f"FALLA {nombre}: no existe {comando.relative_to(RAIZ)}", file=sys.stderr)
            problemas += 1
            continue

        destino = DIR_WORKFLOWS / f"{nombre}.md"
        esperado = _contenido(nombre, descripcion)

        if len(esperado) > LIMITE_CARACTERES:
            print(
                f"FALLA {nombre}: el workflow pesa {len(esperado)} caracteres y el "
                f"límite de Antigravity es {LIMITE_CARACTERES}",
                file=sys.stderr,
            )
            problemas += 1
            continue

        actual = destino.read_text(encoding="utf-8") if destino.exists() else None

        if args.check:
            if actual is None:
                print(f"FALLA {nombre}: falta .agents/workflows/{nombre}.md")
                problemas += 1
            elif actual != esperado:
                print(f"FALLA {nombre}: el workflow quedó desactualizado")
                problemas += 1
            else:
                print(f"ok    {nombre}")
            continue

        if actual == esperado:
            print(f"--    {nombre}: sin cambios")
        else:
            destino.write_text(esperado, encoding="utf-8")
            print(f"ok    {nombre}: escrito")

    # Un workflow que ya no corresponde a ningún comando expuesto queda huérfano y
    # AGY lo seguiría ofreciendo en el listado de `/`.
    sobrantes = sorted(
        p.name for p in DIR_WORKFLOWS.glob("*.md") if p.stem not in COMANDOS
    )
    if sobrantes:
        print(f"FALLA: workflows sin comando en COMANDOS -> {sobrantes}", file=sys.stderr)
        problemas += 1

    if problemas:
        print(
            f"\n{problemas} problema(s). Corre `uv run python scripts/agy_workflows.py` "
            "para regenerar.",
            file=sys.stderr,
        )
        return 1

    print(f"\n{len(COMANDOS)} workflow(s) de AGY al día en .agents/workflows/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
