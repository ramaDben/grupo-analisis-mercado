# -*- coding: utf-8 -*-
"""Genera el Simulador GI: una hoja donde el ejecutivo elige el activo de una lista
y anota operaciones del periodo, sin tocar lotes ni spread.

Cada fila es una operacion independiente con su propia fecha y su propio COMPRA/VENTA
(como la planilla original de post-venta), y los dias que queda abierta alimentan el
costo de mantencion (swap). Los 25 activos del catalogo se leen del terminal MT5 y
quedan en la hoja Datos, que es la que alimenta los BUSCARV de la hoja Simulador.

    uv run --with MetaTrader5 --with openpyxl --with pillow --with tzdata \
        python scripts/simulador_gi.py
"""
import json
import sys
from datetime import datetime, timedelta
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
DESTINO = REPO / "calculadoras excel" / "Simulador GI (piloto).xlsx"
LOGO = REPO / "calculadoras excel" / "assets" / "logo_gi.png"

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
        "nombre": nombre,
        "ticker": ticker,
        "digits": s.digits,
        "contrato": s.trade_contract_size,
        "clp_unidad": clp_unidad,
        "tasa": margen_lote / (clp_unidad * precio),
        "spread": (s.spread or 0) * s.point,
        "precio": precio,
        "swap_modo": s.swap_mode,
        "swap_largo": s.swap_long,
        "swap_corto": s.swap_short,
    })

mt5.shutdown()
print("activos con datos: %d de %d" % (len(filas), len(catalogo)))

# ------------------------------------------------------------------ estilos
NAVY, ACENTO, CREMA = "203864", "50C0A8", "FFF2CC"
BLANCO, GRIS, ROJO, TENUE = "FFFFFF", "F2F2F2", "C00000", "595959"
borde = Border(*[Side(style="thin", color="BFBFBF")] * 4)
CLP, PRECIO, LOTES, FECHA, ENTERO = '"$"#,##0', "#,##0.00###", "0.00", "dd-mm-yy", "0"

OPS = list(range(10, 16))          # seis operaciones, como la planilla original
TOT = 16                           # fila de totales

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
    dat.cell(row=r, column=1, value=f["nombre"])
    dat.cell(row=r, column=2, value=f["ticker"])
    dat.cell(row=r, column=3, value=f["digits"])
    dat.cell(row=r, column=4, value=f["contrato"])
    dat.cell(row=r, column=5, value=round(f["clp_unidad"], 4))
    dat.cell(row=r, column=6, value=round(f["tasa"], 6)).number_format = "0.00%"
    dat.cell(row=r, column=7, value=f["spread"]).number_format = PRECIO
    dat.cell(row=r, column=8, value=f["precio"]).number_format = PRECIO
    dat.cell(row=r, column=9, value=f["swap_modo"])
    dat.cell(row=r, column=10, value=f["swap_largo"])
    dat.cell(row=r, column=11, value=f["swap_corto"])
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
for col, w in zip("ABCDEFGHIJKLMN", (3, 3, 12, 13, 15, 12, 12, 13, 11, 13, 14, 16, 28, 3)):
    ws.column_dimensions[col].width = w


def estilar(c, fmt="General", size=11, negrita=False, color="000000",
            fondo=None, centrado=True, editable=False, wrap=False):
    c.font = Font(bold=negrita, size=size, color=color)
    c.number_format = fmt
    c.alignment = Alignment(horizontal="center" if centrado else "left",
                            vertical="center", wrap_text=wrap)
    if fondo:
        c.fill = PatternFill("solid", fgColor=fondo)
    c.border = borde
    if editable:
        c.protection = Protection(locked=False)
    return c


def entrada(ref, valor, fmt):
    """Celda editable: crema y azul, desbloqueada bajo la proteccion de hoja."""
    c = ws[ref]
    c.value = valor
    return estilar(c, fmt, size=11, negrita=True, color="0000C0", fondo=CREMA, editable=True)


def salida(ref, formula, fmt, size=11, negrita=True):
    c = ws[ref]
    c.value = formula
    return estilar(c, fmt, size=size, negrita=negrita, fondo=GRIS)


def banda(rango, texto, fondo, color, size, alto, italica=False):
    """Titulo de ancho completo. En celda combinada el estilo va en TODAS las celdas."""
    ws.merge_cells(rango)
    ini, fin = rango.split(":")
    ws[ini].value = texto
    fila = int("".join(ch for ch in ini if ch.isdigit()))
    col_i, col_f = ord(ini[0]), ord(fin[0])
    for o in range(col_i, col_f + 1):
        c = ws["%s%d" % (chr(o), fila)]
        c.fill = PatternFill("solid", fgColor=fondo)
        c.font = Font(bold=not italica, italic=italica, size=size, color=color)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[fila].height = alto


# --- encabezado
banda("C1:L1", "SIMULADOR DE OPERACIONES", NAVY, BLANCO, 18, 34)
banda("C2:L2", "Seleccione el instrumento y registre las operaciones del periodo. "
               "El volumen y los costos se calculan automáticamente.",
      BLANCO, TENUE, 10, 20, italica=True)
if LOGO.exists():
    img = XLImage(str(LOGO))
    img.height, img.width = 62, 67
    ws.add_image(img, "M1")

# --- dos preguntas de contexto
for r, etiqueta, valor, fmt in [
        (4, "1 · Instrumento", filas[0]["nombre"], "General"),
        (5, "2 · Capital de la cuenta", 2000000, CLP)]:
    ws.merge_cells("C%d:E%d" % (r, r))
    ws["C%d" % r].value = etiqueta
    ws["C%d" % r].font = Font(bold=True, size=11)
    ws["C%d" % r].alignment = Alignment(vertical="center")
    ws.merge_cells("F%d:G%d" % (r, r))
    entrada("F%d" % r, valor, fmt)
    for cc in "FG":
        ws["%s%d" % (cc, r)].fill = PatternFill("solid", fgColor=CREMA)
        ws["%s%d" % (cc, r)].border = borde
    ws.row_dimensions[r].height = 26

# --- helpers ocultos que resuelven el activo elegido
BUSCA = "=IFERROR(VLOOKUP($F$4,Datos!$A:$K,%d,FALSE),0)"
for r, idx, etiqueta in [(1, 2, "ticker"), (2, 3, "digits"), (3, 4, "contrato"),
                         (4, 5, "clp_unidad"), (5, 6, "tasa"), (6, 7, "spread"),
                         (7, 8, "precio_ref"), (8, 9, "swap_modo"),
                         (9, 10, "swap_compra"), (10, 11, "swap_venta")]:
    ws["O%d" % r] = etiqueta
    ws["P%d" % r] = BUSCA % idx
for col in "OP":
    ws.column_dimensions[col].hidden = True

# --- referencias del activo elegido, arriba a la derecha
for r, etiqueta, formula, fmt in [
        (4, "Precio de referencia", "=$P$7", PRECIO),
        (5, "Capital mínimo por operación (0,01 lotes)", "=0.01*$P$7*$P$4*$P$5", CLP),
        # el spread se congela al generar el archivo, asi que va a la vista: si se
        # generó en un momento de spread ancho, todas las simulaciones lo heredan.
        (6, "Spread vigente al generar", "=$P$6", PRECIO)]:
    ws.merge_cells("I%d:K%d" % (r, r))
    ws["I%d" % r].value = etiqueta
    ws["I%d" % r].font = Font(size=10, color=TENUE)
    ws["I%d" % r].alignment = Alignment(horizontal="right", vertical="center")
    salida("L%d" % r, formula, fmt, size=11)

# --- aviso general
ws.merge_cells("C7:M7")
ws["C7"].value = (
    '=IF($F$4="","⚠ Seleccione un instrumento de la lista.",'
    'IF(SUMPRODUCT(($E$10:$E$15>0)*($F$10:$F$15=0))>0,'
    '"⚠ Hay una operación con capital comprometido y sin precio de entrada.",'
    'IF(SUMPRODUCT(($F$10:$F$15>0)*(ABS($F$10:$F$15/$P$7-1)>0.1))>0,'
    '"⚠ Un precio de entrada difiere en más de 10% del precio de referencia ($"'
    '&FIXED($P$7,$P$2)&"). Verifique que corresponda al instrumento seleccionado.",'
    'IF(SUMPRODUCT(($E$10:$E$15>0)*($I$10:$I$15=0))>0,'
    '"⚠ Hay una operación bajo el volumen mínimo de 0,01 lotes, que requiere $"'
    '&FIXED(0.01*$P$7*$P$4*$P$5,0)&".",'
    'IF($L$19>$F$5,"⚠ El margen requerido excede el capital de la cuenta.",'
    '"✓ "&COUNTIF($I$10:$I$15,">0")&" operación(es) sobre "&$P$1'
    '&". El volumen indicado es el que se ingresa en MT5.")))))'
)
for cc in "CDEFGHIJKLM":
    ws["%s7" % cc].fill = PatternFill("solid", fgColor=CREMA)
    ws["%s7" % cc].border = borde
ws["C7"].font = Font(bold=True, size=11)
ws["C7"].alignment = Alignment(horizontal="center", vertical="center")
ws.row_dimensions[7].height = 30

# --- tabla de operaciones
banda("C8:M8", "OPERACIONES DEL PERIODO   ·   cada fila es una operación independiente, con su fecha, dirección y capital", NAVY, BLANCO, 12, 24)
cabeceras = ["FECHA", "DIRECCIÓN", "CAPITAL COMPROMETIDO", "PRECIO DE ENTRADA",
             "PRECIO DE SALIDA", "DÍAS DE MANTENCIÓN", "VOLUMEN (LOTES)",
             "COSTO DE APERTURA", "COSTO DE MANTENCIÓN", "RESULTADO NETO", "OBSERVACIÓN"]
for i, txt in enumerate(cabeceras):
    c = ws.cell(row=9, column=3 + i, value=txt)
    estilar(c, size=9, negrita=True, color=BLANCO, fondo=ACENTO, wrap=True)
ws.row_dimensions[9].height = 34

# ejemplo: tres operaciones del periodo, una de ellas perdedora
d = filas[0]["digits"]
base = round(filas[0]["precio"], d)
ejemplo = [
    (AHORA.date() - timedelta(days=4), "COMPRA", 500000, base - 3, base + 2, 2),
    (AHORA.date() - timedelta(days=2), "VENTA", 400000, base + 4, base + 1, 1),
    (AHORA.date() - timedelta(days=1), "COMPRA", 300000, base, base - 1.5, 0),
]
for i, r in enumerate(OPS):
    if i < len(ejemplo):
        fecha, direccion, pone, ent, sal, dias = ejemplo[i]
        entrada("C%d" % r, fecha, FECHA)
        entrada("D%d" % r, direccion, "General")
        entrada("E%d" % r, pone, CLP)
        entrada("F%d" % r, round(ent, d), PRECIO)
        entrada("G%d" % r, round(sal, d), PRECIO)
        entrada("H%d" % r, dias, ENTERO)
    else:
        entrada("C%d" % r, None, FECHA)
        entrada("D%d" % r, None, "General")
        entrada("E%d" % r, None, CLP)
        entrada("F%d" % r, None, PRECIO)
        entrada("G%d" % r, None, PRECIO)
        entrada("H%d" % r, None, ENTERO)

    # los lotes salen del monto: es la traduccion que el ejecutivo no tiene que hacer
    salida("I%d" % r, "=IFERROR(MAX(0,ROUNDDOWN($E{r}/($F{r}*$P$4*$P$5),2)),0)".format(r=r), LOTES)
    salida("J%d" % r, '=IF($I{r}=0,"",$I{r}*$P$6*$P$4)'.format(r=r), CLP)
    # costo de mantencion. Los dias efectivos suman 2 por semana completa porque el
    # broker cobra swap triple un dia a la semana (miercoles o viernes segun el activo).
    salida("K%d" % r, (
        '=IF(OR($I{r}=0,$H{r}=0),"",ABS(IF($D{r}="VENTA",$P$10,$P$9)'
        '*IF($P$8={pts},$I{r}*POWER(10,-$P$2)*$P$4,$I{r}*$F{r}*$P$4/100/360))'
        '*($H{r}+2*ROUNDDOWN($H{r}/7,0)))'
    ).format(r=r, pts=MODO_PUNTOS), CLP)
    salida("L%d" % r, (
        '=IF($I{r}=0,"",IF($D{r}="COMPRA",$G{r}-$F{r},$F{r}-$G{r})*$I{r}*$P$4'
        "-N($J{r})-N($K{r}))"
    ).format(r=r), CLP)
    a = salida("M%d" % r, (
        '=IF(OR($I{r}=0,$G{r}=""),"",IF(AND($D{r}="COMPRA",$G{r}<$F{r}),'
        '"precio de salida inferior a la entrada: resultado negativo en una compra",'
        'IF(AND($D{r}="VENTA",$G{r}>$F{r}),"precio de salida superior a la entrada: resultado negativo en una venta","")))'
    ).format(r=r), "General", size=9, negrita=False)
    a.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws.row_dimensions[r].height = 24

# --- totales
ws.merge_cells("C%d:D%d" % (TOT, TOT))
ws["C%d" % TOT].value = "TOTALES"
for cc in "CD":
    c = ws["%s%d" % (cc, TOT)]
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.font = Font(bold=True, size=11, color=BLANCO)
    c.alignment = Alignment(horizontal="center", vertical="center")
    c.border = borde
for col in "EFGHI":
    salida("%s%d" % (col, TOT), "=SUM(%s10:%s15)" % (col, col),
           CLP if col == "E" else (LOTES if col == "I" else "General"))
for col in "FGH":
    ws["%s%d" % (col, TOT)].value = None
    ws["%s%d" % (col, TOT)].fill = PatternFill("solid", fgColor=NAVY)
for col in "JKL":
    salida("%s%d" % (col, TOT), "=SUM(%s10:%s15)" % (col, col), CLP)
salida("M%d" % TOT, None, "General")
for col in "EIJKL":
    ws["%s%d" % (col, TOT)].fill = PatternFill("solid", fgColor=NAVY)
    ws["%s%d" % (col, TOT)].font = Font(bold=True, size=11, color=BLANCO)
ws["M%d" % TOT].fill = PatternFill("solid", fgColor=NAVY)
ws.row_dimensions[TOT].height = 24

# --- cierre del periodo
cierre = [
    (18, "Exposición nocional total", "=SUMPRODUCT($I$10:$I$15,$F$10:$F$15)*$P$4"),
    # sobre los lotes YA redondeados, no sobre lo que se pretendia poner: al bajar
    # 0,5437 a 0,54 lotes el margen real queda por debajo del monto ingresado.
    (19, "Margen requerido (posiciones simultáneas)", "=$L$18*$P$5"),
    (20, "Resultado neto del periodo", "=$L$16"),
    (21, "Patrimonio final", "=$F$5+$L$16"),
]
for r, etiqueta, formula in cierre:
    ws.merge_cells("I%d:K%d" % (r, r))
    ws["I%d" % r].value = etiqueta
    ws["I%d" % r].font = Font(bold=(r == 21), size=11)
    ws["I%d" % r].alignment = Alignment(horizontal="right", vertical="center")
    c = salida("L%d" % r, formula, CLP, size=13 if r == 21 else 11)
    if r == 21:
        c.fill = PatternFill("solid", fgColor=CREMA)
    ws.row_dimensions[r].height = 22

# --- rojo cuando pierde, y en los avisos
ws.conditional_formatting.add("L10:L%d" % TOT,
                              FormulaRule(formula=['AND($L10<>"",$L10<0)'],
                                          font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("M10:M15",
                              FormulaRule(formula=['$M10<>""'], font=Font(bold=True, color=ROJO)))
ws.conditional_formatting.add("L21", FormulaRule(formula=["$L$21<$F$5"],
                                                 font=Font(bold=True, color=ROJO)))

# --- pie
banda("C23:M23",
      "Especificaciones del broker al %s hora Chile. Celdas crema: campos editables; "
      "el resto son fórmulas. El COSTO DE MANTENCIÓN (swap) es una estimación: agrega "
      "2 días por semana completa, porque el broker aplica cargo triple un día a la "
      "semana. Este simulador no incorpora stop loss." % SELLO,
      BLANCO, "808080", 9, 30, italica=True)
ws["C23"].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

# --- listas desplegables (formula1 sin "=": con el igual Excel descarta la validación)
dv_act = DataValidation(type="list", formula1="Datos!$A$2:$A$%d" % ultima, allow_blank=False,
                        showErrorMessage=True, errorTitle="Instrumento no válido",
                        error="Seleccione un instrumento de la lista.")
ws.add_data_validation(dv_act)
dv_act.add(ws["F4"])

dv_dir = DataValidation(type="list", formula1='"COMPRA,VENTA"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Dirección no válida",
                        error="Seleccione COMPRA o VENTA.")
ws.add_data_validation(dv_dir)
for r in OPS:
    dv_dir.add(ws["D%d" % r])

dv_dias = DataValidation(type="whole", operator="between", formula1="0", formula2="3650",
                         allow_blank=True, showErrorMessage=True,
                         errorTitle="Días no válidos",
                         error="Indique los días completos de mantención de la posición (0 si se abre y cierra en la misma jornada).")
ws.add_data_validation(dv_dias)
for r in OPS:
    dv_dias.add(ws["H%d" % r])

# --- proteger todo menos las celdas crema
ws.protection.sheet = True
ws.protection.formatCells = False
ws.print_area = "B1:N24"
ws.page_setup.orientation = "landscape"
ws.page_setup.fitToPage = True
ws.sheet_properties.pageSetUpPr.fitToPage = True

DESTINO.parent.mkdir(parents=True, exist_ok=True)
wb.save(DESTINO)
print("generado:", DESTINO)
print("ejemplo:", filas[0]["nombre"], "con 3 operaciones alrededor de", base)
