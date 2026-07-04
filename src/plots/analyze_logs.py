import os
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# Carregar todos os logs da pasta de um benchmark
# ============================================================
def load_logs(directory):
    files = [f for f in os.listdir(directory) if f.endswith(".csv")]
    datasets = {}

    for f in files:
        alg_name = f.split("_")[0]  # GA_ackley_2025.csv → GA
        df = pd.read_csv(os.path.join(directory, f))
        datasets.setdefault(alg_name, []).append(df)

    return datasets


# ============================================================
# Plot 1 — Curva de convergência por algoritmo
# ============================================================
def plot_convergence(datasets, benchmark, save_dir):
    plt.figure(figsize=(10, 6))

    for alg, logs in datasets.items():
        # média (se houver várias execuções do mesmo algoritmo)
        mean_curve = pd.concat(logs).groupby("epoch")["best_value"].mean()

        plt.plot(mean_curve.index, mean_curve.values, label=alg)

    plt.title(f"Convergência — {benchmark}")
    plt.xlabel("Época")
    plt.ylabel("Melhor valor")
    plt.grid(True)
    plt.legend()

    out = os.path.join(save_dir, f"{benchmark}_convergencia.png")
    plt.savefig(out)
    plt.close()


# ============================================================
# Plot 2 — Tempo por época
# ============================================================
def plot_time_curves(datasets, benchmark, save_dir):
    plt.figure(figsize=(10, 6))

    for alg, logs in datasets.items():
        mean_time = pd.concat(logs).groupby("epoch")["time_seconds"].mean()
        plt.plot(mean_time.index, mean_time.values, label=alg)

    plt.title(f"Tempo médio por época — {benchmark}")
    plt.xlabel("Época")
    plt.ylabel("Tempo (s)")
    plt.grid(True)
    plt.legend()

    out = os.path.join(save_dir, f"{benchmark}_tempos.png")
    plt.savefig(out)
    plt.close()


# ============================================================
# Plot 3 — Comparação entre algoritmos (último valor)
# ============================================================
def plot_last_value_comparison(datasets, benchmark, save_dir):
    labels = []
    values = []

    for alg, logs in datasets.items():
        last_vals = [df["best_value"].iloc[-1] for df in logs]
        labels.append(alg)
        values.append(last_vals)

    plt.figure(figsize=(10, 6))
    plt.boxplot(values, labels=labels)
    plt.title(f"Comparação dos melhores valores (última época) — {benchmark}")
    plt.ylabel("Melhor valor final")
    plt.grid(True)

    out = os.path.join(save_dir, f"{benchmark}_boxplot.png")
    plt.savefig(out)
    plt.close()


# ============================================================
# Processar um benchmark completo
# ============================================================
def analyze_benchmark(benchmark_dir):
    benchmark = os.path.basename(benchmark_dir)
    print(f"🔍 Analisando benchmark: {benchmark}")

    datasets = load_logs(benchmark_dir)

    if not datasets:
        print("⚠ Nenhum log encontrado.")
        return

    plot_convergence(datasets, benchmark, benchmark_dir)
    plot_time_curves(datasets, benchmark, benchmark_dir)
    plot_last_value_comparison(datasets, benchmark, benchmark_dir)

    print(f"📊 Gráficos gerados em {benchmark_dir}")


# ============================================================
# Rodar análise em TODOS os benchmarks
# ============================================================
def analyze_all(logs_root="logs"):
    for bench in os.listdir(logs_root):
        bench_dir = os.path.join(logs_root, bench)
        if os.path.isdir(bench_dir):
            analyze_benchmark(bench_dir)


if __name__ == "__main__":
    analyze_all()
