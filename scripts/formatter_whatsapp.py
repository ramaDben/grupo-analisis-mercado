"""
Formateador de mensajes para WhatsApp.
Lee los templates y los rellena con datos del mercado.
"""

import json
from datetime import date
from pathlib import Path
from string import Template

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"


def leer_template(nombre: str) -> str:
    """Lee un template desde templates/."""
    ruta = TEMPLATES_DIR / nombre
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def reemplazar_variables(template: str, variables: dict) -> str:
    """Reemplaza {{variable}} por su valor en el template."""
    resultado = template
    for clave, valor in variables.items():
        resultado = resultado.replace(f"{{{{{clave}}}}}", str(valor))
    return resultado


def formatear_apertura(datos_niveles: dict, dato_dia: dict, drivers: str, fecha: str = None) -> str:
    """
    Formatea el mensaje de apertura de mercado.

    Args:
        datos_niveles: Dict con niveles técnicos por activo
        dato_dia: Dict con el dato económico del día
        drivers: String con explicación de drivers
        fecha: Fecha formateada (si None, usa hoy)
    """
    template = leer_template("apertura_mercado.txt")

    if fecha is None:
        from scripts.orquestador import obtener_fecha_formateada
        fecha = obtener_fecha_formateada()

    variables = {
        "fecha": fecha,
        "drivers": drivers,
        **dato_dia
    }

    # Construir sección de niveles por activo
    seccion_niveles = ""
    for activo, niveles in datos_niveles.items():
        seccion_niveles += f"\n📈 *{activo}* — Niveles en {niveles.get('temporalidad', '4H')}\n"
        seccion_niveles += f"_Operativa {niveles.get('tipo_operativa', 'intradía')}_\n\n"
        seccion_niveles += f"• Resistencia: {niveles.get('resistencia_1', 'N/A')}\n"
        if niveles.get('zona_interes'):
            zona = niveles['zona_interes']
            seccion_niveles += f"• Zona de interés: {zona.get('desde', 'N/A')} - {zona.get('hasta', 'N/A')}\n"
        seccion_niveles += f"• Soporte: {niveles.get('soporte_1', 'N/A')}\n"
        seccion_niveles += f"• Sesgo: {niveles.get('sesgo', 'neutral')}\n"

    variables["seccion_niveles"] = seccion_niveles

    return reemplazar_variables(template, variables)


def formatear_encuesta_tendencia(activo: str) -> str:
    """Formatea la encuesta de tendencia (L, X, J)."""
    template = leer_template("encuesta_tendencia.txt")
    return reemplazar_variables(template, {"activo": activo})


def formatear_encuesta_precio(activo: str, cuando: str = "mañana") -> str:
    """Formatea la encuesta de precio de apertura (M, V)."""
    template = leer_template("encuesta_precio.txt")
    return reemplazar_variables(template, {
        "activo": activo,
        "cuando": cuando
    })


def formatear_señal(datos_señal: dict) -> str:
    """
    Formatea una señal operativa completa.

    Args:
        datos_señal: Dict con todos los campos de la señal
    """
    template = leer_template("señal_operativa.txt")

    # Formatear bullets
    bullets = datos_señal.get("bullets_analisis", [])
    bullets_texto = "\n".join(f"• {b}" for b in bullets[:3])
    datos_señal["bullets_texto"] = bullets_texto

    # Formatear CLP con separador de miles
    if "tp_clp" in datos_señal:
        tp_clp = datos_señal["tp_clp"]
        datos_señal["tp_clp_fmt"] = f"+${tp_clp:,.0f}".replace(",", ".")
    if "sl_clp" in datos_señal:
        sl_clp = abs(datos_señal["sl_clp"])
        datos_señal["sl_clp_fmt"] = f"-${sl_clp:,.0f}".replace(",", ".")

    # Número de señal esta semana
    from scripts.señal_manager import señales_enviadas_semana
    datos_señal["n_señal"] = señales_enviadas_semana() + 1

    return reemplazar_variables(template, datos_señal)


def formatear_resumen_semanal(calendario_semana: list, concepto: dict = None) -> str:
    """
    Formatea el resumen semanal del lunes.

    Args:
        calendario_semana: Lista de datos económicos de la semana
        concepto: Dict con el concepto educativo de la semana
    """
    template = leer_template("resumen_semanal.txt")

    # Construir lista de datos
    datos_texto = ""
    dias_rojos = []
    for dato in calendario_semana:
        emoji = "🔴" if dato.get("importancia", 0) >= 3 else "📌"
        datos_texto += f"\n{emoji} *{dato['dia']}* 🕐 {dato['hora_chile']} — {dato['indicador']} ({dato['pais']})\n"
        datos_texto += f"   → Posible impacto en: {', '.join(dato.get('activos_afectados', []))}\n"
        if dato.get("importancia", 0) >= 3:
            dias_rojos.append(dato["dia"])

    variables = {
        "semana": f"Semana del {date.today().strftime('%d/%m/%Y')}",
        "datos_semana": datos_texto,
        "dias_rojos": ", ".join(set(dias_rojos)) if dias_rojos else "Ninguno esta semana"
    }

    if concepto:
        variables["nombre_concepto"] = concepto.get("nombre", "")
        variables["explicacion_concepto"] = concepto.get("explicacion", "")
        variables["por_que_importa"] = concepto.get("por_que_importa", "")

    return reemplazar_variables(template, variables)


def formatear_cierre_semanal(resumen: dict) -> str:
    """Formatea el cierre semanal del viernes."""
    template = leer_template("cierre_semanal.txt")
    return reemplazar_variables(template, resumen)


def formatear_concepto_semana(concepto: dict) -> str:
    """Formatea el concepto educativo de la semana."""
    template = leer_template("concepto_semana.txt")
    return reemplazar_variables(template, concepto)


if __name__ == "__main__":
    # Test: generar una encuesta de tendencia
    print("=== Test: Encuesta de tendencia ===")
    print(formatear_encuesta_tendencia("USD/CLP"))
    print()

    print("=== Test: Encuesta de precio ===")
    print(formatear_encuesta_precio("Oro (XAU/USD)", "el lunes"))
