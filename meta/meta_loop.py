"""
meta_loop.py
-------------
Loop de meta-evolução: evolui o CÓDIGO das funções de adaptação de
hiperparâmetros do FCDGA (F, alpha/beta, lambda), usando o próprio
mecanismo de seleção sexual do FCDGA em nível de "meta-indivíduo",
e o Ollama como operador de crossover/mutação.

ATENÇÃO: este é um scaffold. Os pontos marcados com "# TODO(integração)"
precisam ser conectados à implementação real em src/algorithms/fcdga.py.
Ajuste conforme a assinatura real da sua classe FCDGA e das funções de
benchmark em src/benchmarks/benchmarks.py.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

import numpy as np

# requer a versão corrigida do fcdga (com parâmetro F_schedule) —
# veja src_algorithms_fcdga_fixed.py entregue junto com este scaffold
from src.algorithms.fcdga import fcdga

from .llm_ops import crossover_llm, mutacao_llm
from .sandbox import executar_com_seguranca

# TODO(integração): troque pelas funções reais de src/benchmarks/benchmarks.py
# se elas diferirem destas — mantendo essas por padrão, o meta-loop já
# funciona de ponta a ponta.
def sphere(x):
    return float(np.sum(x ** 2))


def rastrigin(x):
    A = 10
    return float(A * len(x) + np.sum(x ** 2 - A * np.cos(2 * np.pi * x)))


def ackley(x):
    a, b, c = 20, 0.2, 2 * np.pi
    d = len(x)
    soma1 = np.sum(x ** 2)
    soma2 = np.sum(np.cos(c * x))
    return float(
        -a * np.exp(-b * np.sqrt(soma1 / d)) - np.exp(soma2 / d) + a + np.e
    )


BENCHMARKS = {
    "sphere": sphere,
    "rastrigin": rastrigin,
    "ackley": ackley,
}

NOME_FUNCAO_ADAPTACAO = "f_adaptativo"  # nome que o LLM deve usar na assinatura
DIM_TESTE = 10          # dimensão reduzida para a meta-evolução rodar rápido
GENS_TESTE = 100        # gerações reduzidas por avaliação (velocidade > precisão aqui)
POP_TESTE = 30

CODIGO_SEMENTE = f'''
def {NOME_FUNCAO_ADAPTACAO}(geracao, max_geracoes):
    """Retorna o valor de F (fator diferencial) para a geração atual."""
    F_min, F_max = 0.3, 0.9
    progresso = geracao / max(1, max_geracoes)
    return F_max - (F_max - F_min) * progresso
'''.strip()


@dataclass
class MetaIndividuo:
    codigo: str
    fitness: float = math.inf         # menor é melhor (score agregado nos benchmarks)
    custo_sinal: float = 0.0          # "display" -> aqui, penalidade por complexidade
    valido: bool = True
    erro: str | None = None

    @property
    def fitness_efetivo(self) -> float:
        # equivalente a f_efetivo(x) = f(x) - lambda * C(s(x)) do paper,
        # mas aqui SOMAMOS o custo porque menor-é-melhor
        LAMBDA = 0.01
        return self.fitness + LAMBDA * self.custo_sinal


def custo_complexidade(codigo: str) -> float:
    """Proxy simples de 'custo do sinal': número de linhas não-vazias.
    Substitua por algo mais rico (complexidade ciclomática via `radon`,
    por exemplo) se quiser um sinal mais fiel à metáfora biológica."""
    return float(len([l for l in codigo.splitlines() if l.strip()]))


def avaliar(individuo: MetaIndividuo, n_execucoes: int = 3) -> None:
    """Executa o código candidato num sandbox e, se válido, roda o
    FCDGA completo usando essa função de adaptação nos benchmarks,
    agregando o desempenho em individuo.fitness."""

    ok, saida = executar_com_seguranca(
        individuo.codigo,
        nome_funcao=NOME_FUNCAO_ADAPTACAO,
        args_teste=(10, 100),  # geracao=10, max_geracoes=100 (exemplo)
    )
    if not ok:
        individuo.valido = False
        individuo.erro = saida
        individuo.fitness = math.inf
        return

    # Extrai a função F_schedule do código validado, em namespace restrito
    # (sem builtins perigosos -- o sandbox já garantiu que não há imports
    # nem chamadas proibidas na análise estática; aqui é só a extração).
    namespace: dict = {"__builtins__": {"range": range, "len": len, "min": min, "max": max}}
    try:
        exec(individuo.codigo, namespace)
        funcao_F = namespace[NOME_FUNCAO_ADAPTACAO]
    except Exception as e:
        individuo.valido = False
        individuo.erro = f"Falha ao extrair função: {e}"
        individuo.fitness = math.inf
        return

    scores = []
    for nome_bench, func_bench in BENCHMARKS.items():
        try:
            for _ in range(n_execucoes):
                melhor = fcdga(
                    func_bench, dim=DIM_TESTE, pop_size=POP_TESTE, gens=GENS_TESTE,
                    F_schedule=funcao_F,
                )
                scores.append(melhor)
        except Exception as e:
            individuo.valido = False
            individuo.erro = f"Falha ao rodar fcdga em {nome_bench}: {e}"
            individuo.fitness = math.inf
            return

    individuo.fitness = float(np.mean(scores))
    individuo.custo_sinal = custo_complexidade(individuo.codigo)
    individuo.valido = True


def selecao_sexual(pop: list[MetaIndividuo], alpha=1.0, beta=0.3) -> MetaIndividuo:
    """Escolhe um vencedor via torneio probabilístico estilo FCDGA:
    P(i vence j) = sigmoide(alpha*(fit_j - fit_i) + beta*(custo_j - custo_i))
    (menor fitness/custo => melhor, por isso a inversão de sinal)."""
    i, j = random.sample(pop, 2)

    def sigmoide(x):
        return 1 / (1 + math.exp(-x))

    delta = alpha * (j.fitness_efetivo - i.fitness_efetivo) + beta * (j.custo_sinal - i.custo_sinal)
    return i if random.random() < sigmoide(delta) else j


def rodar_meta_evolucao(
    tamanho_pop: int = 6,
    geracoes: int = 5,
    modelo_llm: str = "phi3:3.8b",  # modelo confirmado disponível no container lexlearn-ollama
) -> MetaIndividuo:
    populacao = [MetaIndividuo(codigo=CODIGO_SEMENTE) for _ in range(tamanho_pop)]
    for ind in populacao:
        avaliar(ind)

    for gen in range(geracoes):
        print(f"\n=== Geração meta {gen + 1}/{geracoes} ===")

        vencedora = selecao_sexual(populacao)
        outra_boa = selecao_sexual(populacao)

        try:
            codigo_filho = crossover_llm(
                vencedora.codigo, vencedora.fitness_efetivo,
                outra_boa.codigo, outra_boa.fitness_efetivo,
                nome_funcao=NOME_FUNCAO_ADAPTACAO,
                modelo=modelo_llm,
            )
        except Exception as e:
            print(f"  [crossover_llm falhou: {e}] usando cópia da vencedora")
            codigo_filho = vencedora.codigo

        if random.random() < 0.3:
            try:
                codigo_filho = mutacao_llm(codigo_filho, NOME_FUNCAO_ADAPTACAO, modelo=modelo_llm)
            except Exception as e:
                print(f"  [mutacao_llm falhou: {e}] mantendo filho sem mutação")

        filho = MetaIndividuo(codigo=codigo_filho)
        avaliar(filho)

        print(f"  válido={filho.valido}  fitness={filho.fitness:.2f}"
              if filho.valido else f"  inválido: {filho.erro}")

        # elitismo simples: substitui o pior indivíduo se o filho for melhor
        pior = max(populacao, key=lambda x: x.fitness_efetivo)
        if filho.valido and filho.fitness_efetivo < pior.fitness_efetivo:
            populacao.remove(pior)
            populacao.append(filho)

    melhor = min(populacao, key=lambda x: x.fitness_efetivo)
    print("\n=== Melhor função de adaptação encontrada ===")
    print(melhor.codigo)
    print(f"fitness_efetivo = {melhor.fitness_efetivo:.4f}")
    return melhor


if __name__ == "__main__":
    rodar_meta_evolucao()
