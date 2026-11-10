from corrector.marcas import Fallo, segmentar


def f(original, correccion="x", tipo="gramatica"):
    return Fallo(original, correccion, tipo, "porque sí")


def unir(trozos):
    return "".join(t["texto"] for t in trozos)


def test_marca_en_orden():
    texto = "Yesterday I go to the office and they didn't listened me."
    fallos = [f("go", "went"), f("listened me", "listen to me")]
    trozos = segmentar(texto, fallos)
    assert unir(trozos) == texto
    marcados = [t for t in trozos if "numero" in t]
    assert [(t["texto"], t["numero"], t["correccion"]) for t in marcados] == [
        ("go", 1, "went"), ("listened me", 2, "listen to me")]
    assert all(x.colocado for x in fallos)


def test_no_confunde_palabra_repetida():
    # "go" aparece dentro de "ago" antes; el segundo fallo "go" debe ir tras el primero
    texto = "I go there and I go home."
    trozos = segmentar(texto, [f("go", "went"), f("go", "went")])
    posiciones = []
    i = 0
    for t in trozos:
        if "numero" in t:
            posiciones.append(i)
        i += len(t["texto"])
    assert posiciones == [2, 17]


def test_desordenado_se_busca_desde_el_principio_sin_solapar():
    texto = "He have a dog and she have a cat."
    fallos = [f("she have", "she has"), f("He have", "He has")]
    trozos = segmentar(texto, fallos)
    assert unir(trozos) == texto
    assert [t["numero"] for t in trozos if "numero" in t] == [2, 1]


def test_mayusculas_distintas_y_fragmento_inexistente():
    texto = "i am agree with you."
    fallos = [f("I am agree", "I agree"), f("no existe", "y")]
    trozos = segmentar(texto, fallos)
    assert trozos[0] == {"texto": "i am agree", "numero": 1, "correccion": "I agree", "tipo": "gramatica"}
    assert fallos[1].colocado is False and fallos[1].numero == 2
    assert unir(trozos) == texto


def test_sin_fallos():
    assert segmentar("All good.", []) == [{"texto": "All good."}]
