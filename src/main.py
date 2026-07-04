import os
import csv
import time
from datetime import datetime

from algorithms.fcdga import fcdga
from algorithms.de import differential_evolution
from algorithms.ga import genetic_algorithm

from benchmarks.benchmarks import (
    sphere, rastrigin, ackley, rosenbrock, griewank
)

BENCHMARKS = [sphere, rastrigin, ackley, rosenbrock, griewank]

# ============================================================
# Criação de diretórios de log
# ============================================================
def create_log_dir(func_name):
    base = "logs"
    path = os.path.join(base, func_name)
    os.makedirs(path, exist_ok=True)
    return path

# ============================================================
# Criar arquivo CSV
# ============================================================
def csv_logger(directory, run_id, alg_name, func_name):
    filename = os.path.join(directory, f"{alg_name}_{func_name}_{run_id}.csv")
    f = open(filename, "w", newline="")
    writer = csv.writer(f)
    writer.writerow(["epoch", "best_value", "time_seconds"])
    return f, writer

# ============================================================
# Execução com logging por época
# ============================================================
def run_with_logging(algorithm, alg_name, func, **kwargs):
    func_name = func.__name__
    # CRIA diretório logs/ackley/ ou logs/sphere/ etc.
    log_dir = create_log_dir(func_name)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file, writer = csv_logger(log_dir, run_id, alg_name, func_name)

    print(f"\n➡ Rodando {alg_name} com a função {func_name}...")

    pop_size = kwargs.get("pop_size", 50)
    gens     = kwargs.get("gens", 1000)
    dim      = kwargs.get("dim", 30)

    import numpy as np
    pop = np.random.uniform(-5, 5, (pop_size, dim))

    start_total = time.time()

    for epoch in range(gens):
        epoch_start = time.time()

        # roda 1 época
        best_value = algorithm(func, dim=dim, pop_size=pop_size, gens=1)

        epoch_time = time.time() - epoch_start

        writer.writerow([epoch, best_value, epoch_time])
        print(f"Epoch {epoch}: best = {best_value:.5f} | tempo = {epoch_time:.4f}s")

    total_time = time.time() - start_total
    csv_file.close()

    print(f"\n✔ Finalizado! Tempo total: {total_time:.2f} s")
    print(f"✔ Logs em: {log_dir}/{alg_name}_{func_name}_{run_id}.csv\n")


# ============================================================
# Rodar benchmarks em lote para um algoritmo
# ============================================================
def run_batch_algorithm(algorithm, alg_name):
    for func in BENCHMARKS:
        print(f"\n=== Rodando {alg_name} em {func.__name__} ===")
        run_with_logging(algorithm, alg_name, func)

# ============================================================
# Rodar TODOS os algoritmos em TODOS os benchmarks
# ============================================================
def run_batch_all():
    algs = [
        (fcdga, "FCDGA"),
        (differential_evolution, "DE"),
        (genetic_algorithm, "GA")
    ]
    for alg, name in algs:
        run_batch_algorithm(alg, name)

# ============================================================
# MENU
# ============================================================
def menu():
    print("\n================ MENU ================")
    print("1 - Rodar FCDGA")
    print("2 - Rodar DE")
    print("3 - Rodar GA")
    print("4 - Rodar um algoritmo em TODOS os benchmarks")
    print("5 - Rodar TODOS os algoritmos em TODOS os benchmarks")
    print("0 - Sair")
    return input("Escolha: ")

# ============================================================
# LOOP PRINCIPAL
# ============================================================
if __name__ == "__main__":
    func = sphere  # função padrão, mas será ignorada em batch

    while True:
        op = menu()

        if op == "0":
            break

        elif op == "1":
            run_with_logging(fcdga, "FCDGA", func)

        elif op == "2":
            run_with_logging(differential_evolution, "DE", func)

        elif op == "3":
            run_with_logging(genetic_algorithm, "GA", func)

        elif op == "4":
            alg_choice = input("Algoritmo (1=FCDGA, 2=DE, 3=GA): ")

            if alg_choice == "1":
                run_batch_algorithm(fcdga, "FCDGA")
            elif alg_choice == "2":
                run_batch_algorithm(differential_evolution, "DE")
            elif alg_choice == "3":
                run_batch_algorithm(genetic_algorithm, "GA")
            else:
                print("Opção inválida!")

        elif op == "5":
            run_batch_all()

        else:
            print("Opção inválida!")
