# Maquinaria de hipótesis y validación — vista de conjunto

> Diagramas ASCII de cómo encajan `grupo-analisis-mercado` (descubrimiento) y
> `genesis` (validación). Estado verificado contra el código el 2026-08-12.

---

## 1. Overview — el recorrido de una hipótesis

De un paper académico a una estrategia autorizada a operar.

```text
   ╔══════════════════════════════════════════════════════════╗
   ║        grupo-analisis-mercado   ·   DESCUBRIMIENTO       ║
   ╚══════════════════════════════════════════════════════════╝

     ( papers SSRN )
           │
           │ extrae
           ▼
     ┌──────────────┐   genera     ┌────────────────────────────┐
     │  LLM  (Agy)  │─────────────▶│  catálogo SSRN v1.3        │
     └──────────────┘  hipótesis   │  · id_setup · familia      │
                                   │  · procedencia académica   │
     ┌──────────────┐              │  · espacio de búsqueda     │
     │   régimen    │┄┄┄ filtra ┄┄▶│  · régimen macro óptimo    │
     │point-in-time │              └──────────────┬─────────────┘
     └──────────────┘                             │
                                                  │ HypothesisSpec
                                                  ▼
                                       ┌─────────────────────┐
                                       │   genesis_bridge    │
                                       └──────────┬──────────┘
                                                  │
   ═══════════════════════════════════════════════╪══════════════
            frontera de repos                     │ genoma + datos
   ═══════════════════════════════════════════════╪══════════════
                                                  ▼
   ╔══════════════════════════════════════════════════════════╗
   ║              genesis   ·   VALIDACIÓN                    ║
   ╚══════════════════════════════════════════════════════════╝
                                                  │
                                                  │ veredicto
                                                  ▼
                                       ┌─────────────────────┐
                                       │     certificado     │
                                       └──────────┬──────────┘
                                                  │ si aprueba
                                                  ▼
                                          ( operación real )
```

Leyenda: `───▶` flujo principal · `┄┄▶` dependencia condicional.

---

## 2. Las cuatro capas de genesis y qué usa hoy el puente

El hallazgo central: **el puente usa genesis como simulador, no como autoridad
de validación**. Consume la capa 3 casi entera y omite la capa 4 casi entera.

```text
   ┌─ CAPA 1 · DATOS ────────────────────────────────────────┐
   │  store Parquet · calendario · sesiones · calidad        │  parcial
   │  AnnotatedBar          ◀── USA                          │
   └─────────────────────────────────────────────────────────┘
   ┌─ CAPA 2 · ESTRATEGIA ───────────────────────────────────┐
   │  StrategyCandidate     ◀── USA                          │  usa
   │  Inspector             ◀── USA                          │
   └─────────────────────────────────────────────────────────┘
   ┏━ CAPA 3 · BACKTEST ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
   ┃  Simulator             ◀── USA                          ┃  USA
   ┃  CostsConfig           ◀── USA                          ┃  CASI
   ┃  Ledger / FillRecord   ◀── USA                          ┃  TODA
   ┃  metrics               ◀── USA  (incluido _privado)     ┃
   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
   ┌─ CAPA 4 · VALIDACIÓN ───────────────────────────────────┐
   │  run_wfa                      ✗  no la llama            │
   │  run_dsr_pbo                  ✗  no la llama            │  OMITE
   │  run_purged_cv                ✗  no la llama            │  CASI
   │  run_montecarlo_symbol        ✗  no la llama            │  TODA
   │  run_sensitivity              ✗  no la llama            │
   │  run_prop_sim                 ✗  no la llama            │
   │  run_verdict                  ✗  no la llama            │
   │  trial_ledger  (#53)          ✗  tiene uno paralelo     │
   │  _dsr.deflated_sharpe_ratio   ◀── USA  (API privada)    │
   │  VerdictKind / VerdictResult  ◀── USA  (solo tipos)     │
   └─────────────────────────────────────────────────────────┘
```

Consecuencia: los gates G1-G9, C1-C2 y P1-P6 **nunca se evalúan**. El puente
reimplementa un subconjunto propio.

---

## 3. Actual vs. destino — dónde vive la autoridad

```text
   ACTUAL  (2.000 líneas de puente)      DESTINO  (puente delgado)
   ────────────────────────────────      ─────────────────────────

   catálogo                              catálogo
      │                                     │
      ▼                                     ▼
   ┌────────────────────────┐            ┌──────────────────┐
   │     genesis_bridge     │            │  genesis_bridge  │
   │                        │            │  (traduce y ya)  │
   │  · arma candidato      │            └────────┬─────────┘
   │  · corre Simulator     │                     │ genoma
   │  · calcula DSR solo    │                     ▼
   │  · PBO = None          │            ╔══════════════════╗
   │  · ledger propio       │            ║   run_verdict    ║
   │  · gates ad-hoc        │            ║   (genesis)      ║
   └───────────┬────────────┘            ╚════════┬═════════╝
               │                                  │ orquesta
               │ usa solo                         ├─▶ run_wfa
               ▼                                  ├─▶ run_dsr_pbo
        ┌─────────────┐                           ├─▶ run_purged_cv
        │  Simulator  │                           ├─▶ run_montecarlo
        └─────────────┘                           ├─▶ run_sensitivity
                                                  ├─▶ trial_ledger #53
                                                  └─▶ gates G/C/P/T
               │                                  │
               ▼                                  ▼
        certificado                        certificado
     (métricas propias)                 (veredicto genesis)
```

**Por qué importa:** un DSR hardcodeado solo es posible si el puente es quien
asigna el DSR. En la columna derecha no existe el lugar donde poner la constante.

---

## 4. Ciclo de vida del certificado

```text
        ●
        │
        ▼
   ┌─────────────┐
   │  CANDIDATO  │
   └──────┬──────┘
          │ validación real  (WFA · DSR · PBO · MC · ≥30 trades OOS)
          ▼
   ┌──────────────────────────────┐
   │  GATE_ESTADISTICO_APROBADO   │   operational_status: BLOQUEADO
   └──────┬───────────────────────┘
          │ auditoría humana del mecanismo
          ▼
   ┌──────────────────────────────┐
   │      VALIDADO_GENESIS        │   operational_status: PAPER_ONLY
   └──────┬───────────────────────┘
          │ incubación en paper trading
          ▼
   ┌──────────────────────────────┐
   │      APROBADO_LIMITADO       │   operational_status: LIVE_LIMITED
   └──────┬───────────────────────┘
          │
          ▼
          ◉

   Desde cualquier estado, ante métricas inválidas o muestra insuficiente:

          ──── revocación ───▶  ┌──────────┐
                                │ REVOKED  │  (append-only, nunca se borra)
                                └──────────┘
```

Los tres certificados emitidos hasta hoy (S3×XAUUSD, S3×US100, S2×XAUUSD)
están en `REVOKED` por la auditoría forense del 2026-08-21.

---

## 5. Riesgos abiertos, ubicados en el flujo

```text
   ( papers SSRN )
         │
         ▼
   ┌──────────────┐
   │  LLM  (Agy)  │
   └──────┬───────┘
          ▼
   ┌────────────────────┐
   │  catálogo SSRN     │◀━━ R1  NO ESTÁ EN GIT
   └──────┬─────────────┘        vive en el brain cache de Antigravity;
          │                      si se limpia, todo hash queda huérfano
          ▼
   ┌────────────────────┐
   │ hypothesis_loader  │◀━━ R2  MATCHER POR SUBSTRING
   └──────┬─────────────┘        puede devolver la hipótesis equivocada
          │                      en silencio, y esa identidad va al trial_id
          ▼
   ┌────────────────────┐
   │ validation_runner  │◀━━ R3  dsr_real = 0.0 en el except
   └──────┬─────────────┘        un error de cálculo se disfraza de métrica
          │              ◀━━ R4  ledger de ensayos paralelo al de genesis
          │                      dos contadores ⇒ ninguno es autoritativo
          ▼
   ┌────────────────────┐
   │      genesis       │◀━━ R5  sin modo "hipótesis": run_verdict exige
   └────────────────────┘        contexto prop completo, y esquivarlo fue
                                 lo que abrió la puerta al fraude auditado
```

| # | Riesgo | Costo de arreglo |
|---|---|---|
| R1 | Catálogo fuera de control de versiones | minutos |
| R2 | Matcher de identidad por substring | horas |
| R3 | `dsr_real = 0.0` en el `except` | minutos |
| R4 | Ledger de ensayos duplicado | días |
| R5 | genesis sin modo hipótesis (partir `FirmProfile`) | semanas |

---

## 6. La brecha de temporalidad

```text
   catálogo             genesis
   ────────             ───────
   S3_..._H1            ┌───────────────┐
   hipótesis en   ──?──▶│  M1 + ticks   │   no hay resampleo
   H1 / D1              │  únicamente   │   ni store multi-TF
   (la literatura       └───────────────┘
    publicada)

   Hoy:  200 velas H1  ≈  10 días        ← lo que corrió la auditoría
   Pide: 5.000-10.000 velas H1           ← criterio de remediación
   Hay:  ~29.000 velas H1 equivalentes   ← export del 2026-08-12
                                            (M1 desde 2017, ticks desde 2021-10)
```

El bloqueador de datos **ya está resuelto**; falta el resampleo M1→H1.
