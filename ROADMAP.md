# 🗺️ Roadmap — FCDGA / AG-caranguejos

Este roadmap acompanha duas frentes que caminham juntas: a evolução do algoritmo em
si (pesquisa) e sua aplicação real no [LexLearn-v3](https://github.com/otluiz) (produto).

---

## ✅ Fase 0 — Algoritmo base (concluída)

- [x] Implementação inicial do FCDGA (seleção sexual + reprodução diferencial)
- [x] Correção de bug: aptidão efetiva (`f_eff`) calculada mas não usada na seleção
- [x] Correção de bug: ausência de elitismo real (população inteira substituída por
      geração, causando regressão do melhor valor entre gerações)
- [x] Validação empírica: FCDGA supera GA clássico e DE/rand/1/bin em Rastrigin e
      Ackley (funções multimodais), com overhead de tempo ~2,4-2,5× — ver `README.md`

## ✅ Fase 1 — Meta-evolução de hiperparâmetros (concluída — MVP local)

- [x] Módulo `meta/` — sandbox seguro (AST + subprocess) para validar código gerado
      por LLM antes de executar
- [x] `meta/llm_ops.py` — operadores de crossover/mutação via Ollama, com prompts
      diretivos para reduzir verbosidade de modelos generalistas (phi3)
- [x] `meta/meta_loop.py` — loop completo: seleção sexual (estilo FCDGA) escolhe pais
      entre variantes de código, LLM recombina, sandbox valida, elitismo decide
      sobrevivência
- [x] Integração de ponta a ponta testada com `phi3:3.8b` rodando em container Docker
      local (`lexlearn-ollama`), evoluindo a função de adaptação do fator `F`

**Aprendizados desta fase**: modelos pequenos (3-4B parâmetros) em VRAM limitada
funcionam para tarefas de geração de código restritas (uma função, assinatura fixa),
desde que o prompt seja bem diretivo e o sandbox tolere falhas graciosamente
(fallback para o pai em caso de código inválido).

---

## 🚧 Fase 2 — MVP de otimização aplicada ao LexLearn (planejada, curto prazo)

Escopo detalhado em [`optimizer_worker_integration.md`](./optimizer_worker_integration.md)
(a ser incorporado ao `architecture_master.md` do LexLearn-v3 após revisão).

- [ ] Serviço `lexlearn-optimizer` no `docker-compose.yml`
- [ ] Tabelas `optimizer_runs` e `config_otimizada` no Postgres
- [ ] Calibração do limiar de similaridade do cache de resumos, **por tipo de
      documento** (CF, CC, CPC, ECA), usando Optuna (não FCDGA — ver justificativa
      no documento de integração)
- [ ] Gate de aprovação (automática com regra conservadora, ou manual) antes de
      qualquer novo threshold entrar em produção
- [ ] Endpoint de leitura em `rag_service.py` com fallback seguro para o valor fixo
      atual

**Critério de sucesso**: redução mensurável de reprocessamentos desnecessários
(falsos negativos do cache) sem aumento de resumos desatualizados servidos (falsos
positivos), medido por tipo de documento.

## 🔭 Fase 3 — Evolução de prompts (Map-Reduce e Quiz)

- [ ] Adaptar `meta/llm_ops.py` para recombinar **templates de prompt** em vez de
      funções Python (reuso direto da infraestrutura da Fase 1)
- [ ] Fitness para prompts de resumo: comparação com resumos revisados por humano
      (se houver curadoria) ou métrica automática de consistência factual
- [ ] Fitness para prompts de quiz: **taxa de aprovação real** em
      `quiz_approval_queue` vs. `quiz_rejected` — sinal de qualidade já existente no
      schema do LexLearn, sem necessidade de avaliação sintética
- [ ] Sandbox mais restritivo que o atual (container efêmero, não só subprocess) se
      os prompts evoluídos passarem a ser usados para gerar conteúdo de produção

## 🔭 Fase 4 — Chunking hierárquico e ranking do RAG

- [ ] Otimizar estratégia de agrupamento de artigos para a fase de Reduce em
      documentos grandes (CPC: 1.072 artigos, CC: 1.807 artigos), minimizando
      chamadas ao LLM sem perder qualidade de resposta
- [ ] Calibrar pesos do ranking de chunks (similaridade semântica + posição
      hierárquica + recência) contra um conjunto de perguntas-gabarito validado
- [ ] Este é o único item do roadmap onde a metáfora evolutiva completa do FCDGA
      (territórios, seleção sexual, reprodução diferencial) se justifica plenamente,
      por ser um problema combinatório real, não um escalar nem um texto único

---

## Fora de escopo (por ora)

- Geração de código de aplicação (rotas, migrations) via evolução — avaliado e
  descartado por risco/benefício desfavorável; ver discussão na Fase 1. O caminho
  recomendado para código de produção continua sendo Claude Code local com testes
  automatizados como grade de aceite.
- Publicação do FCDGA como paper formal — depende da Fase 0 estar
  estatisticamente validada (testes de Wilcoxon/Friedman entre algoritmos,
  benchmarks completos incluindo Sphere/Rosenbrock/Griewank).
