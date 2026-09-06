"""Tests del hook de ingesta macro (SessionStart).

Por qué este hook exige cobertura exhaustiva:
1. Corre en cada arranque de sesión de Claude Code de forma automática. Un fallo
   no controlado o un código de retorno distinto de cero tumbaría la inicialización
   de la sesión del usuario.
2. Si la lógica de vencimiento (`esta_vencida`) falla o diverge entre modos, el
   modelo inyecta cifras macro desactualizadas creyendo que están frescas mientras
   en background se ejecuta una actualización, publicando datos viejos con fecha de hoy.
3. Si el manejo de locks falla, un proceso huérfano puede bloquear indefinidamente
   la actualización de datos macroeconómicos soberanos (BCCh, FRED, LME).
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for _p in (RAIZ / "scripts", RAIZ / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import hook_ingesta_macro as hook  # noqa: E402


@pytest.fixture(autouse=True)
def aislar_rutas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Aísla las rutas de datos del hook a un directorio temporal.

    Por qué es mandatorio: ninguna prueba puede escribir en 'data/' ni en
    'data central/', ni depender del estado real de ejecución del entorno
    del analista. Si una prueba escribiera en producción, alteraría el reloj
    de ingesta de la siguiente sesión real de trabajo.
    """
    estado_dir = tmp_path / "data central" / "DATA AGENDA"
    estado_dir.mkdir(parents=True, exist_ok=True)
    estado_path = estado_dir / "estado_ejecucion.json"

    lock_dir = tmp_path / "data"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / ".ingesta_macro.lock"

    log_dir = tmp_path / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "hook_ingesta_macro.log"

    monkeypatch.setattr(hook, "ESTADO", estado_path)
    monkeypatch.setattr(hook, "LOCK", lock_path)
    monkeypatch.setattr(hook, "LOG", log_path)

    return {
        "estado": estado_path,
        "lock": lock_path,
        "log": log_path,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Lectura del archivo de estado
# ─────────────────────────────────────────────────────────────────────────────
def test_leer_estado_archivo_inexistente():
    """Si el archivo de estado no existe, debe devolver None sin lanzar excepción.

    Un clon nuevo del repositorio o un ambiente recién desplegado no cuenta con
    el JSON de agenda macro. El hook debe tolerar la ausencia sin interrumpir
    la apertura de Claude Code.
    """
    assert hook.ESTADO.exists() is False
    assert hook.leer_estado() is None


def test_leer_estado_archivo_corrupto():
    """Un archivo de estado con JSON truncado o corrupto debe devolver None.

    Si una escritura previa falló a la mitad por corte de energía o caída de red,
    el archivo contendrá bytes inválidos. La lectura debe atrapar cualquier error
    para evitar que un JSON roto detenga el inicio de la sesión.
    """
    hook.ESTADO.write_text("{este_no_es_un_json_valido:", encoding="utf-8")
    assert hook.leer_estado() is None


def test_leer_estado_exitoso():
    """Debe parsear correctamente el contenido cuando el JSON es válido.

    Asegura que el contrato de claves esperado por los siguientes pasos
    sea recibido íntegramente como diccionario estándar.
    """
    datos = {"ultima_ejecucion_utc": "2026-09-06T12:00:00+00:00", "status": "OK"}
    hook.ESTADO.write_text(json.dumps(datos), encoding="utf-8")
    assert hook.leer_estado() == datos


# ─────────────────────────────────────────────────────────────────────────────
# Antigüedad en horas
# ─────────────────────────────────────────────────────────────────────────────
def test_antiguedad_horas_estado_ausente_o_sin_marca():
    """Sin estado o sin marca temporal UTC, la antigüedad no se puede calcular.

    Devolver None (en lugar de 0 o un valor inventado) es fundamental porque
    0 significaría que la ingesta acaba de ocurrir, impidiendo que el sistema
    advierta la necesidad de refresco.
    """
    assert hook.antiguedad_horas(None) is None
    assert hook.antiguedad_horas({}) is None
    assert hook.antiguedad_horas({"otra_clave": 123}) is None
    assert hook.antiguedad_horas({"ultima_ejecucion_utc": ""}) is None
    assert hook.antiguedad_horas({"ultima_ejecucion_utc": None}) is None


def test_antiguedad_horas_marca_ilegible():
    """Formatos no conformes o tipos incompatibles deben retornar None sin lanzar.

    Si el campo contiene texto corrupto, números enteros o estructuras inválidas,
    la función no puede explotar con ValueError ni TypeError: debe retornar None
    para que la guardia decida refrescar de forma segura.
    """
    assert hook.antiguedad_horas({"ultima_ejecucion_utc": "fecha-invalida"}) is None
    assert hook.antiguedad_horas({"ultima_ejecucion_utc": 123456789}) is None
    assert hook.antiguedad_horas({"ultima_ejecucion_utc": ["2026-09-06"]}) is None


def test_antiguedad_horas_calculo_correcto_aware_y_naive():
    """Calcula correctamente las horas transcurridas tanto en UTC aware como naive.

    El pipeline de datos macroeconómicos a veces serializa ISO con offset explícito
    (+00:00 o Z) y otras veces strings sin zona. Ambos deben tratarse como UTC
    para que el delta horario sea exacto y no sufra desfases por hora local.
    """
    ahora = datetime.now(timezone.utc)

    # Caso 1: con zona UTC explícita (+00:00)
    marca_aware = (ahora - timedelta(hours=3.5)).isoformat()
    resultado_aware = hook.antiguedad_horas({"ultima_ejecucion_utc": marca_aware})
    assert resultado_aware is not None
    assert abs(resultado_aware - 3.5) < 0.05

    # Caso 2: naive (sin zona explícita, se asume UTC según el módulo)
    marca_naive = (ahora - timedelta(hours=2.0)).strftime("%Y-%m-%dT%H:%M:%S")
    resultado_naive = hook.antiguedad_horas({"ultima_ejecucion_utc": marca_naive})
    assert resultado_naive is not None
    assert abs(resultado_naive - 2.0) < 0.05


# ─────────────────────────────────────────────────────────────────────────────
# Decisión de vencimiento (esta_vencida)
# ─────────────────────────────────────────────────────────────────────────────
def test_esta_vencida_fail_closed_cuando_no_hay_registro():
    """Si no sabemos cuándo fue la última ingesta, se asume vencida (fail-closed).

    Por qué es crítico: en un clon nuevo o tras borrar temporales, asumir que
    los datos están frescos causaría que el sistema nunca descargue las series
    macroeconómicas iniciales. El valor por defecto siempre debe refrescar.
    """
    assert hook.esta_vencida(None) is True
    assert hook.esta_vencida({}) is True
    assert hook.esta_vencida({"ultima_ejecucion_utc": "formato-roto"}) is True


def test_esta_vencida_por_debajo_del_umbral():
    """Dentro de las 6 horas de umbral, los datos se consideran frescos.

    Refrescar con mayor frecuencia saturaría las APIs de los bancos centrales
    (FRED y BCCh), que publican cifras solo una o dos veces al día.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=5.9)).isoformat()
    assert hook.esta_vencida({"ultima_ejecucion_utc": marca}) is False


def test_esta_vencida_exactamente_en_el_umbral():
    """En el límite exacto de 6 horas, la condición `>= UMBRAL_HORAS` debe vencer.

    Verifica el comportamiento de frontera del código (`horas >= UMBRAL_HORAS`).
    Al cumplir 6 horas completas la sesión de la tarde ya no debe depender
    del cierre de la mañana, por lo que debe disparar el refresco.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=6.0)).isoformat()
    assert hook.esta_vencida({"ultima_ejecucion_utc": marca}) is True


def test_esta_vencida_por_encima_del_umbral():
    """Superadas las 6 horas, el estado debe marcarse inequívocamente como vencido.

    Garantiza que cualquier sesión abierta con datos añejos alerte al analista
    y habilite la descarga de los nuevos indicadores macro.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=6.1)).isoformat()
    assert hook.esta_vencida({"ultima_ejecucion_utc": marca}) is True


# ─────────────────────────────────────────────────────────────────────────────
# Concurrencia y expiración de lock (lock_vigente)
# ─────────────────────────────────────────────────────────────────────────────
def test_lock_vigente_sin_archivo():
    """Si no existe el archivo de lock, no hay otra ingesta en curso.

    Permite que la sesión tome el lock y dispare la ingesta sin falsos positivos.
    """
    hook.LOCK.unlink(missing_ok=True)
    assert hook.lock_vigente() is False


def test_lock_vigente_con_lock_reciente():
    """Un lock creado hace pocos minutos indica un proceso vivo en curso.

    Evita que dos ventanas simultáneas de Claude Code corran pipelines paralelos
    que colisionen escribiendo sobre los mismos archivos JSON de 'data central/'.
    """
    hook.LOCK.write_text("9999 2026-09-06T14:00:00Z\n", encoding="utf-8")
    mtime_reciente = time.time() - 60  # Hace 1 minuto
    os.utime(hook.LOCK, (mtime_reciente, mtime_reciente))
    assert hook.lock_vigente() is True


def test_lock_vigente_con_lock_huerfano_expirado():
    """Un lock con más de 15 minutos se considera huérfano y se ignora.

    La ingesta real demora ~55 segundos. Un lock de 16 minutos solo ocurre si un
    proceso previo murió abruptamente sin pasar por su bloque `finally`. Si no se
    ignorara, bloquearía indefinidamente la ingesta macro en todo el repositorio.
    """
    hook.LOCK.write_text("9999 2026-09-06T13:00:00Z\n", encoding="utf-8")
    mtime_viejo = time.time() - (hook.LOCK_HUERFANO_MIN * 60 + 30)  # 15.5 minutos
    os.utime(hook.LOCK, (mtime_viejo, mtime_viejo))
    assert hook.lock_vigente() is False


def test_lock_vigente_tolerancia_a_errores_stat(monkeypatch: pytest.MonkeyPatch):
    """Cualquier excepción al inspeccionar el archivo de lock debe retornar False.

    Problemas de permisos temporales en Windows o condiciones de carrera donde el
    archivo es eliminado entre la comprobación y el stat no deben interrumpir el hook.
    """
    mock_lock = MagicMock()
    mock_lock.stat.side_effect = OSError("Error simulado de acceso a disco en Windows")
    monkeypatch.setattr(hook, "LOCK", mock_lock)
    assert hook.lock_vigente() is False


# ─────────────────────────────────────────────────────────────────────────────
# Conversión horaria a Santiago de Chile (hora_chile)
# ─────────────────────────────────────────────────────────────────────────────
def test_hora_chile_marca_valida():
    """Convierte marcas ISO UTC al huso horario oficial de Chile (regla canónica).

    Toda publicación y reporte al analista debe expresarse en hora local chilena
    para mantener consistencia con los horarios de apertura y cierre del mercado.
    """
    # 2026-09-06 14:30 UTC -> en Santiago (UTC-4 / UTC-3) debe formatear como YYYY-MM-DD HH:MM
    resultado = hook.hora_chile("2026-09-06T14:30:00Z")
    assert len(resultado) == 16
    assert resultado.startswith("2026-09-06")
    assert ":" in resultado


def test_hora_chile_marca_invalida_nunca_lanza():
    """Entradas corruptas o vacías no deben lanzar jamás excepción.

    Un dato con formato inesperado no puede impedir que el contexto del modelo
    se arme. Si falla la conversión, debe devolver el string original o 'desconocida'.
    """
    assert hook.hora_chile("marca_corrupta") == "marca_corrupta"
    assert hook.hora_chile("") == "desconocida"
    assert hook.hora_chile(None) == "desconocida"


# ─────────────────────────────────────────────────────────────────────────────
# Formateo del texto de estado para el contexto del modelo (texto_estado)
# ─────────────────────────────────────────────────────────────────────────────
def test_texto_estado_sin_registro_avisa_falta_y_refresco():
    """Si no hay estado, advierte que no hay cifras macro y que corre ingesta.

    Alerta al modelo para que no invente ni cite cifras de bancos centrales
    mientras la base de datos se encuentra vacía.
    """
    texto = hook.texto_estado(None)
    assert "[DATOS MACRO]" in texto
    assert "No hay registro de ingesta previa" in texto
    assert "hasta que termine no hay datos de bancos centrales que citar" in texto


def test_texto_estado_completo_con_fuentes_antiguedad_y_errores():
    """Verifica que el texto incluya el desglose de fuentes, antigüedad y fallas.

    El modelo necesita conocer qué APIs respondieron (BCCh, FRED) y si hubo errores
    parciales para no asumir que los datos ausentes equivalen a una variación cero.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=2.0)).isoformat()
    estado = {
        "ultima_ejecucion_utc": marca,
        "status_por_fuente": {"BCCh": "OK", "FRED": "OK"},
        "errores_por_fuente": {"COMMODITIES": "Timeout en LME"},
        "hay_novedades": True,
        "novedades_detalle": ["Tasa TPM se mantiene en 5.5%"],
    }
    texto = hook.texto_estado(estado)

    assert "BCCh OK" in texto
    assert "FRED OK" in texto
    assert "hace 2.0 h" in texto
    assert "COMMODITIES: Timeout en LME" in texto
    assert "Tasa TPM se mantiene en 5.5%" in texto
    assert "Dentro del umbral de 6 h: no se refresco nada." in texto


def test_texto_estado_vencido_advierte_cambio_inminente_de_cifras():
    """Cuando está vencida, DEBE advertir que los datos van a mutar en la sesión.

    Esta advertencia es la única defensa contra el anacronismo: evita que el
    modelo lea y cite un dato viejo justo antes de que el proceso en background
    escriba el nuevo archivo sobre disco.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=8.0)).isoformat()
    estado = {
        "ultima_ejecucion_utc": marca,
        "status_por_fuente": {"BCCh": "OK"},
    }
    texto = hook.texto_estado(estado)

    assert "Supera el umbral de 6 h" in texto
    assert "van a cambiar durante esta sesion" in texto
    assert "releelos antes de citar cifras macro" in texto


# ─────────────────────────────────────────────────────────────────────────────
# Envoltorio del hook SessionStart (modo_estado)
# ─────────────────────────────────────────────────────────────────────────────
def test_modo_estado_estructura_json_y_contexto_anidado(capsys: pytest.CaptureFixture):
    """La salida debe ser JSON válido con additionalContext estrictamente anidado.

    Si additionalContext se emitiera en la raíz del objeto en lugar de adentro
    de `hookSpecificOutput`, Claude Code lo ignora en silencio. Este test blinda
    el contrato de interoperabilidad del hook.
    """
    hook.modo_estado()
    salida = capsys.readouterr().out.strip()

    data = json.loads(salida)
    assert "hookSpecificOutput" in data
    assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "additionalContext" in data["hookSpecificOutput"]
    assert len(data["hookSpecificOutput"]["additionalContext"]) > 0
    assert data["suppressOutput"] is True


def test_modo_estado_incluye_system_message_cuando_vencida(capsys: pytest.CaptureFixture):
    """Si los datos están vencidos, debe incluir systemMessage para notificar al usuario.

    Proporciona feedback visual inmediato en la interfaz de Claude Code avisando
    que el refresco de bancos centrales se encuentra corriendo en background.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=9.0)).isoformat()
    hook.ESTADO.write_text(
        json.dumps({"ultima_ejecucion_utc": marca}), encoding="utf-8"
    )

    retorno = hook.modo_estado()
    assert retorno == 0

    salida = json.loads(capsys.readouterr().out.strip())
    assert "systemMessage" in salida
    assert "Datos macro vencidos" in salida["systemMessage"]


def test_modo_estado_no_incluye_system_message_cuando_fresca(capsys: pytest.CaptureFixture):
    """Si los datos están frescos, no debe emitir systemMessage superfluo.

    Evita ruidos o notificaciones innecesarias en cada sesión si los datos ya
    fueron actualizados recientemente.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=1.0)).isoformat()
    hook.ESTADO.write_text(
        json.dumps({"ultima_ejecucion_utc": marca}), encoding="utf-8"
    )

    retorno = hook.modo_estado()
    assert retorno == 0

    salida = json.loads(capsys.readouterr().out.strip())
    assert "systemMessage" not in salida


def test_modo_estado_retorna_cero_con_archivo_ausente_o_corrupto(capsys: pytest.CaptureFixture):
    """El modo estado DEBE retornar código 0 bajo cualquier circunstancia.

    Un error de red previo, archivo ausente o JSON corrupto jamás puede impedir
    que el analista abra Claude Code.
    """
    # 1. Sin archivo
    hook.ESTADO.unlink(missing_ok=True)
    assert hook.modo_estado() == 0

    # 2. Con archivo corrupto
    hook.ESTADO.write_text("{archivo_danado", encoding="utf-8")
    assert hook.modo_estado() == 0


# ─────────────────────────────────────────────────────────────────────────────
# Modo refresco y protección contra sobre-ejecución (modo_refrescar)
# ─────────────────────────────────────────────────────────────────────────────
def test_modo_refrescar_no_dispara_pipeline_si_datos_frescos(monkeypatch: pytest.MonkeyPatch):
    """Si los datos están frescos, no debe invocar subprocess ni crear lock.

    Garantiza que no se consuman recursos innecesarios ni se golpeen las APIs
    cuando la ingesta previa ocurrió hace menos de 6 horas.
    """
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=2.0)).isoformat()
    hook.ESTADO.write_text(
        json.dumps({"ultima_ejecucion_utc": marca}), encoding="utf-8"
    )

    mock_run = MagicMock()
    monkeypatch.setattr(hook.subprocess, "run", mock_run)

    retorno = hook.modo_refrescar()
    assert retorno == 0
    assert mock_run.call_count == 0
    assert hook.LOCK.exists() is False


def test_modo_refrescar_no_dispara_pipeline_si_lock_vigente(monkeypatch: pytest.MonkeyPatch):
    """Si otra sesión ya tiene la ingesta en curso, no debe disparar un proceso paralelo.

    Previene colisiones de escritura concurrentes en los JSON de 'data central/'.
    """
    # Estado vencido
    ahora = datetime.now(timezone.utc)
    marca = (ahora - timedelta(hours=10.0)).isoformat()
    hook.ESTADO.write_text(
        json.dumps({"ultima_ejecucion_utc": marca}), encoding="utf-8"
    )

    # Lock activo creado hace 2 minutos
    hook.LOCK.write_text("1111 2026-09-06T14:00:00Z\n", encoding="utf-8")
    mtime = time.time() - 120
    os.utime(hook.LOCK, (mtime, mtime))

    mock_run = MagicMock()
    monkeypatch.setattr(hook.subprocess, "run", mock_run)

    retorno = hook.modo_refrescar()
    assert retorno == 0
    assert mock_run.call_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# Registro en log y tolerancia de errores (anotar)
# ─────────────────────────────────────────────────────────────────────────────
def test_anotar_escribe_en_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verifica que anotar registre el mensaje con marca temporal.

    Permite auditar el comportamiento del hook en background sin interferir
    con el flujo principal.

    El log va a `tmp_path`, no al de verdad. La primera version de este test
    llamaba a `anotar` sin parchear `LOG` y le agregaba una linea a la bitacora
    operativa en cada corrida de la suite: un test que escribe en una ruta
    compartida ensucia lo que otro va a leer, y ademas contamina el registro que
    sirve para diagnosticar el hook.
    """
    monkeypatch.setattr(hook, "LOG", tmp_path / "hook.log")
    hook.anotar("evento de prueba del hook")
    assert hook.LOG.exists()
    contenido = hook.LOG.read_text(encoding="utf-8")
    assert "evento de prueba del hook" in contenido


def test_anotar_tolera_excepciones_sin_lanzar(monkeypatch: pytest.MonkeyPatch):
    """Si no se puede escribir el log (disco lleno, permisos), no debe fallar.

    El logging es de mejor esfuerzo; nunca debe propagar errores que aborten
    el refresco.
    """
    mock_log = MagicMock()
    mock_log.parent.mkdir.side_effect = OSError("Fallo simulado al crear directorio de logs")
    monkeypatch.setattr(hook, "LOG", mock_log)
    # No debe levantar excepción
    hook.anotar("mensaje que fallará")


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada de CLI (main)
# ─────────────────────────────────────────────────────────────────────────────
def test_main_por_defecto_ejecuta_modo_estado(capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch):
    """Sin argumentos, el comportamiento por defecto es --estado (bloqueante stdlib).

    SessionStart de Claude Code invoca el hook sin parámetros por defecto.
    """
    monkeypatch.setattr(sys, "argv", ["hook_ingesta_macro.py"])
    codigo = hook.main()
    assert codigo == 0

    salida = capsys.readouterr().out
    assert "SessionStart" in salida


def test_main_argumento_invalido_devuelve_codigo_dos(capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch):
    """Argumentos desconocidos deben retornar código 2 e imprimir uso en stderr.

    Cumple con el estándar POSIX para errores de sintaxis de argumentos en CLI.
    """
    monkeypatch.setattr(sys, "argv", ["hook_ingesta_macro.py", "--argumento-invalido"])
    codigo = hook.main()
    assert codigo == 2

    err = capsys.readouterr().err
    assert "uso: hook_ingesta_macro.py [--estado|--refrescar]" in err
