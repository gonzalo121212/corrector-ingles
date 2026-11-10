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
    assert [t["numero"] for t in trozos if "numero" in t] == [1, 2]
    assert [x.original for x in sorted(fallos, key=lambda x: x.numero)] == ["He have", "she have"]


def test_mayusculas_distintas_y_fragmento_inexistente():
    texto = "i am agree with you."
    fallos = [f("I am agree", "I agree"), f("no existe", "y")]
    trozos = segmentar(texto, fallos)
    assert trozos[0] == {"texto": "i am agree", "numero": 1, "correccion": "I agree", "tipo": "gramatica"}
    assert fallos[1].colocado is False and fallos[1].numero == 2
    assert unir(trozos) == texto


def test_sin_fallos():
    assert segmentar("All good.", []) == [{"texto": "All good."}]


def test_error_repetido_se_marca_en_cada_aparicion():
    from corrector.marcas import texto_corregido
    texto = ("Hi! i have a cuple of cuestions. How i can use the word allright?\n\n"
             "how i can use the word allright?")
    fallos = [f("cuple", "couple", "ortografia"), f("allright", "alright", "ortografia"),
              f("how i can use", "how can I use", "gramatica")]
    trozos = segmentar(texto, fallos)
    marcados = [(t["texto"], t["numero"], t["correccion"]) for t in trozos if "numero" in t]
    assert marcados == [("cuple", 1, "couple"), ("How i can use", 2, "How can I use"),
                        ("allright", 3, "alright"), ("how i can use", 2, "how can I use"),
                        ("allright", 3, "alright")]
    assert texto_corregido(trozos) == ("Hi! i have a couple of cuestions. How can I use the word "
                                       "alright?\n\nhow can I use the word alright?")


def test_palabra_suelta_de_gramatica_no_se_repite_ni_corta_palabras():
    texto = "Its fine. The dog wagged its tail. Its late."
    trozos = segmentar(texto, [f("Its", "It's", "gramatica")])
    marcados = [t["texto"] for t in trozos if "numero" in t]
    assert marcados == ["Its"]
    assert trozos[0]["correccion"] == "It's"
    # "i" no se marca dentro de otras palabras
    trozos = segmentar("I think i am in it", [f("i", "I", "ortografia")])
    assert [t["texto"] for t in trozos if "numero" in t] == ["i"]


def test_gana_el_fragmento_largo_si_se_solapan():
    from corrector.marcas import texto_corregido
    texto = "How i can use it? I think i can."
    fallos = [f("i", "I", "ortografia"), f("How i can use it?", "How can I use it?", "gramatica")]
    trozos = segmentar(texto, fallos)
    marcados = [(t["texto"], t["numero"]) for t in trozos if "numero" in t]
    assert marcados == [("How i can use it?", 1), ("i", 2)]
    assert texto_corregido(trozos) == "How can I use it? I think I can."


def test_visibles_quita_repetidos_cubiertos():
    from corrector.marcas import visibles
    texto = "how i can use it? how i can use it?"
    fallos = [f("i", "I", "ortografia"), f("how i can use it?", "How can I use it?"),
              f("how i can use it?", "How can I use it?"), f("no existe", "z")]
    trozos = segmentar(texto, fallos)
    v = visibles(fallos, trozos)
    # La primera entrada ya marca las dos apariciones; la segunda y la "i" sobran.
    assert [(x.original, x.numero, x.colocado) for x in v] == [
        ("how i can use it?", 1, True), ("no existe", 2, False)]
    assert [t["numero"] for t in trozos if "numero" in t] == [1, 1]
