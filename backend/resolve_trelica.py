
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
    esforcos_por_barra: {barra_id: {no_i, no_j, N_orientado, tensao, deformacao}}
- Além disso, ao executar diretamente, imprime um JSON e uma versão textual formatada com ';' (compatível com o exemplo do enunciado).
"""
import io
from pathlib import Path
from typing import List
import json
import sys


from model import No, Barra, Trelica


def _split(line: str) -> List[str]:
    return [p.strip() for p in line.split(";")]

def criar_trelica_de_dados(dados: dict) -> Trelica:
    """Cria e retorna um objeto Trelica a partir de um dicionário de dados."""
    
    nos_dados = dados.get("nos", [])
    barras_dados = dados.get("barras", [])

    if not nos_dados or not barras_dados:
        raise ValueError("Dados de 'nos' ou 'barras' ausentes no JSON.")

    
    nos_obj_map = {}
    for no_data in nos_dados:
        no = No(
            id=no_data["id"], 
            x=no_data["x"], 
            y=no_data["y"],
            carga=tuple(no_data["carga"]),
            apoio=no_data["apoio"]
        )
        nos_obj_map[no.id] = no

    
    barras_obj = []
    for barra_data in barras_dados:
        no_i = nos_obj_map.get(barra_data["no_i"])
        no_j = nos_obj_map.get(barra_data["no_j"])
        
        if not no_i or not no_j:
            raise ValueError(f"Nó referenciado na barra {barra_data['id']} não encontrado.")

        barra = Barra(
            id=barra_data["id"],
            no_i=no_i,
            no_j=no_j,
            E=barra_data.get("E", 210e9), 
            A=barra_data.get("A", 0.01)    
        )
        barras_obj.append(barra)
    
    
    trelica = Trelica()
    for no in nos_obj_map.values():
        trelica.adicionar_no(no)
    for barra in barras_obj:
        trelica.adicionar_barra(barra)
        
    return trelica

def carregar_entrada(path: str) -> Trelica:
    """
    Carrega arquivo e monta o objeto Trelica.
    Veja docstring do topo para o formato esperado.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    
    try:
        raw = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        raw = p.read_text(encoding="latin-1").splitlines()

    
    lines = [l.strip() for l in raw if l.strip()]

    if len(lines) == 0:
        raise ValueError("Arquivo vazio")

    
    header = _split(lines[0])
    if len(header) < 2:
        raise ValueError("Cabeçalho inválido. Deve ser: n; m")
    n_nos = int(header[0])
    

    idx = 1

    
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

    
    adj = []
    for _ in range(n_nos):
        parts = _split(lines[idx])
        
        row = [int(p) for p in parts]
        if len(row) != n_nos:
            raise ValueError(f"Matriz de adjacência: linha com {len(row)} colunas (esperado {n_nos})")
        adj.append(row)
        idx += 1

    
    for i in range(n_nos):
        parts = _split(lines[idx])
        if len(parts) < 2:
            raise ValueError(f"Linha de carga inválida: {lines[idx]}")
        Fx = float(parts[0])
        Fy = float(parts[1])
        nos[i].carga = (Fx, Fy)
        idx += 1

    
    for i in range(n_nos):
        apoio = lines[idx].strip()
        nos[i].apoio = apoio
        idx += 1

    
    barras: List[Barra] = []
    barra_id = 1
    for i in range(n_nos):
        for j in range(i+1, n_nos):
            if adj[i][j] == 1:
                
                barras.append(Barra(barra_id, nos[i], nos[j]))
                barra_id += 1

    
    t = Trelica()
    for no in nos:
        t.adicionar_no(no)
    for b in barras:
        t.adicionar_barra(b)

    return t

def carregar_entrada_from_stream(stream: io.StringIO) -> Trelica:
    """
    Carrega os dados de um stream de texto (vindo de um upload) e monta o objeto Trelica.
    """
    
    raw = stream.read().splitlines()

    lines = [l.strip() for l in raw if l.strip()]

    if len(lines) == 0:
        raise ValueError("Arquivo vazio")

    header = _split(lines[0])
    if len(header) < 2:
        raise ValueError("Cabeçalho inválido. Deve ser: n; m")
    n_nos = int(header[0])

    idx = 1
    
    
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

    adj = []
    for _ in range(n_nos):
        parts = _split(lines[idx])
        row = [int(p) for p in parts]
        if len(row) != n_nos:
            raise ValueError(f"Matriz de adjacência: linha com {len(row)} colunas (esperado {n_nos})")
        adj.append(row)
        idx += 1

    for i in range(n_nos):
        parts = _split(lines[idx])
        if len(parts) < 2:
            raise ValueError(f"Linha de carga inválida: {lines[idx]}")
        Fx = float(parts[0])
        Fy = float(parts[1])
        nos[i].carga = (Fx, Fy)
        idx += 1

    for i in range(n_nos):
        apoio = lines[idx].strip()
        nos[i].apoio = apoio
        idx += 1

    barras: List[Barra] = []
    barra_id = 1
    for i in range(n_nos):
        for j in range(i+1, n_nos):
            if adj[i][j] == 1:
                barras.append(Barra(barra_id, nos[i], nos[j]))
                barra_id += 1

    t = Trelica()
    for no in nos:
        t.adicionar_no(no)
    for b in barras:
        t.adicionar_barra(b)

    return t


def resolver_trelica_from_stream(stream: io.StringIO) -> dict:
    """
    Resolve a treliça lida de um stream de texto.
    """
    t = carregar_entrada_from_stream(stream)
    t.resolver()

    esforcos_por_barra = {}
    for barra in t.barras:
        N = t._N[barra.id]
        tensao = t._tensoes[barra.id]
        deformacao = t._deformacoes[barra.id]
        esforcos_por_barra[barra.id] = {
            "no_i": barra.no_i.id,
            "no_j": barra.no_j.id,
            "N_orientado": float(N),
            "tensao": float(tensao),
            "deformacao": float(deformacao)
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

def resolver_trelica(path: str) -> dict:
    """
    Resolve a treliça lida do arquivo path.
    Retorna um dicionário JSON-ready com:
      - deslocamentos
      - reacoes
      - esforcos_por_barra (N_orientado, tensao, deformacao)
    """
    t = carregar_entrada(path)
    t.resolver()

    
    esforcos_por_barra = {}
    for barra in t.barras:
        N = t._N[barra.id]
        tensao = t._tensoes[barra.id]
        deformacao = t._deformacoes[barra.id]
        esforcos_por_barra[barra.id] = {
            "no_i": barra.no_i.id,
            "no_j": barra.no_j.id,
            "N_orientado": float(N),
            "tensao": float(tensao),
            "deformacao": float(deformacao)
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
      - Segundo bloco: esforços por barra (para cada barra, imprime N_orientado; tensao; deformacao)
    """
    
    
    desloc = resultados.get("deslocamentos", {})
    nos_ord = list(desloc.keys())

    reacoes = resultados.get("reacoes", {})
    print("\n=== Saída formatada (para avaliação) ===\n")

    
    for no_id in nos_ord:
        if no_id in reacoes:
            Rx = reacoes[no_id]["Rx"]
            Ry = reacoes[no_id]["Ry"]
        else:
            Rx, Ry = 0.0, 0.0
        
        print(f"{Rx:.1f}; {Ry:.1f}")

    
    esforcos = resultados.get("esforcos_por_barra", {})
    for barra_id in sorted(esforcos.keys()):
        e = esforcos[barra_id]
        
        print(f"{e['N_orientado']:.1f}; {e['tensao']:.3e}; {e['deformacao']:.3e}")

    print("\n=== Fim da saída formatada ===\n")


if __name__ == "__main__":
    
    default_path = Path("Exemplo") / "exemplo.txt"

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = str(default_path)

    
    try:
        resultados = resolver_trelica(path)
    except Exception as e:
        print(f"Erro ao resolver treliça: {e}")
        sys.exit(1)

    
    print("=== RESULTADOS (JSON) ===")
    print(json.dumps(resultados, indent=2, ensure_ascii=False))

    
    imprimir_saida_formatada(resultados)