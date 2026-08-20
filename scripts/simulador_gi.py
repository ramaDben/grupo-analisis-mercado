# -*- coding: utf-8 -*-
"""Genera el Simulador GI: una hoja donde el ejecutivo elige el instrumento de una
lista y registra las operaciones del periodo, sin tener que conocer el tamano de
contrato ni el spread vigente.

La tabla separa SIMULACION de COSTOS, como la planilla original de post-venta, y
VOLUMEN EN CLP / VOLUMEN EN LOTES son columnas gemelas: la misma magnitud en dos
unidades. Su sincronizacion bidireccional la hace la macro de assets/gemelas.bas,
porque dos celdas no pueden ser a la vez editables y calculadas sin caer en
referencia circular. Sin la macro, la columna que manda es VOLUMEN EN LOTES: todas
las formulas de la fila leen de ella.

Cada fila es una operacion independiente con su propia direccion, y los dias de
mantencion alimentan el swap. Los 25 instrumentos del catalogo se leen del terminal
MT5 y quedan en la hoja Datos, que alimenta los BUSCARV de la hoja Simulador.

Complejidad
-----------
Variables: n = instrumentos del catalogo (25) · k = parametros resueltos por
instrumento (10 celdas BUSCARV) · r = filas de operacion (6) · d = dias de
mantencion de una operacion.

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

Por fila de operacion:
    resultado bruto, costo de apertura, costo de mantencion y resultado neto son
    formulas cerradas, O(1) cada una. Total O(r).

    El costo de mantencion es O(1) porque el conteo de cargos es d directo. El
    modelo alternativo, recorrer cada dia evaluando su dia de semana y el cargo
    triple, es O(d) por fila, O(r * d) en la hoja, y en Excel exige INDIRECT, que
    es volatil y obliga a recalcular todo ante cualquier edicion. Medido contra
    el historial entrega la MISMA desviacion que la forma cerrada (0,3% en la
    operacion de control), asi que O(1) domina: menos trabajo, sin volatilidad y
    sin ganancia de exactitud que lo justifique.

Sincronizacion de las gemelas (macro): O(1) por celda editada. El evento se
restringe al rango de las tres columnas implicadas, de modo que una edicion en
cualquier otra parte de la hoja no ejecuta codigo.

Agregados: O(r) para las sumas de totales, la exposicion por SUMPRODUCT y cada
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
MACRO = CARPETA / "assets" / "gemelas.bas"

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

mt5.shutdown()
print("instrumentos con datos: %d de %d" % (len(filas), len(catalogo)))

# ------------------------------------------------------------------ estilos
NAVY, ACENTO, ORO, CREMA = "203864", "50C0A8", "BF8F00", "FFF2CC"
BLANCO, GRIS, ROJO, TENUE = "FFFFFF", "F2F2F2", "C00000", "595959"
borde = Border(*[Side(style="thin", color="BFBFBF")] * 4)
CLP, PRECIO, LOTES, ENTERO = '"$"#,##0', "#,##0.00###", "0.00", "0"

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
for col, w in zip("ABCDEFGHIJKLMN",
                  (3, 3, 13, 15, 15, 13, 13, 13, 14, 15, 16, 15, 26, 3)):
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
banda("C1:L1", "SIMULADOR DE OPERACIONES", NAVY, BLANCO, 18, 34)
banda("C2:L2", "Seleccione el instrumento y registre las operaciones del periodo. "
               "El volumen en pesos y el volumen en lotes son la misma magnitud: al "
               "modificar uno, el otro se ajusta.", BLANCO, TENUE, 10, 20, italica=True)
if LOGO.exists():
    img = XLImage(str(LOGO))
    img.height, img.width = 62, 67
    ws.add_image(img, "M1")

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
    ws["O%d" % r] = etiqueta
    ws["P%d" % r] = BUSCA % idx
for col in "OP":
    ws.column_dimensions[col].hidden = True

# --- referencias del instrumento elegido
for r, etiqueta, formula, fmt in [
        (4, "Precio de referencia", "=$P$7", PRECIO),
        (5, "Capital mínimo por operación (0,01 lotes)", "=0.01*$P$7*$P$4*$P$5", CLP),
        # el spread se congela al generar el archivo, asi que va a la vista: si se
        # genero en un momento de spread ancho, todas las simulaciones lo heredan.
        (6, "Spread vigente al generar", "=$P$6", PRECIO)]:
    ws.merge_cells("I%d:K%d" % (r, r))
    ws["I%d" % r].value = etiqueta
    ws["I%d" % r].font = Font(size=10, color=TENUE)
    ws["I%d" % r].alignment = Alignment(horizontal="right", vertical="center")
    salida("L%d" % r, formula, fmt)

# --- franja de validacion
ws.merge_cells("C7:M7")
ws["C7"].value = (
    '=IF($F$4="","⚠ Seleccione un instrumento de la lista.",'
    'IF(SUMPRODUCT(($E$11:$E$16>0)*($F$11:$F$16=0))>0,'
    '"⚠ Hay una operación con volumen y sin precio de entrada.",'
    'IF(SUMPRODUCT(($F$11:$F$16>0)*(ABS($F$11:$F$16/$P$7-1)>0.1))>0,'
    '"⚠ Un precio de entrada difiere en más de 10% del precio de referencia ($"'
    '&FIXED($P$7,$P$2)&"). Verifique que corresponda al instrumento seleccionado.",'
    'IF(SUMPRODUCT(($D$11:$D$16>0)*($E$11:$E$16=0))>0,'
    '"⚠ Hay una operación bajo el volumen mínimo de 0,01 lotes, que requiere $"'
    '&FIXED(0.01*$P$7*$P$4*$P$5,0)&".",'
    'IF($L$20>$F$5,"⚠ El margen requerido excede el capital de la cuenta.",'
    '"✓ "&COUNTIF($E$11:$E$16,">0")&" operación(es) sobre "&$P$1'
    '&". El volumen en lotes es el que se ingresa en MT5.")))))'
)
for cc in "CDEFGHIJKLM":
    ws["%s7" % cc].fill = PatternFill("solid", fgColor=CREMA)
    ws["%s7" % cc].border = borde
ws["C7"].font = Font(bold=True, size=11)
ws["C7"].alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[7].height = 30

# --- bandas de bloque: la separacion simulacion / costos de la planilla original
banda("C9:I9", "SIMULACIÓN", NAVY, BLANCO, 12, 24)
banda("J9:L9", "COSTOS", ORO, BLANCO, 12, 24)
ws["M9"].fill = PatternFill("solid", fgColor=NAVY)
ws["M9"].border = borde

# --- encabezados de columna
cabeceras = [("C", "DIRECCIÓN", ACENTO), ("D", "VOLUMEN EN CLP", ACENTO),
             ("E", "VOLUMEN EN LOTES", ACENTO), ("F", "PRECIO DE ENTRADA", ACENTO),
             ("G", "PRECIO DE SALIDA", ACENTO), ("H", "DÍAS DE MANTENCIÓN", ACENTO),
             ("I", "RESULTADO BRUTO", ACENTO),
             ("J", "COSTO DE APERTURA (SPREAD)", ORO),
             ("K", "COSTO DE MANTENCIÓN (SWAP)", ORO),
             ("L", "RESULTADO NETO", ORO), ("M", "OBSERVACIÓN", ACENTO)]
for col, txt, fondo in cabeceras:
    estilar(ws["%s10" % col], size=9, negrita=True, color=BLANCO, fondo=fondo, wrap=True)
    ws["%s10" % col].value = txt
ws.row_dimensions[10].height = 34

# --- ejemplo: tres operaciones del periodo, la ultima perdedora
d, base = filas[0]["digits"], round(filas[0]["precio"], filas[0]["digits"])
por_lote = filas[0]["clp_unidad"] * filas[0]["tasa"]   # margen por lote y por 1,0 de precio
ejemplo = [("COMPRA", 0.54, base - 3, base + 2, 2),
           ("VENTA", 0.43, base + 4, base + 1, 1),
           ("COMPRA", 0.32, base, base - 1.5, 0)]

for i, r in enumerate(OPS):
    if i < len(ejemplo):
        direccion, lotes, ent, sal, dias = ejemplo[i]
        entrada("C%d" % r, direccion, "General")
        entrada("D%d" % r, round(lotes * ent * por_lote), CLP)
        entrada("E%d" % r, lotes, LOTES)
        entrada("F%d" % r, round(ent, d), PRECIO)
        entrada("G%d" % r, round(sal, d), PRECIO)
        entrada("H%d" % r, dias, ENTERO)
    else:
        for col, fmt in (("C", "General"), ("D", CLP), ("E", LOTES),
                         ("F", PRECIO), ("G", PRECIO), ("H", ENTERO)):
            entrada("%s%d" % (col, r), None, fmt)

    # todas las formulas leen el VOLUMEN EN LOTES: es la columna que manda
    salida("I%d" % r, ('=IF(OR($E{r}=0,$G{r}=0),"",IF($C{r}="COMPRA",$G{r}-$F{r},'
                       '$F{r}-$G{r})*$E{r}*$P$4)').format(r=r), CLP)
    salida("J%d" % r, '=IF($E{r}=0,"",$E{r}*$P$6*$P$4)'.format(r=r), CLP)
    # costo de mantencion, por dias calendario. NO se suman dias por el cargo triple:
    # ese triple REEMPLAZA los rollovers del fin de semana, que no ocurren, asi que una
    # semana completa son 7 cargos para 7 dias calendario. Verificado 2026-08-19 contra
    # el historial: posicion 590040, #AAPL BUY 2,98 lotes del 05 al 11 de agosto, 6 dias
    # con un fin de semana completo dentro; el terminal cobro 36.063,35 y esta formula
    # da 36.163,34, o sea 0,3% de desviacion. Forma cerrada O(1) frente a O(d) del
    # conteo por dia de semana, con la misma exactitud medida: ver Complejidad arriba.
    # Se niega en vez de usar ABS para que una tasa positiva quede como abono.
    salida("K%d" % r, ('=IF(OR($E{r}=0,$H{r}=0),"",-IF($C{r}="VENTA",$P$10,$P$9)'
                       '*IF($P$8={pts},$E{r}*POWER(10,-$P$2)*$P$4,'
                       '$E{r}*$F{r}*$P$4/100/360)*$H{r})').format(r=r, pts=MODO_PUNTOS), CLP)
    salida("L%d" % r, '=IF($E{r}=0,"",N($I{r})-N($J{r})-N($K{r}))'.format(r=r), CLP)
    obs = salida("M%d" % r, (
        '=IF(OR($E{r}=0,$G{r}=0),"",IF(AND($C{r}="COMPRA",$G{r}<$F{r}),'
        '"precio de salida inferior a la entrada: resultado negativo en una compra",'
        'IF(AND($C{r}="VENTA",$G{r}>$F{r}),'
        '"precio de salida superior a la entrada: resultado negativo en una venta","")))'
    ).format(r=r), "General", size=9, negrita=False)
    obs.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 24

# --- totales
ws["C%d" % TOT].value = "TOTALES"
for col in "CDEFGHIJKLM":
    c = ws["%s%d" % (col, TOT)]
    if col in "DEIJKL":
        c.value = "=SUM(%s11:%s16)" % (col, col)
        c.number_format = LOTES if col == "E" else CLP
    c.fill = PatternFill("solid", fgColor=ORO if col in "JKL" else NAVY)
    c.font = Font(bold=True, size=11, color=BLANCO)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = borde
ws.row_dimensions[TOT].height = 24

# --- cierre del periodo
cierre = [
    (19, "Exposición nocional total", "=SUMPRODUCT($E$11:$E$16,$F$11:$F$16)*$P$4"),
    # sobre el volumen en lotes, no sobre la suma de importes ingresados
    (20, "Margen requerido (posiciones simultáneas)", "=$L$19*$P$5"),
    (21, "Resultado neto del periodo", "=$L$17"),
    (22, "Patrimonio final", "=$F$5+$L$17"),
]
for r, etiqueta, formula in cierre:
    ws.merge_cells("I%d:K%d" % (r, r))
    ws["I%d" % r].value = etiqueta
    ws["I%d" % r].font = Font(bold=(r == 22), size=11)
    ws["I%d" % r].alignment = Alignment(horizontal="right", vertical="center")
    c = salida("L%d" % r, formula, CLP, size=13 if r == 22 else 11)
    if r == 22:
        c.fill = PatternFill("solid", fgColor=CREMA)
    ws.row_dimensions[r].height = 22

# --- rojo cuando pierde, y en las observaciones
ws.conditional_formatting.add("I11:L%d" % TOT,
                              FormulaRule(formula=['AND(I11<>"",I11<0)'],
                                          font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("M11:M16",
                              FormulaRule(formula=['$M11<>""'], font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("L22", FormulaRule(formula=["$L$22<$F$5"],
                                                 font=Font(bold=True, color=ROJO)))

# --- pie
banda("C24:M24",
      "Especificaciones del broker al %s hora Chile. Celdas crema: campos editables; "
      "el resto son fórmulas. VOLUMEN EN CLP y VOLUMEN EN LOTES son gemelas y se "
      "sincronizan con la macro del archivo: el importe se homologa al equivalente "
      "exacto del volumen, cuyo paso mínimo es 0,01 lotes. El COSTO DE MANTENCIÓN "
      "(SWAP) se estima por días calendario. Este simulador no incorpora stop loss."
      % SELLO, BLANCO, "808080", 9, 30, italica=True, izq=True)

# --- listas y validaciones (formula1 sin "=": con el igual Excel descarta la validación)
validaciones = [
    (DataValidation(type="list", formula1="Datos!$A$2:$A$%d" % ultima, allow_blank=False,
                    showErrorMessage=True, errorTitle="Instrumento no válido",
                    error="Seleccione un instrumento de la lista."), ["F4"]),
    (DataValidation(type="list", formula1='"COMPRA,VENTA"', allow_blank=True,
                    showErrorMessage=True, errorTitle="Dirección no válida",
                    error="Seleccione COMPRA o VENTA."), ["C%d" % r for r in OPS]),
    (DataValidation(type="whole", operator="between", formula1="0", formula2="3650",
                    allow_blank=True, showErrorMessage=True, errorTitle="Días no válidos",
                    error="Indique los días completos de mantención de la posición "
                          "(0 si se abre y cierra en la misma jornada)."),
     ["H%d" % r for r in OPS]),
    (DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0",
                    allow_blank=True, showErrorMessage=True, errorTitle="Volumen no válido",
                    error="El volumen en lotes no puede ser negativo. El paso mínimo "
                          "es 0,01."), ["E%d" % r for r in OPS]),
]
for dv, refs in validaciones:
    ws.add_data_validation(dv)
    for ref in refs:
        dv.add(ws[ref])

# --- proteger todo menos las celdas crema
ws.protection.sheet = True
ws.protection.formatCells = False
ws.print_area = "B1:N25"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToPage = True
ws.sheet_properties.pageSetUpPr.fitToPage = True

CARPETA.mkdir(parents=True, exist_ok=True)
wb.save(DESTINO)
print("generado:", DESTINO)
print("macro de las gemelas:", MACRO if MACRO.exists() else "FALTA: %s" % MACRO)
print("ejemplo:", filas[0]["nombre"], "con 3 operaciones alrededor de", base)
