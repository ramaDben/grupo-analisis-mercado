"""Contenido de la capacitación de Análisis Fundamental.

Separado del renderer a propósito: acá vive el criterio editorial del Área de Estudios
y Post-Venta, y en `capacitacion_fundamental_ppt.py` vive la maqueta. Editar el texto
de una slide no debe obligar a tocar el dibujo, ni al revés.

Criterio de redacción (regla de oro del proyecto): voz novata, toda sigla explicada en
español la primera vez que aparece, dirección siempre explícita. El eje es *aprender a
interpretar la publicación*; la implicación de precio se deriva del concepto.

Sintaxis: en cualquier texto, *asterisco* marca destacado.
"""

from pptx.dml.color import RGBColor

VERDE = RGBColor(0x00, 0xDC, 0x82)
ROJO = RGBColor(0xE8, 0x40, 0x40)
AMBAR = RGBColor(0xF5, 0xA5, 0x24)
AZUL = RGBColor(0x4C, 0x8D, 0xFF)
GRIS = RGBColor(0xA9, 0xA5, 0xB4)

SEC_0 = "Fundamentos de lectura"
SEC_1 = "Indicadores EE.UU."
SEC_2 = "Indicadores Chile"
SEC_3 = "Política monetaria"
SEC_4 = "Contexto global"
SEC_5 = "Interpretar en la práctica"

SLIDES = [
    # ==================================================================================
    # APERTURA
    # ==================================================================================
    {
        "tipo": "portada",
        "kicker": "Capacitación interna · Equipo comercial e IBS",
        "titulo": "Análisis\nFundamental",
        "bajada": "Cómo interpretar la publicación de datos económicos: qué mide cada "
                  "indicador, cómo se lee su resultado y *qué debería hacer el precio*.",
        "meta": [
            ("Preparado por", "Área de Estudios y Post-Venta"),
            ("Fecha", "31 de julio de 2026"),
            ("Naturaleza", "Material educativo interno"),
        ],
    },
    {
        "tipo": "bullets",
        "titulo": "Qué vas a poder hacer al terminar",
        "bajada": "El objetivo no es memorizar reacciones. Es entender el mecanismo, "
                  "para poder leer *incluso un dato que no vimos en clase*.",
        "columnas": 2,
        "puntos": [
            ("1 · Leer cualquier publicación",
             "Reconocer las tres cifras que trae todo dato —anterior, esperado y "
             "efectivo— y saber cuál de ellas mueve el mercado."),
            ("2 · Entender qué mide cada indicador",
             "Qué está contando, cómo se construye, qué deja fuera y por qué existe. "
             "Sin eso, el número es solo un número."),
            ("3 · Distinguir el detalle que importa",
             "Casi todo dato relevante trae sub-lecturas. Saber cuál pesa evita leer "
             "el titular y equivocarse."),
            ("4 · Conectarlo con la tasa de interés",
             "Todo dato de EE.UU. se traduce, tarde o temprano, en una expectativa "
             "sobre qué hará la Reserva Federal."),
            ("5 · Anticipar la dirección del precio",
             "Derivar del concepto —no de memoria— qué debería hacer el dólar, el oro, "
             "el petróleo y las bolsas."),
            ("6 · Explicárselo a un cliente",
             "Traducirlo a lenguaje simple, con dirección clara, en menos de 30 "
             "segundos y sin jerga sin explicar."),
        ],
        "clave": ("La idea que ordena todo el curso",
                  "Un dato económico no es una noticia: es *una medición*. Y el mercado "
                  "no reacciona a la medición, sino a *la diferencia entre lo que se "
                  "medía y lo que se esperaba medir*. Todo lo demás se deduce de ahí."),
    },

    # ==================================================================================
    # BLOQUE 0 — FUNDAMENTOS DE LECTURA
    # ==================================================================================
    {
        "tipo": "seccion",
        "numero": "0",
        "titulo": "Fundamentos de lectura",
        "bajada": "Conceptos que aplican a *toda* publicación, sea de Estados Unidos, "
                  "de Chile o de China. Es el bloque que convierte a alguien que "
                  "memoriza en alguien que interpreta.",
        "color": VERDE,
    },
    {
        "tipo": "cajas",
        "titulo": "La anatomía de toda publicación: tres cifras",
        "bajada": "Cuando salga cualquier dato, vas a ver estas tres. Aprender a "
                  "mirarlas en este orden es el 80% del trabajo.",
        "seccion": SEC_0,
        "cajas": [
            {"kicker": "Cifra 1", "titulo": "Anterior", "color": GRIS,
             "lineas": ["El valor de la *publicación pasada*.",
                        "Sirve para una sola cosa: ver la *tendencia*. ¿El dato viene "
                        "acelerando o desacelerando?",
                        "Ojo: el anterior *puede haber cambiado* desde que se publicó "
                        "(lo veremos en «revisiones»)."]},
            {"kicker": "Cifra 2", "titulo": "Esperado o consenso", "color": AMBAR,
             "lineas": ["Lo que el mercado *cree* que va a salir.",
                        "Es el promedio de las estimaciones de decenas de bancos y "
                        "casas de análisis.",
                        "*Este número ya está en el precio.* Si el dato sale igual al "
                        "consenso, en teoría no debería pasar nada."]},
            {"kicker": "Cifra 3", "titulo": "Efectivo o actual", "color": VERDE,
             "lineas": ["El valor que *realmente* salió.",
                        "Por sí solo no dice nada. Solo significa algo *comparado con "
                        "el consenso*.",
                        "La resta entre ambos —efectivo menos esperado— es lo que se "
                        "llama *la sorpresa*."]},
        ],
        "nota": ("El error número uno",
                 "Mirar solo la cifra efectiva. Una inflación de 3% puede ser una "
                 "excelente noticia o una muy mala, y la única forma de saberlo es "
                 "*mirar contra qué se comparaba*."),
    },
    {
        "tipo": "bullets",
        "titulo": "Por qué el mercado se mueve con la sorpresa",
        "bajada": "El concepto se llama *«ya está en el precio»* (o «descontado»), y es "
                  "la razón de que un dato buenísimo a veces no mueva nada.",
        "seccion": SEC_0,
        "puntos": [
            ("El precio de hoy contiene lo que se espera de mañana",
             "Si todo el mercado cree que la inflación va a salir en 3%, los "
             "operadores ya compraron o vendieron *antes* de que salga. Ese 3% ya está "
             "incorporado en el precio actual."),
            ("Entonces, ¿qué queda por descubrir?",
             "Solo *la parte que nadie esperaba*. Cuando el dato sale distinto al "
             "consenso, el mercado tiene información nueva y ajusta el precio."),
            ("De ahí que un dato «bueno» pueda hacer caer el precio",
             "Si se esperaba un crecimiento de 4% y sale 2%, el 2% es un buen número "
             "en sí mismo, pero es *una decepción*. El precio corrige hacia abajo."),
            ("Y que un dato «malo» pueda hacerlo subir",
             "Si se esperaba una caída del 5% y solo cae 1%, la economía se contrajo, "
             "pero *mucho menos de lo temido*. El precio sube por alivio."),
        ],
        "clave": ("Cómo decírselo a un cliente",
                  "«El mercado no premia los buenos resultados: premia las sorpresas. "
                  "Es como un alumno del que se espera un 7,0 y saca un 6,5: sacó una "
                  "buena nota, pero *decepcionó*.»"),
    },
    {
        "tipo": "tabla",
        "titulo": "Las tres unidades de medida (y por qué se confunden)",
        "bajada": "El mismo indicador se publica en varias unidades a la vez. Leer la "
                  "equivocada es la causa más común de una interpretación errónea.",
        "seccion": SEC_0,
        "encabezados": ["Unidad", "Qué compara", "Para qué sirve", "Cuidado con"],
        "pesos": [1.5, 2.4, 2.6, 3.0],
        "filas": [
            ["Mensual", "El mes contra el mes anterior",
             "Ver la *tendencia reciente*: qué está pasando ahora mismo",
             "Es pequeña (0,2%, 0,3%) y muy sensible: un decimal es mucho"],
            ["Interanual\n(o anual)", "El mes contra el *mismo mes del año pasado*",
             "Ver la *foto de largo plazo*; es la que titula la prensa",
             "Arrastra doce meses de historia: puede bajar sin que nada mejore hoy"],
            ["Anualizado", "Proyecta el trimestre *como si durara todo un año*",
             "Comparar trimestres entre sí; se usa en el PIB de EE.UU.",
             "No es el crecimiento anual: es una *proyección* del trimestre"],
        ],
        "nota": ("Regla práctica del área",
                 "Para saber qué está pasando *hoy*, mira la variación *mensual*. Para "
                 "saber dónde estamos *paradios*, mira la *interanual*. El mercado, en "
                 "el corto plazo, reacciona más a la mensual."),
    },
    {
        "tipo": "cajas",
        "titulo": "El efecto base: por qué el dato anual puede engañarte",
        "bajada": "Concepto poco explicado y absolutamente esencial. La cifra anual "
                  "puede *bajar* aunque los precios estén subiendo igual que siempre.",
        "seccion": SEC_0,
        "color": AMBAR,
        "cajas": [
            {"kicker": "Qué es", "titulo": "La comparación arrastra el pasado",
             "color": AMBAR,
             "lineas": ["La cifra interanual compara *este mes* contra *el mismo mes "
                        "del año pasado*.",
                        "Entonces depende de dos cosas: lo que pasa hoy… *y de lo que "
                        "pasó hace un año*.",
                        "Si hace doce meses hubo un mes excepcionalmente alto, al "
                        "salir de la comparación la cifra anual *cae sola*."]},
            {"kicker": "Ejemplo ilustrativo", "titulo": "Baja sin que mejore nada",
             "color": AZUL,
             "lineas": ["Supongamos que la inflación sube *0,3% todos los meses*, sin "
                        "cambios.",
                        "Pero hace un año hubo un mes de *0,9%* por un alza de "
                        "combustibles.",
                        "Cuando ese 0,9% sale de la ventana de doce meses y lo "
                        "reemplaza un 0,3%, *la cifra anual baja 0,6 puntos*.",
                        "Nada mejoró. Solo cambió el punto de comparación."]},
            {"kicker": "Cómo se usa", "titulo": "Para anticipar, no para sorprenderse",
             "color": VERDE,
             "lineas": ["El efecto base es *conocido de antemano*: los meses del año "
                        "pasado ya están publicados.",
                        "Por eso los analistas ya lo tienen en su consenso.",
                        "Sirve para *anticipar* que la cifra anual va a bajar (o "
                        "subir) en los próximos meses casi por inercia.",
                        "Y para no atribuirle mérito a una baja que era aritmética."]},
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "General y subyacente: por qué se excluyen alimentos y energía",
        "bajada": "Suena arbitrario y no lo es. Entender esta distinción es entender "
                  "cómo piensa un banco central.",
        "seccion": SEC_0,
        "cajas": [
            {"kicker": "Dato general", "titulo": "Todo lo que la gente paga",
             "color": AZUL,
             "lineas": ["Incluye *absolutamente todo*: la cuenta de la luz, la "
                        "bencina, el pan, el arriendo.",
                        "Es el que *siente* la gente en el bolsillo y el que aparece "
                        "en las noticias.",
                        "Problema: sube y baja con violencia por cosas que nadie "
                        "controla (una sequía, un conflicto que sube el petróleo)."]},
            {"kicker": "Dato subyacente", "titulo": "Sin alimentos ni energía",
             "color": VERDE,
             "lineas": ["Se le quitan los dos componentes *más volátiles*: alimentos y "
                        "energía.",
                        "Lo que queda muestra *la tendencia de fondo*: si la inflación "
                        "está metida en los servicios, los arriendos, los sueldos.",
                        "En inglés se le dice *core*, y verás ese nombre en muchas "
                        "plataformas."]},
            {"kicker": "Por qué importa",
             "titulo": "El banco central no controla el clima", "color": AMBAR,
             "lineas": ["Una tasa de interés más alta *no baja el precio del petróleo*: "
                        "eso lo fija la geopolítica y la OPEP+.",
                        "Pero sí puede enfriar el consumo, los arriendos y las "
                        "presiones de sueldos.",
                        "Por eso el banco central mira *el subyacente*: es la parte de "
                        "la inflación sobre la que su herramienta *sí* actúa.",
                        "Y por eso el mercado también lo pondera más."]},
        ],
        "nota": ("Consecuencia directa para la lectura",
                 "Si el dato general sorprende al alza *pero el subyacente sale en "
                 "línea*, la reacción del precio suele ser corta y revertirse: el "
                 "mercado concluye que fue energía, no inflación de fondo."),
    },
    {
        "tipo": "bullets",
        "titulo": "Dos conceptos que explican por qué el número «cambia»",
        "bajada": "Desestacionalización y revisiones. Sin estos dos, tarde o temprano "
                  "vas a pensar que la fuente se equivocó.",
        "seccion": SEC_0,
        "columnas": 2,
        "puntos": [
            ("Desestacionalización · qué es",
             "Hay movimientos que se repiten *todos los años*: en diciembre se "
             "contrata para las fiestas, en marzo suben los útiles escolares."),
            ("Desestacionalización · para qué",
             "Si no se corrigiera, cada diciembre parecería un auge y cada enero una "
             "crisis. El ajuste *quita el patrón estacional* para dejar ver lo real."),
            ("Desestacionalización · cómo se lee",
             "El dato que publica el calendario y que mueve el mercado es *el "
             "ajustado*. El «sin ajustar» existe, pero se usa para otras cosas "
             "(reajustes, contratos)."),
            ("Revisiones · qué son",
             "El primer número sale con información *incompleta*: no todas las "
             "empresas respondieron la encuesta a tiempo. Después se corrige."),
            ("Revisiones · dónde pegan más",
             "En el empleo de EE.UU. cada publicación *revisa los dos meses "
             "anteriores*. En el PIB hay tres estimaciones sucesivas del mismo "
             "trimestre."),
            ("Revisiones · por qué te importan",
             "Una revisión grande *puede mover más que el dato del mes*: si el mes "
             "pasado se crearon 100 mil empleos menos de lo informado, la foto del "
             "empleo cambia entera."),
        ],
        "clave": ("Lo que esto te enseña sobre la naturaleza del dato",
                  "Un indicador económico es *una estimación que mejora con el "
                  "tiempo*, no una verdad definitiva. Quien interpreta bien trata el "
                  "primer número como *la mejor aproximación disponible*, no como un "
                  "hecho cerrado."),
    },
    {
        "tipo": "cajas",
        "titulo": "Dos formas de medir la economía: encuesta y registro",
        "bajada": "Saber de qué tipo es el dato que estás leyendo te dice *cuánta "
                  "confianza* darle y *cuánto se adelanta*.",
        "seccion": SEC_0,
        "cajas": [
            {"kicker": "Tipo 1 · Registro", "titulo": "Se cuenta lo que ya ocurrió",
             "color": AZUL,
             "lineas": ["Se suman hechos concretos: sueldos pagados, cajas registradas, "
                        "barriles almacenados, contenedores exportados.",
                        "*Ventaja:* es preciso y difícil de discutir.",
                        "*Desventaja:* llega tarde. Cuando se publica, el hecho ya "
                        "pasó.",
                        "Ejemplos: nóminas, ventas minoristas, balanza comercial, PIB."]},
            {"kicker": "Tipo 2 · Encuesta", "titulo": "Se pregunta cómo se ve el futuro",
             "color": VERDE,
             "lineas": ["Se consulta a gerentes de compra, a empresas o a "
                        "consumidores: *¿mejor o peor que el mes pasado?*",
                        "*Ventaja:* se adelanta. Quien compra insumos hoy sabe qué va "
                        "a producir en tres meses.",
                        "*Desventaja:* mide *percepción*, y la percepción puede "
                        "equivocarse o contagiarse del ánimo general.",
                        "Ejemplos: PMI, ISM, confianza del consumidor."]},
            {"kicker": "Cómo se combinan", "titulo": "Uno avisa, el otro confirma",
             "color": AMBAR,
             "lineas": ["La lectura profesional los usa *en secuencia*: la encuesta "
                        "*anticipa* el giro, el registro lo *confirma*.",
                        "Si las encuestas se deterioran tres meses seguidos y luego "
                        "las ventas caen, había aviso.",
                        "Si la encuesta se deteriora y el registro *no* la sigue, fue "
                        "ruido de ánimo.",
                        "Nunca contrapongas uno al otro: *miden cosas distintas*."]},
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Índices de difusión: por qué 50 es la frontera",
        "bajada": "Todos los PMI e ISM se leen igual. Entendido una vez, aplica a "
                  "Estados Unidos, a China, a la Zona Euro y a Chile.",
        "seccion": SEC_0,
        "color": AZUL,
        "cajas": [
            {"kicker": "Cómo se construye", "titulo": "Se cuenta cuántos mejoran",
             "color": AZUL,
             "lineas": ["Se le pregunta a cientos de gerentes de compra: *¿su actividad "
                        "está mejor, igual o peor que el mes pasado?*",
                        "El índice es el *porcentaje que responde «mejor»*, más la "
                        "mitad de los que responden «igual».",
                        "Por eso el resultado va siempre entre 0 y 100."]},
            {"kicker": "Qué significa el 50",
             "titulo": "La mitad mejora, la mitad empeora", "color": VERDE,
             "lineas": ["*Sobre 50* → más empresas mejoran que empeoran: la actividad "
                        "*se está expandiendo*.",
                        "*Bajo 50* → más empresas empeoran: la actividad *se está "
                        "contrayendo*.",
                        "*En 50* → equilibrio exacto, sin cambio.",
                        "La distancia respecto de 50 indica *qué tan generalizado* es "
                        "el movimiento."]},
            {"kicker": "La trampa clásica", "titulo": "Mide dirección, no tamaño",
             "color": AMBAR,
             "lineas": ["Un PMI de 52 *no* significa que la economía creció 52, ni un "
                        "2%. Significa que *más empresas mejoraron que empeoraron*.",
                        "Un PMI que cae de 58 a 53 sigue indicando *expansión*, solo "
                        "que menos generalizada. No es contracción.",
                        "Y una empresa gigante cuenta *lo mismo* que una chica: el "
                        "índice no pondera por tamaño."]},
        ],
    },
    {
        "tipo": "tabla",
        "titulo": "Adelantados, coincidentes y atrasados",
        "bajada": "El tercer eje de clasificación. Te dice *para qué* sirve cada dato: "
                  "para anticipar, para confirmar o para explicar.",
        "seccion": SEC_0,
        "encabezados": ["Tipo", "Qué hace", "Ejemplos", "Cómo se usa al interpretar"],
        "pesos": [1.6, 2.3, 2.6, 3.2],
        "filas": [
            ["Adelantados", "Se mueven *antes* que la economía",
             "PMI e ISM, peticiones de subsidio, permisos de construcción, "
             "expectativas de inflación",
             "Para *anticipar* el giro. Son los que más mueven el precio, porque traen "
             "información nueva"],
            ["Coincidentes", "Se mueven *junto con* la economía",
             "Nóminas de empleo, producción industrial, ventas minoristas",
             "Para *confirmar* que el giro anticipado se está materializando de verdad"],
            ["Atrasados", "Se mueven *después* que la economía",
             "Tasa de desempleo, PIB, inflación subyacente",
             "Para *explicar* y para medir consecuencias. Mueven menos… salvo que "
             "sorprendan mucho"],
        ],
        "nota": ("Por qué la inflación, siendo atrasada, mueve tanto",
                 "Porque el banco central *decide sobre ella*. Un dato atrasado que "
                 "define la política monetaria pesa más que un adelantado que no "
                 "define nada. *El peso lo da la consecuencia, no el timing.*"),
    },
    {
        "tipo": "bullets",
        "titulo": "La cadena de transmisión: del dato al precio",
        "bajada": "Este es el mapa mental que hay que tener siempre. *Todo* dato de "
                  "Estados Unidos recorre este camino.",
        "seccion": SEC_0,
        "puntos": [
            ("Paso 1 · Sale el dato y se compara con el consenso",
             "Nace la sorpresa. Sin sorpresa, la cadena no arranca."),
            ("Paso 2 · Cambia la expectativa sobre la tasa de interés",
             "El mercado recalcula: *¿esto hace más o menos probable que la Reserva "
             "Federal baje la tasa?* Acá se decide todo lo que sigue."),
            ("Paso 3 · Se mueve el rendimiento de los bonos del Tesoro",
             "Los bonos son el termómetro de esa expectativa. Si se espera tasa más "
             "alta por más tiempo, *el rendimiento sube*."),
            ("Paso 4 · Se mueve el dólar",
             "Rendimiento más alto = tener dólares paga más = *entra capital y el "
             "dólar se fortalece*. Es el eslabón que conecta con nuestros activos."),
            ("Paso 5 · Reaccionan los activos, cada uno por su razón",
             "El oro *baja* (compite con un bono que ahora paga más). El Nasdaq *baja* "
             "(vale por ganancias futuras, que a tasa alta valen menos hoy). El "
             "USD/CLP *sube* (el dólar se fortalece frente a todo)."),
        ],
        "clave": ("La pregunta única que resume la cadena",
                  "Frente a cualquier dato de EE.UU., pregúntate solo esto: "
                  "*¿le da a la Reserva Federal una razón para mantener la tasa alta, "
                  "o para bajarla?* Con esa respuesta, la dirección de los cuatro "
                  "activos se deduce sola."),
    },

    # ==================================================================================
    # BLOQUE 1 — ESTADOS UNIDOS
    # ==================================================================================
    {
        "tipo": "seccion",
        "numero": "1",
        "titulo": "Indicadores de Estados Unidos",
        "bajada": "Son los que mandan en el mercado global, porque definen la tasa de "
                  "interés del dólar — y el dólar es *la moneda en la que se cotiza "
                  "casi todo lo que operamos*.",
        "color": AZUL,
    },
    {
        "tipo": "tabla",
        "titulo": "El mes macro de Estados Unidos",
        "bajada": "Los datos no salen al azar: siguen una secuencia que se repite todos "
                  "los meses. Conocerla te permite *preparar* la semana.",
        "seccion": SEC_1,
        "color": AZUL,
        "encabezados": ["Momento del mes", "Qué se publica", "Hora Chile", "Tipo"],
        "pesos": [2.0, 4.2, 1.5, 2.0],
        "filas": [
            ["Día hábil 1", "Índice de gerentes de compra manufacturero (ISM)",
             "10:00", "Encuesta · adelantado"],
            ["Día hábil 3", "Índice de gerentes de compra de servicios (ISM)",
             "10:00", "Encuesta · adelantado"],
            ["Viernes 1", "Informe de empleo: nóminas, desempleo y salarios",
             "08:30", "Registro + encuesta"],
            ["Días 10 a 15", "Inflación al consumidor (IPC) y al productor (IPP)",
             "08:30", "Registro · atrasado"],
            ["Mitad de mes", "Ventas minoristas",
             "08:30", "Registro · coincidente"],
            ["Fin de mes", "Gasto en consumo personal (PCE) y PIB trimestral",
             "08:30", "Registro · atrasado"],
            ["Todos los jueves", "Peticiones de subsidio por desempleo",
             "08:30", "Registro · adelantado"],
        ],
        "nota": ("Sobre las horas: nunca las asumas fijas",
                 "Los horarios de arriba son los de *hoy, 31 de julio*. Estados Unidos "
                 "y Chile cambian su horario de verano en meses distintos, así que la "
                 "misma publicación puede caer una hora antes o después según la época "
                 "del año. *Confirma siempre en el calendario.*"),
    },
    {
        "tipo": "ficha",
        "titulo": "Índice de precios al consumidor (IPC)",
        "bajada": "El indicador más observado del planeta. Si vas a dominar uno solo, "
                  "que sea este.",
        "seccion": SEC_1,
        "color": AZUL,
        "meta": [
            ("Quién lo publica", "Oficina de Estadísticas Laborales"),
            ("Cuándo", "Entre el día 10 y 15 · 08:30 Chile"),
            ("Frecuencia", "Mensual"),
            ("Tipo", "Registro · atrasado"),
        ],
        "bloques": [
            ("qué mide exactamente",
             ["Cuánto cambió el precio de *una canasta fija* de bienes y servicios que "
              "compra un hogar urbano típico.",
              "«Fija» es la palabra clave: se mide *siempre la misma canasta*, para que "
              "el cambio sea de precio y no de hábitos de consumo.",
              "El componente más grande es la *vivienda* (arriendos y su equivalente "
              "para propietarios): alrededor de un tercio del índice.",
              "Es *la inflación que siente la gente*, y por eso es la que tiene peso "
              "político y mediático."]),
            ("cómo está construido",
             ["Se recolectan decenas de miles de precios en comercios y viviendas de "
              "todo el país, cada mes.",
              "Cada categoría *pesa* según cuánto gasta en ella un hogar promedio: si "
              "la vivienda es un tercio del gasto, es un tercio del índice.",
              "El resultado se ajusta por estacionalidad para poder comparar meses.",
              "*Limitación importante:* al ser una canasta fija, si la carne sube y la "
              "gente se cambia al pollo, el índice sigue midiendo la carne. Tiende a "
              "*sobreestimar* la inflación real. Este defecto es la razón de que exista "
              "el PCE."]),
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "IPC: cómo se lee la publicación",
        "bajada": "Salen cuatro cifras al mismo tiempo. El orden en que las mires "
                  "determina si interpretas bien o mal.",
        "seccion": SEC_1,
        "color": AZUL,
        "cajas": [
            {"kicker": "Mira primero", "titulo": "Subyacente mensual",
             "color": VERDE,
             "lineas": ["*La más importante de las cuatro.*",
                        "Sin alimentos ni energía, mes contra mes.",
                        "Muestra la *tendencia de fondo, ahora*: si la inflación está "
                        "metida en servicios y arriendos.",
                        "Es la que el banco central mira y la que más mueve el precio.",
                        "Referencia conceptual: un 0,2% mensual sostenido equivale, "
                        "más o menos, a la meta de 2% anual."]},
            {"kicker": "Mira segundo", "titulo": "Subyacente anual",
             "color": AZUL,
             "lineas": ["La misma exclusión, pero contra el mismo mes del año pasado.",
                        "Da el *contexto*: ¿venimos bajando o estancados?",
                        "Recuerda el *efecto base*: parte de su movimiento puede ser "
                        "pura aritmética del año anterior.",
                        "Es la que se compara contra la meta oficial del banco "
                        "central."]},
            {"kicker": "Mira al final", "titulo": "General, mensual y anual",
             "color": AMBAR,
             "lineas": ["Es el titular de la prensa, y el que *menos* define la "
                        "política monetaria.",
                        "Su diferencia con el subyacente te dice *qué hicieron la "
                        "energía y los alimentos* este mes.",
                        "Si el general sorprende y el subyacente no: fue energía. "
                        "Reacción típica *corta y con reversión*.",
                        "Si *ambos* sorprenden en la misma dirección: la señal es "
                        "sólida y el movimiento tiende a sostenerse."]},
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "IPC: qué debería hacer el precio, y por qué",
        "bajada": "Ejemplo ilustrativo con consenso de *0,2%* en la variación mensual "
                  "subyacente. Fíjate en que la dirección *se deduce*, no se memoriza.",
        "seccion": SEC_1,
        "cajas": [
            {"kicker": "Sale 0,4% · sobre lo esperado",
             "titulo": "La inflación no cede", "color": ROJO,
             "lineas": ["*Razonamiento:* si los precios siguen subiendo, el banco "
                        "central no puede bajar la tasa. Dinero caro por más tiempo.",
                        "*Dólar (índice DXY):* sube ⬆️ — un rendimiento más alto atrae "
                        "capital hacia el dólar.",
                        "*Oro:* baja ⬇️ — no paga interés; si el bono paga más, el oro "
                        "pierde atractivo relativo.",
                        "*Nasdaq 100:* baja ⬇️ — vale por ganancias futuras, y a tasa "
                        "más alta esas ganancias valen menos hoy.",
                        "*USD/CLP:* sube ⬆️ — el dólar se fortalece frente a todo, y "
                        "el peso es una moneda emergente."]},
            {"kicker": "Sale 0,1% · bajo lo esperado",
             "titulo": "Se abre el camino a recortes", "color": VERDE,
             "lineas": ["*Razonamiento:* si los precios se calman, el banco central "
                        "gana espacio para abaratar el dinero.",
                        "*Dólar:* baja ⬇️ — el rendimiento esperado cae y el dólar "
                        "pierde atractivo.",
                        "*Oro:* sube ⬆️ — enfrenta menos competencia de los bonos y "
                        "además se abarata para quien compra en otra moneda.",
                        "*Nasdaq 100:* sube ⬆️ — tasa más baja hace valer más las "
                        "ganancias futuras.",
                        "*USD/CLP:* baja ⬇️ — dólar global más débil y más apetito por "
                        "activos emergentes."]},
            {"kicker": "Sale 0,2% · en línea",
             "titulo": "Ya estaba en el precio", "color": AMBAR,
             "lineas": ["*Razonamiento:* no hay información nueva. La cadena de "
                        "transmisión no arranca.",
                        "*Reacción típica:* movimiento breve por el ruido de los "
                        "primeros segundos, y *reversión*.",
                        "*Dónde se va el mercado entonces:* al detalle. Busca la "
                        "vivienda, los servicios, la diferencia general-subyacente.",
                        "*Lectura para el cliente:* «salió como se esperaba, así que el "
                        "mercado ya lo tenía incorporado».",
                        "Es el escenario donde más se equivoca quien opera el titular."]},
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "Índice de precios al productor (IPP)",
        "bajada": "La inflación *antes* de llegar a la góndola. Se subestima, y es uno "
                  "de los mejores adelantos que existen.",
        "seccion": SEC_1,
        "color": AZUL,
        "meta": [
            ("Quién lo publica", "Oficina de Estadísticas Laborales"),
            ("Cuándo", "Junto al IPC, a un día · 08:30 Chile"),
            ("Frecuencia", "Mensual"),
            ("Tipo", "Registro · adelantado"),
        ],
        "bloques": [
            ("qué mide exactamente",
             ["Los precios que *reciben los productores* por lo que venden — no los que "
              "paga el consumidor.",
              "Es decir: mide la inflación *aguas arriba*, en la fábrica y en el "
              "mayorista, antes de que llegue al público.",
              "También tiene su versión *subyacente*, sin alimentos ni energía, por la "
              "misma razón que el IPC.",
              "Incluye bienes y también servicios de transporte y almacenamiento."]),
            ("cómo se interpreta",
             ["*Su valor está en la secuencia:* si al productor le suben los costos "
              "hoy, tenderá a traspasarlos al consumidor en los meses siguientes.",
              "*Si IPP e IPC apuntan en la misma dirección* → la señal se refuerza "
              "mucho: la presión es real y viene por toda la cadena.",
              "*Si se contradicen* → en el corto plazo gana el IPC (es el que mira el "
              "banco central), pero el IPP te está avisando del *próximo* IPC.",
              "*Dato adicional:* algunos componentes del IPP alimentan el cálculo del "
              "PCE, así que un IPP alto suele adelantar un PCE alto.",
              "*Efecto en precio:* la misma dirección que el IPC, pero con menos "
              "intensidad — salvo que sorprenda mucho."]),
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "Gasto en consumo personal (PCE)",
        "bajada": "La medida de inflación que el banco central *eligió como su meta "
                  "oficial*. Entender por qué la eligió es entender el indicador.",
        "seccion": SEC_1,
        "color": AZUL,
        "meta": [
            ("Quién lo publica", "Oficina de Análisis Económico"),
            ("Cuándo", "Fin de mes · 08:30 Chile"),
            ("Frecuencia", "Mensual"),
            ("La meta oficial", "2% anual en la versión subyacente"),
        ],
        "bloques": [
            ("qué mide, y en qué se diferencia del IPC",
             ["Mide la inflación sobre *lo que la gente efectivamente gastó*, no sobre "
              "una canasta fija.",
              "*Diferencia 1 — la canasta se adapta:* si la carne sube y la gente se "
              "cambia al pollo, el PCE lo registra. El IPC no.",
              "*Diferencia 2 — cobertura más amplia:* incluye gasto hecho *por cuenta "
              "del consumidor*, como la salud que paga el seguro o el empleador. El IPC "
              "solo cuenta lo que sale del bolsillo.",
              "*Diferencia 3 — distintos pesos:* la vivienda pesa mucho menos que en el "
              "IPC, y la salud mucho más.",
              "Consecuencia práctica: el PCE suele resultar *algo más bajo* que el IPC."]),
            ("cómo se lee su publicación",
             ["*Mira el subyacente:* es la cifra sobre la que está definida la meta de "
              "2%. Es *el número* de la política monetaria.",
              "*Sale después del IPC*, así que el mercado ya lo estimó a partir de "
              "aquel. Por eso suele mover menos de lo que su importancia sugeriría.",
              "*Cuándo sí mueve fuerte:* cuando *contradice* al IPC. Ahí obliga a "
              "recalcular todo el escenario de tasas.",
              "*Viene acompañado* del ingreso y del gasto personal: si el gasto crece "
              "más que el ingreso, la gente está usando ahorros o deuda — consumo "
              "fuerte pero *menos sostenible*.",
              "*Efecto en precio:* idéntica lógica al IPC, y con más autoridad, porque "
              "es la vara oficial."]),
        ],
    },
    {
        "tipo": "tabla",
        "titulo": "Las tres inflaciones, comparadas",
        "bajada": "Miden lo mismo en apariencia y responden preguntas distintas. Esta "
                  "tabla es la que conviene tener a mano.",
        "seccion": SEC_1,
        "color": AZUL,
        "encabezados": ["", "IPC", "IPP", "PCE"],
        "pesos": [1.8, 2.7, 2.7, 2.8],
        "filas": [
            ["¿Qué precios mide?", "Los que paga el consumidor",
             "Los que recibe el productor", "Los del consumo efectivamente realizado"],
            ["¿Canasta?", "Fija: siempre la misma",
             "Producción nacional", "Se adapta al cambio de hábitos"],
            ["¿Para qué sirve?", "Saber qué siente la gente",
             "Anticipar la inflación futura", "Medir contra la meta oficial"],
            ["¿Quién lo mira más?", "La prensa y el público",
             "Los analistas de costos", "El banco central"],
            ["¿Cuánto mueve el precio?", "Mucho — es el de mayor impacto",
             "Moderado", "Mucho, pero ya anticipado por el IPC"],
        ],
        "nota": ("Cómo explicárselo a un cliente en una frase",
                 "«El IPC mide lo que subió el supermercado; el IPP, lo que subió la "
                 "fábrica antes de llegar al supermercado; y el PCE es la medida que el "
                 "banco central usa para decidir si sube o baja las tasas.»"),
    },
    {
        "tipo": "cajas",
        "titulo": "El informe de empleo: tres mediciones en un solo documento",
        "bajada": "Sale todo junto el primer viernes del mes, a las 08:30 de Chile. Y "
                  "sus tres partes *pueden contradecirse entre sí*.",
        "seccion": SEC_1,
        "color": AZUL,
        "cajas": [
            {"kicker": "Parte 1", "titulo": "Nóminas no agrícolas",
             "color": VERDE,
             "lineas": ["Cuántos *puestos de trabajo netos* se crearon el mes pasado.",
                        "Sale de una encuesta a *empresas* (unas 120 mil "
                        "establecimientos): cuenta puestos, no personas.",
                        "Excluye el sector agrícola —muy estacional— y el trabajo por "
                        "cuenta propia.",
                        "*Es la cifra que titula*, y la que más mueve el mercado."]},
            {"kicker": "Parte 2", "titulo": "Tasa de desempleo",
             "color": AMBAR,
             "lineas": ["Sale de una encuesta *distinta*: a *hogares* (unos 60 mil).",
                        "Por eso puede contradecir a las nóminas: son dos muestras "
                        "diferentes midiendo cosas diferentes.",
                        "Cuenta *personas que buscan trabajo y no encuentran*, como "
                        "porcentaje de la fuerza laboral.",
                        "Tiene una trampa grande, que vemos en la slide siguiente."]},
            {"kicker": "Parte 3", "titulo": "Salario promedio por hora",
             "color": AZUL,
             "lineas": ["Cuánto crecieron los sueldos, mensual y anualmente.",
                        "*Es el puente conceptual hacia la inflación:* si los sueldos "
                        "suben rápido, las empresas traspasan ese costo a los precios.",
                        "El banco central lo vigila de cerca por eso mismo.",
                        "Referencia conceptual: un crecimiento en torno a 3%-3,5% anual "
                        "es *compatible* con una inflación de 2%."]},
        ],
        "nota": ("Por qué este informe mueve tanto",
                 "Porque toca *directamente la mitad del mandato* del banco central "
                 "(el empleo) y, a través de los salarios, también la otra mitad (los "
                 "precios). Es el único dato del mes que habla de las dos cosas."),
    },
    {
        "tipo": "cajas",
        "titulo": "Nóminas y desempleo: las dos trampas de lectura",
        "bajada": "Son los dos errores de interpretación más frecuentes del mercado, y "
                  "los dos se evitan entendiendo *cómo se construye* cada cifra.",
        "seccion": SEC_1,
        "cajas": [
            {"kicker": "Trampa 1", "titulo": "El desempleo puede bajar por mala razón",
             "color": ROJO,
             "lineas": ["La tasa es una *división*: desocupados dividido por *fuerza "
                        "laboral*.",
                        "Y solo se cuenta en la fuerza laboral a quien *está buscando* "
                        "trabajo activamente.",
                        "Entonces, si alguien se desanima y deja de buscar, *sale del "
                        "denominador*: la tasa de desempleo *baja* aunque esa persona "
                        "siga sin trabajo.",
                        "*Cómo se resuelve:* mirar siempre la *tasa de participación*. "
                        "Si el desempleo bajó y la participación también, la mejora es "
                        "falsa.",
                        "Y al revés: si el desempleo sube *porque entró más gente a "
                        "buscar*, es señal de una economía que *atrae* trabajadores."]},
            {"kicker": "Trampa 2", "titulo": "Un empleo muy fuerte puede ser mala noticia",
             "color": AMBAR,
             "lineas": ["Contraintuitivo y central: *«buenas noticias económicas» no "
                        "siempre son «buenas noticias para el mercado»*.",
                        "Si la economía crea mucho más empleo de lo esperado, sube la "
                        "presión sobre los sueldos y, con ella, la inflación.",
                        "Eso obliga al banco central a *mantener la tasa alta más "
                        "tiempo* → el dólar se fortalece y las bolsas caen.",
                        "*Cuándo se invierte esta lógica:* cuando el miedo dominante es "
                        "la recesión y no la inflación. Ahí un empleo fuerte *sí* es "
                        "celebrado por las bolsas.",
                        "*Conclusión:* el signo de la reacción depende de *qué problema "
                        "le preocupa hoy al mercado*."]},
        ],
        "nota": ("Y la tercera cosa que hay que mirar siempre: las revisiones",
                 "Cada informe *corrige los dos meses anteriores*. Una revisión de "
                 "-100 mil empleos cambia la foto del mercado laboral más que el dato "
                 "del mes, y muchas veces el mercado reacciona a eso y no al titular."),
    },
    {
        "tipo": "ficha",
        "titulo": "Producto interno bruto (PIB)",
        "bajada": "La medida más completa de una economía… y una de las que menos mueve "
                  "el precio. Vale la pena entender por qué.",
        "seccion": SEC_1,
        "color": AZUL,
        "meta": [
            ("Quién lo publica", "Oficina de Análisis Económico"),
            ("Cuándo", "Fin de mes · 08:30 Chile"),
            ("Frecuencia", "Trimestral, en tres estimaciones"),
            ("Unidad", "Anualizado y desestacionalizado"),
        ],
        "bloques": [
            ("qué mide y cómo se compone",
             ["El valor de *todos los bienes y servicios finales* producidos en el país "
              "durante el trimestre.",
              "Se compone de cuatro patas: *consumo de los hogares* (alrededor del 70% "
              "en EE.UU.), *inversión* de las empresas, *gasto público* y "
              "*exportaciones menos importaciones*.",
              "Se publica *anualizado*: el trimestre se proyecta como si el ritmo "
              "durara doce meses. Un 2,5% trimestral anualizado *no* es un 2,5% anual.",
              "*Dónde está la calidad del dato:* en la composición. Un PIB que crece "
              "por *consumo* es sólido; uno que crece por *acumulación de inventarios* "
              "—productos que se fabricaron y no se vendieron— es frágil y suele "
              "revertirse el trimestre siguiente."]),
            ("cómo se lee, y por qué mueve poco",
             ["*Tres estimaciones del mismo trimestre:* la *adelantada* (unos 30 días "
              "después del cierre), la *segunda* (60 días) y la *tercera* (90 días).",
              "*La que mueve es la adelantada*: es la que trae información nueva. Las "
              "otras dos solo ajustan.",
              "*Por qué mueve poco en general:* es un dato *muy atrasado*. Cuando se "
              "publica, el mercado ya vio tres meses de empleo, inflación y consumo — "
              "es decir, ya sabe cómo venía el trimestre.",
              "*Para qué sí sirve:* para *fijar el relato*. Dos trimestres negativos "
              "consecutivos activan la conversación de recesión, y eso sí cambia el "
              "escenario de tasas.",
              "*Efecto en precio:* PIB sobre lo esperado → dólar arriba, bolsas "
              "usualmente arriba (mejores ganancias), oro abajo."]),
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "ISM y PMI: los índices de gerentes de compra",
        "bajada": "Los adelantados más importantes. Ya sabes leerlos: se interpretan "
                  "con la línea de los 50 que vimos en el bloque de fundamentos.",
        "seccion": SEC_1,
        "color": AZUL,
        "meta": [
            ("ISM manufacturero", "Día hábil 1 · 10:00 Chile"),
            ("ISM de servicios", "Día hábil 3 · 10:00 Chile"),
            ("PMI de S&P Global", "Adelanto a mitad de mes · 09:45"),
            ("Frontera", "50 = expansión / contracción"),
        ],
        "bloques": [
            ("qué miden y por qué hay dos familias",
             ["Ambos preguntan a *gerentes de compra* —las personas que deciden cuántos "
              "insumos comprar— si su actividad mejora o empeora.",
              "*Por qué a ellos:* quien compra insumos hoy sabe qué va a producir en "
              "tres meses. Es información *del futuro*.",
              "El *ISM* lo publica el Instituto de Gestión de Suministros; el *PMI* lo "
              "publica S&P Global. Miden lo mismo con muestras y metodologías "
              "distintas, así que pueden diferir.",
              "*El de servicios pesa más que el manufacturero*: los servicios son "
              "cerca del 70% de la economía de EE.UU. Un error frecuente es darle más "
              "peso a la manufactura porque suena más «económica»."]),
            ("qué mirar dentro del índice",
             ["El titular es un promedio de sub-índices, y *los sub-índices dicen más "
              "que el titular*.",
              "*Nuevos pedidos:* el más adelantado de todos. Es la demanda que viene.",
              "*Empleo:* anticipa las nóminas del mes.",
              "*Precios pagados:* anticipa la inflación de costos. Cuando este sube "
              "fuerte, es un aviso temprano de IPP e IPC.",
              "*Efecto en precio:* un ISM de servicios sobre lo esperado fortalece el "
              "dólar (economía sólida → tasa alta sostenida) y presiona al oro. Si el "
              "sub-índice de precios sube fuerte, el efecto se amplifica."]),
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Consumo y empleo semanal: dos termómetros de frecuencia distinta",
        "bajada": "Uno mide dónde se juega el 70% de la economía. El otro es el dato "
                  "macro más frecuente que existe.",
        "seccion": SEC_1,
        "color": AZUL,
        "cajas": [
            {"kicker": "Mitad de mes · 08:30", "titulo": "Ventas minoristas",
             "color": VERDE,
             "lineas": ["Cuánto vendió el comercio: el termómetro directo del consumo.",
                        "*Por qué importa tanto:* el consumo es cerca del 70% del PIB "
                        "de EE.UU. Mientras el consumo aguante, no hay recesión.",
                        "*Qué mirar de verdad:* el *grupo de control*, que excluye "
                        "autos, bencina, materiales de construcción y comida fuera del "
                        "hogar.",
                        "*Por qué ese y no el titular:* los excluidos son muy volátiles "
                        "—el precio de la bencina distorsiona todo— y el grupo de "
                        "control es el que alimenta el cálculo del PIB.",
                        "*Se publica en pesos, no en unidades:* si los precios subieron, "
                        "las ventas pueden crecer sin que se venda más. Hay que "
                        "cruzarlo con la inflación."]},
            {"kicker": "Todos los jueves · 08:30",
             "titulo": "Peticiones de subsidio por desempleo", "color": AMBAR,
             "lineas": ["Cuántas personas pidieron seguro de cesantía *esa semana*.",
                        "*Su virtud es la frecuencia:* es el único dato macro relevante "
                        "que sale cada semana. Detecta un giro antes que cualquier otro.",
                        "*Cómo se lee:* nunca la semana suelta —es muy ruidosa— sino "
                        "el *promedio de cuatro semanas*.",
                        "*Referencias conceptuales:* bajo unas 250 mil indica un "
                        "mercado laboral sano; sostenidamente sobre 300 mil indica "
                        "deterioro real.",
                        "*Ojo con feriados y estacionalidad:* semanas cortas o cierres "
                        "de planta distorsionan el dato puntual."]},
        ],
    },
    {
        "tipo": "tabla",
        "titulo": "Los complementarios: qué aportan y qué no",
        "bajada": "No mueven el mercado por sí solos, pero *completan el cuadro*. "
                  "Conocerlos te permite explicar por qué el mercado se movió sin un "
                  "dato grande.",
        "seccion": SEC_1,
        "color": AZUL,
        "encabezados": ["Indicador", "Qué mide", "Cómo se interpreta"],
        "pesos": [2.4, 3.4, 4.2],
        "filas": [
            ["Vacantes de empleo\n(JOLTS)", "Cuántos puestos están abiertos sin llenar",
             "Mide la *demanda* de trabajo. El banco central mira cuántas vacantes hay "
             "por cada desocupado: si sobran vacantes, hay presión sobre los sueldos"],
            ["Empleo privado ADP", "Empleo del sector privado, según una procesadora "
             "de nóminas",
             "Sale dos días antes que el informe oficial, pero *su correlación mes a "
             "mes es baja*. Sirve de referencia, no de pronóstico"],
            ["Confianza del\nconsumidor", "Cómo ve su situación y su futuro el "
             "consumidor",
             "Su valor está en el sub-índice de *expectativas de inflación*: si la "
             "gente espera más inflación, la exige en sueldos y se vuelve profecía "
             "autocumplida"],
            ["Pedidos de bienes\ndurables", "Pedidos de productos que duran años "
             "(maquinaria, autos)",
             "Mide *inversión empresarial*: si las empresas piden maquinaria, esperan "
             "vender. Muy volátil por los pedidos de aviones: mírese sin transporte"],
        ],
    },
    {
        "tipo": "tabla",
        "titulo": "Jerarquía: cuáles pesan más, y por qué",
        "bajada": "La pregunta de Hari. La respuesta corta: *el peso no es fijo*. "
                  "Depende de qué problema le preocupa al mercado en ese momento.",
        "seccion": SEC_1,
        "color": VERDE,
        "encabezados": ["Nivel de impacto", "Indicadores", "Razón de su peso"],
        "pesos": [2.2, 4.0, 3.8],
        "filas": [
            ["Máximo", "Decisión de tasas y su comunicado · IPC · Informe de empleo",
             "Definen o determinan directamente la tasa de interés, que es el precio "
             "del dinero"],
            ["Alto", "PCE subyacente · ISM de servicios · Ventas minoristas "
             "(grupo de control)",
             "Son la vara oficial de la meta, el adelanto del sector más grande y el "
             "pulso del consumo"],
            ["Medio", "PIB (primera estimación) · IPP · ISM manufacturero · "
             "Peticiones de subsidio",
             "Confirman o anticipan, pero no cambian el escenario por sí solos"],
            ["Bajo", "ADP · confianza · bienes durables · índices regionales",
             "Aportan matices; mueven solo si sorprenden de forma extraordinaria"],
        ],
        "nota": ("La regla que hay que llevarse: manda el régimen",
                 "Cuando el problema del mercado es *la inflación*, el IPC manda y un "
                 "empleo fuerte se lee como amenaza. Cuando el problema es *la "
                 "recesión*, el empleo manda y un empleo fuerte se celebra. *Antes de "
                 "interpretar un dato, define qué le preocupa hoy al mercado.*"),
    },
    {
        "tipo": "bullets",
        "titulo": "Cuando los datos se contradicen: cómo se resuelve",
        "bajada": "La otra pregunta de Hari. Los resultados mixtos son *la norma*, no "
                  "la excepción, y hay reglas de prioridad para leerlos.",
        "seccion": SEC_1,
        "color": AMBAR,
        "puntos": [
            ("Regla 1 · El subyacente manda sobre el general",
             "Porque el general lo mueven energía y alimentos, que la tasa de interés "
             "*no puede controlar*. Si el general sorprende y el subyacente no, el "
             "movimiento suele revertirse."),
            ("Regla 2 · Lo mensual manda sobre lo anual en el corto plazo",
             "Porque la cifra anual arrastra el efecto base, que ya era conocido. Lo "
             "mensual es lo *nuevo*."),
            ("Regla 3 · Manda el dato que habla del problema del momento",
             "Es la regla del régimen. En un mercado preocupado por la inflación, un "
             "empleo fuerte con salarios contenidos se lee *bien*; con salarios al alza, "
             "se lee *mal*."),
            ("Regla 4 · Si dos partes del mismo informe se contradicen, no operes el "
             "primer minuto",
             "El mercado reacciona primero al titular y después al detalle. Es el patrón "
             "*reacción y reversión*: es donde más pierde quien opera por reflejo."),
        ],
        "clave": ("Cómo se ve esto en la práctica",
                  "Nóminas muy sobre lo esperado, pero desempleo que *sube* y salarios "
                  "*en línea*. Parece contradictorio y no lo es: entró más gente a "
                  "buscar trabajo. Es *crecimiento sin presión inflacionaria* — el mejor "
                  "escenario posible. El titular dice «economía recalentada»; el detalle "
                  "dice lo contrario, y *el detalle tiene razón*."),
    },

    # ==================================================================================
    # BLOQUE 2 — CHILE
    # ==================================================================================
    {
        "tipo": "seccion",
        "numero": "2",
        "titulo": "Indicadores de Chile",
        "bajada": "El dólar en Chile tiene *dos motores*: lo que pasa con el dólar en "
                  "el mundo y lo que pasa acá. Este bloque cubre el segundo.",
        "color": AMBAR,
    },
    {
        "tipo": "tabla",
        "titulo": "Quién publica qué en Chile",
        "bajada": "Dos instituciones concentran todo. Conocer el reparto evita buscar "
                  "en la fuente equivocada.",
        "seccion": SEC_2,
        "color": AMBAR,
        "encabezados": ["Indicador", "Institución", "Cuándo", "Qué responde"],
        "pesos": [2.4, 2.2, 2.2, 3.0],
        "filas": [
            ["Inflación (IPC)", "Instituto Nacional de Estadísticas",
             "Alrededor del día 8 · 08:00", "¿Suben los precios?"],
            ["Actividad mensual\n(IMACEC)", "Banco Central",
             "Primeros días del mes · 08:30", "¿Crece la economía este mes?"],
            ["PIB trimestral", "Banco Central", "Mes siguiente al trimestre",
             "¿Cuánto creció en el trimestre?"],
            ["Desempleo", "Instituto Nacional de Estadísticas",
             "Fin de mes · 08:00", "¿Hay trabajo?"],
            ["Balanza comercial", "Banco Central", "Primeros días del mes · 08:30",
             "¿Entran o salen dólares del país?"],
            ["Tasa de política\nmonetaria (TPM)", "Banco Central",
             "8 reuniones al año · 18:00", "¿Cuánto cuesta el dinero en Chile?"],
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "IPC de Chile",
        "bajada": "Mismo concepto que el de Estados Unidos, pero *la dirección del "
                  "efecto sobre el dólar es la inversa*. Acá está el detalle que más se "
                  "confunde.",
        "seccion": SEC_2,
        "color": AMBAR,
        "meta": [
            ("Quién lo publica", "Instituto Nacional de Estadísticas"),
            ("Cuándo", "Alrededor del día 8 · 08:00 Chile"),
            ("Meta del Banco Central", "3% anual, con tolerancia de ±1 punto"),
            ("Frecuencia", "Mensual"),
        ],
        "bloques": [
            ("cómo se lee",
             ["Se publica la variación *mensual* y la *acumulada en doce meses*; la "
              "segunda es la que se compara contra la meta de 3%.",
              "También tiene versiones *sin volátiles*, que cumplen el mismo rol que el "
              "subyacente estadounidense.",
              "*Contexto local que importa:* buena parte de la canasta chilena depende "
              "de bienes importados, así que *un dólar más alto se traduce en más "
              "inflación* unos meses después. Se le llama traspaso del tipo de cambio.",
              "Eso genera un círculo que conviene tener claro: dólar sube → inflación "
              "sube → el Banco Central endurece → el peso se fortalece."]),
            ("qué debería hacer el USD/CLP, y por qué",
             ["*Cuidado con la dirección:* en el par USD/CLP, cuando el número sube "
              "significa que *el peso se debilita*.",
              "*IPC sobre lo esperado* → el Banco Central *no puede bajar* la tasa, o "
              "incluso debe subirla → tener pesos paga más → *el USD/CLP baja* ⬇️.",
              "*IPC bajo lo esperado* → se abre espacio para *recortar* la tasa → los "
              "pesos rinden menos → *el USD/CLP sube* ⬆️.",
              "*Es el efecto espejo del caso estadounidense:* allá una inflación alta "
              "*fortalece* al dólar; acá una inflación alta *fortalece al peso*, y por "
              "eso el par baja.",
              "*Magnitud:* el efecto local suele ser menor que el del dólar global. Si "
              "los dos motores apuntan en direcciones opuestas, normalmente gana el "
              "global."]),
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "IMACEC: el termómetro mensual de la economía chilena",
        "bajada": "No existe un equivalente exacto en Estados Unidos, y es el "
                  "indicador de actividad más seguido del país.",
        "seccion": SEC_2,
        "color": AMBAR,
        "meta": [
            ("Nombre completo", "Índice mensual de actividad económica"),
            ("Quién lo publica", "Banco Central de Chile"),
            ("Cuándo", "Primeros días del mes · 08:30"),
            ("Cobertura", "Cerca del 90% de los bienes y servicios del PIB"),
        ],
        "bloques": [
            ("por qué existe y qué mide",
             ["El PIB se publica *cada tres meses*: para conducir la política monetaria "
              "eso es demasiado lento.",
              "El IMACEC resuelve ese problema estimando *mensualmente* la actividad, "
              "cubriendo cerca del 90% de lo que después mide el PIB.",
              "Se compara contra *el mismo mes del año anterior*, así que le aplica "
              "todo lo que vimos sobre el efecto base.",
              "*Ventaja para nosotros:* llega temprano y con alta frecuencia. Cuando "
              "sale el PIB trimestral, el IMACEC ya lo había anticipado casi por "
              "completo — por eso el PIB chileno mueve poco."]),
            ("el desglose que hay que mirar",
             ["*IMACEC minero y no minero:* la distinción clave.",
              "El minero depende del precio del cobre y de la producción de las faenas: "
              "puede subir por razones que *no dicen nada* de la economía interna.",
              "El *no minero* es el que refleja de verdad la demanda interna: comercio, "
              "servicios, industria.",
              "*Qué debería hacer el precio:* IMACEC sobre lo esperado → economía "
              "sólida y menos urgencia de recortar la tasa → *el USD/CLP baja* ⬇️. "
              "IMACEC decepcionante → más presión para recortar → *el USD/CLP sube* ⬆️.",
              "*Matiz importante:* si el IMACEC sube *solo por minería*, el efecto sobre "
              "el peso es más débil de lo que sugeriría el titular."]),
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "Empleo, precios al productor y PIB en Chile",
        "bajada": "Tres indicadores que se leen con lo que ya sabes. Lo relevante acá "
                  "es *cómo cambia su interpretación* por la forma en que se publican.",
        "seccion": SEC_2,
        "color": AMBAR,
        "cajas": [
            {"kicker": "Fin de mes · 08:00", "titulo": "Tasa de desempleo",
             "color": AMBAR,
             "lineas": ["Mismo concepto que en EE.UU. —incluida la trampa de la "
                        "participación—, con una diferencia de forma importante.",
                        "*Se publica como trimestre móvil:* el promedio de los últimos "
                        "tres meses.",
                        "Consecuencia: *cambia lento y suaviza los giros*. No esperes "
                        "que reaccione rápido a un shock.",
                        "*Efecto:* desempleo alto → presión para recortar la tasa → "
                        "*USD/CLP sube* ⬆️."]},
            {"kicker": "Mensual", "titulo": "IPC del productor (IPP)",
             "color": GRIS,
             "lineas": ["Mismo concepto que su par estadounidense: precios de fábrica "
                        "antes del consumidor.",
                        "*El mercado local lo sigue mucho menos* que el IPC, así que "
                        "rara vez mueve el tipo de cambio por sí solo.",
                        "*Dónde sí es útil:* como adelanto de costos, y para "
                        "anticipar presiones sobre el IPC de los meses siguientes.",
                        "Úsalo como contexto, no como detonante."]},
            {"kicker": "Trimestral", "titulo": "PIB",
             "color": GRIS,
             "lineas": ["La medición completa de la economía, con la misma estructura "
                        "de cuatro patas que vimos para EE.UU.",
                        "*Suele mover poco*, por una razón que ya conoces: el IMACEC "
                        "mensual ya lo adelantó.",
                        "*Su valor está en el relato* y en las proyecciones: alimenta "
                        "las estimaciones del Informe de Política Monetaria.",
                        "Trátalo como *confirmación*, no como noticia."]},
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "Balanza comercial y el cobre",
        "bajada": "Si tuvieras que elegir *un solo* driver local del dólar en Chile, "
                  "sería este. Y es el que conecta a Chile con China.",
        "seccion": SEC_2,
        "color": VERDE,
        "meta": [
            ("Quién lo publica", "Banco Central de Chile"),
            ("Cuándo", "Primeros días del mes · 08:30"),
            ("Qué es", "Exportaciones menos importaciones"),
            ("Peso del cobre", "Cerca de la mitad de las exportaciones"),
        ],
        "bloques": [
            ("el mecanismo, paso a paso",
             ["Cuando Chile exporta, el comprador paga en *dólares*. Para gastar ese "
              "dinero en el país, hay que *venderlo y comprar pesos*.",
              "Más exportaciones → *más oferta de dólares* en el mercado local → el "
              "dólar se abarata → *el USD/CLP baja*.",
              "Un *superávit* (se exporta más de lo que se importa) presiona el dólar a "
              "la baja. Un *déficit* lo presiona al alza.",
              "Y como el cobre es cerca de la mitad de lo que Chile exporta, *el precio "
              "del cobre es, en la práctica, el driver de esa oferta de dólares*."]),
            ("por qué el peso chileno se mueve con el cobre",
             ["El peso es una de las monedas del mundo *más correlacionadas con el "
              "cobre*. No es casualidad: es su principal fuente de divisas.",
              "*Cobre sube* → entran más dólares → *USD/CLP baja* ⬇️.",
              "*Cobre baja* → entran menos dólares → *USD/CLP sube* ⬆️.",
              "Por eso el operador de USD/CLP mira el cobre *tanto como* mira el dólar "
              "global. Son los dos motores del par.",
              "*Y por eso los datos de China nos importan directamente:* China es el "
              "principal comprador del cobre chileno. Lo desarrollamos en el bloque de "
              "contexto global."]),
        ],
    },
    {
        "tipo": "ficha",
        "titulo": "Tasa de política monetaria (TPM) y el diferencial de tasas",
        "bajada": "El resultado de todo lo anterior: cada dato chileno termina "
                  "empujando esta decisión.",
        "seccion": SEC_2,
        "color": AMBAR,
        "meta": [
            ("Quién decide", "Consejo del Banco Central de Chile"),
            ("Cuándo", "8 reuniones al año · comunicado 18:00"),
            ("El informe clave", "IPoM, cuatro veces al año"),
            ("Su mandato", "Inflación en 3% y estabilidad financiera"),
        ],
        "bloques": [
            ("qué es y cómo se comunica",
             ["Es *la tasa a la que se presta el dinero entre bancos* en Chile, y el "
              "Banco Central la fija. De ella cuelgan todas las demás tasas del país.",
              "El comunicado de la decisión *importa tanto como la decisión*: en él se "
              "señala hacia dónde irá la tasa. El mercado opera esa señal.",
              "El *Informe de Política Monetaria (IPoM)* trae las proyecciones de "
              "inflación y crecimiento, y puede mover el tipo de cambio *más que la "
              "decisión misma*.",
              "*Efecto directo:* si sube la TPM, tener pesos rinde más → *el USD/CLP "
              "baja* ⬇️. Si la baja, ocurre lo contrario ⬆️."]),
            ("el diferencial de tasas: el concepto que amarra todo",
             ["El capital busca rendimiento. Lo que importa no es la tasa chilena en "
              "sí, sino *la diferencia entre la tasa de Chile y la de Estados Unidos*.",
              "*Si la Reserva Federal tiene tasas más altas que el Banco Central de "
              "Chile*, conviene tener dólares antes que pesos → sale capital → *el "
              "USD/CLP sube* ⬆️.",
              "*Si el diferencial se estrecha a favor de Chile* → conviene tener pesos "
              "→ entra capital → *el USD/CLP baja* ⬇️.",
              "*Consecuencia práctica:* el USD/CLP puede moverse fuerte *sin que salga "
              "ningún dato chileno*, solo porque cambió la expectativa sobre la tasa "
              "estadounidense.",
              "Por eso, para operar el dólar en Chile hay que seguir *los datos de "
              "Estados Unidos* con la misma atención que los locales."]),
        ],
    },

    # ==================================================================================
    # BLOQUE 3 — POLÍTICA MONETARIA
    # ==================================================================================
    {
        "tipo": "seccion",
        "numero": "3",
        "titulo": "Cómo los datos deciden las tasas",
        "bajada": "Todo lo anterior converge acá. Este es el bloque que responde *por "
                  "qué* un dato mueve el precio, y no solo *cuánto*.",
        "color": VERDE,
    },
    {
        "tipo": "cajas",
        "titulo": "Qué es una tasa de política monetaria",
        "bajada": "Antes de conectar los datos con la tasa, hay que tener claro qué es "
                  "la tasa y qué puede hacer.",
        "seccion": SEC_3,
        "cajas": [
            {"kicker": "Qué es", "titulo": "El precio del dinero",
             "color": VERDE,
             "lineas": ["Es la tasa de referencia que fija el banco central, y de ella "
                        "cuelgan todas las demás: créditos, hipotecas, depósitos.",
                        "*No la fija el mercado: la decide un comité*, mirando datos.",
                        "En Estados Unidos la decide el comité de la Reserva Federal, "
                        "ocho veces al año. En Chile, el Consejo del Banco Central, "
                        "también ocho veces."]},
            {"kicker": "Cómo funciona", "titulo": "Enfría o calienta la demanda",
             "color": AZUL,
             "lineas": ["*Tasa alta* → el crédito se encarece → se consume e invierte "
                        "menos → la demanda cae → *los precios dejan de subir tan "
                        "rápido*. El costo es menos crecimiento y más desempleo.",
                        "*Tasa baja* → el crédito se abarata → se consume e invierte "
                        "más → la economía se activa. El riesgo es *más inflación*.",
                        "Es un balancín: no se puede tener las dos cosas al mismo "
                        "tiempo."]},
            {"kicker": "Su límite", "titulo": "Actúa con retraso y no lo controla todo",
             "color": AMBAR,
             "lineas": ["*Actúa con retraso:* una subida de tasa tarda meses en "
                        "reflejarse en los precios. El banco central decide *mirando "
                        "hacia adelante*, no el dato de hoy.",
                        "*No controla la oferta:* no puede bajar el precio del petróleo "
                        "ni arreglar una sequía. Solo actúa sobre la demanda.",
                        "*De ahí que mire el subyacente:* es la parte de la inflación "
                        "sobre la que su herramienta *sí* tiene efecto."]},
        ],
        "nota": ("Por qué esto explica la reacción del mercado",
                 "Como la tasa actúa con retraso, el mercado no espera la decisión: "
                 "*cotiza la probabilidad* de que ocurra. Cada dato mueve esa "
                 "probabilidad, y ese movimiento es lo que ves en el precio *el mismo "
                 "día del dato*, meses antes de la reunión."),
    },
    {
        "tipo": "cajas",
        "titulo": "El doble mandato, y por qué genera tensión",
        "bajada": "La Reserva Federal persigue *dos objetivos a la vez*, y a veces se "
                  "contradicen. Ahí es donde la lectura de datos se vuelve interesante.",
        "seccion": SEC_3,
        "cajas": [
            {"kicker": "Mandato 1", "titulo": "Máximo empleo",
             "color": VERDE,
             "lineas": ["Que haya el mayor nivel de empleo *sostenible*.",
                        "Se vigila con: nóminas, tasa de desempleo, participación, "
                        "vacantes, peticiones de subsidio.",
                        "No hay una cifra objetivo pública, a diferencia de la "
                        "inflación."]},
            {"kicker": "Mandato 2", "titulo": "Precios estables",
             "color": AZUL,
             "lineas": ["Meta explícita: *2% anual* medido en el gasto en consumo "
                        "personal subyacente.",
                        "Se vigila con: PCE, IPC, IPP, salarios, expectativas de "
                        "inflación.",
                        "Es el mandato *con número*, y por eso el más fácil de evaluar "
                        "desde fuera."]},
            {"kicker": "La tensión", "titulo": "Los dos objetivos chocan",
             "color": AMBAR,
             "lineas": ["Para bajar la inflación hay que enfriar la economía… y eso "
                        "*destruye empleo*.",
                        "Para proteger el empleo hay que estimular… y eso *aviva la "
                        "inflación*.",
                        "*Lo que hay que leer en cada dato:* a cuál de los dos mandatos "
                        "le está hablando, y si le da al comité una razón para "
                        "*apretar* o para *aflojar*.",
                        "*Comparación útil:* el Banco Central de Chile tiene un mandato "
                        "*centrado en la inflación* (3%), no un doble mandato "
                        "simétrico. Por eso reacciona distinto ante los mismos datos."]},
        ],
    },
    {
        "tipo": "tabla",
        "titulo": "De la lectura del dato a la dirección del precio",
        "bajada": "La tabla de síntesis. *No la memorices*: verifica que puedas "
                  "reconstruir cada fila con la cadena de transmisión.",
        "seccion": SEC_3,
        "color": VERDE,
        "encabezados": ["Lectura del dato", "Qué implica para la tasa", "Dólar",
                        "Oro", "Nasdaq 100", "USD/CLP"],
        "pesos": [3.0, 3.0, 1.2, 1.1, 1.5, 1.4],
        "filas": [
            ["Inflación sobre lo esperado", "Tasa alta por más tiempo",
             "Sube ⬆️", "Baja ⬇️", "Baja ⬇️", "Sube ⬆️"],
            ["Inflación bajo lo esperado", "Se abre espacio a recortes",
             "Baja ⬇️", "Sube ⬆️", "Sube ⬆️", "Baja ⬇️"],
            ["Empleo muy fuerte\n(régimen de inflación)", "Retrasa los recortes",
             "Sube ⬆️", "Baja ⬇️", "Baja ⬇️", "Sube ⬆️"],
            ["Empleo muy débil\n(régimen de recesión)", "Adelanta los recortes",
             "Baja ⬇️", "Sube ⬆️", "Mixto", "Sube ⬆️"],
            ["Actividad sobre lo esperado", "Menos urgencia de estimular",
             "Sube ⬆️", "Baja ⬇️", "Sube ⬆️", "Sube ⬆️"],
            ["Cobre o PMI de China al alza", "Sin efecto directo en la Fed",
             "—", "Sube ⬆️", "—", "Baja ⬇️"],
        ],
        "nota": ("Las dos filas que parecen inconsistentes, y no lo son",
                 "Con *empleo muy débil* el Nasdaq queda «mixto»: la tasa más baja lo "
                 "favorece, pero una recesión daña las ganancias de las empresas. Y con "
                 "*actividad fuerte* el Nasdaq sube aunque el dólar también: ahí pesa "
                 "más la expectativa de mejores resultados. *Cuando dos fuerzas "
                 "compiten, hay que decidir cuál domina — eso es interpretar.*"),
    },
    {
        "tipo": "cajas",
        "titulo": "Los cuatro escenarios: crecimiento contra inflación",
        "bajada": "Cualquier combinación de datos cae en uno de estos cuatro cuadrantes. "
                  "Ubicarlo es *el resumen ejecutivo* de tu lectura del mes.",
        "seccion": SEC_3,
        "cajas": [
            {"kicker": "Crece + inflación baja",
             "titulo": "El escenario ideal", "color": VERDE,
             "lineas": ["La economía crece *sin* generar presión de precios. Se le "
                        "llama «ricitos de oro»: ni muy caliente ni muy frío.",
                        "El banco central puede *recortar sin riesgo*.",
                        "*Bolsas:* el mejor de los escenarios ⬆️⬆️.",
                        "*Dólar:* tiende a debilitarse ⬇️. *Oro:* sube ⬆️. "
                        "*USD/CLP:* baja ⬇️."]},
            {"kicker": "Crece + inflación alta",
             "titulo": "Economía recalentada", "color": AMBAR,
             "lineas": ["La demanda supera a la oferta y empuja los precios.",
                        "El banco central debe *apretar*: subir la tasa o mantenerla "
                        "alta más tiempo.",
                        "*Bolsas:* bajo presión ⬇️, aunque las ganancias sean buenas.",
                        "*Dólar:* se fortalece ⬆️. *Oro:* baja ⬇️. "
                        "*USD/CLP:* sube ⬆️."]},
            {"kicker": "Se contrae + inflación baja",
             "titulo": "Recesión con desinflación", "color": AZUL,
             "lineas": ["La actividad cae y arrastra los precios con ella.",
                        "El banco central *recorta rápido* para reactivar.",
                        "*Bolsas:* primero caen por las ganancias, luego suben por la "
                        "tasa. Secuencia en dos tiempos.",
                        "*Dólar:* baja ⬇️, aunque puede subir por refugio. *Oro:* sube "
                        "⬆️. *USD/CLP:* sube ⬆️ por aversión al riesgo."]},
            {"kicker": "Se contrae + inflación alta",
             "titulo": "Estanflación", "color": ROJO,
             "lineas": ["El peor cuadrante: actividad débil *y* precios altos.",
                        "El banco central queda *atrapado*: si recorta, aviva la "
                        "inflación; si sube, profundiza la recesión.",
                        "*Bolsas:* el peor escenario ⬇️⬇️.",
                        "*Oro:* suele ser el gran beneficiado ⬆️⬆️, por refugio. "
                        "*USD/CLP:* sube ⬆️."]},
        ],
    },
    {
        "tipo": "bullets",
        "titulo": "El camino a la decisión: cómo se arma el escenario",
        "bajada": "La idea que hay que transmitirle al cliente: *cada dato es una pieza "
                  "de un rompecabezas* que se completa el día de la reunión.",
        "seccion": SEC_3,
        "puntos": [
            ("El mercado no espera la reunión: cotiza su probabilidad",
             "Existe un mercado de futuros donde se transa la expectativa de tasa. De "
             "ahí salen las frases del tipo «el mercado asigna 70% de probabilidad a un "
             "recorte»."),
            ("Cada dato mueve esa probabilidad, y la probabilidad mueve el precio",
             "Un IPC alto puede bajar la probabilidad de recorte de 70% a 40%. Ese "
             "cambio *es* el movimiento del dólar de ese día. No hay que esperar la "
             "reunión para verlo."),
            ("Por eso el orden del mes importa",
             "Los primeros datos *instalan* una hipótesis; los siguientes la confirman o "
             "la desmienten. Un IPC alto tras un empleo débil pesa distinto que tras un "
             "empleo fuerte."),
            ("Y por eso el comunicado puede mover más que la decisión",
             "Si la decisión ya estaba descontada al 95%, no queda sorpresa en ella. La "
             "sorpresa está en *lo que se dice sobre lo que viene*: es el mismo "
             "principio de «ya está en el precio», aplicado a las palabras."),
        ],
        "clave": ("La frase para el cliente",
                  "«Los datos económicos son piezas que van armando el camino hacia la "
                  "decisión de tasas. Por eso los seguimos uno por uno: cuando llega el "
                  "día de la reunión, el mercado ya se movió.»"),
    },

    # ==================================================================================
    # BLOQUE 4 — CONTEXTO GLOBAL
    # ==================================================================================
    {
        "tipo": "seccion",
        "numero": "4",
        "titulo": "Contexto global",
        "bajada": "Dos referencias que no son datos de un país, sino *termómetros del "
                  "sistema*: el índice del dólar y la actividad de China.",
        "color": AZUL,
    },
    {
        "tipo": "ficha",
        "titulo": "Índice del dólar (Dollar Index o DXY)",
        "bajada": "No es un dato económico: es *un precio*. Y es la variable que "
                  "conecta todo lo que operamos.",
        "seccion": SEC_4,
        "color": AZUL,
        "meta": [
            ("Qué es", "El valor del dólar contra una canasta de monedas"),
            ("Cuántas monedas", "Seis"),
            ("Referencia", "Base 100 = valor de la canasta en 1973"),
            ("Cotiza", "En continuo, no en publicaciones"),
        ],
        "bloques": [
            ("cómo está construido, y qué implica esa construcción",
             ["Mide el dólar contra seis monedas, con pesos *muy desiguales*:",
              "*Euro: cerca del 58%.* Yen japonés: 14%. Libra esterlina: 12%. Dólar "
              "canadiense: 9%. Corona sueca: 4%. Franco suizo: 4%.",
              "*Consecuencia crítica:* el índice es, en la práctica, *tres cuartas "
              "partes Europa*. Cuando sube, muchas veces lo que ocurrió es que *el euro "
              "se debilitó*, no que el dólar se fortaleciera frente a todo.",
              "*Y lo que NO incluye:* el yuan chino, el peso mexicano, el real "
              "brasileño, el peso chileno. Ninguna moneda emergente.",
              "Por eso puede subir mientras el dólar *cae* frente a las monedas de "
              "América Latina. No es una contradicción: mide otra cosa."]),
            ("cómo se interpreta",
             ["*Lo que importa es la dirección, no el nivel:* el 100 es un valor "
              "histórico de referencia, no una frontera con significado.",
              "*La regla del espejo:* casi todo lo que operamos se cotiza en dólares, "
              "así que si el dólar vale más, se necesitan *menos* dólares por unidad de "
              "activo.",
              "*DXY sube* → oro baja ⬇️, petróleo baja ⬇️, cobre baja ⬇️, USD/CLP "
              "sube ⬆️, monedas emergentes se debilitan.",
              "*DXY baja* → exactamente lo contrario.",
              "*Cuándo la regla se rompe:* en episodios de pánico, el dólar y el oro "
              "*suben juntos*, porque los dos son refugio. Ahí no manda la mecánica del "
              "tipo de cambio, sino el flujo hacia la seguridad. *Reconocer cuándo estás "
              "en ese régimen es parte de interpretar bien.*"]),
        ],
    },
    {
        "tipo": "cajas",
        "titulo": "PMI de China: por qué hay dos y qué dice su diferencia",
        "bajada": "Ya sabes leer un índice de difusión. Lo que hay que entender acá es "
                  "*por qué se publican dos versiones* y qué información hay en el "
                  "contraste.",
        "seccion": SEC_4,
        "color": AZUL,
        "cajas": [
            {"kicker": "Versión oficial", "titulo": "PMI de la Oficina Nacional de "
                                                   "Estadísticas",
             "color": ROJO,
             "lineas": ["Lo publica *el Estado chino*.",
                        "Su muestra se concentra en *empresas grandes y estatales*.",
                        "Sale a fin de mes o el día 1, a las *21:30 de Chile*.",
                        "Refleja bien el efecto del *estímulo público*, que llega "
                        "primero a las empresas grandes."]},
            {"kicker": "Versión privada", "titulo": "PMI Caixin",
             "color": AMBAR,
             "lineas": ["Lo publica un medio financiero privado.",
                        "Su muestra se concentra en *empresas medianas, pequeñas y "
                        "exportadoras*.",
                        "Sale uno o dos días después, a las *21:45 de Chile*.",
                        "Refleja mejor la *demanda real de mercado* y el pulso "
                        "exportador."]},
            {"kicker": "La lectura conjunta", "titulo": "El contraste es la información",
             "color": VERDE,
             "lineas": ["*Los dos sobre 50* → expansión amplia y creíble.",
                        "*Los dos bajo 50* → contracción confirmada. Señal fuerte.",
                        "*Oficial sube y Caixin baja* → el estímulo estatal funciona en "
                        "las grandes, *pero no llega a las pymes*. Recuperación frágil.",
                        "*Oficial baja y Caixin sube* → la demanda de mercado repunta "
                        "*sin* apoyo público. Más sano, aunque menos frecuente.",
                        "Leer solo uno de los dos es perder la mitad del mensaje."]},
        ],
        "nota": ("Un detalle de horario que hay que tener presente",
                 "China está *doce horas adelante* de Chile, así que estos datos salen "
                 "cerca de las *21:30 de la noche anterior* a la fecha de su "
                 "calendario. Cuando abrimos la jornada, el movimiento *ya empezó*: "
                 "nuestro trabajo es evaluar si el mercado ya lo incorporó o si queda "
                 "recorrido."),
    },
    {
        "tipo": "bullets",
        "titulo": "Por qué un dato de China mueve el dólar en Chile",
        "bajada": "La cadena completa, eslabón por eslabón. Es el ejemplo más claro de "
                  "que interpretar es *seguir un mecanismo*, no memorizar una "
                  "correlación.",
        "seccion": SEC_4,
        "color": VERDE,
        "puntos": [
            ("Eslabón 1 · China es el mayor consumidor de cobre del mundo",
             "Su construcción, su infraestructura y su manufactura eléctrica absorben "
             "una parte enorme de la producción mundial."),
            ("Eslabón 2 · El PMI anticipa esa demanda",
             "Si los gerentes de compra chinos reportan menos actividad, van a comprar "
             "*menos insumos*. El cobre es uno de los principales."),
            ("Eslabón 3 · Menos demanda esperada baja el precio del cobre",
             "El cobre cotiza globalmente y responde a expectativas, no solo a compras "
             "concretadas."),
            ("Eslabón 4 · Chile recibe menos dólares",
             "El cobre es cerca de la mitad de las exportaciones chilenas. Si baja de "
             "precio, entra menos moneda extranjera al país."),
            ("Eslabón 5 · El dólar se encarece frente al peso",
             "Menos oferta de dólares en el mercado local → *el USD/CLP sube* ⬆️. Y se "
             "suma el efecto de aversión al riesgo, que castiga a las monedas "
             "emergentes."),
        ],
        "clave": ("La misma cadena, para el petróleo",
                  "China es también el mayor importador de crudo del mundo. Un PMI "
                  "chino débil implica *menos demanda de energía* → el petróleo WTI "
                  "baja ⬇️. Es el mismo mecanismo aplicado a otro insumo: *entendida la "
                  "cadena, se puede reconstruir para cualquier materia prima*."),
    },

    # ==================================================================================
    # BLOQUE 5 — PRÁCTICA
    # ==================================================================================
    {
        "tipo": "seccion",
        "numero": "5",
        "titulo": "Interpretar en la práctica",
        "bajada": "Tres publicaciones para leer de principio a fin, el método de "
                  "lectura en seis pasos y los errores que hay que evitar.",
        "color": AMBAR,
    },
    {
        "tipo": "ejercicio",
        "titulo": "Ejercicio 1 · La inflación sorprende al alza",
        "seccion": SEC_5,
        "dato": [
            "*Índice de precios al consumidor de EE.UU.*",
            "*Subyacente mensual*",
            "Anterior: 0,2%  ·  Esperado: 0,2%",
            "*Efectivo: 0,4%*  🔥",
            "",
            "*Subyacente anual*",
            "Anterior: 3,1%  ·  Esperado: 3,1%",
            "*Efectivo: 3,3%*",
            "",
            "*General mensual*",
            "Esperado: 0,3%  ·  Efectivo: 0,4%",
            "",
            "Cifras ilustrativas: no corresponden a una publicación real.",
        ],
        "lectura": [
            "*Paso 1 — la sorpresa:* el subyacente mensual salió *al doble* de lo "
            "esperado. Es la cifra que más pesa, así que la sorpresa es de las grandes.",
            "*Paso 2 — ¿es de fondo?* Sí: *general y subyacente sorprenden en la misma "
            "dirección*. No fue energía ni un alimento puntual — la presión está en el "
            "núcleo de la canasta.",
            "*Paso 3 — el anual confirma:* subió en vez de bajar. Aunque hubiera efecto "
            "base favorable, no alcanzó a compensar.",
            "*Conclusión:* la inflación *no está cediendo*, y la presión es amplia. Se "
            "aleja la posibilidad de que el banco central baje la tasa.",
        ],
        "precio": [
            "*Dólar (DXY): sube* ⬆️ — tasa alta por más tiempo significa mayor "
            "rendimiento, y el capital va donde le pagan más.",
            "*Oro: baja* ⬇️ — no paga interés; si los bonos rinden más, pierde "
            "atractivo relativo. Y un dólar más caro lo encarece para el resto del "
            "mundo.",
            "*Nasdaq 100: baja* ⬇️ — vale por ganancias futuras, y a tasa más alta esas "
            "ganancias valen menos hoy.",
            "*USD/CLP: sube* ⬆️ — dólar global fuerte y menos apetito por riesgo "
            "emergente.",
            "*Temporalidad del impacto:* intradía a swing de jornada (uno a tres días).",
        ],
    },
    {
        "tipo": "ejercicio",
        "titulo": "Ejercicio 2 · Un informe de empleo contradictorio",
        "seccion": SEC_5,
        "dato": [
            "*Informe de empleo de EE.UU.*",
            "",
            "*Nóminas no agrícolas*",
            "Esperado: 160 mil",
            "*Efectivo: 250 mil*  🔥",
            "",
            "*Tasa de desempleo*",
            "Anterior: 4,1%  ·  Esperado: 4,1%",
            "*Efectivo: 4,3%*  🔥",
            "",
            "*Salario por hora, anual*",
            "Esperado: 3,4%  ·  Efectivo: 3,4%",
            "",
            "*Tasa de participación:* sube de 62,4% a 62,8%",
            "",
            "Cifras ilustrativas: no corresponden a una publicación real.",
        ],
        "lectura": [
            "*Paso 1 — la contradicción aparente:* se crearon muchos más empleos de lo "
            "esperado, *y sin embargo* el desempleo subió. Parece imposible.",
            "*Paso 2 — la trampa de la participación, al revés:* la participación "
            "*subió* 0,4 puntos. Entró más gente a buscar trabajo, y eso agranda el "
            "denominador de la tasa. Por eso sube el desempleo aunque haya más empleos.",
            "*Paso 3 — el árbitro son los salarios:* salieron *exactamente en línea*. "
            "No hay presión de costos laborales, o sea *no hay amenaza inflacionaria*.",
            "*Conclusión:* es *crecimiento sin recalentamiento* — la economía atrae "
            "trabajadores y los absorbe sin empujar los sueldos. Un buen escenario, "
            "aunque el titular sugiera lo contrario.",
        ],
        "precio": [
            "*Reacción de los primeros segundos:* el dólar *sube* ⬆️ y las bolsas "
            "*bajan* ⬇️, porque los algoritmos leen el titular de nóminas.",
            "*Reacción al leer el detalle:* *reversión*. El dólar devuelve la subida y "
            "las bolsas recuperan, porque los salarios contenidos descartan la amenaza "
            "de inflación.",
            "*Escenario resultante:* favorable para las bolsas ⬆️ y de dólar sin "
            "dirección clara.",
            "*La enseñanza operativa:* con un dato mixto, *el primer minuto es ruido*. "
            "Quien opera el titular queda del lado equivocado de la reversión.",
            "*Temporalidad:* intradía; la lectura de fondo, swing de jornada.",
        ],
    },
    {
        "tipo": "ejercicio",
        "titulo": "Ejercicio 3 · China se contrae y llega a Chile",
        "seccion": SEC_5,
        "dato": [
            "*Índices de gerentes de compra de China*",
            "",
            "*PMI manufacturero oficial*",
            "Anterior: 50,3  ·  Esperado: 50,1",
            "*Efectivo: 49,2*  🔥",
            "",
            "*PMI Caixin*",
            "Anterior: 49,8  ·  Esperado: 49,9",
            "*Efectivo: 48,8*  🔥",
            "",
            "*Publicados:* 21:30 y 21:45 de Chile, *la noche anterior*",
            "",
            "Cifras ilustrativas: no corresponden a una publicación real.",
        ],
        "lectura": [
            "*Paso 1 — los dos bajo 50:* más empresas empeoran que mejoran. No es "
            "desaceleración: es *contracción*.",
            "*Paso 2 — los dos peor que lo esperado:* hay sorpresa negativa genuina, "
            "no un resultado ya descontado.",
            "*Paso 3 — el contraste no salva nada:* cuando ambas versiones caen juntas, "
            "el deterioro alcanza *tanto a las grandes empresas como a las pymes "
            "exportadoras*. Es la señal más fuerte que puede dar este par de "
            "indicadores.",
            "*Conclusión:* menor demanda esperada de materias primas y de energía desde "
            "el mayor consumidor del mundo.",
        ],
        "precio": [
            "*Cobre: baja* ⬇️ — China es el mayor consumidor y el precio responde a "
            "expectativas de demanda.",
            "*USD/CLP: sube* ⬆️ — por dos vías que se suman: menos dólares de "
            "exportación llegando a Chile, y aversión al riesgo que castiga a las "
            "monedas emergentes.",
            "*Petróleo WTI: baja* ⬇️ — China es el mayor importador de crudo; menos "
            "actividad es menos demanda de energía.",
            "*El factor horario:* el dato salió *21:30 de anoche*. Al abrir, parte del "
            "movimiento ya ocurrió — la pregunta a resolver es *si el mercado ya lo "
            "incorporó del todo o queda recorrido*.",
            "*Temporalidad:* swing de jornada (uno a tres días).",
        ],
    },
    {
        "tipo": "bullets",
        "titulo": "El método: seis pasos para leer cualquier publicación",
        "bajada": "Aplicable a un dato de EE.UU., de Chile o de China. Si lo sigues en "
                  "orden, no necesitas recordar tablas.",
        "seccion": SEC_5,
        "color": VERDE,
        "columnas": 2,
        "puntos": [
            ("Paso 1 · Antes de que salga, anota el consenso",
             "Sin consenso no hay sorpresa que medir, y sin sorpresa no hay lectura "
             "posible. Anótalo *antes*, nunca después."),
            ("Paso 2 · Define de antemano las tres reacciones",
             "Qué vas a concluir si sale mejor, peor o en línea. Decidirlo antes evita "
             "improvisar bajo la volatilidad del momento."),
            ("Paso 3 · Al salir, mide la sorpresa en la cifra que pesa",
             "No en el titular: en la sub-lectura relevante — el subyacente mensual, el "
             "grupo de control, el PMI de servicios."),
            ("Paso 4 · Verifica coherencia interna",
             "¿Las sub-lecturas apuntan en la misma dirección? ¿Hubo revisiones al "
             "pasado? Si el informe se contradice, la señal es débil."),
            ("Paso 5 · Traduce a expectativa de tasa",
             "La pregunta única: *¿esto le da al banco central una razón para apretar o "
             "para aflojar?* De la respuesta se deduce la dirección del precio."),
            ("Paso 6 · Recién ahí mira el gráfico",
             "El nivel técnico dice *dónde*; el fundamental dice *por qué* y *hacia "
             "dónde*. Los dos juntos son un análisis; cada uno solo, la mitad."),
        ],
        "clave": ("Regla de prudencia operativa",
                  "En los minutos previos a un dato de alto impacto, la liquidez baja y "
                  "la diferencia entre precio de compra y de venta se abre. El "
                  "movimiento de los primeros segundos es en buena medida aleatorio: "
                  "*conviene esperar el cierre de la primera vela de 15 minutos antes "
                  "de concluir algo*."),
    },
    {
        "tipo": "tabla",
        "titulo": "Ocho errores de interpretación que hay que evitar",
        "bajada": "Todos son fáciles de cometer y todos se corrigen con los conceptos "
                  "del bloque 0.",
        "seccion": SEC_5,
        "color": ROJO,
        "encabezados": ["El error", "Por qué falla", "La corrección"],
        "pesos": [3.0, 3.6, 3.4],
        "filas": [
            ["Leer solo la cifra efectiva",
             "Un número sin referencia no significa nada",
             "Compararla *siempre* contra el consenso"],
            ["Quedarse en el titular anual",
             "Arrastra el efecto base, que ya era conocido",
             "Mirar la *variación mensual subyacente*"],
            ["Asumir que buena noticia económica es buena para la bolsa",
             "Depende de si obliga a mantener la tasa alta",
             "Preguntarse antes *qué problema le preocupa hoy al mercado*"],
            ["Leer la tasa de desempleo sin la participación",
             "Puede bajar porque la gente dejó de buscar trabajo",
             "Revisar siempre la *tasa de participación*"],
            ["Ignorar las revisiones del empleo",
             "Cambian la foto más que el dato del mes",
             "Leer los dos meses corregidos antes de concluir"],
            ["Convertir horas con un desfase fijo",
             "Chile y EE.UU. cambian de horario en meses distintos",
             "Confirmar la hora *en el calendario*, cada vez"],
            ["Operar el primer minuto de un dato mixto",
             "El mercado reacciona al titular y luego revierte",
             "Esperar a que cierre la primera vela de 15 minutos"],
            ["Tratar la correlación como una ley",
             "Dólar y oro suben juntos en episodios de refugio",
             "Identificar en qué *régimen* está el mercado"],
        ],
    },
    {
        "tipo": "bullets",
        "titulo": "Cómo explicárselo al cliente",
        "bajada": "El último tramo, y el que define si el análisis sirve. Un dato bien "
                  "interpretado y mal comunicado *no llega*.",
        "seccion": SEC_5,
        "color": VERDE,
        "columnas": 2,
        "puntos": [
            ("La regla de los 30 segundos",
             "Si un cliente sin experiencia no entiende el mensaje en menos de medio "
             "minuto, hay que reescribirlo más simple. «Más simple» *nunca* significa "
             "«sin dirección»."),
            ("Toda sigla se explica la primera vez",
             "Nombre en español, sigla entre paréntesis una sola vez, y una línea de "
             "explicación. Nunca «el core PCE salió hot»."),
            ("Siempre nombra la dirección",
             "El cliente debe terminar de leer sabiendo *hacia dónde apunta el activo*. "
             "Un análisis que no deja clara la dirección está incompleto."),
            ("Estructura de tres líneas",
             "*Qué pasó* (el dato y su sorpresa) · *por qué importa* (el efecto en la "
             "tasa) · *qué esperar* (la dirección del activo)."),
            ("Énfasis direccional sí, dramatización no",
             "Se dice «sesgo bajista» o «presión vendedora». No se dice «se va a "
             "derrumbar» ni se le atribuyen sensaciones al mercado."),
            ("Explica el mecanismo, no solo el resultado",
             "«El dólar sube porque la inflación alta obliga a mantener las tasas "
             "altas, y eso atrae capital» enseña. «El dólar sube» solo informa."),
        ],
        "clave": ("Ejemplo de un mismo dato, mal y bien comunicado",
                  "❌ «Core CPI hot, 40 puntos base sobre consenso, hawkish para la "
                  "Fed, largos en DXY.»   ✅ «Los precios en Estados Unidos subieron "
                  "más de lo esperado. Eso significa que su banco central no podrá "
                  "abaratar el dinero pronto, y cuando el dinero se mantiene caro el "
                  "dólar se fortalece. Sesgo alcista para el dólar hoy.»"),
    },
    {
        "tipo": "tabla",
        "titulo": "Diccionario rápido",
        "bajada": "Las siglas y expresiones que aparecieron en esta capacitación, en "
                  "una sola página para tener a mano.",
        "seccion": SEC_5,
        "color": VERDE,
        "encabezados": ["Sigla o término", "Nombre en español", "En una línea"],
        "pesos": [1.8, 3.0, 5.2],
        "filas": [
            ["IPC", "Índice de precios al consumidor",
             "Cuánto subieron los precios que paga la gente. La inflación más conocida"],
            ["IPP", "Índice de precios al productor",
             "Precios de fábrica antes de llegar al consumidor; anticipa la inflación"],
            ["PCE", "Gasto en consumo personal",
             "La medida de inflación que el banco central de EE.UU. usa como meta (2%)"],
            ["PIB", "Producto interno bruto",
             "Todo lo que produce un país; mide si la economía crece o se contrae"],
            ["Subyacente\n(core)", "Sin alimentos ni energía",
             "La inflación sin los componentes volátiles; muestra la tendencia de fondo"],
            ["PMI / ISM", "Índice de gerentes de compra",
             "Encuesta a empresas; sobre 50 la actividad se expande, bajo 50 se contrae"],
            ["Nóminas\n(NFP)", "Nóminas no agrícolas",
             "Cuántos empleos creó EE.UU. el mes pasado, sin contar el campo"],
            ["IMACEC", "Índice mensual de actividad económica",
             "El termómetro mensual de la economía chilena, del Banco Central"],
            ["TPM", "Tasa de política monetaria",
             "La tasa de interés que fija el Banco Central de Chile"],
            ["DXY", "Índice del dólar",
             "El valor del dólar contra seis monedas; casi 60% de su peso es el euro"],
        ],
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
                   "Todas las cifras usadas en los ejemplos son *ilustrativas* y no "
                   "corresponden a publicaciones reales. Las referencias de precio "
                   "describen *mecanismos de mercado*, no pronósticos: el "
                   "comportamiento efectivo de un activo depende del contexto, del "
                   "posicionamiento previo y de factores no contenidos en un solo dato."]),
        "proceso": ("Validación de contenido",
                    ["Todo análisis de mercado, informe o material que se vaya a "
                     "difundir —cualquiera sea el canal— pasa por el *Área de Estudios "
                     "y Post-Venta* para su validación y verificación previa, con el "
                     "fin de que la naturaleza del contenido quede clara y explícita.",
                     "Cualquier duda sobre qué se puede afirmar, mostrar o "
                     "recomendar se resuelve directamente con el área."]),
        "firma": ["*Benjamín Ignacio Bravo Soza* — Ingeniero en Finanzas · Diplomado en "
                  "Gestión de Riesgos bajo estándar PMI · Operador Acreditado CMV",
                  "Área de Estudios y Post-Venta · Grupo de Análisis de Mercado — GI · "
                  "31 de julio de 2026"],
    },
]
