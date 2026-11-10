import json
import os

import pytest
from fastapi.testclient import TestClient

from corrector import config, ia
from corrector.app import create_app
from corrector.marcas import Fallo


def cliente(corregir):
    return TestClient(create_app(corregir=corregir, allowed_hosts={"testserver"},
                                 cargar_env=lambda: None))


def test_corrige_y_marca():
    def corregir(texto):
        return {"fallos": [Fallo("go", "went", "gramatica", "Pasado.")],
                "texto_corregido": "Yesterday I went home.", "aviso": ""}
    r = cliente(corregir).post("/api/corregir", json={"texto": "  Yesterday I go home.  "})
    assert r.status_code == 200
    d = r.json()
    assert d["texto"] == "Yesterday I go home."
    assert d["trozos"][1] == {"texto": "go", "numero": 1, "correccion": "went", "tipo": "gramatica"}
    assert d["fallos"][0]["colocado"] is True and d["correcto"] is False
    assert d["texto_corregido"] == "Yesterday I went home."


def test_frase_correcta():
    r = cliente(lambda t: {"fallos": [], "texto_corregido": t, "aviso": ""}).post(
        "/api/corregir", json={"texto": "All good."})
    assert r.json()["correcto"] is True


def test_vacio_y_demasiado_largo():
    c = cliente(lambda t: pytest.fail("no debe llamar a la IA"))
    assert c.post("/api/corregir", json={"texto": "   "}).status_code == 400
    assert c.post("/api/corregir", json={"texto": "a" * 801}).status_code == 400


def test_error_de_ia_llega_como_mensaje():
    def corregir(texto):
        raise ia.ErrorIA("La cuenta de OpenAI no tiene saldo")
    r = cliente(corregir).post("/api/corregir", json={"texto": "Hi"})
    assert r.status_code == 502 and "saldo" in r.json()["detail"]


def test_rechaza_otra_web():
    c = cliente(lambda t: pytest.fail("no debe llamar a la IA"))
    r = c.post("/api/corregir", json={"texto": "Hi"}, headers={"origin": "https://malo.com"})
    assert r.status_code == 403


def test_respuesta_de_ia_se_valida():
    buena = json.dumps({"correcto": False, "texto_corregido": "I went.", "aviso": "",
                        "fallos": [{"original": "go", "correccion": "went", "tipo": "raro",
                                    "explicacion": "x"}]})
    r = ia.corregir("I go.", llamar=lambda t: buena)
    assert r["fallos"][0].tipo == "gramatica" and r["texto_corregido"] == "I went."
    with pytest.raises(ia.ErrorIA):
        ia.corregir("I go.", llamar=lambda t: "no es json")
    with pytest.raises(ia.ErrorIA):
        ia.corregir("I go.", llamar=lambda t: '{"fallos": [{"original": "x"}]}')


def test_sin_clave(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ia.ErrorIA, match="Falta la clave"):
        ia._llamar_openai("Hi")


def test_cargar_env(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    env = tmp_path / ".env"
    env.write_text('﻿# comentario\nOPENAI_API_KEY = "sk-prueba"\nOTRA=1\nOPENAI_MODEL=\n', "utf-8")
    config.cargar_env(env)
    assert os.environ["OPENAI_API_KEY"] == "sk-prueba"
    assert "OTRA" not in os.environ
    assert ia.modelo() == "gpt-4o-mini"
    config.cargar_env(tmp_path / "no-existe")
