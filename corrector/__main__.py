"""Arranque: python -m corrector"""
import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from corrector.app import PUERTO, create_app

URL = f"http://127.0.0.1:{PUERTO}/"


def _puerto_ocupado() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", PUERTO)) == 0


def _abrir_cuando_responda(timeout: float = 30) -> None:
    fin = time.monotonic() + timeout
    while time.monotonic() < fin:
        try:
            with urllib.request.urlopen(URL, timeout=2):
                webbrowser.open(URL)
                return
        except Exception:
            time.sleep(0.5)


def main() -> None:
    if _puerto_ocupado():
        print("El corrector ya está abierto (o el puerto 8766 está ocupado).")
        webbrowser.open(URL)
        return
    threading.Thread(target=_abrir_cuando_responda, daemon=True).start()
    print(f"Corrector de inglés en {URL}  (cierra esta ventana para salir)")
    uvicorn.run(create_app(), host="127.0.0.1", port=PUERTO, log_level="warning")


if __name__ == "__main__":
    main()
