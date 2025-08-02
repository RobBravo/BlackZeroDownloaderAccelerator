import requests
import os
from urllib.parse import urlsplit, urlparse
from tqdm import tqdm


def es_url_valida(url):
    parsed = urlparse(url)
    return all([parsed.scheme in ["http", "https"], parsed.netloc])


def generar_nombre_unico(ruta_descargas, nombre_archivo):
    base, ext = os.path.splitext(nombre_archivo)
    contador = 1
    nombre_final = nombre_archivo
    while os.path.exists(os.path.join(ruta_descargas, nombre_final)):
        nombre_final = f"{base}_{contador}{ext}"
        contador += 1
    return nombre_final


def descargar_archivo(url):
    if not es_url_valida(url):
        print("❌ URL no válida. Asegúrese de que comienza con http o https.")
        return

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        nombre_archivo = os.path.basename(urlsplit(url).path)
        if not nombre_archivo:
            nombre_archivo = "archivo_descargado"

        ruta_descargas = os.path.join(os.path.expanduser("~"), "Downloads")
        nombre_archivo = generar_nombre_unico(ruta_descargas, nombre_archivo)
        ruta_archivo = os.path.join(ruta_descargas, nombre_archivo)

        tamaño_archivo = int(response.headers.get("content-length", 0))
        progreso_descarga = tqdm(total=tamaño_archivo, unit="B", unit_scale=True, desc=nombre_archivo) if tamaño_archivo else None

        with open(ruta_archivo, "wb") as archivo:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    archivo.write(chunk)
                    if progreso_descarga:
                        progreso_descarga.update(len(chunk))

        if progreso_descarga:
            progreso_descarga.close()

        print("\n✅ Descarga completada con éxito.")
        print(f"📄 Archivo: {nombre_archivo}")
        print(f"📁 Guardado en: {ruta_archivo}")

    except requests.exceptions.RequestException as e:
        print("❌ Error durante la descarga:", e)


if __name__ == "__main__":
    print("🚀 Acelerador de descargas BlackZero")
    print("#####################################\n")
    url = input("🔗 Ingrese la URL del archivo a descargar: ").strip()
    descargar_archivo(url)