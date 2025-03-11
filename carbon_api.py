from datetime import datetime, timedelta
import requests
import json
import os
import pathlib
import sys

"""
Obtiene la intensidad de carbono (gCO2/kwh) para una ubicación dada (latitud y longitud).

Parámetros:
latitud: Latitud de la ubicación.
longitud: Longitud de la ubicación.

Retorna:
respuesta: Intensidad de carbono en la ubicación especificada. Devuelve 'No data' si no hay información disponible o None en caso de error, con el mensaje correspondiente.
"""


def obtener_carbon_intensity_nodo(latitud, longitud):
    url_carbon_intensity = f'https://api.electricitymap.org/v3/carbon-intensity/latest?lat={latitud}&lon={longitud}'
    try:
        respuesta = requests.get(url_carbon_intensity, timeout=10)  # Agregado un timeout de 10 segundos
        if respuesta.status_code == 200:
            return respuesta.json().get('carbonIntensity', 'No data')
        print(f"Error al obtener carbon_intensity para ({latitud}, {longitud}): {respuesta.status_code}")
    except requests.exceptions.Timeout:
        print(f"Error: La solicitud para ({latitud}, {longitud}) superó el tiempo de espera.")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al obtener carbon_intensity para ({latitud}, {longitud}): {e}")
    sys.exit("No hay datos de Carbon Intensity")
    return None


"""
Guarda las carbon_intensity captadas de la API en un documento, almacenando la fecha en que se captaron.

Parámetros:
carbon_intensity: Datos de carbon_intensity captadas de la red.
timestamp: Marca de tiempo de la captura de datos.
"""


def guardar_carbon_intensity(carbon_intensity, timestamp, topo):
    path = pathlib.Path.cwd() / 'historic_carbon_intensity' / topo
    data = {'carbon_intensity': carbon_intensity, 'timestamp': timestamp}
    with open(path, 'w') as archivo:
        json.dump(data, archivo)


"""
Carga las carbon_intensity almacenadas en el archivo correspondiente.

Retorna:
data: Los datos de las carbon_intensity almacenados. Retornará 'None' en caso de error al leer el archivo o si este no existe.
"""


def cargar_carbon_intensity(topo):
    path = pathlib.Path.cwd() / 'historic_carbon_intensity' / topo
    if os.path.exists(path):
        with open(path, 'r') as archivo:
            data = json.load(archivo)
            return data
    return None


"""
Comprueba si los datos de carbon_intensity están actualizados comparando la fecha y hora de ejecución del programa con la guardada en el archivo de carbon_intensity.

Retorna:
data: Los datos de carbon_intensity. En el caso de que no haya datos almacenados o no estén actualizados, retorna 'None'.
"""


def datos_actualizados(topo):
    data = cargar_carbon_intensity(topo)
    if data:
        timestamp = datetime.fromisoformat(data['timestamp'])
        if datetime.now() - timestamp < timedelta(hours=1):  # Verifica si los datos son más recientes de 1 hora
            return data['carbon_intensity']
    return None


"""
Extrae las coordenadas de los nodos desde un archivo XML y obtiene las carbon_intensity de carbono para cada nodo.

Parámetros:
ruta_xml: Ruta del archivo XML que contiene los nodos y sus coordenadas.

Retorna:
carbon_intensity: Las carbon_intensity, almacenadas anteriormente o recien captadas, en forma de lista.
"""


def obtener_carbon_intensity(topology, ubications):
    # Verificar si los datos están actualizados
    carbon_intensity = datos_actualizados(topology + '.json')
    if carbon_intensity:
        return carbon_intensity

    # Si los datos no están actualizados, obtenerlos desde la API
    print(f"Obteniendo datos de carbono en tiempo real para {topology}")
    carbon_intensity = [obtener_carbon_intensity_nodo(u[0], u[1]) for u in ubications]

    # Guardar las carbon_intensity y la hora de la consulta
    timestamp = datetime.now().isoformat()
    guardar_carbon_intensity(carbon_intensity, timestamp, topology + '.json')

    return carbon_intensity