import numpy as np

def differential_evolution(func, dim=30, pop_size=50, gens=1000,
                           F=0.6, CR=0.9):

    pop = np.random.uniform(-5, 5, (pop_size, dim))

    for g in range(gens):
        for i in range(pop_size):
            a, b, c = np.random.choice(pop_size, 3, replace=False)
            mutant = pop[a] + F*(pop[b] - pop[c])
            trial = np.where(np.random.rand(dim) < CR, mutant, pop[i])

            if func(trial) < func(pop[i]):
                pop[i] = trial

    best = min(pop, key=func)
    return func(best)
