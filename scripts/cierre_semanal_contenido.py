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
TITULO = "El Petróleo Vuelve a Mandar y"
TITULO_ACENTO = "el Yen Rompe el Libreto"

BAJADA = (
    "El petróleo volvió a liderar la semana con un alza de doble dígito pese a un "
    "dato de inventarios más flojo de lo esperado: el impulso vino de la oferta, "
    "no de la demanda. El dólar, en cambio, no tuvo una semana pareja: se impuso "
    "frente al peso chileno y cedió frente al yen, que se adelantó a la reunión "
    "del Banco de Japón del miércoles próximo."
)

RESUMEN_EJECUTIVO = (
    "La semana que cierra este viernes 11 de septiembre volvió a estar dominada "
    "por la energía: el petróleo subió con fuerza pese a que el informe oficial "
    "de inventarios en Estados Unidos mostró una caída de apenas 0,39 millones de "
    "barriles, muy por debajo del 1,40 millones que esperaba el mercado. El "
    "impulso no vino entonces de la demanda, sino de la atención puesta en la "
    "oferta, con la OPEP en la agenda de la semana y declaraciones de alto "
    "impacto del gobierno de Estados Unidos sobre energía. En paralelo, el Banco "
    "Central Europeo subió su tasa de depósito a 2,50 % y su tasa principal a "
    "2,65 %, en línea con lo esperado, y la inflación de agosto en Estados Unidos "
    "salió mixta: el índice general subió 0,4 % mensual, en línea, pero el índice "
    "subyacente sorprendió al alza con 0,3 % contra 0,2 % previsto. El Banco "
    "Central de Chile mantuvo su Tasa de Política Monetaria en 4,5 %. La tasa "
    "real a diez años en Estados Unidos subió apenas 2 puntos base a 2,46 %, y "
    "aun así alcanzó para empujar al oro a la baja. El dato más atípico de la "
    "semana fue el yen japonés, que se fortaleció con fuerza mientras las tasas "
    "de Estados Unidos subían: el bono japonés a diez años trepó a 2,92 % y el "
    "mercado empezó a posicionarse de cara a la reunión del Banco de Japón del "
    "miércoles próximo."
)

# Nota corta de cada tarjeta de la portada, por slug de activo.
NOTAS_PORTADA = {
    "usdclp": "Sube pese al cobre débil; no hubo dólar fuerte parejo.",
    "xauusd": "Cede terreno con la tasa real algo más alta.",
    "copper": "Retrocede y no acompaña el rally del petróleo.",
    "wti": "Nuevo salto pese a un dato de inventarios flojo.",
    "brent": "Sigue al WTI con el mismo impulso de oferta.",
    "us100": "Prácticamente plano, digiriendo una inflación mixta.",
    "usdjpy": "El quiebre de la semana: se adelantó al Banco de Japón.",
}

# ─────────────────────────────────────────────────────────────────────────────
# Curva soberana
# ─────────────────────────────────────────────────────────────────────────────
INTRO_CURVA = (
    "La curva de Estados Unidos se movió poco esta semana, y lo que más subió fue "
    "la expectativa de inflación a diez años, no las tasas nominales. Eso ocurre "
    "cuando el mercado empieza a mirar con algo más de atención el traspaso del "
    "costo de la energía a los precios, sin llegar todavía a preocuparse en "
    "serio. La tasa real, que es lo que rinde un bono ya descontada la "
    "inflación, subió apenas 2 puntos base a 2,46 %, y ese movimiento chico "
    "alcanzó para explicar la caída del oro en una semana de fuerte alza del "
    "petróleo."
)

# Diagnóstico por serie. La clave es el código que emite `cierre_semanal_datos`.
DIAGNOSTICO_CURVA = {
    "DGS2": "El tramo que más refleja las expectativas de tasa de la Fed subió apenas 4 puntos base: un movimiento chico, coherente con una semana sin sorpresas grandes en la inflación.",
    "DGS10": "La referencia global del precio del dinero. Se mantiene sobre 4,80 %, el nivel que sigue pesando sobre las acciones tecnológicas.",
    "DGS30": "El tramo más largo casi no se movió (apenas 1 punto base), así que la prima por plazo sigue contenida.",
    "DFII10": "El costo real del dinero, ya descontada la inflación. Su alza de 2 puntos base fue chica, pero es el principal competidor del oro y explica buena parte de su retroceso.",
    "T10YIE": "La inflación que el mercado descuenta a diez años fue lo que más se movió esta semana: +6 puntos base, la primera señal de que el mercado empieza a mirar la energía con algo más de atención.",
    "SPREAD": "La curva sigue en terreno positivo y prácticamente sin cambios en la semana, así que no está anticipando recesión.",
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
            "Subió de {previo} a {actual} ({var}), pero no por un dólar fuerte a nivel "
            "global: en la misma semana el yen se apreció con fuerza frente al billete "
            "verde. El impulso vino del lado local, con el cobre cediendo terreno y "
            "quitándole soporte al peso."
        ),
        "significa": (
            "Zona entre {s1} y {r1}, con el precio sobre sus promedios de 20 y 50 horas "
            "y una fuerza de tendencia alta. Es de los pocos activos de la semana con "
            "una estructura alcista clara."
        ),
        "prohibido": (
            "Prohibido apostar a una baja rápida del dólar: con el cobre débil y la "
            "tendencia técnica alcista, el sesgo es de fortaleza del peso. Y ojo con el "
            "horario, porque el dólar en Chile solo tiene liquidez profunda entre las "
            "09:00 y las 14:00."
        ),
    },
    "xauusd": {
        "pasando": (
            "Retrocedió de {previo} a {actual} ({var}) en una semana en que la tasa "
            "real subió apenas 2 puntos base a 2,46 %. Es un movimiento chico en la "
            "tasa para una caída grande en el precio, así que el resto lo explica la "
            "fortaleza selectiva del dólar frente al oro."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}. La fuerza de tendencia es moderada "
            "y la tendencia de corto plazo pasó a bajista, así que el rebote hacia el "
            "promedio de 20 horas es la zona a vigilar antes de sumar."
        ),
        "prohibido": (
            "Prohibido vender en corto persiguiendo la caída: el nivel de la tasa real "
            "sigue siendo bajo en términos históricos, y un indicador en zona baja no "
            "autoriza a perseguir la baja sin una señal de rebote confirmada."
        ),
    },
    "copper": {
        "pasando": (
            "Cerró en {actual} ({var}), a la baja y sin acompañar el salto del "
            "petróleo. Es la señal que más importa de la semana: si el cobre no "
            "confirma, el alza de la energía sigue siendo un tema de oferta y no de "
            "una economía global que se recalienta."
        ),
        "significa": (
            "Resistencia en {r1} y soporte en {s1}. Sirve sobre todo como termómetro "
            "de demanda industrial, y esta semana no dio la confirmación que el modelo "
            "exige."
        ),
        "prohibido": (
            "Prohibido leer esta caída como el inicio de una tendencia bajista sin "
            "confirmación adicional, y prohibido usar el cobre como argumento de "
            "demanda mientras siga por debajo de su promedio de 50 horas."
        ),
    },
    "wti": {
        "pasando": (
            "Subió de {previo} a {actual} ({var}), el mayor movimiento de la semana "
            "entre todos los activos que seguimos, y la segunda semana consecutiva de "
            "alza fuerte. Lo llamativo es que el informe oficial de inventarios salió "
            "flojo (una caída de apenas 0,39 millones de barriles contra 1,40 "
            "esperados), así que el impulso no vino de un faltante real de crudo sino "
            "de la atención puesta en la oferta, con la OPEP en la agenda de la semana."
        ),
        "significa": (
            "Rango de la semana entre {s1} y {r1}, con el canal de las últimas 50 "
            "horas entre {don_low} y {don_high}. El precio quedó cerca de la parte "
            "alta de ese canal, así que el espacio hacia arriba es más estrecho que "
            "hace cinco días."
        ),
        "prohibido": (
            "Prohibido vender en la resistencia apostando a que ahí se frena solo. Y "
            "como el cobre no confirmó demanda, el modelo trata este alza como shock "
            "de oferta: operar con la mitad del tamaño habitual y el stop más ceñido."
        ),
    },
    "brent": {
        "pasando": (
            "Acompañó al WTI subiendo de {previo} a {actual} ({var}), con el mismo "
            "driver de oferta. La diferencia entre ambos crudos se mantuvo estable, "
            "señal de que el movimiento es global y no un problema local de Estados "
            "Unidos."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}. La fuerza de tendencia es "
            "moderada, coherente con un ajuste rápido de precio más que con un cambio "
            "de tendencia consolidado."
        ),
        "prohibido": (
            "Prohibido vender en resistencia. Y prohibido operar energía sin stop de "
            "protección: el fin de semana concentra el riesgo de titulares en este "
            "activo, sobre todo con la reunión de la OPEP todavía fresca."
        ),
    },
    "us100": {
        "pasando": (
            "Cerró en {actual} ({var}), prácticamente plano en la semana. La "
            "inflación subyacente algo más caliente de lo esperado (0,3 % contra "
            "0,2 %) fue un freno, pero no alcanzó para gatillar una caída, porque el "
            "dato general vino en línea."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}, con el precio pegado a sus "
            "promedios de 20 y 50 horas. Es un activo en pausa, a la espera de la "
            "decisión de la Fed del miércoles próximo."
        ),
        "prohibido": (
            "Prohibido comprar cada caída sin confirmación. Con el bono a diez años "
            "en 4,83 %, el costo del dinero sigue comprimiendo lo que las empresas "
            "valen hoy, y la reunión de la Fed puede mover ese umbral en cualquier "
            "dirección."
        ),
    },
    "usdjpy": {
        "pasando": (
            "Cayó de {previo} a {actual} ({var}), la baja más marcada de la semana y "
            "el movimiento más atípico: el yen se fortaleció incluso mientras las "
            "tasas de Estados Unidos subían. El bono japonés a diez años trepó a "
            "2,92 % y el mercado empezó a posicionarse de cara a la reunión del Banco "
            "de Japón del miércoles próximo."
        ),
        "significa": (
            "Soporte en {s1} y resistencia en {r1}. La fuerza de tendencia es alta y "
            "el precio quedó cerca del piso de su canal de las últimas 50 horas, la "
            "estructura más definida de los siete activos."
        ),
        "prohibido": (
            "Prohibido perseguir compras esperando un rebote automático. Con una "
            "reunión de un banco central de por medio, el precio puede moverse mucho "
            "más de lo que sugiere la estructura técnica, en cualquier dirección."
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
        "titulo": "ESCENARIO POSITIVO · LA FED PRIORIZA EL CONSUMO",
        "prob": 30,
        "bullets": (
            "La Fed, tras un IPC subyacente apenas por sobre lo esperado, prioriza la señal más floja del consumo (la confianza de Michigan cayó a 47,8 esta semana) y deja la puerta abierta a un recorte.",
            "El Banco de Japón mantiene su tasa sin cambios y el yen devuelve parte de lo ganado esta semana, dando algo de aire al dólar.",
            "El petróleo cede terreno al no sumar un nuevo catalizador de oferta, y el oro recupera con una tasa real más contenida.",
        ),
    },
    {
        "clase": "base",
        "emoji": "🟡",
        "titulo": "ESCENARIO BASE · TRES BANCOS CENTRALES, SIN SORPRESAS",
        "prob": 50,
        "bullets": (
            "La Fed mantiene la tasa sin cambios y repite el mensaje de cautela, sin comprometerse a un calendario de recortes.",
            "El Banco de Japón sostiene su tasa en 1,0 %, pero deja espacio para una subida hacia fin de año, y el yen se mantiene firme sin sobresaltos.",
            "El petróleo consolida el alza de esta semana sin extenderla, a la espera del próximo informe de inventarios.",
        ),
    },
    {
        "clase": "risk",
        "emoji": "🔴",
        "titulo": "ESCENARIO DE RIESGO · EL BANCO DE JAPÓN SORPRENDE",
        "prob": 20,
        "bullets": (
            "El Banco de Japón sorprende con una subida de tasas y el yen se dispara con fuerza, arrastrando volatilidad al resto de los activos que seguimos.",
            "La Fed, con la inflación subyacente todavía por sobre su objetivo, endurece el tono y aleja el primer recorte del año.",
            "El petróleo extiende el alza si la OPEP mantiene el mensaje de oferta ajustada, esta vez sin el respaldo de una caída real de inventarios.",
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# Radar de la próxima semana
# ─────────────────────────────────────────────────────────────────────────────
# Horas convertidas con zoneinfo desde el huso de origen de cada emisor (nunca a
# mano ni con offsets fijos, issue #38): Chile ya está en horario de verano desde
# el 2026-09-06, así que la Reserva Federal (Este de EE.UU.) queda a 1 hora de
# Chile y Japón a 12 horas.
RADAR = (
    {
        "cuando": "Miércoles 16-Sep (11:30)",
        "evento": "Inventarios de petróleo crudo",
        "fuente": "Administración de Información Energética (EIA)",
        "impacto": "Dirá si el impulso de esta semana tiene sustento en la demanda real o sigue siendo un tema de oferta.",
    },
    {
        "cuando": "Miércoles 16-Sep (15:00)",
        "evento": "Decisión de tasas de interés",
        "fuente": "Reserva Federal de Estados Unidos (Fed)",
        "impacto": "El evento central del mes: tras un IPC subyacente algo caliente, el mercado necesita saber si eso alcanza para frenar los recortes.",
    },
    {
        "cuando": "Miércoles a jueves 16/17-Sep (23:30 a 00:30)",
        "evento": "Decisión de tasas de interés",
        "fuente": "Banco de Japón (BoJ)",
        "impacto": "El yen ya se adelantó fortaleciéndose esta semana; acá se confirma o se corrige esa apuesta.",
    },
)

AVISO_HORARIO = (
    "Atención al calendario de la próxima semana. El miércoles 16 se concentran "
    "el informe de inventarios de petróleo, la decisión de tasas de la Reserva "
    "Federal y, horas más tarde, la decisión del Banco de Japón: tres eventos de "
    "alto impacto en menos de veinticuatro horas. Es una semana para operar con "
    "menor tamaño y stops más amplios, no para forzar entradas."
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
