# Menor 16: siglas ADP y EIA explicadas en mapa y víspera. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Explicar las siglas ADP y EIA en los textos del mapa semanal y la víspera para ejecutivos comerciales (regla del proyecto: toda sigla se explica una sola vez en lenguaje simple), asegurando mediante un test de contrato que ningún evento tier <= 2 de EE.UU. o Chile contenga siglas en mayúsculas de 3 o más letras sin explicación entre paréntesis.

**Architecture:** El módulo `scripts/analista/semana.py` usa el diccionario `NOMBRES` para sobrescribir los nombres base provenientes de `data/glosario_siglas.json` cuando estos vienen sin su sigla explicada o sin especificar la decisión (actualmente contiene la decisión de tasas del FOMC). Se amplía `NOMBRES` con las entradas `"Empleo privado ADP"` e `"Inventarios de petróleo crudo (EIA)"` proporcionando redacciones concisas en español chileno ("informe de la empresa ADP" e "informe de la agencia de energía EIA"). La función `_nombre(ev)` utiliza este diccionario y alimenta directamente a `armar_mapa` y `armar_vispera`. En `tests/test_analista_semana.py` se añaden tests unitarios para ambos eventos y un test de contrato que recorre `data/glosario_siglas.json` exigiendo que todos los eventos tier <= 2 de EE.UU. y Chile reconocidos por `tipo_de_evento` tengan sus siglas debidamente explicadas.

**Tech Stack:** Python 3.11+, pytest vía `uv run`, glosario canónico `data/glosario_siglas.json`.

**Spec:** `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md` (§ Reglas de texto) y especificación del Menor 16.

---

## Global Constraints

- **TDD estricto:** escribir el test que falla antes de tocar el código de producción.
- **Reglas de texto:** español de Chile, tuteo neutro, **sin guion largo (`—`) ni guion medio (`–`)**, sin lenguaje de asesoría u órdenes (`compra`, `vende`, `oportunidad`, `cobertura`).
- **Aislamiento de canales:** ningún módulo de `scripts/analista/` puede importar ni referenciar el envío a WhatsApp (`tests/test_analista_avisos_semana.py::test_el_agendador_no_importa_el_envio_de_whatsapp`).
- **Rama de trabajo:** trabajar exclusivamente en `feat/alerta-semana-ejecutivos`. Nunca commitear a `master`; sin push.
- **Formato del commit:** el commit debe terminar exactamente con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Integridad y encoding:** preservar UTF-8 al editar archivos; no usar `Set-Content` de PowerShell para strings con acentos.
- **Suite completa:** al cerrar la tarea, correr `uv run pytest -q` y verificar que la suite completa pase limpia.

---

## Review Focus

1. **Revisión exhaustiva de eventos tier <= 2 de EE.UU. y Chile:**
   Se verificó el catálogo completo de 22 eventos tier <= 2 en `data/glosario_siglas.json`:
   - `ADP` ("Empleo privado ADP"): sigla suelta sin paréntesis ni explicación. Requiere entrada en `NOMBRES`.
   - `Crude Oil Inventories` ("Inventarios de petróleo crudo (EIA)"): trae `(EIA)` como sigla sin explicar qué es la EIA ni de quién es el informe. Requiere entrada en `NOMBRES`.
   - Otras entradas como `CPI` ("Índice de precios al consumidor (IPC)"), `PPI` ("Índice de precios al productor (IPP)") y `GDP` ("Producto interno bruto (PIB)") ya traen su sigla desarrollada en el nombre en español previo al paréntesis.
   - Entradas como `PMI`, `ISM`, `NFP`, `JOLTS`, `PCE`, `Jobless Claims`, `TPM`, `IMACEC` traen su nombre descriptivo en español sin siglas en mayúsculas de 3+ letras.
   - Exclusiones válidas de siglas operativas: `CLT`, `CLST`, `CFD`, `Fed`.
2. **Formato en mapa y víspera:**
   - La redacción en `_nombre` no debe terminar en punto para evitar dobles puntos en la víspera (`sale {nombre}.`).
   - Los textos deben integrarse con naturalidad tanto en el mapa del lunes (`• {cuando} · {nombre} · mueve: {activos}`) como en la víspera (`📍 {dia} a las {hora} sale {nombre}.`).

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `scripts/analista/semana.py` | Diccionario `NOMBRES`: añadir entradas explicativas para ADP e EIA | Modificar |
| `tests/test_analista_semana.py` | Test unitario de redacción para ADP/EIA y test de contrato sobre el glosario | Modificar |

---

### Task 1: Explicar siglas ADP y EIA en `semana.py` y añadir test de contrato

**Files:**
- Modify: `scripts/analista/semana.py:57-59`
- Modify: `tests/test_analista_semana.py`

**Interfaces:**
- Produces:
  - `NOMBRES["Empleo privado ADP"] = "Empleo privado de EE.UU. (informe de la empresa ADP)"`
  - `NOMBRES["Inventarios de petróleo crudo (EIA)"] = "Inventarios de petróleo crudo de EE.UU. (informe de la agencia de energía EIA)"`
- Consumes:
  - `_nombre(ev)` en `scripts/analista/semana.py` devuelve el nombre con sigla explicada para eventos de ADP y EIA.
  - `armar_mapa(eventos, ahora)` y `armar_vispera(ev, ahora)` incluyen los nombres explicados sin guion largo ni siglas sueltas.

- [ ] **Step 1: Escribir los tests unitarios y de contrato en `tests/test_analista_semana.py`**

Agregar al final de `tests/test_analista_semana.py`:

```python
# ───────────────────────────────────────────── menor 16: siglas explicadas (ADP, EIA)


def test_adp_y_eia_explican_su_sigla():
    adp_ev = ev("ADP Nonfarm Employment Change (Sep)", "2026-10-21 09:15")
    nom_adp = sm._nombre(adp_ev)
    assert nom_adp == "Empleo privado de EE.UU. (informe de la empresa ADP)"
    mapa_adp = sm.armar_mapa([adp_ev], LUNES)
    assert "Empleo privado de EE.UU. (informe de la empresa ADP)" in mapa_adp
    vispera_adp = sm.armar_vispera(adp_ev, datetime(2026, 10, 20, 16, 0, tzinfo=SCL))
    assert "Empleo privado de EE.UU. (informe de la empresa ADP)" in vispera_adp

    crudo_ev = ev("Crude Oil Inventories", "2026-10-21 12:30")
    nom_crudo = sm._nombre(crudo_ev)
    assert nom_crudo == "Inventarios de petróleo crudo de EE.UU. (informe de la agencia de energía EIA)"
    mapa_crudo = sm.armar_mapa([crudo_ev], LUNES)
    assert "Inventarios de petróleo crudo de EE.UU. (informe de la agencia de energía EIA)" in mapa_crudo
    vispera_crudo = sm.armar_vispera(crudo_ev, datetime(2026, 10, 20, 16, 0, tzinfo=SCL))
    assert "Inventarios de petróleo crudo de EE.UU. (informe de la agencia de energía EIA)" in vispera_crudo


def test_contrato_glosario_todas_las_siglas_explicadas():
    """Toda sigla de 3+ letras mayúsculas en eventos tier<=2 de EE.UU./Chile debe tener explicación."""
    excluidas = {"CLT", "CLST", "CFD", "FED"}
    patrones_conocidos = {
        "IPC": "precios al consumidor",
        "IPP": "precios al productor",
        "PIB": "producto interno bruto",
    }

    fallas = []
    for key, entrada in GLOSARIO.items():
        if key.startswith("_"):
            continue
        tier = sm._tier({"diccionario": entrada})
        if tier > sm.TIER_ALTO:
            continue
        pais = entrada.get("pais")
        if pais not in sm.PAISES_DEL_TEMA:
            continue

        ev_candidato = {"nombre": key, "pais": pais, "diccionario": entrada}
        if sm.tipo_de_evento(ev_candidato) is None:
            for c in entrada.get("titulos_ff", []):
                ev_alt = {"nombre": c, "pais": pais, "diccionario": entrada}
                if sm.tipo_de_evento(ev_alt) is not None:
                    ev_candidato = ev_alt
                    break
            else:
                continue

        nombre = sm._nombre(ev_candidato)
        siglas = [s for s in re.findall(r"\b[A-Z]{3,}\b", nombre) if s not in excluidas]
        for s in siglas:
            # 1. ¿Está dentro de paréntesis con texto explicativo adicional?
            m_paren = re.search(rf"\(([^)]*\b{s}\b[^)]*)\)", nombre)
            if m_paren and len(m_paren.group(1).strip().split()) > 1:
                continue
            # 2. ¿Es una sigla en paréntesis precedida por su desarrollo en español?
            if s in patrones_conocidos and patrones_conocidos[s] in nombre.lower() and f"({s})" in nombre:
                continue
            fallas.append((key, nombre, s))

    assert not fallas, f"Eventos con siglas sin explicar: {fallas}"
```

- [ ] **Step 2: Correr y ver que fallan (FAIL)**

Ejecutar en PowerShell:
```powershell
uv run pytest tests/test_analista_semana.py -k "sigla or contrato" -q
```

Salida esperada (FAIL):
```
FAILED tests/test_analista_semana.py::test_adp_y_eia_explican_su_sigla - AssertionError: assert 'Empleo privado ADP de EE.UU.' == 'Empleo privado de EE.UU. (informe de la empresa ADP)'
FAILED tests/test_analista_semana.py::test_contrato_glosario_todas_las_siglas_explicadas - AssertionError: Eventos con siglas sin explicar: [('ADP', 'Empleo privado ADP de EE.UU.', 'ADP'), ('Crude Oil Inventories', 'Inventarios de petróleo crudo (EIA) de EE.UU.', 'EIA')]
2 failed, 46 deselected in 2.15s
```

- [ ] **Step 3: Implementar la ampliación de `NOMBRES` en `scripts/analista/semana.py`**

Modificar `NOMBRES` en [scripts/analista/semana.py](file:///C:/Users/bbrav/gam-alerta/scripts/analista/semana.py#L57-L59):

```python
# Nombres que el glosario trae sin su sigla explicada o sin decir qué decide.
NOMBRES = {
    "Comité de mercado abierto de la Fed": "Decisión de tasas de la Reserva Federal (Fed) de EE.UU.",
    "Empleo privado ADP": "Empleo privado de EE.UU. (informe de la empresa ADP)",
    "Inventarios de petróleo crudo (EIA)": "Inventarios de petróleo crudo de EE.UU. (informe de la agencia de energía EIA)",
}
```

- [ ] **Step 4: Correr y ver que pasan los nuevos tests (PASS)**

Ejecutar en PowerShell:
```powershell
uv run pytest tests/test_analista_semana.py -k "sigla or contrato" -q
```

Salida esperada (PASS):
```
..                                                                       [100%]
2 passed, 46 deselected in 2.18s
```

- [ ] **Step 5: Correr la suite de analista y la suite completa**

Ejecutar en PowerShell:
```powershell
uv run pytest tests/test_analista_semana.py tests/test_analista_avisos_semana.py tests/test_analista_bot_avisos.py -q
```
Salida esperada:
```
....................................................................................................     [100%]
100 passed in 3.48s
```

Luego ejecutar la suite completa del repositorio:
```powershell
uv run pytest -q
```
Verificar que la suite completa pase limpia sin fallos.

- [ ] **Step 6: Commit de los cambios**

Ejecutar en PowerShell:
```powershell
git add scripts/analista/semana.py tests/test_analista_semana.py
git commit -m "fix(analista): explicar siglas ADP y EIA en mapa y vispera (Menor 16)

Ampliacion de NOMBRES en semana.py para que Empleo privado ADP e
Inventarios de petroleo crudo (EIA) salgan con su sigla explicada en
lenguaje simple y formato chileno sin guion largo. Test de contrato
que audita todos los eventos tier<=2 de EE.UU. y Chile del glosario.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
