"""Coloca cada fallo sobre su fragmento exacto del texto original."""
import re
from dataclasses import dataclass


@dataclass
class Fallo:
    original: str
    correccion: str
    tipo: str
    explicacion: str
    numero: int = 0
    colocado: bool = False
    veces: int = 0


def _patron(fragmento: str) -> re.Pattern:
    """Sin distinguir mayúsculas, espacios flexibles y sin cortar palabras por la mitad."""
    partes = [re.escape(p) for p in fragmento.split()]
    cuerpo = r"\s+".join(partes)
    inicio = r"(?<!\w)" if fragmento[:1].isalnum() else ""
    fin = r"(?!\w)" if fragmento[-1:].isalnum() else ""
    return re.compile(inicio + cuerpo + fin, re.IGNORECASE)


def _repetible(f: Fallo) -> bool:
    """Se marca en todas sus apariciones si no depende del contexto (falta de ortografía o
    fragmento de varias palabras)."""
    return f.tipo == "ortografia" or len(f.original.split()) >= 2


def _ajustar_mayuscula(encontrado: str, correccion: str) -> str:
    if encontrado[:1].isupper() and correccion[:1].islower():
        return correccion[:1].upper() + correccion[1:]
    return correccion


def _casi_igual(encontrado: str, original: str) -> bool:
    a, b = " ".join(encontrado.split()), " ".join(original.split())
    return a[1:] == b[1:] and a[:1].lower() == b[:1].lower()


def segmentar(texto: str, fallos: list[Fallo]) -> list[dict]:
    """Devuelve trozos: {"texto"} normales o {"texto","numero","correccion","tipo"} marcados.

    Cada fallo se coloca en la primera aparición libre (sin solaparse con otra marca). Si es
    repetible, también en las demás apariciones libres, con el mismo número. Los que no se
    encuentran quedan con colocado=False: salen en la explicación, pero sin marca.
    """
    marcas: list[tuple[int, int, Fallo]] = []

    def libre(a: int, b: int) -> bool:
        return not any(x < b and a < y for x, y, _ in marcas)

    for n, f in enumerate(fallos, 1):
        f.numero, f.colocado, f.veces = n, False, 0
    # Los fragmentos largos primero: si la IA da "i" y también "How i can use", gana la frase
    # completa, cuya corrección ya incluye la pequeña.
    for f in sorted(fallos, key=lambda x: -len(x.original.strip())):
        original = f.original.strip()
        if not original:
            continue
        candidatos = [m for m in _patron(original).finditer(texto)
                      if libre(m.start(), m.end())
                      and m.group() != _ajustar_mayuscula(m.group(), f.correccion)]
        # Preferir las apariciones iguales salvo, como mucho, la mayúscula inicial.
        buenos = [m for m in candidatos if _casi_igual(m.group(), original)] or candidatos[:1]
        for m in buenos:
            if not libre(m.start(), m.end()):
                continue
            marcas.append((m.start(), m.end(), f))
            f.colocado = True
            f.veces += 1
            if not _repetible(f):
                break
    marcas.sort(key=lambda m: m[0])

    # Numerar de izquierda a derecha; los no colocados, al final.
    orden: list[Fallo] = []
    for _, _, f in marcas:
        if f not in orden:
            orden.append(f)
    orden += [f for f in fallos if not f.colocado]
    for n, f in enumerate(orden, 1):
        f.numero = n

    trozos: list[dict] = []
    actual = 0
    for a, b, f in marcas:
        if a > actual:
            trozos.append({"texto": texto[actual:a]})
        trozos.append({"texto": texto[a:b], "numero": f.numero,
                       "correccion": _ajustar_mayuscula(texto[a:b], f.correccion), "tipo": f.tipo})
        actual = b
    if actual < len(texto):
        trozos.append({"texto": texto[actual:]})
    return trozos


def visibles(fallos: list[Fallo], trozos: list[dict]) -> list[Fallo]:
    """Fallos para la explicación, en orden, sin los repetidos que ya cubre otra marca."""
    marcados = [" ".join(t["texto"].lower().split()) for t in trozos if "numero" in t]
    quedan = [f for f in fallos if f.colocado or not any(
        " ".join(f.original.lower().split()) in m for m in marcados)]
    quedan.sort(key=lambda f: f.numero)
    for n, f in enumerate(quedan, 1):
        if f.numero != n:  # solo pueden cambiar los no colocados, que van al final
            f.numero = n
    return quedan


def texto_corregido(trozos: list[dict]) -> str:
    return "".join(t.get("correccion", t["texto"]) for t in trozos)
