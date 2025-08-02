# 🛰️ Acelerador de Descargas BlackZero

**BlackZero** es un script robusto en Python que permite descargar archivos desde una URL con barra de progreso en tiempo real. Ideal para automatizar descargas de forma simple, visual y eficiente.

---

## 🧠 Características

- Solicita una URL de descarga al usuario.
- Valida que la URL sea válida (`http` o `https`).
- Extrae automáticamente el nombre del archivo o asigna uno genérico si es necesario.
- Muestra una barra de progreso interactiva con `tqdm`.
- Descarga el archivo en la carpeta **Descargas** del usuario, sin sobrescribir archivos existentes.
- Informa claramente el estado de la descarga y su ubicación final.
- Maneja errores de conexión, URLs inválidas o archivos sin tamaño definido.

---

## 🛠️ Requisitos

- Python 3.x
- Módulos:
  - `requests`
  - `tqdm`

Instala las dependencias con:

```bash
pip install -r requirements.txt
```

---

## 🚀 Cómo usar

1. Asegúrate de tener Python 3 instalado.
2. Ejecuta el script desde la terminal:

```bash
python blackzero_downloader.py
```

3. Ingresa la URL del archivo que deseas descargar cuando se te solicite.

---

## 📁 Ruta de descarga

El archivo se guarda automáticamente en la carpeta de **Descargas** de tu usuario:

```plaintext
Windows: C:\Users\<tu_usuario>\Downloads\
Linux/macOS: /home/<usuario>/Downloads/
```

⚠️ Si ya existe un archivo con el mismo nombre, se renombrará automáticamente para evitar sobrescribirlo.

---

## 🔍 Estructura del código

### Funciones principales

#### `es_url_valida(url)`
Valida que la URL comience con `http` o `https`.

#### `generar_nombre_unico(ruta, nombre)`
Evita sobrescribir archivos renombrándolos automáticamente si ya existen.

#### `descargar_archivo(url)`
- Verifica que la URL sea válida.
- Descarga el archivo con barra de progreso.
- Maneja archivos sin `content-length`.
- Muestra información clara de éxito o errores.

---

## 🧱 Ejemplo de uso

```
🚀 Acelerador de descargas BlackZero
#####################################

🔗 Ingrese la URL del archivo a descargar: https://example.com/archivo.zip

archivo.zip: 100%|██████████████████████| 10.0M/10.0M [00:03<00:00, 3.12MB/s]

✅ Descarga completada con éxito.
📄 Archivo: archivo.zip
📁 Guardado en: C:\Users\ingmo\Downloads\archivo.zip
```

---

## ❌ Manejo de errores

- URLs inválidas
- Archivos inaccesibles
- Problemas de red
- Servidores sin tamaño definido

Ejemplo:

```
❌ Error durante la descarga: HTTPSConnectionPool(host='example.com', port=443): Max retries exceeded...
```

---

## 🧯 Consideraciones

- Multiplataforma (Windows, macOS, Linux).
- No requiere argumentos ni configuración previa.
- Perfecto para integrarse en scripts de automatización.

---

## ⚖️ Licencia

MIT - Libre para usar, modificar y distribuir.
