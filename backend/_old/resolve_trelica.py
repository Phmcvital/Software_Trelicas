# -*- coding: latin-1 -*-
#resolve a treliça

import numpy as np
from model import No, Barra

# ----------------------------------------------------
# Monta a matriz de rigidez global da treli�a
# ----------------------------------------------------
def montar_matriz_global(nos, barras):
    ndof = 2 * len(nos)  # 2 graus de liberdade por n� (x, y)
    K = np.zeros((ndof, ndof))  # matriz global inicializada com zeros

    for barra in barras:
        k_local = np.array(barra.matriz_rigidez_local())
        i = nos.index(barra.no_i)
        j = nos.index(barra.no_j)

        # mapeamento dos DOFs (x,y de cada n�)
        dof = [2*i, 2*i+1, 2*j, 2*j+1]

        # adiciona k_local em K global
        for a in range(4):
            for b in range(4):
                K[dof[a], dof[b]] += k_local[a, b]

    return K

# ----------------------------------------------------
# Monta o vetor de for�as globais
# ----------------------------------------------------
def montar_vetor_forcas(nos):
    F = []
    for no in nos:
        F.extend([no.carga[0], no.carga[1]])  # Fx, Fy de cada n�
    return np.array(F)

# ----------------------------------------------------
# Aplica condi��es de contorno (apoios)
# ----------------------------------------------------
def aplicar_condicoes_contorno(K, F, nos):
    K_mod = K.copy()
    F_mod = F.copy()

    for i, no in enumerate(nos):
        if no.apoio == "X":  # engaste em X
            dof = 2*i
            K_mod[dof, :] = 0
            K_mod[:, dof] = 0
            K_mod[dof, dof] = 1
            F_mod[dof] = 0

        elif no.apoio == "Y":  # engaste em Y
            dof = 2*i+1
            K_mod[dof, :] = 0
            K_mod[:, dof] = 0
            K_mod[dof, dof] = 1
            F_mod[dof] = 0

        elif no.apoio == "XY":  # n� engastado em X e Y
            for dof in [2*i, 2*i+1]:
                K_mod[dof, :] = 0
                K_mod[:, dof] = 0
                K_mod[dof, dof] = 1
                F_mod[dof] = 0

    return K_mod, F_mod

# ----------------------------------------------------
# Resolve o sistema linear (K * U = F)
# ----------------------------------------------------
def resolver_deslocamentos(K, F):
    U = np.linalg.solve(K, F)
    return U

# ----------------------------------------------------
# Calcula esfor�os nas barras
# ----------------------------------------------------
def calcular_esforcos(barras, U, nos):
    esforcos = {}
    for barra in barras:
        i = nos.index(barra.no_i)
        j = nos.index(barra.no_j)

        # deslocamentos locais dos n�s i e j
        u_e = np.array([U[2*i], U[2*i+1], U[2*j], U[2*j+1]])

        # matriz local de rigidez
        k_local = np.array(barra.matriz_rigidez_local())

        # for�a interna local
        f_local = k_local @ u_e
        esforcos[barra.id] = f_local

    return esforcos

# ----------------------------------------------------
# Fun��o principal de resolu��o da treli�a
# ----------------------------------------------------
def resolver_trelica(nos, barras):
    # 1. Monta matriz de rigidez global
    K = montar_matriz_global(nos, barras)

    # 2. Monta vetor de for�as globais
    F = montar_vetor_forcas(nos)

    # 3. Aplica condi��es de contorno (apoios)
    K_mod, F_mod = aplicar_condicoes_contorno(K, F, nos)

    # 4. Resolve sistema linear
    U = resolver_deslocamentos(K_mod, F_mod)

    # 5. Calcula esfor�os internos nas barras
    esforcos = calcular_esforcos(barras, U, nos)

    return U, esforcos


if __name__ == "__main__":
    from model import No, Barra, Trelica

    print("=== Defini��o da Treli�a ===")
    qtd_nos = int(input("Quantos n�s a treli�a possui? "))

    nos = []
    for i in range(qtd_nos):
        nome = input(f"Nome do n� {i+1}: ")
        x = float(input(f"Coordenada x de {nome}: "))
        y = float(input(f"Coordenada y de {nome}: "))
        apoio = input(f"Apoio de {nome} (N, P, X, Y ou vazio): ").strip().upper() or None
        carga_x = float(input(f"Carga em x de {nome} (N): "))
        carga_y = float(input(f"Carga em y de {nome} (N): "))
        no = No(nome, x, y, apoio=apoio)
        no.carga = (carga_x, carga_y)
        nos.append(no)

    qtd_barras = int(input("\nQuantas barras a treli�a possui? "))
    barras = []
    for i in range(qtd_barras):
        n1 = input(f"N� inicial da barra {i+1}: ")
        n2 = input(f"N� final da barra {i+1}: ")
        no1 = next(n for n in nos if n.id == n1)
        no2 = next(n for n in nos if n.id == n2)
        barras.append(Barra(i+1, no1, no2))

    t = Trelica()
    for n in nos:
        t.adicionar_no(n)
    for b in barras:
        t.adicionar_barra(b)

    t.montar_sistema()
    t.resolver()

    print("\n=== RESULTADOS ===")
    print("Deslocamentos por n�:")
    for no in t.nos:
        print(f"{no.id}: Ux = {no.Ux:.6e}, Uy = {no.Uy:.6e}")

    print("\nRea��es nos apoios:")
for no_id, (rx, ry) in t.obter_reacoes().items():
    print(f"{no_id}: Rx = {rx:.2f}, Ry = {ry:.2f}")

    print("\nEsfor�os axiais nas barras:")
    for barra_id, N in t.esforcos_axiais().items():
        print(f"Barra {barra_id}: N = {N:.2f}")
