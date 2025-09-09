from datetime import datetime, timedelta
import requests
import json
import os
import pathlib
import sys
from geopy.geocoders import Nominatim
from dateutil.relativedelta import relativedelta

api_token = '07645265-77a4-4590-836c-df6f39502ed9'
base_url = 'https://api.ember-energy.org'

geolocator = Nominatim(user_agent='geoapi')

"""
Obtiene la intensidad de carbono (gCO2/kwh) para una ubicación dada (latitud y longitud).

Parámetros:
lat: Latitud de la ubicación.
lon: Longitud de la ubicación.

Retorna:
value: Intensidad de carbono en la ubicación especificada. Devuelve 'No data' si no hay información disponible o None en caso de error, con el mensaje correspondiente.
"""


def get_carbon_intensity_node(lat, lon):
    ts = datetime.now().timestamp()
    dt = datetime.fromtimestamp(ts)
    prev_dt = dt - relativedelta(months=1)
    location = geolocator.reverse((lat, lon), language="en")
    query_url = (
            f"{base_url}/v1/carbon-intensity/monthly"
            +f"?entity={location.raw["address"]["country"]}&start_date={prev_dt.strftime('%Y-%m')}&include_all_dates_value_range=false&api_key={api_token}"
    )

    print(query_url)

    data = make_request(lat, lon, query_url)
    value = data[0]["emissions_intensity_gco2_per_kwh"]

    return value


"""
Obtiene la intensidad de carbono (gCO2/kWh) para una ubicación dada (latitud y longitud) durante un período de tiempo.

Parámetros:
lat -> Latitud de la ubicación
lon -> Longitud de la ubicación
start_ts -> Timestamp inicial
end_ts -> Timestamp final (opcional)

Devuelve:
values -> List de intensidades de carbono de la ubicación especificada durante el período de tiempo estipulado. Devuelve 'No data' si no hay información disponible
          Si no se indica timestamp final, el período de tiempo es hasta la actualidad.
"""


def get_monthly_carbon_intensity_node(lat, lon, start_ts, end_ts=None):
    if end_ts is None:
        end_ts = datetime.now().timestamp()

    end_dt = datetime.fromtimestamp(end_ts)
    start_dt = datetime.fromtimestamp(start_ts)

    location = geolocator.reverse((lat, lon), language="en")

    query_url = (
            f"{base_url}/v1/carbon-intensity/monthly"
            + f"?entity={location.raw["address"]["country"]}&start_date={start_dt.strftime('%Y-%m')}&end_date={end_dt.strftime('%Y-%m')}&include_all_dates_value_range=false&api_key={api_token}"
    )

    data = make_request(lat, lon, query_url)
    values = [item["emissions_intensity_gco2_per_kwh"] for item in data]

    return values


"""
Realiza una petición al endpoint correspondiente.

Parámetros:
lat -> Latitud de la ubicación
lon -> Longitud de la ubicación
query_url -> URL de la query

Devuelve:
data -> Todos los datos de carbono recuperados de la petición
"""


def make_request(lat, lon, query_url):
    try:
        response = requests.get(query_url, timeout=10)  # Agregado un timeout de 10 segundos
        if response.status_code == 200:
            data = response.json()
            value = (
                data.get("data", {})
            )
            return value
        print(f"Error al obtener carbon_intensity para ({lat}, {lon}): {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"Error: La solicitud para ({lat}, {lon}) superó el tiempo de espera.")
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al obtener carbon_intensity para ({lat}, {lon}): {e}")
    sys.exit("No hay datos de Carbon Intensity")
    return None