import numpy as np

def sphere(x):
    return np.sum(x**2)

def rastrigin(x):
    return 10*len(x) + np.sum(x**2 - 10*np.cos(2*np.pi*x))

def ackley(x):
    a, b, c = 20, 0.2, 2*np.pi
    d = len(x)
    return -a*np.exp(-b*np.sqrt(np.sum(x**2)/d)) \
           - np.exp(np.sum(np.cos(c*x))/d) + a + np.e

def rosenbrock(x):
    return np.sum(100*(x[1:] - x[:-1]**2)**2 + (1 - x[:-1])**2)

def griewank(x):
    return np.sum(x**2)/4000 - np.prod(
        np.cos(x/np.sqrt(np.arange(1, len(x)+1)))
    ) + 1
