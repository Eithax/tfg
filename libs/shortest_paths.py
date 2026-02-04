import heapq
import itertools
import networkx as nx

def dijkstra_path_length(graph, source, target):
    try:
        return nx.dijkstra_path_length(graph, source, target, weight='weight')
    except nx.NetworkXNoPath:
        return float('inf')

def yen_k_shortest_paths(graph, source, target, k):
    if source == target:
        return [[source]]

    paths = []
    potential_paths = []

    # First shortest path using Dijkstra
    try:
        first_path = nx.dijkstra_path(graph, source, target, weight='weight')
        paths.append(first_path)
    except nx.NetworkXNoPath:
        return []

    for i in range(1, k):
        for j in range(len(paths[-1]) - 1):
            spur_node = paths[-1][j]
            root_path = paths[-1][:j + 1]

            g_copy = graph.copy()

            # Remove edges that would recreate previously found paths
            for path in paths:
                if path[:j + 1] == root_path and len(path) > j + 1:
                    if g_copy.has_edge(path[j], path[j + 1]):
                        g_copy.remove_edge(path[j], path[j + 1])

            # Remove nodes in root path except spur_node
            for node in root_path[:-1]:
                g_copy.remove_node(node)

            try:
                spur_path = nx.dijkstra_path(g_copy, spur_node, target, weight='weight')
                total_path = root_path[:-1] + spur_path
                total_weight = sum(
                    graph[u][v]['weight'] for u, v in zip(total_path, total_path[1:])
                )
                heapq.heappush(potential_paths, (total_weight, total_path))
            except nx.NetworkXNoPath:
                continue

        if potential_paths:
            _, new_path = heapq.heappop(potential_paths)
            paths.append(new_path)
        else:
            break

    return paths

def all_pairs_k_shortest_paths(graph, k):
    """
    Calcula los k caminos más cortos entre todos los pares de nodos.
    """
    all_paths = {}
    nodes = list(graph.nodes())
    total_pairs = len(nodes) * (len(nodes) - 1)

    print(f"Calculando k={k} caminos para {len(nodes)} nodos ({total_pairs} pares)...")

    for source in nodes:
        for target in nodes:
            if source != target:
                paths = yen_k_shortest_paths(graph, source, target, k)
                if paths:
                    all_paths[(source, target)] = paths

    return all_paths

def all_pairs_k_shortest_paths_nx(graph, k):
    all_paths = {}
    nodes = list(graph.nodes())

    for src in nodes:
        for dst in nodes:
            if src == dst:
                continue

            try:
                k_paths = list(itertools.islice(
                    nx.shortest_simple_paths(graph, src, dst, weight='weight'),
                    k
                ))
                if k_paths:
                    all_paths[(src, dst)] = k_paths

            except nx.NetworkXNoPath:
                continue

    return all_paths