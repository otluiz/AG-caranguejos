import json, sys, os
import numpy as np
from collections import defaultdict
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

IN = sys.argv[1]
FIG = sys.argv[2]
os.makedirs(FIG, exist_ok=True)
R = [json.loads(l) for l in open(IN)]
FUNCS = ["sphere", "rastrigin", "ackley", "rosenbrock", "griewank"]
NOME = {"sphere": "Sphere", "rastrigin": "Rastrigin", "ackley": "Ackley",
        "rosenbrock": "Rosenbrock", "griewank": "Griewank"}
ALGS = ["AG", "DE", "FCDGA", "FCDGA-s"]
best = defaultdict(list); tempo = defaultdict(list); curva = defaultdict(list)
for r in R:
    k = (r["alg"], r["func"])
    best[k].append(r["best"]); tempo[k].append(r["tempo_s"]); curva[k].append(r["curva"])

def fmt(v):
    if v == 0: return "0"
    if abs(v) >= 1000 or abs(v) < 0.01: return f"{v:.2e}".replace(".", ",")
    return f"{v:.2f}".replace(".", ",")

print("n por célula:", {k: len(v) for k, v in best.items()}.values().__iter__().__next__())
print("\n## Tabela descritiva (média ± desvio | mediana) e tempo médio por execução")
for f in FUNCS:
    for a in ALGS:
        x = np.array(best[(a, f)])
        print(f"{NOME[f]} | {a} | {fmt(x.mean())} ± {fmt(x.std(ddof=1))} | {fmt(np.median(x))} | "
              f"min {fmt(x.min())} | {np.mean(tempo[(a, f)]):.1f} s")

def holm(ps):
    idx = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0
    for r, i in enumerate(idx):
        run = max(run, (m - r) * ps[i]); adj[i] = min(1, run)
    return adj

print("\n## Mann-Whitney bilateral: FCDGA (repositório) contra cada um, Holm por função")
for ref in ["FCDGA", "FCDGA-s"]:
    print(f"-- referência {ref}")
    for f in FUNCS:
        outros = [a for a in ALGS if a != ref]
        ps, meds = [], []
        for a in outros:
            u, p = stats.mannwhitneyu(best[(ref, f)], best[(a, f)], alternative="two-sided")
            ps.append(p)
            meds.append(np.median(best[(ref, f)]) < np.median(best[(a, f)]))
        adj = holm(np.array(ps))
        s = "; ".join(f"vs {a}: p={adj[i]:.2e} ({'melhor' if meds[i] else 'pior'})" for i, a in enumerate(outros))
        print(f"{NOME[f]}: {s}")

print("\n## Friedman sobre as medianas por função (5 blocos, 4 algoritmos) e postos médios")
M = np.array([[np.median(best[(a, f)]) for a in ALGS] for f in FUNCS])
ranks = np.array([stats.rankdata(row) for row in M])
chi, p = stats.friedmanchisquare(*M.T)
print("postos médios:", dict(zip(ALGS, ranks.mean(0).round(2))), f"chi2={chi:.2f} p={p:.3g}")

print("\n## Postos por função (1 = melhor mediana)")
for f, row in zip(FUNCS, ranks):
    print(NOME[f], dict(zip(ALGS, row)))

# Figuras
cores = {"AG": "#8c8c8c", "DE": "#1f77b4", "FCDGA": "#d62728", "FCDGA-s": "#2ca02c"}
fig, axs = plt.subplots(2, 3, figsize=(11, 7)); axs = axs.ravel(); axs[5].axis("off")
for ax, f in zip(axs, FUNCS):
    ax.boxplot([best[(a, f)] for a in ALGS], labels=ALGS, showfliers=True)
    ax.set_title(NOME[f]); ax.set_yscale("log"); ax.tick_params(axis="x", rotation=30)
axs[0].set_ylabel("melhor valor (escala log)"); axs[3].set_ylabel("melhor valor (escala log)")
plt.tight_layout(); plt.savefig(f"{FIG}/fig_boxplots.png", dpi=200); plt.close()

xs = np.linspace(60000 / 50, 60000, 50) / 1000
fig, axs = plt.subplots(2, 3, figsize=(11, 7)); axs = axs.ravel(); axs[5].axis("off")
for ax, f in zip(axs, FUNCS):
    for a in ALGS:
        c = np.median(np.array(curva[(a, f)]), axis=0)
        ax.plot(xs, c, label=a, color=cores[a])
    ax.set_title(NOME[f]); ax.set_yscale("log"); ax.set_xlabel("avaliações (mil)")
axs[0].set_ylabel("mediana do melhor valor"); axs[3].set_ylabel("mediana do melhor valor")
h, l = axs[0].get_legend_handles_labels(); axs[5].legend(h, l, loc="center", fontsize=12, title="Algoritmo")
plt.tight_layout(); plt.savefig(f"{FIG}/fig_convergencia.png", dpi=200); plt.close()
print("\nfiguras salvas em", FIG)
