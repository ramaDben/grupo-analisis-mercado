# Sistema de Habilitación Comercial para Ejecutivos — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar el comando `/ejecutivo [tipo]` que genera piezas para ejecutivos comerciales: HTML preview + TXT WhatsApp, con paleta corporativa y flujo de aprobación igual al del sistema cliente.

**Architecture:** Comando master `.claude/commands/ejecutivo.md` que parsea `$ARGUMENTS` y despacha a 5 flujos (kit/folleto/apertura/semana/mirror). Cada flujo llena templates HTML en `templates/ejecutivo/` con `{{variables}}` reemplazadas en tiempo de ejecución y guarda los artefactos en `data/mensajes/ejecutivos/`. El PDF lo genera el ejecutivo via Ctrl+P desde el navegador.

**Tech Stack:** Claude Code slash commands (markdown), HTML/CSS con @media print, PowerShell para rutas y fechas, MCP market-data para datos de mercado.

**Spec:** `docs/superpowers/specs/2026-06-05-ejecutivo-comercial-design.md`

---

## Mapa de archivos

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `config/ejecutivos.json` | Crear | Áreas, firma, activos foco, disclaimer |
| `config/productos.json` | Ya existe | Placeholder — contenido en issue separado |
| `templates/ejecutivo/kit.html` | Crear | Template HTML del kit de primer contacto |
| `templates/ejecutivo/folleto.html` | Crear | Template HTML del folleto de producto |
| `templates/ejecutivo/apertura.html` | Crear | Template HTML de niveles como oportunidades |
| `templates/ejecutivo/semana.html` | Crear | Template HTML del calendario semanal ejecutivo |
| `templates/ejecutivo/mirror.html` | Crear | Template HTML del mirror de pieza cliente |
| `.claude/commands/ejecutivo.md` | Crear | Comando master con 5 flujos |

---

## Task 1: Configuración base

**Files:**
- Create: `config/ejecutivos.json`

- [ ] **Step 1: Crear `config/ejecutivos.json`**

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

- [ ] **Step 2: Verificar que ambos configs existen y son JSON válido**

```powershell
Get-Content config/ejecutivos.json | ConvertFrom-Json | Select-Object area_activa
Get-Content config/productos.json  | ConvertFrom-Json | Select-Object _pendiente
```

Resultado esperado:
```
area_activa
-----------
trading

_pendiente
----------
Definir con el director...
```

- [ ] **Step 3: Commit**

```powershell
git add config/ejecutivos.json
git commit -m "feat(#62): agregar config/ejecutivos.json con area trading MVP"
```

---

## Task 2: Template `kit.html`

**Files:**
- Create: `templates/ejecutivo/kit.html`

El template usa `{{variables}}` que el comando reemplaza en tiempo de ejecución. Las variables son: `{{fecha}}`, `{{area_nombre}}`, `{{ejecutivo_firma}}`, `{{disclaimer}}`.

- [ ] **Step 1: Crear carpeta y template**

Crear `templates/ejecutivo/kit.html` con este contenido:

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kit de Primer Contacto — {{area_nombre}}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  :root {
    --bg: #0d1b2a; --card-bg: #0f2744; --gold: #f0a500;
    --green: #00c853; --text: #e8f4fd; --muted: #7a9bbb;
    --border: rgba(255,255,255,0.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); font-family:'Inter',sans-serif; color:var(--text); padding:24px 16px 40px; }
  .header { text-align:center; margin-bottom:24px; }
  .brand { font-size:11px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-bottom:6px; }
  .title { font-size:22px; font-weight:800; color:var(--gold); }
  .subtitle { font-size:12px; color:var(--muted); margin-top:4px; }
  .card { background:var(--card-bg); border:1px solid var(--border); border-radius:16px; padding:28px; max-width:680px; margin:0 auto 20px; }
  .card-label { font-size:10px; letter-spacing:2px; text-transform:uppercase; color:var(--muted); margin-bottom:12px; }
  .card-title { font-size:16px; font-weight:800; color:var(--gold); margin-bottom:16px; }
  .card-body { font-size:14px; line-height:1.7; color:var(--text); }
  .card-body p { margin-bottom:10px; }
  .tag { display:inline-block; background:rgba(240,165,0,.15); color:var(--gold); font-size:10px; font-weight:700; padding:3px 10px; border-radius:20px; letter-spacing:1px; margin-bottom:16px; }
  .footer { text-align:center; font-size:11px; color:var(--muted); margin-top:24px; max-width:680px; margin-left:auto; margin-right:auto; }

  @media print {
    :root { --bg:#fff; --card-bg:#f8f9fa; --gold:#1565c0; --text:#111; --muted:#555; --border:#ddd; }
    body { background:#fff; color:#111; padding:12px; }
    .card { border:1px solid #ddd; box-shadow:none; }
    .brand, .subtitle { color:#555; }
    .tag { background:#e8f0fe; color:#1565c0; border:1px solid #c5cae9; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="brand">GrupoInteligencia.com · Asesoría Financiera</div>
  <div class="title">Kit de Primer Contacto</div>
  <div class="subtitle">{{area_nombre}} · {{fecha}}</div>
</div>

<!-- SECCIÓN 1: PRESENTACIÓN -->
<div class="card">
  <div class="tag">PRESENTACIÓN</div>
  <div class="card-title">¿Quiénes somos?</div>
  <div class="card-body">
    {{seccion_presentacion}}
  </div>
</div>

<!-- SECCIÓN 2: SCRIPT NO CONTESTA -->
<div class="card">
  <div class="tag">SCRIPT · NO CONTESTA</div>
  <div class="card-title">Mensaje para dejar si no contesta</div>
  <div class="card-body">
    {{script_no_contesta}}
  </div>
</div>

<!-- SECCIÓN 3: SCRIPT SÍ CONTESTA -->
<div class="card">
  <div class="tag">SCRIPT · SÍ CONTESTA</div>
  <div class="card-title">Guía de conversación cuando contesta</div>
  <div class="card-body">
    {{script_si_contesta}}
  </div>
</div>

<div class="footer">
  {{ejecutivo_firma}}<br>
  <span style="font-size:10px;opacity:.7">{{disclaimer}}</span>
</div>

</body>
</html>
```

- [ ] **Step 2: Verificar que el archivo existe**

```powershell
Test-Path templates/ejecutivo/kit.html
```

Resultado esperado: `True`

- [ ] **Step 3: Commit**

```powershell
git add templates/ejecutivo/kit.html
git commit -m "feat(#62): template HTML kit primer contacto ejecutivo"
```

---

## Task 3: Template `folleto.html`

**Files:**
- Create: `templates/ejecutivo/folleto.html`

Variables: `{{fecha}}`, `{{area_nombre}}`, `{{ejecutivo_firma}}`, `{{disclaimer}}`, `{{producto_nombre}}`, `{{producto_tipo}}`, `{{producto_descripcion}}`, `{{producto_beneficios}}` (lista HTML de `<li>`), `{{producto_para_quien}}`.

- [ ] **Step 1: Crear `templates/ejecutivo/folleto.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{producto_nombre}} — Folleto</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
  :root {
    --bg:#0d1b2a; --card-bg:#0f2744; --gold:#f0a500; --green:#00c853;
    --blue-accent:#1565c0; --text:#e8f4fd; --muted:#7a9bbb;
    --border:rgba(255,255,255,0.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); font-family:'Inter',sans-serif; color:var(--text); padding:24px 16px 40px; display:flex; flex-direction:column; align-items:center; }
  .brand-bar { font-size:11px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-bottom:20px; }
  .card { background:var(--card-bg); border:1px solid var(--border); border-radius:20px; width:100%; max-width:680px; overflow:hidden; box-shadow:0 24px 80px rgba(0,0,0,.5); }
  .card-header { padding:28px 32px 20px; border-bottom:1px solid var(--border); }
  .product-type { font-size:10px; background:rgba(240,165,0,.15); color:var(--gold); padding:4px 12px; border-radius:20px; font-weight:700; letter-spacing:1px; display:inline-block; margin-bottom:12px; }
  .product-name { font-size:36px; font-weight:900; color:var(--gold); line-height:1.1; }
  .product-desc { font-size:14px; color:var(--muted); margin-top:10px; line-height:1.6; }
  .card-section { padding:24px 32px; border-bottom:1px solid var(--border); }
  .section-label { font-size:10px; letter-spacing:2px; text-transform:uppercase; color:var(--muted); margin-bottom:14px; }
  .benefits { list-style:none; display:flex; flex-direction:column; gap:10px; }
  .benefits li { font-size:14px; color:var(--text); padding-left:20px; position:relative; line-height:1.55; }
  .benefits li::before { content:'•'; position:absolute; left:0; color:var(--gold); font-size:18px; top:-2px; }
  .para-quien { font-size:14px; color:var(--text); line-height:1.7; }
  .card-footer { padding:16px 32px; display:flex; justify-content:space-between; align-items:center; background:rgba(0,0,0,.2); }
  .footer-brand { font-size:11px; color:var(--muted); font-style:italic; }
  .footer-date { font-size:11px; color:var(--muted); }
  .disclaimer { font-size:10px; color:var(--muted); padding:14px 32px; text-align:center; max-width:680px; line-height:1.5; }

  @media print {
    :root { --bg:#fff; --card-bg:#f8f9fa; --gold:#1565c0; --text:#111; --muted:#555; --border:#ddd; }
    body { background:#fff; align-items:flex-start; padding:8px; }
    .card { box-shadow:none; border:1px solid #ddd; max-width:100%; }
    .product-type { background:#e8f0fe; color:#1565c0; border:1px solid #c5cae9; }
    .brand-bar { color:#555; }
  }
</style>
</head>
<body>

<div class="brand-bar">GrupoInteligencia.com · Asesoría Financiera</div>

<div class="card">
  <div class="card-header">
    <div class="product-type">{{producto_tipo}}</div>
    <div class="product-name">{{producto_nombre}}</div>
    <div class="product-desc">{{producto_descripcion}}</div>
  </div>

  <div class="card-section">
    <div class="section-label">¿Por qué es interesante?</div>
    <ul class="benefits">
      {{producto_beneficios}}
    </ul>
  </div>

  <div class="card-section">
    <div class="section-label">¿Para quién es?</div>
    <div class="para-quien">{{producto_para_quien}}</div>
  </div>

  <div class="card-footer">
    <span class="footer-brand">{{ejecutivo_firma}}</span>
    <span class="footer-date">{{fecha}}</span>
  </div>
</div>

<div class="disclaimer">{{disclaimer}}</div>

</body>
</html>
```

- [ ] **Step 2: Verificar**

```powershell
Test-Path templates/ejecutivo/folleto.html
```

- [ ] **Step 3: Commit**

```powershell
git add templates/ejecutivo/folleto.html
git commit -m "feat(#62): template HTML folleto de producto ejecutivo"
```

---

## Task 4: Template `apertura.html`

**Files:**
- Create: `templates/ejecutivo/apertura.html`

Variables: `{{fecha}}`, `{{area_nombre}}`, `{{ejecutivo_firma}}`, `{{disclaimer}}`, `{{cards_activos}}` (bloque HTML repetido por activo con `{{activo_nombre}}`, `{{zona_entrada}}`, `{{precio_actual}}`, `{{argumento_comercial}}`, `{{clientes_objetivo}}`).

- [ ] **Step 1: Crear `templates/ejecutivo/apertura.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Oportunidades del Día — {{fecha}}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
  :root {
    --bg:#0d1b2a; --card-bg:#0f2744; --gold:#f0a500; --green:#00c853;
    --text:#e8f4fd; --muted:#7a9bbb; --border:rgba(255,255,255,0.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); font-family:'Inter',sans-serif; color:var(--text); padding:24px 16px 40px; }
  .header { text-align:center; margin-bottom:24px; }
  .brand { font-size:11px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-bottom:6px; }
  .title { font-size:22px; font-weight:800; color:var(--gold); }
  .subtitle { font-size:12px; color:var(--muted); margin-top:4px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; max-width:980px; margin:0 auto; }
  .asset-card { background:var(--card-bg); border:1px solid var(--border); border-radius:16px; overflow:hidden; }
  .asset-header { padding:20px 22px 14px; border-bottom:1px solid var(--border); }
  .asset-name { font-size:28px; font-weight:900; color:var(--gold); }
  .zona-label { font-size:10px; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-top:8px; }
  .zona-value { font-size:18px; font-weight:700; color:var(--green); margin-top:2px; }
  .precio-row { font-size:12px; color:var(--muted); margin-top:6px; }
  .asset-body { padding:16px 22px; }
  .body-label { font-size:10px; letter-spacing:1.5px; text-transform:uppercase; color:var(--muted); margin-bottom:8px; }
  .argumento { font-size:13px; color:var(--text); line-height:1.6; margin-bottom:14px; }
  .clientes-tag { display:inline-block; background:rgba(240,165,0,.1); border:1px solid rgba(240,165,0,.25); color:var(--gold); font-size:11px; font-weight:600; padding:5px 12px; border-radius:20px; }
  .footer { text-align:center; font-size:11px; color:var(--muted); margin-top:24px; }

  @media print {
    :root { --bg:#fff; --card-bg:#f8f9fa; --gold:#1565c0; --green:#1b7e44; --text:#111; --muted:#555; --border:#ddd; }
    body { background:#fff; }
    .asset-card { border:1px solid #ddd; break-inside:avoid; }
    .zona-value { color:#1b7e44; }
    .clientes-tag { background:#e8f0fe; border-color:#c5cae9; color:#1565c0; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="brand">GrupoInteligencia.com · {{area_nombre}}</div>
  <div class="title">Oportunidades del Día</div>
  <div class="subtitle">{{fecha}} · Uso interno ejecutivo</div>
</div>

<div class="grid">
  {{cards_activos}}
</div>

<div class="footer">
  {{ejecutivo_firma}} · <span style="opacity:.6">{{disclaimer}}</span>
</div>

</body>
</html>
```

El bloque `{{cards_activos}}` se repite por cada activo con esta estructura:
```html
<div class="asset-card">
  <div class="asset-header">
    <div class="asset-name">{{activo_nombre}}</div>
    <div class="zona-label">Zona de entrada interesante</div>
    <div class="zona-value">{{zona_entrada}}</div>
    <div class="precio-row">Precio actual: {{precio_actual}}</div>
  </div>
  <div class="asset-body">
    <div class="body-label">Argumento comercial</div>
    <div class="argumento">{{argumento_comercial}}</div>
    <div class="body-label">Clientes a contactar</div>
    <div class="clientes-tag">{{clientes_objetivo}}</div>
  </div>
</div>
```

- [ ] **Step 2: Verificar**

```powershell
Test-Path templates/ejecutivo/apertura.html
```

- [ ] **Step 3: Commit**

```powershell
git add templates/ejecutivo/apertura.html
git commit -m "feat(#62): template HTML apertura ejecutivo (niveles como oportunidades)"
```

---

## Task 5: Template `semana.html`

**Files:**
- Create: `templates/ejecutivo/semana.html`

Variables: `{{fecha_inicio}}`, `{{fecha_fin}}`, `{{area_nombre}}`, `{{ejecutivo_firma}}`, `{{disclaimer}}`, `{{filas_semana}}` (filas HTML de tabla).

- [ ] **Step 1: Crear `templates/ejecutivo/semana.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Oportunidades de la Semana — {{fecha_inicio}}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  :root {
    --bg:#0d1b2a; --card-bg:#0f2744; --gold:#f0a500; --green:#00c853;
    --red:#ff3d3d; --text:#e8f4fd; --muted:#7a9bbb; --border:rgba(255,255,255,0.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); font-family:'Inter',sans-serif; color:var(--text); padding:24px 16px 40px; }
  .header { text-align:center; margin-bottom:24px; }
  .brand { font-size:11px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-bottom:6px; }
  .title { font-size:22px; font-weight:800; color:var(--gold); }
  .subtitle { font-size:12px; color:var(--muted); margin-top:4px; }
  .table-wrap { max-width:980px; margin:0 auto; overflow-x:auto; }
  table { width:100%; border-collapse:collapse; }
  th { background:rgba(240,165,0,.1); color:var(--gold); font-size:10px; letter-spacing:1.5px; text-transform:uppercase; padding:12px 16px; text-align:left; border-bottom:1px solid var(--border); }
  td { padding:14px 16px; border-bottom:1px solid var(--border); font-size:13px; vertical-align:top; line-height:1.55; }
  tr:hover td { background:rgba(255,255,255,.03); }
  .dia-cell { font-weight:700; color:var(--gold); white-space:nowrap; }
  .impact-high { color:var(--red); font-weight:700; }
  .impact-med  { color:var(--gold); }
  .producto-tag { display:inline-block; background:rgba(0,200,83,.1); border:1px solid rgba(0,200,83,.2); color:var(--green); font-size:11px; padding:3px 10px; border-radius:20px; }
  .footer { text-align:center; font-size:11px; color:var(--muted); margin-top:24px; }

  @media print {
    :root { --bg:#fff; --card-bg:#f8f9fa; --gold:#1565c0; --green:#1b7e44; --red:#c62828; --text:#111; --muted:#555; --border:#ddd; }
    body { background:#fff; }
    th { background:#e8f0fe; color:#1565c0; }
    .producto-tag { background:#e8f5e9; border-color:#a5d6a7; color:#1b7e44; }
    tr { break-inside:avoid; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="brand">GrupoInteligencia.com · {{area_nombre}}</div>
  <div class="title">Oportunidades de la Semana</div>
  <div class="subtitle">{{fecha_inicio}} al {{fecha_fin}} · Uso interno ejecutivo</div>
</div>

<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th>Día / Hora</th>
        <th>Evento económico</th>
        <th>Impacto</th>
        <th>Producto relevante</th>
        <th>Clientes a contactar</th>
      </tr>
    </thead>
    <tbody>
      {{filas_semana}}
    </tbody>
  </table>
</div>

<div class="footer">
  {{ejecutivo_firma}} · <span style="opacity:.6">{{disclaimer}}</span>
</div>

</body>
</html>
```

Cada fila `{{filas_semana}}` tiene esta estructura:
```html
<tr>
  <td class="dia-cell">{{dia}}<br><span style="font-weight:400;color:var(--muted);font-size:12px;">{{hora_clst}}</span></td>
  <td>{{evento_nombre}}<br><span style="color:var(--muted);font-size:12px;">{{evento_pais}} · {{evento_periodo}}</span></td>
  <td class="{{impact-high|impact-med}}">{{impacto_emoji}} {{impacto_label}}</td>
  <td><span class="producto-tag">{{producto_relevante}}</span></td>
  <td style="color:var(--muted)">{{tipo_cliente}}</td>
</tr>
```

- [ ] **Step 2: Verificar**

```powershell
Test-Path templates/ejecutivo/semana.html
```

- [ ] **Step 3: Commit**

```powershell
git add templates/ejecutivo/semana.html
git commit -m "feat(#62): template HTML semana ejecutivo (calendario como oportunidades)"
```

---

## Task 6: Template `mirror.html`

**Files:**
- Create: `templates/ejecutivo/mirror.html`

Variables: `{{fecha}}`, `{{area_nombre}}`, `{{ejecutivo_firma}}`, `{{disclaimer}}`, `{{tipo_pieza_cliente}}`, `{{resumen_cliente}}`, `{{como_usarlo}}`, `{{que_hacer}}`.

- [ ] **Step 1: Crear `templates/ejecutivo/mirror.html`**

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Habilitación Ejecutivo — {{fecha}}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
  :root {
    --bg:#0d1b2a; --card-bg:#0f2744; --gold:#f0a500; --green:#00c853;
    --blue-accent:#1565c0; --text:#e8f4fd; --muted:#7a9bbb;
    --border:rgba(255,255,255,0.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); font-family:'Inter',sans-serif; color:var(--text); padding:24px 16px 40px; }
  .header { text-align:center; margin-bottom:24px; }
  .brand { font-size:11px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; margin-bottom:6px; }
  .title { font-size:22px; font-weight:800; color:var(--gold); }
  .subtitle { font-size:12px; color:var(--muted); margin-top:4px; }
  .section { background:var(--card-bg); border:1px solid var(--border); border-radius:16px; padding:24px 28px; max-width:720px; margin:0 auto 16px; }
  .section-num { font-size:10px; letter-spacing:2px; text-transform:uppercase; color:var(--muted); margin-bottom:6px; }
  .section-title { font-size:16px; font-weight:800; color:var(--gold); margin-bottom:14px; }
  .section-body { font-size:14px; line-height:1.7; color:var(--text); }
  .section-body p { margin-bottom:10px; }
  .section-body ul { padding-left:18px; }
  .section-body li { margin-bottom:8px; }
  .pieza-badge { display:inline-block; background:rgba(21,101,192,.15); border:1px solid rgba(21,101,192,.3); color:#7ca9ff; font-size:11px; font-weight:600; padding:4px 12px; border-radius:20px; margin-bottom:14px; }
  .footer { text-align:center; font-size:11px; color:var(--muted); margin-top:20px; max-width:720px; margin-left:auto; margin-right:auto; }

  @media print {
    :root { --bg:#fff; --card-bg:#f8f9fa; --gold:#1565c0; --text:#111; --muted:#555; --border:#ddd; }
    body { background:#fff; }
    .section { border:1px solid #ddd; break-inside:avoid; }
    .pieza-badge { background:#e8f0fe; border-color:#c5cae9; color:#1565c0; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="brand">GrupoInteligencia.com · {{area_nombre}}</div>
  <div class="title">Habilitación Ejecutivo</div>
  <div class="subtitle">{{fecha}} · Basado en pieza enviada al cliente</div>
</div>

<!-- SECCIÓN 1: QUÉ VIO EL CLIENTE -->
<div class="section">
  <div class="section-num">1 de 3</div>
  <div class="pieza-badge">Pieza cliente: {{tipo_pieza_cliente}}</div>
  <div class="section-title">¿Qué recibió el cliente hoy?</div>
  <div class="section-body">
    {{resumen_cliente}}
  </div>
</div>

<!-- SECCIÓN 2: CÓMO USARLO -->
<div class="section">
  <div class="section-num">2 de 3</div>
  <div class="section-title">¿Cómo usar esta información con tu cliente?</div>
  <div class="section-body">
    {{como_usarlo}}
  </div>
</div>

<!-- SECCIÓN 3: QUÉ HACER -->
<div class="section">
  <div class="section-num">3 de 3</div>
  <div class="section-title">¿Qué hacer ahora?</div>
  <div class="section-body">
    {{que_hacer}}
  </div>
</div>

<div class="footer">
  {{ejecutivo_firma}} · <span style="opacity:.6">{{disclaimer}}</span>
</div>

</body>
</html>
```

- [ ] **Step 2: Verificar todos los templates existen**

```powershell
"kit","folleto","apertura","semana","mirror" | ForEach-Object { Test-Path "templates/ejecutivo/$_.html" }
```

Resultado esperado: 5 líneas con `True`.

- [ ] **Step 3: Commit**

```powershell
git add templates/ejecutivo/mirror.html
git commit -m "feat(#62): template HTML mirror ejecutivo (habilitacion diaria)"
```

---

## Task 7: Comando master `/ejecutivo`

**Files:**
- Create: `.claude/commands/ejecutivo.md`

Este es el archivo más importante. Contiene las instrucciones paso a paso que Claude sigue cuando el director escribe `/ejecutivo [tipo]`.

- [ ] **Step 1: Crear `.claude/commands/ejecutivo.md`**

Usar Write con la ruta `.claude/commands/ejecutivo.md` y el siguiente contenido:

~~~markdown
Genera piezas de habilitación comercial para ejecutivos. Produce dos artefactos: `preview.html` (para prepararse y exportar PDF) y `whatsapp.txt` (para enviar al cliente por WhatsApp).

## SETUP

Lee `config/ejecutivos.json`. Usa el campo `area_activa` para obtener la configuración del área activa (nombre, firma, activos_foco, disclaimer).

Obtén la fecha y hora de Chile:
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
$fecha     = $now.ToString('yyyy-MM-dd')
$hora_slug = $now.ToString('HH-mm')
$fecha_es  = $now.ToString('d') + ' de ' + (Get-Culture).DateTimeFormat.GetMonthName($now.Month) + ' de ' + $now.Year
```

Parsea `$ARGUMENTS`:
- `kit`                    → flujo A
- `folleto [producto]`     → flujo B (producto es opcional; ver fallback)
- `apertura`               → flujo C
- `semana`                 → flujo D
- `mirror`                 → flujo E
- Sin argumentos o tipo inválido → mostrar:
  ```
  ¿Qué tipo de pieza necesitas?
  1. kit       — Kit de primer contacto (presentación + scripts)
  2. folleto   — Folleto de un producto específico
  3. apertura  — Niveles del día como oportunidades de inversión
  4. semana    — Calendario semanal con oportunidades de conversación
  5. mirror    — Versión ejecutivo de la última pieza enviada al cliente
  ```
  Esperar respuesta del director y continuar con el flujo elegido.

---

## FLUJO A — Kit de primer contacto (`/ejecutivo kit`)

Lee el template `templates/ejecutivo/kit.html`.

Genera el contenido de cada sección con lenguaje comercial (no técnico):

**Sección 1 — Presentación** (`{{seccion_presentacion}}`):
Redacta un párrafo que explique qué es Grupo Inteligencia, qué hace el área de trading y qué valor aporta al cliente. Tono: cercano, confiable, no financiero técnico. Incluye mención a la supervisión CMF.

**Sección 2 — Script no contesta** (`{{script_no_contesta}}`):
Mensaje corto (3-4 líneas) que el ejecutivo puede enviar por WhatsApp si el cliente no contestó la llamada. Tono: no intrusivo, deja la puerta abierta. Ejemplo base:
> "Hola [Nombre], te contacté del equipo de trading de Grupo Inteligencia. Tenía un dato del mercado que puede ser de tu interés. Cuando tengas un momento, con gusto te cuento. Saludos."

**Sección 3 — Script sí contesta** (`{{script_si_contesta}}`):
Guía de conversación en 3 pasos:
1. Apertura (presentación rápida, máx 2 líneas)
2. Gancho (mencionar un dato macro o movimiento reciente del activo más relevante del día, obtenido de `config/ejecutivos.json` campo `activos_foco[0]`)
3. Cierre (ofrecer envío de material + coordinar próxima conversación)

Reemplaza todas las `{{variables}}` en el template: `{{fecha}}` → `$fecha_es`, `{{area_nombre}}` → nombre del área, `{{ejecutivo_firma}}` → valor de `email_firma`, `{{disclaimer}}` → valor de `disclaimer`.

Guarda el HTML generado como `preview.html` y el TXT (script condensado de contacto) como `whatsapp.txt`.

Ruta de guardado:
```powershell
$dir = "data/mensajes/ejecutivos/$fecha/kit"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```
Guardar `preview.html` en `$dir/preview.html` y `whatsapp.txt` en `$dir/whatsapp.txt`.

Mostrar al director para aprobación:
```
━━━━━━━━━━━━━━━━━━━
📋 KIT DE PRIMER CONTACTO — [fecha_es]
━━━━━━━━━━━━━━━━━━━
[resumen de lo generado en TXT — script condensado]
━━━━━━━━━━━━━━━━━━━
✅ Artefactos listos:
   • preview.html → data/mensajes/ejecutivos/[fecha]/kit/preview.html
     (Abre en Chrome → Ctrl+P → Guardar como PDF para distribuir)
   • whatsapp.txt → data/mensajes/ejecutivos/[fecha]/kit/whatsapp.txt

¿Aprobado? ¿Ajustar algo?
```

Al aprobar: guardar ambos archivos con Write.

---

## FLUJO B — Folleto de producto (`/ejecutivo folleto [producto]`)

Lee `config/productos.json`.

**Si `productos` está vacío** (catálogo aún no definido):
```
⚠️ El catálogo de productos aún está vacío (issue pendiente).
Puedes generar el folleto ingresando los datos manualmente:

Nombre del producto:
Tipo (ej: Fondo Mutuo / APV / Renta Fija / Acciones):
Descripción breve (1 línea):
Beneficios (escribe 1 por línea, termina con línea vacía):
¿Para quién es? (perfil del cliente objetivo):
```

**Si hay productos** y se pasó nombre en `$ARGUMENTS`: buscar por nombre (case-insensitive). Si no se pasó nombre o no se encontró, mostrar lista y pedir elección.

Lee el template `templates/ejecutivo/folleto.html`. Reemplaza:
- `{{producto_nombre}}` → nombre del producto
- `{{producto_tipo}}` → tipo
- `{{producto_descripcion}}` → descripción
- `{{producto_beneficios}}` → lista HTML: cada beneficio como `<li>texto</li>`
- `{{producto_para_quien}}` → texto del perfil del cliente
- `{{fecha}}` → `$fecha_es`
- `{{area_nombre}}` → nombre del área
- `{{ejecutivo_firma}}` → valor `email_firma`
- `{{disclaimer}}` → valor `disclaimer`

Ruta de guardado:
```powershell
$slug_producto = "[nombre-producto-lowercase-sin-espacios]"
$dir = "data/mensajes/ejecutivos/$fecha/folleto-$slug_producto"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```

El `whatsapp.txt` contiene 3 bullets del producto en formato WhatsApp:
```
📄 *[Nombre del producto]*

• [Beneficio 1]
• [Beneficio 2]
• [Beneficio 3]

¿Te interesa que te cuente más? 😊
```

Mostrar para aprobación con la misma estructura del FLUJO A (adaptando el tipo a "FOLLETO · [nombre producto]").

---

## FLUJO C — Apertura ejecutivo (`/ejecutivo apertura`)

Obtén los activos del día desde `config/ejecutivos.json` campo `activos_foco`.

Para **CADA activo** en `activos_foco`, llama:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})
```

Con los datos obtenidos (precio, soportes, resistencias), genera el encuadre comercial:
- `{{activo_nombre}}` → nombre amigable del activo (consultar `config/activos.json`)
- `{{zona_entrada}}` → rango entre soporte más cercano y precio actual, en formato precio (ej: "889.60 – 895.00")
- `{{precio_actual}}` → precio actual del MCP
- `{{argumento_comercial}}` → 2-3 líneas en lenguaje novato explicando por qué es momento de conversar con clientes sobre este activo. Sin jerga técnica. Conectar con drivers de `config/drivers.json`.
- `{{clientes_objetivo}}` → tipo de cliente que tiene sentido contactar hoy (ej: "Clientes con inversiones en dólares")

Si el MCP devuelve error para un activo: omitir ese activo del HTML y anotarlo en el TXT como "⚠️ Sin datos para [activo] hoy".

Lee el template `templates/ejecutivo/apertura.html`. Construye el bloque `{{cards_activos}}` concatenando una card por activo.

Ruta de guardado: `data/mensajes/ejecutivos/$fecha/apertura/`

El `whatsapp.txt` contiene un argumento por activo, en formato:
```
📊 *Oportunidades del día — [fecha_es]*

💰 *[Activo A]*
[argumento_comercial en 2 líneas]
→ Llama a: [clientes_objetivo]

💰 *[Activo B]*
[...]
```

---

## FLUJO D — Semana ejecutivo (`/ejecutivo semana`)

Llama `mcp__market-data__obtener_calendario_macro({"min_impact": "medium"})`.

Si devuelve error: usar WebSearch como fallback (query: `investing.com calendario económico semana [fecha] Chile Estados Unidos impacto alto`).

Para cada evento del calendario, determina:
- `{{producto_relevante}}` → qué producto de banca inversiones puede conectarse con ese dato macro. Lógica:
  - Datos de empleo/inflación USA → "Acciones / Renta Fija"
  - Datos de tasas Fed/BCCh → "APV / Fondos Mutuos"
  - Datos de inventarios petróleo → mencionar solo si aplica
  - Datos de China → "Acciones internacionales"
  - Default → "Portafolio diversificado"
- `{{tipo_cliente}}` → perfil del cliente al que tiene sentido llamar ese día (ej: "Clientes conservadores", "Clientes con dólares")
- Impacto: clase CSS `impact-high` para alto (★★★), `impact-med` para medio (★★)

Construye `{{filas_semana}}` con una fila HTML por evento (ver estructura en Task 5).

Ruta de guardado: `data/mensajes/ejecutivos/$fecha/semana/`

El `whatsapp.txt`:
```
📅 *Oportunidades de la semana — [fecha_inicio] al [fecha_fin]*

[Por día:]
*[DÍA]*
• [Hora CLT] — [Evento] → Hablar de: [producto_relevante] con [tipo_cliente]
```

---

## FLUJO E — Mirror ejecutivo (`/ejecutivo mirror`)

Lee el directorio `data/mensajes/` y busca la última pieza guardada del día de hoy (la más reciente por timestamp en el nombre de archivo).

Si no hay piezas del día de hoy: mostrar
```
⚠️ No hay piezas del cliente guardadas hoy todavía.
¿Quieres que genere el mirror de ayer? (s/n)
```

Con la pieza encontrada, lee su contenido. Determina el tipo (`{{tipo_pieza_cliente}}`): niveles / dato_macro / noticia / señal / concepto / etc.

Genera las 3 secciones:
- `{{resumen_cliente}}` → resumen en 3-4 líneas de qué información recibió el cliente. Lenguaje simple.
- `{{como_usarlo}}` → 2-3 sugerencias concretas de cómo el ejecutivo puede usar esa información en una conversación de hoy. Formato de lista `<ul><li>`.
- `{{que_hacer}}` → 2-3 acciones concretas: a quién llamar, qué decir, qué enviar. Formato de lista `<ul><li>`.

Lee el template `templates/ejecutivo/mirror.html`. Reemplaza todas las `{{variables}}`.

Ruta de guardado: `data/mensajes/ejecutivos/$fecha/mirror/`

El `whatsapp.txt`:
```
🔁 *Habilitación del ejecutivo — [fecha_es]*
Pieza cliente: [tipo_pieza_cliente]

📌 Qué recibió el cliente:
[resumen en 2 líneas]

💬 Cómo usarlo:
• [sugerencia 1]
• [sugerencia 2]

✅ Qué hacer:
• [acción 1]
• [acción 2]
```

---

## REGLAS GENERALES (todos los flujos)

- Lenguaje: comercial, simple, en tuteo chileno neutro. NUNCA jerga técnica sin explicar.
- El HTML generado siempre es el contenido del template con `{{variables}}` reemplazadas — nunca inventar estructura HTML nueva.
- Al guardar: usar Write con la ruta completa. Crear el directorio antes si no existe (ver PowerShell en cada flujo).
- Siempre mostrar para aprobación antes de guardar. Al aprobar: guardar ambos archivos.
- Instrucción PDF siempre visible al mostrar para aprobación:
  `(Abre preview.html en Chrome → Ctrl+P → Guardar como PDF para distribuir al cliente)`
~~~

- [ ] **Step 2: Verificar que el comando existe**

```powershell
Test-Path .claude/commands/ejecutivo.md
```

- [ ] **Step 3: Commit**

```powershell
git add .claude/commands/ejecutivo.md
git commit -m "feat(#62): comando /ejecutivo con 5 flujos de habilitacion comercial"
```

---

## Task 8: Test funcional — flujo `kit`

No hay tests unitarios en este sistema. La validación es funcional: ejecutar el comando y verificar los artefactos.

- [ ] **Step 1: Ejecutar `/ejecutivo kit` en Claude Code**

Escribir en el prompt de Claude Code:
```
/ejecutivo kit
```

- [ ] **Step 2: Verificar que el comando no falla en el SETUP**

Claude debe leer `config/ejecutivos.json` sin errores y mostrar que cargó el área `trading`.

- [ ] **Step 3: Verificar el output antes de aprobar**

El output debe contener:
- Sección de presentación (párrafo sobre Grupo Inteligencia)
- Script "no contesta" (mensaje corto de WhatsApp)
- Script "sí contesta" (3 pasos: apertura / gancho / cierre)
- Instrucción de PDF visible

- [ ] **Step 4: Aprobar y verificar artefactos guardados**

Después de aprobar, verificar:
```powershell
$today = (Get-Date).ToString('yyyy-MM-dd')
Test-Path "data/mensajes/ejecutivos/$today/kit/preview.html"
Test-Path "data/mensajes/ejecutivos/$today/kit/whatsapp.txt"
```

Ambos deben ser `True`.

- [ ] **Step 5: Verificar el HTML abre correctamente en el navegador**

```powershell
$today = (Get-Date).ToString('yyyy-MM-dd')
Start-Process "data/mensajes/ejecutivos/$today/kit/preview.html"
```

El HTML debe renderizar con fondo oscuro, paleta dorada, tres secciones visibles. Si se imprime (Ctrl+P), debe verse con fondo blanco y texto oscuro.

---

## Task 9: Test funcional — flujo `apertura`

- [ ] **Step 1: Ejecutar `/ejecutivo apertura`**

```
/ejecutivo apertura
```

- [ ] **Step 2: Verificar que el MCP se invocó**

Claude debe haber llamado `mcp__market-data__get_asset_levels` para cada activo en `activos_foco` de `ejecutivos.json` (USDCLP, XAUUSD, WTI.spot, US100.spot).

- [ ] **Step 3: Verificar el output**

Cada activo debe mostrar:
- Nombre del activo
- Zona de entrada (rango de precios)
- Argumento comercial en lenguaje simple (sin jerga técnica)
- Tipo de cliente a contactar

- [ ] **Step 4: Aprobar y verificar artefactos**

```powershell
$today = (Get-Date).ToString('yyyy-MM-dd')
Test-Path "data/mensajes/ejecutivos/$today/apertura/preview.html"
Test-Path "data/mensajes/ejecutivos/$today/apertura/whatsapp.txt"
```

---

## Task 10: Test funcional — flujo `folleto` (modo fallback)

- [ ] **Step 1: Ejecutar `/ejecutivo folleto` con catálogo vacío**

```
/ejecutivo folleto
```

Dado que `config/productos.json` está vacío, el comando debe mostrar el formulario de entrada manual.

- [ ] **Step 2: Ingresar un producto de prueba**

Cuando el comando pregunte, ingresar:
```
Nombre del producto: Fondo Mutuo Conservador
Tipo: Fondo Mutuo
Descripción breve: Un fondo que invierte en instrumentos de renta fija para preservar capital con bajo riesgo.
Beneficios:
Capital protegido frente a la volatilidad del mercado
Liquidez en 24-48 horas hábiles
Rentabilidad mayor que una cuenta corriente

¿Para quién es? Clientes que buscan una alternativa segura al ahorro tradicional sin asumir riesgo de mercado.
```

- [ ] **Step 3: Verificar el output y los artefactos**

```powershell
$today = (Get-Date).ToString('yyyy-MM-dd')
Get-ChildItem "data/mensajes/ejecutivos/$today/" -Recurse -Filter "*.html"
```

Debe aparecer un `preview.html` en una carpeta `folleto-*`.

---

## Task 11: Test funcional — flujos `semana` y `mirror`

- [ ] **Step 1: Ejecutar `/ejecutivo semana`**

```
/ejecutivo semana
```

Verificar que el output muestra una tabla con días de la semana, eventos macro, productos relevantes y tipos de cliente.

- [ ] **Step 2: Ejecutar `/ejecutivo mirror`**

```
/ejecutivo mirror
```

Si hay piezas guardadas en `data/mensajes/` del día, debe mostrar las 3 secciones (resumen cliente / cómo usarlo / qué hacer). Si no hay piezas del día, debe preguntar si usar las de ayer.

- [ ] **Step 3: Commit final de artefactos generados (solo si se desea persistir los ejemplos)**

```powershell
git add data/mensajes/ejecutivos/
git commit -m "test(#62): artefactos de prueba generados por /ejecutivo kit y /ejecutivo apertura"
```

---

## Task 12: Cerrar issue #62

- [ ] **Step 1: Actualizar los checkboxes del issue #62 en GitHub**

Marcar todos los criterios "ready to design" como completados en el issue #62:
- [x] Catálogo de productos definido y aprobado → placeholder en `config/productos.json`
- [x] Segmentación de ejecutivos confirmada → una sola versión MVP (área trading)
- [x] Canal de entrega definido → Email (HTML + PDF via print)
- [x] Enfoque folletos validado → texto + HTML con @media print
- [x] Disclaimer CMF confirmado → incluido en `ejecutivos.json`
- [x] Timing de entrega ejecutivo vs. cliente resuelto → simultáneo
- [x] Decisión tomada → comando master `/ejecutivo [tipo]`

- [ ] **Step 2: Comentar en el issue con resumen de implementación**

Agregar comentario al issue #62 indicando que el MVP fue implementado, qué archivos se crearon, y listar los issues pendientes (catálogo productos, más áreas, métricas).

- [ ] **Step 3: Commit final**

```powershell
git add -A
git commit -m "feat(#62): implementacion completa MVP Sistema Habilitacion Comercial Ejecutivos"
```
