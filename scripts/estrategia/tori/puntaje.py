"""El escáner de Tori (spec §5): situación por horizonte, adicionales y exclusiones.

Cada situación tiene una banda de 25 puntos y lo que suma dentro de ella tiene
tope `tope_adicionales` (24), así el orden de situaciones del spec no se invierte
por los adicionales. Solo la resta por precio lejos de la seguridad baja de banda.
Las bandas, los umbrales y los pesos son parámetros nuestros (parametros.py).
Nada macro: la agenda no mueve el ranking (spec §8.2).
"""
from __future__ import annotations

from estrategia.contrato import Lectura, Linea, Puntaje
from estrategia.tori.parametros import PARAMETROS, Parametros


def bandas(p: Parametros) -> dict[str, dict[str, float]]:
    """El piso de cada situación por horizonte, leído de los parámetros."""
    return {"sesion": dict(p.bandas_sesion), "semana": dict(p.bandas_semana)}


BANDAS = bandas(PARAMETROS)
SIN_ESTRUCTURA = "sin líneas trazables: no hay estructura que leer"
PRUEBA_SEMANAL = "una línea A+ está en prueba: el análisis semanal espera el cierre de la vela"
CONTRA_SECUENCIA = "va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas"


def _rol(lectura: Lectura, rol: str) -> Linea | None:
    return next((x for x in lectura.lineas if x.rol == rol and x.marco == lectura.marco), None)


def _principal(x: Linea | None) -> bool:
    """Una línea puntúa como principal si es A+ y no es muy empinada (doctrina 2.2)."""
    return x is not None and x.calidad == "A+" and not x.empinada


def situacion(lectura: Lectura, p: Parametros) -> str:
    m = lectura.metricas
    accion, seguridad = _rol(lectura, "accion"), _rol(lectura, "seguridad")
    cerca = lambda clave: m.get(clave, float("inf")) <= p.cerca_atr_d1  # noqa: E731
    if lectura.estado == "PRUEBA":
        # Solo es setup si la otra línea existe: será la de seguridad tras la ruptura (V18).
        otra = seguridad if lectura.en_prueba.linea.rol == "accion" else accion
        return "ruptura" if _principal(lectura.en_prueba.linea) and otra is not None else "tendencia"
    if lectura.estado == "RUPTURA":
        # Sin línea de control trazada no hay setup de Tori (V18), y lejos de ella el riesgo
        # es alto y se pasa (doctrina 2.5): la frescura de la ruptura es esta distancia.
        es_setup = _principal(accion) and seguridad is not None and cerca("dist_seguridad_atr_d1")
        return "ruptura" if es_setup else "tendencia"
    if lectura.estado == "REBOTE":
        # El rebote es setup si la línea que lo sostuvo es A+ (doctrina 2.5, V7).
        return "a_punto" if _principal(seguridad) else "tendencia"
    if lectura.estado == "TENDENCIA":
        if (_principal(accion) and cerca("dist_accion_atr_d1")) or \
                (_principal(seguridad) and cerca("dist_seguridad_atr_d1")):
            return "a_punto"
        return "tendencia"
    return "rango"


def _sin_estructura(lectura: Lectura) -> bool:
    diagonales = [x for x in lectura.lineas if x.tipo == "diagonal" and x.marco == lectura.marco]
    bordes = [x for x in lectura.lineas if x.rol == "rango" and x.toques >= 2]
    return not diagonales and not bordes


def puntuar(lectura: Lectura, horizonte: str, p: Parametros) -> Puntaje:
    if _sin_estructura(lectura):
        return Puntaje(0.0, {}, SIN_ESTRUCTURA)
    if horizonte == "semana" and lectura.estado == "PRUEBA" and lectura.en_prueba.linea.calidad == "A+":
        return Puntaje(0.0, {}, PRUEBA_SEMANAL)
    if lectura.metricas.get("contra_secuencia", 0.0) == 1.0:
        return Puntaje(0.0, {}, CONTRA_SECUENCIA)  # ipUbs [00:36], [01:11]; director, 2026-10-10
    m = lectura.metricas
    sit = situacion(lectura, p)
    base = bandas(p)[horizonte][sit]
    principal = _rol(lectura, "accion") if sit == "ruptura" else _rol(lectura, "seguridad")
    suma: dict[str, float] = {}
    if principal is not None and principal.toques >= p.toques_calidad:
        suma["calidad_toques"] = p.peso_calidad
    if m.get("semanas_principal", 0.0) >= p.semanas_calidad:
        suma["calidad_semanas"] = p.peso_calidad
    peso_confluencia = p.peso_confluencia_semana if horizonte == "semana" else p.peso_confluencia_sesion
    suma["confluencia"] = m.get("confluencia", 0.0) * peso_confluencia
    suma["doble_confirmacion"] = p.peso_doble_confirmacion * m.get("doble_confirmacion", 0.0)
    seg, obj = m.get("dist_seguridad_atr_d1"), m.get("dist_objetivo_atr_d1")
    if seg is not None and obj is not None and obj >= p.espacio_factor * seg:
        suma["espacio"] = p.peso_espacio
    adicionales = min(sum(suma.values()), p.tope_adicionales)
    restas: dict[str, float] = {}
    if seg is not None and seg > p.lejos_atr_d1:
        restas["lejos_de_seguridad"] = -p.resta_lejos  # Tori pasa esa operación (doctrina 2.5)
    puntos = max(0.0, min(100.0, base + adicionales + sum(restas.values())))
    return Puntaje(puntos, {"base": base, **suma, "adicionales": adicionales, **restas}, None)
