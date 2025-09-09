




import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple, Dict
import traceback

from model import Trelica, No, Barra
from resolve_trelica import criar_trelica_de_dados

class NoPayload(BaseModel):
    id: str
    x: float
    y: float
    carga: Tuple[float, float]
    apoio: str

class BarraPayload(BaseModel):
    id: int
    no_i: str
    no_j: str
    E: float = 210e9 
    A: float = 0.01   

class TrelicaPayload(BaseModel):
    nos: List[NoPayload]
    barras: List[BarraPayload]

app = FastAPI(
    title="API para Resolução de Treliças",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://software-trelicas-app.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/calcular")
async def calcular_trelica(payload: TrelicaPayload):
    """
    Recebe os dados da treliça em formato JSON, calcula e retorna os resultados.
    """
    try:
        dados_dict = payload.dict()
        
        trelica = criar_trelica_de_dados(dados_dict)
        
        
        trelica.resolver()
        
        esforcos_por_barra = {}
        for barra in trelica.barras:
            N = trelica._N[barra.id]
            c, s = barra.cos_sin()
            esforcos_por_barra[barra.id] = {
                "no_i": barra.no_i.id,
                "no_j": barra.no_j.id,
                "N_orientado": float(N)
            }

        resultados = {
            "deslocamentos": {
                no.id: {"Ux": float(no.Ux), "Uy": float(no.Uy)}
                for no in trelica.nos
            },
            "reacoes": {
                no_id: {"Rx": float(rx), "Ry": float(ry)}
                for no_id, (rx, ry) in trelica.reacoes().items()
            },
            "esforcos_por_barra": esforcos_por_barra
        }

        return resultados

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Erro no cálculo: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)