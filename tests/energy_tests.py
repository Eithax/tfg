from collections import defaultdict
import numpy as np
import json

def total_carbon_intensity(position, **kwargs):
    nodes_traffic = defaultdict(int)
    links_traffic = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=float)
    lambda_n = (41.625-23.375)/400000   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0

    # Crear conjunto de enlaces activos
    active_links = set()
    for i in range(kwargs['num_nodes']):
        for j in range(kwargs['num_nodes']):
            if position[i][j] == 1:
                active_links.add((i, j))

    # Función auxiliar para verificar si un camino usa solo enlaces activos
    def path_is_valid(v_path):
        for index in range(len(v_path) - 1):
            if (v_path[index], v_path[index + 1]) not in active_links:
                return False
        return True

    # Función auxiliar para verificar capacidad disponible
    def path_has_capacity(v_path, v_demand, current_links_traffic):
        """
        Verifica si un camino tiene capacidad suficiente para la demanda.
        """
        for index in range(len(v_path) - 1):
            src_node = v_path[index]
            dst_node = v_path[index + 1]
            current_flow = current_links_traffic[src_node][dst_node]
            max_flow = kwargs['nodes_max_flow'][src_node][dst_node]

            if current_flow + v_demand > max_flow:
                return False
        return True

    # Asignación de flujos
    # Crear lista de demandas ordenadas
    demands = []
    for src in range(kwargs['num_nodes']):
        for dst in range(kwargs['num_nodes']):
            if src != dst:
                demand = kwargs['flow_matrix'][src][dst]
                demands.append((src, dst, demand))

    # Ordenar por demanda descendente
    demands.sort(key=lambda x: x[2], reverse=True)

    # Intentar asignar cada flujo
    for (src, dst, demand) in demands:
        if demand == 0:
            continue

        # Buscar el mejor camino disponible
        selected_path = None

        if (src, dst) in kwargs['all_k_paths']:
            for path in kwargs['all_k_paths'][(src, dst)]:
                if path_is_valid(path) and path_has_capacity(path, demand, links_traffic):
                    selected_path = path
                    break

        # Si no hay camino válido, topología inválida
        if selected_path is None:
            return float('inf')

        # Actualizar tráfico en enlaces y nodos
        prev = selected_path[0]
        for n in selected_path[1:]:
            links_traffic[prev][n] += demand
            nodes_traffic[n] += demand
            prev = n

    # Cargar la información histórica de carbono de esa red
    nodes_carbon_intensity = json.load(open(
        './resources/topologies/Historic_Carbon_Intensity/' + kwargs['filepath'] + '.json'))

    # Cálculo de emisiones
    per_node_emissions = {}

    for node_x in range(kwargs['num_nodes']):
        node_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
        node_dynamic = nodes_traffic[node_x] * lambda_n * node_carbon
        dynamic_power += nodes_traffic[node_x] * lambda_n * node_carbon
        node_ports = 0.0

        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                node_x_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
                node_y_carbon = nodes_carbon_intensity['carbon_intensity'][node_y] / 1000
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

        per_node_emissions[node_x] = {
            'dynamic': node_dynamic,
            'ports': node_ports,
            'total': node_dynamic + node_ports,
            'carbon_intensity': node_carbon,
            'traffic': nodes_traffic[node_x],
            'active_links': sum(1 for ny in range(kwargs['num_nodes'])
                                if node_x != ny and position[node_x][ny] != 0)
        }

    return {
        'total': dynamic_power + power_ports,
        'dynamic_power': dynamic_power,
        'power_ports': power_ports,
        'active_links': len(active_links),
        'link_utilization': links_traffic / kwargs['nodes_max_flow'],
        'per_node_emissions': per_node_emissions
    }


def total_carbon_intensity_vch(position, **kwargs):
    nodes_traffic = defaultdict(int)
    links_traffic = np.zeros((kwargs['num_nodes'], kwargs['num_nodes']), dtype=float)
    lambda_n = (41.625-23.375)/400000   # 0.000045625 W/Mbps
    beta_l = 5.5    # Watts
    dynamic_power = 0.0
    power_ports = 0.0
    violations = 0
    big_m = 1e12

    # Crear conjunto de enlaces activos
    active_links = set()
    for i in range(kwargs['num_nodes']):
        for j in range(kwargs['num_nodes']):
            if position[i][j] == 1:
                active_links.add((i, j))

    # Función auxiliar para verificar si un camino usa solo enlaces activos
    def path_is_valid(v_path):
        for index in range(len(v_path) - 1):
            if (v_path[index], v_path[index + 1]) not in active_links:
                return False
        return True

    # Función auxiliar para verificar capacidad disponible
    def path_has_capacity(v_path, v_demand, current_links_traffic):
        """
        Verifica si un camino tiene capacidad suficiente para la demanda.
        """
        for index in range(len(v_path) - 1):
            src_node = v_path[index]
            dst_node = v_path[index + 1]
            current_flow = current_links_traffic[src_node][dst_node]
            max_flow = kwargs['nodes_max_flow'][src_node][dst_node]

            if current_flow + v_demand > max_flow:
                return False
        return True

    # Asignación de flujos
    # Crear lista de demandas ordenadas
    demands = []
    for src in range(kwargs['num_nodes']):
        for dst in range(kwargs['num_nodes']):
            if src != dst:
                demand = kwargs['flow_matrix'][src][dst]
                demands.append((src, dst, demand))

    # Ordenar por demanda descendente
    demands.sort(key=lambda x: x[2], reverse=True)

    # Intentar asignar cada flujo
    for (src, dst, demand) in demands:
        if demand == 0:
            continue

        # Buscar el mejor camino disponible
        selected_path = None

        if (src, dst) in kwargs['all_k_paths']:
            for path in kwargs['all_k_paths'][(src, dst)]:
                if path_is_valid(path) and path_has_capacity(path, demand, links_traffic):
                    selected_path = path
                    break

        # Si no hay camino válido, topología inválida
        if selected_path is None:
            violations += 1
            continue

        # Actualizar tráfico en enlaces y nodos
        prev = selected_path[0]
        for n in selected_path[1:]:
            links_traffic[prev][n] += demand
            nodes_traffic[n] += demand
            prev = n

    # Cargar la información histórica de carbono de esa red
    nodes_carbon_intensity = json.load(open(
        './resources/topologies/Historic_Carbon_Intensity/' + kwargs['filepath'] + '.json'))

    # Cálculo de emisiones
    for node_x in range(kwargs['num_nodes']):
        node_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
        dynamic_power += nodes_traffic[node_x] * lambda_n * node_carbon

        for node_y in range(kwargs['num_nodes']):
            if node_x != node_y and position[node_x][node_y] != 0:
                node_x_carbon = nodes_carbon_intensity['carbon_intensity'][node_x] / 1000
                node_y_carbon = nodes_carbon_intensity['carbon_intensity'][node_y] / 1000
                power_ports += beta_l * (node_x_carbon + node_y_carbon)

    total_cost = dynamic_power + power_ports + violations*big_m
    return total_cost




