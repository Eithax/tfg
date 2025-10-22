import json
import numpy as np
import matplotlib.pyplot as plt

def plot_from_json(files, title="Evolución del coste por iteración"):
    """Dibuja las curvas de coste de uno o varios ficheros de resultados JSON."""
    plt.figure(figsize=(10, 6))
    for file_path in files:
        with open(file_path, "r") as f:
            data = json.load(f)

        network = data.get("network", "Unknown")
        tm = data.get("traffic_matrix", "TM?")
        threads = data.get("config", {}).get("threads", "?")

        for run_data in data.get("results", []):
            cost_history = run_data.get("cost_history", [])

            if isinstance(cost_history, dict) and "data" in cost_history:
                xs = [p["iter"] for p in cost_history["data"]]
                ys = [p["cost"] if p["cost"] is not None else np.nan for p in cost_history["data"]]
            elif isinstance(cost_history, list):
                xs = list(range(1, len(cost_history) + 1))
                ys = [y if np.isfinite(y) else np.nan for y in cost_history]
            else:
                continue

            label = f"{network}-TM{tm}-T{threads}-Run{run_data.get('run', '?')}"
            plt.plot(xs, ys, label=label)

    plt.xlabel("Iteración")
    plt.ylabel("Coste")
    plt.title(title)
    plt.legend(fontsize=8)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_avg_cost_histories(files, title="Coste promedio por iteración"):
    """Dibuja la media y desviación estándar del coste a lo largo de las iteraciones."""
    plt.figure(figsize=(10, 6))

    for file_path in files:
        with open(file_path, "r") as f:
            data = json.load(f)

        network = data.get("network", "Unknown")
        tm = data.get("traffic_matrix", "?")
        threads = data.get("config", {}).get("threads", "?")

        histories = []
        for run_data in data.get("results", []):
            cost_history = run_data.get("cost_history", [])
            if isinstance(cost_history, dict) and "data" in cost_history:
                ys = [p["cost"] if p["cost"] is not None else np.nan for p in cost_history["data"]]
            elif isinstance(cost_history, list):
                ys = [y if np.isfinite(y) else np.nan for y in cost_history]
            else:
                continue
            histories.append(ys)

        if not histories:
            continue

        min_len = min(len(h) for h in histories)
        histories = [h[:min_len] for h in histories]
        arr = np.array(histories)
        mean = np.nanmean(arr, axis=0)
        std = np.nanstd(arr, axis=0)

        xs = list(range(1, len(mean) + 1))
        label = f"{network}-TM{tm}-T{threads}"
        plt.plot(xs, mean, label=label)
        plt.fill_between(xs, mean - std, mean + std, alpha=0.2)

    plt.xlabel("Iteración")
    plt.ylabel("Coste promedio ± desviación")
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
