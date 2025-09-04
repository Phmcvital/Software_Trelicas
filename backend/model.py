# -*- coding: utf-8 -*-
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
    carga: Tuple[float, float] = (0.0, 0.0)  # (Fx, Fy) positivos para +x, +y
    apoio: str = "N"  # "N" livre, "P" pino (X e Y), "X" restringe x, "Y" restringe y

    # resultados
    Ux: float = 0.0
    Uy: float = 0.0

@dataclass
class Barra:
    id: int
    no_i: No
    no_j: No
    E: float = 210e9        # Pa
    A: float = 1e-2         # m² (valor padrão se não informado)

    def comprimento(self) -> float:
        dx = self.no_j.x - self.no_i.x
        dy = self.no_j.y - self.no_i.y
        return math.hypot(dx, dy)

    def cos_sin(self) -> Tuple[float,float]:
        L = self.comprimento()
        c = (self.no_j.x - self.no_i.x) / L
        s = (self.no_j.y - self.no_i.y) / L
        return c, s

    def K_local(self) -> np.ndarray:
        c, s = self.cos_sin()
        k = self.E*self.A/self.comprimento()
        # matriz 4x4 da barra de treliça 2D
        return k * np.array([
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s]
        ])

class Trelica:
    def __init__(self):
        self.nos: List[No] = []
        self.barras: List[Barra] = []
        self._map: Dict[str,int] = {}

    def adicionar_no(self, no: No):
        if no.id in self._map:
            raise ValueError(f"Nó repetido: {no.id}")
        self._map[no.id] = len(self.nos)
        self.nos.append(no)

    def adicionar_barra(self, barra: Barra):
        self.barras.append(barra)

    def _dof_idx(self, i: int) -> Tuple[int,int]:
        return 2*i, 2*i+1

    def montar(self) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        n = len(self.nos)
        K = np.zeros((2*n, 2*n), dtype=float)
        F = np.zeros(2*n, dtype=float)

        # forças nodais
        for i,no in enumerate(self.nos):
            F[2*i]   = no.carga[0]
            F[2*i+1] = no.carga[1]

        # rigidez global
        for barra in self.barras:
            i = self._map[barra.no_i.id]
            j = self._map[barra.no_j.id]
            ke = barra.K_local()
            dofs = [2*i, 2*i+1, 2*j, 2*j+1]
            for a in range(4):
                for b in range(4):
                    K[dofs[a], dofs[b]] += ke[a,b]

        # restrições
        fixos: List[int] = []
        for i,no in enumerate(self.nos):
            if no.apoio.upper() in ("P","PX","XP"):  # tratar somente "P" (pino) aqui
                fixos += [2*i, 2*i+1]
            else:
                if no.apoio.upper() == "X":
                    fixos += [2*i]
                if no.apoio.upper() == "Y":
                    fixos += [2*i+1]

        return K, F, fixos

    def resolver(self):
        K, F, fixos = self.montar()
        dofs = np.arange(K.shape[0])
        livres = np.array([d for d in dofs if d not in fixos], dtype=int)

        # Particionamento
        KLL = K[np.ix_(livres, livres)]
        FL  = F[livres]

        U = np.zeros_like(F)
        if len(livres) > 0:
            U[livres] = np.linalg.solve(KLL, FL)

        # salvar deslocamentos
        for i,no in enumerate(self.nos):
            no.Ux = float(U[2*i])
            no.Uy = float(U[2*i+1])

        # reações R = K*U - F (sinal positivo = reação aplicada pelo apoio no nó)
        R = K @ U - F
        self._reacoes: Dict[str,Tuple[float,float]] = {}
        for i,no in enumerate(self.nos):
            if (2*i in fixos) or (2*i+1 in fixos):
                self._reacoes[no.id] = (float(R[2*i]), float(R[2*i+1]))

        # esforços axiais
        self._N: Dict[int, float] = {}
        for barra in self.barras:
            i = self._map[barra.no_i.id]
            j = self._map[barra.no_j.id]
            ue = np.array([U[2*i], U[2*i+1], U[2*j], U[2*j+1]])
            c,s = barra.cos_sin()
            L = barra.comprimento()
            k = barra.E*barra.A/L
            # deformação axial ~ ( (u_j - u_i)·(c,s) ) / L; esforço = EA/L * projeção
            axial = k * ( (ue[2]-ue[0])*c + (ue[3]-ue[1])*s )
            # Por convenção: N > 0 = tração, N < 0 = compressão
            self._N[barra.id] = float(axial)

    def deslocamentos(self) -> Dict[str,Tuple[float,float]]:
        return {no.id: (no.Ux, no.Uy) for no in self.nos}

    def reacoes(self) -> Dict[str,Tuple[float,float]]:
        return self._reacoes

    def esforcos_axiais(self) -> Dict[int, float]:
        return self._N
