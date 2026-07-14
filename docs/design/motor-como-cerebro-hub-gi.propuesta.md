# El motor como cerebro de un hub inteligente — Propuesta para Grupo Inteligencia

> **Qué es este documento.** Una propuesta de visión, en fase preliminar, para integrar un motor de inteligencia de mercado **que ya existe y funciona** como el cerebro de un hub interno (ejecutivos) y externo (clientes) de GI. No es un blueprint de construcción: es el caso de negocio y la prueba de que la idea sirve, con la dirección técnica suficiente para decidir si vale la pena invertir.
>
> **Audiencia:** liderazgo / dueños de GI.
> **Fase:** preliminar — sin construcción aún.
> **Qué se pide decidir:** explorar viabilidad y alcance, no aprobar un desarrollo.

---

## 1. La idea en una frase

GI ya tiene la red de clientes y los ejecutivos; lo que no tiene es una **fuente de inteligencia de mercado que produzca contenido, todos los días, sin depender de una persona**. Ese motor ya existe — fue construido para automatizar el trabajo de análisis diario — y puede convertirse en el cerebro que alimenta tanto a los ejecutivos como a los clientes desde una sola fuente.

---

## 2. El problema / la oportunidad

Hoy la operación de contenido de mercado tiene tres límites naturales:

- **Depende de una persona cada mañana.** El análisis diario lo produce un humano; si esa persona no está, no hay contenido. No escala.
- **El cliente recibe poco valor continuo.** Sin un flujo constante de análisis y educación, la relación con el cliente se enfría: rota, no recomienda, no sube de plan.
- **Los ejecutivos no siempre hablan el mismo idioma del mercado.** Cada uno arma su lectura como puede; el mensaje al cliente es inconsistente.

La oportunidad: un motor que ya genera ese contenido de forma automática y consistente puede **romper la dependencia humana**, dar **valor continuo al cliente** y **alinear a los ejecutivos** bajo un mismo lenguaje — sin sumar headcount.

---

## 3. La solución: un cerebro, dos hubs

Una misma inteligencia, segmentada por audiencia, alimentando dos superficies:

```
            ┌─────────────────────────────────────────────────┐
            │                  EL MOTOR  (ya existe)            │
            │  Convierte datos crudos de mercado en             │
            │  inteligencia lista para leer, adaptada a quién   │
            │  la recibe: niveles, sesgo, calendario, contenido │
            │  segmentado y educación.                          │
            └───────────────┬─────────────────┬─────────────────┘
                            │                 │
                  alimenta  │                 │  alimenta
                            ▼                 ▼
              ┌───────────────────┐   ┌───────────────────┐
              │   HUB INTERNO     │   │   HUB EXTERNO     │
              │   (ejecutivos)    │   │    (clientes)     │
              │                   │   │                   │
              │ • Análisis diario │   │ • Análisis        │
              │ • Mismo lenguaje  │   │ • Señales         │
              │ • Métricas de las │   │ • Educación       │
              │   cuentas de sus  │   │ • Su propia       │
              │   clientes        │   │   cuenta          │
              └───────────────────┘   └───────────────────┘

  Origen: el motor nació para automatizar el análisis diario.
  En el camino se volvió evidente que ese mismo cerebro puede servir a toda GI.
```

La clave: **es el mismo motor**. El hub interno y el externo no son dos desarrollos; son dos vistas, con permisos distintos, sobre la misma inteligencia.

---

## 4. ¿Sirve? — Sí, y hay evidencia

La pregunta de fondo no es "¿se podría construir algo así?" sino "¿el motor de GI realmente produce lo que un hub necesita?". La respuesta es sí, **hoy**, no en una promesa futura. El motor ya genera de forma automática:

| Lo que produce el motor hoy | Para el ejecutivo se ve como… | Para el cliente se ve como… |
|---|---|---|
| **Niveles técnicos** (soportes, resistencias, sesgo) por activo y temporalidad | El mapa del día para responderle a su cartera | "¿Hacia dónde va el activo y qué vigilar?" |
| **Calendario económico** del día (Chile, EE.UU., China, Zona Euro) con el dato real vs. lo esperado | Qué evento puede mover al cliente hoy | "El dato de hoy, explicado simple" |
| **Contenido segmentado por audiencia** (mismo hecho, dos registros) | Refuerzo de concepto para su discurso | Análisis y educación a su nivel |
| **Material educativo progresivo** (currículo de conceptos) | Consistencia en cómo se explica | "Aprendo a leer el mercado" |

> **La demostración concreta** (recomendada para acompañar esta propuesta): tomar la salida real de un día y mostrarla lado a lado — la misma inteligencia renderizada como la vería un ejecutivo y como la vería un cliente. Eso convierte "podría servir" en "miren, ya sirve".

---

## 5. ¿De qué forma? — la dirección de stack

Sin entrar a diseñar la construcción, la dirección técnica que justifica alcance, costo y compliance es la siguiente:

- **Regla de oro:** WordPress (donde GI ya invirtió: UltimateMember + ACF) es la **capa de experiencia** — login, perfiles, render. **Nunca** es el motor ni toca datos transaccionales. Eso lo mantiene simple, seguro y barato.
- **El motor vive en la nube**, siempre encendido, y expone su inteligencia a través de una **única puerta de entrada (API)**. WordPress y ambos hubs consumen esa puerta; no hablan con el mercado directamente.
- **Las métricas de cuenta del cliente** (balance, P/L, drawdown, historial) son la pieza más potente para el hub interno — y la que **depende de un tercero**: requiere acceso de administración al servidor MT5, que **provee el bróker** (la "Manager API"). Es un bloqueante externo con costo y licencia propios. Se nombra explícitamente porque condiciona el alcance: el resto del hub puede arrancar sin ella; esta pieza no avanza hasta que el bróker la habilite.

Topología elegida para arrancar (MVP): **WordPress como experiencia + una puerta de API delante del motor**. Respeta la inversión de GI en WordPress, saca el motor transaccional fuera de WordPress, y deja el bloqueante del bróker aislado en una sola pieza. Es lean hoy y tiene ruta de crecimiento sin rehacer el motor.

---

## 6. Valor de negocio y diferenciación

- **Retención y NPS:** el cliente que recibe valor continuo (análisis + educación) se queda más, recomienda más y sube de plan. El motor pasa GI de "vender señales" a "enseñar a leer el mercado".
- **Menos churn:** la relación deja de enfriarse entre señal y señal.
- **Ejecutivos alineados:** todos hablan el mismo idioma del mercado, todos los días, sin reuniones de coordinación.
- **Escala sin headcount:** el contenido diario no crece con más analistas; crece con el motor.
- **Diferenciación:** la mayoría de los competidores entrega señales sueltas o análisis genérico. Un hub que combina inteligencia diaria, educación progresiva y la propia cuenta del cliente es un producto difícil de copiar — y GI ya tiene el cerebro construido.

---

## 7. Costo, alcance y riesgo (MVP — decenas de usuarios)

**Alcance del MVP:**
- Motor de análisis + contenido alojado en la nube, alimentando el hub.
- Hub interno y externo como vistas sobre WordPress (lo que GI ya tiene).
- Métricas de cuenta MT5: **documentadas y diseñadas, pero condicionadas** a que el bróker habilite el acceso.

**Orden de magnitud de costo (MVP lean):** hosting en la nube siempre encendido + la puerta de API son costos mensuales modestos y predecibles; el grueso del valor (el motor) ya está construido. La pieza de cuentas MT5 agrega el costo de licencia/acceso del bróker, que **hay que cotizar con ellos**.

**Riesgos y mitigación:**

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Acceso a Manager API del bróker | Alto — bloquea las métricas de cuenta | Aislar esa pieza; el resto del hub arranca sin ella; confirmar acceso/costo con el bróker como primer paso |
| Hosting/operación 24·7 del motor | Medio — el motor hoy corre local | Definir nube lean en la propuesta; es un costo conocido y acotado |
| Datos sensibles de cliente | Medio — compliance | WordPress nunca toca datos transaccionales; ver §8 |

**Filosofía:** lean ahora, con ruta de escala explícita. No se sobre-construye para miles cuando hoy son decenas.

---

## 8. Compliance

- **Separación estricta:** WordPress maneja identidad y experiencia; los datos transaccionales (cuentas, operaciones) viven detrás de la API, nunca en WordPress. Esto reduce la superficie de riesgo.
- **Datos de cliente:** las métricas de cuenta se exponen solo al cliente dueño y a su ejecutivo asignado, vía permisos por rol.
- **KYC / identidad:** se apoya en lo que GI ya use para alta de clientes; el hub no reinventa el onboarding regulatorio.

---

## 9. Siguiente paso (pequeño y concreto)

No se pide aprobar un desarrollo completo. Se piden dos cosas acotadas que despejan el camino:

1. **Confirmar con el bróker** el acceso, licencia y costo de la Manager API (despeja el único bloqueante externo).
2. **Piloto del hub interno** con la salida actual del motor: mostrar a un par de ejecutivos el análisis diario automático durante una semana y medir si les sirve. Costo cercano a cero, evidencia real.

Con eso, GI decide con datos — no con una promesa.
