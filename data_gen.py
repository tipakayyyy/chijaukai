"""
data_gen.py
Generación de datos sintéticos para el MVP de CamAI.

En producción, estos datos vendrían de los sistemas HIS/EHR del hospital
(Fase 1 del roadmap técnico: "Preparación de datos"). Para la demo del
hackathon usamos un generador aleatorio pero determinista (seed fija) que
respeta los parámetros del caso base de la propuesta:
    - Hospital de 200 camas
    - 85% de ocupación promedio
    - ~34 altas diarias
"""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

# (diagnóstico, LOS base en días, complejidad clínica)
DIAGNOSTICOS = [
    ("Neumonía", 4.5, "media"),
    ("Apendicectomía", 2.5, "baja"),
    ("Insuficiencia cardíaca", 6.0, "alta"),
    ("Fractura de cadera", 5.5, "media"),
    ("Cirugía general", 3.5, "media"),
    ("EPOC exacerbado", 5.0, "alta"),
    ("Parto normal", 1.5, "baja"),
    ("ACV isquémico", 7.0, "alta"),
]


@dataclass
class Paciente:
    id: int
    diagnostico: str
    complejidad: str
    los_base_dias: float
    hora_ingreso: datetime
    cama_id: str = None
    estado: str = "ingresado"  # ingresado | alta_prevista | dado_de_alta | esperando_cama
    hora_alta_prevista: datetime = None
    hora_alta_real: datetime = None


@dataclass
class Cama:
    id: str
    ocupada: bool = False
    paciente_id: int = None
    necesita_limpieza: bool = False
    hora_liberada: datetime = None


def generar_camas(n_camas: int = 200, ocupacion: float = 0.85, seed: int = 42):
    """Crea el parque de camas del hospital con la ocupación inicial del caso base."""
    rnd = random.Random(seed)
    n_ocupadas = int(n_camas * ocupacion)
    ocupadas_idx = set(rnd.sample(range(n_camas), n_ocupadas))
    camas = [Cama(id=f"C-{i+1:03d}", ocupada=(i in ocupadas_idx)) for i in range(n_camas)]
    return camas


def generar_pacientes(camas, hora_actual: datetime, seed: int = 42):
    """Asigna un paciente sintético a cada cama ya ocupada."""
    rnd = random.Random(seed + 1)
    pacientes = []
    pid = 1
    for cama in camas:
        if cama.ocupada:
            diag, los_base, complejidad = rnd.choice(DIAGNOSTICOS)
            los_real = max(0.5, rnd.gauss(los_base, los_base * 0.2))
            hora_ingreso = hora_actual - timedelta(days=rnd.uniform(0.2, los_real))
            p = Paciente(
                id=pid,
                diagnostico=diag,
                complejidad=complejidad,
                los_base_dias=los_real,
                hora_ingreso=hora_ingreso,
                cama_id=cama.id,
                estado="ingresado",
            )
            cama.paciente_id = pid
            pacientes.append(p)
            pid += 1
    return pacientes
