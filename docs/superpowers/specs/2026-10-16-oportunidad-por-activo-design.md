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
`{ticker, dir, creada, vence, creado_por, reusos: [], seguimientos: []}`. `vence = creada + 7 d`.
Una entrada con `vence` pasado no se reusa. Las entradas antiguas de seis activos quedan como
legado de solo lectura (no se migran). Un registro corrupto sigue levantando `RegistroDanado`.

## 6. Datos sellados que entran a agy

`preparar_oportunidad` arma solo el activo pedido: lectura, escenario, simulación, gráfico,
`drivers.<ticker>`, `agenda_semana`, `curva` y un bloque `fundamental` armado por Python con lo que
ya mide el sistema. Lo que el terminal no mide no se afirma como hecho.

## 7. Noticias y fuentes (agy busca y cita)

Para esta pieza agy puede usar la web. Escribe `editorial.fuentes[]`; cada entrada trae
`entidad`, `fecha`, `url` y `tesis` (una frase). Python valida (`esquema.py`):

- URL y fecha obligatorias. Ventana de frescura: **14 días**.
- La entidad debe estar en `config/fuentes_prestigio.json`: lista cerrada y versionada (grandes
  bancos de inversión, Fed, BCE, BCCh, EIA, OPEP, y medios financieros de referencia). Una entidad
  fuera de la lista no pasa. El director la edita.
- Regla 1 se mantiene: toda cifra del texto debe estar en `datos`. **Única excepción:** una cifra
  que aparezca en la `tesis` de una fuente y atribuida a ella en la misma frase («JPMorgan ve el
  oro en 4.800 dólares»). Una cifra de tercero sin atribución se rechaza.
- Sin ninguna fuente válida, la pieza sale con el análisis propio y avisa «sin voces de bancos o
  prensa atingentes esta vez». No se rellena ni se inventa.
- Los candados actuales siguen: sin guion largo, sin voseo, sin HTML, sin instrucción personal,
  sin `%`, y el cierre que invita a operar el escenario.

## 8. Salida

`oportunidad_html` con un activo: lámina PNG, panel de simulación y tres secciones nuevas:
*Fundamental*, *Lectura técnica* y *Voces de bancos y prensa* (con enlace a cada fuente). La
discrepancia con los bancos se muestra con su propia marca, no escondida. `/analista` suma las
reglas de web, `fuentes` y discrepancia.

## 9. Fallas

Igual que hoy: el analista recibe el motivo y nunca una pieza a medias; una redacción que no
termina no gasta cupo. El timeout de agy sube de 12 a 20 minutos por la búsqueda (a confirmar con
una medición real). Una falla de la web no impide la pieza: degrada al punto «sin voces».

## 10. Pruebas

Contratos que fallan si se rompen: la vigencia de 7 días (día 6 reusa, día 8 rehace), el reúso sin
cupo, el nombre de quien creó y de quien reutiliza, `/seguimiento` sin análisis vigente, un activo
fuera del catálogo, una fuente sin URL o con entidad no listada, una cifra de tercero sin
atribución, y que el bot siga sin importar el envío a WhatsApp.

## 11. Pendiente de confirmar al planificar

1. Contenido exacto de `config/fuentes_prestigio.json` (propongo una lista inicial y el director la
   ajusta).
2. Cómo se obtiene un nombre legible para símbolos fuera del catálogo.
3. Medición real del tiempo de agy con web, para fijar el timeout.
