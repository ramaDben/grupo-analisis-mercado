"""
Orquestador principal del Grupo de Análisis de Mercado.
Coordina la operativa diaria: determina qué contenido generar según el día,
selecciona activos por rotación y gestiona el límite de señales semanales.
"""

import json
from datetime import datetime, date, timedelta
from pathlib import Path

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def cargar_json(ruta: Path) -> dict:
    """Carga un archivo JSON y retorna su contenido."""
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar_json(ruta: Path, datos) -> None:
    """Guarda datos en un archivo JSON."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def cargar_agenda() -> dict:
    """Carga la agenda semanal desde config/agenda_semanal.json."""
    return cargar_json(CONFIG_DIR / "agenda_semanal.json")


def cargar_activos() -> dict:
    """Carga la configuración de activos desde config/activos.json."""
    return cargar_json(CONFIG_DIR / "activos.json")


def cargar_drivers() -> dict:
    """Carga los drivers por activo desde config/drivers.json."""
    return cargar_json(CONFIG_DIR / "drivers.json")


def obtener_dia_semana() -> str:
    """Retorna el día de la semana actual en español."""
    dias = {
        0: "lunes",
        1: "martes",
        2: "miercoles",
        3: "jueves",
        4: "viernes",
        5: "sabado",
        6: "domingo"
    }
    return dias[date.today().weekday()]


def obtener_fecha_formateada() -> str:
    """Retorna la fecha actual formateada para los mensajes."""
    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }
    hoy = date.today()
    dia_semana = obtener_dia_semana().capitalize()
    return f"{dia_semana} {hoy.day} de {meses[hoy.month]} {hoy.year}"


def señales_enviadas_semana() -> int:
    """Cuenta cuántas señales se han enviado esta semana."""
    historial_path = DATA_DIR / "historial_senales.json"
    if not historial_path.exists():
        guardar_json(historial_path, [])
        return 0

    historial = cargar_json(historial_path)
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana

    return sum(
        1 for s in historial
        if date.fromisoformat(s["fecha"]) >= inicio_semana
    )


def señales_restantes() -> int:
    """Calcula cuántas señales se pueden enviar aún esta semana."""
    agenda = cargar_agenda()
    max_señales = agenda.get("max_señales_semana", 3)
    return max_señales - señales_enviadas_semana()


def seleccionar_activos_rotacion(n: int = 2) -> list:
    """
    Selecciona activos del día usando rotación para cubrir todos durante la semana.
    Lunes y viernes cubren más activos que martes-jueves.
    """
    config = cargar_activos()
    activos = config["activos"]
    dia_num = date.today().weekday()

    # Rotación: desplaza el inicio según el día de la semana
    inicio = (dia_num * 2) % len(activos)
    seleccion = []
    for i in range(n):
        seleccion.append(activos[(inicio + i) % len(activos)])

    return seleccion


def generar_plan_diario() -> dict:
    """
    Genera el plan completo de ejecución para hoy.
    Retorna un diccionario con toda la información necesaria para los agentes.
    """
    dia = obtener_dia_semana()

    if dia in ("sabado", "domingo"):
        return {
            "dia": dia,
            "fecha": date.today().isoformat(),
            "fecha_formateada": obtener_fecha_formateada(),
            "es_dia_operativo": False,
            "mensaje": "Fin de semana — no hay operativa"
        }

    agenda = cargar_agenda()
    plan_dia = agenda["agenda"][dia]

    # Viernes tiene más activos
    n_activos = 3 if dia == "viernes" else 2
    activos_hoy = seleccionar_activos_rotacion(n=n_activos)

    return {
        "dia": dia,
        "fecha": date.today().isoformat(),
        "fecha_formateada": obtener_fecha_formateada(),
        "es_dia_operativo": True,
        "activos_hoy": [
            {
                "ticker": a["ticker"],
                "nombre": a["nombre"],
                "temporalidades": a["temporalidades"]
            }
            for a in activos_hoy
        ],
        "contenido_requerido": plan_dia["contenido"],
        "encuesta": plan_dia["encuesta"],
        "señales_disponibles": señales_restantes(),
        "señales_enviadas": señales_enviadas_semana(),
        "notas_dia": plan_dia.get("notas", ""),
        "horarios": agenda.get("horarios_sugeridos", {})
    }


def mostrar_plan(plan: dict) -> None:
    """Muestra el plan del día de forma legible."""
    print("=" * 60)
    print(f"📋 PLAN DEL DÍA — {plan['fecha_formateada']}")
    print("=" * 60)

    if not plan.get("es_dia_operativo"):
        print(f"\n{plan['mensaje']}")
        return

    print(f"\n📅 Día: {plan['dia'].upper()}")
    print(f"📆 Fecha: {plan['fecha']}")

    print(f"\n📊 Activos del día:")
    for activo in plan["activos_hoy"]:
        print(f"   • {activo['ticker']} ({activo['nombre']}) — Temporalidades: {', '.join(activo['temporalidades'])}")

    print(f"\n📝 Contenido a generar:")
    for contenido in plan["contenido_requerido"]:
        print(f"   • {contenido}")

    print(f"\n📊 Encuesta:")
    print(f"   • Tipo: {plan['encuesta']['tipo']}")
    print(f"   • {plan['encuesta']['descripcion']}")

    print(f"\n🎯 Señales:")
    print(f"   • Enviadas esta semana: {plan['señales_enviadas']}/3")
    print(f"   • Disponibles: {plan['señales_disponibles']}")

    if plan["notas_dia"]:
        print(f"\n💡 Notas: {plan['notas_dia']}")

    print(f"\n🕐 Horarios sugeridos:")
    for actividad, hora in plan["horarios"].items():
        print(f"   • {actividad}: {hora}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    plan = generar_plan_diario()
    mostrar_plan(plan)

    # Guardar plan del día para que los agentes lo lean
    guardar_json(DATA_DIR / "plan_hoy.json", plan)
    print(f"\n✅ Plan guardado en data/plan_hoy.json")
