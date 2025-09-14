from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from typing import Optional,List, Dict
from pydantic import BaseModel

# Definimos el modelo de datos para un hospital
class HospitalBase(BaseModel):
    nombre: str
    tipo: str
    especialidades: List[str]
    ubicacion: Dict[str, str]
    telefonos: List[str]
    dias_y_horarios: str

# Cargamos la "base de datos" JSON
with open("hospitales.json", "r", encoding="utf-8") as f:
    hospitales = json.load(f)

app = FastAPI()

# 🔹 Habilitar CORS (para pruebas: cualquier origen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Permite cualquier origen (frontend, otro server, etc.)
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Permite cualquier cabecera
)

# Ruta para devolver todos los hospitales
@app.get("/")
async def obtener_todos():
    return JSONResponse(content=hospitales)

# Ruta para filtrar hospitales con paginación
@app.get("/hospitales")
async def filtrar_hospitales(
    nombre: Optional[str] = Query(None, description="Nombre del hospital para filtrar (substring)"),
    ciudad: Optional[str] = Query(None, description="Ciudad para filtrar"),
    localidad: Optional[str] = Query(None, description="Localidad para filtrar"),
    especialidad: Optional[str] = Query(None, description="Especialidad para filtrar"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, description="Cantidad de hospitales por página"),
):
    resultado = hospitales

    if nombre:
        resultado = [h for h in resultado if nombre.lower() in h["nombre"].lower()]

    if ciudad:
        resultado = [h for h in resultado if ciudad.lower() in h["ubicacion"]["ciudad"].lower()]

    if localidad:
        resultado = [h for h in resultado if localidad.lower() in h["ubicacion"]["localidad"].lower()]

    if especialidad:
        resultado = [
            h for h in resultado
            if any(especialidad.lower() in e.lower() for e in h["especialidades"])
        ]

    total = len(resultado)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    resultado_paginado = resultado[start:end]

    return JSONResponse(content={
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "data": resultado_paginado
    })

@app.post("/hospitales")
async def agregar_hospital(hospital: HospitalBase):
    # Verificar si ya existe un hospital con el mismo nombre
    if any(h["nombre"].lower() == hospital.nombre.lower() for h in hospitales):
        raise HTTPException(status_code=400, detail="Ya existe un hospital con ese nombre")

    # Generar ID automático
    nuevo_id = max([h["id"] for h in hospitales], default=0) + 1
    nuevo_hospital = hospital.model_dump()
    nuevo_hospital["id"] = nuevo_id

    hospitales.append(nuevo_hospital)

    with open("hospitales.json", "w", encoding="utf-8") as f:
        json.dump(hospitales, f, ensure_ascii=False, indent=4)

    return {"mensaje": "Hospital agregado correctamente", "hospital": nuevo_hospital}


# Ruta para obtener un hospital por nombre exacto
@app.get("/hospitales/{nombre}")
async def obtener_hospital(nombre: str):
    nombre = nombre.lower()
    resultados = [h for h in hospitales if nombre in h["nombre"].lower()]
    return JSONResponse(content=resultados)



if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)

