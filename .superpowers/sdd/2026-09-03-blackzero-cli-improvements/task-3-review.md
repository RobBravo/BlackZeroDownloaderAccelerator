# Revisión independiente — Task 3

## Veredicto

**No aprobado: requiere correcciones.** La base de la transferencia cumple gran parte del brief y la suite pasa, pero hay dos defectos de severidad alta que pueden producir corrupción silenciosa o pérdida de un archivo ya existente.

## Alcance revisado

- Brief: `task-3-brief.md`.
- Informe de implementación: `task-3-report.md`.
- Paquete/diff de `cc54907..72b87f8`: `task-3-review-package.md`.
- Contratos Task 1/2: `blackzero/models.py`, `blackzero/errors.py` y `blackzero/files.py`.
- Implementación y pruebas: `blackzero/downloader.py` y `tests/test_downloader.py`.

La ruta del paquete indicada inicialmente tenía un segmento `.superpowers/sdd/...` duplicado; se revisó el paquete real ubicado directamente en el directorio SDD de Task 3.

## Hallazgos

### [Alta] Un `206` cuyo rango no coincide con el offset solicitado se concatena como si fuera válido

**Evidencia de código:** `blackzero/downloader.py:147-161` considera reanudada cualquier respuesta `206` cuando existe un parcial, pero no analiza ni valida el inicio de `Content-Range`. `_total_size` (`:66-76`) solo extrae el total final de la cabecera.

**Reproducción independiente:** con `file.part = b"abc"`, una respuesta `206` con `Content-Range: bytes 0-5/6` y cuerpo `b"abcdef"` devuelve éxito con:

```text
b'abcabcdef'
True
```

El resultado está corrupto y se marca como `resumed=True`. Un servidor defectuoso, proxy o respuesta fuera de especificación puede por tanto entregar un archivo corrupto sin checksum y sin error.

**Cobertura ausente:** las pruebas de Range solo ejercen un servidor que responde exactamente al offset pedido. Debe añadirse un caso de inicio de `Content-Range` incorrecto y definirse una recuperación segura (reinicio desde cero o error sin finalizar el destino).

### [Alta] Un checksum fallido con `overwrite=True` destruye el destino preexistente

**Evidencia de código:** `blackzero/downloader.py:181` llama a `finalize_part(..., overwrite=True)` antes de comprobar el hash en `:183-186`. `finalize_part` usa `os.replace`, por lo que sustituye el archivo existente; después `destination.unlink()` borra ese nuevo destino ante un mismatch.

**Reproducción independiente:** con destino previo `file = b"old"`, una descarga `b"new"`, `overwrite=True` y checksum SHA-256 incorrecto produjo:

```text
checksum
False
```

`False` significa que el destino ya no existe. `--overwrite` autoriza reemplazar un resultado verificado, no perder el archivo anterior por una descarga que no supera la integridad.

**Cobertura ausente:** la prueba de mismatch solo usa un destino inexistente. Debe cubrir destino existente + `overwrite=True` y conservarlo cuando el checksum falla; la verificación debe producirse antes de la finalización atómica.

## Cumplimiento y calidad por separado

### Cumplimiento confirmado

- Interfaces `download` y `parse_checksum` presentes y con los modelos/errores requeridos.
- `requests.Session`, `stream=True`, timeout de conexión/lectura `(timeout, timeout)`, chunks de 64 KiB y context managers para respuesta/sesión.
- Reintentos para 503, 429 y 408, sin reintentos para 404; backoff exponencial acotado y `Retry-After` numérico.
- Progreso con tamaño conocido/desconocido, manejo de 200 como descarga fresca y hash SHA-256 incremental.
- Uso de `finalize_part`, rutas temporales derivadas de destinos sanitizados, y limpieza en `finally` salvo `keep_partial`.

### Calidad y seguridad

- La estructura es clara, las excepciones se tipifican y los temporales se limpian correctamente en las rutas cubiertas.
- Los dos hallazgos anteriores impiden considerar segura la implementación: falta validar el contrato de `Range/206` y el orden checksum/finalización compromete la semántica segura de overwrite.
- No se observan errores de espacios en el diff revisado.

## Validación ejecutada

| Comando | Resultado |
| --- | --- |
| `PYTHONPATH=<worktree> python -m pytest tests/test_downloader.py -q` | 15 passed |
| `PYTHONPATH=<worktree> python -m pytest tests -q` | 34 passed |
| `git diff --check cc54907 72b87f8` | Correcto (salida vacía, código 0) |
| Repro aislado: `206` con `Content-Range` inconsistente | Corrupción confirmada: `b'abcabcdef'` |
| Repro aislado: mismatch + `overwrite=True` con destino previo | Pérdida del destino confirmada |

## Nota de estado

El worktree ya tenía cambios no relacionados en documentación y artefactos SDD antes de escribir este informe. Esta revisión no modificó código ni pruebas; solo creó el presente archivo solicitado.
