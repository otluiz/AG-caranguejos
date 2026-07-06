import numpy as np


def fcdga(func, dim=30, pop_size=50, gens=1000,
          F=0.6, alpha=1, beta=1, lamb=0.1, n_terr=5,
          elite_frac=0.1, F_schedule=None,
          return_history=False):
    """
    Versão corrigida do FCDGA original.

    Correções em relação à versão anterior:
      1. A seleção sexual agora usa a aptidão EFETIVA (fitness - lamb*sinal^2),
         não a aptidão bruta -- antes o parâmetro `lamb` não tinha efeito real
         na dinâmica evolutiva, era calculado mas nunca usado.
      2. Elitismo real: os `elite_frac` melhores indivíduos de cada geração
         são preservados intactos na próxima geração, em vez de a população
         inteira ser descartada e substituída por filhos. Isso evita a
         regressão de "melhor valor" entre gerações observada nos gráficos
         de convergência (picos abruptos).

    Extensão para meta-evolução:
      - `F_schedule`: callable opcional (geracao, max_geracoes) -> float.
        Se fornecido, substitui o `F` fixo a cada geração. É o ponto de
        integração usado por meta/meta_loop.py para testar funções de
        adaptação geradas pelo LLM.

    Parâmetros
    ----------
    return_history : bool
        Se True, retorna (melhor_fitness, historico) em vez de só melhor_fitness,
        onde historico[g] = melhor fitness já encontrado ATÉ a geração g
        (curva monotonicamente não-crescente, diferente do gráfico atual
        que plota o melhor DA geração, causando a aparência serrilhada).
    """
    pop = np.random.uniform(-5, 5, (pop_size, dim))

    def sexual_trait(x):
        return np.std(x)

    n_elite = max(1, int(pop_size * elite_frac))
    melhor_global = None
    melhor_global_fitness = np.inf
    historico = []

    for g in range(gens):
        F_atual = F_schedule(g, gens) if F_schedule is not None else F

        fitness = np.array([func(x) for x in pop])
        signal = np.array([sexual_trait(x) for x in pop])
        f_eff = fitness - lamb * (signal ** 2)

        # Atualiza o melhor global (para elitismo e para o histórico de convergência real)
        idx_melhor_gen = np.argmin(fitness)
        if fitness[idx_melhor_gen] < melhor_global_fitness:
            melhor_global_fitness = fitness[idx_melhor_gen]
            melhor_global = pop[idx_melhor_gen].copy()
        historico.append(melhor_global_fitness)

        # --- Elitismo: preserva os n_elite melhores indivíduos (por fitness bruta) ---
        indices_elite = np.argsort(fitness)[:n_elite]
        elite = pop[indices_elite].copy()

        territories = np.array_split(pop, n_terr)
        new_children = []

        n_children_total = pop_size - n_elite
        base_children = n_children_total // n_terr
        extra = n_children_total % n_terr

        for t_id, T in enumerate(territories):
            if len(T) < 2:
                T = pop  # fallback: usa população toda

            n_children = base_children + (1 if t_id < extra else 0)

            for _ in range(n_children):
                xf = T[np.random.randint(len(T))]

                replace_flag = True if len(T) < 3 else False
                i, j = np.random.choice(len(T), 2, replace=replace_flag)
                xi, xj = T[i], T[j]

                # --- usa aptidão EFETIVA na seleção sexual (fix do bug 1) ---
                fi_eff = func(xi) - lamb * (sexual_trait(xi) ** 2)
                fj_eff = func(xj) - lamb * (sexual_trait(xj) ** 2)
                si, sj = sexual_trait(xi), sexual_trait(xj)
                diff = alpha * (fi_eff - fj_eff) + beta * (si - sj)
                diff = np.clip(diff, -500, 500)  # evita overflow no exp para diffs extremos
                p = 1 / (1 + np.exp(-diff))

                xw, xl = (xi, xj) if np.random.rand() < p else (xj, xi)

                child = xf + F_atual * (xw - xl) + np.random.normal(0, 0.01, dim)
                new_children.append(child)

        pop = np.vstack([elite, np.array(new_children)])[:pop_size]

    if melhor_global is None:
        melhor_global = min(pop, key=func)
        melhor_global_fitness = func(melhor_global)

    if return_history:
        return melhor_global_fitness, historico
    return melhor_global_fitness
