"""
agents.py
Implementación simplificada (MVP) de los cuatro agentes descritos en la
arquitectura CamAI Swarm Engine:

    [ Agente Triage/Ingreso ] --> [ Agente Predictor de Alta (Motor LOS) ]
                |                                |
                v                                v
          [ Agente Orquestador de Camas -- optimización húngara ]
                              |
                              v
          [ Agente de Operaciones / Limpieza -- cola dinámica ]

Nota de alcance (ver README > "Alcance del MVP"):
El Motor LOS aquí es una heurística determinística + ruido, no un modelo de
ML entrenado. El Orquestador de Camas SÍ usa el algoritmo húngaro real
(scipy.optimize.linear_sum_assignment) tal como se describe en la propuesta,
porque es el componente que garantiza la asignación óptima global.
"""

import random
from datetime import timedelta

import numpy as np
from scipy.optimize import linear_sum_assignment


class AgenteTriage:
    """Clasifica y registra el estado clínico inicial de cada paciente."""

    def registrar(self, paciente):
        return {
            "paciente_id": paciente.id,
            "complejidad": paciente.complejidad,
            "diagnostico": paciente.diagnostico,
        }


class AgenteMotorLOS:
    """
    Motor Predictivo de Duración de Estancia (LOS) — versión MVP.
    Estima el momento probable de alta con una heurística por complejidad
    clínica más una variabilidad aleatoria, simulando la incertidumbre de
    una predicción real. En producción sería un modelo entrenado con
    variables clínicas y administrativas (Fase 2 del roadmap técnico).
    """

    FACTOR_INCERTIDUMBRE = {"baja": 0.10, "media": 0.20, "alta": 0.30}

    def predecir_alta(self, paciente, hora_actual):
        dias_transcurridos = (hora_actual - paciente.hora_ingreso).total_seconds() / 86400
        dias_restantes = max(0.05, paciente.los_base_dias - dias_transcurridos)
        incertidumbre = self.FACTOR_INCERTIDUMBRE[paciente.complejidad]
        ruido = random.gauss(0, dias_restantes * incertidumbre)
        prediccion_dias = max(0.05, dias_restantes + ruido)
        return hora_actual + timedelta(days=prediccion_dias)


class AgenteOrquestadorCamas:
    """
    Resuelve la asignación óptima entre pacientes que esperan cama y camas
    recién liberadas como un problema de emparejamiento bipartito, usando
    el algoritmo húngaro (complejidad polinómica), garantizando una
    asignación óptima global en lugar de heurísticas reactivas locales.
    """

    def optimizar_asignacion(self, pacientes_nuevos, camas_liberadas):
        if not pacientes_nuevos or not camas_liberadas:
            return {}

        n, m = len(pacientes_nuevos), len(camas_liberadas)
        costo = np.zeros((n, m))

        for i in range(n):
            for j, cama in enumerate(camas_liberadas):
                # Minimizar tiempo ocioso: penaliza dejar camas libres esperando.
                espera_horas = cama.get("horas_libre", 0)
                costo[i, j] = -espera_horas + random.uniform(0, 0.01)

        filas, columnas = linear_sum_assignment(costo)
        asignaciones = {}
        for f, c in zip(filas, columnas):
            asignaciones[pacientes_nuevos[f]["paciente_id"]] = camas_liberadas[c]["cama_id"]
        return asignaciones


class AgenteLimpieza:
    """Traduce la asignación en una cola de trabajo priorizada en tiempo real."""

    def generar_cola(self, camas_pendientes_limpieza):
        return sorted(camas_pendientes_limpieza, key=lambda c: c["horas_esperando"], reverse=True)
