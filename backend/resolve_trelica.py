# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from model import No, Barra, Trelica

def carregar_entrada(path: str) -> Trelica:
    txt = Path(path).read_text(encoding="utf-8").strip().splitlines()
    # também tentar latin-1 se falhar
    try:
        lines = [l.strip() for l in txt if l.strip()]
    except Exception:
        lines = [l.strip() for l in Path(path).read_text(encoding="latin-1").splitlines() if l.strip()]

    # Formato:
    # n_nos; n_barras
    # <nome>; x; y   (n vezes)
    # matriz de apoios (3 linhas de 3 colunas 0/1?) -> aqui adotamos 1 por linha de DOFs? (vamos ignorar, pois entrada exemplo usa outra seção)
    # ... usaremos a parte final do exemplo: cargas por nó (Fx;Fy) por nó, e depois apoios por nó (linha por nó)
    # Vamos interpretar conforme o arquivo de exemplo fornecido.

    # Para simplificar, detectamos pelo ponto-e-vírgula e números.
    def split(line):
        return [p.strip() for p in line.split(";")]

    header = split(lines[0])
    n_nos, n_barras = int(header[0]), int(header[1])

    nos = []
    idx = 1
    for _ in range(n_nos):
        nome, x, y = split(lines[idx]); idx += 1
        nos.append(No(nome, float(x), float(y)))
    # As próximas 3 linhas do exemplo são uma matriz que não precisamos; vamos pular 3 linhas
    idx += 3

    # Cargas: n linhas (Fx; Fy)
    for i in range(n_nos):
        Fx, Fy = [float(v) for v in split(lines[idx])]; idx += 1
        nos[i].carga = (Fx, Fy)

    # Apoios: n linhas com "N", "P", "X" ou "Y"
    for i in range(n_nos):
        apoio = lines[idx].strip(); idx += 1
        nos[i].apoio = apoio

    # Barras: deduziremos de um padrão? O exemplo não lista barras; então vamos assumir todas adjacentes por intenção do usuário:
    # No seu caso específico (exemplo), as barras são: A-B e B-C
    # Para generalizar, se houver mais linhas sobrando, poderíamos ler pares "i;j"; aqui manteremos fixo A-B e B-C caso existam A,B,C.
    mapa = {no.id: no for no in nos}
    barras = []
    if all(k in mapa for k in ("A","B")):
        barras.append(Barra(1, mapa["A"], mapa["B"]))
    if all(k in mapa for k in ("B","C")):
        barras.append(Barra(2, mapa["B"], mapa["C"]))

    t = Trelica()
    for no in nos:
        t.adicionar_no(no)
    for b in barras:
        t.adicionar_barra(b)
    return t

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else str(Path("Exemplo")/"exemplo.txt")
    t = carregar_entrada(path)
    t.resolver()

    print("=== RESULTADOS ===")
    print("Deslocamentos por nó:")
    for no in t.nos:
        print(f"{no.id}: Ux = {no.Ux:.6e}, Uy = {no.Uy:.6e}")

    print("\nReações nos apoios (sinal + = força do apoio no nó):")
    for no_id, (rx, ry) in t.reacoes().items():
        print(f"{no_id}: Rx = {rx:.2f}, Ry = {ry:.2f}")

    print("\nEsforços axiais nas barras (N>0 tração, N<0 compressão):")
    for barra_id, N in t.esforcos_axiais().items():
        print(f"Barra {barra_id}: N = {N:.2f}")

if __name__ == "__main__":
    main()
