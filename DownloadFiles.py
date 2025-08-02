import requests
import os
from urllib.parse import urlsplit
from tqdm import tqdm

def descargar_archivo(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        nombre_archivo = os.path.basename(urlsplit(url).path)
        tamaño_archivo = int(response.headers.get("content-length", 0))
        progreso_descarga = tqdm(total=tamaño_archivo, unit="B", unit_scale=True)

        ruta_descargas = 'C:\\Users\\ingmo\\Downloads\\'  # Cambiado a una variable para mayor claridad
        ruta_archivo = os.path.join(ruta_descargas, nombre_archivo)

        with open(ruta_archivo, "wb") as archivo:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    archivo.write(chunk)
                    progreso_descarga.update(len(chunk))

        progreso_descarga.close()
        print("Descarga completada!")
        print("Se ha descargado el archivo:", nombre_archivo)
        print("La ruta de destino del archivo es:", ruta_archivo)
    except requests.exceptions.RequestException as e:
        print("Error durante la descarga:", e)

# Solicitar URL y carpeta de destino al usuario
print('Acelerador de descargas BlackZero')
print('#################################')
url = input("Ingrese la URL del archivo a descargar: ")

descargar_archivo(url)
