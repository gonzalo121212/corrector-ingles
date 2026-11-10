# Corrector de inglés

Escribe una frase o un texto corto en inglés (hasta 3-4 líneas) y te marca los fallos: arriba tu texto con cada error tachado y su corrección, debajo una explicación en español de cada uno y el texto corregido completo.

Usa un modelo de OpenAI (por defecto `gpt-4o-mini`) con tu clave.

## Primera vez

1. Abre el archivo `.env` de esta carpeta con el Bloc de notas y pega tu clave de OpenAI después de `OPENAI_API_KEY=`. Guarda.
2. Doble clic en `arrancar.bat`. La primera vez instala lo necesario (un par de minutos). Se abre el navegador en http://127.0.0.1:8766/.

Deja la ventana negra abierta mientras lo uses; para cerrarlo, cierra esa ventana.

## Uso

Escribe el texto y pulsa «Corregir» (o Ctrl+Intro).

- **Rojo:** error (gramática, vocabulario, ortografía o puntuación).
- **Ámbar:** sugerencia: es correcto, pero un nativo no lo diría así.

## Cambiar de modelo

En `.env`, cambia `OPENAI_MODEL` (por ejemplo `gpt-4.1-mini`). No hace falta reiniciar: se lee en cada corrección.

## Privacidad

El texto que escribes se envía a OpenAI para corregirlo. La clave solo está en `.env`, que no se sube a git.

## Tests

`.venv\Scripts\python -m pytest`
