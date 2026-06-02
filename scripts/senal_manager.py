"""
Gestor de señales operativas.
Controla el límite semanal de 3 señales, registra el historial
y convierte TP/SL a pesos chilenos (CLP).
"""

import json
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORIAL_PATH = DATA_DIR / "historial_senales.json"


def _cargar_historial() -> list:
    """Carga el historial de señales. Crea el archivo si no existe."""
    if not HISTORIAL_PATH.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    with open(HISTORIAL_PATH, encoding="utf-8") as f:
        return json.load(f)


def _guardar_historial(historial: list) -> None:
    """Guarda el historial de señales."""
    with open(HISTORIAL_PATH, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def señales_enviadas_semana() -> int:
    """Cuenta cuántas señales se han enviado esta semana (lunes a domingo)."""
    historial = _cargar_historial()
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    return sum(
        1 for s in historial
        if date.fromisoformat(s["fecha"]) >= inicio_semana
    )


def señales_restantes() -> int:
    """Cuántas señales se pueden enviar aún esta semana (máximo 3)."""
    return max(0, 3 - señales_enviadas_semana())


def puede_enviar_señal() -> bool:
    """Verifica si se puede enviar una señal más esta semana."""
    return señales_restantes() > 0


def registrar_señal(datos_señal: dict) -> dict:
    """
    Registra una nueva señal en el historial.

    Args:
        datos_señal: Dict con los datos de la señal (ticker, tipo, entrada, tp, sl, etc.)

    Returns:
        Dict con resultado: éxito o error si se excedió el límite.
    """
    if not puede_enviar_señal():
        return {
            "exito": False,
            "error": "Límite semanal alcanzado (3/3 señales)",
            "señales_enviadas": señales_enviadas_semana(),
            "señales_restantes": 0
        }

    historial = _cargar_historial()

    registro = {
        "fecha": date.today().isoformat(),
        "numero_semana": señales_enviadas_semana() + 1,
        "ticker": datos_señal.get("ticker"),
        "nombre_activo": datos_señal.get("nombre_activo"),
        "tipo": datos_señal.get("tipo"),  # BUY o SELL
        "entrada": datos_señal.get("entrada"),
        "take_profit": datos_señal.get("take_profit"),
        "stop_loss": datos_señal.get("stop_loss"),
        "tp_clp": datos_señal.get("tp_clp"),
        "sl_clp": datos_señal.get("sl_clp"),
        "temporalidad": datos_señal.get("temporalidad"),
        "tipo_operativa": datos_señal.get("tipo_operativa"),
        "estado": "abierta"  # abierta, cerrada_tp, cerrada_sl, cerrada_manual
    }

    historial.append(registro)
    _guardar_historial(historial)

    return {
        "exito": True,
        "señal_numero": registro["numero_semana"],
        "señales_restantes": señales_restantes(),
        "registro": registro
    }


def convertir_a_clp(precio_entrada: float, precio_objetivo: float,
                     acciones: float, tipo_cambio_usdclp: float) -> float:
    """
    Convierte la diferencia entre entrada y objetivo a pesos chilenos.

    Args:
        precio_entrada: Precio de entrada en USD
        precio_objetivo: Precio de TP o SL en USD
        acciones: Número de acciones
        tipo_cambio_usdclp: Tipo de cambio USD/CLP actual

    Returns:
        Monto en CLP (positivo para ganancia, negativo para pérdida)
    """
    diferencia_usd = (precio_objetivo - precio_entrada) * acciones
    return round(diferencia_usd * tipo_cambio_usdclp, 0)


def calcular_clp_señal(entrada: float, tp: float, sl: float,
                        acciones: float, tipo_cambio: float) -> dict:
    """
    Calcula TP y SL en CLP para una señal completa.

    Returns:
        Dict con tp_clp y sl_clp.
    """
    return {
        "tp_clp": convertir_a_clp(entrada, tp, acciones, tipo_cambio),
        "sl_clp": convertir_a_clp(entrada, sl, acciones, tipo_cambio)
    }


def obtener_historial_semana() -> list:
    """Retorna las señales enviadas esta semana."""
    historial = _cargar_historial()
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    return [
        s for s in historial
        if date.fromisoformat(s["fecha"]) >= inicio_semana
    ]


def resumen_señales() -> dict:
    """Genera un resumen del estado de señales de la semana."""
    semana = obtener_historial_semana()
    return {
        "enviadas": len(semana),
        "restantes": señales_restantes(),
        "max_semana": 3,
        "señales": semana
    }


if __name__ == "__main__":
    print("🎯 Estado de señales")
    print("-" * 40)

    resumen = resumen_señales()
    print(f"Señales enviadas esta semana: {resumen['enviadas']}/3")
    print(f"Señales restantes: {resumen['restantes']}")

    if resumen["señales"]:
        print("\nSeñales de la semana:")
        for s in resumen["señales"]:
            print(f"  • {s['fecha']} — {s['ticker']} {s['tipo']} @ {s['entrada']}")
    else:
        print("\nNo se han enviado señales esta semana.")

    # Test de conversión CLP
    print("\n💱 Test conversión CLP:")
    resultado = calcular_clp_señal(
        entrada=180, tp=200, sl=168,
        acciones=7.5, tipo_cambio=950
    )
    print(f"  Entrada: $180 → TP: $200 / SL: $168")
    print(f"  Acciones: 7.5 / TC: 950 CLP/USD")
    print(f"  TP en CLP: +${resultado['tp_clp']:,.0f}")
    print(f"  SL en CLP: ${resultado['sl_clp']:,.0f}")
