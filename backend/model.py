# Classes: Nó, Elemento e treliça

import math
from typing import List, Tuple

class No:

    # Representação de um nó

    def __init__(self, id: str, x: float, y: float, carga: Tuple[float, float] = (0.0, 0.0), apoio: str = "N"):
        self.id = id
        self.x = x
        self.y = y
        self.carga = carga
        self.apoio = apoio

    def __repr__(self):
        return f"No({self.id}, x={self.x}, y={self.y}, carga={self.carga}, apoio={self.apoio})"
    
class Barra:

    #representação de uma barra

    def __init__(self, id: int, no_i: No, no_j: No, E: float = 210e9, A: float = 0.01):
        self.id = id
        self.no_i = no_i
        self.no_j = no_j
        self.E = E # elasticidade
        self.A = A # área da seção transversal

        # geometria
        dx = no_j.x - no_i.x # distancia x
        dy = no_j.y - no_i.y # distancia y
        self.comprimento = math.sqrt(dx**2 + dy**2)
        self.cos = dx / self.comprimento
        self.sen = dx / self.comprimento

    def matriz_rigidez_local(self):

        #matriz de rigidez local em coordenadas (4x4)

        k = (self.E * self.A) / self.comprimento
        c = self.cos
        s = self.sen
        return k * [
            [ c*c,  c*s, -c*c, -c*s],
            [ c*s,  s*s, -c*s, -s*s],
            [-c*c, -c*s,  c*c,  c*s],
            [-c*s, -s*s,  c*s,  s*s],
        ]
    
    def __repr(self):
        return f"Barra({self.id}, {self.no_i.id}-{self.no_j.id}, L={self.comprimento:.3f})"
    
    