"""Corrección con un modelo de OpenAI (por defecto gpt-6-luna) y respuesta en formato fijo."""
import json
import os
from typing import Callable

from corrector.marcas import Fallo

MODELO_POR_DEFECTO = "gpt-6-luna"
TIPOS = ["gramatica", "vocabulario", "ortografia", "puntuacion", "naturalidad"]

INSTRUCCIONES = """Eres un profesor de inglés nativo que corrige frases de un alumno hispanohablante que está practicando.

Analiza el texto teniendo en cuenta el contexto de toda la frase: tiempos verbales, concordancia, preposiciones, palabras que suenan igual (their/there, its/it's), palabras que existen pero no encajan (affect/effect), falsos amigos del español (actually/currently, assist/attend, constipated...), orden de las palabras, ortografía y puntuación importante.

Método: revisa el texto frase por frase y palabra por palabra, de principio a fin, sin saltarte ninguna frase ni párrafo.

Reglas:
- Marca TODOS los errores. Si el mismo error aparece varias veces (aunque sea idéntico), incluye una entrada por cada aparición, en su orden.
- El pronombre "I" siempre va en mayúscula: cada "i" suelta es un error de ortografía. También la mayúscula al empezar frase.
- Marca solo errores reales. No cambies lo que ya es correcto, aunque tú lo dirías de otra forma. El inglés británico y el americano son igual de válidos.
- Usa el tipo "naturalidad" solo para algo gramaticalmente correcto pero que un nativo no diría así; es una sugerencia, no un error.
- "original" debe ser una copia EXACTA del fragmento del texto del alumno (mismas letras, mayúsculas y espacios), lo más corto posible pero con las palabras necesarias para entender el error. No solapes fragmentos.
- Lista los fallos en el orden en que aparecen en el texto.
- "correccion" es cómo debería quedar ese fragmento.
- "explicacion" va en español, en una o dos frases sencillas, diciendo por qué está mal y la regla que se aplica.
- "texto_corregido" es el texto completo, con todos sus párrafos y saltos de línea, con las correcciones aplicadas.
- Si no hay nada que corregir: "correcto" es true, "fallos" está vacío y "texto_corregido" es igual al original.
- Si el texto no está en inglés, devuelve "correcto": false, sin fallos, y "aviso" explicando en español que solo corriges inglés. En otro caso "aviso" es una cadena vacía."""

ESQUEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["correcto", "fallos", "texto_corregido", "aviso"],
    "properties": {
        "correcto": {"type": "boolean"},
        "fallos": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["original", "correccion", "tipo", "explicacion"],
                "properties": {
                    "original": {"type": "string"},
                    "correccion": {"type": "string"},
                    "tipo": {"type": "string", "enum": TIPOS},
                    "explicacion": {"type": "string"},
                },
            },
        },
        "texto_corregido": {"type": "string"},
        "aviso": {"type": "string"},
    },
}


class ErrorIA(Exception):
    pass


def modelo() -> str:
    return os.environ.get("OPENAI_MODEL", "").strip() or MODELO_POR_DEFECTO


def _crear(cliente, openai, **args):
    """Pide temperature=0 (respuestas más estables); los modelos que razonan, como gpt-6-luna,
    no lo admiten y entonces se repite sin ese ajuste."""
    try:
        return cliente.chat.completions.create(temperature=0, **args)
    except openai.BadRequestError as e:
        if "temperature" not in str(e).lower():
            raise
        return cliente.chat.completions.create(**args)


def _llamar_openai(texto: str) -> str:
    import openai

    clave = os.environ.get("OPENAI_API_KEY", "").strip()
    if not clave:
        raise ErrorIA("Falta la clave de OpenAI: pégala en el archivo .env de la carpeta del "
                      "programa (OPENAI_API_KEY=...), guárdalo y vuelve a probar.")
    cliente = openai.OpenAI(api_key=clave, timeout=120, max_retries=1)
    try:
        r = _crear(cliente, openai, model=modelo(),
                   messages=[{"role": "system", "content": INSTRUCCIONES},
                             {"role": "user", "content": texto}],
                   response_format={"type": "json_schema",
                                    "json_schema": {"name": "correccion", "strict": True,
                                                    "schema": ESQUEMA}})
    except openai.AuthenticationError:
        raise ErrorIA("OpenAI no acepta la clave del archivo .env. Revisa que esté bien copiada.") from None
    except openai.RateLimitError as e:
        if "quota" in str(e).lower():
            raise ErrorIA("La cuenta de OpenAI no tiene saldo (insufficient_quota).") from None
        raise ErrorIA("Demasiadas peticiones seguidas a OpenAI; espera unos segundos.") from None
    except openai.NotFoundError:
        raise ErrorIA(f"OpenAI no reconoce el modelo «{modelo()}». Revisa OPENAI_MODEL en .env.") from None
    except (openai.APIConnectionError, openai.APITimeoutError):
        raise ErrorIA("No se pudo conectar con OpenAI. Comprueba la conexión a Internet.") from None
    except openai.APIError as e:
        raise ErrorIA(f"OpenAI devolvió un error: {e}") from None
    contenido = r.choices[0].message.content
    if not contenido:
        raise ErrorIA("OpenAI no devolvió ninguna respuesta; prueba otra vez.")
    return contenido


def corregir(texto: str, llamar: Callable[[str], str] = _llamar_openai) -> dict:
    try:
        datos = json.loads(llamar(texto))
        fallos = [Fallo(str(f["original"]), str(f["correccion"]),
                        f["tipo"] if f["tipo"] in TIPOS else "gramatica", str(f["explicacion"]))
                  for f in datos["fallos"]]
        return {"fallos": fallos, "texto_corregido": str(datos["texto_corregido"]),
                "aviso": str(datos.get("aviso") or "")}
    except (ValueError, KeyError, TypeError) as e:
        raise ErrorIA("La respuesta de la IA no tenía el formato esperado; prueba otra vez.") from e
