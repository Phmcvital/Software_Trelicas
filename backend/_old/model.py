# -*- coding: latin-1 -*-
import math
from typing import List, Tuple, Dict
import numpy as np

# Classe que representa um nó da treliça
class No:
    def __init__(self, id: str, x: float, y: float, carga: Tuple[float, float] = (0.0, 0.0), apoio: str = "N"):
        # Identificador (ex: "A", "B", "C")
        self.id = id
        # Coordenadas do nó
        self.x = x
        self.y = y
        # Força aplicada no nó (Px, Py)
        self.carga = carga
        # Tipo de apoio: N (livre), P (pino), X (rolete vertical), Y (apoio lateral)
        self.apoio = apoio
        # Deslocamentos que serão calculados
        self.Ux = 0.0
        self.Uy = 0.0
    def __repr__(self):
        return f"No({self.id}, x={self.x}, y={self.y}, carga={self.carga}, apoio={self.apoio}, U=({self.Ux:.6g},{self.Uy:.6g}))"

# Classe que representa uma barra (elemento de ligação entre dois nós)
class Barra:
    def __init__(self, id: int, no_i: No, no_j: No, E: float = 210e9, A: float = 0.01):
        # Identificador da barra
        self.id = id
        # Nós de extremidade
        self.no_i = no_i
        self.no_j = no_j
        # Propriedades do material e seção
        self.E = E
        self.A = A
        # Diferença de coordenadas
        dx = no_j.x - no_i.x
        dy = no_j.y - no_i.y
        # Comprimento da barra
        self.comprimento = math.hypot(dx, dy)
        # Cossenos diretores
        self.cos = dx / self.comprimento if self.comprimento != 0 else 0.0
        self.sen = dy / self.comprimento if self.comprimento != 0 else 0.0
    # Matriz de rigidez em coordenadas globais (4x4)
    def matriz_rigidez_global(self) -> np.ndarray:
        k = (self.E * self.A) / self.comprimento
        c = self.cos
        s = self.sen
        return k * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s],
        ], dtype=float)
    # Calcula a força axial na barra dado o vetor de deslocamentos locais
    def forca_axial(self, Ue: np.ndarray) -> float:
        c = self.cos
        s = self.sen
        return (self.E * self.A / self.comprimento) * np.dot(np.array([-c, -s, c, s], dtype=float), Ue)
    def __repr__(self):
        return f"Barra({self.id}, {self.no_i.id}-{self.no_j.id}, L={self.comprimento:.6g})"

# Classe principal que controla a treliça
class Trelica:
    def __init__(self):
        # Lista de nós
        self.nos: List[No] = []
        # Lista de barras
        self.barras: List[Barra] = []
        # Mapeamento id do nó -> índice
        self._mapa_indices: Dict[str, int] = {}
        # Matrizes globais
        self.K: np.ndarray | None = None
        self.F: np.ndarray | None = None
        self.U: np.ndarray | None = None
        # Resultados
        self.reacoes: Dict[str, Tuple[float, float]] = {}
        self.forcas_axiais: Dict[int, float] = {}
    # Adiciona um nó à treliça
    def adicionar_no(self, no: No):
        if no.id in self._mapa_indices:
            raise ValueError("Nó duplicado")
        self._mapa_indices[no.id] = len(self.nos)
        self.nos.append(no)
    # Adiciona uma barra à treliça
    def adicionar_barra(self, barra: Barra):
        self.barras.append(barra)
    # Retorna os graus de liberdade (Ux,Uy) de um nó
    def _dof(self, idx_no: int) -> Tuple[int,int]:
        return 2*idx_no, 2*idx_no+1
    # Monta a matriz de rigidez global e o vetor de forças
    def montar_sistema(self):
        n = len(self.nos)
        self.K = np.zeros((2*n, 2*n), dtype=float)
        self.F = np.zeros(2*n, dtype=float)
        # Monta vetor de forças globais
        for i,no in enumerate(self.nos):
            self.F[2*i] = no.carga[0]
            self.F[2*i+1] = no.carga[1]
        # Monta matriz de rigidez global
        for barra in self.barras:
            i = self._mapa_indices[barra.no_i.id]
            j = self._mapa_indices[barra.no_j.id]
            dofs = [*self._dof(i), *self._dof(j)]
            ke = barra.matriz_rigidez_global()
            for a in range(4):
                for b in range(4):
                    self.K[dofs[a], dofs[b]] += ke[a,b]
    # Determina os graus de liberdade fixos pelos apoios
    def _dofs_fixos(self) -> List[int]:
        fixos = []
        for i,no in enumerate(self.nos):
            if no.apoio.upper() == "P":
                fixos.extend([2*i, 2*i+1])
            elif no.apoio.upper() == "X":
                fixos.append(2*i+1)
            elif no.apoio.upper() == "Y":
                fixos.append(2*i)
        return sorted(set(fixos))
    # Resolve o sistema da treliça
    def resolver(self):
        if self.K is None or self.F is None:
            self.montar_sistema()
        n = len(self.nos)
        # Graus de liberdade fixos e livres
        fixos = self._dofs_fixos()
        livres = [d for d in range(2*n) if d not in fixos]
        # Submatriz e vetor reduzidos
        Kff = self.K[np.ix_(livres, livres)]
        Ff = self.F[livres]
        # Resolve deslocamentos livres
        Uf = np.linalg.solve(Kff, Ff) if len(livres) > 0 else np.array([], dtype=float)
        # Monta vetor global de deslocamentos
        self.U = np.zeros(2*n, dtype=float)
        self.U[livres] = Uf
        # Atualiza deslocamentos dos nós
        for i,no in enumerate(self.nos):
            no.Ux = float(self.U[2*i])
            no.Uy = float(self.U[2*i+1])
        # Calcula reações nos apoios
        R = self.K @ self.U - self.F
        self.reacoes = {}
        for i,no in enumerate(self.nos):
            rx = R[2*i] if 2*i in fixos else 0.0
            ry = R[2*i+1] if 2*i+1 in fixos else 0.0
            if abs(rx) > 0 or abs(ry) > 0:
                self.reacoes[no.id] = (float(rx), float(ry))
        # Calcula forças axiais nas barras
        self.forcas_axiais = {}
        for barra in self.barras:
            i = self._mapa_indices[barra.no_i.id]
            j = self._mapa_indices[barra.no_j.id]
            dofs = [*self._dof(i), *self._dof(j)]
            Ue = self.U[dofs]
            N = barra.forca_axial(Ue)
            self.forcas_axiais[barra.id] = float(N)
    # Retorna deslocamentos por nó
    def deslocamentos(self) -> Dict[str, Tuple[float,float]]:
        return {no.id:(no.Ux,no.Uy) for no in self.nos}
    # Retorna reações de apoio
    def obter_reacoes(self) -> Dict[str, Tuple[float,float]]:
        return dict(self.reacoes)
    # Retorna esforços axiais nas barras
    def esforcos_axiais(self) -> Dict[int, float]:
        return dict(self.forcas_axiais)

# Exemplo mínimo de uso:
# A = No("A", 0.0, 0.0, apoio="P")
# B = No("B", 1.0, 0.0, apoio="X")
# C = No("C", 1.0, 1.0, carga=(0.0, -1000.0))
# t = Trelica()
# for n in [A,B,C]: t.adicionar_no(n)
# t.adicionar_barra(Barra(1,A,C))
# t.adicionar_barra(Barra(2,B,C))
# t.adicionar_barra(Barra(3,A,B))
# t.montar_sistema()
# t.resolver()
# print(t.deslocamentos())
# print(t.obter_reacoes())
# print(t.esforcos_axiais())
