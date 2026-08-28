# El Truco de Magia de Grupo Inteligencia (Taste Primer)

> *Documento sagrado de criterio estético y editorial. Representa los instintos de la marca, no solo sus especificaciones técnicas.*

---

## 1. El ADN Visual
- **Elegancia de Terminal Cuantitativo**: No somos una fintech colorida de consumo ni un canal de señales de Telegram. El aspecto visual evoca una estación Bloomberg futurista o un centro de comando macroeconómico.
- **Dark Emerald Glass**: Los contenedores y tarjetas flotan sobre el fondo con un tratamiento de cristal esmeralda ultra-oscuro (`rgba(8, 20, 24, 0.75)`, `backdrop-filter: blur(28px)`), con biseles reflectivos superiores tenues (`rgba(80, 192, 168, 0.40)`).
- **Fotografía Real Cinematográfica + Sombra Asimétrica**: En piezas visuales (16:9), la fotografía macroscópica de activos reales (lingotes de oro, barriles, chips, terminales) ocupa el 100% del fondo, degradándose con una sombra asimétrica direccional suave que garantiza legibilidad radical sin necesidad de cajas opacas.
- **Tipografía**:
  - **Goldman 700**: Reservada para titulares de impacto, cifras clave gigantes, sellos de estado (`ALERTA DE MERCADO`, `ÚLTIMA HORA`) y la firma `GRUPO INTELIGENCIA`.
  - **Plus Jakarta Sans (400/600/700)**: Para todo el cuerpo de texto, párrafos de contexto, chips, tablas macro y disclaimers.
- **Norma de Formatos de Canvas (Horizontal 16:9 vs Vertical 9:16)**:
  - **Horizontal 16:9 (`1920×1080`)**: Exclusivo para **Alertas Técnicas y piezas con gráficos MT5**, donde la serie temporal de velas y los niveles de soporte/resistencia exigen amplitud horizontal.
  - **Vertical 9:16 (`1080×1920`)**: **Obligatorio para toda imagen con carga textual y sin gráfico técnico** (calendarios, agendas, guías pedagógicas, conceptos didácticos y breaking news). En vertical, se maximiza el aprovechamiento del ancho (márgenes estrechos de ~44px) y se calibra la fuente a escala grande (titulares 64px, tarjetas 38px, cuerpo 28-32px en peso 600/700) para garantizar lectura natural en celular sin zoom.

---

## 2. El ADN Verbal
- **Voz Novata pero Rigurosa**: Explicamos fenómenos macroeconómicos e intermercado complejos con claridad absoluta y sin jerga pretenciosa, pero con precisión técnica y rigor matemático.
- **Cero Promesas de Ganancia**: Nunca se promete rentabilidad, nunca se habla de "ganar dinero fácil", ni se usa lenguaje de casino ("apuesta", "disparo seguro").
- **Enfoque en Escenarios y Gestión de Riesgo**: Las piezas señalan desequilibrios de precios, niveles técnicos (soportes/resistencias) y veredictos macro frente a consensos oficiales, dejando siempre explícito que el control de riesgo y la volatilidad mandan.
- **Titulares Activos**: Estructura directa `[Sujeto] + [Verbo de Acción] + [Impacto/Zona Clave]`.

---

## 3. Prohibiciones Visuales Absolutas (Anti-Patrones de Marca)
- **Cero Gráficos Mock o SVGs Manuales**: Queda estrictamente prohibido dibujar curvas o vectores de precios "a mano", inventar polilíneas simplificadas de pocos puntos o incrustar SVGs aproximados en scripts ad-hoc.
- **Obligatoriedad del Pipeline Canónico de Gráficos**: Todo gráfico técnico de mercado DEBE generarse obligatoriamente mediante la cadena oficial: `serie_mt5.py` (60 velas H1 de alta densidad) ➔ `story_grafico.py` (motor geométrico y anti-colisión) ➔ `story_render.py`.
- **Prohibición de Templates HTML Inline Improvisados**: Jamás se debe renderizar una pieza de mercado usando HTML temporal escrito a mano dentro de un script si ya existe la plantilla oficial en `templates/stories/` (`alerta.html`, `calendario.html`, `dato_macro.html`, `breaking.html`).
- **Integridad de Cromo y Fidelidad Visual**: Todo gráfico debe conservar sus clases de alta fidelidad (`.g-linea`, `.g-area`, `.g-punto`, `.g-halo`, `.g-nivel`), las transparencias Dark Emerald y el biselado reflectivo del snapshot oficial.

---

## 4. Principio de Accesibilidad y Ultra-Legibilidad Universal (Low-Vision Friendly)
- **Diseño Amigable para Dificultades de Visión (Miopía / Presbicia / Cortos de Vista)**: Toda pieza visual de Grupo Inteligencia DEBE ser legible de forma inmediata y cómoda por cualquier persona sin forzar la vista, sin entrecerrar los ojos y sin requerir zoom en celulares o pantallas secundarias.
- **Escala Tipográfica Gigante y Contrastada**:
  - **Piezas Horizontales (16:9)**: Titulares en Goldman 700 a **46px+**, cuerpos de texto a **24px+** (peso semi-bold 600), precios principales a **68px+**, valores de soporte/resistencia a **28px+**, y etiquetas dentro del gráfico a **26px+** con contorno protector grueso (`stroke-width: 5px`).
  - **Piezas Verticales (9:16)**: Titulares a **64px+**, tarjetas a **38px+**, cuerpos explicativos a **28px - 32px** (peso 600/700) y aprovechamiento máximo del ancho de pantalla (~44px márgenes).
- **Prohibición de Micro-Texto y Trazos Finos**:
  - Queda terminantemente prohibido el uso de tamaños menores a 15px en badges/labels y menores a 24px en párrafos.
  - Queda prohibido el uso de pesos ligeros (font-weight 300/400) en textos de lectura sobre fondo oscuro.
- **Luminosidad y Contraste de Datos**:
  - Todo dato numérico clave debe contrastar en blanco puro (`#FFFFFF`) o colores de estado de alta luminosidad (`#00DC82` verde, `#E84040` rojo, `#50C0A8` esmeralda), y los trazados de gráficos deben usar líneas gruesas (`stroke-width: 3.2px - 4.5px`) para garantizar visibilidad instantánea.

