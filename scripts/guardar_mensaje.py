"""
Guarda el mensaje generado como .txt listo para copiar al grupo.
Uso: python guardar_mensaje.py <tipo> <contenido>
Tipos: alerta, apertura, concepto, encuesta, señal, noticia, dato_macro, cierre, pregunta
"""
import sys
import os
from datetime import datetime

def guardar(tipo: str, contenido: str) -> str:
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M")
    nombre = f"{fecha}_{tipo}.txt"
    ruta_dir = os.path.join(os.path.dirname(__file__), "..", "data", "mensajes")
    os.makedirs(ruta_dir, exist_ok=True)
    ruta = os.path.join(ruta_dir, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python guardar_mensaje.py <tipo> <contenido>")
        sys.exit(1)
    tipo = sys.argv[1]
    contenido = " ".join(sys.argv[2:])
    ruta = guardar(tipo, contenido)
    print(f"✓ Guardado en: {ruta}")
