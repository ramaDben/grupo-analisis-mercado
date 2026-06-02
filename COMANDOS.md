# Comandos diarios — Director de Trading

Estos son los comandos que pegas directamente en Claude Code (`claude`) desde la carpeta del proyecto. Claude Code lee automáticamente el CLAUDE.md y toda la configuración.

> **Interfaz principal: los slash commands.** El día a día se opera con `/lunes`, `/martes`, `/apertura`, `/señal`, etc. (ver tabla completa en `CLAUDE.md`). Los bloques de prompt de abajo son la alternativa manual/legacy y **no dependen** de ejecutar `python scripts/...`: los scripts quedan como utilidades opcionales que puedes correr a mano, nunca como paso obligatorio de la operativa.

---

## 🚀 Operativa completa del día (automática)

```
Ejecuta la operativa completa de hoy. Pasos:
1. Lee config/agenda_semanal.json y determina qué corresponde hoy (rotación de activos, encuesta del día)
2. Usa web search para obtener el calendario económico de hoy en Investing.com (filtrar Chile, EE.UU., Zona Euro, 3 estrellas)
3. Usa web search para obtener precios actuales de los activos del día
4. Genera niveles técnicos (soportes, resistencias, sesgo) en 4H y 1H
5. Identifica los drivers que mueven cada activo hoy
6. Selecciona la noticia más relevante del calendario y explícala simple
7. Genera la encuesta del día según la agenda
8. Formatea TODO para WhatsApp usando los templates de templates/
9. Muéstrame cada mensaje para que yo lo apruebe antes de enviarlo

Recuerda: lenguaje simple, el cliente debe entender en 30 segundos.
```

---

## 📅 Lunes — Resumen semanal

```
Es lunes. Genera todo el contenido del lunes:

1. RESUMEN SEMANAL: busca en Investing.com el calendario económico de toda esta semana. Lista los datos más importantes (IPC, PMI, PCE, NFP, decisiones de tasas) con día, hora Chile y posible impacto en nuestros activos. Marca los días de alta volatilidad con 🔴.

2. CONCEPTO DE LA SEMANA: elige un concepto educativo relevante para esta semana (puede ser un indicador como RSI, MACD, ATR, o un concepto macro como IPC, PMI, tasas de interés, Dollar Index). Explícalo en 3-4 líneas simples con un ejemplo real.

3. APERTURA DE MERCADO: niveles técnicos + noticia del día + drivers para los activos que correspondan hoy.

4. ENCUESTA DE TENDENCIA: genera la encuesta para uno de los activos del día.

Formatea todo con los templates de templates/ para WhatsApp. Muéstrame cada mensaje para aprobación.
```

---

## 📊 Martes a Jueves — Operativa diaria

```
Genera la operativa diaria:

1. Busca en Investing.com los datos económicos relevantes de hoy
2. Obtén precios actuales de los activos que toca cubrir hoy (ver rotación en config/agenda_semanal.json)
3. Genera niveles técnicos en 4H y 1H: soportes, resistencias, zona de interés, sesgo
4. Explica los drivers que mueven cada activo hoy (consulta config/drivers.json para la referencia)
5. Selecciona el dato económico más importante y explícalo simple
6. Genera la encuesta del día (tendencia si es miércoles/jueves, precio apertura si es martes)

Formatea para WhatsApp con los templates. Muéstrame para aprobación.
```

---

## 📊 Viernes — Cierre semanal

```
Es viernes. Genera TODO el contenido del viernes:

1. OPERATIVA NORMAL: niveles + noticia + drivers (como cualquier día)

2. CIERRE SEMANAL (para enviar por la tarde): genera un resumen de la semana con:
   - Qué pasó esta semana (resumen en 3-4 líneas)
   - Qué datos sorprendieron y por qué
   - Cómo reaccionaron los activos principales
   - Qué esperar para la próxima semana (eventos clave)

3. ENCUESTA DE PRECIO: "¿A qué precio abrirá el [activo] el lunes?" — ideal para cuando hay noticia importante fuera de horario.

Formatea todo para WhatsApp. Muéstrame para aprobación. El cierre semanal lo envío por la tarde.
```

---

## 🎯 Señal operativa

```
Analiza [ACTIVO] y evalúa si hay oportunidad para una señal operativa.

Antes de generar la señal:
1. Verifica en data/historial_senales.json cuántas señales van esta semana (máximo 3)
2. Si ya se enviaron 3, avísame y no generes señal

Si hay oportunidad clara, genera la señal con:
- Ticker y nombre del activo
- BUY o SELL
- Precio de entrada
- Take Profit con equivalente en CLP (usar tipo de cambio USD/CLP actual)
- Stop Loss con equivalente en CLP
- Volumen y acciones sugeridas
- 3 bullets máximo de análisis (técnico + fundamental)
- Temporalidad y tipo de operativa

Usa el template de templates/señal_operativa.txt. El cliente debe ver cuánto gana y cuánto pierde en pesos chilenos sin calcular nada.

Muéstrame para aprobación. Si la apruebo, registra en data/historial_senales.json.
```

> **Nota**: reemplaza `[ACTIVO]` por el ticker (ej: USD/CLP, Oro, WTI, US100, #CRM, etc.)

---

## 🏦 Evento de alto impacto — Decisión de tasas

```
Hay decisión de tasas de [FED/BCCH/BCE] el [FECHA].

Genera cobertura completa:

1. ANÁLISIS PREVIO (para enviar días antes):
   - Conecta los datos recientes (IPC, PCE, PMI, empleo) con el escenario de tasas
   - Ejemplo: "El PCE salió más bajo de lo esperado → confirma el escenario de recorte"
   - Explica qué espera el mercado (probabilidades de recorte/alza)
   - Indica cómo afectaría a nuestros activos cada escenario

2. DÍA DE LA DECISIÓN:
   - Análisis previo breve (recordatorio de lo que se espera)
   - Formato para monitoreo en vivo post-decisión
   - Template para explicar el resultado y su impacto

Formatea para WhatsApp. El objetivo es que el cliente entienda que los datos económicos son piezas que arman el camino hacia la decisión.
```

> **Nota**: reemplaza `[FED/BCCH/BCE]` y `[FECHA]`

---

## ⚠️ Alerta intradía

```
Acaba de pasar algo importante: [DESCRIBE EL EVENTO].

Genera una alerta rápida para el grupo con:
1. Qué pasó (en 1-2 líneas simples)
2. Por qué importa
3. Cómo podría afectar a nuestros activos
4. Usa el template de templates/alerta_intradia.txt

Esto es urgente — formatea y muéstrame rápido para enviarlo.
```

> **Nota**: reemplaza `[DESCRIBE EL EVENTO]` con lo que pasó

---

## 📚 Contenido educativo extra

```
Genera una "Pregunta del día" para el grupo.

Elige una pregunta interesante relacionada con lo que pasó esta semana en el mercado.
Ejemplo: "¿Por qué creen que el oro subió tras el dato de inflación de EE.UU.?"

La pregunta debe:
- Estar conectada con algo que ya cubrimos en el grupo
- Ser respondible con la información que hemos compartido
- Fomentar que el cliente piense y conecte conceptos

Genera la pregunta y prepara la respuesta correcta (la envío al día siguiente).
```

---

## 📋 Glosario del grupo

```
Genera un glosario completo para fijar como mensaje en el grupo de WhatsApp.

Incluir explicaciones simples de:
- Indicadores macro: IPC, PMI, PCE, NFP, PIB
- Conceptos de mercado: Dollar Index, spread de tasas, carry trade
- Indicadores técnicos: ATR, RSI, MACD, medias móviles, soportes, resistencias
- Drivers por activo: los principales de USD/CLP, Oro, WTI, US100
- Tipos de operativa: scalper, intradía, swing
- Temporalidades: 15M, 1H, 4H, 1D

Cada concepto en máximo 2 líneas. Formato WhatsApp limpio para mensaje fijado.
```

---

## 🔧 Utilidades

### Ver estado de señales de la semana
```
Ejecuta python scripts/senal_manager.py y muéstrame el resumen de señales de esta semana.
```

### Ver plan del día
```
Ejecuta python scripts/orquestador.py y muéstrame el plan de hoy.
```

### Obtener precios actuales
```
Obtén los precios actuales de USD/CLP, Oro, WTI y US100 usando web search. Muéstralos con variación del día.
```

---

## 📈 MT5 — MetaTrader 5

### Primera vez: instalar dependencias y configurar
```
Ejecuta python scripts/setup.py para instalar todas las dependencias.
Luego ejecuta python scripts/mt5_integration.py para probar la conexión con MT5.
Si algún ticker no funciona, usa la función buscar_simbolo() para encontrar
el nombre correcto en tu broker. Muéstrame los resultados.
```

### Buscar nombres de activos en tu broker
```
Ejecuta este código Python para buscar los símbolos correctos en tu broker MT5:

import MetaTrader5 as mt5
mt5.initialize()
# Buscar símbolos que contengan estos textos:
for texto in ["CLP", "XAU", "GOLD", "OIL", "WTI", "NAS", "US100", "USTEC"]:
    simbolos = mt5.symbols_get(group=f"*{texto}*")
    if simbolos:
        print(f"{texto}: {[s.name for s in simbolos]}")
mt5.shutdown()

Muéstrame los resultados para actualizar el TICKER_MAP_MT5 en scripts/mt5_integration.py.
```

### Análisis completo de un activo desde MT5
```
Ejecuta el análisis completo desde MT5 para [ACTIVO] en [TEMPORALIDAD]:
1. Conéctate a MT5 con scripts/mt5_integration.py
2. Obtén el precio actual desde el broker
3. Descarga las velas y calcula indicadores (SMA 50, SMA 200, RSI)
4. Identifica soportes, resistencias y sesgo
5. Genera el gráfico PNG con niveles dibujados
6. Muéstrame el análisis y la imagen generada

Si el gráfico se genera correctamente, formatea el mensaje de apertura
para WhatsApp incluyendo la ruta de la imagen para adjuntar al mensaje.
```

### Generar gráficos de todos los activos del día
```
Genera los gráficos del día desde MT5:
1. Lee el plan del día (python scripts/orquestador.py)
2. Para cada activo del día, ejecuta analisis_completo_activo() desde scripts/mt5_integration.py
3. Genera gráficos en 4H con SMA 50, SMA 200 y RSI
4. Dibuja soportes (verde) y resistencias (rojo) en cada gráfico
5. Guarda las imágenes en data/charts/
6. Muéstrame los gráficos generados y el análisis de cada uno
```

### Operativa completa con MT5 (el comando definitivo)
```
Ejecuta la operativa completa del día usando MT5 como fuente de datos:

1. Ejecuta scripts/orquestador.py para el plan del día
2. Conéctate a MT5
3. Para cada activo del día:
   a. Obtén precio actual desde MT5
   b. Descarga velas en 4H y 1H
   c. Calcula indicadores: SMA 50, SMA 200, RSI (elige UNO para el mensaje)
   d. Identifica soportes, resistencias y sesgo
   e. Genera gráfico PNG con niveles
4. Busca con web search la noticia económica más relevante del día
5. Explica los drivers consultando config/drivers.json
6. Genera encuesta del día según la agenda
7. Formatea TODO para WhatsApp con los templates
8. Incluye las rutas de imágenes para adjuntar

Muéstrame cada mensaje + imagen para aprobación.
Al desconectarte de MT5 al final.
```
