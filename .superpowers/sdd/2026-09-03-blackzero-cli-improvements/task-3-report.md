# Informe Task 3

## Alcance implementado

- `blackzero/downloader.py`: motor HTTP/HTTPS de una transferencia con `requests.Session`, respuestas administradas por contexto, timeout de conexión/lectura, chunks de 64 KiB, reintentos acotados y `Retry-After` numérico.
- El motor consume los contratos de Task 1 y los helpers de Task 2 para seleccionar destinos, escribir `.part` y finalizar de forma atómica.
- Incluye validación de URL, errores tipados (`input`, `http`, `network`, `filesystem`, `checksum`), progreso con tamaño conocido o desconocido, reanudación Range/206, reinicio seguro ante respuesta 200 y ante cambio de nombre por `Content-Disposition`.
- SHA-256 se calcula incrementalmente; un desajuste elimina el archivo final. Los parciales se eliminan en `finally` salvo `keep_partial`.
- `tests/test_downloader.py`: fixture HTTP local y 15 pruebas sin red externa que cubren streaming, tamaños conocidos/desconocidos, timeout, cierre de respuesta, estados reintentables y permanentes, limpieza, reanudación, fallback, checksum y la regresión de cambio de nombre durante una reanudación.

## TDD

- RED inicial: `pytest tests/test_downloader.py -q` produjo 13 fallos esperados porque `blackzero.downloader` no existía.
- Se implementó la mínima capa de transferencia y se llevaron los casos a verde.
- Se añadieron y observaron en rojo dos regresiones adicionales: limpieza de un parcial previo tras fallo de reanudación y prevención de un archivo truncado cuando `Content-Disposition` cambia el destino de una respuesta 206. Ambas quedaron cubiertas en la suite final.

## Commit

- `72b87f8 feat: add reliable streamed downloads`

## Comandos y resultados

- `PYTHONPATH=<worktree> pytest tests/test_downloader.py -q`: **15 passed**.
- `PYTHONPATH=<worktree> pytest -q`: **34 passed**.
- `C:\Users\ingmo\AppData\Local\Programs\Python\Python312\python.exe -m compileall -q blackzero`: **correcto**.
- `git diff --cached --check`: **correcto** antes del commit enmendado.

## Preocupaciones

- La reanudación usa Range de forma optimista cuando encuentra un `.part`; si el servidor no lo respeta, se reinicia de forma segura con la respuesta 200. No se hace una petición HEAD adicional para evitar una ronda de red extra y depender de cabeceras que algunos servidores omiten.
- El worktree ya contenía cambios no relacionados en documentación y artefactos SDD; no se modificaron ni se incluyeron en el commit de Task 3.
- El alias de Windows `python` está configurado hacia Microsoft Store en este entorno; la comprobación de sintaxis se ejecutó con el intérprete Python 3.12 absoluto que usa `pytest`.
