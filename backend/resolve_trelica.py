# -*- coding: utf-8 -*-
"""
resolver_trelica.py
-------------------
Leitura, montagem e resolução da treliça usando model.Trelica.

Formato do arquivo de entrada (Exemplo/exemplo.txt):
- Linha 1: n; m    (n = número de nós, m = número de elementos)   -> m pode ser ignorado (derivado da matriz)
- Próximas n linhas: ID; x; y
- Próximas n linhas: matriz de adjacência n x n (0/1 separadas por ';')  -> simétrica
- Próximas n linhas: cargas nodais (Fx; Fy) em N
- Próximas n linhas: apoios por nó (uma letra por linha: N, P, X ou Y)

Saída:
- Função resolver_trelica(path) retorna um dicionário (JSON-ready) com:
    deslocamentos: {no_id: {Ux, Uy}}
    reacoes: {no_id: {Rx, Ry}}   (apenas nós com apoio)
    esforcos_por_barra: {barra_id: {no_i, no_j, Nx, Ny, N_orientado}}
- Além disso, ao executar diretamente, imprime um JSON e uma versão textual formatada com ';' (compatível com o exemplo do enunciado).
"""

from pathlib import Path
from typing import List
import json
import sys

# importar suas classes do model.py
from model import No, Barra, Trelica


def _split(line: str) -> List[str]:
    return [p.strip() for p in line.split(";")]


def carregar_entrada(path: str) -> Trelica:
    """
    Carrega arquivo e monta o objeto Trelica.
    Veja docstring do topo para o formato esperado.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    # tenta ler em utf-8, senão latin-1
    try:
        raw = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        raw = p.read_text(encoding="latin-1").splitlines()

    # remover linhas em branco e manter a ordem
    lines = [l.strip() for l in raw if l.strip()]

    if len(lines) == 0:
        raise ValueError("Arquivo vazio")

    # cabeçalho
    header = _split(lines[0])
    if len(header) < 2:
        raise ValueError("Cabeçalho inválido. Deve ser: n; m")
    n_nos = int(header[0])
    # m_barras = int(header[1])  # não é estritamente necessário (vamos derivar das ligações)

    idx = 1

    # Ler nós
    nos: List[No] = []
    for _ in range(n_nos):
        parts = _split(lines[idx])
        if len(parts) < 3:
            raise ValueError(f"Linha de nó inválida: {lines[idx]}")
        nome = parts[0]
        x = float(parts[1])
        y = float(parts[2])
        nos.append(No(nome, x, y))
        idx += 1

    # Ler matriz de adjacência n x n
    adj = []
    for _ in range(n_nos):
        parts = _split(lines[idx])
        # aceitar espaços extras; converter para ints
        row = [int(p) for p in parts]
        if len(row) != n_nos:
            raise ValueError(f"Matriz de adjacência: linha com {len(row)} colunas (esperado {n_nos})")
        adj.append(row)
        idx += 1

    # Ler cargas nodais (Fx; Fy)
    for i in range(n_nos):
        parts = _split(lines[idx])
        if len(parts) < 2:
            raise ValueError(f"Linha de carga inválida: {lines[idx]}")
        Fx = float(parts[0])
        Fy = float(parts[1])
        nos[i].carga = (Fx, Fy)
        idx += 1

    # Ler apoios (uma letra por nó)
    for i in range(n_nos):
        apoio = lines[idx].strip()
        nos[i].apoio = apoio
        idx += 1

    # Criar barras a partir da matriz de adjacência (i < j)
    barras: List[Barra] = []
    barra_id = 1
    for i in range(n_nos):
        for j in range(i+1, n_nos):
            if adj[i][j] == 1:
                # usar construtor Barra(id, no_i, no_j) - E e A virão dos defaults do model.py
                barras.append(Barra(barra_id, nos[i], nos[j]))
                barra_id += 1

    # Montar Trelica
    t = Trelica()
    for no in nos:
        t.adicionar_no(no)
    for b in barras:
        t.adicionar_barra(b)

    return t


def resolver_trelica(path: str) -> dict:
    """
    Resolve a treliça lida do arquivo path.
    Retorna um dicionário JSON-ready com:
      - deslocamentos
      - reacoes
      - esforcos_por_barra (Nx, Ny, N_orientado)
    """
    t = carregar_entrada(path)
    t.resolver()

    # construir esforços por barra: Nx, Ny (componentes) e N_orientado (assinado)
    esforcos_por_barra = {}
    for barra in t.barras:
        N = t._N[barra.id]  # esforço axial ao longo da barra (positivo = tração)
        c, s = barra.cos_sin()
        Nx = N * c
        Ny = N * s
        esforcos_por_barra[barra.id] = {
            "no_i": barra.no_i.id,
            "no_j": barra.no_j.id,
            "Nx": float(Nx),
            "Ny": float(Ny),
            "N_orientado": float(N)
        }

    resultados = {
        "deslocamentos": {
            no.id: {"Ux": float(no.Ux), "Uy": float(no.Uy)}
            for no in t.nos
        },
        "reacoes": {
            no_id: {"Rx": float(rx), "Ry": float(ry)}
            for no_id, (rx, ry) in t.reacoes().items()
        },
        "esforcos_por_barra": esforcos_por_barra
    }

    return resultados


def imprimir_saida_formatada(resultados: dict):
    """
    Produz uma saída textual parecida com o exemplo do enunciado,
    usando ponto decimal e ';' como separador, cada linha terminando sem texto extra.
    Estrutura:
      - Primeiro bloco: reações por nó (ordenado pelos nós na entrada). Para nós sem apoio, imprime 0.0; 0.0
      - Segundo bloco: esforços por barra (para cada barra, imprime Nx; Ny; N_orientado)
    """
    # Reações: precisamos manter a ordem dos nós - resultados contém apenas nós com apoio
    # Para recuperar a ordem original, tentamos extrair do JSON de deslocamentos (assume que a ordem lá reflete a leitura)
    desloc = resultados.get("deslocamentos", {})
    nos_ord = list(desloc.keys())

    reacoes = resultados.get("reacoes", {})
    print("\n=== Saída formatada (para avaliação) ===\n")

    # Imprimir reações no mesmo número de linhas do exemplo: uma linha por nó com Rx; Ry
    for no_id in nos_ord:
        if no_id in reacoes:
            Rx = reacoes[no_id]["Rx"]
            Ry = reacoes[no_id]["Ry"]
        else:
            Rx, Ry = 0.0, 0.0
        # formatar com uma casa decimal (exemplo usa .1), mas aqui deixo 1 decimal caso queira ajustar
        print(f"{Rx:.1f}; {Ry:.1f}")

    # Em muitos exemplos, depois imprimem os esforços por barra:
    esforcos = resultados.get("esforcos_por_barra", {})
    for barra_id in sorted(esforcos.keys()):
        e = esforcos[barra_id]
        # imprimir Nx; Ny; N_orientado
        print(f"{e['Nx']:.1f}; {e['Ny']:.1f}; {e['N_orientado']:.1f}")

    print("\n=== Fim da saída formatada ===\n")


if __name__ == "__main__":
    # Caminho padrão (como você pediu): pasta Exemplo/exemplo.txt
    default_path = Path("Exemplo") / "exemplo.txt"

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = str(default_path)

    # Executa e imprime JSON + saída formatada
    try:
        resultados = resolver_trelica(path)
    except Exception as e:
        print(f"Erro ao resolver treliça: {e}")
        sys.exit(1)

    # Imprime JSON (legível)
    print("=== RESULTADOS (JSON) ===")
    print(json.dumps(resultados, indent=2, ensure_ascii=False))

    # Imprime versão textual formatada compatível com enunciado
    imprimir_saida_formatada(resultados)
