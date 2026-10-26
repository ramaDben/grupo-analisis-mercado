"""Catálogo cerrado y banco de imágenes ilustrativas para el correo de oportunidad.

Cada correo abre con una noticia de apertura acompañada siempre de una imagen ilustrativa sobria
(spec 2026-10-24 §2). Para evitar costo y demoras de generación en cada despacho y asegurar variedad
visual, las imágenes se reutilizan rotándolas con un periodo de enfriamiento de 7 días. agy genera una
por variante del motivo y nada más: con el banco completo, otra generación solo repetiría una foto que ya
existe (las seis fachadas idénticas del 2026-10-26), así que rota la de uso más antiguo.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista.generador_imagen import Generador, ImagenNoGenerada

CONFIG = RAIZ / "config" / "motivos_imagen.json"
BANCO = RAIZ / "data" / "imagenes_ilustrativas"
COOLDOWN_DIAS = 7


def _catalogo(ruta: Path = CONFIG) -> dict[str, Any]:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def motivos(ruta: Path = CONFIG) -> dict[str, dict[str, Any]]:
    """Devuelve el diccionario de motivos del catálogo cerrado."""
    return _catalogo(ruta).get("motivos", {})


def estilo(ruta: Path = CONFIG) -> str:
    """El estilo de marca que llevan todas las imágenes: el de las fotos de las Stories."""
    return _catalogo(ruta).get("estilo", "")


def prompt_de(motivo: str, variante: int = 0, ruta: Path = CONFIG) -> str:
    """La variante del motivo con el estilo de marca y las prohibiciones fijas (neutralidad legal y de marca)."""
    datos = _catalogo(ruta)
    catalogo = datos.get("motivos", {})
    if motivo not in catalogo:
        raise KeyError(f"Motivo no encontrado en el catálogo: {motivo}")
    variantes = catalogo[motivo]["variantes"]
    return " ".join(x for x in (variantes[variante % len(variantes)], datos.get("estilo", ""),
                                datos.get("prohibiciones", "")) if x)


def motivo_para(motivo: str, ticker: str, ruta: Path = CONFIG) -> str:
    """El motivo que acompaña al activo: la materia prima de otro activo se cambia por la del activo.

    El motivo lo elige agy, y el 2026-10-26 una noticia de plata salió con lingotes de oro. Un motivo
    con `activos` solo vale para esos tickers; los demás (el banco central, el dólar) valen para todos.
    """
    datos = _catalogo(ruta)
    catalogo = datos.get("motivos", {})
    duenos = catalogo.get(motivo, {}).get("activos")
    if not duenos or ticker in duenos:
        return motivo
    propio = next((m for m, info in catalogo.items() if ticker in info.get("activos", ())), None)
    return propio or datos.get("respaldo", "banco_central")


def _imagenes(dir_motivo: Path) -> list[Path]:
    if not dir_motivo.is_dir():
        return []
    return [p for p in sorted(dir_motivo.iterdir()) if p.is_file() and p.suffix.lower() in (".png", ".jpg")]


def _sin_imagen(dir_motivo: Path, variantes: int) -> list[int]:
    """Las variantes sin su `v{i}.png`. Se leen del nombre y no de la cantidad de archivos: si la v1
    falló y la v2 no, contar volvería a generar la v2 y la v1 no existiría nunca."""
    presentes = {p.stem for p in _imagenes(dir_motivo)}
    return [i for i in range(variantes) if f"v{i}" not in presentes]


def faltantes(banco: Path = BANCO) -> list[tuple[str, int]]:
    """Las variantes de cada motivo que todavía no tienen imagen en el banco, en orden."""
    return [(m, i) for m, info in motivos().items()
            for i in _sin_imagen(Path(banco) / m, len(info["variantes"]))]


def _leer_usos(uso_path: Path) -> dict[str, str]:
    """Lee el registro de uso; si está ausente o dañado asume banco sin uso previo para no bloquear el correo."""
    if not uso_path.exists():
        return {}
    try:
        contenido = json.loads(uso_path.read_text(encoding="utf-8"))
        return contenido if isinstance(contenido, dict) else {}
    except Exception:
        return {}


def _guardar_uso(uso_path: Path, usos: dict[str, str], clave: str, hoy: date) -> None:
    """Registra la fecha de despacho para mantener el enfriamiento de 7 días entre repeticiones."""
    usos[clave] = hoy.isoformat()
    uso_path.parent.mkdir(parents=True, exist_ok=True)
    uso_path.write_text(json.dumps(usos, ensure_ascii=False, indent=2), encoding="utf-8")


def elegir(
    motivo: str,
    hoy: date,
    generar: Generador | None,
    banco: Path = BANCO,
    ahora: datetime | None = None,
) -> tuple[Path | None, str | None]:
    """Elige o genera una imagen ilustrativa para la noticia del correo según la rotación del banco.

    `ahora` queda por compatibilidad: la imagen generada se nombra por su variante (`v{i}.png`).
    """
    # Valida existencia en catálogo antes de interactuar con disco para fallar de inmediato si es desconocido
    prompt_de(motivo)
    variantes = len(motivos()[motivo]["variantes"])

    banco = Path(banco)
    uso_path = banco / "uso.json"
    usos = _leer_usos(uso_path)

    dir_motivo = banco / motivo
    imagenes = _imagenes(dir_motivo)

    def fecha_de_uso(p: Path) -> date | None:
        clave = f"{motivo}/{p.name}"
        f_str = usos.get(clave)
        if f_str:
            try:
                return date.fromisoformat(f_str)
            except ValueError:
                return None
        return None

    # 1. Buscar imagen sin uso en los últimos COOLDOWN_DIAS días o nunca usada (las nunca usadas primero)
    disponibles: list[tuple[int, date, Path]] = []
    for p in imagenes:
        f_uso = fecha_de_uso(p)
        if f_uso is None:
            # Nunca usada: máxima prioridad (0), con fecha mínima y nombre determinista
            disponibles.append((0, date.min, p))
        elif (hoy - f_uso) >= timedelta(days=COOLDOWN_DIAS):
            # Fuera de cooldown: prioridad 1, fecha más antigua primero
            disponibles.append((1, f_uso, p))

    if disponibles:
        disponibles.sort(key=lambda item: (item[0], item[1], item[2].name))
        elegida = disponibles[0][2]
        _guardar_uso(uso_path, usos, f"{motivo}/{elegida.name}", hoy)
        return (elegida, None)

    # 2. Sin disponibles, se genera solo la variante que todavía no tiene imagen en el banco
    pendientes = _sin_imagen(dir_motivo, variantes)
    incompleto = bool(pendientes)
    if incompleto and generar is not None:
        destino = dir_motivo / f"v{pendientes[0]}.png"
        try:
            ruta_generada = generar(prompt_de(motivo, pendientes[0]), destino)
            _guardar_uso(uso_path, usos, f"{motivo}/{ruta_generada.name}", hoy)
            return (ruta_generada, None)
        except ImagenNoGenerada:
            pass

    # 3. Banco completo, o la generación falló: se reutiliza la de uso más antiguo. Con el banco completo es
    # la rotación normal y no se avisa; incompleto, el analista sabe que no se pudo hacer una nueva.
    if imagenes:
        def clave_antiguedad(p: Path) -> tuple[int, date, str]:
            f_uso = fecha_de_uso(p)
            if f_uso is None:
                return (0, date.min, p.name)
            return (1, f_uso, p.name)

        mas_antigua = min(imagenes, key=clave_antiguedad)
        _guardar_uso(uso_path, usos, f"{motivo}/{mas_antigua.name}", hoy)
        if not incompleto:
            return (mas_antigua, None)
        aviso = (f"La imagen de la noticia ya salió en otro análisis de los últimos {COOLDOWN_DIAS} días: "
                 "no pude generar una nueva.")
        return (mas_antigua, aviso)

    # 4. Si el motivo no tiene ninguna imagen y no se pudo generar
    aviso = "No pude generar la imagen de la noticia: el correo la muestra sin imagen."
    return (None, aviso)


if __name__ == "__main__":
    # Llena el banco antes de que lo pida un analista: cada imagen son ~76 s de agy (medido el 2026-10-24).
    from analista.generador_imagen import generar_con_agy

    for motivo, i in faltantes():
        try:
            print(generar_con_agy(prompt_de(motivo, i), BANCO / motivo / f"v{i}.png"), flush=True)
        except ImagenNoGenerada as exc:
            print(f"{motivo} v{i}: {exc}", flush=True)
