from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn
import json

# Cargamos la "base de datos" JSON
with open("hospitales.json", "r", encoding="utf-8") as f:
    hospitales = json.load(f)

app = FastAPI()

# Ruta para devolver todos los hospitales
@app.get("/")
async def obtener_todos():
    return JSONResponse(content=hospitales)

# Ruta para obtener un hospital por nombre
@app.get("/hospital/{nombre}")
async def obtener_hospital(nombre: str):
    hospital = next((h for h in hospitales if h["nombre"].lower() == nombre.lower()), None)
    if hospital:
        return JSONResponse(content=hospital)
    else:
        raise HTTPException(status_code=404, detail="Hospital no encontrado")

# Ruta para filtrar hospitales por especialidad
@app.get("/hospital")
async def filtrar_hospitales(
    nombre: str = Query(None, description="Nombre del hospital para filtrar"),
    ciudad: str = Query(None, description="Ciudad para filtrar"),
    especialidad: str = Query(None, description="Especialidad para filtrar")
):
    resultado = hospitales

    # Filtrar por nombre si se proporciona
    if nombre:
        resultado = [h for h in resultado if nombre.lower() in h["nombre"].lower()]

    # Filtrar por ciudad si se proporciona
    if ciudad:
        resultado = [h for h in resultado if ciudad.lower() in h["ubicacion"]["ciudad"].lower()]

    # Filtrar por especialidad si se proporciona
    if especialidad:
        resultado = [
            h for h in resultado
            if especialidad.lower() in (e.lower() for e in h["especialidades"])
        ]

    if resultado:
        return JSONResponse(content=resultado)
    else:
        raise HTTPException(status_code=404, detail="No se encontraron hospitales con esos filtros")
