
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
import math

@dataclass
class No:
    id: str
    x: float
    y: float
    carga: Tuple[float, float] = (0.0, 0.0)  
    apoio: str = "N"  

    
    Ux: float = 0.0
    Uy: float = 0.0

@dataclass
class Barra:
    id: int
    no_i: No
    no_j: No
    E: float = 210e9        
    A: float = 1e-2         

# Função responsável por comprimento
    def comprimento(self) -> float:
        dx = self.no_j.x - self.no_i.x
        dy = self.no_j.y - self.no_i.y
        return math.hypot(dx, dy)

# Função responsável por cos sin
    def cos_sin(self) -> Tuple[float,float]:
        L = self.comprimento()
        c = (self.no_j.x - self.no_i.x) / L
        s = (self.no_j.y - self.no_i.y) / L
        return c, s

# Função responsável por K local
    def K_local(self) -> np.ndarray:
        c, s = self.cos_sin()
        k = self.E*self.A/self.comprimento()
        
        return k * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s]
        ])
    def tensao(self, N: float) -> float:
        # Calcula a tensão na barra (Força/Área)
        return N / self.A

    def deformacao(self, tensao: float) -> float:
        # Calcula a deformação na barra (Tensão/Módulo de Young)
        return tensao / self.E

class Trelica:
# Função responsável por   init  
    def __init__(self):
        self.nos: List[No] = []
        self.barras: List[Barra] = []
        self._map: Dict[str,int] = {}

# Função responsável por adicionar no
    def adicionar_no(self, no: No):
        if no.id in self._map:
            raise ValueError(f"Nó repetido: {no.id}")
        self._map[no.id] = len(self.nos)
        self.nos.append(no)

# Função responsável por adicionar barra
    def adicionar_barra(self, barra: Barra):
        self.barras.append(barra)

# Função responsável por  dof idx
    def _dof_idx(self, i: int) -> Tuple[int,int]:
        return 2*i, 2*i+1

# Função responsável por montar
    def montar(self) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        n = len(self.nos)
        K = np.zeros((2*n, 2*n), dtype=float)
        F = np.zeros(2*n, dtype=float)

        
        for i,no in enumerate(self.nos):
            F[2*i]   = no.carga[0]
            F[2*i+1] = no.carga[1]

        
        for barra in self.barras:
            i = self._map[barra.no_i.id]
            j = self._map[barra.no_j.id]
            ke = barra.K_local()
            dofs = [2*i, 2*i+1, 2*j, 2*j+1]
            for a in range(4):
                for b in range(4):
                    K[dofs[a], dofs[b]] += ke[a,b]

        
        fixos: List[int] = []
        for i,no in enumerate(self.nos):
            if no.apoio.upper() in ("P","PX","XP"):  
                fixos += [2*i, 2*i+1]
            else:
                if no.apoio.upper() == "X":
                    fixos += [2*i]
                if no.apoio.upper() == "Y":
                    fixos += [2*i+1]

        return K, F, fixos

# Função responsável por resolver
    def resolver(self):
        K, F, fixos = self.montar()
        dofs = np.arange(K.shape[0])
        livres = np.array([d for d in dofs if d not in fixos], dtype=int)

        KLL = K[np.ix_(livres, livres)]
        FL  = F[livres]

        U = np.zeros_like(F)
        if len(livres) > 0:
            U[livres] = np.linalg.solve(KLL, FL)

        for i,no in enumerate(self.nos):
            no.Ux = float(U[2*i])
            no.Uy = float(U[2*i+1])

        R = K @ U - F
        self._reacoes: Dict[str,Tuple[float,float]] = {}
        for i,no in enumerate(self.nos):
            if (2*i in fixos) or (2*i+1 in fixos):
                self._reacoes[no.id] = (float(R[2*i]), float(R[2*i+1]))

        self._N: Dict[int, float] = {}
        self._tensoes: Dict[int, float] = {}
        self._deformacoes: Dict[int, float] = {}
        for barra in self.barras:
            i = self._map[barra.no_i.id]
            j = self._map[barra.no_j.id]
            ue = np.array([U[2*i], U[2*i+1], U[2*j], U[2*j+1]])
            c,s = barra.cos_sin()
            L = barra.comprimento()
            k = barra.E*barra.A/L
            
            axial = k * ( (ue[2]-ue[0])*c + (ue[3]-ue[1])*s )
            tensao = barra.tensao(axial)
            deformacao = barra.deformacao(tensao)

            self._N[barra.id] = float(axial)
            self._tensoes[barra.id] = float(tensao)
            self._deformacoes[barra.id] = float(deformacao)

# Função responsável por deslocamentos
    def deslocamentos(self) -> Dict[str,Tuple[float,float]]:
        return {no.id: (no.Ux, no.Uy) for no in self.nos}

# Função responsável por reacoes
    def reacoes(self) -> Dict[str,Tuple[float,float]]:
        return self._reacoes

# Função responsável por esforcos axiais
    def esforcos_axiais(self) -> Dict[int, float]:
        return self._N
# Função responsável por tensoes
    def tensoes(self) -> Dict[int, float]:
        return self._tensoes
# Função responsável por deformacoes
    def deformacoes(self) -> Dict[int, float]:
        return self._deformacoes