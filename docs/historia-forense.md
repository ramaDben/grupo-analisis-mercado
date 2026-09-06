# Historia forense: las mediciones detrás de las reglas

`CLAUDE.md` conserva cada regla **con su razón en una frase**, porque una regla sin su porqué se
revierte: la próxima vez que alguien optimice el despacho va a poner el pie en el editor porque
es más directo, y el canal va a recibir un mensaje al que le faltan renglones sin que nadie lo
note.

Lo que vive acá es la otra mitad: **la medición, la tabla y la fecha.** Se consulta cuando hace
falta el número exacto, cuando alguien quiere volver a discutir una decisión, o cuando conviene
saber si una hipótesis ya se probó y salió falsa.

Cada sección corresponde a una de `CLAUDE.md`, con el mismo nombre.

---

## Un solo reloj: `config/agenda_mercado.json`

### La cripto se mueve en la mañana americana, no en Asia

Medido el 2026-09-04 sobre 90 días de velas H1 en BTC, ETH, SOL y LTC. La cifra es la mediana
del rango por hora contra la mediana diaria, solo días hábiles.

| Bloque (hora NY) | BTC | ETH | SOL | LTC |
|---|---|---|---|---|
| Asia 18–02 | 1,01x | 0,98x | 0,94x | 0,97x |
| Europa 03–08 | 0,98x | 0,96x | 0,90x | 0,98x |
| **NY mañana 08–12** | **1,80x** | **1,65x** | **1,52x** | **1,49x** |
| NY tarde 12–16 | 1,23x | 1,17x | 1,16x | 1,14x |

El máximo está en 09:00–10:00, donde BTC llega a **2,09x** su mediana diaria. La sesión asiática
está plana y Europa también: **la hipótesis del rollover asiático era falsa.** El momento va a
las 09:00 y no a las 10:00 solo para no chocar con el de los índices, porque cada momento
produce su propia tanda.

**El fin de semana la cripto está más quieta, no más activa**: 0,76x a 0,85x del día hábil. La
sesión `fin_de_semana` existía en parte pensando en lo contrario, y el dato no respalda esa idea.

### El offset del servidor de MT5, medido

La primera corrida de esa medición dio el máximo en las 06:00 de Nueva York, que habría apuntado
a la apertura de Londres y a una conclusión distinta. El servidor del broker corre en **UTC−4**,
así que el máximo real estaba cuatro horas después. Es el mismo error de interpretar la marca de
tiempo de MT5 como UTC cuando viene en hora del servidor.
