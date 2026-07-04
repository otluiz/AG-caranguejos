import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_log_file(filepath):
    df = pd.read_csv(filepath)

    plt.figure(figsize=(10, 5))
    plt.plot(df["epoch"], df["best_value"], label="Best value")
    plt.xlabel("Época")
    plt.ylabel("Melhor valor")
    plt.title(f"Convergência - {os.path.basename(filepath)}")
    plt.grid(True)
    plt.legend()
    plt.show()

def plot_multiple_logs(directory):
    files = [f for f in os.listdir(directory) if f.endswith(".csv")]

    plt.figure(figsize=(10, 5))

    for f in files:
        df = pd.read_csv(os.path.join(directory, f))
        plt.plot(df["epoch"], df["best_value"], label=f)

    plt.xlabel("Época")
    plt.ylabel("Melhor valor")
    plt.title(f"Comparação de convergência - {directory}")
    plt.grid(True)
    plt.legend()
    plt.show()
