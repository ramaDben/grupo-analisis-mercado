# -*- coding: utf-8 -*-
"""Genera el Simulador GI: una hoja donde el ejecutivo elige el instrumento de una
lista y registra las operaciones del periodo, sin tener que conocer el tamano de
contrato ni el spread vigente.

La tabla separa SIMULACION de COSTOS, como la planilla original de post-venta.

Se escribe el VOLUMEN EN LOTES, la unidad en que el usuario de la planilla explica la
operacion a sus clientes y la que se ingresa en el terminal. De esa columna leen todas
las demas formulas de la fila.

MARGEN REQUERIDO es el capital que ese volumen bloquea al precio de entrada de la
fila. NO es el volumen expresado en pesos: el equivalente en pesos de un volumen es el
NOCIONAL (lotes x precio x valor por lote), y el margen es ese nocional multiplicado
por la tasa que exige el broker. Confundirlos hacia leer $496.125 como el tamano de una
posicion que en realidad mueve $49 millones.

APALANCAMIENTO = nocional / capital de la cuenta, o sea cuantas veces el capital
controla esa operacion. Se descartaron las otras dos lecturas posibles: nocional /
margen da 1 / tasa, constante por instrumento, de modo que la columna repetiria el
mismo numero en todas las filas; y margen / capital no es apalancamiento sino la
fraccion del capital comprometida. La definicion elegida es ADITIVA, asi que el total
de la columna ES el apalancamiento del periodo, sin formula aparte.

El monto controlado por fila no se muestra porque seria redundante: con el capital
fijo, monto y apalancamiento son el mismo numero reescalado. El monto en pesos va en
el cierre, donde se conversa la magnitud.

Complejidad
-----------
Variables: n = instrumentos del catalogo (25) · k = parametros resueltos por
instrumento (10 celdas BUSCARV) · r = filas de operacion (6) · d = dias que la
posicion queda abierta.

Generacion (este script), por corrida:
    tiempo   O(n), con 4 llamadas IPC al terminal por instrumento
             (symbol_info, symbol_info_tick, order_calc_profit, order_calc_margin).
             Domina la latencia del IPC, no el computo.
    espacio  O(n + r)

Recalculo (Excel), por cambio de instrumento:
    O(k * n) comparaciones = k busquedas lineales sobre n filas. BUSCARV con
    coincidencia exacta (FALSE) fuerza el barrido lineal; con la columna ordenada
    y coincidencia aproximada (TRUE) seria O(log n) por binaria. Se descarta por
    CORRECCION, no por costo: la coincidencia aproximada devuelve la fila anterior
    mas cercana cuando el nombre no calza exacto, entregando en silencio los
    parametros de otro instrumento. Con n = 25 el barrido no cuesta nada.

Por fila de operacion: margen, apalancamiento, resultado bruto, costo de apertura,
costo de mantencion y resultado neto son formulas cerradas, O(1) cada una. Total O(r).

    El costo de mantencion es O(1) porque el conteo de cargos es d directo. El
    modelo alternativo, recorrer cada dia evaluando su dia de semana y el cargo
    triple, es O(d) por fila, O(r * d) en la hoja, y en Excel exige INDIRECT, que
    es volatil y obliga a recalcular todo ante cualquier edicion. Medido contra
    el historial entrega la MISMA desviacion que la forma cerrada (0,3% en la
    operacion de control), asi que O(1) domina.

Agregados: O(r) para las sumas de totales, el monto controlado por SUMPRODUCT y cada
predicado de la franja de validacion (su cantidad es constante).

Total del recalculo: O(k * n + r), acotado por constantes del catalogo, de modo que
en la practica es tiempo constante.

    uv run --with MetaTrader5 --with openpyxl --with pillow --with tzdata \
        python scripts/simulador_gi.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import MetaTrader5 as mt5
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
from openpyxl.worksheet.datavalidation import DataValidation

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
CARPETA = REPO / "calculadoras excel"
DESTINO = CARPETA / "Simulador GI.xlsx"
LOGO = CARPETA / "assets" / "logo_gi.png"

AHORA = datetime.now(ZoneInfo("America/Santiago"))
SELLO = AHORA.strftime("%Y-%m-%d %H:%M")

# swap_mode de MT5: solo estos dos aparecen en el catalogo (verificado 2026-08-19).
# 1 = puntos por dia por lote. 5 = interes anual sobre el nocional, ano bancario 360.
MODO_PUNTOS, MODO_INTERES = 1, 5

# ---------------------------------------------------------------- datos MT5
assert mt5.initialize(), mt5.last_error()
cuenta = mt5.account_info()

cat = json.loads((REPO / "config" / "activos.json").read_text(encoding="utf-8"))
catalogo = [(a["ticker_mt5"], a["nombre"]) for a in cat["forex_commodities"] + cat["indices"]]
catalogo += [(a["ticker_mt5"], a["nombre"]) for s in cat["acciones"].values() for a in s["componentes"]]

filas = []
for ticker, nombre in catalogo:
    s = mt5.symbol_info(ticker)
    if s is None or not s.visible:
        mt5.symbol_select(ticker, True)
        s = mt5.symbol_info(ticker)
    if s is None:
        print("  ! sin datos:", ticker)
        continue
    tick = mt5.symbol_info_tick(ticker)
    precio = (tick.ask if tick else 0) or s.ask
    if not precio:
        print("  ! sin precio:", ticker)
        continue

    # CLP que vale mover el precio 1,0 con 1 lote. Trae dentro el tamano de contrato
    # Y la conversion a pesos, asi que una sola constante sirve para cualquier activo.
    # order_calc_profit y no tick_value: tick_value miente en los CFD de acciones.
    clp_unidad = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, ticker, 1.0, precio, precio + 1.0)
    margen_lote = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, ticker, 1.0, precio)
    if not clp_unidad or not margen_lote:
        print("  ! sin calculo:", ticker)
        continue
    if s.swap_mode not in (MODO_PUNTOS, MODO_INTERES):
        print("  ! modo de swap no soportado en %s: %d" % (ticker, s.swap_mode))

    filas.append({
        "nombre": nombre, "ticker": ticker, "digits": s.digits,
        "contrato": s.trade_contract_size, "clp_unidad": clp_unidad,
        "tasa": margen_lote / (clp_unidad * precio),
        "spread": (s.spread or 0) * s.point, "precio": precio,
        "swap_modo": s.swap_mode, "swap_largo": s.swap_long, "swap_corto": s.swap_short,
    })

# umbrales de margen de la cuenta, en porcentaje (margin_so_mode = 0)
LLAMADA, CIERRE_FORZADO = cuenta.margin_so_call, cuenta.margin_so_so

mt5.shutdown()
print("instrumentos con datos: %d de %d" % (len(filas), len(catalogo)))
print("umbrales del broker: llamada %s%% · cierre forzado %s%%" % (LLAMADA, CIERRE_FORZADO))

# ------------------------------------------------------------------ estilos
NAVY, ACENTO, ORO, CREMA = "203864", "50C0A8", "BF8F00", "FFF2CC"
BLANCO, GRIS, ROJO, TENUE = "FFFFFF", "F2F2F2", "C00000", "595959"
borde = Border(*[Side(style="thin", color="BFBFBF")] * 4)
CLP, PRECIO, LOTES, ENTERO, VECES = '"$"#,##0', "#,##0.00###", "0.00", "0", "0.0"
NIVEL, ADVERSO = '0"%"', '0.00"%"'
VECES_CIERRE = '0.0" veces"'

OPS = list(range(11, 17))     # seis operaciones, como la planilla original
TOT = 17

wb = Workbook()

# ============================================================== hoja Datos
dat = wb.create_sheet("Datos")
enc = ["INSTRUMENTO", "TICKER MT5", "DECIMALES", "TAMAÑO DE CONTRATO (1 lote)",
       "VALOR EN CLP DE 1,0 DE PRECIO (POR LOTE)", "MARGEN", "SPREAD",
       "PRECIO DE REFERENCIA", "MODO SWAP", "SWAP COMPRA", "SWAP VENTA"]
for i, t in enumerate(enc, start=1):
    c = dat.cell(row=1, column=i, value=t)
    c.font = Font(bold=True, color=BLANCO, size=9)
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
for r, f in enumerate(filas, start=2):
    for col, val in enumerate([f["nombre"], f["ticker"], f["digits"], f["contrato"],
                               round(f["clp_unidad"], 4), round(f["tasa"], 6), f["spread"],
                               f["precio"], f["swap_modo"], f["swap_largo"],
                               f["swap_corto"]], start=1):
        dat.cell(row=r, column=col, value=val)
    dat.cell(row=r, column=6).number_format = "0.00%"
    dat.cell(row=r, column=7).number_format = PRECIO
    dat.cell(row=r, column=8).number_format = PRECIO
ultima = len(filas) + 1
nota = dat.cell(row=ultima + 2, column=1, value=(
    "Actualizado desde MT5 (cuenta %s, %s) el %s hora Chile. No editar a mano: "
    "se regenera con scripts/simulador_gi.py. MODO SWAP 1 = puntos por día por lote; "
    "5 = interés anual sobre el nocional (año de 360 días)."
    % (cuenta.login, cuenta.currency, SELLO)))
nota.font = Font(italic=True, size=9, color="808080")
for col, w in zip("ABCDEFGHIJK", (26, 12, 11, 17, 21, 10, 11, 13, 11, 13, 13)):
    dat.column_dimensions[col].width = w
dat.freeze_panes = "A2"

# =========================================================== hoja Simulador
ws = wb.active
ws.title = "Simulador"
ws.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGHIJKLMNO",
                  (3, 3, 13, 14, 14, 16, 13, 13, 11, 14, 15, 16, 15, 26, 3)):
    ws.column_dimensions[col].width = w


def estilar(c, fmt="General", size=11, negrita=False, color="000000",
            fondo=None, editable=False, wrap=False, izq=False):
    c.font = Font(bold=negrita, size=size, color=color)
    c.number_format = fmt
    c.alignment = Alignment(horizontal="left" if izq else "center",
                            vertical="center", wrap_text=wrap)
    if fondo:
        c.fill = PatternFill("solid", fgColor=fondo)
    c.border = borde
    if editable:
        c.protection = Protection(locked=False)
    return c


def entrada(ref, valor, fmt):
    """Celda editable: crema y azul, desbloqueada bajo la proteccion de hoja."""
    ws[ref].value = valor
    return estilar(ws[ref], fmt, negrita=True, color="0000C0", fondo=CREMA, editable=True)


def salida(ref, formula, fmt, size=11, negrita=True):
    ws[ref].value = formula
    return estilar(ws[ref], fmt, size=size, negrita=negrita, fondo=GRIS)


def banda(rango, texto, fondo, color, size, alto, italica=False, izq=False):
    """Titulo de ancho completo. En celda combinada el estilo va en TODAS las celdas."""
    ws.merge_cells(rango)
    ini, fin = rango.split(":")
    ws[ini].value = texto
    fila = int("".join(ch for ch in ini if ch.isdigit()))
    for o in range(ord(ini[0]), ord(fin[0]) + 1):
        c = ws["%s%d" % (chr(o), fila)]
        c.fill = PatternFill("solid", fgColor=fondo)
        c.font = Font(bold=not italica, italic=italica, size=size, color=color)
        c.alignment = Alignment(horizontal="left" if izq else "center",
                                vertical="center", wrap_text=True)
    ws.row_dimensions[fila].height = alto


# --- encabezado
banda("C1:M1", "SIMULADOR DE OPERACIONES", NAVY, BLANCO, 18, 34)
banda("C2:M2", "Se escribe el volumen en lotes, la unidad del terminal. La planilla "
               "calcula el margen que bloquea, el apalancamiento y los costos.",
      BLANCO, TENUE, 10, 24, italica=True)
if LOGO.exists():
    img = XLImage(str(LOGO))
    img.height, img.width = 62, 67
    ws.add_image(img, "N1")

# --- contexto del periodo
for r, etiqueta, valor, fmt in [
        (4, "1 · Instrumento", filas[0]["nombre"], "General"),
        (5, "2 · Capital de la cuenta", 2000000, CLP)]:
    ws.merge_cells("C%d:E%d" % (r, r))
    ws["C%d" % r].value = etiqueta
    ws["C%d" % r].font = Font(bold=True, size=11)
    ws["C%d" % r].alignment = Alignment(vertical="center")
    ws.merge_cells("F%d:G%d" % (r, r))
    entrada("F%d" % r, valor, fmt)
    ws["G%d" % r].fill = PatternFill("solid", fgColor=CREMA)
    ws["G%d" % r].border = borde
    ws["G%d" % r].protection = Protection(locked=False)
    ws.row_dimensions[r].height = 26

# --- helpers ocultos que resuelven el instrumento elegido
BUSCA = "=IFERROR(VLOOKUP($F$4,Datos!$A:$K,%d,FALSE),0)"
for r, idx, etiqueta in [(1, 2, "ticker"), (2, 3, "digits"), (3, 4, "contrato"),
                         (4, 5, "clp_unidad"), (5, 6, "tasa"), (6, 7, "spread"),
                         (7, 8, "precio_ref"), (8, 9, "swap_modo"),
                         (9, 10, "swap_compra"), (10, 11, "swap_venta")]:
    ws["Q%d" % r] = etiqueta
    ws["R%d" % r] = BUSCA % idx
ws["Q11"], ws["R11"] = "llamada_margen", LLAMADA
ws["Q12"], ws["R12"] = "cierre_forzado", CIERRE_FORZADO
for col in "QR":
    ws.column_dimensions[col].hidden = True

# --- referencias del instrumento elegido
for r, etiqueta, formula, fmt in [
        (4, "Precio de referencia", "=$R$7", PRECIO),
        (5, "Capital mínimo por operación (0,01 lotes)", "=0.01*$R$7*$R$4*$R$5", CLP),
        # el spread se congela al generar el archivo, asi que va a la vista: si se
        # genero en un momento de spread ancho, todas las simulaciones lo heredan.
        (6, "Spread vigente al generar", "=$R$6", PRECIO)]:
    ws.merge_cells("J%d:L%d" % (r, r))
    ws["J%d" % r].value = etiqueta
    ws["J%d" % r].font = Font(size=10, color=TENUE)
    ws["J%d" % r].alignment = Alignment(horizontal="right", vertical="center")
    salida("M%d" % r, formula, fmt)

# --- franja de validacion
ws.merge_cells("C7:N7")
ws["C7"].value = (
    '=IF($F$4="","⚠ Seleccione un instrumento de la lista.",'
    # el separador decimal de un Excel en español es la coma: un valor digitado con
    # punto queda como TEXTO y toda la fila cae en #¡VALOR!. La validación de celda lo
    # rechaza al escribirlo, pero no se dispara al pegar, así que hace falta el control
    'IF(SUMPRODUCT(--ISTEXT($D$11:$D$16))+SUMPRODUCT(--ISTEXT($G$11:$H$16))'
    '+SUMPRODUCT(--ISTEXT($I$11:$I$16))>0,'
    '"⚠ Hay un valor escrito como texto. El separador decimal de este Excel es la '
    'coma: escriba 0,54 y no 0.54.",'
    'IF(SUMPRODUCT(($D$11:$D$16>0)*($G$11:$G$16=0))>0,'
    '"⚠ Hay una operación con volumen y sin precio de entrada.",'
    'IF(SUMPRODUCT(($G$11:$G$16>0)*(ABS($G$11:$G$16/$R$7-1)>0.1))>0,'
    '"⚠ Un precio de entrada difiere en más de 10% del precio de referencia ($"'
    '&FIXED($R$7,$R$2)&"). Verifique que corresponda al instrumento seleccionado.",'
    'IF(SUMPRODUCT(--(MOD(ROUND($D$11:$D$16*100,6),1)<>0))>0,'
    '"⚠ Hay un volumen que no es múltiplo de 0,01 lotes, el paso mínimo de MT5.",'
    'IF($M$21>$F$5,"⚠ El margen requerido excede el capital de la cuenta.",'
    '"✓ "&COUNTIF($D$11:$D$16,">0")&" operación(es) sobre "&$R$1'
    '&". El volumen en lotes es el que se ingresa en MT5."))))))'
)
for cc in "CDEFGHIJKLMN":
    ws["%s7" % cc].fill = PatternFill("solid", fgColor=CREMA)
    ws["%s7" % cc].border = borde
ws["C7"].font = Font(bold=True, size=11)
ws["C7"].alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[7].height = 30

# --- bandas de bloque: la separacion simulacion / costos de la planilla original
banda("C9:J9", "SIMULACIÓN", NAVY, BLANCO, 12, 24)
banda("K9:M9", "COSTOS", ORO, BLANCO, 12, 24)
ws["N9"].fill = PatternFill("solid", fgColor=NAVY)
ws["N9"].border = borde

# --- encabezados de columna
cabeceras = [("C", "DIRECCIÓN", ACENTO), ("D", "VOLUMEN EN LOTES", ACENTO),
             ("E", "MARGEN REQUERIDO", ACENTO), ("F", "APALANCAMIENTO (VECES)", ACENTO),
             ("G", "PRECIO DE ENTRADA", ACENTO), ("H", "PRECIO DE SALIDA", ACENTO),
             ("I", "DÍAS ABIERTA", ACENTO), ("J", "RESULTADO BRUTO", ACENTO),
             ("K", "COSTO DE APERTURA (SPREAD)", ORO),
             ("L", "COSTO DE MANTENCIÓN (SWAP)", ORO),
             ("M", "RESULTADO NETO", ORO), ("N", "OBSERVACIÓN", ACENTO)]
for col, txt, fondo in cabeceras:
    estilar(ws["%s10" % col], size=9, negrita=True, color=BLANCO, fondo=fondo, wrap=True)
    ws["%s10" % col].value = txt
ws.row_dimensions[10].height = 34

# --- ejemplo: tres operaciones del periodo, la ultima perdedora
d, base = filas[0]["digits"], round(filas[0]["precio"], filas[0]["digits"])
ejemplo = [("COMPRA", 0.54, base - 3, base + 2, 2),
           ("VENTA", 0.43, base + 4, base + 1, 1),
           ("COMPRA", 0.32, base, base - 1.5, 0)]

for i, r in enumerate(OPS):
    if i < len(ejemplo):
        direccion, lotes, ent, sal, dias = ejemplo[i]
        entrada("C%d" % r, direccion, "General")
        entrada("D%d" % r, lotes, LOTES)
        entrada("G%d" % r, round(ent, d), PRECIO)
        entrada("H%d" % r, round(sal, d), PRECIO)
        entrada("I%d" % r, dias, ENTERO)
    else:
        for col, fmt in (("C", "General"), ("D", LOTES),
                         ("G", PRECIO), ("H", PRECIO), ("I", ENTERO)):
            entrada("%s%d" % (col, r), None, fmt)

    # el margen que ese volumen bloquea al precio de entrada de la fila. NO es el
    # volumen expresado en pesos: el equivalente en pesos de un volumen es el nocional,
    # que es este mismo producto SIN la tasa de margen.
    salida("E%d" % r, '=IF($D{r}=0,"",$D{r}*$G{r}*$R$4*$R$5)'.format(r=r), CLP)
    # apalancamiento = nocional / capital de la cuenta. Es aditivo, asi que el total de
    # la columna es el apalancamiento del periodo.
    salida("F%d" % r, '=IF(OR($D{r}=0,$F$5=0),"",$D{r}*$G{r}*$R$4/$F$5)'.format(r=r), VECES)
    salida("J%d" % r, ('=IF(OR($D{r}=0,$H{r}=0),"",IF($C{r}="COMPRA",$H{r}-$G{r},'
                       '$G{r}-$H{r})*$D{r}*$R$4)').format(r=r), CLP)
    salida("K%d" % r, '=IF($D{r}=0,"",$D{r}*$R$6*$R$4)'.format(r=r), CLP)
    # costo de mantencion, por dias calendario. NO se suman dias por el cargo triple:
    # ese triple REEMPLAZA los rollovers del fin de semana, que no ocurren, asi que una
    # semana completa son 7 cargos para 7 dias calendario. Verificado 2026-08-19 contra
    # el historial: posicion 590040, #AAPL BUY 2,98 lotes del 05 al 11 de agosto, 6 dias
    # con un fin de semana completo dentro; el terminal cobro 36.063,35 y esta formula
    # da 36.163,34, o sea 0,3% de desviacion. Se niega en vez de usar ABS para que una
    # tasa positiva quede como abono y no como costo.
    salida("L%d" % r, ('=IF(OR($D{r}=0,$I{r}=0),"",-IF($C{r}="VENTA",$R$10,$R$9)'
                       '*IF($R$8={pts},$D{r}*POWER(10,-$R$2)*$R$4,'
                       '$D{r}*$G{r}*$R$4/100/360)*$I{r})').format(r=r, pts=MODO_PUNTOS), CLP)
    salida("M%d" % r, '=IF($D{r}=0,"",N($J{r})-N($K{r})-N($L{r}))'.format(r=r), CLP)
    obs = salida("N%d" % r, (
        '=IF(OR($D{r}=0,$H{r}=0),"",IF(AND($C{r}="COMPRA",$H{r}<$G{r}),'
        '"precio de salida inferior a la entrada: resultado negativo en una compra",'
        'IF(AND($C{r}="VENTA",$H{r}>$G{r}),'
        '"precio de salida superior a la entrada: resultado negativo en una venta","")))'
    ).format(r=r), "General", size=9, negrita=False)
    obs.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 24

# --- totales
ws["C%d" % TOT].value = "TOTALES"
FORMATO_TOTAL = {"D": LOTES, "E": CLP, "F": VECES, "J": CLP, "K": CLP, "L": CLP, "M": CLP}
for col in "CDEFGHIJKLMN":
    c = ws["%s%d" % (col, TOT)]
    if col in FORMATO_TOTAL:
        c.value = "=SUM(%s11:%s16)" % (col, col)
        c.number_format = FORMATO_TOTAL[col]
    c.fill = PatternFill("solid", fgColor=ORO if col in "KLM" else NAVY)
    c.font = Font(bold=True, size=11, color=BLANCO)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = borde
ws.row_dimensions[TOT].height = 24

# --- cierre del periodo
cierre = [
    (19, "Monto total controlado", "=SUMPRODUCT($D$11:$D$16,$G$11:$G$16)*$R$4", CLP),
    # el apalancamiento del periodo es la suma de la columna, por ser aditivo
    (20, "Apalancamiento total", "=$F$17", VECES_CIERRE),
    (21, "Margen requerido (posiciones simultáneas)", "=$M$19*$R$5", CLP),
    # nivel de margen tal como lo reporta MT5: patrimonio sobre margen usado. Al abrir,
    # el patrimonio es el capital, porque todavia no hay resultado flotante.
    (22, "Nivel de margen al abrir", '=IF($M$21=0,"",100*$F$5/$M$21)', NIVEL),
    # lo que la columna de apalancamiento provoca preguntar, respondido con la mecanica
    # del margen y sin necesidad de stop loss
    (23, "Movimiento adverso hasta la llamada a margen",
     '=IF($M$19=0,"",100*($F$5-$R$11/100*$M$21)/$M$19)', ADVERSO),
    (24, "Resultado neto del periodo", "=$M$17", CLP),
    (25, "Patrimonio final", "=$F$5+$M$17", CLP),
]
for r, etiqueta, formula, fmt in cierre:
    ws.merge_cells("J%d:L%d" % (r, r))
    ws["J%d" % r].value = etiqueta
    ws["J%d" % r].font = Font(bold=(r == 25), size=11)
    ws["J%d" % r].alignment = Alignment(horizontal="right", vertical="center")
    c = salida("M%d" % r, formula, fmt, size=13 if r == 25 else 11)
    if r == 25:
        c.fill = PatternFill("solid", fgColor=CREMA)
    ws.row_dimensions[r].height = 22

# --- rojo cuando pierde, y en las observaciones
ws.conditional_formatting.add("J11:M%d" % TOT,
                              FormulaRule(formula=['AND(J11<>"",J11<0)'],
                                          font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("N11:N16",
                              FormulaRule(formula=['$N11<>""'], font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("M25", FormulaRule(formula=["$M$25<$F$5"],
                                                 font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("M22", FormulaRule(formula=["$M$22<$R$11"],
                                                 font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("M23", FormulaRule(formula=["$M$23<=0"],
                                                 font=Font(bold=True, color=ROJO)))

# --- pie
banda("C27:N27",
      "Especificaciones del broker al %s hora Chile. Celdas crema: campos editables; "
      "el resto son fórmulas. El volumen en lotes se escribe en múltiplos de 0,01, el "
      "paso que acepta MT5. APALANCAMIENTO son las veces que el capital de la cuenta "
      "queda controlado por esa operación, y la columna es aditiva: su total es el "
      "apalancamiento del periodo. El COSTO DE MANTENCIÓN (SWAP) se estima por días "
      "calendario. El broker llama a margen cuando el nivel baja de %g%% y cierra "
      "posiciones en %g%%. Este simulador no incorpora stop loss."
      % (SELLO, LLAMADA, CIERRE_FORZADO),
      BLANCO, "808080", 9, 30, italica=True, izq=True)

# --- listas y validaciones (formula1 sin "=": con el igual Excel descarta la validación)
validaciones = [
    (DataValidation(type="list", formula1="Datos!$A$2:$A$%d" % ultima, allow_blank=False,
                    showErrorMessage=True, errorTitle="Instrumento no válido",
                    error="Seleccione un instrumento de la lista."), ["F4"]),
    (DataValidation(type="list", formula1='"COMPRA,VENTA"', allow_blank=True,
                    showErrorMessage=True, errorTitle="Dirección no válida",
                    error="Seleccione COMPRA o VENTA."), ["C%d" % r for r in OPS]),
    (DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0.01",
                    allow_blank=True, showErrorMessage=True, errorTitle="Volumen no válido",
                    error="El volumen mínimo que acepta MT5 es 0,01 lotes, en múltiplos "
                          "de 0,01. Use la coma como separador decimal: 0,54 y no 0.54."),
     ["D%d" % r for r in OPS]),
    (DataValidation(type="decimal", operator="greaterThan", formula1="0",
                    allow_blank=True, showErrorMessage=True, errorTitle="Precio no válido",
                    error="Escriba un precio numérico, con la coma como separador "
                          "decimal: 918,75 y no 918.75."),
     ["%s%d" % (c, r) for r in OPS for c in "GH"]),
    (DataValidation(type="whole", operator="between", formula1="0", formula2="3650",
                    allow_blank=True, showErrorMessage=True, errorTitle="Días no válidos",
                    error="Indique los días completos que la posición queda abierta "
                          "(0 si se abre y cierra en la misma jornada)."),
     ["I%d" % r for r in OPS]),
    (DataValidation(type="decimal", operator="greaterThan", formula1="0",
                    allow_blank=False, showErrorMessage=True,
                    errorTitle="Capital no válido",
                    error="Escriba el capital de la cuenta en pesos, sin separador "
                          "decimal."), ["F5"]),
]
for dv, refs in validaciones:
    ws.add_data_validation(dv)
    for ref in refs:
        dv.add(ws[ref])

# --- proteger todo menos las celdas crema
ws.protection.sheet = True
ws.protection.formatCells = False
ws.print_area = "B1:O28"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToPage = True
ws.sheet_properties.pageSetUpPr.fitToPage = True

CARPETA.mkdir(parents=True, exist_ok=True)
wb.save(DESTINO)
print("generado:", DESTINO)
print("ejemplo:", filas[0]["nombre"], "con 3 operaciones alrededor de", base)
