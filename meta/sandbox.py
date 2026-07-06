"""
sandbox.py
-----------
Executa com segurança um trecho de código Python gerado pelo LLM,
validando sintaxe antes de rodar e isolando em subprocesso com timeout.

Uso típico:
    ok, resultado_ou_erro = executar_com_seguranca(codigo_fonte, nome_funcao="f_adaptativo")
"""

import ast
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

# Nós da AST que NÃO são permitidos no código gerado (evita imports perigosos,
# acesso a arquivo, rede, exec/eval, etc.)
NODES_PROIBIDOS = (ast.Import, ast.ImportFrom)
NOMES_PROIBIDOS = {
    "open", "exec", "eval", "compile", "__import__",
    "os", "sys", "subprocess", "socket", "shutil",
}


class CodigoInvalidoError(Exception):
    pass


def validar_sintaxe(codigo: str) -> ast.Module:
    """Levanta CodigoInvalidoError se o código não for Python válido
    ou usar construções proibidas."""
    try:
        arvore = ast.parse(codigo)
    except SyntaxError as e:
        raise CodigoInvalidoError(f"Erro de sintaxe: {e}") from e

    for node in ast.walk(arvore):
        if isinstance(node, NODES_PROIBIDOS):
            raise CodigoInvalidoError(
                f"Import não permitido em código gerado: linha {node.lineno}"
            )
        if isinstance(node, ast.Name) and node.id in NOMES_PROIBIDOS:
            raise CodigoInvalidoError(
                f"Uso de nome proibido '{node.id}' na linha {node.lineno}"
            )
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise CodigoInvalidoError(
                f"Acesso a atributo dunder proibido na linha {node.lineno}"
            )

    return arvore


def executar_com_seguranca(
    codigo: str,
    nome_funcao: str,
    args_teste: tuple = (),
    timeout_s: float = 5.0,
) -> tuple[bool, str]:
    """
    Valida e executa `codigo` (que deve definir `nome_funcao`) em um
    subprocesso isolado, chamando a função com `args_teste` só para
    garantir que ela executa sem lançar exceção.

    Retorna (sucesso: bool, saida_ou_erro: str).
    """
    try:
        validar_sintaxe(codigo)
    except CodigoInvalidoError as e:
        return False, str(e)

    # Monta o script em duas partes SEPARADAS -- nunca embutir `codigo`
    # dentro de um template com indentação, pois a indentação interna do
    # código gerado (ex.: corpo de função) quebra o textwrap.dedent().
    rodape = textwrap.dedent(f"""
        if __name__ == "__main__":
            resultado = {nome_funcao}(*{args_teste!r})
            print(repr(resultado))
    """)
    script = f"{codigo}\n\n{rodape}"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as f:
        f.write(script)
        caminho = f.name

    try:
        proc = subprocess.run(
            [sys.executable, caminho],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return False, f"Timeout ({timeout_s}s) ao executar código gerado"
    finally:
        Path(caminho).unlink(missing_ok=True)

    if proc.returncode != 0:
        return False, proc.stderr.strip()[-500:]

    return True, proc.stdout.strip()
