import numpy as np
from optimization_functions import total_carbon_intensity

# Datos de prueba
num_nodes = 3
num_links = 2

# Matriz de carbono (valores arbitrarios para prueba)
carbon_matrix = np.array([
    [0, 10, 0],  # Enlace 0-1 con CI=10
    [10, 0, 20], # Enlace 1-0 con CI=10, 1-2 con CI=20
    [0, 20, 0]   # Enlace 2-1 con CI=20
])

# Matriz de flujo (tráfico entre nodos)
flow_matrix = np.array([
    [0, 5, 0],   # 5 Mbps de 0 a 1
    [5, 0, 10],  # 5 Mbps de 1 a 0, 10 Mbps de 1 a 2
    [0, 10, 0]   # 10 Mbps de 2 a 1
])

# Posiciones geográficas de los nodos (lat, lon)
nodes_geoposition = {
    0: {'lat': 40.0, 'lon': -3.0},
    1: {'lat': 41.0, 'lon': -3.5},
    2: {'lat': 40.5, 'lon': -3.2}
}

# Máximo flujo por nodo
nodes_max_flow = {0: 20, 1: 30, 2: 20}

# Función mock para obtener carbono por nodo (simplificada para la prueba)
def obtener_carbon_intensity_nodo(lat, lon):
    # Valores arbitrarios basados en la latitud para la prueba
    return lat * 2  # Solo un ejemplo

# Posición de prueba (matriz de adyacencia)
position = np.array([
    [0, 1, 0],  # Enlace 0-1 activo
    [1, 0, 1],  # Enlaces 1-0 y 1-2 activos
    [0, 1, 0]   # Enlace 2-1 activo
])

# Parámetros para la función
kwargs = {
    'num_nodes': num_nodes,
    'num_links': num_links,
    'carbon_matrix': carbon_matrix,
    'flow_matrix': flow_matrix,
    'nodes_geoposition': nodes_geoposition,
    'nodes_max_flow': nodes_max_flow
}

# Ejecutar la función
result = total_carbon_intensity(position, **kwargs)

# Verificar resultados esperados
print("Resultado de carbono total:", result)

# Verificación manual:
# 1. Cálculo de tráfico por nodo:
#    - Nodo 0: solo recibe 5 Mbps de 1-0
#    - Nodo 1: recibe 5 Mbps de 0-1 y 10 Mbps de 2-1 = 15 Mbps
#    - Nodo 2: recibe 10 Mbps de 1-2
#    Todos están dentro de los límites (20, 30, 20 respectivamente)

# 2. Dynamic power:
#    lambda_n = (41.625-23.375/400000) ≈ 41.625
#    - Nodo 0: 5 * 41.625 * (40.0*2) = 5 * 41.625 * 80 = 16,650
#    - Nodo 1: 15 * 41.625 * (41.0*2) = 15 * 41.625 * 82 = 51,198.75
#    - Nodo 2: 10 * 41.625 * (40.5*2) = 10 * 41.625 * 81 = 33,716.25
#    Total dynamic power ≈ 16,650 + 51,198.75 + 33,716.25 ≈ 101,565

# 3. Power ports (beta_l = 5.5):
#    - Enlace 0-1: 5.5 * (80 + 82) = 5.5 * 162 = 891
#    - Enlace 1-0: 5.5 * (82 + 80) = 891 (igual que arriba)
#    - Enlace 1-2: 5.5 * (82 + 81) = 5.5 * 163 = 896.5
#    - Enlace 2-1: 5.5 * (81 + 82) = 896.5 (igual que arriba)
#    Total power ports ≈ 891*2 + 896.5*2 ≈ 3,575

# Total esperado ≈ 101,565 + 3,575 ≈ 105,140

# Nota: Los valores exactos pueden variar ligeramente según los cálculos intermedios
# y la precisión de lambda_n, pero debería estar en ese rango.


# Cambiamos el flujo máximo del nodo 1 a un valor más bajo
nodes_max_flow_invalid = {0: 20, 1: 10, 2: 20}
kwargs_invalid = kwargs.copy()
kwargs_invalid['nodes_max_flow'] = nodes_max_flow_invalid

# Ejecutar la función
result_invalid = total_carbon_intensity(position, **kwargs_invalid)

print("\nResultado con solución inválida (debería ser 99999):", result_invalid)