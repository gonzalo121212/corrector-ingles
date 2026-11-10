from dataclasses import asdict
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from corrector import config, ia
from corrector.marcas import segmentar

STATIC = Path(__file__).parent / "static"
PUERTO = 8766
HOSTS = {f"127.0.0.1:{PUERTO}", f"localhost:{PUERTO}"}
ORIGENES = {f"http://127.0.0.1:{PUERTO}", f"http://localhost:{PUERTO}"}
MAX_CARACTERES = 800


def create_app(corregir=ia.corregir, allowed_hosts: set[str] | None = None,
               cargar_env=config.cargar_env) -> FastAPI:
    hosts = set(HOSTS if allowed_hosts is None else allowed_hosts)
    app = FastAPI(title="Corrector de inglés")

    @app.middleware("http")
    async def proteger(request: Request, call_next):
        origen = request.headers.get("origin")
        if request.headers.get("host") not in hosts or (
                request.method != "GET" and origen is not None and origen not in ORIGENES):
            return JSONResponse({"detail": "Petición no permitida"}, status_code=403)
        return await call_next(request)

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.post("/api/corregir")
    def api_corregir(texto: str = Body(..., embed=True)):
        texto = texto.strip()
        if not texto:
            raise HTTPException(400, "Escribe una frase en inglés")
        if len(texto) > MAX_CARACTERES:
            raise HTTPException(400, f"Texto demasiado largo (máximo {MAX_CARACTERES} caracteres)")
        cargar_env()
        try:
            r = corregir(texto)
        except ia.ErrorIA as e:
            raise HTTPException(502, str(e)) from None
        trozos = segmentar(texto, r["fallos"])
        return {
            "texto": texto,
            "trozos": trozos,
            "fallos": [asdict(f) for f in r["fallos"]],
            "texto_corregido": r["texto_corregido"],
            "aviso": r["aviso"],
            "correcto": not r["fallos"] and not r["aviso"],
            "modelo": ia.modelo(),
        }

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app
