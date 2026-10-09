# Informe del analista: general, firmado y con plan de escenarios

Fecha: 2026-10-08. Extiende `2026-10-08-bot-telegram-analistas-design.md`.

## Por qué

1. **El informe se parece demasiado a WhatsApp.** Sale del mismo payload (soporte, resistencia,
   tres escenarios) y agy solo lo redacta más largo. Para que el analista tenga algo que el canal
   no tiene, el informe suma un **plan de escenarios condicionado** con base estadística medida.
2. **Nadie en GI está inscrito como asesor de inversión.** La línea que no se cruza es la
   recomendación personalizada. La versión "Preparado para <trader>" era el elemento que más
   acercaba un análisis general a eso, y con un plan encima el riesgo crecía. Se elimina.
3. **El informe lo firma el director**, con su credencial dicha con exactitud y verificable.
   No se menciona a la CMF en ninguna parte (decisión del director).

## 1. Fuera la personalización

- `orden.py`: desaparece `para <trader>`. Si un pedido lo trae, el bot responde
  "Los informes ya no se personalizan: es un análisis general que puedes compartir tal cual."
  y no lo atiende (no lo ignora en silencio).
- `Orden` pierde `trader`; `clave_base()` queda como la clave del pedido.
- `informe_html`: fuera la barra de personalización, su script, `TRADER_GENERICO` y la
  segunda copia. **Un solo HTML por pedido.** La barra queda solo con "Imprimir o PDF".
- `bot.py`: la respuesta entrega un archivo; el reuso sigue por pieza base.
- Tests: se borran los de la versión dedicada y se agrega uno de contrato: ni el paquete ni la
  plantilla contienen `trader`, `Preparado para` ni `Asesor asignado`.

## 2. La franja

| Rótulo | Valor |
|---|---|
| Análisis | Benjamín Ignacio Bravo Soza |
| Compartido por | nombre del analista que pidió la pieza (del config de usuarios) |
| Cotización | hora de la lectura del terminal |
| Edición | fecha |

"Compartido por" no personaliza nada para el cliente: registra quién distribuyó el informe.

## 3. Bloque de firma

Al cierre del cuerpo, antes del pie legal:

- Foto circular de 2,5 cm (incrustada en base64).
- Firma escaneada, si existe; sin ella el bloque sale igual, sin hueco.
- **Benjamín Ignacio Bravo Soza** · Director de Análisis Técnico · Grupo Inteligencia
- Acreditación CMV · Categoría Operadores · N° A-32915 · Vigente hasta el 31-03-2028
- Verificable en `https://cmvsystem.cmvchile.cl/certificados/635409A1A002` (enlace)
- Frase fija: *"Análisis general de mercado, idéntico para todos sus destinatarios. No es
  asesoría de inversión ni considera el perfil de quien lo lee."*

Todo sale de un bloque `autor` en `config/analistas_telegram.json` (gitignoreado; el
`.example` versionado lleva marcadores):

```json
"autor": {
  "nombre": "Benjamín Ignacio Bravo Soza",
  "cargo": "Director de Análisis Técnico",
  "foto": "config/autor/foto.png",
  "firma": null,
  "acreditacion": {
    "entidad": "CMV", "categoria": "Operadores", "numero": "A-32915",
    "vigente_hasta": "2028-03-31",
    "url": "https://cmvsystem.cmvchile.cl/certificados/635409A1A002"
  }
}
```

Reglas:
- **Vencida la acreditación, no se imprime** y el bot avisa al director en cada pedido. Una
  credencial vencida en un informe es peor que ninguna.
- **Sin `autor` en el config, el bot no arranca**: un informe sin firma no es el producto.
- Foto o firma declaradas y ausentes en disco: el informe sale sin ellas y el bot lo avisa
  (mismo criterio que una imagen faltante: se dice, no se rellena).
- `config/autor/` va gitignoreado: son datos personales.
- Prohibido usar fotos generadas o retocadas con IA (Regla 0 y credibilidad de la firma).

## 4. Plan de escenarios (solo `/activo` en v1)

Sección nueva, **escrita por Python y no por agy**, después de la lectura técnica.

| Elemento | Contenido | Fuente |
|---|---|---|
| Sesgo | Alcista o bajista | `direccion_tecnica` (precio contra EMA 50), la misma del chip |
| Gatillo | "El escenario alcista se activa con un cierre de vela de 1 hora sobre R1" (espejo para el bajista con S1) | `s1/r1` del payload; si el nivel es de respaldo ATR (`niveles_origen = atr`), no hay plan: se dice que el activo no tiene estructura medible hoy |
| Invalidación | "El escenario se anula bajo X" | Chandelier N=22, k=3,0 sobre H1, doctrina de salida del director |
| Recorrido típico | "1,5 veces la volatilidad de una hora: X" y si cabe en el ATR diario restante | Modelo ADC+ATR, mismos campos del payload |
| Base estadística | ver abajo | Serie H1 del terminal |
| Estado | Armado / activado / invalidado, con hora | Última vela H1 cerrada |

Solo se arma el plan **a favor del sesgo**. El escenario contrario queda en los tres
escenarios que ya trae la pieza.

**Sin objetivo fijo (TP), a propósito.** Lo medido en septiembre: ningún objetivo fijo tuvo
expectativa positiva en 236 señales; el Chandelier dio +0,28 R. El recorrido típico es una
distancia de referencia, no un objetivo.

### Base estadística

Módulo nuevo `scripts/analista/estadistica.py`, puro (recibe un DataFrame H1, no lee nada).

- **Serie:** las últimas 10.000 velas H1 del terminal para ese símbolo (`copy_rates`), así
  cubre todo el catálogo y no solo los seis activos de `data central/`.
- **Niveles históricos:** en cada vela se recalculan S1/R1 con **la misma función de
  producción** (`_get_support_resistance` sobre la ventana de 300 velas previas), sin mirar el
  futuro. Una sola definición de nivel para el plan y su estadística.
- **Evento:** primer cierre H1 sobre R1 (alcista) con el cierre sobre la EMA 50, y R1 de origen
  `swing`. Un nivel cuenta una vez: no se repite el evento mientras R1 no cambie.
- **Desenlace en las 24 velas siguientes:**
  - recorrido: el máximo alcanza `cierre + 1,5 × ATR14`,
  - invalidación: el mínimo toca el Chandelier,
  - si ambos ocurren en la misma vela, cuenta como invalidación (supuesto conservador),
  - ninguno: "sin definición".
- **La comparación contra el azar es obligatoria.** Con una invalidación a 3 ATR y un
  recorrido de 1,5 ATR, el recorrido sale primero muchas veces por pura geometría. Publicar
  solo "lo logró el 70 % de las veces" engaña. Por eso se mide la misma regla de desenlace
  desde **todas las velas del período** (línea base) y el informe muestra las dos cifras:

  > "En los últimos 18 meses esta condición se dio 42 veces en el oro. El precio recorrió
  > 1,5 veces la volatilidad de una hora antes de tocar la invalidación en el 64 % de los casos.
  > Desde una hora cualquiera del mismo período, la misma regla se cumplió en el 61 %."

- **Si la condición no supera a la línea base por al menos 5 puntos**, la frase lo dice: "En
  este activo la condición no ha mostrado ventaja frente a una hora cualquiera." Es honesto y
  enseña algo.
- **Menos de 30 eventos:** "Muestra insuficiente para una estadística (N casos)". No se
  publica porcentaje.
- Los porcentajes se redondean a entero y las frases son plantillas de Python; agy no escribe
  ninguna cifra del plan.

Costo esperado: 10.000 ventanas de 300 velas con `_swing_levels` en Python puro. Se mide en la
implementación; si pasa de 20 s se vectoriza la detección de swings, sin cambiar su definición
(test de equivalencia contra la función original).

## 5. Candados de lenguaje

`esquema.errores` suma una lista de frases prohibidas en **todo** el texto editorial y en las
plantillas del plan:

- instrucción de operar: `compra ya`, `vende ya`, `es momento de comprar/vender`, `entra al
  mercado`, `abre una posición`, `cierra tu posición`, `toma ganancias`, `debes comprar/vender`,
  `deberías comprar/vender`;
- recomendación: `recomendamos`, `te recomiendo`, `te conviene`, `señal de compra/venta`;
- dimensionamiento: `lote`, `lotes`, `apalanca`, `% de tu capital`, `arriesga`.

Son **frases**, no palabras sueltas: `compra` o `entra` solas aparecen en texto legítimo
("gerentes de compra (PMI)", "si rompe un borde y vuelve a entrar"), y un candado que bloquea
eso termina desactivado. Se busca sin tildes y sin distinguir mayúsculas. Las formas
impersonales ("el escenario se activa", "la presión compradora") no caen. `.claude/commands/analista.md` suma la regla 10: lenguaje
impersonal y condicional, nunca una instrucción al lector.

## 6. Bitácora de planes

`data/bitacora_planes_analistas.json`, **versionada** (mismo criterio que
`historial_despachos.json`: es historia de lo que se entregó). Una entrada por informe con plan:
fecha, hora, activo, sesgo, gatillo, invalidación, recorrido, estadística publicada, analista
que lo pidió y huella del HTML.

El desenlace (activado y recorrido / activado e invalidado / no se activó) se completa con
`bot_analistas.py --desenlaces`, que relee la serie H1 para cada plan de más de 24 h sin
desenlace. Sirve para responder un reclamo con datos y para publicar algún día un historial que
incluya las pérdidas.

## Fuera de alcance

- Plan de escenarios en `/jornada`, `/dato` y `/calendario`.
- Desenlaces automáticos desde el reloj.
- Cualquier recomendación personalizada: si un analista la quiere dar, es un acto suyo, fuera
  del bot.

## Pruebas

- Personalización: contrato de ausencia; pedido con "para X" recibe el mensaje y no gasta agy.
- Firma: con y sin firma; acreditación vencida no se imprime y avisa; sin `autor` no arranca.
- Estadística: serie sintética con resultado conocido (evento, recorrido, invalidación, empate
  en la misma vela, sin definición); sin mirar el futuro (cambiar velas posteriores a la ventana
  no cambia los niveles del evento); N < 30; sin ventaja.
- Plan: nivel de origen ATR no produce plan; textos con decimales del activo.
- Candados: cada frase prohibida cae; las impersonales pasan.
- Bitácora: se escribe una entrada; `--desenlaces` la completa.
- E2E real con `/activo oro` y `/activo usdclp`, mirando el HTML.
