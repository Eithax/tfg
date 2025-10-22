"""import numpy as np
from libs.optimization_functions import total_carbon_intensity
from api.ember_carbon_api import get_carbon_intensity_node

# Prueba de la API
print(get_carbon_intensity_node(48.8566, 2.3522))

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
#    lambda_n = (41.625-23.375)/400000 ≈ 0.000045625
#    - Nodo 0: 5 * 0.000045625 * 416 = 0.0949364
#    - Nodo 1: 15 * 0.000045625 * 386 = 0.088090025
#    - Nodo 2: 10 * 0.000045625 * 353 = 0.0805590125
#    Total dynamic power ≈ 0.0949364 + 0.088090025 + 0.0805590125 ≈ 0.2635854375

# 3. Power ports (beta_l = 5.5):
#    - Enlace 0-1: 5.5 * (416 + 386) = 4411
#    - Enlace 1-0: 5.5 * (386 + 416) = 4411 (igual que arriba)
#    - Enlace 1-2: 5.5 * (386 + 353) = 4064.5
#    - Enlace 2-1: 5.5 * (353 + 386) = 4064.5 (igual que arriba)
#    Total power ports ≈ 4411*2 + 4064.5*2 ≈ 16951

# Total esperado ≈ (0.2635854375 + 16951) / 1000 ≈ 0.00470868432

# Nota: Los valores exactos pueden variar ligeramente según los cálculos intermedios
# y la precisión de lambda_n, pero debería estar en ese rango.


# Cambiamos el flujo máximo del nodo 1 a un valor más bajo
nodes_max_flow_invalid = {0: 20, 1: 10, 2: 20}
kwargs_invalid = kwargs.copy()
kwargs_invalid['nodes_max_flow'] = nodes_max_flow_invalid

# Ejecutar la función
result_invalid = total_carbon_intensity(position, **kwargs_invalid)

print("\nResultado con solución inválida (debería ser inf):", result_invalid)"""


from libs.result_analysis import (
    plot_cost_vs_iterations,
    plot_cost_vs_particles
)

files = [
    "results/Abilene/Abilene_TM1_1threads_20251010_183001.json",
    "results/Abilene_TM1_2threads_20251010_183030.json",
    "results/Abilene_TM1_1threads_20251010_184000.json",
]

# Evolución del coste a lo largo de las iteraciones (misma TM)
plot_cost_vs_iterations(files, tm_target=1, group_by="config")

# Coste final según número de partículas
plot_cost_vs_particles(files, tm_target=1, group_by="threads")
