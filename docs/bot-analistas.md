# Bot de Telegram para analistas y ejecutivos

El equipo le pide al bot las mismas piezas que el director le pide a Claude Code, y recibe un
**informe HTML** listo para entregar a su trader. Diseño completo:
`docs/superpowers/specs/2026-10-08-bot-telegram-analistas-design.md`.

## Qué se puede pedir

| Comando | Pieza |
|---|---|
| `/activo oro` | Niveles, dirección, drivers, escenarios y el gráfico TradingView del carrusel |
| `/calendario hoy` · `/calendario semana` | Agenda de alto impacto en hora de Chile, con la lámina de Avisos |
| `/dato` · `/dato ipc` | El último dato con cifra (o el pedido): veredicto y movimiento del dólar y el oro. Si todavía no sale, en modo anticipación |
| `/jornada apertura` · `/jornada cierre` | Los cinco activos base con sus gráficos diarios y la curva de tasas |

Cualquiera acepta `para Nombre Apellido`, y entonces llegan dos archivos: la versión con el nombre
del trader y la genérica. La genérica trae una barra para escribir otro nombre y guardar esa
versión desde el navegador, sin volver a pedirla.

`/estado` muestra el cupo del día, `/id` el número de usuario y `/ayuda` la lista.

## Cómo funciona

```
pedido → orden.py (gramática cerrada) → preparar.py (datos + gráficos, carpeta propia)
       → agy /analista (solo redacta pieza.json) → esquema.py (valida) → láminas
       → informe_html.py (maqueta fija) → Telegram + carpeta de Drive
```

- **agy solo redacta.** No recibe nada de lo que el analista escribió: recibe la ruta de la
  pieza. Datos, imágenes y láminas van sellados con una huella, y si cambian la pieza se descarta.
- **Toda cifra del texto tiene que estar en los datos del terminal** (Regla 1). El texto tampoco
  puede traer HTML, guion largo ni voseo.
- **La maqueta es nuestra**: cabecera y lema del evergreen GI, cuerpo con la legibilidad de la
  guía USD/CLP, colores de `marca.css` (sección "Documento claro").
- **Personalizar no cuesta agy.** La pieza se reusa mientras está vigente (`reuso_minutos`; un
  dato ya publicado vale todo el día) y la versión para otro trader solo rearma el HTML.
- **No toca la producción.** Trabaja en `data/informes_analistas/` y no usa los `preparar()` de
  los pipelines, que escriben en `data/carrusel/`, `data/screener/` y los historiales. Un test
  impide que el bot importe el envío a WhatsApp o la bitácora de despachos.

## Puesta en marcha

1. Crear el bot con @BotFather y poner `TELEGRAM_BOT_TOKEN=...` en `.env`.
2. `uv run python scripts/bot_analistas.py --probar-token`
3. Copiar `config/analistas_telegram.example.json` a `config/analistas_telegram.json`
   (gitignoreado) y agregar a cada persona por su número de usuario. Quien no está, recibe su
   número al escribirle al bot y se lo pasa al director.
4. `ruta_drive`: la raíz de Google Drive para escritorio (por ejemplo `G:\Mi unidad`). El bot
   crea `GI Informes/<fecha>/` adentro. `url_carpeta_drive` es opcional y va en la respuesta.
5. Probar sin Telegram, con MT5 abierto:
   `uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --una "/activo oro para Juan Pérez"`
6. Dejarlo corriendo: `scripts\instalar_bot_telegram.ps1 -Instalar` (sin `-Instalar` solo muestra
   qué haría).

## Cuando algo falla

El analista recibe el motivo, y nunca una pieza a medias ni un gráfico de otro día.

| Mensaje | Qué pasó |
|---|---|
| `no uso el terminal: ...` | MT5 cerrado o en otra cuenta que la de `config/cuenta_mt5.json` |
| `La redacción no terminó (timeout ...)` | agy no respondió en 12 minutos. No gasta cupo |
| `El texto no pasó los controles` | agy escribió una cifra ajena, HTML o guion largo. No se entrega |
| `Drive no está configurado` | Falta `ruta_drive`; el archivo igual llega por Telegram |

La bitácora está en `data/logs/bot_telegram.log` y el estado (offset, cupo y piezas vigentes) en
`data/.bot_telegram_estado.json`.
