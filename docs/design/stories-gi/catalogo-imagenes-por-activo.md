# Catálogo de imágenes por activo: lo que falta

Fecha: 2026-10-25. Pedido del director: cada par de divisas, acción, materia prima e índice con su
imagen característica, porque el propósito de las imágenes es dar vida a la pieza y una misma foto
repetida en todo lo anula.

La fuente es el campo `imagen` de `config/activos.json`, que apunta a
`templates/stories/assets/activos/<slug>.jpg`. La usan las Stories y, desde el 2026-10-25, el lienzo
del webinar (`scripts/webinar/rendir.py`, `imagen_de_activo`). El estándar de formato y montaje está
en `templates/stories/assets/activos/README.md` (1800×924, JPG calidad 88).

Prohibiciones de siempre (`config/motivos_imagen.json`): sin logos, sin marcas, sin texto ni números
legibles, sin banderas, sin personas reconocibles.

## Ya tienen imagen propia (22)

Oro, plata, WTI, cobre, USD/CLP, USD/JPY, EUR/USD, GBP/USD, US100, US500, US30, Russell (IWM),
MercadoLibre, semiconductores (SOXX), Bitcoin, Ethereum, Solana, Litecoin, Cardano y Dogecoin. Los ETF
comparten la de su índice (GLD con el oro, QQQ con el US100, SPY con el US500), y eso es correcto.

## Sin imagen o con una genérica compartida (17)

| Activo | Hoy | Motivo propuesto |
|---|---|---|
| Brent (`BRENT.spot`) | ninguna | Plataforma petrolera en mar abierto al atardecer |
| DAX (`GER40.spot`) | ninguna | Línea de ensamblaje automotriz con brazos robóticos |
| Dollar Index (`USDIDX`) | ninguna | Balanza de precisión con monedas, tonos verde y acero |
| Apple (`#AAPL`) | circuito genérico | Dispositivo de aluminio minimalista sobre mesa clara, sin marca |
| Microsoft (`#MSFT`) | circuito genérico | Pasillo de centro de datos con luz azul |
| Nvidia (`#NVDA`) | circuito genérico | Tarjeta gráfica en macro con luz verde |
| Amazon (`#AMZN`) | circuito genérico | Centro logístico con cintas y cajas, sin marca |
| AMD (`#AMD`) | circuito genérico | Oblea de silicio con reflejos rojos |
| JPMorgan (`#JPM`) | columnata US30 | Lobby bancario de mármol y bronce |
| Bank of America (`#BAC`) | columnata US30 | Sucursal bancaria moderna de vidrio, de noche |
| Goldman Sachs (`#GS`) | columnata US30 | Sala de operaciones con pantallas desenfocadas, sin cifras |
| Morgan Stanley (`#MS`) | columnata US30 | Rascacielos de vidrio de Midtown de noche |
| Boeing (`#BA`) | columnata US30 | Avión comercial en hangar, sin librea |
| Caterpillar (`#CAT`) | columnata US30 | Maquinaria pesada amarilla en faena minera, sin logos |
| GE (`#GE`) | columnata US30 | Turbina de motor de avión en fábrica |
| Deere (`#DE`) | columnata US30 | Tractor verde en campo de cultivo al amanecer, sin logo |
| Pares FX fuera de los 4 base | ninguna | Uno por par cuando entren al catálogo: arquitectura del banco central de cada moneda, sin banderas |

## Cómo se completa

1. El director aprueba los motivos de la tabla (o los cambia).
2. Se generan en tandas chicas con el mismo flujo de las existentes y se revisan a ojo una por una:
   nada de texto, logos ni marcas visibles.
3. Al guardar cada `<slug>.jpg`, se llena su campo `imagen` en `config/activos.json`. Ese campo es el
   interruptor: sin el archivo en disco no se llena.
