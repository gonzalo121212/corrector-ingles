"""Lee el archivo .env (clave y modelo) en cada corrección, sin necesidad de reiniciar."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV = RAIZ / ".env"
CLAVES = ("OPENAI_API_KEY", "OPENAI_MODEL")


def cargar_env(ruta: Path = ENV) -> None:
    try:
        lineas = ruta.read_text("utf-8-sig").splitlines()
    except OSError:
        return
    for linea in lineas:
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        nombre, valor = (x.strip() for x in linea.split("=", 1))
        if nombre in CLAVES:
            os.environ[nombre] = valor.strip('"').strip("'")
