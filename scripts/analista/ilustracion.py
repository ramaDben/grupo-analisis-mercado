"""Catálogo cerrado y banco de imágenes ilustrativas para el correo de oportunidad.

Cada correo abre con una noticia de apertura acompañada siempre de una imagen ilustrativa sobria
(spec 2026-10-24 §2). Para evitar costo y demoras de generación en cada despacho y asegurar variedad
visual, las imágenes se reutilizan rotándolas con un periodo de enfriamiento de 7 días. agy genera una
nueva solo cuando no quedan imágenes disponibles en el banco o todas están en enfriamiento reciente.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from analista import RAIZ
from analista.generador_imagen import Generador, ImagenNoGenerada

CONFIG = RAIZ / "config" / "motivos_imagen.json"
BANCO = RAIZ / "data" / "imagenes_ilustrativas"
COOLDOWN_DIAS = 7


def motivos(ruta: Path = CONFIG) -> dict[str, dict[str, str]]:
    """Devuelve el diccionario de motivos del catálogo cerrado."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return datos.get("motivos", {})


def prompt_de(motivo: str, ruta: Path = CONFIG) -> str:
    """Construye el prompt agregando las prohibiciones fijas para garantizar neutralidad legal y de marca."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    catalogo = datos.get("motivos", {})
    if motivo not in catalogo:
        raise KeyError(f"Motivo no encontrado en el catálogo: {motivo}")
    prompt = catalogo[motivo]["prompt"]
    prohibiciones = datos.get("prohibiciones", "")
    return prompt + " " + prohibiciones


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
    """Elige o genera una imagen ilustrativa para la noticia del correo según la rotación del banco."""
    # Valida existencia en catálogo antes de interactuar con disco para fallar de inmediato si es desconocido
    prompt = prompt_de(motivo)

    banco = Path(banco)
    uso_path = banco / "uso.json"
    usos = _leer_usos(uso_path)

    dir_motivo = banco / motivo
    imagenes: list[Path] = []
    if dir_motivo.is_dir():
        for p in sorted(dir_motivo.iterdir()):
            if p.is_file() and p.suffix.lower() in (".png", ".jpg"):
                imagenes.append(p)

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

    # 2. Si no hay imágenes disponibles y se proporcionó generador, intentar generar una nueva
    if generar is not None:
        if ahora is None:
            ahora = datetime.now()
        destino = dir_motivo / f"{ahora:%Y%m%d-%H%M%S}.png"
        try:
            ruta_generada = generar(prompt, destino)
            _guardar_uso(uso_path, usos, f"{motivo}/{ruta_generada.name}", hoy)
            return (ruta_generada, None)
        except ImagenNoGenerada:
            pass

    # 3. Si falló la generación o generar es None pero hay imágenes en el motivo, reutilizar la más antigua
    if imagenes:
        def clave_antiguedad(p: Path) -> tuple[int, date, str]:
            f_uso = fecha_de_uso(p)
            if f_uso is None:
                return (0, date.min, p.name)
            return (1, f_uso, p.name)

        mas_antigua = min(imagenes, key=clave_antiguedad)
        _guardar_uso(uso_path, usos, f"{motivo}/{mas_antigua.name}", hoy)
        aviso = (f"La imagen de la noticia ya salió en otro análisis de los últimos {COOLDOWN_DIAS} días: "
                 "no pude generar una nueva.")
        return (mas_antigua, aviso)

    # 4. Si el motivo no tiene ninguna imagen y no se pudo generar
    aviso = "No pude generar la imagen de la noticia: el correo la muestra sin imagen."
    return (None, aviso)
