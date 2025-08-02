# 🛰️ Acelerador de Descargas BlackZero

**BlackZero** es un script simple en Python que permite descargar archivos desde una URL y muestra una barra de progreso durante la descarga. Ideal para automatizar descargas de forma más informativa que un simple `wget`.

---

## 🧠 Características

- Solicita una URL de descarga al usuario.
- Extrae automáticamente el nombre del archivo.
- Muestra una barra de progreso interactiva gracias a `tqdm`.
- Descarga el archivo en la carpeta de **Descargas** del usuario (configurable).
- Informa claramente el estado de la descarga y su ubicación final.
- Maneja errores de conexión o URLs inválidas.

---

## 🛠️ Requisitos

- Python 3.x
- Módulos:
  - `requests`
  - `tqdm`

Puedes instalar los módulos con:

```bash
pip install requests tqdm
```

---

## 🚀 Cómo usar

1. Asegúrate de tener Python 3 instalado.
2. Ejecuta el script:

```bash
python DownloadFiles.py
```

3. Ingresa la URL del archivo que deseas descargar cuando el programa lo solicite.

---

## 📁 Ruta de descarga

El archivo se guarda automáticamente en la siguiente ruta:

```plaintext
C:\Users\<tu_usuario>\Downloads\
```

> ⚠️ Puedes modificar la variable `ruta_descargas` para cambiar la ubicación de descarga predeterminada.

---

## 🧩 Estructura del código

### `descargar_archivo(url)`
- Recibe una URL.
- Hace una solicitud `GET` por streaming.
- Calcula el tamaño total del archivo.
- Descarga el contenido en bloques de 1024 bytes.
- Muestra una barra de progreso visual en consola.
- Guarda el archivo en la ruta indicada.

### Interacción con el usuario
- El script solicita al usuario que ingrese la URL.
- Llama a la función `descargar_archivo()` con esa URL.

---

## 🧱 Ejemplo de uso

```
Acelerador de descargas BlackZero
#################################
Ingrese la URL del archivo a descargar: https://example.com/archivo.zip

100%|█████████████████████████████████████| 10.0M/10.0M [00:03<00:00, 3.12MB/s]
Descarga completada!
Se ha descargado el archivo: archivo.zip
La ruta de destino del archivo es: C:\Users\usuario\Downloads\archivo.zip
```

---

## 🧯 Manejo de errores

Si la URL no es válida o hay problemas de conexión, el script mostrará un mensaje de error como:

```
Error durante la descarga: HTTPSConnectionPool(host='example.com', port=443): Max retries exceeded...
```

---

## 📌 Notas

- Este script es multiplataforma con ligeros ajustes, pero actualmente está configurado para **Windows**.
- Para usarlo en Linux o macOS, cambia la variable `ruta_descargas` a una ruta válida como `/home/usuario/Downloads`.

---

## ⚖️ Licencia

MIT - Libre para usar, modificar y distribuir.
