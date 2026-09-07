# Revisión Task 2 — manejo seguro de nombres y rutas

**Resultado:** RECHAZADO hasta corregir el hallazgo alto de sobrescritura.

## Alcance y evidencia revisada

- Brief: `task-2-brief.md`.
- Informe: `task-2-report.md`.
- Paquete de revisión y estado real del commit `f5c8582` (base `ec75b7e`).
- Pruebas ejecutadas en el worktree, con Python 3.12 y `PYTHONPATH` apuntando al worktree:
  - `python -m pytest tests/test_files.py -q` → **11 passed**.
  - `python -m pytest -q` → **15 passed**.
  - `python -m compileall -q blackzero` → **correcto**.
  - `git diff --check ec75b7e f5c8582` → **correcto**.

No se modificó código ni pruebas durante la revisión; este archivo es el único artefacto escrito.

## Cumplimiento del brief

| Requisito | Estado | Evidencia / observación |
|---|---|---|
| Crear solamente `blackzero/files.py` y `tests/test_files.py` | Cumple | El diff `ec75b7e..f5c8582` contiene exactamente esos dos archivos. |
| Interfaces solicitadas | Cumple | Las seis funciones requeridas existen con las firmas solicitadas. |
| Directorio Downloads por defecto | Cumple | `default_download_dir()` devuelve `Path.home() / "Downloads"` resuelto. |
| URL, `Content-Disposition` y fallback | Parcial | URL y `filename` normal funcionan; `filename*` no cumple para valores RFC 5987 con idioma/charset (hallazgo M-1). |
| Caracteres Windows, reservados y separadores | Cumple | La sanitización cubre caracteres inválidos, controles, separadores, finales punto/espacio y nombres DOS reservados. |
| Colisiones, `overwrite` y creación de directorio | Parcial | `choose_destination()` cubre el caso normal, pero el paso final puede sobrescribir un destino ya existente sin autorización (hallazgo A-1). |
| Rutas dentro del output seleccionado | Parcial | `choose_destination()` resuelve y verifica la contención. La garantía de no sobrescritura se pierde al finalizar. |
| `.part` y renombrado atómico | Parcial | `os.replace` realiza un reemplazo atómico, pero precisamente por ello sustituye archivos existentes sin respetar el requisito global de `overwrite`. |
| TDD | No verificable de forma independiente | El informe declara un RED previo a la implementación, pero el paquete final no conserva una prueba temporal/auditable de ese orden. Las pruebas existentes sí cubren buena parte de los casos pedidos. |

## Hallazgos de cumplimiento

### Alta — A-1: `finalize_part` destruye un destino existente sin autorización de `overwrite`

- **Archivo/línea:** `blackzero/files.py:124`.
- **Evidencia:** `os.replace(Path(part), destination)` reemplaza `destination` si ya existe. La función no recibe `overwrite` ni comprueba que el destino siga libre. Por tanto, entre `choose_destination(..., overwrite=False)` y la finalización —o ante una llamada directa— puede sobrescribirse un archivo del usuario.
- **Impacto:** pérdida de datos; incumple explícitamente la regla global «no sobrescribir salvo `overwrite`».
- **Corrección concreta:** garantizar una publicación *no-replace* cuando el flujo no autorizó sobrescritura. Con la firma actual, `finalize_part` debe rechazar un `destination` existente y usar una operación de creación atómica que no pueda reemplazarlo (por ejemplo, enlazar `part` a `destination` con `os.link` y solo después eliminar `part`, tratando `FileExistsError` como colisión). Si se necesita soportar sobrescritura al finalizar, el contrato debe transportar explícitamente esa autorización desde el flujo que llama a la función; no se debe aplicar `os.replace` incondicionalmente.
- **Prueba requerida:** crear un `.part` y un `destination` preexistente con contenido distinto; verificar que la finalización sin autorización levanta una excepción de colisión, conserva el contenido de destino y conserva el `.part` para poder reintentar.

### Media — M-1: el análisis de `filename*` no implementa correctamente RFC 5987 con idioma o charset

- **Archivo/líneas:** `blackzero/files.py:61-65`.
- **Evidencia:** el código busca literalmente `''` con `partition("''")`. Un encabezado válido como `filename*=UTF-8'en'caf%C3%A9.txt` no contiene esa secuencia y devuelve `UTF-8'en'café.txt` como nombre, en vez de `café.txt`. Tampoco decodifica los bytes según el charset declarado.
- **Impacto:** nombres incorrectos para respuestas HTTP válidas con `Content-Disposition`; el requisito del brief de soportar este encabezado queda incompleto.
- **Corrección concreta:** separar `charset'language'payload` en dos apóstrofes, aplicar `unquote_to_bytes(payload)` y decodificar con el charset declarado; si el valor es inválido o el charset no está disponible, ignorar ese candidato y aplicar el fallback seguro de URL.
- **Prueba requerida:** añadir `filename*=UTF-8'en'caf%C3%A9.txt` y, como mínimo, un caso de charset no UTF-8 o inválido que use el fallback de URL.

## Calidad técnica y pruebas

### Lo que está bien

- Compatible con Python 3.10+: usa sintaxis `X | None` y `Path.is_relative_to`, disponibles desde versiones anteriores o iguales a 3.10.
- La sanitización está concentrada en `_sanitize_candidate`, evita duplicación y protege correctamente los casos Windows cubiertos.
- La búsqueda de encabezados es insensible a mayúsculas/minúsculas.
- La elección normal de destino crea el directorio y resuelve el nombre antes de devolverlo.
- Las pruebas son pequeñas, legibles y validan URL, encabezados, caracteres inválidos, reservados, colisiones, `overwrite`, creación de directorio, contención, `.part` y movimiento.
- No hay cambios fuera del alcance ni errores de espacios en el diff.

### Cobertura que debe reforzarse

- **Alta:** falta una prueba de que `finalize_part` no destruya un destino existente cuando `overwrite=False`; la prueba actual `tests/test_files.py:82-94` solo cubre un destino ausente.
- **Media:** falta el caso RFC 5987 con `charset` e idioma; `tests/test_files.py:29-33` solo cubre el subconjunto `UTF-8''...`.
- **Media:** la condición de carrera anotada en el informe sigue siendo real: `exists()` seguido de la creación del archivo no reserva el nombre. La corrección de A-1 debe hacer que la publicación sea una creación sin reemplazo, no solo añadir una comprobación previa.

## Decisión de revisión

No aprobar mientras A-1 permanezca abierto. Tras corregirlo, ejecutar como mínimo `python -m pytest tests/test_files.py -q` y `python -m pytest -q`, incorporando las pruebas negativas de no sobrescritura y de `filename*` RFC 5987.
