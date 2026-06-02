# Referencia de comandos

Todos los comandos se invocan desde Claude Code con `/nombre`. Cada comando genera contenido formateado para WhatsApp y lo muestra para aprobación antes de guardarlo en `data/mensajes/`.

---

## Capa 1 — Comandos de día

Paquetes completos para cada día de la semana. Generan varias piezas en orden, una por una, esperando aprobación entre cada una.

### `/domingo`
**Cuándo**: domingo, para preparar la semana.

**Genera**:
1. Resumen noticias del fin de semana (eventos que pasaron sábado-domingo)
2. Preview de la semana: datos macro importantes, eventos a monitorear
3. Sesgo para el lunes: qué esperar en la apertura
4. Encuesta de la semana para el grupo

**Tipo de archivo guardado**: `domingo.txt`

---

### `/lunes`
**Cuándo**: lunes AM, antes de la apertura del mercado.

**Genera** (5 piezas):
1. Resumen del calendario económico semanal (datos de alto impacto L-V)
2. Earnings de la semana (empresas del catálogo que reportan)
3. Concepto de la semana (macro / técnico / conceptual)
4. Apertura de mercado (2 activos del día, niveles 4H)
5. Encuesta de tendencia AM

**Tipo de archivo guardado**: `apertura.txt`, `concepto.txt`, `encuesta.txt`

---

### `/martes`
**Cuándo**: martes AM.

**Genera** (3 piezas):
1. Apertura de mercado (2 activos del día, niveles 4H)
2. Dato macro del día (calendario → director elige)
3. Encuesta de precio de apertura

**Tipo de archivo guardado**: `apertura.txt`, `dato_macro.txt`, `encuesta.txt`

---

### `/miercoles`
**Cuándo**: miércoles AM. Prioridad: datos EIA de inventarios de petróleo (suelen publicarse miércoles).

**Genera** (3 piezas):
1. Apertura de mercado (2 activos, con énfasis en WTI si hay EIA)
2. Dato macro del día (EIA tiene prioridad si aplica)
3. Encuesta de tendencia AM

**Tipo de archivo guardado**: `apertura.txt`, `dato_macro.txt`, `encuesta.txt`

---

### `/jueves`
**Cuándo**: jueves AM. Alerta especial para Jobless Claims (dato semanal de desempleo EE.UU.).

**Genera** (3 piezas):
1. Apertura de mercado (2 activos)
2. Dato macro (Jobless Claims tiene prioridad si aplica)
3. Encuesta de tendencia AM

**Tipo de archivo guardado**: `apertura.txt`, `dato_macro.txt`, `encuesta.txt`

---

### `/viernes_am`
**Cuándo**: viernes AM. Cubre **3 activos** (en vez de 2). Primer viernes del mes = NFP (dato de empleo).

**Genera** (3 piezas):
1. Apertura de 3 activos (niveles 4H cada uno)
2. Dato macro del día (NFP destacado si aplica)
3. Encuesta de precio de apertura del lunes

**Tipo de archivo guardado**: `apertura.txt`, `dato_macro.txt`, `encuesta.txt`

---

### `/viernes_pm`
**Cuándo**: viernes PM, tras el cierre del mercado (~16:00-17:00 CLT).

**Genera**:
1. Resumen de la semana por activo (cómo cerró cada uno, hecho relevante)
2. Qué viene la próxima semana (datos macro, eventos)
3. Reflexión o aprendizaje de la semana

**Tipo de archivo guardado**: `cierre.txt`

---

## Capa 2 — Comandos de tarea (ad hoc)

Para situaciones puntuales que no corresponden a la operativa estándar del día.

### `/encuesta [tipo] [activo]`
Genera una encuesta de **sentimiento puro** para el grupo. Sin precios, sin números y sin contenido educativo. Tres tipos:
- `posicion [activo?]` — qué está operando el grupo (🟢 Compré / 🔴 Vendí / ⚪ No operé). Sin activo, un poll por cada activo del día.
- `tendencia [activo?]` — qué tendencia proyectan (📈 Alcista / 📉 Bajista / ➡️ Lateral).
- `movimiento [semana?]` — qué activo tendrá más movimiento (hoy, o `semana` para la dominical).

El tipo es obligatorio (sin tipo, el comando pregunta). Los activos salen de `data/plan_hoy.json`. La contextualización la da el mensaje previo de la mañana, no la encuesta. Lo educativo (revelado, lección) vive en `/rencuesta` y futuros comandos.

**Ejemplo**: `/encuesta posicion USDCLP`

---

### `/dato_macro`
Trae el calendario económico del día y lista los datos disponibles. El director elige cuál desarrollar. El comando genera el mensaje explicativo para ese dato (qué es, a qué hora sale, qué se espera, cómo podría reaccionar el activo).

---

### `/noticia`
Busca 3-5 noticias relevantes del momento para los activos del grupo. El director elige cuál publicar. El comando la formatea en lenguaje simple para el grupo.

---

### `/chart`
Genera un screenshot de MT5 para el activo y temporalidad elegidos. Opciones de indicador: EMA+ATR o S/R fractal. El chart se guarda en `data/charts/`.

---

### `/señal`
Genera una señal operativa. **Antes de generar**, verifica en `data/historial_señales.json` cuántas señales se han enviado esta semana. Si ya hay 3, informa al director y no genera una nueva.

Campos obligatorios: ticker, nombre activo, BUY/SELL, entrada, TP, SL (en puntos y en CLP), volumen, tipo (swing/scalper), hasta 3 bullets de análisis.

---

### `/alerta`
Detecta qué está moviendo el mercado ahora mismo y genera una alerta urgente para el grupo. Busca noticias frescas (últimas 2 horas) y las conecta con el impacto en los activos cubiertos.

---

### `/concepto`
Genera un concepto educativo conectado a algo que pasó esta semana. Propone 3 opciones y el director elige una. El mensaje explica el concepto en lenguaje simple con un ejemplo real del mercado actual.

---

### `/pregunta`
Genera una pregunta abierta para fomentar la participación del grupo. Ejemplo: *"¿Por qué creen que el oro subió tras el dato de inflación?"*. Máximo 1 por semana.

---

### `/estado`
Dashboard del sistema. Muestra:
- Señales de la semana (cuántas usadas de 3)
- Plan del día según `config/agenda_semanal.json`
- Activos del día
- Estado de MCPs (reporte-flash ✅, WhatsApp ⏳)
- Mensajes guardados hoy en `data/mensajes/`

---

## Capa 3 — Acciones individuales

### `/accion [TICKER]`
Análisis completo de una de las 12 acciones del catálogo. Incluye:
- Análisis técnico (4H via `analyze_ticker`)
- Drivers específicos de la empresa
- Noticias recientes de earnings o eventos corporativos
- Conexión con su índice (US100, US30)

**Tickers válidos**: `#AAPL` · `#MSFT` · `#NVDA` · `#AMZN` · `#JPM` · `#BAC` · `#GS` · `#MS` · `#BA` · `#CAT` · `#GE` · `#DE`

---

### `/earnings`
Calendario de earnings de las 12 acciones para la semana actual. Para cada empresa que reporta incluye: día, hora Chile (BMO/AMC), EPS esperado, ingresos esperados, foco del mercado y conexión con su índice.

---

## Flujo de aprobación (aplica a todos los comandos)

```
Comando genera borrador
        ↓
Director revisa en pantalla
        ↓
¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?
        ↓
Si aprueba → Claude guarda en data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt
        ↓
Director copia texto y lo pega en el grupo WhatsApp
```

**Nunca se envía nada sin aprobación explícita.**

---

## Tipos de archivo guardado

| Tipo | Descripción |
|------|-------------|
| `alerta` | Alerta urgente de mercado |
| `apertura` | Análisis de apertura de mercado |
| `concepto` | Concepto educativo de la semana |
| `encuesta` | Encuesta de sentimiento (posicion/tendencia/movimiento) |
| `señal` | Señal operativa (BUY/SELL) |
| `noticia` | Noticia seleccionada del día |
| `dato_macro` | Explicación de dato económico |
| `cierre` | Cierre semanal del viernes |
| `pregunta` | Pregunta abierta al grupo |
| `niveles` | Niveles técnicos del día |
