from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import uvicorn

# ================================
# Conexión a MongoDB
usuario = "usuario"
contraseña = "ZMb95Uwde2nubNMS"
cluster = "cluster0.ov43urr.mongodb.net"
bd = "baseDeDatos"
coleccion = "hospitales"

uri = f"mongodb+srv://{usuario}:{contraseña}@{cluster}/{bd}?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client[bd]
hosp = db[coleccion]
# ================================

# Definimos el modelo de datos para un hospital
class HospitalBase(BaseModel):
    nombre: str
    tipo: str
    especialidades: List[str]
    ubicacion: Dict[str, str]
    telefonos: List[str]
    dias_y_horarios: str

app = FastAPI()

# 🔹 Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Función para convertir ObjectId a string
def serializar_hospital(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])  # Convertir ObjectId
    return doc

# Ruta para devolver todos los hospitales
@app.get("/")
async def obtener_todos():
    hospitales = [serializar_hospital(h) for h in hosp.find({})]
    return JSONResponse(content=hospitales)

# Ruta para filtrar hospitales con paginación
@app.get("/hospitales")
async def filtrar_hospitales(
    nombre: Optional[str] = Query(None),
    ciudad: Optional[str] = Query(None),
    localidad: Optional[str] = Query(None),
    especialidad: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
):
    query = {}

    if nombre:
        query["nombre"] = {"$regex": nombre, "$options": "i"}
    if ciudad:
        query["ubicacion.ciudad"] = {"$regex": ciudad, "$options": "i"}
    if localidad:
        query["ubicacion.localidad"] = {"$regex": localidad, "$options": "i"}
    if especialidad:
        query["especialidades"] = {"$regex": especialidad, "$options": "i"}

    total = hosp.count_documents(query)
    total_pages = (total + page_size - 1) // page_size
    skip = (page - 1) * page_size

    resultado = [serializar_hospital(h) for h in hosp.find(query).skip(skip).limit(page_size)]

    return JSONResponse(content={
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "data": resultado
    })

@app.post("/hospitales")
async def agregar_hospital(hospital: HospitalBase):
    # Verificar si ya existe
    existe = hosp.find_one({"nombre": {"$regex": f"^{hospital.nombre}$", "$options": "i"}})
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un hospital con ese nombre")

    # Generar ID incremental
    ultimo = hosp.find_one(sort=[("id", -1)])
    nuevo_id = (ultimo["id"] if ultimo else 0) + 1

    nuevo_hospital = hospital.model_dump()
    nuevo_hospital["id"] = nuevo_id

    inserted = hosp.insert_one(nuevo_hospital)
    nuevo_hospital["_id"] = str(inserted.inserted_id)

    return {"mensaje": "Hospital agregado correctamente", "hospital": nuevo_hospital}

@app.get("/hospitales/{nombre}")
async def obtener_hospital(nombre: str):
    resultados = [serializar_hospital(h) for h in hosp.find({"nombre": {"$regex": nombre, "$options": "i"}})]
    return JSONResponse(content=resultados)

@app.delete("/hospitales/{nombre}")
async def eliminar_hospital(nombre: str):
    result = hosp.delete_one({"nombre": {"$regex": f"^{nombre}$", "$options": "i"}})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Hospital '{nombre}' no encontrado")
    return {"message": f"Hospital '{nombre}' eliminado correctamente"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
