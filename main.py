# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import random
import os

# Cargar variables del .env
load_dotenv()

SUPABASE_URL = os.getenv("sb_url")
SUPABASE_KEY = os.getenv("sb_anon_key")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan las variables sb_url o sb_anon_key en el archivo .env")

# Inicializar cliente de Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="CamAI API - Supabase Client", version="4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS PYDANTIC ---
class PacienteBase(BaseModel):
    nombre: str
    edad: int
    diagnostico: str
    frecuencia_cardiaca: int
    saturacion_oxigeno: int
    comorbilidades: int

class PacienteCreate(PacienteBase):
    pass

class PacienteUpdate(BaseModel):
    nombre: Optional[str] = None
    edad: Optional[int] = None
    diagnostico: Optional[str] = None
    frecuencia_cardiaca: Optional[int] = None
    saturacion_oxigeno: Optional[int] = None
    comorbilidades: Optional[int] = None

# --- MOTOR DE PREDICCIÓN CON IA ---
def calcular_prediccion_ia(edad: int, diagnostico: str, fc: int, sat: int, comorbilidades: int):
    riesgo = 0
    if sat < 92: riesgo += 40
    if fc > 100: riesgo += 20
    if edad > 65: riesgo += 20
    riesgo += (comorbilidades * 10)

    requiere_internacion = riesgo >= 50
    probabilidad = min(99.0, max(5.0, riesgo + random.uniform(-3, 3)))
    
    dias_estancia = 0.0
    if requiere_internacion:
        base_dias = {"Neumonía": 4.5, "Insuficiencia cardíaca": 6.0, "Apendicectomía": 2.5, "ACV": 7.0, "Sepsis": 8.5}.get(diagnostico, 3.5)
        dias_estancia = round(max(1.0, base_dias + (comorbilidades * 0.8) + random.uniform(-0.5, 0.5)), 1)
        
    nivel_riesgo = "ALTO" if riesgo >= 70 else ("MEDIO" if riesgo >= 40 else "BAJO")
    return requiere_internacion, round(probabilidad, 1), dias_estancia, nivel_riesgo

# --- ENDPOINTS REST ---

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/api/v1/pacientes")
def listar_pacientes():
    response = supabase.table("pacientes").select("*").execute()
    return response.data

@app.post("/api/v1/pacientes")
def agregar_paciente(paciente: PacienteCreate):
    internacion, prob, dias, riesgo = calcular_prediccion_ia(
        paciente.edad, paciente.diagnostico, paciente.frecuencia_cardiaca,
        paciente.saturacion_oxigeno, paciente.comorbilidades
    )
    
    payload = {
        **paciente.model_dump(),
        "requiere_internacion": internacion,
        "probabilidad_internacion": prob,
        "dias_estancia_estimados": dias,
        "nivel_riesgo": riesgo
    }
    
    response = supabase.table("pacientes").insert(payload).execute()
    return response.data

@app.put("/api/v1/pacientes/{paciente_id}")
def modificar_paciente(paciente_id: int, datos: PacienteUpdate):
    # Obtener paciente actual
    res_actual = supabase.table("pacientes").select("*").eq("id", paciente_id).execute()
    if not res_actual.data:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    p = res_actual.data[0]
    
    # Aplicar cambios enviados
    datos_actualizados = datos.model_dump(exclude_unset=True)
    for key, val in datos_actualizados.items():
        p[key] = val
        
    internacion, prob, dias, riesgo = calcular_prediccion_ia(
        p["edad"], p["diagnostico"], p["frecuencia_cardiaca"], p["saturacion_oxigeno"], p["comorbilidades"]
    )
    
    p["requiere_internacion"] = internacion
    p["probabilidad_internacion"] = prob
    p["dias_estancia_estimados"] = dias
    p["nivel_riesgo"] = riesgo
    
    response = supabase.table("pacientes").update(p).eq("id", paciente_id).execute()
    return response.data

@app.delete("/api/v1/pacientes/{paciente_id}")
def eliminar_paciente(paciente_id: int):
    supabase.table("pacientes").delete().eq("id", paciente_id).execute()
    return {"mensaje": f"Paciente {paciente_id} eliminado exitosamente."}

# --- SIMULADOR DE DATOS DE PRUEBA ---
@app.post("/api/v1/simular-datos")
def generar_simulacion(cantidad: int = 10):
    nombres = ["Roberto", "María", "Carlos", "Lucía", "Jorge", "Elena", "Pedro", "Sofía", "Miguel", "Valeria"]
    apellidos = ["García", "Rodríguez", "López", "Pérez", "González", "Martínez", "Sánchez", "Romero"]
    diagnosticos = ["Neumonía", "Insuficiencia cardíaca", "Apendicectomía", "ACV", "Sepsis", "Bronquitis"]

    registros = []
    for _ in range(cantidad):
        nombre_comp = f"{random.choice(nombres)} {random.choice(apellidos)}"
        edad = random.randint(18, 85)
        diag = random.choice(diagnosticos)
        fc = random.randint(60, 130)
        sat = random.randint(82, 100)
        comorb = random.randint(0, 4)

        internacion, prob, dias, riesgo = calcular_prediccion_ia(edad, diag, fc, sat, comorb)

        registros.append({
            "nombre": nombre_comp,
            "edad": edad,
            "diagnostico": diag,
            "frecuencia_cardiaca": fc,
            "saturacion_oxigeno": sat,
            "comorbilidades": comorb,
            "requiere_internacion": internacion,
            "probabilidad_internacion": prob,
            "dias_estancia_estimados": dias,
            "nivel_riesgo": riesgo
        })

    response = supabase.table("pacientes").insert(registros).execute()
    return {"mensaje": f"Se han insertado {len(registros)} pacientes de simulación en Supabase.", "datos": response.data}

@app.get("/api/v1/dashboard")
def obtener_dashboard():
    response = supabase.table("pacientes").select("*").execute()
    pacientes = response.data
    
    totales = len(pacientes)
    internados = sum(1 for p in pacientes if p.get("requiere_internacion"))
    sum_dias = sum(p.get("dias_estancia_estimados", 0) for p in pacientes if p.get("requiere_internacion"))
    promedio_dias = round(sum_dias / internados, 1) if internados > 0 else 0.0

    return {
        "pacientes_totales_evaluados": totales,
        "pacientes_a_internar": internados,
        "promedio_dias_estancia": promedio_dias,
        "camas_disponibles": max(0, 50 - internados)
    }