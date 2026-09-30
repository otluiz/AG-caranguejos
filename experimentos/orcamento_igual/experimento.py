"""Experimento FCDGA x AG x DE com orçamento igual de avaliações da função objetivo.

Usa o código do repositório otluiz/AG-caranguejos (commit 964cb72) sem alterá-lo:
  - fcdga()              : versão do repositório (seleção sexual como está)
  - fcdga_sinal()        : mesma coisa com o sinal da aptidão invertido na seleção
                           (vence com maior prob. o indivíduo de MENOR f_eff)
  - genetic_algorithm()  : AG do repositório
  - de_padrao()          : DE/rand/1/bin canônico (guarda o fitness, índice j_rand,
                           r1,r2,r3 distintos de i) -- o DE do repositório reavalia
                           func(pop[i]) a cada comparação e gastaria o dobro do
                           orçamento.
O orçamento é imposto por um invólucro que conta avaliações, guarda o melhor valor
já visto e interrompe a execução ao atingir o limite.
"""
import sys, os, json, time
import numpy as np
from multiprocessing import Pool

REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO)
from src.algorithms.fcdga import fcdga
from src.algorithms.ga import genetic_algorithm
from src.benchmarks import benchmarks as B

DIM = 30
BUDGET = int(os.environ.get("BUDGET", 60000))
RUNS = int(os.environ.get("RUNS", 30))
CHECK = np.linspace(BUDGET / 50, BUDGET, 50).astype(int)  # pontos da curva
FUNCS = {"sphere": B.sphere, "rastrigin": B.rastrigin, "ackley": B.ackley,
         "rosenbrock": B.rosenbrock, "griewank": B.griewank}


class Esgotado(Exception):
    pass


class Orcamento:
    def __init__(self, f, limite):
        self.f, self.limite, self.n = f, limite, 0
        self.melhor = np.inf
        self.curva = []
        self.k = 0

    def __call__(self, x):
        if self.n >= self.limite:
            raise Esgotado
        v = float(self.f(x))
        self.n += 1
        if v < self.melhor:
            self.melhor = v
        while self.k < len(CHECK) and self.n >= CHECK[self.k]:
            self.curva.append(self.melhor)
            self.k += 1
        return v


def fcdga_sinal(func, dim=30, pop_size=50, gens=10**9, F=0.6, alpha=1, beta=1,
                lamb=0.1, n_terr=5, elite_frac=0.1):
    """Idêntico ao fcdga() do repositório, exceto o sinal do termo de aptidão."""
    pop = np.random.uniform(-5, 5, (pop_size, dim))
    trait = lambda x: np.std(x)
    n_elite = max(1, int(pop_size * elite_frac))
    for g in range(gens):
        fitness = np.array([func(x) for x in pop])
        elite = pop[np.argsort(fitness)[:n_elite]].copy()
        territories = np.array_split(pop, n_terr)
        n_total = pop_size - n_elite
        base, extra = n_total // n_terr, n_total % n_terr
        kids = []
        for t_id, T in enumerate(territories):
            if len(T) < 2:
                T = pop
            for _ in range(base + (1 if t_id < extra else 0)):
                xf = T[np.random.randint(len(T))]
                i, j = np.random.choice(len(T), 2, replace=len(T) < 3)
                xi, xj = T[i], T[j]
                fi = func(xi) - lamb * trait(xi) ** 2
                fj = func(xj) - lamb * trait(xj) ** 2
                diff = alpha * (fj - fi) + beta * (trait(xi) - trait(xj))  # <- sinal
                p = 1 / (1 + np.exp(-np.clip(diff, -500, 500)))
                xw, xl = (xi, xj) if np.random.rand() < p else (xj, xi)
                kids.append(xf + F * (xw - xl) + np.random.normal(0, 0.01, dim))
        pop = np.vstack([elite, np.array(kids)])[:pop_size]


def de_padrao(func, dim=30, pop_size=50, gens=10**9, F=0.6, CR=0.9):
    pop = np.random.uniform(-5, 5, (pop_size, dim))
    fit = np.array([func(x) for x in pop])
    idx = np.arange(pop_size)
    for g in range(gens):
        for i in range(pop_size):
            r1, r2, r3 = np.random.choice(idx[idx != i], 3, replace=False)
            mutant = pop[r1] + F * (pop[r2] - pop[r3])
            mask = np.random.rand(dim) < CR
            mask[np.random.randint(dim)] = True
            trial = np.where(mask, mutant, pop[i])
            ft = func(trial)
            if ft <= fit[i]:
                pop[i], fit[i] = trial, ft


ALGS = {
    "AG": lambda f: genetic_algorithm(f, dim=DIM, gens=10**9),
    "DE": lambda f: de_padrao(f, dim=DIM),
    "FCDGA": lambda f: fcdga(f, dim=DIM, gens=10**9),
    "FCDGA-s": lambda f: fcdga_sinal(f, dim=DIM),
}


def uma_execucao(args):
    alg, fname, run = args
    seed = 1000 * run + 17
    np.random.seed(seed)
    orc = Orcamento(FUNCS[fname], BUDGET)
    t0 = time.perf_counter()
    try:
        ALGS[alg](orc)
    except Esgotado:
        pass
    dt = time.perf_counter() - t0
    while len(orc.curva) < len(CHECK):
        orc.curva.append(orc.melhor)
    return {"alg": alg, "func": fname, "run": run, "seed": seed, "best": orc.melhor,
            "fes": orc.n, "tempo_s": dt, "curva": orc.curva}


if __name__ == "__main__":
    tarefas = [(a, f, r) for f in FUNCS for a in ALGS for r in range(RUNS)]
    out = os.environ.get("OUT", "resultados.jsonl")
    with Pool(int(os.environ.get("PROCS", 7))) as pool, open(out, "w") as fh:
        for k, res in enumerate(pool.imap_unordered(uma_execucao, tarefas), 1):
            fh.write(json.dumps(res) + "\n"); fh.flush()
            if k % 20 == 0:
                print(f"{k}/{len(tarefas)}", flush=True)
    print("fim")
