import numpy as np

# ----------------------------------------------------
# Funções Benchmark
# ----------------------------------------------------
def sphere(x):
    return np.sum(x**2)

def rastrigin(x):
    return 10*len(x) + np.sum(x**2 - 10*np.cos(2*np.pi*x))

def ackley(x):
    a, b, c = 20, 0.2, 2 * np.pi
    d = len(x)
    return -a * np.exp(-b*np.sqrt(np.sum(x**2)/d)) - np.exp(np.sum(np.cos(c*x))/d) + a + np.e

def rosenbrock(x):
    return np.sum(100*(x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def griewank(x):
    return np.sum(x**2)/4000 - np.prod(np.cos(x/np.sqrt(np.arange(1, len(x)+1)))) + 1

# ----------------------------------------------------
# FCDGA - Fiddler Crab Differential Genetic Algorithm
# ----------------------------------------------------
def fcdga(func, dim=30, pop_size=50, gens=1000, F=0.6, alpha=1, beta=1, lamb=0.1, n_terr=5):
    # População inicial
    pop = np.random.uniform(-5, 5, (pop_size, dim))

    def sexual_trait(x):
        # Exemplo simples: desvio padrão dos genes como "sinal"
        return np.std(x)

    for g in range(gens):
        # Avaliação
        fitness = np.array([func(x) for x in pop])
        signal  = np.array([sexual_trait(x) for x in pop])

        # Fitness efetivo com custo do sinal
        f_eff = fitness - lamb * (signal ** 2)

        # Divisão em territórios (mantém tamanhos parecidos)
        territories = np.array_split(pop, n_terr)
        territories_f = np.array_split(f_eff, n_terr)  # fitness efetivo por território

        new_pop = []

        # Quantos filhos cada território gera
        base_children = pop_size // n_terr
        extra_children = pop_size % n_terr  # sobras são distribuídas nos primeiros territórios

        for t_idx, (T, Tf) in enumerate(zip(territories, territories_f)):
            # Quantidade de filhos para este território
            n_children = base_children + (1 if t_idx < extra_children else 0)

            # Segurança: se território tiver menos de 2 indivíduos, usa a população global
            if len(T) < 2:
                T = pop
                Tf = f_eff

            for _ in range(n_children):
                # Seleciona uma fêmea aleatória no território
                xf = T[np.random.randint(len(T))]

                # Seleciona dois machos (índices) – se território for pequeno, permite reposição
                replace_flag = True if len(T) < 3 else False
                i, j = np.random.choice(len(T), 2, replace=replace_flag)
                xi, xj = T[i], T[j]

                fi, fj = func(xi), func(xj)
                si, sj = sexual_trait(xi), sexual_trait(xj)

                # Probabilidade do macho i "vencer" j
                diff = alpha * (fi - fj) + beta * (si - sj)
                p = 1 / (1 + np.exp(-diff))  # sigmoide

                if np.random.rand() < p:
                    xw, xl = xi, xj  # winner, loser
                else:
                    xw, xl = xj, xi

                # Reprodução diferencial guiada pela fêmea
                child = xf + F * (xw - xl) + np.random.normal(0, 0.01, dim)
                new_pop.append(child)

        # Garante que o tamanho bate certinho
        new_pop = np.array(new_pop)
        if len(new_pop) > pop_size:
            new_pop = new_pop[:pop_size]

        pop = new_pop

    # Melhor indivíduo final
    best = min(pop, key=func)
    return func(best)

# ----------------------------------------------------
# Differential Evolution clássico
# ----------------------------------------------------
def differential_evolution(func, dim=30, pop_size=50, gens=1000, F=0.6, CR=0.9):
    pop = np.random.uniform(-5, 5, (pop_size, dim))

    for g in range(gens):
        for i in range(pop_size):
            a, b, c = np.random.choice(pop_size, 3, replace=False)
            mutant = pop[a] + F*(pop[b] - pop[c])
            cross = np.where(np.random.rand(dim) < CR, mutant, pop[i])

            if func(cross) < func(pop[i]):
                pop[i] = cross

    best = min(pop, key=func)
    return func(best)

# ----------------------------------------------------
# Algoritmo Genético clássico (simples)
# ----------------------------------------------------
def genetic_algorithm(func, dim=30, pop_size=50, gens=1000, mut=0.01):
    pop = np.random.uniform(-5, 5, (pop_size, dim))

    for g in range(gens):
        fitness = np.array([func(x) for x in pop])
        idx = np.argsort(fitness)
        elite = pop[idx[:2]]

        # Seleção por torneio
        new_pop = []
        for _ in range(pop_size):
            i, j = np.random.choice(pop_size, 2)
            winner = pop[i] if fitness[i] < fitness[j] else pop[j]
            new_pop.append(winner)

        pop = np.array(new_pop)

        # Crossover + mutação
        for i in range(0, pop_size, 2):
            if i+1 < pop_size:
                a, b = pop[i], pop[i+1]
                mask = np.random.rand(dim) > 0.5
                a[mask], b[mask] = b[mask], a[mask]
            pop[i] += np.random.normal(0, mut, dim)

        pop[:2] = elite  # elitismo

    best = min(pop, key=func)
    return func(best)

# ----------------------------------------------------
# Experimento comparativo completo
# ----------------------------------------------------
def run_experiment(func, name, runs=30):
    results_fcdga = []
    results_de    = []
    results_ga    = []

    for _ in range(runs):
        results_fcdga.append(fcdga(func))
        results_de.append(differential_evolution(func))
        results_ga.append(genetic_algorithm(func))

    print(f"\n=== {name} ===")
    print("FCDGA:", np.mean(results_fcdga), np.std(results_fcdga), min(results_fcdga))
    print("DE   :", np.mean(results_de), np.std(results_de), min(results_de))
    print("GA   :", np.mean(results_ga), np.std(results_ga), min(results_ga))

# Executar teste
run_experiment(sphere, "Sphere")
run_experiment(rastrigin, "Rastrigin")
run_experiment(ackley, "Ackley")
run_experiment(rosenbrock, "Rosenbrock")
run_experiment(griewank, "Griewank")
