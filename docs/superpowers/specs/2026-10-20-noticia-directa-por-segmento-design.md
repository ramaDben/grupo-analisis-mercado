# Noticia directa por segmento en `/oportunidad`

Fecha: 2026-10-20. Estado: borrador para aprobación del director. Nada de esto está construido.

## Intención y por qué

La pieza `/oportunidad <activo>` del bot de analistas (`scripts/analista/`) cita voces externas junto
al activo. Hoy esas voces no tienen relación directa con el activo. El caso que lo destapó: en USD/CHF
nunca aparece el Banco Nacional Suizo (SNB) ni nada de Suiza; la pieza repite tasas y DXY.

Causas medidas en el código (verificadas el 2026-10-20):

1. **Cuota de "voz de banco" ciega al activo.** `fuentes.falta_banco` (`fuentes.py:192-208`) exige una
   fuente de los grupos `cuentan_como_banco` (`config/fuentes_prestigio.json`: bancos de inversión y
   Chile). No pregunta si esa voz habla del activo.
2. **Lista cerrada sin anclas.** `fuentes_prestigio.json` no trae el SNB ni medios suizos, y tampoco
   emisores de ETF. Una nota que la web sí encuentre se descarta en `depurar`.
3. **Drivers genéricos.** Un activo sin ficha en `config/drivers.json` cae en
   `GENERALES = ("dxy", "bono_10")` (`hechos.py:33`, `:57`), y el esquema obliga a que el texto cite
   esas cifras. USD/CHF no está en `CLAVE_DRIVERS` (`hechos.py:29`).
4. **Agenda limitada.** `agenda.PAISES` cubre EE.UU., Chile, China y Zona Euro.

## Meta, no metas y antimetas

**Meta.** Cada oportunidad lleva al menos una fuente directa del activo, o no se publica.

**No metas.**
- No se cambia la lectura técnica ni la dirección de la pieza (sigue saliendo de la estrategia activa).
- No se amplía el calendario económico a países que hoy no cubre (ver "Fuera de alcance").
- No se toca la rotación diaria, el carrusel ni los canales de WhatsApp.

**Antimetas (fracaso aunque funcione).**
- Rellenar con una noticia genérica para que la pieza salga.
- Que una voz de banco o un macro de EE.UU. cuente como "directa" para un activo que no es suyo.
- Escribir a mano una cifra, una fecha o un precio (Regla 1 de CLAUDE.md).

## Decisiones del director (2026-10-20)

1. Sin noticia directa del activo, la oportunidad **no se publica**. Se avisa el motivo en el bot, sin
   relleno y sin gastar cupo.
2. Se separa por **seis segmentos**, cada uno con su universo de fuentes ya armado: `fx`,
   `commodities`, `acciones`, `etfs`, `indices` y `cripto`. Los seis se construyen en el mismo
   proyecto. Ningún activo conserva la regla genérica: todos deben tener una voz que lo represente.
3. En acciones, la fecha de earnings sale de **yfinance**, con aviso de que no es fuente oficial.
4. En ETF, el emisor (BlackRock, Invesco, State Street y similares) es la entidad directa.

## Decididas por el director (2026-10-20)

El director respondió "sigo tu recomendación para ambas":

- **P1. La fecha de earnings de yfinance NO habilita sola la publicación de una acción.**
  La acción sale con un comunicado o resultado ya publicado (IR o SEC EDGAR); la fecha de
  yfinance es dato de contexto con su aviso de "no oficial".
- **P2. La voz de banco YA NO es requisito.** Basta la directa; el banco suma al correo si
  existe y respalda la lectura.

## Qué cuenta como "directa" por segmento

| Segmento | Ancla | Cuenta como directa | No cuenta |
|---|---|---|---|
| `fx` | La pata que **no** es dólar: su banco central, su gobierno o un medio de ese país | Política monetaria o macro local, publicada por el banco central, el ministerio o un medio local calificado | Fed, DXY, tasas de EE.UU. |
| `commodities` | El mercado del activo (oro, plata, petróleo, cobre) | OPEP/OPEP+, EIA, IEA, API; WGC, LBMA, compras de bancos centrales; Cochilco, Codelco, LME, ICSG | Tasas y DXY solos |
| `acciones` | La empresa | Resultados trimestrales ya publicados, guidance, recompras, comunicados y presentaciones de relaciones con inversionistas (IR), notas de wire que citen el anuncio. La fecha de earnings es contexto, no habilita (ver P1) | Opinión de analistas, macro genérico |
| `etfs` | El emisor del fondo | Publicación **fechada y con URL** del emisor: comunicado o comentario del gestor sobre el fondo, su índice o su subyacente | Macro genérico; titular genérico del subyacente que no sea del emisor |
| `indices` | El proveedor del índice y su bolsa | Comunicados de rebalanceo o metodología del proveedor o la bolsa; notas de medios de la lista cerrada cuyo titular o resumen nombre el índice y trate niveles, valuación o tendencia | Fed, BCE, IPC, NFP o DXY genéricos; titulares tipo "Wall Street cae" que no nombren el índice; earnings de un constituyente que no nombre el índice |
| `cripto` | Fundación o proyecto de la red; si no tiene entidad central, emisores de ETF spot, bolsas institucionales, reguladores y datos on-chain | Publicación fechada con URL de esas entidades cuyo titular o tesis nombre la cripto | Portales cripto no autorizados, redes sociales, rumor, macro genérico |

**ETF, llamado mío (recomendación que el director aceptó el 2026-10-20 sin que yo la hubiera
escrito antes; confirmar al leer este documento).** Los flujos netos y los holdings leídos de la
página del fondo **no habilitan por sí solos**: entran al análisis como dato, con la fecha en que se
leyeron. Habilita únicamente una publicación fechada con enlace. Razón: una cifra de página no tiene
fecha ni URL verificables, y la lista cerrada existe para poder comprobar cada cita.

## Contrato común (las piezas que comparten los cuatro segmentos)

1. **`config/segmentos_fuentes.json` (nuevo).** Una clave por segmento; dentro, entidades por ancla y
   medios con dominios, mismo formato que `fuentes_prestigio.json`. Lo edita el director. La lista
   cerrada actual se conserva para los medios y las entidades ya validadas; se decide en el plan si
   `segmentos_fuentes.json` la reemplaza o la extiende (llamado mío: extenderla, para no romper el
   formato que ya validan los tests).
2. **`segmento` y `ancla` en cada activo de `config/activos.json`.** El ancla es un objeto. Campos
   comunes: `nombre`, `entidades`, `dominios`. Por segmento se suman: `pais` y `banco_central` (fx);
   `mercado` (commodities); `ticker`, `sitio_ir` (acciones); `emisor`, `indice`, `subyacente` (etfs);
   `proveedor`, `bolsa`, `terminos_ancla` (indices); `red`, `fundacion` (cripto).
   Los términos con los que el titular debe nombrar el ancla (nombre, ticker, "NDX", "S&P 500") viven
   en el ancla, para que la verificación de contenido no dependa de texto escrito en el código.
   Para un activo fuera de catálogo (USD/CHF hoy), `preparar._catalogo_o_terminal` (`preparar.py:97-108`)
   debe inferir segmento y ancla; si no puede, la oportunidad no se publica y lo dice.
3. **Una sola regla.** `falta_banco` pasa a `falta_fuente_directa(pieza, segmento, ancla)` y `bancos` a
   `fuentes_directas(fuentes, segmento, ancla)`. Mismo mecanismo de dos intentos que `_con_banco`
   (`bot.py:319-337`).
4. **Un solo aviso.** `SIN_BANCO` (`bot.py:218`) pasa a `SIN_NOTICIA_DIRECTA`, parametrizado por el
   ancla. Conserva la frase "No gasté tu cupo" (el cupo existe: `bot.py:269`).
5. **Lo que hoy cuenta como banco no se pierde.** Una voz de banco de inversión sigue sumando al
   correo (`seleccionar_bancos_correo`), pero ya no habilita por sí sola la publicación.
6. **Herencia partida.** Drivers y agenda se heredan del subyacente (GLD con la mecánica del oro, QQQ
   y SPY con la de los índices). Las **fuentes** tienen ancla propia estricta, porque si GLD heredara
   las del oro, un titular genérico del metal contaría como directa y volvería el problema.

## Por segmento: lo propio

**FX.** Mapa divisa a banco central, ministerio y medios locales: CHF/SNB (snb.ch, admin.ch; NZZ, Le
Temps, Handelszeitung), JPY/BoJ (boj.or.jp, mof.go.jp), GBP/BoE, EUR/BCE, CLP/BCCh. AUD, CAD, NZD y MXN
quedan **fuera del primer corte** hasta verificar sus dominios (eran suposición de agy). Fichas de
drivers nuevas para USD/CHF y los demás pares incluidos; `agenda.PAISES` suma Suiza, Japón y Reino
Unido.

**Commodities.** Oro, plata, WTI, Brent y cobre. Ya hay ficha en `drivers.json` para oro y WTI; faltan
Brent, cobre y plata. OPEP, WGC, EIA y Cochilco pasan de `organismos` a fuentes que habilitan para su
propio mercado (hoy solo suman). Los inventarios EIA y sus horas se calculan con `hora_chile.ps1`,
nunca a mano.

**Acciones.** Las 14 de `activos.json` (prefijo `#`). Requiere una **ingesta nueva** en
`data central/DATA ACCIONES/` con `earnings_calendar.json` y `estados_financieros.json`: hoy no existe
nada de eso (solo hay menciones sueltas a "earnings" en el screener y en el contexto macro). Fecha de
earnings por yfinance, con la leyenda de que no es oficial; informes presentados por SEC EDGAR
(`data.sec.gov`, por `cik`) como respaldo de resultados. Las fechas futuras se redactan en modo
anticipación. Cifras de resultados siempre leídas de la ingesta, nunca escritas.

**ETFs.** QQQ.US (Invesco), SPY.US (State Street), GLD.US (World Gold Trust y WGC, con State Street),
IWM.US y SOXX.US (BlackRock/iShares). Dominios a verificar antes de cerrar la lista: `spdrs.com` y
`spdrgoldshares.com` (suposición de agy). Medios del sector: etf.com, etfdb.com, Morningstar.

**Índices.** US100.spot, US500.spot, US30.spot y GER40.spot. Hoy solo US100 tiene ficha en
`drivers.json`; faltan US500, US30 y GER40, con los nombres de driver del esquema real (no los que
propuso agy). Voz: Nasdaq (US100), S&P Dow Jones Indices y NYSE (US500, US30), Deutsche Börse, STOXX
y Xetra (GER40). Los dominios de GER40, `cboe.com`, `dowjones.com` e `indexes.nasdaqomx.com` son
suposición de agy y se verifican antes de cerrar la lista. GER40 requiere sumar Alemania a
`agenda.PAISES` y la bolsa Xetra a `config/feriados_bolsa.json`. Un precio objetivo de un banco sobre
el índice suma al correo, pero no habilita sola.

**Cripto.** BTCUSD, ETHUSD, SOLUSD, LTCUSD, ADAUSD y DOGUSD. Viven en `forex_commodities` con
`categoria: crypto` (no hay una sección propia; hay que confirmarlo abriendo el archivo). Las
fundaciones de Ethereum, Solana, Cardano (con IOG), Litecoin y Dogecoin son la voz de su red; BTC,
LTC y DOGE, sin entidad central, se anclan en emisores de ETF spot (iShares/BlackRock, Fidelity,
Grayscale), bolsas (Coinbase, Kraken, Binance), reguladores (SEC, CFTC) y datos on-chain (Glassnode).
Mercado 24/7: sin catalizador fechado la agenda sale vacía y no inventa correlaciones macro. Un
comunicado de un emisor de ETF sobre su propio producto es marketing; se decide en el plan si cuenta
(llamado mío: cuenta solo si trae datos del fondo o del mercado, no si es promoción del producto).
Un blog de fundación cuenta solo como artículo fechado con URL propia.

## Restricciones

- Regla 1: precios y cifras de MT5 o de la ingesta en tiempo de ejecución, nunca escritos.
- Texto de cliente sin guion largo ni medio; español chileno, sin voseo.
- Horas en hora Chile con `scripts\hora_chile.ps1`; eventos asiáticos con cruce de día.
- `.agents/workflows/analista.md` y `.claude/commands/analista.md` se **regeneran** con
  `scripts/agy_workflows.py`; no se editan a mano.
- Ramas de feature (`feat/...`) y PR; nunca commit directo a master.
- Los tests que fijan el comportamiento actual se actualizan, no se borran para pasar:
  `test_analista_fuentes.py` (`:149-215`), `test_analista_bot.py` (texto de `SIN_BANCO`),
  `test_analista_hechos.py` (`:98-100` usa COPPER como "activo sin ficha", que dejará de serlo),
  `test_analista_esquema.py` (no analizado todavía).

## Fuera de alcance del primer corte

- **Calendario económico de otros países.** `obtener_calendario_macro` solo cubre Chile, EE.UU., China
  y Zona Euro. Para Suiza, Reino Unido, Canadá, etc. la noticia directa viene de la búsqueda web
  validada, no de un calendario de datos. Ampliar el calendario es otro proyecto.
- Gas natural (no está en el catálogo, su ticker es suposición).
- AUD, CAD, NZD y MXN hasta verificar dominios.

## Riesgos

- Semanas sin pieza: ETF y acciones fuera de temporada de resultados pueden pasar días sin noticia
  directa. Es la consecuencia buscada de la decisión 1, pero conviene medirla.
- La fecha de earnings de yfinance puede cambiar o fallar; el aviso "no oficial" la acompaña.
- El modelo puede inventar notas para pasar el filtro; lo cubren `_del_dominio`, `verificar_url` y la
  lista cerrada.
- Ventana de frescura: hoy 14 días para bancos. Llamado mío: mantener 14 días en todos los segmentos
  para el primer corte y medir antes de variarla por segmento.

## Qué queda al constructor

El esquema JSON exacto de `segmentos_fuentes.json`, los nombres internos de las funciones nuevas, el
orden de implementación (propuesta: contrato y regla común, luego FX, commodities, acciones y ETF),
y la redacción final de los avisos del bot.

## Llamados míos (para que el director los revise)

1. Extender `fuentes_prestigio.json` en vez de reemplazarlo.
2. Frescura de 14 días en los seis segmentos. agy propuso 7 días para cripto; se mide antes de variar.
3. Dejar AUD, CAD, NZD, MXN y gas natural fuera del primer corte.
4. En ETF, los flujos de página complementan pero no habilitan.
5. Orden de construcción: común, FX, commodities, acciones, ETF, índices, cripto.
6. Una nota es directa si el dominio y la entidad están en la lista cerrada del segmento **y** el
   titular o resumen nombra el ancla (por sus `terminos_ancla`).
7. La consulta que se le pide al modelo se arma desde las entidades y dominios del ancla.
8. El contenido inicial de `segmentos_fuentes.json` lo propone el constructor y verifica cada dominio
   con `verificar_url`; los que no verifiquen quedan fuera. El director revisa la lista.
9. La ingesta de acciones se engancha a `pipeline_datos.py`, con el mismo umbral de frescura; si el
   archivo falta o está vencido, esa acción no publica y el bot lo dice. El `cik` va en el ancla.
10. USD/CLP tiene como ancla al Banco Central de Chile; un test garantiza que no pierde su cobertura.
11. Earnings de un constituyente no cuentan como directa de un índice salvo que el titular nombre el
    índice.
