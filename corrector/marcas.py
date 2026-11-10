"""Coloca cada fallo sobre su fragmento exacto del texto original."""
from dataclasses import dataclass


@dataclass
class Fallo:
    original: str
    correccion: str
    tipo: str
    explicacion: str
    numero: int = 0
    colocado: bool = False


def _buscar(texto: str, fragmento: str, desde: int) -> int:
    pos = texto.find(fragmento, desde)
    if pos < 0:
        pos = texto.lower().find(fragmento.lower(), desde)
    return pos


def segmentar(texto: str, fallos: list[Fallo]) -> list[dict]:
    """Devuelve trozos de texto: {"texto"} normales o {"texto","numero","correccion","tipo"} marcados.

    Los fallos se buscan en orden a partir del anterior; si uno no aparece, se busca desde el
    principio sin solaparse con lo ya marcado. Los que no se encuentran quedan con colocado=False
    (salen en la explicación, pero sin marca).
    """
    for n, f in enumerate(fallos, 1):
        f.numero = n
    marcas: list[tuple[int, int, Fallo]] = []
    cursor = 0
    for f in fallos:
        frag = f.original.strip()
        if not frag:
            continue
        pos = _buscar(texto, frag, cursor)
        if pos < 0:
            pos = _buscar(texto, frag, 0)
            while pos >= 0 and any(a < pos + len(frag) and pos < b for a, b, _ in marcas):
                pos = _buscar(texto, frag, pos + 1)
        if pos < 0:
            continue
        marcas.append((pos, pos + len(frag), f))
        f.colocado = True
        cursor = pos + len(frag)
    marcas.sort(key=lambda m: m[0])

    trozos: list[dict] = []
    actual = 0
    for a, b, f in marcas:
        if a > actual:
            trozos.append({"texto": texto[actual:a]})
        trozos.append({"texto": texto[a:b], "numero": f.numero, "correccion": f.correccion,
                       "tipo": f.tipo})
        actual = b
    if actual < len(texto):
        trozos.append({"texto": texto[actual:]})
    return trozos
