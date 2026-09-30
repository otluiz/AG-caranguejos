# 🦀 FCDGA — Fiddler Crab-inspired Differential-Genetic Algorithm

**Um operador evolutivo bioinspirado no comportamento de seleção sexual dos caranguejos violinistas (*Uca* spp.), combinando o melhor de Algoritmos Genéticos e Evolução Diferencial.**

![status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)
![python](https://img.shields.io/badge/python-3.11-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 🌊 A inspiração

Caranguejos violinistas machos possuem uma garra hipertrofiada usada em *displays* rítmicos para atrair fêmeas e competir por território. Fêmeas escolhem parceiros com base no sinal visual **e** na aptidão física real do macho — um equilíbrio natural entre "aparência" (exploração) e "qualidade genética" (intensificação).

O **FCDGA** traduz esse mecanismo para otimização contínua:

- 🏝️ **Territórios**: a população é dividida em subgrupos com competição local
- 💪 **Traço sexual sintético**: cada indivíduo carrega um "display" além da aptidão pura
- 🎲 **Seleção sexual probabilística**: chance de vencer um duelo via função sigmoide, combinando aptidão e sinal
- 🧬 **Reprodução diferencial**: a fêmea escolhida atua como vetor-base da recombinação (estilo DE), cruzada com machos vencedores de cada território

O resultado é um híbrido AG + DE que busca aumentar a diversidade populacional e evitar convergência prematura em funções multimodais. Os resultados atuais mostram que isso funciona no Rastrigin, mas que a intensificação ainda fica abaixo da DE clássica nas demais funções (ver Resultados).

📄 O paper completo com a fundamentação teórica e metodologia está em [`Latex/fcdga.latex`](Latex/fcdga.latex).

---

## 📊 Resultados

Resultados do experimento com **orçamento igual de avaliações** para todos os
algoritmos: 60.000 avaliações da função objetivo por execução, D = 30, 30 execuções
por configuração com sementes fixas, Mann-Whitney com correção de Holm e Friedman.
Protocolo completo, código, dados brutos e figuras estão em
[`experimentos/orcamento_igual/`](experimentos/orcamento_igual/).

<p align="center">
  <img src="experimentos/orcamento_igual/figuras/fig_boxplots.png" width="720" alt="Boxplots das cinco funções">
</p>

Mediana do melhor valor encontrado (menor é melhor):

| Função     | AG       | DE/rand/1/bin | FCDGA (versão original) | **FCDGA (atual)** |
|------------|---------:|--------------:|------------------------:|------------------:|
| Sphere     | 2,58e-04 | **3,16e-10**  | 9,31                    | 2,00              |
| Rastrigin  | 59,73    | 179,11        | 103,38                  | **49,77**         |
| Ackley     | 3,25     | **1,60e-05**  | 3,38                    | 3,37              |
| Rosenbrock | 30,06    | **21,52**     | 4,55e+03                | 191,69            |
| Griewank   | 1,53e-05 | **2,68e-11**  | 0,17                    | 0,28              |

O que os dados mostram:

- **A DE clássica é a melhor em 4 de 5 funções.** Em Sphere, Ackley e Griewank ela
  chega a valores praticamente nulos.
- **O FCDGA atual é o melhor em Rastrigin**, com diferença significativa em relação
  ao AG (p = 0,013) e à DE (p < 0,001). No Rastrigin o AG converge prematuramente
  (estaciona perto de 60 com cerca de 6 mil avaliações), e o FCDGA continua
  melhorando até cerca de 40 mil.
- **A correção do sinal da seleção sexual** (ver abaixo) melhorou o algoritmo em
  Sphere, Rastrigin e Rosenbrock (p < 0,001), sem diferença em Ackley e com leve
  piora em Griewank (p = 0,031).
- Nas funções unimodais o FCDGA é o mais lento. Uma hipótese, ainda não testada: o
  traço sexual `std(x)` dá bônus a coordenadas espalhadas, mas o ótimo dessas funções
  está na origem, onde `std(x) = 0`.

> **Nota sobre resultados anteriores.** Versões anteriores deste README diziam que o
> FCDGA superava consistentemente o AG e a DE em Rastrigin e Ackley. Aqueles números
> vinham de uma comparação com o mesmo número de **gerações**, mas por geração o
> FCDGA faz cerca de 140 avaliações, a DE 100 e o AG 50. Com o mesmo número de
> **avaliações**, a vantagem só se mantém no Rastrigin, e apenas com a seleção
> corrigida.

### Correção do sinal na seleção sexual

Como o problema é de minimização, o macho com menor aptidão efetiva deve ter mais
chance de vencer o duelo. A versão original usava `alpha * (fi_eff - fj_eff)`, que dá
probabilidade menor que 0,5 ao melhor indivíduo: o duelo favorecia o pior, e o filho
era deslocado para longe da melhor solução. O `fcdga()` atual usa
`alpha * (fj_eff - fi_eff)`. O comportamento antigo continua disponível com
`fcdga(..., favorece_pior=True)`, só para reproduzir os resultados da versão
original.

---

## 🚀 Instalação

```bash
git clone https://github.com/otluiz/AG-caranguejos.git
cd AG-caranguejos
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Uso rápido

```python
from src.algorithms.fcdga import fcdga
from src.benchmarks.benchmarks import rastrigin

melhor_fitness = fcdga(
    func=rastrigin,
    dim=30,
    pop_size=50,
    gens=500,
    n_terr=5,
)
print(f"Melhor fitness encontrado: {melhor_fitness}")
```

Para acompanhar a curva de convergência real (monotonicamente decrescente, não o
melhor-por-geração bruto):

```python
melhor_fitness, historico = fcdga(rastrigin, dim=30, gens=500, return_history=True)
```

Ou rode a bateria completa de benchmarks (compara FCDGA, AG clássico e DE):

```bash
python src/benchmarks/benchmarks.py
```

Os resultados (CSVs de convergência + gráficos) são salvos em `src/logs/<algoritmo>/<funcao>/`.

---

## 🗂️ Estrutura do projeto

```
AG-caranguejos/
├── Latex/                    # Paper (fonte LaTeX)
│   └── fcdga.latex
├── src/
│   ├── algorithms/
│   │   ├── fcdga.py           # Algoritmo proposto (hook F_schedule p/ meta-evolução; favorece_pior=True reproduz a versão original)
│   │   ├── ga.py               # AG clássico (baseline)
│   │   └── de.py                # DE/rand/1/bin (baseline)
│   ├── benchmarks/
│   │   └── benchmarks.py     # Funções: Sphere, Rastrigin, Ackley, Rosenbrock, Griewank
│   ├── caranguejos_violonistas.py
│   └── logs/                    # Saídas de execução (não versionado)
├── meta/                       # Meta-evolução: LLM local evolui os hiperparâmetros do FCDGA
│   ├── sandbox.py               # Validação (AST) + execução isolada de código gerado
│   ├── llm_ops.py                # Crossover/mutação via Ollama
│   └── meta_loop.py               # Orquestração do ciclo de meta-evolução
├── experimentos/
│   └── orcamento_igual/        # Experimento com orçamento igual (código, dados, figuras)
├── docs/figures/               # Gráficos da versão anterior (comparação por gerações)
├── ROADMAP.md                  # Plano de fases (algoritmo + aplicação real)
└── README.md
```

---

## 🧪 Funções de benchmark

| Função      | Modalidade    | Domínio típico     |
|-------------|---------------|---------------------|
| Sphere      | Unimodal      | [-5.12, 5.12]        |
| Rastrigin   | Multimodal    | [-5.12, 5.12]        |
| Ackley      | Multimodal    | [-32.768, 32.768]    |
| Rosenbrock  | Unimodal (vale estreito) | [-5, 10]  |
| Griewank    | Multimodal    | [-600, 600]          |

---

## 🤖 Meta-evolução: um LLM local evolui o próprio algoritmo

Além de otimizar funções matemáticas, o FCDGA pode evoluir **seus próprios
hiperparâmetros** — em vez de valores fixos de `F` (fator diferencial), um LLM local
(via [Ollama](https://ollama.com)) gera e recombina *funções de adaptação* de `F`,
usando a mesma lógica de seleção sexual do algoritmo, agora aplicada a variantes de
código:

```python
from meta.meta_loop import rodar_meta_evolucao

melhor = rodar_meta_evolucao(tamanho_pop=6, geracoes=5)
print(melhor.codigo)  # a função de adaptação de F que melhor performou nos benchmarks
```

Todo código gerado passa por validação estática (AST) e execução isolada em
subprocesso com timeout antes de ser aceito — ver `meta/sandbox.py`. Testado
localmente com `phi3:3.8b` rodando em container Docker (4GB VRAM).

---

## 🏛️ Aplicação real: LexLearn

Esse mesmo mecanismo está sendo levado para calibrar parâmetros de produção da
plataforma educacional LexLearn — a começar pelo limiar de similaridade do cache de
resumos de leis (CF, CC, CPC, ECA). Arquitetura de integração, alterações de schema e
o motivo de usar Optuna em vez do FCDGA nesse caso específico estão documentados em
`optimizer_worker_integration.md` (repositório do LexLearn).

---

## 🛣️ Roadmap

Plano completo, com fases concluídas e planejadas (algoritmo + aplicação real), em
[`ROADMAP.md`](ROADMAP.md). Resumo:

- [x] Correção de bugs de elitismo e fitness efetivo (Fase 0)
- [x] Meta-evolução de hiperparâmetros via LLM local (Fase 1)
- [ ] MVP de otimização aplicada ao LexLearn — threshold de similaridade (Fase 2)
- [ ] Evolução de prompts de resumo e quiz (Fase 3)
- [ ] Chunking hierárquico e pesos de ranking do RAG (Fase 4)
- [x] Testes estatísticos formais (Mann-Whitney/Friedman) entre FCDGA, AG e DE, com orçamento igual de avaliações
- [x] Correção do sinal da seleção sexual (minimização)
- [ ] Publicação dos resultados finais no paper

Acompanhe o progresso no [GitHub Project](../../projects) do repositório.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* com sugestões, bugs ou novas funções de benchmark, ou enviar um *pull request*.

```bash
git checkout -b feature/minha-melhoria
git commit -m "Descrição da melhoria"
git push origin feature/minha-melhoria
```

---

## 📚 Referências

- HOLLAND, J. H. *Adaptation in natural and artificial systems*. University of Michigan Press, 1975.
- STORN, R.; PRICE, K. Differential evolution — A simple and efficient heuristic for global optimization. *Journal of Global Optimization*, 1997.
- FOSTER, S. A. The evolution of behavior in fiddler crabs. *Biological Reviews*, 1996.
- BASOLO, A. L. Sexual selection and signal evolution in fiddler crabs. *Journal of Experimental Biology*, 2000.
- ANDERSSON, M. *Sexual Selection*. Princeton University Press, 1994.

---

## 📄 Licença

Este projeto está sob a licença MIT — veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<p align="center">
  <i>Feito com 🦀 e evolução diferencial, por <a href="https://github.com/otluiz">Othon Luiz</a></i>
</p>
