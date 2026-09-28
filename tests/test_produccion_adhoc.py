# -*- coding: utf-8 -*-
"""Suite de pruebas para el módulo de Producción y Despacho Ad-hoc Sistematizado."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

import produccion_adhoc as pa


@pytest.fixture
def manifiesto_valido_tmp(tmp_path: Path) -> Path:
    """Genera un manifiesto válido temporal con textos conformes a guardrails."""
    png_falso = tmp_path / "story_test.png"
    png_falso.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 6000)

    txt_avisos = (
        "📊 *Subasta del Tesoro de EE.UU. a 20 Años (UST 20Y)*\n\n"
        "El Tesoro colocó USD 13.000 millones con rendimiento de 4,72%.\n\n"
        "💡 *Por qué importa*: El costo del dinero a largo plazo influye en el dólar global.\n\n"
        "Más detalles en #04_indices_bursatiles y #02_forex_divisas."
    )
    
    txt_indices = (
        "🇺🇸 *Impacto en Nasdaq 100 por Subasta UST 20Y*\n\n"
        "El rendimiento de 4,72% mantiene la presión sobre valoraciones tecnológicas.\n\n"
        "Soporte clave en 19,450.00 pts; resistencia en 19,800.00 pts.\n\n"
        "Seguimiento en vivo en #01_macro_y_apertura."
    )

    data = {
        "tanda": "2026-09-16_14-00_test_tanda",
        "descripcion": "Tanda de prueba sistematizada",
        "despachos": [
            {
                "canal": "01_macro_y_apertura",
                "alias": "avisos",
                "pieza": "test_macro",
                "activo": "UST20Y",
                "adjunto": str(png_falso),
                "archivo_txt": str(tmp_path / "test_macro.txt"),
                "mensaje_texto": txt_avisos,
            },
            {
                "canal": "04_indices_bursatiles",
                "alias": "indices",
                "pieza": "test_indices",
                "activo": "US100",
                "adjunto": str(png_falso),
                "archivo_txt": str(tmp_path / "test_indices.txt"),
                "mensaje_texto": txt_indices,
            },
        ],
    }

    ruta_manifiesto = tmp_path / "manifiesto.json"
    ruta_manifiesto.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta_manifiesto


def test_cargar_manifiesto_valido(manifiesto_valido_tmp: Path):
    datos = pa.cargar_manifiesto(manifiesto_valido_tmp)
    assert datos["tanda"] == "2026-09-16_14-00_test_tanda"
    assert len(datos["despachos"]) == 2


def test_cargar_manifiesto_invalido(tmp_path: Path):
    m_invalido = tmp_path / "invalido.json"
    m_invalido.write_text('{"solo_un_campo": 123}', encoding="utf-8")
    with pytest.raises(ValueError, match="El manifiesto requiere el campo 'tanda'"):
        pa.cargar_manifiesto(m_invalido)


def test_generar_artefactos_escribe_txt(manifiesto_valido_tmp: Path, tmp_path: Path):
    manifiesto = pa.cargar_manifiesto(manifiesto_valido_tmp)
    generados = pa.generar_artefactos(manifiesto, base_dir=tmp_path)
    
    txt_macro = tmp_path / "test_macro.txt"
    txt_indices = tmp_path / "test_indices.txt"
    
    assert txt_macro.exists()
    assert txt_indices.exists()
    assert "Subasta del Tesoro" in txt_macro.read_text(encoding="utf-8")
    assert "Impacto en Nasdaq" in txt_indices.read_text(encoding="utf-8")


def test_auditoria_guardrails_exitosa(manifiesto_valido_tmp: Path):
    manifiesto = pa.cargar_manifiesto(manifiesto_valido_tmp)
    # Generar los archivos txt primero
    pa.generar_artefactos(manifiesto)
    ok, errores = pa.auditar_manifiesto(manifiesto)
    assert ok, f"La auditoría debió pasar pero falló con: {errores}"
    assert len(errores) == 0


def test_auditoria_detecta_guion_largo(manifiesto_valido_tmp: Path, tmp_path: Path):
    manifiesto = pa.cargar_manifiesto(manifiesto_valido_tmp)
    # Inyectar un guión largo prohibido (em-dash)
    manifiesto["despachos"][0]["mensaje_texto"] = "Texto con guión largo — prohibido por regla."
    
    ok, errores = pa.auditar_manifiesto(manifiesto)
    assert not ok
    assert any("Guión largo prohibido" in e for e in errores)


def test_ejecutar_despacho_dry_run(manifiesto_valido_tmp: Path, tmp_path: Path):
    manifiesto = pa.cargar_manifiesto(manifiesto_valido_tmp)
    pa.generar_artefactos(manifiesto)
    
    with patch("produccion_adhoc.WhatsAppSender") as mock_sender_cls:
        mock_sender = MagicMock()
        mock_sender.enviar.return_value = {"status": "simulado", "destinatario": "avisos"}
        mock_sender_cls.return_value = mock_sender
        
        codigo = pa.ejecutar_despacho(manifiesto, dry_run=True)
        assert codigo == 0
        assert mock_sender.enviar.call_count == 2
