"""Panel HTML del uso del bot de analistas: quién pide qué, cuándo y cómo le fue.

    uv run python scripts/uso_bot.py            # escribe data/uso_bot.html
    uv run python scripts/uso_bot.py --abrir    # y lo abre en el navegador

Lee `data/uso_bot.jsonl` (lo escribe el bot) y, para lo anterior a esa bitácora, rescata los pedidos del
log viejo. Los nombres salen de `config/analistas_telegram.json` al generar el panel.
Es un archivo único sin servidor ni red: se regenera cuando se quiere mirar.
"""
from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from analista import uso  # noqa: E402

CONFIG = RAIZ / "config" / "analistas_telegram.json"
SALIDA = RAIZ / "data" / "uso_bot.html"


def equipo(config_ruta: Path = CONFIG) -> dict[str, dict]:
    """Los usuarios autorizados con su nombre; sin config el panel igual sale, con los ids a la vista."""
    try:
        datos = json.loads(config_ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {
        str(uid): {"nombre": a.get("nombre") or str(uid), "cargo": a.get("cargo", ""), "rol": a.get("rol", ""),
                   "cupo": a.get("cupo_diario")}
        for uid, a in (datos.get("analistas") or {}).items()
    }


def armar(eventos: list[dict], usuarios: dict[str, dict], ahora: datetime | None = None) -> str:
    ahora = ahora or datetime.now(uso.SANTIAGO)
    datos = {"generado": ahora.strftime("%Y-%m-%d %H:%M"), "hoy": ahora.strftime("%Y-%m-%d"),
             "usuarios": usuarios, "eventos": eventos}
    # `</` dentro de un <script> cierra la etiqueta antes de tiempo: el texto de un usuario podría traerlo.
    blob = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    return PLANTILLA.replace("__DATOS__", blob)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--abrir", action="store_true", help="abre el panel en el navegador")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    args = ap.parse_args()
    ids = set(equipo())
    # el log viejo guarda también pedidos de pruebas (ids 111, 222): solo cuenta quien está en el config
    eventos = [e for e in uso.todos() if e["usuario"] in ids or e.get("clase") == "no_autorizado"]
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(armar(eventos, equipo()), encoding="utf-8")
    print(f"Panel escrito en {args.salida} ({len(eventos)} eventos)")
    if args.abrir:
        webbrowser.open(args.salida.as_uri())


PLANTILLA = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Uso del bot</title>
<style>
:root{--fondo:#f6f7f9;--tarjeta:#fff;--texto:#1b2430;--suave:#667085;--borde:#e2e6ec;--acento:#1f9e86;--mal:#c0392b;--aviso:#b7791f;--ok:#1f9e86}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--fondo:#12171d;--tarjeta:#1b222b;--texto:#e8edf2;--suave:#9aa6b2;--borde:#2c3642;--acento:#3fc3a8;--mal:#ef6b5b;--aviso:#e0a84a;--ok:#3fc3a8}}
:root[data-theme="dark"]{--fondo:#12171d;--tarjeta:#1b222b;--texto:#e8edf2;--suave:#9aa6b2;--borde:#2c3642;--acento:#3fc3a8;--mal:#ef6b5b;--aviso:#e0a84a;--ok:#3fc3a8}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 48px}
header{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;justify-content:space-between;margin-bottom:16px}
h1{font-size:22px;margin:0}
h2{font-size:16px;margin:28px 0 10px}
.suave{color:var(--suave);font-size:13px}
.filtros{display:flex;gap:6px;flex-wrap:wrap}
button.f{border:1px solid var(--borde);background:var(--tarjeta);color:var(--texto);padding:6px 12px;border-radius:999px;cursor:pointer;font:inherit;font-size:13px}
button.f[aria-pressed="true"]{background:var(--acento);border-color:var(--acento);color:#fff}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.kpi,.tarjeta{background:var(--tarjeta);border:1px solid var(--borde);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:26px;line-height:1.1}
table{width:100%;border-collapse:collapse;background:var(--tarjeta);border:1px solid var(--borde);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--borde);font-size:14px;vertical-align:top}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--suave)}
tr:last-child td{border-bottom:0}
tr.fila{cursor:pointer}
tr.fila:hover,tr.fila.sel{background:color-mix(in srgb,var(--acento) 10%,transparent)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.tabla-scroll{overflow-x:auto}
.etq{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--borde);color:var(--suave)}
.ok{color:var(--ok)}.mal{color:var(--mal)}.aviso{color:var(--aviso)}
.barra{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:13px}
.barra i{display:block;height:10px;background:var(--acento);border-radius:3px;min-width:2px}
.barra span:first-child{width:110px;flex:none;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.horas{display:grid;grid-template-columns:repeat(24,1fr);gap:2px;align-items:end;height:60px}
.horas div{background:var(--acento);border-radius:2px 2px 0 0;min-height:2px}
.rejilla{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}
.vacio{padding:18px;text-align:center;color:var(--suave)}
@media (max-width:600px){th:nth-child(n+6),td:nth-child(n+6){display:none}}
</style>
</head>
<body>
<main>
<header>
  <div><h1>Uso del bot</h1><div class="suave" id="meta"></div></div>
  <div class="filtros" id="filtros" role="group" aria-label="Período"></div>
</header>
<div class="kpis" id="kpis"></div>
<h2>Por persona <span class="suave">(toca una fila para ver su detalle)</span></h2>
<div class="tabla-scroll"><table id="personas"></table></div>
<div id="detalle"></div>
<h2>Intentos de personas no autorizadas</h2>
<div class="tabla-scroll"><table id="extranos"></table></div>
</main>
<script id="datos" type="application/json">__DATOS__</script>
<script>
const D = JSON.parse(document.getElementById('datos').textContent);
const PERIODOS = [['hoy','Hoy',0],['7d','7 días',6],['30d','30 días',29],['todo','Todo',null]];
let periodo = '7d', elegido = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dia = e => e.ts.slice(0,10), hora = e => e.ts.slice(11,16);

function desde(){
  const dias = PERIODOS.find(p => p[0] === periodo)[2];
  if (dias === null) return '0000-00-00';
  const d = new Date(D.hoy + 'T12:00:00'); d.setDate(d.getDate() - dias);
  return d.toISOString().slice(0,10);
}
const nombre = id => (D.usuarios[id] || {}).nombre || ('Usuario ' + id);
const fmtFecha = e => e ? (dia(e) === D.hoy ? 'hoy ' : dia(e).slice(5).split('-').reverse().join('/') + ' ') + hora(e) : '—';
const cuenta = (lista, f) => { const m = {}; lista.forEach(x => { const k = f(x); if (k) m[k] = (m[k]||0)+1; }); return Object.entries(m).sort((a,b)=>b[1]-a[1]); };

function resumen(evs){
  const m = evs.filter(e => e.tipo === 'mensaje'), r = evs.filter(e => e.tipo === 'resultado');
  return {
    mensajes: m.length,
    pedidos: m.filter(e => e.clase === 'pedido').length,
    comandos: m.filter(e => e.clase === 'comando').length,
    ruido: m.filter(e => e.clase === 'no_entendido').length,
    botones: evs.filter(e => e.tipo === 'boton').length,
    fallos: r.filter(e => e.resultado !== 'ok').length,
    entregados: r.filter(e => e.resultado === 'ok').length,
    seg: r.filter(e => e.segundos != null).map(e => e.segundos),
    ultimo: evs.length ? evs[evs.length-1] : null,
  };
}

function barras(pares, max=8){
  if (!pares.length) return '<div class="suave">Sin datos</div>';
  const tope = pares[0][1];
  return pares.slice(0,max).map(([k,n]) => `<div class="barra"><span title="${esc(k)}">${esc(k)}</span><i style="width:${Math.round(n/tope*100)}%"></i><span>${n}</span></div>`).join('');
}

function pintar(){
  const corte = desde();
  const evs = D.eventos.filter(e => dia(e) >= corte);
  const autorizados = evs.filter(e => D.usuarios[e.usuario]);
  $('meta').textContent = 'Generado ' + D.generado + ' (hora de Chile). Eventos en el período: ' + evs.length;
  $('filtros').innerHTML = PERIODOS.map(p => `<button class="f" data-p="${p[0]}" aria-pressed="${p[0]===periodo}">${p[1]}</button>`).join('');
  $('filtros').querySelectorAll('button').forEach(b => b.onclick = () => { periodo = b.dataset.p; pintar(); });

  const t = resumen(autorizados), activos = new Set(autorizados.map(e => e.usuario)).size;
  const med = t.seg.length ? Math.round(t.seg.reduce((a,b)=>a+b,0)/t.seg.length) : null;
  $('kpis').innerHTML = [
    [activos + ' de ' + Object.keys(D.usuarios).length, 'personas activas'],
    [t.pedidos, 'pedidos de piezas'], [t.comandos, 'comandos y consultas'], [t.botones, 'toques de botones'],
    [t.fallos, 'pedidos con fallo'], [med === null ? '—' : med + ' s', 'tiempo medio por pedido']
  ].map(([n,l]) => `<div class="kpi"><b>${esc(n)}</b><span class="suave">${l}</span></div>`).join('');

  const ids = Object.keys(D.usuarios);
  const filas = ids.map(id => ({id, r: resumen(evs.filter(e => e.usuario === id))})).sort((a,b) => b.r.pedidos - a.r.pedidos || b.r.mensajes - a.r.mensajes);
  $('personas').innerHTML = '<thead><tr><th>Persona</th><th>Rol</th><th class="num">Pedidos</th><th class="num">Comandos</th><th class="num">Botones</th><th class="num">Fallos</th><th>Último movimiento</th></tr></thead><tbody>' +
    filas.map(({id,r}) => { const u = D.usuarios[id];
      return `<tr class="fila ${id===elegido?'sel':''}" data-id="${esc(id)}"><td><b>${esc(u.nombre)}</b><div class="suave">${esc(u.cargo)}</div></td><td><span class="etq">${esc(u.rol||'—')}</span></td><td class="num">${r.pedidos}</td><td class="num">${r.comandos}</td><td class="num">${r.botones}</td><td class="num ${r.fallos?'mal':''}">${r.fallos}</td><td>${fmtFecha(r.ultimo)}</td></tr>`; }).join('') + '</tbody>';
  $('personas').querySelectorAll('tr.fila').forEach(tr => tr.onclick = () => { elegido = elegido === tr.dataset.id ? null : tr.dataset.id; pintar(); });

  detalle(evs);

  const ext = evs.filter(e => e.clase === 'no_autorizado');
  $('extranos').innerHTML = ext.length
    ? '<thead><tr><th>Cuándo</th><th>Número de usuario</th><th>Escribió</th></tr></thead><tbody>' + ext.slice().reverse().slice(0, 30).map(e => `<tr><td>${fmtFecha(e)}</td><td>${esc(e.usuario)}</td><td>${esc(e.texto)}</td></tr>`).join('') + (ext.length > 30 ? `<tr><td colspan="3" class="suave">Se muestran los 30 más recientes de ${ext.length}.</td></tr>` : '') + '</tbody>'
    : '<tbody><tr><td class="vacio">Nadie sin autorización escribió en este período.</td></tr></tbody>';
}

function detalle(evs){
  const cont = $('detalle');
  if (!elegido) { cont.innerHTML = ''; return; }
  const mios = evs.filter(e => e.usuario === elegido), r = resumen(mios), u = D.usuarios[elegido];
  const pedidos = mios.filter(e => e.tipo === 'mensaje' && e.clase === 'pedido');
  const horas = Array(24).fill(0); mios.filter(e => e.tipo === 'mensaje').forEach(e => horas[+hora(e).slice(0,2)]++);
  const topeH = Math.max(1, ...horas);
  const porDia = cuenta(mios.filter(e => e.tipo === 'mensaje'), e => dia(e)).sort((a,b) => a[0] < b[0] ? 1 : -1);
  const lineas = mios.slice().reverse().slice(0, 80).map(e => {
    let que, estado = '';
    if (e.tipo === 'mensaje') { que = (e.pieza ? '/' + e.pieza + (e.ticker ? ' ' + e.ticker : '') : (e.texto || '')); estado = `<span class="etq">${esc({pedido:'pedido',comando:'comando',no_entendido:'no entendido',no_autorizado:'no autorizado'}[e.clase] || e.clase)}</span>`; }
    else if (e.tipo === 'boton') { que = 'botón «' + e.accion + '» de un aviso'; estado = '<span class="etq">botón</span>'; }
    else { que = 'respuesta: ' + e.pieza + (e.ticker ? ' ' + e.ticker : ''); estado = e.resultado === 'ok' ? `<span class="ok">entregado${e.segundos!=null?' en '+e.segundos+' s':''}</span>` : `<span class="mal">${esc(e.resultado)}${e.detalle?': '+esc(e.detalle):''}</span>`; }
    return `<tr><td>${fmtFecha(e)}</td><td>${esc(que)}</td><td>${estado}</td></tr>`;
  }).join('');
  cont.innerHTML = `<h2>${esc(u.nombre)} <span class="suave">${esc(u.cargo)}${u.cupo?' · cupo diario ' + u.cupo:''}</span></h2>
  <div class="rejilla">
    <div class="tarjeta"><b>Activos más pedidos</b>${barras(cuenta(pedidos, e => e.ticker && e.ticker.toUpperCase()))}</div>
    <div class="tarjeta"><b>Qué pide</b>${barras(cuenta(mios.filter(e=>e.tipo==='mensaje'), e => e.pieza || (e.clase === 'no_entendido' ? 'no entendido' : null)))}</div>
    <div class="tarjeta"><b>Hora del día (Chile)</b><div class="horas">${horas.map((n,h) => `<div title="${h}:00 — ${n}" style="height:${Math.round(n/topeH*100)}%"></div>`).join('')}</div><div class="suave" style="display:flex;justify-content:space-between"><span>0h</span><span>12h</span><span>23h</span></div></div>
    <div class="tarjeta"><b>Mensajes por día</b>${barras(porDia, 7)}</div>
  </div>
  <h2>Línea de tiempo <span class="suave">(últimos 80 eventos)</span></h2>
  <div class="tabla-scroll"><table><thead><tr><th>Cuándo</th><th>Qué</th><th>Estado</th></tr></thead><tbody>${lineas || '<tr><td class="vacio" colspan="3">Sin movimiento en este período.</td></tr>'}</tbody></table></div>`;
}
pintar();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
