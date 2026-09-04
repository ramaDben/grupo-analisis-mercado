#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hoja de estilos del informe de cierre semanal.

Extraida tal cual del compilador el 2026-09-04, sin cambios de diseno: el
ejemplar del 28 de agosto ya salio al canal con este aspecto y el estandar esta
aprobado. Vive aparte para que el compilador quede legible y para que un ajuste
de maqueta no obligue a leer 900 lineas.

Las llaves van dobladas (`{{` y `}}`) porque el bloque se interpola como
f-string, igual que en el original.
"""


def hoja_de_estilos(caras_de_fuente: str) -> str:
    """El CSS completo, con las @font-face embebidas que recibe."""
    return f"""
{caras_de_fuente}

@page {{
    size: A4 portrait;
    margin: 0;
}}

* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #2D3748;
    background: #E2E8F0;
    -webkit-font-smoothing: antialiased;
}}

.a4-page {{
    width: 794px;
    height: 1123px;
    background: #FFFFFF;
    margin: 0 auto;
    position: relative;
    overflow: hidden;
    page-break-after: always;
    break-after: page;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 16mm 20mm;
}}

/* Encabezados y Pies de página institucionales */
.page-header {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding-bottom: 8px;
    border-bottom: 1.5px solid #50C0A8;
    margin-bottom: 12px;
}}

.page-header-left {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #3E91AF;
    text-transform: uppercase;
}}

.page-header-right {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 8.5px;
    font-weight: 600;
    color: #718096;
    letter-spacing: 0.05em;
}}

.page-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 8px;
    border-top: 1px solid #E2E8F0;
    margin-top: 10px;
    font-size: 8.5px;
    color: #718096;
}}

.page-footer-left {{
    font-weight: 700;
    color: #50C0A8;
    letter-spacing: 0.08em;
}}

.page-footer-right {{
    font-weight: 600;
}}

/* Tipografía de Contenido */
.section-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 15px;
    font-weight: 700;
    color: #0B1916;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.section-title::before {{
    content: "";
    display: inline-block;
    width: 4px;
    height: 14px;
    background: #50C0A8;
    border-radius: 2px;
}}

.body-p {{
    font-size: 10.5px;
    line-height: 1.55;
    color: #334155;
    margin-bottom: 8px;
    text-align: justify;
}}

.highlight-box {{
    background: #F0FDF4;
    border-left: 3.5px solid #50C0A8;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 12px;
}}

.highlight-box p {{
    font-size: 10px;
    line-height: 1.5;
    color: #166534;
    font-weight: 500;
}}

/* Tablas estilizadas */
.table-custom {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0 14px 0;
    font-size: 9.5px;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

.table-custom th {{
    background: #0B1916;
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 9px;
    letter-spacing: 0.04em;
    padding: 7px 10px;
    text-align: left;
    border-bottom: 2px solid #50C0A8;
}}

.table-custom td {{
    padding: 6.5px 10px;
    border-bottom: 1px solid #E2E8F0;
    color: #334155;
    vertical-align: middle;
}}

.table-custom tr:nth-child(even) td {{
    background: #F8FAFC;
}}

.table-custom tr:last-child td {{
    border-bottom: none;
}}

/* Fichas de Activos */
.asset-card {{
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.03);
}}

.asset-card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}

.asset-card-title {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 12px;
    font-weight: 800;
    color: #0B1916;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.asset-badge {{
    font-family: 'Goldman', sans-serif;
    font-size: 10.5px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
}}

.badge-up {{ background: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }}
.badge-down {{ background: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }}

.asset-chart-img {{
    width: 100%;
    height: 145px;
    object-fit: contain;
    border-radius: 4px;
    border: 1px solid #CBD5E1;
    margin: 4px 0 8px 0;
    background: #FFFFFF;
    display: block;
}}

.three-layers {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 9.5px;
    line-height: 1.45;
}}

.layer-item {{
    display: flex;
    gap: 6px;
}}

.layer-label {{
    font-weight: 800;
    color: #0F172A;
    min-width: 135px;
}}

.layer-prohibited {{
    color: #991B1B;
    background: #FEF2F2;
    padding: 2px 6px;
    border-radius: 4px;
    border-left: 3px solid #DC2626;
}}

/* Portada Estilo Editorial Oscuro */
.cover-page {{
    background: #04100D;
    color: #FFFFFF;
    padding: 24mm 22mm;
    justify-content: space-between;
}}

.cover-bg-glow {{
    position: absolute;
    top: 0; right: 0; bottom: 0; left: 0;
    background: radial-gradient(circle at 85% 15%, rgba(80, 192, 168, 0.22) 0%, transparent 65%),
                radial-gradient(circle at 15% 85%, rgba(62, 145, 175, 0.16) 0%, transparent 60%),
                linear-gradient(135deg, #061814 0%, #020806 100%);
    z-index: 0;
}}

.cover-content {{
    position: relative;
    z-index: 1;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}

.cover-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(80, 192, 168, 0.3);
    padding-bottom: 14px;
}}

.cover-logo {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.cover-logo-icon {{
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #50C0A8, #3E91AF);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Goldman', sans-serif;
    font-weight: 700;
    font-size: 16px;
    color: #04100D;
}}

.cover-logo-text {{
    font-family: 'Goldman', sans-serif;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #FFFFFF;
}}

.cover-badge {{
    background: rgba(80, 192, 168, 0.15);
    border: 1px solid rgba(80, 192, 168, 0.4);
    color: #50C0A8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    padding: 5px 14px;
    border-radius: 100px;
}}

.cover-hero {{
    margin: 20px 0;
}}

.cover-kicker {{
    font-size: 11px;
    font-weight: 700;
    color: #3E91AF;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 8px;
}}

.cover-title {{
    font-family: 'Goldman', sans-serif;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.18;
    color: #FFFFFF;
    margin-bottom: 12px;
}}

.cover-title span {{ color: #50C0A8; }}

.cover-subtitle {{
    font-size: 12.5px;
    color: #C1E5E4;
    line-height: 1.55;
    max-width: 90%;
    margin-bottom: 16px;
}}

.cover-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 14px;
}}

.cover-card {{
    background: rgba(8, 28, 23, 0.7);
    border: 1px solid rgba(80, 192, 168, 0.25);
    border-radius: 8px;
    padding: 10px 12px;
}}

.cover-card-header {{
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #94A3B8;
    font-weight: 700;
    margin-bottom: 4px;
}}

.cover-card-price {{
    font-family: 'Goldman', sans-serif;
    font-size: 18px;
    color: #FFFFFF;
    font-weight: 700;
}}

.cover-card-driver {{
    font-size: 9px;
    color: #718096;
    margin-top: 4px;
    line-height: 1.35;
}}

/* Escenarios */
.scenario-card {{
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 8px;
}}

.scenario-pos {{ background: #F0FDF4; border: 1px solid #86EFAC; border-left: 4px solid #16A34A; }}
.scenario-base {{ background: #FEFCE8; border: 1px solid #FDE047; border-left: 4px solid #CA8A04; }}
.scenario-risk {{ background: #FEF2F2; border: 1px solid #FCA5A5; border-left: 4px solid #DC2626; }}

.scenario-title {{
    font-size: 10.5px;
    font-weight: 800;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}}

.scenario-pos .scenario-title {{ color: #15803D; }}
.scenario-base .scenario-title {{ color: #A16207; }}
.scenario-risk .scenario-title {{ color: #B91C1C; }}

.scenario-bullets {{
    font-size: 9.5px;
    color: #334155;
    line-height: 1.45;
    padding-left: 14px;
}}
"""
