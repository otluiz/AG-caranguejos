"""
llm_ops.py
-----------
Operadores de crossover e mutação que usam um LLM local via Ollama
para recombinar/variar trechos de código Python.

Requer Ollama rodando localmente (padrão: http://localhost:11434).
Instale um modelo antes de usar, ex.: `ollama pull qwen2.5-coder:7b`
"""

import json
import re
import urllib.error
import urllib.request

OLLAMA_URL = "http://127.0.0.1:11435/api/generate"  # 127.0.0.1 evita resolução IPv6 (::1) que pode não responder no mapeamento Docker
MODELO_PADRAO = "phi3:3.8b"  # nome exato conforme `ollama list` no container lexlearn-ollama


def _chamar_ollama(prompt: str, modelo: str = MODELO_PADRAO, temperatura: float = 0.7) -> str:
    payload = {
        "model": modelo,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperatura},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:  # phi3 pode ser lento/verboso
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Ollama respondeu HTTP {e.code} em {OLLAMA_URL} (modelo='{modelo}'): {corpo}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Não foi possível conectar ao Ollama em {OLLAMA_URL}: {e}. "
            f"Confira se `docker ps` mostra lexlearn-ollama rodando e a porta mapeada."
        ) from e
    return data.get("response", "")


def _extrair_codigo(texto: str) -> str:
    """Extrai o primeiro bloco ```python ... ``` da resposta do LLM.
    Se não houver bloco, assume que a resposta inteira é código."""
    match = re.search(r"```(?:python)?\s*(.*?)```", texto, re.DOTALL)
    return match.group(1).strip() if match else texto.strip()


PROMPT_CROSSOVER = """\
Você é um gerador de código Python. NÃO explique nada, NÃO cumprimente, \
NÃO adicione comentários fora do código. Sua ÚNICA saída deve ser um \
bloco de código.

Contexto: duas variantes de uma função de adaptação de hiperparâmetro \
para um algoritmo evolutivo (FCDGA), com o desempenho de cada uma em \
benchmarks (menor é melhor).

--- Variante A (fitness={fitness_a:.4f}) ---
{codigo_a}

--- Variante B (fitness={fitness_b:.4f}) ---
{codigo_b}

Tarefa: escreva UMA função Python chamada exatamente `{nome_funcao}`, com \
a mesma assinatura das variantes acima, combinando os elementos mais \
eficazes de A e B.

Responda SOMENTE com:
```python
def {nome_funcao}(...):
    ...
```
"""

PROMPT_MUTACAO = """\
Você é um gerador de código Python. NÃO explique nada, NÃO cumprimente, \
NÃO adicione comentários fora do código. Sua ÚNICA saída deve ser um \
bloco de código.

--- Função original ---
{codigo}

Tarefa: gere uma pequena variação desta função — troque uma constante, \
uma condição, ou a forma do decaimento — mantendo a mesma assinatura de \
`{nome_funcao}` e a mesma finalidade geral. Mude só um aspecto por vez.

Responda SOMENTE com:
```python
def {nome_funcao}(...):
    ...
```
"""


def crossover_llm(
    codigo_a: str, fitness_a: float,
    codigo_b: str, fitness_b: float,
    nome_funcao: str,
    modelo: str = MODELO_PADRAO,
) -> str:
    """Pede ao LLM uma recombinação de duas variantes de código."""
    prompt = PROMPT_CROSSOVER.format(
        codigo_a=codigo_a, fitness_a=fitness_a,
        codigo_b=codigo_b, fitness_b=fitness_b,
        nome_funcao=nome_funcao,
    )
    resposta = _chamar_ollama(prompt, modelo=modelo)
    return _extrair_codigo(resposta)


def mutacao_llm(codigo: str, nome_funcao: str, modelo: str = MODELO_PADRAO) -> str:
    """Pede ao LLM uma pequena mutação pontual do código."""
    prompt = PROMPT_MUTACAO.format(codigo=codigo, nome_funcao=nome_funcao)
    resposta = _chamar_ollama(prompt, modelo=modelo)
    return _extrair_codigo(resposta)
