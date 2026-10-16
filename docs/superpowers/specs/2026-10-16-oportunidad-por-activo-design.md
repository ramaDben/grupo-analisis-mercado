# `/oportunidad <activo>`: análisis profundo por activo, con vigencia de 7 días

Fecha: 2026-10-16. Reemplaza el `/oportunidad` semanal de seis activos
(`2026-10-12-oportunidad-semanal-design.md`). Los demás comandos del bot no cambian.

## 1. Qué se pide

El ejecutivo escribe `/oportunidad` seguido de cualquier activo del terminal MT5. El bot le
entrega un análisis de **ese** activo que junta:

- **Lo técnico de nuestros sistemas:** la lectura de la estrategia activa (dirección, estado,
  líneas, lo que se vigila, lo que invalida, objetivo, escenarios), niveles y gráfico.
- **Lo fundamental:** drivers del activo, curva de tasas, agenda macro de la semana.
- **Voces de bancos y fuentes de prestigio** atingentes al activo, citadas con entidad, fecha y
  enlace.

Lo redacta agy. **Nuestra lectura manda**: si los bancos discrepan, la pieza lo dice abiertamente.

## 2. Vigencia y reúso (decisión del director, 2026-10-16)

- Un análisis vale **7 días corridos desde que se creó** (no la semana ISO).
- Mientras esté vigente, **cualquiera** que pida ese activo recibe el mismo, sin gastar agy ni cupo.
  Pasados los 7 días, el siguiente pedido lo rehace.
- Al crearlo se guarda en **Drive** y queda **registrado a nombre de quien lo generó**
  (`creado_por`). Quien lo reutiliza lo recibe con su propio nombre en el archivo y el registro
  anota el reúso.
- **Caducidad anticipada (aprobada 2026-10-16).** Al reutilizar, Python corre `seguir(referencia)`
  y consulta `debe_reemplazar` (`referencia_semanal.py`). Si una línea se rompió por cierre, el
  precio tocó la invalidación o se alcanzó el objetivo, el análisis **caduca aunque no hayan pasado
  7 días** y se rehace. El anterior queda en el registro como historia, con su motivo. Si el
  terminal no responde en ese momento, se entrega el vigente con el aviso «no pude verificar si
  sigue vigente». Mandar una invalidación ya rota es peor que rehacer.
- `/seguimiento <activo>` mide contra el análisis vigente de ese activo. Sin análisis vigente
  responde: «pide primero /oportunidad <activo>». Conserva su contrato actual (mide contra lo que
  circuló) y sigue sin usar agy.

## 3. Pedido y universo

- `orden.py`: `/oportunidad` exige activo, con las mismas reglas que `/seguimiento` (alias,
  tickers, nombre del catálogo), sin saludo y sin «para …». Sin activo, responde con el uso.
  `clave_base` lleva el ticker.
- **Universo:** los símbolos del terminal. El catálogo (`config/activos.json`) aporta nombre,
  `digits` y `notas_marco`. Un símbolo del terminal que no está en el catálogo se acepta si
  `symbol_info` entrega `digits`, con nota de marco genérica y el aviso «activo fuera del catálogo».
  **Nombre legible:** el `description` de `symbol_info` tal como viene, con limpieza mínima
  (espacios y caracteres de control), sin traducir y sin pedírselo a agy: el nombre se necesita
  antes de llamarlo y no puede cambiar entre corridas.
  Un ticker que no existe en el terminal se rechaza con el motivo.

## 4. Referencia del análisis

La pieza se mide contra una referencia que queda guardada con ella:

1. Si el activo tiene referencia semanal vigente (`data/referencias_semanales/`), se usa esa:
   es la que ya circuló.
2. Si no, se lee de nuevo con `estrategia.leer(ticker, velas, digits, None)` (sin vela en curso,
   así nunca queda en PRUEBA) y esa lectura pasa a ser la referencia de la pieza. No se escribe en
   `referencias_semanales/`: el escáner es su dueño.

Se elimina la lógica de «fuera de la foto», `fuera_con_referencia` y la rehecha por aparición de
referencia: ya no hay seis activos que alinear.

## 5. Registro

`data/semanal/registro.json` pasa de una entrada por semana a una **por activo**:
`{ticker, dir, creada, vence, creado_por, reusos: [], seguimientos: [], caducada: null}`.
`vence = creada + 7 d`. Una entrada con `vence` pasado, o con `caducada` (fecha y motivo, ver
sección 2), no se reusa. Las entradas antiguas de seis activos quedan como
legado de solo lectura (no se migran). Un registro corrupto sigue levantando `RegistroDanado`.

## 6. Datos sellados que entran a agy

`preparar_oportunidad` arma solo el activo pedido: lectura, escenario, simulación, gráfico,
`drivers.<ticker>`, `agenda_semana`, `curva` y un bloque `fundamental` armado por Python con lo que
ya mide el sistema. Lo que el terminal no mide no se afirma como hecho.

## 7. Noticias y fuentes (agy busca y cita)

Para esta pieza agy puede usar la web. Escribe `editorial.fuentes[]`; cada entrada trae
`entidad` (quién opina), `medio` (dónde se publicó), `fecha`, `url`, `postura` (alcista, bajista o
neutral) y `tesis` (una frase). Se separan entidad y medio porque los bancos casi nunca publican su
research en su propio sitio: se lee en Reuters, CNBC o Kitco, y exigir el dominio del banco
rebotaría casi todo. Python valida (`esquema.py`):

- URL y fecha obligatorias. Ventana de frescura: **14 días**.
- La `entidad` debe estar en `config/fuentes_prestigio.json` y el dominio de la `url` debe
  corresponder al `medio`, que también está en la lista. Lista cerrada y versionada, que el
  director edita. Contenido inicial:
  - *Bancos de inversión:* Goldman Sachs, JPMorgan, Morgan Stanley, Bank of America, Citi, UBS,
    Barclays, Standard Chartered, Jefferies, Deutsche Bank, HSBC, ING, Commerzbank.
  - *Chile:* Banco Central de Chile, Cochilco, Banchile, BCI Estudios, Santander Chile, Itaú Chile.
  - *Organismos:* Fed, BCE, EIA, OPEP, FMI, BIS, World Gold Council, Agencia Internacional de Energía.
  - *Medios (solo como `medio`):* Reuters, Bloomberg, Financial Times, WSJ, CNBC, MarketWatch,
    Kitco, FXStreet, Diario Financiero, La Tercera. Investing.com queda fuera (403 a bots, y agy
    entregó solo la portada).
- La URL debe tener ruta de artículo (una portada se rechaza). Python hace un GET a cada URL: un
  404 o un error de dominio la descarta; un 403 de un medio con muro de pago se acepta y queda
  marcada «sin verificar». Cubre el riesgo de URLs inventadas.
- **La discrepancia la calcula Python**, no agy: compara la `postura` de cada fuente con la
  dirección de nuestra lectura y marca la discrepancia. Evita que el modelo se alinee con el
  titular que encontró en vez de con nuestra lectura.
- Regla 1 se mantiene: toda cifra del texto debe estar en `datos`. **Única excepción:** una cifra
  que aparezca en la `tesis` de una fuente y atribuida a ella en la misma frase («JPMorgan ve el
  oro en 4.800 dólares»). Una cifra de tercero sin atribución se rechaza.
- Sin ninguna fuente válida, la pieza sale con el análisis propio y avisa «sin voces de bancos o
  prensa atingentes esta vez». No se rellena ni se inventa.
- Los candados actuales siguen: sin guion largo, sin voseo, sin HTML, sin instrucción personal
  y sin `%`. **El cierre que invitaba a operar el escenario se retira** (ver sección 11): por
  regulación la pieza no invita a operar, invita a revisar la plataforma.

## 8. Salida

`oportunidad_html` con un activo: lámina PNG, panel de simulación **rotulado «ejemplo ilustrativo
para revisar en MT5»** (decisión del director, 2026-10-16: se mantiene, sin lectura de
recomendación) y tres secciones nuevas:
*Fundamental*, *Lectura técnica* y *Voces de bancos y prensa* (con enlace a cada fuente). La
discrepancia con los bancos se muestra con su propia marca, no escondida. `/analista` suma las
reglas de web, `fuentes` y discrepancia.

## 9. Fallas

Igual que hoy: el analista recibe el motivo y nunca una pieza a medias; una redacción que no
termina no gasta cupo. Una falla de la web no impide la pieza: degrada al punto «sin voces».

- **Timeout:** se mantiene en **12 min** (`agy.py`) como valor provisional. agy sugirió 3 a 5 min,
  pero su cifra (11,7 s) es de una sola búsqueda; la consulta completa de prueba tardó 192 s y en
  septiembre un encargo real tomó de 5 a 7 min. Se fija con una corrida completa real (3 a 5
  fuentes más validación), que es la primera tarea del plan.
- **Mensaje inmediato** al ejecutivo: «Armando el análisis de <activo>, tarda unos minutos».
- **Candado por activo:** un segundo pedido del mismo activo mientras se genera recibe «ya se está
  generando» y no lanza otro agy. Evita el reenvío del comando por impaciencia.

## 10. Pruebas

Contratos que fallan si se rompen: la vigencia de 7 días (día 6 reusa, día 8 rehace), el reúso sin
cupo, el nombre de quien creó y de quien reutiliza, `/seguimiento` sin análisis vigente, un activo
fuera del catálogo (con su nombre tomado de `description`), una fuente sin URL, con URL de portada,
con entidad o medio no listados, una cifra de tercero sin atribución, la discrepancia calculada por
Python desde la `postura`, la caducidad anticipada (invalidación rota antes del día 7 rehace, y con
el terminal caído se entrega con el aviso), el candado por activo, y que el bot siga sin importar el
envío a WhatsApp.

## 11. Cierre regulatorio: invitar a revisar la plataforma, no a operar (director, 2026-10-16)

Por temas de regulación, ninguna pieza de `/oportunidad` invita a operar. Su propósito comercial es
que el ejecutivo tenga un motivo para **sentarse con su cliente a revisar la plataforma MT5**:
mirar los gráficos juntos, revisar la lectura y las estrategias. Esto **reemplaza** la regla 10 de
`/analista` (invitar a operar el escenario, 2026-10-12).

- **Bloque fijo escrito por Python, no por agy.** Cierra la ficha HTML con «Para revisar con tu
  cliente en MT5»: ver el gráfico del activo con las líneas de la lectura, repasar los escenarios y
  conversar la estrategia. Es el mismo texto en toda pieza, incluidas las reutilizadas durante los 7
  días. agy no puede omitirlo ni reescribirlo.
- **Texto de acompañamiento del ejecutivo.** El mensaje que el bot entrega para que el ejecutivo lo
  reenvíe (con el saludo de `orden.saludo`) siempre termina invitando al cliente a revisar el activo
  en MT5 junto con su ejecutivo. Lo arma Python con una plantilla; agy no lo redacta.
- **Lo que agy tiene prohibido.** Cualquier invitación u orden de operar («opera», «compra»,
  «vende», «entra», «aprovecha para operar», «el escenario se puede operar»). El validador rechaza
  esas formas, y deja de exigir que `contexto` invite a operar. `contexto` cierra con la lectura:
  qué se vigila y qué la invalida.
- **Contratos de prueba:** la ficha sin el bloque de revisión en MT5 falla; un `contexto` con una
  invitación a operar falla; el texto de acompañamiento sin la invitación a revisar en MT5 falla.
- **Cambios en el código existente:** `esquema.py` (invierte el candado de «invita a operar»),
  `.claude/commands/analista.md` (regla 10 y `titular`/`bajada`, que hoy «empujan a la acción»),
  `oportunidad_html.py` (bloque fijo) y `bot.py` (texto de acompañamiento).
- **Panel de simulación (resuelto, 2026-10-16):** se mantiene y se rotula «ejemplo ilustrativo
  para revisar en MT5». Contrato de prueba: el panel sin ese rótulo falla.

## 12. Puntos abiertos: resueltos el 2026-10-16

1. Lista de `config/fuentes_prestigio.json`: sección 7 (entidad y medio separados).
2. Nombre de símbolos fuera del catálogo: sección 3 (`description` de MT5).
3. Timeout: sección 9 (12 min provisional, a fijar con una corrida completa real en el plan).

Lo único que queda para el plan es esa medición.
