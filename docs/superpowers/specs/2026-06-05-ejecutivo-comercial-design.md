# Diseño: Sistema de Habilitación Comercial para Ejecutivos

**Issue**: #62  
**Fecha**: 2026-06-05  
**Estado**: Aprobado — listo para implementación  
**Fase siguiente**: Plan de implementación

---

## Contexto

El sistema actual entrega contenido al cliente final (análisis, niveles, encuestas, conceptos). Este diseño agrega una **capa paralela** orientada al ejecutivo comercial, entregándole piezas para dos propósitos: **captación** (prospección y primer contacto) y **mantención** (seguimiento y fidelización).

El ejecutivo necesita tres formatos por pieza:
- **HTML** — preview interactivo para prepararse
- **PDF** — adjunto formal para enviar al cliente (generado desde HTML via `Ctrl+P → Guardar como PDF`)
- **TXT** — texto plano para WhatsApp del cliente

---

## Decisiones de Discovery

| Pregunta | Decisión |
|----------|----------|
| Catálogo de productos | `config/productos.json` placeholder; contenido en issue separado |
| Segmentación | Múltiple áreas; MVP funcional con área `trading` |
| Canal del ejecutivo | Email (HTML + PDF) |
| Identidad visual | Plantilla corporativa HTML derivada de `ETF_XLF_card_interactiva.html` |
| Timing vs cliente | Simultáneo |
| Métricas | Pospuestas para iteración posterior |
| Estructura de comando | 1 comando master `/ejecutivo [tipo]` |

---

## Arquitectura

### Comando

Un único `.claude/commands/ejecutivo.md` que parsea `$ARGUMENTS` y despacha a 5 flujos internos.

```
/ejecutivo kit
/ejecutivo folleto [producto]
/ejecutivo apertura
/ejecutivo semana
/ejecutivo mirror
```

Patrón consistente con `/encuesta [tipo]` y `/accion [TICKER]` ya existentes.

### Artefactos de salida

Cada ejecución produce 3 archivos guardados en:

```
data/mensajes/ejecutivos/YYYY-MM-DD/<tipo>/
├── preview.html      ← abre en navegador para prepararse + exportar PDF
└── whatsapp.txt      ← copia y pega en WhatsApp del cliente
```

> El PDF no se genera programáticamente. El comando muestra la instrucción: *"Abre `preview.html` en Chrome → Ctrl+P → Guardar como PDF"*. El HTML tiene `@media print` optimizado para que el resultado quede profesional.

La ruta se construye con `scripts\ruta_mensaje.ps1` igual que el resto del sistema. Tipo: el subtipo del comando (`kit`, `folleto`, `apertura`, `semana`, `mirror`).

---

## Archivos nuevos

```
config/
├── ejecutivos.json          ← áreas + config por área
├── productos.json           ← placeholder (issue separado)
templates/ejecutivo/
├── kit.html
├── folleto.html
├── apertura.html
├── semana.html
└── mirror.html
.claude/commands/
└── ejecutivo.md
```

---

## Sistema de diseño HTML

### Paleta corporativa (derivada de `ETF_XLF_card_interactiva.html`)

```css
:root {
  --bg: #0d1b2a;
  --card-bg: #0f2744;
  --gold: #f0a500;
  --green: #00c853;
  --red: #ff3d3d;
  --blue-accent: #1565c0;
  --text: #e8f4fd;
  --muted: #7a9bbb;
  --border: rgba(255,255,255,0.08);
  font-family: 'Inter', sans-serif;
}
```

### Doble CSS (pantalla y PDF)

- **Pantalla**: fondo oscuro `#0d1b2a`, tarjetas `#0f2744`, acentos dorados
- **`@media print`**: fondo blanco, texto oscuro `#111`, gold → azul corporativo `#1565c0`, bordes visibles. PDF profesional sin fondo oscuro.

### Estructura común de todos los templates

```
[HEADER]  logo "GrupoInteligencia.com" · área · fecha
[BODY]    contenido específico del tipo
[FOOTER]  firma del ejecutivo + disclaimer genérico
```

### Variables de relleno

`{{fecha}}`, `{{area}}`, `{{ejecutivo_firma}}`, `{{activo}}`, `{{contenido_principal}}`, `{{disclaimer}}`

---

## Los 5 flujos

### `kit` — Kit de primer contacto

**Genera:**
- Texto de presentación del área de trading
- Script "no contesta": mensaje corto, no intrusivo
- Script "sí contesta": intro a banca inversiones, por qué importa, seguridad, respaldo CMF

**HTML preview**: card con los 3 secciones claramente separadas  
**TXT**: versión condensada del script de contacto  
**Fuente de datos**: `config/ejecutivos.json` (área activa)

---

### `folleto [producto]` — Folleto de producto

**Genera:**
- Card corporativa: nombre del producto, descripción, beneficios clave, para quién es, disclaimer

**HTML preview**: card estilo corporativo (derivada de la card de señales)  
**TXT**: descripción breve en 3 bullets para WhatsApp  
**Fuente de datos**: `config/productos.json`

**Fallback productos vacío**: si `productos.json` está vacío, el comando informa al director y permite ingresar los datos del producto manualmente para generar igual el folleto. Sin bloqueo.

---

### `apertura` — Niveles del día como oportunidades

**Genera:**
- Los mismos niveles técnicos de `/apertura`, reencuadrados en lenguaje comercial
- "Zona de entrada interesante" en vez de análisis técnico
- Argumento de venta por activo

**HTML preview**: card por activo con encuadre comercial  
**TXT**: argumento comercial del día en lenguaje cliente  
**Fuente de datos**: `mcp__market-data__get_asset_levels` (reutiliza sin cambios)

---

### `semana` — Calendario semanal como oportunidades

**Genera:**
- Calendario macro de la semana reenmarcado para el ejecutivo
- Por cada dato económico: producto relevante + tipo de cliente a llamar

**HTML preview**: tabla semanal con oportunidades de conversación  
**TXT**: preview de oportunidades de la semana  
**Fuente de datos**: `mcp__market-data__obtener_calendario_macro` (reutiliza sin cambios)

---

### `mirror` — Versión ejecutivo de la última pieza del cliente

**Genera:**
- Resumen de qué recibió el cliente hoy
- Cómo usar esa información en conversación con el cliente
- Qué preguntar / qué ofrecer en base a ese contexto

**HTML preview**: card de habilitación con 3 secciones (qué vio el cliente / cómo usarlo / qué hacer)  
**TXT**: guía rápida en formato WhatsApp  
**Fuente de datos**: último archivo en `data/mensajes/YYYY-MM-DD/` (pieza cliente del día)

---

## Config: `ejecutivos.json` (MVP)

```json
{
  "_nota": "Áreas de ejecutivos. MVP activo: solo 'trading'. Agregar más áreas aquí.",
  "area_activa": "trading",
  "areas": {
    "trading": {
      "nombre": "Área de Trading",
      "email_firma": "Grupo Inteligencia · Asesoría Financiera",
      "activos_foco": ["USDCLP", "XAUUSD", "WTI.spot", "US100.spot"],
      "disclaimer": "Este material es de uso interno del ejecutivo. No constituye asesoría de inversión. Grupo Inteligencia SpA está registrada en la CMF."
    }
  }
}
```

---

## Flujo de aprobación

Igual al flujo actual del sistema:
1. Comando genera los 3 artefactos
2. Muestra al director para aprobación
3. Director aprueba → se guardan en `data/mensajes/ejecutivos/`
4. Director abre `preview.html`, exporta PDF via navegador, distribuye

---

## Pendientes para issues futuros

- Completar `config/productos.json` con catálogo real de productos
- Definir más áreas de ejecutivos (banca privada, banca masiva, empresas)
- Métricas de actividad comercial
- Automatización del envío (cuando Evolution API esté conectada)
