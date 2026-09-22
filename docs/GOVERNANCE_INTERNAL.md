# GOBERNANZA Y CONTROL DE VERSIONES INTERNO
**Documento:** `MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO_GI.pdf`  
**Grupo Inteligencia · Departamento de Research y Trading Cuantitativo**  
**Clasificación:** Archivo Interno de Control Editorial y Auditoría Técnica  
**Última Actualización:** 2026-09-21 (Emisión Oficial Octubre 2026)

---

## 1. Mapeo de Versiones (Interna ↔ Pública)

| Versión Interna | Edición Pública Visible | Fecha de Corte | Estado | Propósito / Hito |
|---|---|---|---|---|
| **v1.0** | *No publicada* | Agosto 2026 | Obsoleta | Versión inicial formativa con stops discrecionales en mínimos de velas. |
| **v2.0** | *No publicada* | Septiembre 2026 | Obsoleta | Formalización matemática del ATR de 14 en H1, conmutador de climas R0–R4, precedencia de setups y Chandelier Trailing Exit. |
| **v2.1** | *No publicada* | Septiembre 2026 | Obsoleta | Centralización de umbrales en Anexo A2 (SSOT), unificación de tasa real para Oro en 2,20 %, Presupuesto de Riesgo Neto (Buffer 90/10), Matriz 2D Clima × Setup, Slippage Cap y Módulo 12 de Bitácora. |
| **v3.0** | *No publicada* | Septiembre 2026 | Obsoleta | Corrección integral tras auditoría técnica de Kimi: SSOT en `params.yaml`, unificación de confianza a 51,0 %, presupuesto objetivo 1,00 % con riesgos residuales, caso M4.4 y bitácora M12 re-hechos, matriz direccional de tasas en M9.4. |
| **v3.0.1** | **Edición Pública Inicial · Versión 1.0** | **Octubre 2026** | **VIGENTE OFICIAL** | **Hotfix y Limpieza Editorial Pública**: Retiro de tabla de gobernanza del PDF público, corrección de duplicación en M7.4, unificación estricta de slippage cap a 0,2×ATR, confirmación WTI Δ5d ≥ +1,00 %, tabla M7.3 con dígitos MT5, eliminación de parámetro no respaldado de Bollinger en A2, y neutralización de tokens internos. |

---

## 2. Historial Detallado de Decisiones Técnicas y Hotfixes

### Hotfix v3.0.1 (Septiembre / Octubre 2026)
- **HF-01**: Corrección de bug de concatenación múltiple en M7.4 (texto de lote post-redondeo deduplicado a exactamente una aparición). Causa raíz: ejecución repetitiva de `.replace()` sobre el fragmento de tabla.
- **HF-02**: Actualización de portada, contraportada y pies de página al identificador público oficial (*Edición Pública Inicial · Versión 1.0 · Octubre 2026*).
- **HF-03**: Aplicación estricta de D3: regla única de slippage cap a `0,2 × ATR` en M5.1 y Anexo A2, manteniendo el 15 % únicamente como equivalencia ilustrativa (~13 % para stops de 1,5×ATR).
- **HF-04**: Aplicación estricta de D5: confirmación cruzada de WTI en M8.4, Anexo A2 y `params.yaml` fijada en `Petróleo Δ 5d ≥ +1,00 % (tendencia material, no ruido)` eliminando el umbral tautológico `> 0,00 %`.
- **HF-05**: Reemplazo de columnas en tabla M7.3 por *Decimales típicos de cotización* y *Valor de 1 último decimal por lote (CLP)*, con nota de advertencia sobre dígitos de plataforma en MT5.
- **HF-06**: Eliminación de la fila de ancho de Bandas de Bollinger (≤ 2,0 × ATR) en la tabla A2 por ser una regla no respaldada en el cuerpo del manual.
- **HF-07**: Correcciones menores: M1.3 (seis indicadores), M11 (confianza ≥ 51,0 % inclusive), M5.3 (vencimiento 2 velas H1 y colocabilidad en MT5), M12 (resultado neto en fila 7b: +$8.580 CLP = +0,86 %), M0.4 (concordancia en nota Oro), M4.4 (neutralización a *Verificado contra las reglas de este manual — pasa 6/6 filtros*).
- **Decisión Editorial §2**: El manual público no incluye control de versiones ni referencias a auditorías o procesos editoriales internos.

---

## 3. Política de Mantenimiento y SSOT

1. **Fuente Única de Verdad**: Cualquier modificación de parámetros numéricos debe realizarse primero en `docs/params.yaml` antes de modificar la documentación o los scripts del motor.
2. **Numeración**:
   - Cambios menores / parches técnicos incrementan el tercer dígito interno (`v3.0.x`) y se mantienen bajo la *Edición Pública v1.0*.
   - Cambios de arquitectura o nuevos módulos incrementan el número mayor público (`v2.0`).
