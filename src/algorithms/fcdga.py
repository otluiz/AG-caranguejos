import numpy as np

def fcdga(func, dim=30, pop_size=50, gens=1000,
         F=0.6, alpha=1, beta=1, lamb=0.1, n_terr=5):

    pop = np.random.uniform(-5, 5, (pop_size, dim))

    def sexual_trait(x):
        return np.std(x)

    for g in range(gens):
        fitness = np.array([func(x) for x in pop])
        signal  = np.array([sexual_trait(x) for x in pop])
        f_eff = fitness - lamb*(signal**2)

        territories = np.array_split(pop, n_terr)
        new_pop = []

        base_children = pop_size // n_terr
        extra = pop_size % n_terr

        for t_id, T in enumerate(territories):

            if len(T) < 2:
                T = pop  # fallback: usa população toda

            n_children = base_children + (1 if t_id < extra else 0)

            for _ in range(n_children):
                xf = T[np.random.randint(len(T))]

                replace_flag = True if len(T) < 3 else False
                i, j = np.random.choice(len(T), 2, replace=replace_flag)
                xi, xj = T[i], T[j]

                fi, fj = func(xi), func(xj)
                si, sj = sexual_trait(xi), sexual_trait(xj)
                diff = alpha*(fi - fj) + beta*(si - sj)
                p = 1/(1 + np.exp(-diff))

                xw, xl = (xi, xj) if np.random.rand() < p else (xj, xi)

                child = xf + F*(xw - xl) + np.random.normal(0, 0.01, dim)
                new_pop.append(child)

        pop = np.array(new_pop)[:pop_size]

    best = min(pop, key=func)
    return func(best)
