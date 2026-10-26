// La simulación del panel. Es la MISMA que `simular` de Python (módulo del análisis semanal): un test corre este
// archivo con node y compara. Si cambias una, cambia la otra.
var MULTIPLO = 3;
function _pct(valor, capital) {
  return capital > 0 ? Math.round(valor / capital * 10000) / 100 : null;
}
function simular(c, e, perdida, capital) {
  if (perdida === null || perdida === undefined || !(perdida > 0)) return null;
  var riesgo = Math.abs(Number(e.entrada) - Number(e.stop));
  var clp = Number(c.clp_unidad), minimo = Number(c.vol_min), paso = Number(c.vol_paso);
  if (!(riesgo > 0) || !(clp > 0)) return null;
  var crudo = perdida / (riesgo * clp);
  var bajo = crudo < minimo;
  var vol = bajo ? minimo
    : Math.round((minimo + Math.floor((crudo - minimo) / paso + 1e-9) * paso) * 1e8) / 1e8;
  var p = Math.round(riesgo * clp * vol);
  var g = MULTIPLO * p;
  return {volumen: vol, perdida: p, ganancia: g, bajo_minimo: bajo,
          perdida_pct: _pct(p, capital), ganancia_pct: _pct(g, capital)};
}
function volumenTexto(s) {
  if (!s) return '';
  var coma = function(n) { return String(n).replace('.', ','); };
  return 'Volumen: ' + coma(s.volumen) + ' lotes' + (s.bajo_minimo ? ': es el mínimo que permite el broker.' : '.');
}
