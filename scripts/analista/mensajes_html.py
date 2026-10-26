"""El HTML de mensajes de contexto: tres tarjetas para WhatsApp listas para copiar.

Pagina simple de un solo archivo, sin dependencias externas, legible en celular,
con boton Copiar por tarjeta (navigator.clipboard con respaldo de textarea).
El mensaje es editable y cada tarjeta trae un campo para el comentario del ejecutivo, que va entre la
noticia y la pregunta de cierre (director, 2026-10-26): Copiar arma el mensaje con lo que quedo escrito.
`data-copiar` guarda el mensaje original. Las tarjetas vacias muestran su motivo y no tienen boton.
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from analista import contexto as ctx


def _escapar_attr(texto: str) -> str:
    """Escapa texto para atributo HTML preservando saltos de linea como entidades."""
    escapado = html.escape(texto, quote=True)
    return escapado.replace("\r\n", "&#10;").replace("\r", "&#10;").replace("\n", "&#10;")


def _render_tarjeta(t: ctx.Tarjeta) -> str:
    titulo = html.escape(t.titulo, quote=True)
    if t.texto is not None:
        meta_html = ""
        if t.medio and t.fecha:
            meta_html = f'<span class="meta">{html.escape(t.medio, quote=True)} · {html.escape(t.fecha, quote=True)}</span>'
        elif t.medio:
            meta_html = f'<span class="meta">{html.escape(t.medio, quote=True)}</span>'

        enlace_html = ""
        if t.url:
            enlace_html = (
                f'<p class="enlace-nota"><a href="{html.escape(t.url, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">Ver nota original</a></p>'
            )

        texto_copiar = _escapar_attr(t.texto)
        cuerpo = html.escape(t.cuerpo or t.texto, quote=True)
        pregunta_html = ""
        if t.pregunta:
            pregunta_html = (
                f'  <label class="etiqueta">Pregunta de cierre\n'
                f'    <textarea class="campo" data-parte="pregunta" rows="2">{html.escape(t.pregunta, quote=True)}</textarea>\n'
                f'  </label>\n'
            )
        pie_html = f'  <p class="pie">{html.escape(t.pie, quote=True)}</p>\n' if t.pie else ""

        return (
            f'<article class="tarjeta" data-tarjeta="{titulo}" data-pie="{_escapar_attr(t.pie)}">\n'
            f'  <div class="tarjeta-cabecera">\n'
            f'    <h2>{titulo}</h2>\n'
            f'    {meta_html}\n'
            f'  </div>\n'
            f'  <label class="etiqueta">Mensaje\n'
            f'    <textarea class="campo" data-parte="cuerpo" rows="6">{cuerpo}</textarea>\n'
            f'  </label>\n'
            f'  <label class="etiqueta"><span>Tu comentario <span class="opcional">(opcional)</span></span>\n'
            f'    <textarea class="campo comentario" data-parte="comentario" rows="2" '
            f'placeholder="Lo que tú le dirías sobre esto. Va antes de la pregunta."></textarea>\n'
            f'  </label>\n'
            f'{pregunta_html}'
            f'{pie_html}'
            f'  {enlace_html}\n'
            f'  <div class="acciones">\n'
            f'    <button type="button" class="btn-original" onclick="restablecer(this)">Volver al original</button>\n'
            f'    <button type="button" class="btn-copiar" data-copiar="{texto_copiar}" onclick="copiarTexto(this)">Copiar</button>\n'
            f'  </div>\n'
            f'</article>'
        )
    else:
        motivo = html.escape(t.motivo or "Sin información disponible.", quote=True)
        return (
            f'<article class="tarjeta vacia" data-tarjeta="{titulo}">\n'
            f'  <div class="tarjeta-cabecera">\n'
            f'    <h2>{titulo}</h2>\n'
            f'  </div>\n'
            f'  <div class="motivo">{motivo}</div>\n'
            f'</article>'
        )


def render(pieza: dict[str, Any], saludo: str = "") -> str:
    """Genera el HTML autosuficiente con tres tarjetas de mensajes de contexto."""
    datos = pieza.get("datos", {})
    ticker = datos.get("ticker", "")
    nombre = datos.get("nombre", ticker)

    titulo_pagina = f"Mensajes de contexto: {nombre}" if nombre else "Mensajes de contexto"
    if ticker and ticker != nombre:
        titulo_pagina += f" ({ticker})"

    tarjetas_lista = ctx.tarjetas(pieza, saludo=saludo)
    bloques_tarjetas = "\n".join(_render_tarjeta(t) for t in tarjetas_lista)

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(titulo_pagina, quote=True)}</title>
  <style>
    :root {{
      --fondo: #000000;
      --fondo-alt: #0A0A0F;
      --fondo-tarjeta: #0E2420;
      --fondo-vacia: #121A18;
      --acento: #50C0A8;
      --acento-hover: #3C8CAA;
      --acento-oscuro: #143028;
      --linea: #1E2D2A;
      --texto-1: #FFFFFF;
      --texto-2: #8E9E9B;
      --aviso: #FFB020;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--fondo);
      color: var(--texto-1);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 15px;
      line-height: 1.5;
      padding: 16px;
    }}
    main {{
      max-width: 600px;
      margin: 0 auto;
    }}
    header.cabecera {{
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--linea);
    }}
    header.cabecera h1 {{
      font-size: 18px;
      font-weight: 700;
      color: var(--acento);
      letter-spacing: 0.5px;
    }}
    header.cabecera p {{
      font-size: 13px;
      color: var(--texto-2);
      margin-top: 4px;
    }}
    .tarjeta {{
      background: var(--fondo-tarjeta);
      border: 1px solid var(--linea);
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}
    .tarjeta.vacia {{
      background: var(--fondo-vacia);
      border-style: dashed;
    }}
    .tarjeta-cabecera {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 8px;
    }}
    .tarjeta-cabecera h2 {{
      font-size: 16px;
      font-weight: 700;
      color: var(--texto-1);
    }}
    .tarjeta-cabecera .meta {{
      font-size: 12px;
      color: var(--texto-2);
      font-weight: 500;
    }}
    .etiqueta {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: var(--texto-2);
    }}
    .opcional {{
      font-weight: 400;
    }}
    .campo {{
      width: 100%;
      background: rgba(0, 0, 0, 0.25);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      padding: 12px;
      font-family: inherit;
      font-size: 16px;
      line-height: 1.5;
      color: var(--texto-1);
      resize: vertical;
      overflow: hidden;
    }}
    .campo:focus {{
      outline: none;
      border-color: var(--acento);
    }}
    .campo.comentario {{
      border-style: dashed;
    }}
    .campo::placeholder {{
      color: var(--texto-2);
    }}
    .pie {{
      font-size: 13px;
      color: var(--texto-2);
    }}
    .enlace-nota {{
      font-size: 13px;
    }}
    .enlace-nota a {{
      color: var(--acento);
      text-decoration: none;
      font-weight: 600;
    }}
    .enlace-nota a:hover {{
      text-decoration: underline;
    }}
    .motivo {{
      font-size: 14px;
      color: var(--aviso);
      padding: 8px 0;
    }}
    .acciones {{
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 12px;
    }}
    .btn-original {{
      background: none;
      border: 0;
      color: var(--texto-2);
      font-family: inherit;
      font-size: 13px;
      text-decoration: underline;
      cursor: pointer;
      min-height: 42px;
    }}
    .btn-copiar {{
      background: var(--acento);
      color: var(--fondo);
      border: 0;
      border-radius: 8px;
      padding: 10px 18px;
      font-family: inherit;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.15s ease;
      min-height: 42px;
      min-width: 90px;
    }}
    .btn-copiar:hover {{
      background: var(--acento-hover);
    }}
    .btn-copiar.copiado {{
      background: var(--acento-oscuro);
      color: var(--acento);
    }}
  </style>
</head>
<body>
  <main>
    <header class="cabecera">
      <h1>{html.escape(titulo_pagina, quote=True)}</h1>
      <p>Ajusta el mensaje si quieres, agrega tu comentario sobre la noticia y cópialo para abrir conversación con tu cliente.</p>
      <p class="nota-independientes">Cada mensaje se sostiene solo. La noticia y el análisis técnico pueden apuntar a lados distintos: es normal, porque uno cuenta lo que pasó y el otro lo que muestra el precio. Si los mandas juntos, preséntalos como dos miradas.</p>
    </header>
    {bloques_tarjetas}
  </main>
  <script>
    // El mensaje que se copia: el cuerpo, el comentario del ejecutivo y la pregunta de cierre, y al final la fuente.
    function armar(tarjeta) {{
      function parte(nombre) {{
        var campo = tarjeta.querySelector('[data-parte="' + nombre + '"]');
        return campo ? campo.value.trim() : '';
      }}
      var cuerpo = parte('cuerpo'), comentario = parte('comentario'), pregunta = parte('pregunta');
      var texto = comentario
        ? [cuerpo, comentario, pregunta].filter(Boolean).join('\\n\\n')
        : [cuerpo, pregunta].filter(Boolean).join(' ');
      var pie = tarjeta.dataset.pie || '';
      return pie ? texto + '\\n\\n' + pie : texto;
    }}
    function clave(campo) {{
      var tarjeta = campo.closest('.tarjeta');
      return 'gi-contexto|' + location.pathname + '|' + tarjeta.dataset.tarjeta + '|' +
        campo.getAttribute('data-parte') + '|' + campo.defaultValue.length;
    }}
    function ajustar(campo) {{
      campo.style.height = 'auto';
      campo.style.height = campo.scrollHeight + 2 + 'px';
    }}
    function restablecer(btn) {{
      var campos = btn.closest('.tarjeta').querySelectorAll('.campo');
      Array.prototype.forEach.call(campos, function(campo) {{
        campo.value = campo.defaultValue;
        try {{ localStorage.removeItem(clave(campo)); }} catch (e) {{}}
        ajustar(campo);
      }});
    }}
    document.addEventListener('DOMContentLoaded', function() {{
      Array.prototype.forEach.call(document.querySelectorAll('.campo'), function(campo) {{
        try {{
          var guardado = localStorage.getItem(clave(campo));
          if (guardado !== null) campo.value = guardado;
        }} catch (e) {{}}
        ajustar(campo);
        campo.addEventListener('input', function() {{
          ajustar(campo);
          try {{ localStorage.setItem(clave(campo), campo.value); }} catch (e) {{}}
        }});
      }});
    }});
    function copiarTexto(btn) {{
      var tarjeta = btn.closest('.tarjeta');
      var texto = tarjeta && tarjeta.querySelector('.campo') ? armar(tarjeta) : (btn.getAttribute('data-copiar') || '');
      function exito() {{
        var orig = btn.textContent;
        btn.textContent = 'Copiado';
        btn.classList.add('copiado');
        setTimeout(function() {{
          btn.textContent = orig;
          btn.classList.remove('copiado');
        }}, 2000);
      }}
      if (navigator.clipboard && navigator.clipboard.writeText) {{
        navigator.clipboard.writeText(texto).then(exito).catch(function() {{
          copiarRespaldo(texto, exito);
        }});
      }} else {{
        copiarRespaldo(texto, exito);
      }}
    }}
    function copiarRespaldo(texto, cb) {{
      var ta = document.createElement('textarea');
      ta.value = texto;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      ta.style.top = '0';
      ta.setAttribute('readonly', '');
      document.body.appendChild(ta);
      ta.select();
      try {{
        document.execCommand('copy');
        if (cb) cb();
      }} catch (e) {{}}
      document.body.removeChild(ta);
    }}
  </script>
</body>
</html>
"""


def guardar(pieza: dict[str, Any], dir_pedido: Path, saludo: str = "") -> Path:
    """Escribe dir_pedido / 'mensajes.html' en UTF-8 y devuelve su ruta."""
    dir_pedido.mkdir(parents=True, exist_ok=True)
    ruta = dir_pedido / "mensajes.html"
    contenido = render(pieza, saludo=saludo)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta
