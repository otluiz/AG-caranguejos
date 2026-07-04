import numpy as np

def genetic_algorithm(func, dim=30, pop_size=50, gens=1000, mut=0.01):

    pop = np.random.uniform(-5, 5, (pop_size, dim))

    for g in range(gens):
        fitness = np.array([func(x) for x in pop])
        best_idx = np.argsort(fitness)
        elite = pop[best_idx[:2]]

        new_pop = []
        for _ in range(pop_size):
            i, j = np.random.choice(pop_size, 2)
            winner = pop[i] if fitness[i] < fitness[j] else pop[j]
            new_pop.append(winner)

        pop = np.array(new_pop)

        for i in range(0, pop_size, 2):
            if i+1 < pop_size:
                a, b = pop[i], pop[i+1]
                mask = np.random.rand(dim) > 0.5
                a[mask], b[mask] = b[mask], a[mask]
            pop[i] += np.random.normal(0, mut, dim)

        pop[:2] = elite

    best = min(pop, key=func)
    return func(best)
