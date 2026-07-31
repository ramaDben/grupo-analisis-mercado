"""Contenido de la versión resumida de la capacitación de Análisis Fundamental.

Pensada para quien no va a leer las 55 láminas y acepta saber menos a cambio: 20
láminas, un tercio del material completo.

Criterio del recorte —lo importante es qué se sacrifica, no qué se conserva—:

- **Se conserva** el mecanismo (sorpresa → tasas → dólar → activos), los indicadores
  que efectivamente mueven el precio, la inversión de dirección del USD/CLP, la tabla
  de síntesis y el límite normativo.
- **Se sacrifica** la caja de herramientas conceptual del bloque 0 (efecto base,
  desestacionalización, revisiones, encuesta vs registro, índices de difusión), los
  indicadores secundarios y dos de los tres ejercicios. Con eso se pierde la capacidad
  de leer un dato que no esté en el material; esa pérdida se declara en la lámina 2 en
  lugar de disimularla.

Comparte AUTOR con la versión completa para que la firma no se desincronice.
"""

from capacitacion_fundamental_contenido import AUTOR, AMBAR, AZUL, GRIS, ROJO, VERDE

SEC_1 = "Los datos que mueven"
SEC_2 = "Chile"
SEC_3 = "De la lectura al precio"

SLIDES = [
    {
        "tipo": "portada",
        "kicker": "Resumen ejecutivo · Equipo comercial e IBS",
        "titulo": "Análisis\nFundamental",
        "bajada": "Lo esencial en 19 láminas: cómo leer un dato económico y *qué "
                  "debería hacer el precio*. Versión corta de la capacitación completa.",
        "autor": AUTOR,
        "meta": [
            ("Fecha", "31 de julio de 2026"),
            ("Naturaleza", "Material educativo interno"),
        ],
    },
    {
        "tipo": "bullets",
        "titulo": "Qué te llevas, y qué no",
        "bajada": "Esta versión es un tercio del material completo. Conviene saber "
                  "*exactamente* qué se dejó fuera.",
        "columnas": 2,
        "puntos": [
            ("✓ El mecanismo completo",
             "Por qué se mueve el precio cuando sale un dato, de principio a fin. Es "
             "lo único que no se puede recortar."),
            ("✓ Los indicadores que mandan",
             "Inflación, empleo y actividad en Estados Unidos; los cuatro que mueven "
             "el dólar en Chile."),
            ("✓ Qué debería hacer cada activo",
             "Una tabla de síntesis para el dólar, el oro, el Nasdaq y el USD/CLP."),
            ("✓ Cómo decírselo al cliente",
             "La estructura de tres líneas y el límite entre explicar y recomendar."),
            ("✗ La caja de herramientas conceptual",
             "Efecto base, ajuste estacional, revisiones, índices de difusión. Sin eso "
             "*no vas a poder leer un dato que no esté acá*."),
            ("✗ El detalle de cada indicador",
             "Cómo se construye, qué deja fuera y sus sub-lecturas. Y los "
             "complementarios: vacantes, ADP, confianza, bienes durables."),
        ],
        "clave": ("Dónde está lo que falta",
                  "En la capacitación completa, de 55 láminas, y en la guía rápida de "
                  "consulta. Este resumen sirve para *entender el mecanismo*; para "
                  "*resolver un caso nuevo* hace falta el material completo. Cuando "
                  "aparezca una duda que este documento no cubra, la respuesta está en "
                  "el área."),
    },
    {
        "tipo": "cajas",
        "titulo": "La única regla que hay que memorizar",
        "bajada": "Si te quedas con una sola idea de toda la capacitación, que sea "
                  "esta. Todo lo demás se deduce.",
        "cajas": [
            {"kicker": "Cifra 1", "titulo": "Anterior", "color": GRIS,
             "lineas": ["El valor de la publicación pasada.",
                        "Sirve para ver la *tendencia*: si el dato viene acelerando o "
                        "desacelerando."]},
            {"kicker": "Cifra 2", "titulo": "Esperado", "color": AMBAR,
             "lineas": ["Lo que el mercado creía que iba a salir.",
                        "*Ya está incorporado en el precio.* Si el dato sale igual al "
                        "esperado, en teoría no debería pasar nada."]},
            {"kicker": "Cifra 3", "titulo": "Efectivo", "color": VERDE,
             "lineas": ["Lo que realmente salió.",
                        "Por sí solo no dice nada: solo significa algo *comparado con "
                        "el esperado*.",
                        "La resta entre ambos es *la sorpresa*, y es lo único que "
                        "mueve el precio."]},
        ],
        "nota": ("La consecuencia que descoloca a todos",
                 "Un número «bueno» puede hacer *caer* el precio y uno «malo» puede "
                 "hacerlo *subir*. Si se esperaba un crecimiento de 4% y sale 2%, el "
                 "2% es buen número pero *es una decepción*. El mercado no premia "
                 "buenos resultados: premia sorpresas."),
    },
    {
        "tipo": "bullets",
        "titulo": "La cadena de transmisión",
        "bajada": "El camino que recorre *todo* dato de Estados Unidos hasta llegar al "
                  "precio de lo que operamos.",
        "puntos": [
            ("Paso 1 · Sale el dato y se compara con el consenso",
             "Nace la sorpresa. Sin sorpresa, la cadena no arranca."),
            ("Paso 2 · Cambia la expectativa sobre la tasa de interés",
             "El mercado recalcula: *¿esto hace más o menos probable que la Reserva "
             "Federal baje la tasa?* Acá se decide todo lo que sigue."),
            ("Paso 3 · Se mueve el rendimiento de los bonos",
             "Si se espera tasa alta por más tiempo, el rendimiento sube. Los bonos "
             "son el termómetro de esa expectativa."),
            ("Paso 4 · Se mueve el dólar",
             "Rendimiento más alto = tener dólares paga más = entra capital y *el "
             "dólar se fortalece*."),
            ("Paso 5 · Reacciona cada activo, por su propia razón",
             "El oro *baja* porque no paga interés y ahora el bono rinde más. El "
             "Nasdaq *baja* porque vale por ganancias futuras, que a tasa alta valen "
             "menos hoy. El USD/CLP *sube* porque el dólar se fortalece frente a todo."),
        ],
        "clave": ("La pregunta única",
                  "Frente a cualquier dato: *¿le da a la Reserva Federal una razón "
                  "para mantener la tasa alta, o para bajarla?* Con esa respuesta, la "
                  "dirección de los cuatro activos se deduce sola — no hay que "
                  "memorizar ninguna tabla."),
    },
    {
        "tipo": "seccion",
        "numero": "1",
        "titulo": "Los datos que de verdad mueven",
        "bajada": "De las decenas de publicaciones del mes, tres familias concentran "
                  "casi todo el movimiento: *inflación, empleo y actividad*.",
        "color": AZUL,
    },
    {
        "tipo": "cajas",
        "titulo": "Inflación: la familia que más pesa",
        "bajada": "Tres indicadores miden lo mismo en apariencia y responden preguntas "
                  "distintas. El que manda para la política monetaria es el tercero.",
        "seccion": SEC_1,
        "color": AZUL,
        "cajas": [
            {"kicker": "El más observado", "titulo": "Precios al consumidor (IPC)",
             "color": VERDE,
             "lineas": ["Cuánto subieron los precios que paga la gente.",
                        "Sale entre el día 10 y 15, a las 08:30 de Chile.",
                        "*Qué mirar:* la variación *mensual subyacente* —sin alimentos "
                        "ni energía—, no el titular anual.",
                        "*Por qué el subyacente:* la tasa de interés no baja el precio "
                        "del petróleo, pero sí enfría el consumo y los arriendos."]},
            {"kicker": "El que anticipa", "titulo": "Precios al productor (IPP)",
             "color": AZUL,
             "lineas": ["Precios de fábrica, antes de llegar al consumidor.",
                        "Sale junto al IPC, con un día de diferencia.",
                        "*Su valor está en la secuencia:* si al productor le suben los "
                        "costos, los traspasa al consumidor en los meses siguientes.",
                        "Si IPP e IPC apuntan igual, la señal se refuerza mucho."]},
            {"kicker": "La meta oficial", "titulo": "Gasto en consumo (PCE)",
             "color": AMBAR,
             "lineas": ["La inflación sobre lo que la gente *efectivamente gastó*.",
                        "Fin de mes, 08:30 de Chile.",
                        "*Es la vara del banco central:* su meta de 2% está definida "
                        "en la versión subyacente de este indicador.",
                        "Sale después del IPC, así que suele estar anticipado: mueve "
                        "fuerte solo cuando *lo contradice*."]},
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Empleo: un informe con tres mediciones que se contradicen",
        "bajada": "Sale completo el primer viernes del mes, 08:30 de Chile. Es el único "
                  "dato que le habla *a los dos mandatos* del banco central.",
        "seccion": SEC_1,
        "color": AZUL,
        "cajas": [
            {"kicker": "Las tres partes", "titulo": "Qué trae el informe",
             "color": VERDE,
             "lineas": ["*Nóminas:* cuántos empleos netos se crearon. Es el titular.",
                        "*Tasa de desempleo:* sale de otra encuesta —a hogares, no a "
                        "empresas—, por eso puede contradecir a las nóminas.",
                        "*Salarios:* el puente hacia la inflación. Si los sueldos "
                        "suben rápido, las empresas lo traspasan a precios.",
                        "Referencia: un alza de sueldos en torno a 3%-3,5% anual es "
                        "compatible con una inflación de 2%."]},
            {"kicker": "Trampa 1", "titulo": "El desempleo puede bajar por mala razón",
             "color": ROJO,
             "lineas": ["La tasa es una división: desocupados sobre *fuerza laboral*.",
                        "Solo cuenta como fuerza laboral quien *está buscando* trabajo.",
                        "Si alguien se desanima y deja de buscar, sale del "
                        "denominador y *la tasa baja* aunque siga sin trabajo.",
                        "*Solución:* mirar siempre la *tasa de participación*."]},
            {"kicker": "Trampa 2", "titulo": "Un empleo fuerte puede ser mala noticia",
             "color": AMBAR,
             "lineas": ["Si la economía crea mucho más empleo del esperado, presiona "
                        "los sueldos y con ellos la inflación.",
                        "Eso obliga a mantener la tasa alta más tiempo: *el dólar sube "
                        "y las bolsas caen*.",
                        "*Se invierte* cuando el miedo dominante es la recesión: ahí "
                        "un empleo fuerte sí lo celebran las bolsas.",
                        "El signo depende de *qué problema le preocupa hoy al "
                        "mercado*."]},
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Actividad: dos termómetros y una línea",
        "bajada": "Miden si la economía se está acelerando o enfriando, y uno de ellos "
                  "*se adelanta* a todo lo demás.",
        "seccion": SEC_1,
        "color": AZUL,
        "cajas": [
            {"kicker": "El adelantado", "titulo": "Gerentes de compra (PMI e ISM)",
             "color": VERDE,
             "lineas": ["Se le pregunta a quienes compran insumos si su actividad "
                        "mejora o empeora. Quien compra hoy sabe qué producirá en tres "
                        "meses: es información *del futuro*.",
                        "*La línea de los 50:* sobre 50 la actividad se expande, bajo "
                        "50 se contrae. Mide *dirección*, no tamaño.",
                        "Un PMI que cae de 58 a 53 sigue indicando expansión, solo que "
                        "menos generalizada.",
                        "*El de servicios pesa más* que el manufacturero: los "
                        "servicios son cerca del 70% de esa economía."]},
            {"kicker": "El del consumo", "titulo": "Ventas minoristas",
             "color": AZUL,
             "lineas": ["Cuánto vendió el comercio. A mitad de mes, 08:30 de Chile.",
                        "*Por qué importa:* el consumo es cerca del 70% del PIB de "
                        "Estados Unidos. Mientras el consumo aguante, no hay recesión.",
                        "*Qué mirar:* el *grupo de control*, que excluye autos, "
                        "bencina y materiales de construcción — los más volátiles.",
                        "Se publica en dinero, no en unidades: si los precios "
                        "subieron, las ventas crecen sin que se venda más."]},
        ],
        "nota": ("Y el PIB, ¿dónde queda?",
                 "Es la medida más completa de la economía y *una de las que menos "
                 "mueve el precio*: cuando se publica, el mercado ya vio tres meses de "
                 "empleo, inflación y consumo. Sirve para fijar el relato de recesión "
                 "o expansión, no para anticipar el movimiento del día."),
    },
    {
        "tipo": "tabla",
        "titulo": "Cuáles pesan más",
        "bajada": "Y la advertencia que hace la diferencia: *el peso no es fijo*.",
        "seccion": SEC_1,
        "color": VERDE,
        "encabezados": ["Impacto", "Indicadores", "Por qué pesan"],
        "pesos": [1.8, 4.2, 4.0],
        "filas": [
            ["Máximo", "Decisión de tasas · Inflación al consumidor · Informe de empleo",
             "Definen o determinan directamente el precio del dinero"],
            ["Alto", "Gasto en consumo (PCE) · Gerentes de compra de servicios · "
                     "Ventas minoristas",
             "Son la vara oficial de la meta, el adelanto del sector más grande y el "
             "pulso del consumo"],
            ["Medio", "PIB · Precios al productor · Gerentes de compra manufacturero · "
                      "Subsidios por desempleo",
             "Confirman o anticipan, pero no cambian el escenario por sí solos"],
        ],
        "nota": ("La regla del régimen",
                 "Cuando el problema del mercado es *la inflación*, el IPC manda y un "
                 "empleo fuerte se lee como amenaza. Cuando el problema es *la "
                 "recesión*, el empleo manda y un empleo fuerte se celebra. *Antes de "
                 "interpretar un dato, define qué le preocupa hoy al mercado.*"),
    },
    {
        "tipo": "seccion",
        "numero": "2",
        "titulo": "Chile",
        "bajada": "El dólar acá tiene *dos motores*: lo que pasa con el dólar en el "
                  "mundo y lo que pasa en casa. Y la dirección se invierte.",
        "color": AMBAR,
    },
    {
        "tipo": "tabla",
        "titulo": "Los cuatro que mueven el dólar en Chile",
        "bajada": "Dos instituciones concentran todo: el Instituto Nacional de "
                  "Estadísticas y el Banco Central.",
        "seccion": SEC_2,
        "color": AMBAR,
        "encabezados": ["Indicador", "Qué mide", "Cómo leerlo"],
        "pesos": [2.3, 3.4, 4.3],
        "filas": [
            ["Inflación (IPC)", "La inflación local, que publica el INE",
             "La meta del Banco Central es 3%. Inflación alta le impide bajar la tasa"],
            ["Actividad mensual\n(IMACEC)", "El termómetro mensual de la economía",
             "Mira si el alza viene de *minería* o del resto: el no minero dice más de "
             "la demanda interna"],
            ["Balanza comercial\ny cobre", "Si entran o salen dólares del país",
             "El cobre es cerca de la mitad de lo que Chile exporta: es el driver "
             "local más fuerte del dólar"],
            ["Tasa de política\nmonetaria (TPM)", "Cuánto cuesta el dinero en Chile",
             "Lo que importa es la *diferencia* con la tasa de Estados Unidos, no el "
             "nivel local"],
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Las dos cosas que hay que entender de Chile",
        "bajada": "Una invierte la dirección respecto de todo lo anterior. La otra "
                  "conecta a Chile con el otro lado del mundo.",
        "seccion": SEC_2,
        "cajas": [
            {"kicker": "Cuidado con esto",
             "titulo": "En el USD/CLP la dirección se invierte", "color": ROJO,
             "lineas": ["Cuando el número del par *sube*, lo que ocurre es que *el "
                        "peso se debilita*.",
                        "Entonces un IPC chileno *alto* fortalece al peso —el Banco "
                        "Central no podrá bajar la tasa— y *el USD/CLP baja* ⬇️.",
                        "Es el espejo del caso estadounidense, donde una inflación "
                        "alta *fortalece* al dólar.",
                        "*Regla corta:* dato chileno fuerte → dólar más barato acá. "
                        "Dato estadounidense fuerte → dólar más caro en todas partes.",
                        "*Si los dos motores se contradicen*, normalmente gana el "
                        "global."]},
            {"kicker": "La cadena completa",
             "titulo": "Por qué un dato de China mueve el dólar acá", "color": VERDE,
             "lineas": ["*1.* China es el mayor consumidor de cobre del mundo.",
                        "*2.* Si sus gerentes de compra reportan menos actividad, van "
                        "a comprar menos insumos.",
                        "*3.* Menos demanda esperada baja el precio del cobre.",
                        "*4.* El cobre es cerca de la mitad de las exportaciones "
                        "chilenas: entra menos moneda extranjera al país.",
                        "*5.* Menos oferta de dólares acá → *el USD/CLP sube* ⬆️.",
                        "*Ojo con la hora:* los datos de China salen cerca de las "
                        "21:30 de la noche anterior en hora de Chile."]},
        ],
    },
    {
        "tipo": "seccion",
        "numero": "3",
        "titulo": "De la lectura al precio",
        "bajada": "La síntesis operativa: qué debería hacer cada activo, en qué "
                  "escenario estamos, y cómo se comunica.",
        "color": VERDE,
    },
    {
        "tipo": "tabla",
        "titulo": "Qué debería hacer el precio",
        "bajada": "*No la memorices*: verifica que puedas reconstruir cada fila con la "
                  "cadena de transmisión.",
        "seccion": SEC_3,
        "color": VERDE,
        "encabezados": ["Lectura del dato", "Para la tasa", "Dólar", "Oro",
                        "Nasdaq 100", "USD/CLP"],
        "pesos": [3.0, 2.9, 1.2, 1.1, 1.5, 1.4],
        "filas": [
            ["Inflación sobre lo esperado", "Alta por más tiempo",
             "Sube ⬆️", "Baja ⬇️", "Baja ⬇️", "Sube ⬆️"],
            ["Inflación bajo lo esperado", "Espacio a recortes",
             "Baja ⬇️", "Sube ⬆️", "Sube ⬆️", "Baja ⬇️"],
            ["Empleo muy fuerte\n(régimen de inflación)", "Retrasa los recortes",
             "Sube ⬆️", "Baja ⬇️", "Baja ⬇️", "Sube ⬆️"],
            ["Empleo muy débil\n(régimen de recesión)", "Adelanta los recortes",
             "Baja ⬇️", "Sube ⬆️", "Mixto", "Sube ⬆️"],
            ["Actividad sobre lo esperado", "Menos urgencia de estimular",
             "Sube ⬆️", "Baja ⬇️", "Sube ⬆️", "Sube ⬆️"],
            ["Cobre o China al alza", "Sin efecto directo",
             "—", "Sube ⬆️", "—", "Baja ⬇️"],
        ],
        "nota": ("Cuando dos fuerzas compiten",
                 "Con *empleo muy débil* el Nasdaq queda mixto: la tasa más baja lo "
                 "favorece, pero la recesión daña las ganancias. Decidir cuál domina "
                 "*es* interpretar — y es lo que no reemplaza ninguna tabla."),
    },
    {
        "tipo": "cajas",
        "titulo": "Los cuatro escenarios posibles",
        "bajada": "Cualquier combinación de datos cae en uno de estos cuadrantes. "
                  "Ubicarlo es el resumen de tu lectura del mes.",
        "seccion": SEC_3,
        "cajas": [
            {"kicker": "Crece + inflación baja", "titulo": "El escenario ideal",
             "color": VERDE,
             "lineas": ["Crece sin presionar los precios. El banco central puede "
                        "recortar sin riesgo.",
                        "*Bolsas:* el mejor escenario ⬆️⬆️",
                        "*Dólar:* baja ⬇️ · *Oro:* sube ⬆️",
                        "*USD/CLP:* baja ⬇️"]},
            {"kicker": "Crece + inflación alta", "titulo": "Economía recalentada",
             "color": AMBAR,
             "lineas": ["La demanda supera a la oferta. El banco central debe apretar.",
                        "*Bolsas:* bajo presión ⬇️",
                        "*Dólar:* sube ⬆️ · *Oro:* baja ⬇️",
                        "*USD/CLP:* sube ⬆️"]},
            {"kicker": "Se contrae + inflación baja", "titulo": "Recesión",
             "color": AZUL,
             "lineas": ["La actividad cae y arrastra los precios. Recortes rápidos.",
                        "*Bolsas:* primero caen por ganancias, luego suben por tasa",
                        "*Dólar:* baja ⬇️ · *Oro:* sube ⬆️",
                        "*USD/CLP:* sube ⬆️ por aversión al riesgo"]},
            {"kicker": "Se contrae + inflación alta", "titulo": "Estanflación",
             "color": ROJO,
             "lineas": ["El peor cuadrante: el banco central queda atrapado entre "
                        "avivar la inflación o profundizar la recesión.",
                        "*Bolsas:* el peor escenario ⬇️⬇️",
                        "*Oro:* el gran beneficiado ⬆️⬆️",
                        "*USD/CLP:* sube ⬆️"]},
        ],
    },
    {
        "tipo": "ejercicio",
        "titulo": "Un caso resuelto de principio a fin",
        "seccion": SEC_3,
        "dato": [
            "*Índice de precios al consumidor de EE.UU.*",
            "",
            "*Subyacente mensual*",
            "Anterior: 0,2%  ·  Esperado: 0,2%",
            "*Efectivo: 0,4%*  🔥",
            "",
            "*Subyacente anual*",
            "Esperado: 3,1%  ·  *Efectivo: 3,3%*",
            "",
            "*General mensual*",
            "Esperado: 0,3%  ·  Efectivo: 0,4%",
            "",
            "Cifras ilustrativas: no corresponden a una publicación real.",
        ],
        "lectura": [
            "*La sorpresa:* el subyacente mensual salió al doble de lo esperado, y es "
            "la cifra que más pesa.",
            "*¿Es de fondo?* Sí: general y subyacente sorprenden en la misma "
            "dirección. No fue energía — la presión está en el núcleo de la canasta.",
            "*Conclusión:* la inflación no está cediendo. Se aleja la posibilidad de "
            "que el banco central baje la tasa.",
        ],
        "precio": [
            "*Dólar: sube* ⬆️ — tasa alta por más tiempo significa mayor rendimiento, "
            "y el capital va donde le pagan más.",
            "*Oro: baja* ⬇️ — no paga interés; si los bonos rinden más, pierde "
            "atractivo relativo.",
            "*Nasdaq 100: baja* ⬇️ — vale por ganancias futuras, y a tasa más alta "
            "esas ganancias valen menos hoy.",
            "*USD/CLP: sube* ⬆️ — dólar global fuerte y menos apetito por riesgo "
            "emergente.",
            "*Temporalidad:* intradía a swing de jornada (uno a tres días).",
        ],
    },
    {
        "tipo": "bullets",
        "titulo": "Cómo explicárselo al cliente",
        "bajada": "El tramo que define si el análisis sirve: un dato bien interpretado "
                  "y mal comunicado *no llega*.",
        "seccion": SEC_3,
        "color": VERDE,
        "columnas": 2,
        "puntos": [
            ("La estructura de tres líneas",
             "*Qué pasó* (el dato y su sorpresa) · *por qué importa* (el efecto en la "
             "tasa) · *qué esperar* (la dirección del activo)."),
            ("La regla de los 30 segundos",
             "Si un cliente sin experiencia no lo entiende en medio minuto, hay que "
             "decirlo más simple. «Más simple» nunca significa «sin dirección»."),
            ("Toda sigla se explica",
             "Nombre en español, sigla una sola vez entre paréntesis, y una línea de "
             "explicación. Nunca «el core PCE salió hot»."),
            ("Énfasis direccional sí, dramatización no",
             "Se dice «sesgo bajista» o «presión vendedora». No se dice «se va a "
             "derrumbar» ni se le atribuyen emociones al mercado."),
            ("Explica el mecanismo, no solo el resultado",
             "«El dólar sube porque la inflación obliga a mantener las tasas altas, y "
             "eso atrae capital» enseña. «El dólar sube» solo informa."),
            ("Un ejemplo, mal y bien",
             "❌ «Core CPI hot, hawkish para la Fed».  ✅ «Los precios subieron más de "
             "lo esperado, así que allá no podrán abaratar el dinero pronto y el dólar "
             "se fortalece»."),
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Para qué te sirve esto, y dónde se detiene",
        "bajada": "El valor concreto en tu día a día, y el límite que no se cruza.",
        "seccion": SEC_3,
        "cajas": [
            {"kicker": "Lo que ganas", "titulo": "Una conversación con criterio",
             "color": VERDE,
             "lineas": ["Poder explicar *por qué* se movió el mercado, en vez de "
                        "repetir que se movió.",
                        "Saber qué días hay datos relevantes y anticipar la "
                        "conversación en lugar de reaccionar a ella.",
                        "Distinguir cuándo un movimiento es ruido y cuándo cambia el "
                        "escenario.",
                        "Y lo que más pesa frente a un cliente: *entender lo que "
                        "estás diciendo*."]},
            {"kicker": "Dónde se detiene", "titulo": "Estas preguntas se derivan",
             "color": ROJO,
             "lineas": ["«¿Me conviene comprar dólares ahora?» · «¿Dónde pongo mi "
                        "dinero?» · «¿Hasta dónde va a subir?» · «¿Vendo o me quedo?»",
                        "Explicar *qué pasó y por qué* es análisis, y es nuestro "
                        "trabajo.",
                        "Indicarle a alguien *qué hacer con su dinero* es asesoría de "
                        "inversión, y tiene requisitos que se cumplen desde el área.",
                        "*La respuesta segura:* «déjame consultarlo con el equipo de "
                        "estudios y te confirmo»."]},
        ],
        "nota": ("Si te quedaste con ganas de más",
                 "La capacitación completa son 55 láminas y desarrolla todo lo que "
                 "este resumen dejó fuera. Y la guía rápida de 4 páginas está pensada "
                 "para consultarla con el cliente al teléfono."),
    },
    {
        "tipo": "cierre",
        "kicker": "Cierre",
        "titulo": "Naturaleza del contenido y proceso",
        "aviso": ("Advertencia y naturaleza de este material",
                  ["Este documento es *material educativo de uso interno*, elaborado "
                   "para la formación del equipo comercial y de los IBS. *No "
                   "constituye una recomendación de inversión* ni una asesoría "
                   "personalizada, y no debe distribuirse a clientes en esta forma.",
                   "Las cifras de los ejemplos son *ilustrativas*. Las referencias de "
                   "precio describen *mecanismos de mercado*, no pronósticos: el "
                   "comportamiento efectivo de un activo depende del contexto y de "
                   "factores no contenidos en un solo dato."]),
        "proceso": ("Validación de contenido",
                    ["Todo análisis de mercado, informe o material que se vaya a "
                     "difundir —cualquiera sea el canal— pasa por el *Área de Estudios "
                     "y Post-Venta* para su validación previa.",
                     "Cualquier duda sobre qué se puede afirmar, mostrar o recomendar "
                     "se resuelve directamente con el área."]),
        "autor": AUTOR,
        "fecha": "31 de julio de 2026",
    },
]
