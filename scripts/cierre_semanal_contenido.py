#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contenido editorial del informe de cierre semanal.

Separado de la maqueta (`compilar_informe_cierre_semanal.py`) y de los datos
(`cierre_semanal_datos.py`) por el mismo criterio que la capacitación en PPTX:
editar un texto no debe obligar a tocar el dibujo, ni al revés.

**Las cifras NO se escriben acá.** Los precios, variaciones y niveles llegan del
módulo de datos y se interpolan con `{}`; este archivo aporta la lectura, no los
números (regla 1 del proyecto). Lo que sí es de acá es el juicio: qué explicó el
movimiento, qué significa para el cliente y qué queda prohibido.

Reglas de texto de cliente que este archivo cumple y que conviene no romper:
sin guion largo como inciso, notación chilena en toda cifra escrita a mano,
español chileno neutro, y toda sigla explicada la primera vez que aparece.
"""

from __future__ import annotations

from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# Portada
# ─────────────────────────────────────────────────────────────────────────────
KICKER = "RESEARCH INTERMERCADO · EDICIÓN CIERRE DE SEMANA"
TITULO = "Shock de Oferta en el Crudo y"
TITULO_ACENTO = "una Curva que se Aplana"

BAJADA = (
    "El petróleo se llevó la semana con un alza cercana al 9 %, empujado por una "
    "caída de inventarios en Estados Unidos muy superior a la esperada. El cobre "
    "no acompañó, y esa diferencia es la que define el manejo de riesgo: cuando "
    "el crudo sube sin demanda industrial detrás, el movimiento es más frágil."
)

RESUMEN_EJECUTIVO = (
    "La semana que cierra este viernes 4 de septiembre dejó un cuadro de precios "
    "al alza con actividad despareja, y el motor del movimiento fue la energía. "
    "El informe oficial de inventarios de crudo mostró una caída de 4,45 millones "
    "de barriles cuando el mercado esperaba apenas 0,40 millones, y eso levantó al "
    "WTI cerca del 9 % en cinco sesiones. La señal de costos apareció también en "
    "las encuestas a empresas: los precios pagados de la industria marcaron 71,1 y "
    "los de servicios 72,6, ambos sobre lo previsto. En paralelo la actividad se "
    "mostró irregular, con el índice de Chicago cayendo a 47,1 desde los 57,8 que "
    "se esperaban y el empleo privado creando 38 mil puestos contra 47 mil "
    "previstos. Hoy las nóminas oficiales sorprendieron al alza con 162 mil "
    "empleos frente a 55 mil esperados, lo que refuerza el escenario de tasas "
    "altas por más tiempo. La curva soberana lo recogió aplanándose: el tramo a "
    "dos años subió 20 puntos base y el de treinta apenas 9."
)

# Nota corta de cada tarjeta de la portada, por slug de activo.
NOTAS_PORTADA = {
    "usdclp": "Dólar firme pero sin fuerza; el cobre lo contuvo.",
    "xauusd": "La tasa real en 2,45 % pesó más que el crudo.",
    "copper": "Sube, pero no confirma demanda industrial.",
    "wti": "Inventarios en fuerte caída: shock de oferta.",
    "brent": "Acompaña al WTI con el mismo driver.",
    "us100": "Contenido por el costo del dinero en 4,79 %.",
    "usdjpy": "Se cumplió nuestro escenario de riesgo.",
}

# ─────────────────────────────────────────────────────────────────────────────
# Curva soberana
# ─────────────────────────────────────────────────────────────────────────────
INTRO_CURVA = (
    "La estructura de tasas del Tesoro de Estados Unidos se aplanó durante la "
    "semana: el tramo corto subió con fuerza y el largo apenas se movió. Eso "
    "ocurre cuando el mercado deja de esperar recortes cercanos, y es coherente "
    "con las nóminas de hoy. La pieza que más importa para nuestros activos es la "
    "tasa real, que es lo que rinde un bono ya descontada la inflación: subió 11 "
    "puntos base a 2,45 % y ahí está la explicación de por qué el oro cayó en una "
    "semana de escalada del petróleo."
)

# Diagnóstico por serie. La clave es el código que emite `cierre_semanal_datos`.
DIAGNOSTICO_CURVA = {
    "DGS2": "El tramo que más refleja las expectativas de tasa de la Fed. Subió con fuerza: el mercado descarta recortes cercanos.",
    "DGS10": "La referencia global del precio del dinero. Sobre 4,70 % presiona a las acciones tecnológicas.",
    "DGS30": "El tramo más largo casi no se movió, así que el alza fue de expectativas de tasa y no de prima por plazo.",
    "DFII10": "El costo real del dinero, ya descontada la inflación. Su alza es el principal competidor del oro.",
    "T10YIE": "La inflación que el mercado descuenta a diez años. Estable: el alza de tasas no viene de expectativas desancladas.",
    "SPREAD": "La curva se aplanó pero sigue en terreno positivo, así que no está anticipando recesión.",
}

NOTA_CURVA_REZAGO = (
    "Los niveles de la curva son del dato oficial más reciente publicado por la "
    "Reserva Federal, con la fecha indicada en la última columna. La variación de "
    "cinco días es la que corresponde a la semana."
)

# ─────────────────────────────────────────────────────────────────────────────
# Las tres capas por activo
# ─────────────────────────────────────────────────────────────────────────────
# `{}` recibe los números del módulo de datos. Nada de esto se escribe a mano.
CAPAS = {
    "usdclp": {
        "pasando": (
            "Pasó de {previo} a {actual} ({var}), un movimiento chico para lo que "
            "se movió el resto del mundo. El dólar global se sostuvo con las tasas "
            "al alza, pero el cobre subiendo puso un freno por el lado exportador."
        ),
        "significa": (
            "Zona de equilibrio entre {s1} y {r1}, con el precio operando entre sus "
            "promedios de 20 y 50 horas. La fuerza de tendencia es baja, así que "
            "conviene tratarlo como rango y no como impulso."
        ),
        "prohibido": (
            "Prohibido apostar a la baja del dólar: con el escenario de precios al "
            "alza y economía frenada, el sesgo del peso es de debilidad. Y ojo con el "
            "horario, porque el dólar en Chile solo tiene liquidez profunda entre las "
            "09:00 y las 14:00."
        ),
    },
    "xauusd": {
        "pasando": (
            "Retrocedió de {previo} a {actual} ({var}) en una semana en que el "
            "petróleo subió 9 %. La razón está en la tasa real, que trepó a 2,45 %: "
            "cuando un bono seguro rinde más descontada la inflación, guardar metal "
            "cuesta más caro."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}. La fuerza de tendencia es alta, "
            "así que los retrocesos hacia el promedio de 20 horas siguen siendo la "
            "zona a mirar para el lado comprador."
        ),
        "prohibido": (
            "Prohibido vender en corto: el escenario de precios al alza mantiene el "
            "sesgo comprador del oro, y esta caída es costo de oportunidad por tasas, "
            "no un giro de tendencia. Un indicador en sobrecompra no autoriza la venta."
        ),
    },
    "copper": {
        "pasando": (
            "Cerró en {actual} ({var}), al alza pero lejos de confirmar un ciclo de "
            "demanda industrial. Es el dato que más importa esta semana, y no por lo "
            "que hizo sino por lo que no hizo."
        ),
        "significa": (
            "Soporte medido en {s1}. Su lectura sirve sobre todo como termómetro: "
            "mientras el cobre no acelere, el alza del petróleo se explica por oferta "
            "y no por una economía global que se reactiva."
        ),
        "prohibido": (
            "Prohibido abrir ventas contra la tendencia primaria de las materias "
            "primas industriales. Y prohibido leer este alza como confirmación de "
            "demanda: no alcanza el umbral que el modelo exige."
        ),
    },
    "wti": {
        "pasando": (
            "Subió de {previo} a {actual} ({var}), el mayor movimiento de la semana "
            "entre todos los activos que seguimos. El detonante fue el informe oficial "
            "de inventarios: cayeron 4,45 millones de barriles contra 0,40 esperados."
        ),
        "significa": (
            "Rango de la semana entre {s1} y {r1}, con el canal de las últimas 50 horas "
            "entre {don_low} y {don_high}. El precio quedó operando en la parte alta de "
            "ese canal, así que el espacio hacia arriba es más estrecho que hace cinco días."
        ),
        "prohibido": (
            "Prohibido vender en la resistencia apostando a que ahí se frena. Y una regla "
            "que aplica justo esta semana: como el cobre no confirmó demanda, el modelo "
            "trata este alza como shock de oferta y manda operar con la mitad del tamaño "
            "habitual y el stop más ceñido."
        ),
    },
    "brent": {
        "pasando": (
            "Acompañó al WTI subiendo de {previo} a {actual} ({var}), con el mismo "
            "driver de inventarios. La diferencia entre ambos crudos se mantuvo estable, "
            "señal de que el movimiento es global y no un problema local de Estados Unidos."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}. La fuerza de tendencia es baja pese "
            "al tamaño del movimiento, lo que suele indicar un ajuste rápido de precio "
            "más que un cambio de tendencia consolidado."
        ),
        "prohibido": (
            "Prohibido vender en resistencia. Y prohibido operar energía sin stop de "
            "protección: el fin de semana concentra el riesgo de titulares en este activo."
        ),
    },
    "us100": {
        "pasando": (
            "Cerró en {actual} ({var}), prácticamente plano en la semana. Las nóminas "
            "fuertes de hoy son buenas para las utilidades pero malas para el costo del "
            "dinero, y esas dos fuerzas se anularon entre sí."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}, con el precio pegado a su promedio "
            "de 20 horas. Es un activo en pausa esperando el próximo dato de inflación."
        ),
        "prohibido": (
            "Prohibido comprar cada caída sin confirmación. Con el bono a diez años en "
            "4,79 %, o sea sobre el umbral de 4,70 % que el modelo vigila, el costo del "
            "dinero está comprimiendo lo que las empresas valen hoy."
        ),
    },
    "usdjpy": {
        "pasando": (
            "Cayó de {previo} a {actual} ({var}), la baja más marcada de la semana. "
            "Vale decirlo con claridad: este movimiento es el escenario de riesgo que "
            "publicamos en el informe del 28 de agosto, cuando marcamos un desplome "
            "hacia 155,00 con probabilidad del 15 %."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}. La fuerza de tendencia es alta y el "
            "precio quedó en el piso de su canal de las últimas 50 horas, así que es el "
            "activo con la estructura más definida de los siete."
        ),
        "prohibido": (
            "Prohibido perseguir compras esperando que rebote solo. Cuando un banco "
            "central o un ministerio de finanzas interviene su moneda, el precio puede "
            "moverse mucho más de lo que la estructura técnica sugiere."
        ),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Escenarios para la próxima semana
# ─────────────────────────────────────────────────────────────────────────────
ESCENARIOS = (
    {
        "clase": "pos",
        "emoji": "🟢",
        "titulo": "ESCENARIO POSITIVO · ALIVIO EN PRECIOS",
        "prob": 30,
        "bullets": (
            "La inflación de agosto en Estados Unidos, que se publica el viernes, sale bajo lo esperado y reabre la discusión de recortes de tasa.",
            "La tasa real cede desde 2,45 % y el oro recupera terreno hacia su resistencia.",
            "El Nasdaq 100 quiebra su resistencia con el bono a diez años volviendo bajo 4,70 %.",
        ),
    },
    {
        "clase": "base",
        "emoji": "🟡",
        "titulo": "ESCENARIO BASE · PRECIOS ALTOS SOSTENIDOS",
        "prob": 50,
        "bullets": (
            "La inflación sale en línea y las tasas se mantienen en el rango de esta semana, sin recortes a la vista.",
            "El petróleo consolida el alza sin extenderla, a la espera del próximo informe de inventarios del miércoles.",
            "El dólar en Chile sigue en rango, con el cobre como único contrapeso a la firmeza global del dólar.",
        ),
    },
    {
        "clase": "risk",
        "emoji": "🔴",
        "titulo": "ESCENARIO DE RIESGO · SEGUNDA RONDA DE COSTOS",
        "prob": 20,
        "bullets": (
            "La inflación sorprende al alza y confirma que el alza de la energía ya pasó a los precios al consumidor.",
            "El tramo a dos años supera con holgura el 4,50 % y la curva se aplana aún más, castigando a las acciones de crecimiento.",
            "Nuevo salto del crudo si los inventarios vuelven a caer, esta vez con el oro sin poder cubrir por el nivel de la tasa real.",
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Radar de la próxima semana
# ─────────────────────────────────────────────────────────────────────────────
# Las horas ya están convertidas con `scripts/hora_chile.ps1`. Ojo: desde el
# 2026-09-06 Chile entra en horario de verano y el desfase con Nueva York pasa a
# +1 h, así que un dato de 08:30 en Nueva York cae a las 09:30 en Chile. Ese
# cambio es justo el error de una hora que el proyecto ya se comió una vez.
RADAR = (
    {
        "cuando": "Miércoles 09-Sep (11:30)",
        "evento": "Inventarios de petróleo crudo",
        "fuente": "Administración de Información Energética (EIA)",
        "impacto": "Es el dato que movió la semana. Define si el alza del crudo continúa.",
    },
    {
        "cuando": "Jueves 10-Sep (09:30)",
        "evento": "Peticiones de subsidio por desempleo",
        "fuente": "Departamento del Trabajo de EE.UU.",
        "impacto": "Termómetro semanal del empleo, después del dato fuerte de hoy.",
    },
    {
        "cuando": "Viernes 11-Sep (09:30)",
        "evento": "Inflación de agosto en EE.UU. (IPC)",
        "fuente": "Oficina de Estadísticas Laborales (BLS)",
        "impacto": "El dato de la semana. Dirá si el alza de la energía llegó a los precios al consumidor.",
    },
)

AVISO_HORARIO = (
    "Atención al cambio de hora. Desde este domingo Chile entra en horario de "
    "verano, así que los datos de Estados Unidos que salían a las 08:30 pasan a "
    "publicarse a las 09:30 de Chile. Las horas del radar ya están corregidas."
)

AVISO_LEGAL = (
    "Este informe ha sido elaborado exclusivamente con fines informativos y "
    "formativos por el Área de Research de Grupo Inteligencia, a partir de datos "
    "oficiales del terminal MetaTrader 5, la Reserva Federal de Estados Unidos "
    "(FRED), la Administración de Información Energética (EIA) y el calendario "
    "económico de Investing.com. No constituye una oferta ni una recomendación de "
    "compra o venta de instrumentos financieros o contratos por diferencia. Las "
    "operaciones apalancadas conllevan un riesgo sustancial para el capital."
)

# Encabezado de cada página, por índice de página (2 a 5).
ENCABEZADOS = {
    2: "RESEARCH INTERMERCADO · CURVA SOBERANA & FX",
    3: "RESEARCH INTERMERCADO · METALES",
    4: "RESEARCH INTERMERCADO · ENERGÍA",
    5: "RESEARCH INTERMERCADO · EQUITY & FX GLOBAL",
    6: "RESEARCH INTERMERCADO · ESCENARIOS & MARCO LEGAL",
}

# Reparto de fichas por página: **dos fichas por página como máximo**.
#
# El primer armado puso cuatro en la página 4 y la del yen se perdió entera:
# las páginas son fijas de 1123 px con `overflow: hidden`, así que el contenido
# que no cabe desaparece sin aviso y el informe se lee como completo. El control
# de "cinco páginas" no lo detectó porque el desborde fue DENTRO de una página,
# y por eso el compilador ahora mide el alto de cada una.
PAGINAS_ACTIVOS = {
    2: ("usdclp",),
    3: ("xauusd", "copper"),
    4: ("wti", "brent"),
    5: ("us100", "usdjpy"),
}


def capas_de(slug: str, activo: dict[str, Any], niveles: dict[str, Any]) -> dict[str, str]:
    """Rellena las tres capas de un activo con sus cifras reales.

    Lanza si falta una clave, con la misma política del resto del pipeline: una
    ficha a medias que sale sin avisar llega al cliente.
    """
    from grafico_informe import formatear_precio

    dg = activo["digits"]
    def n(clave: str) -> str:
        valor = niveles.get(clave)
        if not isinstance(valor, (int, float)):
            raise KeyError(f"{slug}: falta el nivel '{clave}' para redactar la ficha")
        return formatear_precio(float(valor), dg)

    contexto = {
        "previo": activo["previo_txt"],
        "actual": activo["actual_txt"],
        "var": activo["var_txt"],
        "s1": n("s1"), "s2": n("s2"), "r1": n("r1"), "r2": n("r2"),
        "don_low": n("donchian_50_low"), "don_high": n("donchian_50_high"),
    }
    plantilla = CAPAS.get(slug)
    if plantilla is None:
        raise KeyError(f"{slug}: no hay texto editorial en CAPAS")
    return {k: v.format(**contexto) for k, v in plantilla.items()}
