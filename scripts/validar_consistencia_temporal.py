#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validar_consistencia_temporal.py
Guardrail profundo de consistencia temporal y anti-anacronismos.

Verifica:
1. Coherencia de fecha: El reloj del sistema en hora de Chile (America/Santiago) debe coincidir
   con la fecha informada en el documento, cabeceras y parámetros.
2. Anti-anacronismo semántico: Detecta y bloquea afirmaciones en tiempo pasado ("tras el discurso",
   "asimilación de", "luego del dato") sobre eventos macroeconómicos futuros que aún no han ocurrido.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SANTIAGO = ZoneInfo("America/Santiago")

# Patrones de conectores y verbos en pasado que indican que el evento ya ocurrió
PATRONES_PASADO = [
    r"\btras\s+(?:el|la|los|las)?\s*",
    r"\bluego\s+de\s+(?:el|la|los|las)?\s*",
    r"\bdespu[eé]s\s+de\s+(?:el|la|los|las)?\s*",
    r"\basimilaci[oó]n\s+de\s+(?:el|la|los|las)?\s*",
    r"\basimilad[oa]s?\s+por\b",
    r"\bincorporad[oa]s?\s+por\b",
    r"\breaccion[oó]\s+a\b",
    r"\btras\s+haber\s+conocido\b",
    r"\bposterior\s+a\s+(?:el|la|los|las)?\s*",
    r"\btras\s+conocerse\b",
]

# Eventos macro sensibles que requieren validación estricta de tiempo
EVENTOS_FUTUROS_CLAVE = [
    (r"simposio de jackson hole", "Jackson Hole"),
    (r"discursos? (?:de|del)?\s*jackson hole", "Discursos de Jackson Hole"),
    (r"deflactor pce", "Deflactor PCE de EE.UU."),
    (r"nfp\b", "Nóminas No Agrícolas (NFP)"),
    (r"informe de empleo", "Informe de Empleo"),
    (r"ipc de tokyo", "IPC de Tokio"),
    (r"decisi[oó]n de tasas de la fed", "Decisión Fed"),
    (r"reuni[oó]n del fomc", "Reunión FOMC"),
]

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

DIAS_SEMANA_ES = {
    0: "lunes", 1: "martes", 2: "miércoles", 3: "jueves",
    4: "viernes", 5: "sábado", 6: "domingo"
}


class TemporalConsistencyError(ValueError):
    """Excepción levantada cuando se detecta una inconsistencia de fecha o un anacronismo."""
    pass


def obtener_ahora_chile() -> datetime:
    """Retorna la fecha y hora actual en Santiago de Chile."""
    return datetime.now(tz=SANTIAGO)


def validar_fecha_documento(
    fecha_declarada: str | None = None,
    ahora: datetime | None = None,
    tolerancia_dias: int = 0
) -> bool:
    """
    Verifica que la fecha declarada sea coherente con la fecha real en Chile.
    fecha_declarada puede ser 'YYYY-MM-DD' o 'DD de mes de YYYY'.
    """
    if ahora is None:
        ahora = obtener_ahora_chile()

    if not fecha_declarada:
        return True

    fecha_norm = fecha_declarada.lower().strip()
    dia_actual = ahora.day
    mes_actual_str = MESES_ES[ahora.month]
    anio_actual = ahora.year
    fecha_iso_actual = ahora.strftime("%Y-%m-%d")

    # Caso 1: Formato ISO YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_norm):
        if fecha_norm != fecha_iso_actual:
            raise TemporalConsistencyError(
                f"Error de Fecha: El documento indica '{fecha_declarada}', pero en Chile la fecha real es '{fecha_iso_actual}'."
            )
        return True

    # Caso 2: Formato texto '28 de agosto de 2026'
    match_texto = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)(?:\s+de\s+(\d{4}))?", fecha_norm)
    if match_texto:
        dia_doc = int(match_texto.group(1))
        mes_doc = match_texto.group(2)
        anio_doc = int(match_texto.group(3)) if match_texto.group(3) else anio_actual

        if dia_doc != dia_actual or mes_doc != mes_actual_str or anio_doc != anio_actual:
            raise TemporalConsistencyError(
                f"Error de Fecha: El texto declara '{dia_doc} de {mes_doc} de {anio_doc}', pero hoy en Chile es '{dia_actual} de {mes_actual_str} de {anio_actual}'."
            )

    return True


def auditar_anacronismos_texto(
    texto: str,
    eventos_futuros_agendados: list[str] | None = None
) -> list[str]:
    """
    Escanea el texto en busca de construcciones gramaticales en pasado
    referidas a eventos futuros conocidos o agendados.
    Retorna lista de alertas encontradas.
    """
    alertas: list[str] = []
    texto_limpio = texto.lower()

    eventos = list(EVENTOS_FUTUROS_CLAVE)
    if eventos_futuros_agendados:
        for ev in eventos_futuros_agendados:
            eventos.append((re.escape(ev.lower()), ev))

    for patron_pasado in PATRONES_PASADO:
        for regex_evento, nombre_evento in eventos:
            # Busca si el conector de pasado está inmediatamente antes del evento
            patron_completo = rf"{patron_pasado}(?:[\w\s]{{0,30}}?){regex_evento}"
            coincidencias = re.findall(patron_completo, texto_limpio)
            if coincidencias:
                for c in coincidencias:
                    alertas.append(
                        f"Anacronismo detectado: Redacción en tiempo pasado ('{c.strip()}') sobre evento futuro '{nombre_evento}'."
                    )

    return alertas


def validar_archivo_markdown(
    ruta_md: str | Path,
    fecha_param: str | None = None,
    estricto: bool = True
) -> bool:
    """
    Valida un archivo markdown completo antes del renderizado.
    """
    path = Path(ruta_md)
    if not path.exists():
        raise FileNotFoundError(f"Archivo markdown no encontrado: {path}")

    contenido = path.read_text(encoding="utf-8")
    ahora = obtener_ahora_chile()

    # 1. Validar fecha
    if fecha_param:
        validar_fecha_documento(fecha_param, ahora=ahora)

    # 2. Auditar anacronismos
    alertas = auditar_anacronismos_texto(contenido)
    if alertas:
        msj = "\n".join([f"  • {a}" for a in alertas])
        if estricto:
            raise TemporalConsistencyError(
                f"Fallo de Guardrail de Consistencia Temporal en '{path.name}':\n{msj}\n"
                "Solución: Reescribe el evento en modo anticipación ('de cara a...', 'a la espera de...') en lugar de darlo por ocurrido."
            )
        else:
            print(f"[ADVERTENCIA TEMPORAL] en {path.name}:\n{msj}", file=sys.stderr)

    return True


def main():
    parser = argparse.ArgumentParser(description="Validador de Consistencia Temporal y Anti-Anacronismos GI")
    parser.add_argument("--md", help="Ruta al archivo Markdown a validar", required=False)
    parser.add_argument("--fecha", help="Fecha declarada (YYYY-MM-DD o 'DD de mes de YYYY')", required=False)
    parser.add_argument("--check-now", action="store_true", help="Imprime la hora canónica de Chile actual")
    parser.add_argument("--no-strict", action="store_true", help="Modo advertencia (no lanza error 1)")

    args = parser.parse_args()

    ahora = obtener_ahora_chile()
    dia_semana = DIAS_SEMANA_ES[ahora.weekday()]
    mes_str = MESES_ES[ahora.month]

    if args.check_now:
        print(f"[RELOJ CANÓNICO CHILE] {dia_semana.capitalize()} {ahora.day} de {mes_str} de {ahora.year} - {ahora.strftime('%H:%M:%S')} CLT")
        return

    if args.fecha:
        try:
            validar_fecha_documento(args.fecha, ahora=ahora)
            print(f"[OK] Fecha '{args.fecha}' es consistente con hoy en Chile ({dia_semana} {ahora.day} de {mes_str} de {ahora.year}).")
        except TemporalConsistencyError as e:
            print(f"[ERROR TEMPORAL] {e}", file=sys.stderr)
            sys.exit(1)

    if args.md:
        try:
            validar_archivo_markdown(args.md, fecha_param=args.fecha, estricto=not args.no_strict)
            print(f"[OK] Documento '{args.md}' validado: Cero anacronismos y fecha coherente.")
        except TemporalConsistencyError as e:
            print(f"[ERROR TEMPORAL] {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
