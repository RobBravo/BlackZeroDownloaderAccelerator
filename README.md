# 🛰️ Acelerador de Descargas BlackZero

BlackZero es un descargador HTTP/HTTPS para terminal, seguro para automatización y compatible con el flujo interactivo original.

## Instalación

Requiere Python 3.10 o posterior.

```bash
python -m pip install -e .
```

También puede instalarse únicamente desde `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

## Uso

La interfaz principal acepta una o más URL:

```powershell
blackzero https://example.com/archivo.zip
python -m blackzero https://example.com/archivo.zip
python -m blackzero https://example.com/a.zip https://example.com/b.zip -o .\descargas
```

```bash
blackzero https://example.com/archivo.zip
python -m blackzero https://example.com/archivo.zip
python -m blackzero https://example.com/a.zip https://example.com/b.zip -o ./descargas
```

El comando `blackzero` queda disponible después de instalar el proyecto con `pip install -e .`.

El destino predeterminado es la carpeta `Downloads` del usuario. Se crea automáticamente. El launcher original sigue funcionando:

```bash
python DownloadFiles.py
python DownloadFiles.py https://example.com/archivo.zip
```

En el primer caso se muestra el banner y se solicita una URL; en el segundo no se solicita entrada.

### Opciones

| Opción | Descripción |
| --- | --- |
| `-o, --output-dir PATH` | Carpeta de destino. |
| `-n, --filename NAME` | Nombre explícito; solo con una URL. |
| `--overwrite` | Reemplaza el archivo existente. Por defecto se añade un sufijo seguro. |
| `--resume` | Reanuda desde `NAME.part` cuando el servidor acepta `Range`. |
| `--retries N` | Reintentos para fallos transitorios; predeterminado: `3`. |
| `--timeout SECONDS` | Tiempo de conexión y lectura; predeterminado: `30`. |
| `--checksum sha256:HEX` | Verifica SHA-256 y elimina el archivo si no coincide. |
| `-q, --quiet` | Oculta progreso y mensajes informativos; conserva errores en `stderr`. |
| `--keep-partial` | Conserva el archivo `.part` tras un fallo. |
| `--version`, `--help` | Muestra versión o ayuda. |

Ejemplos:

```powershell
python -m blackzero https://example.com/app.zip -o .\build -n app.zip --resume --checksum sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
python -m blackzero https://example.com/a.zip -q --retries 5 --timeout 10
```

```bash
python -m blackzero https://example.com/app.zip -o ./build -n app.zip --resume
python -m blackzero https://example.com/a.zip -q --retries 5 --timeout 10
```

## Seguridad y comportamiento

- Solo se aceptan URL `http` y `https` con hostname.
- Los nombres provenientes de la URL o `Content-Disposition` se sanitizan: se eliminan separadores, caracteres de control, caracteres inválidos de Windows y nombres reservados.
- Las descargas se escriben primero en `archivo.ext.part` y se renombran atómicamente al completarse.
- Los archivos existentes no se reemplazan salvo con `--overwrite`; sin esa opción se usa `archivo (1).ext`, etc.
- Los `.part` se eliminan tras errores normales. Use `--keep-partial` para conservarlos.
- `--resume` requiere que el servidor acepte `Range` y responda con `206`; si no, se inicia una descarga nueva.
- La ausencia de `Content-Length` no impide descargar, pero limita la información de progreso.

## Códigos de salida

- `0`: todas las descargas terminaron correctamente.
- `1`: falló una descarga o la verificación de checksum.
- `2`: entrada del CLI inválida, por ejemplo una URL no válida o una opción incompatible.

## Desarrollo

```bash
python -m pip install -e ".[dev]"
pytest -q
```

Las pruebas usan un servidor HTTP local y no dependen de red externa.

## Licencia

MIT - Libre para usar, modificar y distribuir.
